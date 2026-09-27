# CivicPulse AI Usage & Attribution Disclosure (§5.5)

In accordance with course academic honesty policies (§5.5), this document transparently discloses all AI tools used during the design, implementation, and verification of CivicPulse, detailing what was AI-generated, human-guided, and manually modified.

---

## 1. Tools Employed
- **Google DeepMind Antigravity / Gemini 3.8 Flash**: Primary pair-programming agent for architectural scaffolding, Dockerfile multi-stage optimization, K8s manifests, Vitest tests, and Pytest coverage suites.
- **Groq API (Llama 3.1 8B Instant)**: Production hosted runtime LLM for real-time natural language municipal complaint triage.

---

## 2. Component-by-Component Attribution

### 2.1 Backend Layer (`backend/app/`)
- **Generated**: Initial FastAPI route signatures, Pydantic schemas, and SQLAlchemy model scaffolding.
- **Human Modification & Rationale**:
  - Rewrote the dependency injection layer ([app/dependencies.py](file:///d:/SCD%20Assignment%201/backend/app/dependencies.py)) to strictly enforce the architectural requirement that routes must **never** open a direct database session (`AsyncSession`).
  - Added the custom exception handler for `RequestValidationError` in [app/main.py](file:///d:/SCD%20Assignment%201/backend/app/main.py) to guarantee the required field-level error body format (`{ "detail": "...", "errors": [...] }`).
  - Implemented the explicit dictionary transition table in [app/services/state_machine.py](file:///d:/SCD%20Assignment%201/backend/app/services/state_machine.py) to avoid brittle `if/else` checks.

### 2.2 AI Triage & Resilience (`backend/app/providers/triage/`)
- **Generated**: Base protocol interface and prompt strings.
- **Human Modification & Rationale**:
  - Implemented the prompt-injection defense wrapper in [llm.py](file:///d:/SCD%20Assignment%201/backend/app/providers/triage/llm.py) using `<complaint_text>` delimiters to prevent instruction overrides.
  - Implemented single-jittered retry logic that explicitly excludes HTTP 400 client errors (which must never be retried).
  - Designed the deterministic fallback test in [tests/test_fallback.py](file:///d:/SCD%20Assignment%201/backend/tests/test_fallback.py) using `SimulatedTriage(failure_mode="raise")`.

### 2.3 Frontend Layer (`frontend/src/`)
- **Generated**: Basic component boilerplate for React 18 + Vite.
- **Human Modification & Rationale**:
  - Enforced Nginx reverse-proxying in [nginx.conf](file:///d:/SCD%20Assignment%201/frontend/nginx.conf) and relative paths in [api/client.ts](file:///d:/SCD%20Assignment%201/frontend/src/api/client.ts) to guarantee runtime configurability without rebuild.
  - Added live `X-Cache` telemetry badge rendering in [pages/StatsPage.tsx](file:///d:/SCD%20Assignment%201/frontend/src/pages/StatsPage.tsx).
  - Surfaced the exact server 409 error message verbatim in [pages/DashboardPage.tsx](file:///d:/SCD%20Assignment%201/frontend/src/pages/DashboardPage.tsx).

### 2.4 DevOps & Kubernetes (`k8s/`, `compose.yaml`, `.github/`)
- **Generated**: Initial YAML templates for Kubernetes objects.
- **Human Modification & Rationale**:
  - Converted PostgreSQL from a Deployment to a `StatefulSet` with `volumeClaimTemplates` to prevent state loss.
  - Configured `internal: true` on Docker Compose network to provably prevent frontend from communicating with the database.
  - Pinned all container images by exact version tags to avoid unpredictable `:latest` regressions.
  - Configured HPA v2 stabilization behavior parameters (`stabilizationWindowSeconds: 300` on scale-down, `0` on scale-up).
