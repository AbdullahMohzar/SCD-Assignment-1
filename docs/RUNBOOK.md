# CivicPulse Operations Runbook

This runbook provides actionable procedures for deploying, maintaining, debugging, and rolling back the CivicPulse platform across local Docker and Kubernetes environments.

---

## 1. Deployment Procedures

### 1.1 Local Docker Compose (One-Command Startup)
To bring up the entire stack with isolated networks and seeded complaints:
```bash
# 1. Copy template and configure environment (if needed)
cp .env.example .env

# 2. Launch stack in background
docker compose up -d --build

# 3. Apply database migrations
docker compose exec backend alembic upgrade head

# 4. Run idempotent seed command (32 realistic complaints)
docker compose exec backend python seeds/seed_complaints.py

# 5. Verify system readiness
curl -i http://localhost:8000/ready
```
The frontend is reachable at `http://localhost:80` and the backend API at `http://localhost:8000/api/docs`.

### 1.2 Kubernetes Deployment via Kustomize
Deploying to a local Kind/k3d cluster or staging cluster:
```bash
# 1. Create civicpulse namespace and apply base manifests
kubectl apply -k k8s/overlays/dev

# 2. Verify all pods are running and healthy
kubectl get pods -n civicpulse -w

# 3. Port-forward frontend service to inspect UI
kubectl port-forward svc/frontend 8080:80 -n civicpulse
```

---

## 2. Rollback Mechanisms

CivicPulse supports two distinct rollback procedures depending on the operational severity:

### 2.1 Fast Imperative Rollback (The 3 A.M. Incident Response)
When an active production outage requires immediate mitigation without waiting for a CI/CD build run:
```bash
# Immediately rolls back the backend deployment to the previous replica revision
kubectl rollout undo deployment/backend -n civicpulse

# Monitor rollback status in real time
kubectl rollout status deployment/backend -n civicpulse

# Verify previous healthy image is actively serving requests
kubectl get pods -n civicpulse -l app.kubernetes.io/name=backend -o wide
```
*When to use*: Active service outage, crash loops, or severe error spikes in production where every second of downtime counts.

### 2.2 Declarative GitOps Rollback (The Auditable Post-Incident Fix)
Once the immediate fire is extinguished, reconcile Git state to maintain an accurate audit log:
```bash
# 1. Identify previous known good commit SHA
git log --oneline -n 5

# 2. Update Kustomize image tag to the prior commit SHA
cd k8s/overlays/prod
kustomize edit set image ghcr.io/civicpulse/backend=ghcr.io/civicpulse/backend:<PREVIOUS_GOOD_SHA>

# 3. Commit and push rollback to main
git commit -am "fix(rollback): revert backend image to <PREVIOUS_GOOD_SHA>"
git push origin main
```
*When to use*: Post-incident permanent resolution to ensure cluster state matches version control history.

---

## 3. Reading and Filtering Structured JSON Logs

CivicPulse writes structured JSON logs directly to `stdout`. Every log line includes timestamps, severity, `request_id`, duration, and endpoints.

### Inspecting Backend Logs in Real Time
```bash
# Docker Compose: stream backend logs
docker compose logs -f backend

# Kubernetes: stream logs from all backend pods
kubectl logs -n civicpulse -l app.kubernetes.io/name=backend -f --tail=100
```

### Filtering Specific Request Traces
To trace a specific citizen request across the entire request lifecycle using `jq`:
```bash
kubectl logs -n civicpulse -l app.kubernetes.io/name=backend | jq 'select(.request_id == "TARGET_REQUEST_ID")'
```

### Inspecting Triage Fallbacks and Errors
Filter for fallback events where external AI failed and rules stepped in:
```bash
kubectl logs -n civicpulse -l app.kubernetes.io/name=backend | jq 'select(.levelname == "WARNING" and (.message | contains("fallback")))'
```

---

## 4. Incident Response: Triage Failure Troubleshooting

### Symptoms
- `/api/meta/providers` reports `fallback: true` on recent complaints.
- Metrics show rising counter for `civicpulse_triage_fallback_total`.
- Backend logs show `WARNING: Triage fallback triggered`.

### Diagnostic Steps
1. **Check Provider Health & Limits**:
   Query the metadata endpoint to inspect recent outcome latencies:
   ```bash
   curl -s http://localhost:8000/api/meta/providers | jq .
   ```
2. **Inspect Error Class in Logs**:
   Look for `error_class` in log outputs:
   - `RateLimitError` / `429`: Daily or per-minute token quota on Groq/Gemini has been exhausted.
   - `TimeoutError`: LLM endpoint latency exceeded the 10-second hard timeout.
   - `ValidationError`: Model returned malformed or unexpected JSON schema.
3. **Emergency Mitigations**:
   - **Switch to Rule-Based Triage (Immediate zero-cost stabilization)**:
     ```bash
     kubectl set env deployment/backend -n civicpulse TRIAGE_PROVIDER=rules
     ```
   - **Switch to Offline Ollama Container**:
     ```bash
     kubectl set env deployment/backend -n civicpulse TRIAGE_PROVIDER=llm:ollama
     ```
   - **Rotate API Keys**:
     If quota is exhausted, update the Kubernetes secret or `.env` with a fresh developer key and trigger rolling restart:
     ```bash
     kubectl rollout restart deployment/backend -n civicpulse
     ```

---

## 5. Persistence & Network Isolation Verification

### Verifying Database Persistence across Teardown
```bash
# 1. Verify complaint count
curl -s http://localhost:8000/api/stats | jq .total

# 2. Teardown containers (without deleting named volume)
docker compose down

# 3. Re-launch containers
docker compose up -d

# 4. Verify data survived intact
curl -s http://localhost:8000/api/stats | jq .total
```

### Verifying Network Isolation (Frontend Cannot Reach DB)
```bash
# This command MUST fail with exit code 1 or timeout:
docker compose exec frontend ping -c 2 -W 2 database
```

---

## 6. On-Call Quick Diagnostic Checklist

| Subsystem | Health Probe Command | Expected Healthy Output |
| :--- | :--- | :--- |
| **Backend API** | `curl -s http://localhost:8000/health` | `{"status":"alive"}` |
| **Dependencies** | `curl -s http://localhost:8000/ready` | `{"status":"ready", ...}` |
| **PostgreSQL** | `docker compose exec database pg_isready -U civicpulse_user` | `accepting connections` |
| **Redis Cache** | `docker compose exec cache redis-cli ping` | `PONG` |
| **K8s Workloads** | `kubectl get pods -n civicpulse` | `Running (Ready: 1/1)` |
| **HPA Status** | `kubectl get hpa -n civicpulse` | `Target: <utilization>/60%` |

