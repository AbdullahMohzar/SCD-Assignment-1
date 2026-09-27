import asyncio
import logging
import signal
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from pythonjsonlogger import jsonlogger

from app.config import get_settings
from app.database import engine
from app.providers.cache import get_cache_provider
from app.routes.complaints import router as complaints_router
from app.routes.health import router as health_router
from app.routes.meta import router as meta_router
from app.routes.stats import router as stats_router

settings = get_settings()

# Setup structured JSON logging to stdout (§2.2)
logger = logging.getLogger()
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
log_handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(status_code)s %(duration_ms)s"
)
log_handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(log_handler)

# Prometheus metrics for HTTP traffic
HTTP_REQUESTS_TOTAL = Counter(
    "civicpulse_http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_HISTOGRAM = Histogram(
    "civicpulse_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# In-flight request tracking for graceful SIGTERM drain
in_flight_requests = 0
shutdown_initiated = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle and graceful shutdown connections."""
    logging.info({"message": "CivicPulse backend starting", "triage_provider": settings.TRIAGE_PROVIDER})

    # Register SIGTERM signal handler for Kubernetes rolling updates (§2.2)
    loop = asyncio.get_running_loop()

    def handle_sigterm() -> None:
        global shutdown_initiated
        shutdown_initiated = True
        logging.info({"message": "SIGTERM received. Draining in-flight requests before shutdown."})

    try:
        loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    except (NotImplementedError, RuntimeError):
        # Windows or non-main thread fallback
        signal.signal(signal.SIGTERM, lambda sig, frame: handle_sigterm())

    yield

    # Draining phase
    wait_time = 0.0
    while in_flight_requests > 0 and wait_time < 10.0:
        await asyncio.sleep(0.1)
        wait_time += 0.1

    logging.info({"message": "Closing database connection pool and Redis connections..."})
    await engine.dispose()
    await get_cache_provider().close()
    logging.info({"message": "CivicPulse backend successfully drained and shut down."})


app = FastAPI(
    title="CivicPulse API",
    description="Municipal Complaint Intake, Triage, and Operations Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS middleware for edge frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_lifecycle_middleware(request: Request, call_next):
    """Tracks in-flight requests, generates/propagates X-Request-ID, logs structured JSON, and records metrics."""
    global in_flight_requests

    # Reject new traffic during SIGTERM drain
    if shutdown_initiated and request.url.path not in ("/health", "/ready"):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Server is shutting down. Try another replica."},
        )

    in_flight_requests += 1
    # Propagate or generate X-Request-ID (§2.2)
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Log structured JSON line
        logging.info(
            {
                "message": f"{request.method} {request.url.path}",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request_id,
                "duration_ms": duration_ms,
            }
        )

        # Record metrics
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code),
        ).inc()
        HTTP_REQUEST_DURATION_HISTOGRAM.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(time.perf_counter() - start_time)

        return response
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logging.error(
            {
                "message": f"Unhandled error processing {request.method} {request.url.path}: {exc}",
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "error": str(exc),
            }
        )
        raise
    finally:
        in_flight_requests -= 1


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into the required field-level error body (§2.2)."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors.append({"field": field or "body", "message": err.get("msg", "Invalid value")})

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Field-level validation error",
            "errors": errors,
        },
    )


# Register routes
app.include_router(complaints_router)
app.include_router(stats_router)
app.include_router(meta_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "service": "CivicPulse Backend",
        "status": "operational",
        "documentation": "/api/docs",
    }
