# ADR 0002: Frontend Runtime Configuration via Reverse Proxy Architecture

## Status
Accepted

## Context
In modern Single Page Application (SPA) workflows using Vite/React, environment variables like `VITE_API_URL` are evaluated during the build step (`npm run build`) and statically inlined into bundled JavaScript files. 

If the frontend bundle hardcodes an absolute backend URL (such as `http://localhost:8000` or `http://backend:8000`), the resulting container image is strictly bound to that single environment. This violates the core DevOps principle of **Build Once, Deploy Many** (Twelve-Factor App §X), forcing teams to re-compile new container images for staging, testing, and production clusters.

## Decision
We decided to adopt the **Nginx Reverse Proxy Architecture** (`location /api/`) rather than baking URLs or generating `/config.js` scripts:

1. **Relative Client Routing**: The React frontend API client (`frontend/src/api/client.ts`) exclusively issues HTTP calls to relative endpoint paths starting with `/api` (e.g., `fetch('/api/complaints')`).
2. **Nginx Container Routing**: In Docker environments, Nginx listens on port 80 and reverse-proxies all requests destined for `/api/` upstream to `http://backend:8000/api/` across the internal Docker bridge network (`edge`).
3. **Kubernetes Ingress Routing**: In Kubernetes deployments, the Ingress controller terminates external traffic and routes `/api` directly to the `backend` ClusterIP service while routing `/` to the `frontend` service.

## Consequences
- **Positive**:
  - The frontend container image contains zero environment-specific URLs or secrets.
  - A single container image built in CI can be promoted without rebuild through dev, staging, and production.
  - Completely eliminates Cross-Origin Resource Sharing (CORS) pre-flight overhead in browser communication because frontend assets and API endpoints share the same origin.
  - Transparently passes tracing headers (`X-Request-ID`, `X-Forwarded-For`) to backend services.
- **Negative**:
  - Requires local development setups to configure Vite's development proxy server (`vite.config.ts`) to forward `/api` to the backend process.
