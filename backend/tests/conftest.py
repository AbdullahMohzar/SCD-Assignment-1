import os
import sys
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set testing environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TRIAGE_PROVIDER"] = "simulated"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100"

from app.database import get_db_session
from app.dependencies import get_complaint_service, get_stats_service
from app.main import app
from app.models.complaint import Base, Complaint
from app.providers.cache import CacheProvider, get_cache_provider
from app.providers.rate_limiter import DistributedRateLimiter, get_rate_limiter
from app.providers.triage.factory import get_triage_provider
from app.providers.triage.simulated import SimulatedTriage
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.stats_service import StatsService
from app.services.triage_service import TriageService

# Use SQLite in-memory database with static pool for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class MockCacheProvider:
    """In-memory cache provider for deterministic testing."""

    def __init__(self):
        self._store = {}
        self.stats_cache = None

    async def get_client(self):
        return self

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 30):
        self._store[key] = value
        return True

    async def delete(self, key: str):
        self._store.pop(key, None)
        return True

    async def get_stats_cache(self):
        return self.stats_cache

    async def set_stats_cache(self, stats: dict, ttl: int = 30):
        self.stats_cache = stats

    async def invalidate_stats_cache(self):
        self.stats_cache = None

    def compute_triage_hash(self, text: str, location: str) -> str:
        import hashlib
        payload = f"{text.strip().lower()}|{location.strip().lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def get_triage_cache(self, text: str, location: str):
        h = self.compute_triage_hash(text, location)
        return self._store.get(f"triage:{h}")

    async def set_triage_cache(self, text: str, location: str, result: dict, ttl: int = 86400):
        h = self.compute_triage_hash(text, location)
        self._store[f"triage:{h}"] = result

    async def ping(self):
        return True

    async def close(self):
        self._store.clear()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_cache():
    return MockCacheProvider()


@pytest.fixture
async def client(db_session: AsyncSession, mock_cache: MockCacheProvider):
    async def override_get_db():
        yield db_session

    def override_get_complaint_service():
        repo = ComplaintRepository(db_session)
        service = ComplaintService(repo)
        service.cache_provider = mock_cache
        service.triage_service = TriageService(provider=SimulatedTriage())
        service.triage_service.cache = mock_cache
        return service

    def override_get_stats_service():
        repo = ComplaintRepository(db_session)
        service = StatsService(repo)
        service.cache = mock_cache
        return service

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_complaint_service] = override_get_complaint_service
    app.dependency_overrides[get_stats_service] = override_get_stats_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
