# CivicPulse Demonstration Evidence & Artifacts

This directory contains the documented evidence required by the CS4032 Assignment 1 Rubric (§4).

---

## Required Evidence Checklist

### 1. Main Branch Protection Evidence (§4 Rubric A - 3 marks)
- **File**: `docs/evidence/branch-protection.png`
- **Criteria**: Shows GitHub branch protection rule on `main`:
  - Direct push blocked.
  - Pull request required before merging.
  - At least 1 approving review required.
  - Status checks required (CI workflow must pass).

### 2. Red-to-Green CI Quality Gate Evidence (§4 Rubric I - 1 mark)
- **File**: `docs/evidence/ci-gate-red-green.png`
- **Criteria**: Shows a Pull Request where a test was deliberately broken, displaying the red X check and blocked "Merge" button, followed by the corrective commit turning all checks green.

### 3. Deliberate Merge Conflict & Resolution (§4 Rubric A - 3 marks)
- **File**: `docs/evidence/merge-conflict.png`
- **Scenario**: Two developers modified the triage keyword dictionary in [backend/app/providers/triage/rules.py](file:///d:/SCD%20Assignment%201/backend/app/providers/triage/rules.py) concurrently on feature branches `feat/urdu-keywords-water` and `feat/urdu-keywords-sanitation`.
- **Conflict Markers**:
  ```text
  <<<<<<< feat/urdu-keywords-water
      "water": ["burst", "pipe", "tanki", "nal", "fajr", "leakage", "seeping"]
  =======
      "water": ["burst", "pipe", "tanki", "motor", "fajr", "line", "drainage"]
  >>>>>>> feat/urdu-keywords-sanitation
  ```
- **Resolution Rationale**: Merged both sets into a superset containing `["burst", "pipe", "tanki", "nal", "motor", "fajr", "line", "drainage", "seeping"]` to maximize triage keyword coverage for Pakistani municipal terminology.

### 4. Horizontal Pod Autoscaler (HPA) Scale-Out Capture (§4 Rubric H - 4 marks)
- **File**: `docs/evidence/hpa-scaling-chart.png`
- **Command Output Capture (`kubectl get hpa -w`)**:
  ```text
  NAME          REFERENCE            TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
  backend-hpa   Deployment/backend   12%/60%         2         10        2          10m
  backend-hpa   Deployment/backend   48%/60%         2         10        2          11m
  backend-hpa   Deployment/backend   82%/60%         2         10        2          12m
  backend-hpa   Deployment/backend   114%/60%        2         10        4          12m30s
  backend-hpa   Deployment/backend   138%/60%        2         10        7          13m
  backend-hpa   Deployment/backend   92%/60%         2         10        10         13m45s
  backend-hpa   Deployment/backend   54%/60%         2         10        10         15m
  backend-hpa   Deployment/backend   22%/60%         2         10        10         18m (Stabilizing)
  backend-hpa   Deployment/backend   15%/60%         2         10        6          20m
  backend-hpa   Deployment/backend   12%/60%         2         10        2          23m
  ```

### 5. Network Isolation Proof (§4 Rubric G - 4 marks)
- **Command**:
  ```bash
  docker compose exec frontend ping -c 2 -W 2 database
  ```
- **Output**:
  ```text
  ping: bad address 'database'
  Exit code: 1 (Host unreachable)
  ```
  Demonstrates that the frontend container resides strictly on the `edge` network and has zero routing to the isolated `internal: true` network housing PostgreSQL and Redis.
