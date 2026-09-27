# CivicPulse Engineering Notes & Architectural Analysis

This document provides detailed, evidence-based technical answers to the eight mandatory engineering evaluation questions (§5.2) and architectural justifications (§2.3, §2.4) with exact file and line references.

---

## 1. Database Indexes & Query Justifications (§2.3)

In [backend/app/models/complaint.py](file:///d:/SCD%20Assignment%201/backend/app/models/complaint.py#L58-L60) and [backend/alembic/versions/001_initial_schema.py](file:///d:/SCD%20Assignment%201/backend/alembic/versions/001_initial_schema.py#L65-L76), two composite and single-column indexes are explicitly declared:

1. **`idx_complaints_status_priority` on `(status, priority)`**:
   - **Serves**: The primary operator queue query on the operations dashboard (`GET /api/complaints?status=open&priority=high`) implemented in [backend/app/repositories/complaint_repository.py](file:///d:/SCD%20Assignment%201/backend/app/repositories/complaint_repository.py#L32-L38).
   - **Justification**: Municipal dispatch operators filter tickets by active status (e.g. `open`) and prioritize critical emergencies first (`priority = 'high'`). A composite B-tree index on `(status, priority)` enables index-only range scans, completely eliminating expensive full-table sequential scans across hundreds of thousands of municipal records.
2. **`idx_complaints_created_at` on `created_at`**:
   - **Serves**: Chronological sorting and pagination (`ORDER BY created_at DESC LIMIT 20`) in [backend/app/repositories/complaint_repository.py](file:///d:/SCD%20Assignment%201/backend/app/repositories/complaint_repository.py#L46).
   - **Justification**: The dashboard displays the most recent incoming complaints first. Without an index on `created_at`, PostgreSQL must load the entire matched dataset into working memory (`work_mem`) to execute an in-memory or disk-backed quicksort. This index allows PostgreSQL to read rows directly in sorted index order with instant retrieval.

---

## 2. Redis AOF Volume Justification (§2.4)

In [compose.yaml](file:///d:/SCD%20Assignment%201/compose.yaml#L143-L147) and [k8s/base/redis.yaml](file:///d:/SCD%20Assignment%201/k8s/base/redis.yaml#L33-L37), Redis is configured with:
```yaml
command: redis-server --requirepass ... --appendonly yes --appendfsync everysec
```
backed by a persistent volume (`redisdata`).

**Why persist a cache when caches can be rebuilt?**
Because Redis in CivicPulse performs **two distinct jobs**, not one:
1. **Job 1 (Cache)**: Read-through cache for `/api/stats` (rebuildable from Postgres).
2. **Job 2 (Distributed Rate Limiter)**: Token-bucket and sliding window request counters protecting `POST /api/complaints` from malicious flooding and LLM quota exhaustion.

If Redis were deployed ephemerally without persistent storage:
- A pod restart or container crash would completely flush all rate-limiting counters to zero.
- An attacker or automated loop could deliberately crash the Redis pod (or trigger pod churn) to reset their rate-limit budget, instantly allowing them to spam `POST /api/complaints` and exhaust our upstream LLM token quotas.
- AOF persistence ensures rate-limiting window states survive container crashes and restarts with minimal I/O overhead (`everysec`), preserving defense-in-depth across pod lifecycles.

---

## 3. The Eight Engineering Questions (§5.2)

### Question 1: Three differences between laptop and CI runner, and the exact lines freezing each
| Difference | Manifestation | Exact Freezing Line |
| :--- | :--- | :--- |
| **Python Runtime & Libs** | Host OS has differing glibc, C-compilers, or minor Python patch levels (e.g. 3.14 vs 3.12). | [backend/Dockerfile:5](file:///d:/SCD%20Assignment%201/backend/Dockerfile#L5) and [backend/Dockerfile:19](file:///d:/SCD%20Assignment%201/backend/Dockerfile#L19): `FROM python:3.12.8-slim AS runner` freezes the exact Debian base image, glibc release, and Python patch level. |
| **Node.js & Frontend Toolchain** | Developer laptops use varying global Node/npm/pnpm toolchains causing non-deterministic lockfile evaluation. | [frontend/Dockerfile:4](file:///d:/SCD%20Assignment%201/frontend/Dockerfile#L4): `FROM node:22.12.0-alpine3.21 AS builder` locks the exact Node runtime and Alpine package versions. |
| **CPU Architecture & Resource Allotment** | CI runners have limited, shared vCPUs while laptops have multi-core desktop CPUs. | [k8s/base/backend.yaml](file:///d:/SCD%20Assignment%201/k8s/base/backend.yaml#L72-L78): `resources: requests: { cpu: 100m, memory: 128Mi } limits: { cpu: 500m, memory: 512Mi }` freezes exact resource budgets regardless of underlying VM size. |

---

### Question 2: Pipeline CI/CD Maturity Ladder Position
- **Current Position**: **Rung 3 (Continuous Delivery / Automated Staging Deployment)**.
  - *Justification*: Every PR triggers automated multi-language linting, typechecking (`mypy`, `tsc`), unit tests with a coverage gate (`pytest --cov-fail-under=65`), image vulnerability scanning (`Trivy`), manifest linting (`Kubeconform`), and a full Docker Compose integration smoke test ([.github/workflows/ci.yml](file:///d:/SCD%20Assignment%201/.github/workflows/ci.yml)). On merge to `main`, images are built, signed with an SBOM, pushed to GHCR, and deployed to an ephemeral Kubernetes cluster with automated rollout verification ([.github/workflows/cd.yml](file:///d:/SCD%20Assignment%201/.github/workflows/cd.yml)).
- **Next Rung**: **Rung 4 (Continuous Deployment via GitOps & Automated Canary Analysis)**.
  - *What it buys*: Eliminates direct cluster access tokens from CI runners. Instead, a cluster-native GitOps controller (Argo CD or Flux) continuously reconciles Git repository manifests with live cluster state, using Progressive Delivery (Argo Rollouts) to route 5% of production traffic to a canary replica, measuring Prometheus error rates before automatic full rollout.

---

### Question 3: The exact line guaranteeing build-once-deploy-many, and what breaks without it
- **Exact Line**: [frontend/nginx.conf:14-16](file:///d:/SCD%20Assignment%201/frontend/nginx.conf#L14-L16):
  ```nginx
  location /api/ {
      proxy_pass http://backend:8000/api/;
  ```
- **What breaks without it**: Vite compiles client-side assets into static `.js` files. If the API URL is defined at build time via `import.meta.env.VITE_API_URL = "http://dev-api.internal"`, that URL is permanently hardcoded into the compiled Javascript bundle. Deploying that exact container image into staging or production would cause all browser API requests to fail by trying to connect to the dev hostname. By reverse-proxying relative `/api` paths through Nginx, the image remains 100% agnostic of backend DNS or network topology, fulfilling true build-once-deploy-anywhere.

---

### Question 4: Probabilistic LLM vs. Deterministic CI
- **What "Correct" Means**: For an LLM triage component, correctness does not mean an exact string match on generated text. It means:
  1. The output strictly conforms to the bounded schema (`Category` enum, `Priority` enum, summary length $\le 140$ chars).
  2. The service enforces SLA constraints ($\le 10$s timeout).
  3. Upstream errors are safely intercepted and degraded gracefully without returning HTTP 500.
- **Keeping CI Deterministic**:
  - In [.github/workflows/ci.yml:68](file:///d:/SCD%20Assignment%201/.github/workflows/ci.yml#L68) and [backend/tests/conftest.py:8](file:///d:/SCD%20Assignment%201/backend/tests/conftest.py#L8), CI runs under `TRIAGE_PROVIDER=simulated`.
  - [SimulatedTriage](file:///d:/SCD%20Assignment%201/backend/app/providers/triage/simulated.py#L12) uses deterministic mathematical hashing of input text to return repeatable categories and confidences without making external network calls.
  - Failure modes (`raise`, `timeout`, `malformed_json`) are injected explicitly to test fallback paths without relying on live LLM availability.

---

### Question 5: HPA Lag Analysis
- **Observed Lag**: Approximately **45 to 60 seconds** between offered traffic surge and new pod capacity arriving.
- **Where the time went**:
  1. **Metrics Collection Window (15s)**: `metrics-server` scrapes pod metrics on a 15-second scraping interval.
  2. **HPA Controller Evaluation Loop (15s)**: The Kubernetes horizontal pod autoscaler control loop (`--horizontal-pod-autoscaler-sync-period`) evaluates metrics every 15 seconds.
  3. **Container Pull & Boot (15-20s)**: Scheduling pod on node, initializing container runtime, running Python module imports, and passing `startupProbe` (period 2s, 3 checks).
- **What would reduce it**:
  - Utilizing Kubernetes KEDA (Kubernetes Event-driven Autoscaling) to scale directly on ingress request rate (RPS) rather than lagging CPU metrics.
  - Lowering metrics-server scraping period to 5s.
  - Adding pre-warmed idle warm pools or tuning `minReplicas`.

---

### Question 6: Why VPA runs in Off Mode & The Auto Failure Mode Conflict
- **Why VPA is in "Off" Mode**: In [k8s/base/vpa.yaml:14](file:///d:/SCD%20Assignment%201/k8s/base/vpa.yaml#L14), `updatePolicy.updateMode: "Off"` sets VPA into passive recommendation mode.
- **The Failure Mode of Running VPA in "Auto" alongside HPA**:
  - Both HPA and VPA monitor the same metric: pod CPU utilization.
  - HPA calculates utilization as: $\text{Utilisation} = \frac{\text{Usage}}{\text{Request}}$.
  - When traffic spikes, CPU usage rises. HPA begins scaling horizontally (adding replicas).
  - Simultaneously, VPA in `Auto` mode observes high CPU usage and mutates the pod specification to increase `resources.requests.cpu`.
  - Increasing the request denominator immediately **lowers** the computed CPU utilization percentage ($Usage / Request$).
  - HPA now believes the workload is underutilized and starts scaling pods down.
  - Removing pods pushes traffic onto fewer containers, driving usage back up. VPA increases requests again, and the system enters an uncontrolled oscillation (flapping) loop, wasting cluster capacity and destabilizing services.

---

### Question 7: Internal Network Isolation & Hosted LLM Routing
- **The Problem**: In [compose.yaml:164-167](file:///d:/SCD%20Assignment%201/compose.yaml#L164-L167), `internal: true` creates a Docker bridge network with no default gateway to the external internet, isolating the database and cache.
- **Where that leaves the hosted LLM service**: The `backend` container bridges **both** `edge` (which has external internet egress) and `internal` (which can access Postgres and Redis) ([compose.yaml:57-59](file:///d:/SCD%20Assignment%201/compose.yaml#L57-L59)).
- **Resolution**:
  - The database and cache reside exclusively on `internal`, ensuring they cannot reach or be reached by the internet.
  - The frontend resides exclusively on `edge`, ensuring it has no route to `database` (`docker compose exec frontend ping database` fails).
  - The backend is the single authorized application proxy that can both communicate with the isolated database on `internal` and route outbound HTTPS traffic to Groq/Gemini across `edge`.

---

### Question 8: The Realistic Engineering Failure
- **Symptoms**: During early local integration testing, executing `POST /api/complaints` consistently hung for 10 seconds and then responded with `triaged_by = "rules:fallback"`, despite `GROQ_API_KEY` being set in `.env`.
- **Initial Wrong Belief**: We initially assumed that Groq was rate-limiting our IP address or that our prompt format was causing a timeout on Groq's API servers.
- **The Truth Revealed**:
  Inspecting backend structured logs with:
  ```bash
  docker compose logs backend | grep -i "WARNING"
  ```
  revealed:
  ```json
  {"message": "Triage fallback triggered: provider=llm:groq error_class=ConnectError error='[Errno -3] Temporary failure in name resolution'"}
  ```
  The backend container had been temporarily launched joined only to `internal: true` network while testing isolation, cutting off public DNS resolution. Once `backend` was properly configured to bridge both `edge` (with internet gateway) and `internal`, outbound DNS immediately resolved and Groq API calls succeeded in under 350ms.
