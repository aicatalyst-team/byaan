# PoC Plan: Byaan

## Project Classification
- **Type:** llm-app
- **Key Technologies:** Python 3.11, FastAPI, LiteLLM, OpenAI Agents SDK, MCP (Model Context Protocol), SQLAlchemy, Alembic, PostgreSQL, React/TypeScript (Vite), Tauri, Caddy, DuckDB, SQLGlot, Supervisor
- **ODH Relevance:** Byaan is an AI-powered data agent that leverages LLMs for natural language to SQL translation, interactive dashboards, and contextual data analysis. It demonstrates a production-grade LLM application architecture with multi-provider model support (via LiteLLM), persistent context/learning, and MCP integration — all patterns relevant to the Open Data Hub ecosystem for building intelligent data tooling on OpenShift AI.

## PoC Objectives
What we want to prove:
1. The Byaan self-hosted all-in-one container (PostgreSQL + Python backend + Caddy + frontend) builds and runs successfully on OpenShift/Kubernetes
2. The backend health endpoint is reachable, confirming that FastAPI, database migrations, and internal services initialize correctly
3. The frontend static assets are served via the Caddy reverse proxy and the React app loads in a browser
4. The API layer is functional, accepting requests to key endpoints like `/api/connections` and `/api/llm-connections`
5. An LLM provider connection (via LiteLLM) can be configured, confirming the core AI agent capability is operational

## Infrastructure Requirements
- **Inference Server:** none (Byaan uses LiteLLM to proxy to external LLM providers like OpenAI, Anthropic, etc.)
- **Vector Database:** none (not a RAG pipeline; Byaan uses relational databases for context persistence)
- **Embedding Model:** none
- **GPU Required:** no
- **Persistent Storage:** 5Gi PVC — needed for the embedded PostgreSQL data directory (`/var/lib/postgresql/data`), SQLite fallback data, and any uploaded files
- **Resource Profile:** large (4Gi RAM, 2 CPU) — the container runs PostgreSQL, the Python backend, and Caddy simultaneously via Supervisor; PostgreSQL alone needs meaningful memory
- **Sidecar Containers:** none (all-in-one container includes PostgreSQL + Caddy + backend)

## Test Scenarios

### Scenario 1: Health Check
- **Description:** Verify the backend API is running and healthy after container startup (PostgreSQL initialized, Alembic migrations applied, FastAPI serving)
- **Type:** http
- **Input:** GET `/health`
- **Expected:** Returns 200 OK. The docker-compose healthcheck confirms this endpoint exists and is used for readiness.
- **Timeout:** 120 seconds (PostgreSQL initialization + migrations can take time on first boot)

### Scenario 2: Frontend Load
- **Description:** Verify that Caddy serves the pre-built React frontend static assets at the root URL
- **Type:** http
- **Input:** GET `/`
- **Expected:** Returns 200 OK with HTML content. The response should contain React app shell markup (e.g., `<div id="root">` or references to Vite-built JS bundles).
- **Timeout:** 30 seconds

### Scenario 3: Database Connections API
- **Description:** Verify the connections management API is functional
- **Type:** http
- **Input:** GET `/api/connections`
- **Expected:** Returns 200 OK with a JSON array (empty on fresh deployment, but the endpoint should respond correctly). This confirms SQLAlchemy session management and the connections repository are working.
- **Timeout:** 30 seconds

### Scenario 4: LLM Connections API
- **Description:** Verify the LLM provider connections API is functional
- **Type:** http
- **Input:** GET `/api/llm-connections`
- **Expected:** Returns 200 OK with a JSON response listing available/configured LLM providers. This confirms the LiteLLM integration layer is initialized.
- **Timeout:** 30 seconds

## Dockerfile Considerations

The project already has a well-structured `Dockerfile.self-hosted` that should be used as the basis. It is a multi-stage build:

1. **Stage 1 (frontend-builder):** Builds the React frontend using Node 20 + pnpm, producing static assets
2. **Stage 2 (python-builder):** Installs Python dependencies using `uv` with the lockfile
3. **Stage 3 (runtime):** Python 3.11-slim with PostgreSQL 15, Caddy, Supervisor installed; copies built frontend assets, Python virtualenv, backend code, and configuration

Key points for the containerize agent:
- **Use the existing `Dockerfile.self-hosted`** — it is production-ready and handles the complex multi-service setup
- The container listens on **port 80** (Caddy handles TLS termination and proxying). Add `EXPOSE 80`.
- The entrypoint is `docker/self-hosted/entrypoint.sh` which initializes PostgreSQL, runs migrations, and starts Supervisor (which manages PostgreSQL, the Python backend, and Caddy)
- The container needs the `ENCRYPTION_KEY` environment variable set (used for encrypting stored database credentials)
- `APP_MODE` should be set to `self-hosted`
- The container runs multiple processes via Supervisor — this is intentional for a self-hosted all-in-one deployment
- PostgreSQL data is stored at `/var/lib/postgresql/data` — this should be backed by a PVC for persistence
- The Caddy reverse proxy configuration is templated from `docker/self-hosted/Caddyfile.template`

## Deployment Considerations

Deploy as a **Kubernetes Deployment** with 1 replica:

- **Create a Service** on port 80 (the Caddy reverse proxy port). Caddy routes `/api/*` to the FastAPI backend (port 8000 internally) and serves frontend static files for all other paths.
- **PVC:** Mount a 5Gi PersistentVolumeClaim at `/var/lib/postgresql/data` for PostgreSQL data persistence. Without this, all data is lost on pod restart.
- **Readiness Probe:** HTTP GET `/health` on port 80, with an initial delay of 60 seconds (PostgreSQL init + migrations) and a period of 10 seconds
- **Liveness Probe:** HTTP GET `/health` on port 80, with an initial delay of 90 seconds
- **Environment Variables:**
  - `ENCRYPTION_KEY` — Required secret. Used to encrypt database connection credentials at rest. Generate with `openssl rand -hex 32`.
  - `APP_MODE=self-hosted` — Activates self-hosted mode with embedded PostgreSQL
  - `OPENAI_API_KEY` — Required if using OpenAI as the LLM provider (the default). This is used by LiteLLM to proxy requests to the LLM.
  - `BYAAN_DEFAULT_LLM_PROVIDER` — Optional, defaults to `openai`
  - `BYAAN_DEFAULT_LLM_MODEL` — Optional, defaults vary by provider
- **Security Context:** The container needs to run as root (or with specific user setup) because it manages PostgreSQL and Supervisor. On OpenShift, a SecurityContextConstraint (SCC) that allows this may be needed, or the Dockerfile should be adapted to use an unprivileged PostgreSQL setup.
- **Test via HTTP:** All test scenarios use HTTP requests to the Service endpoint. Send GET requests to `/health`, `/`, `/api/connections`, and `/api/llm-connections` and verify 200 responses.
- **Resource Requests:** 2 CPU, 4Gi RAM (minimum for running PostgreSQL + Python backend + Caddy concurrently). Resource limits: 4 CPU, 8Gi RAM.
- **Note on port:** Even though the docker-compose dev setup uses port 8000 for the backend and 5173 for the frontend separately, the self-hosted all-in-one container exposes only port 80 via Caddy, which reverse-proxies both.