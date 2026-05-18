<p align="center">
  <img src="assets/logo.png" alt="Byaan" width="120" />
</p>

<h1 align="center">Byaan</h1>

<p align="center">
  <strong>The AI data agent that actually learns your databases.</strong><br/>
  <sub>Ask questions in plain English, get interactive dashboards. Bring your own models. Keep your databases private.</sub>
</p>

<p align="center">
  <a href="docs/licensing.md"><img src="https://img.shields.io/badge/license-MIT%20%2B%20ELv2-blue.svg" alt="MIT and Elastic License 2.0" /></a>
  <a href="https://github.com/byaan-ai/byaan/releases"><img src="https://img.shields.io/github/v/release/byaan-ai/byaan" alt="Latest Release" /></a>
  <a href="https://hub.docker.com/r/byaan/self-hosted"><img src="https://img.shields.io/docker/pulls/byaan/self-hosted" alt="Docker Pulls" /></a>
  <a href="https://www.byaan.ai"><img src="https://img.shields.io/badge/website-byaan.ai-orange" alt="Website" /></a>
</p>

<p align="center">
  <a href="https://www.byaan.ai">Website</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="docs/self-hosted/README.md">Self-Hosted Docs</a> &middot;
  <a href="docs/security/read-only-guardrails.md">Read-Only Guardrails</a> &middot;
  <a href="docs/security/github-actions-hardening.md">Actions Hardening</a> &middot;
  <a href="CONTRIBUTING.md">Contributing</a> &middot;
  <a href="https://github.com/byaan-ai/byaan/issues">Issues</a>
</p>

<br />

<p align="center">
  <video
    src="https://github.com/user-attachments/assets/b2ffe92e-99b6-4ad9-8337-8a199da7c81c"
    autoplay
    loop
    muted
    playsinline
    width="800"
    poster="assets/hero.png"
  ></video>
</p>

---

## What is Byaan?

Most AI data tools fail for three reasons:

1. **They lack business context.** What does "revenue" mean at your company? Which transactions to exclude? What's the fiscal year? Generic AI doesn't know.
2. **They pick the wrong tables.** With dozens of data sources, AI guesses — and guesses wrong.
3. **They don't learn.** Every session starts from scratch. Same question, same mistakes.

Byaan solves this by building persistent context around your data. It auto-discovers your schema, learns your metric definitions and business rules, and stores that knowledge so every conversation builds on the last. Connect it to your GitHub repos and it learns your codebase context too.

The result is an agent that can accumulate your data's tribal knowledge instead of treating every conversation as a stateless text-to-SQL prompt.

We believe your databases should stay private: on your laptop or within your organization's infrastructure. Byaan runs as a native Mac app or a self-hosted Docker container. In local and community deployments, Byaan connects directly to the model providers you configure instead of routing database traffic through Byaan-hosted infrastructure.

## Key Features

- **Multi-database support** — PostgreSQL, MongoDB, MySQL, SQLite, MSSQL, ODBC, plus CSV/Excel/Parquet/JSON file uploads
- **Local file analysis** — DuckDB-powered analytical queries over CSV, Excel, Parquet, and JSON files, subject to local machine resources
- **Natural language to SQL, Mongo, or other databases** — ask questions about your data, inspect generated queries, and review results
- **Interactive dashboards** — AI-generated charts and tables with dynamic filters and live data
- **Bring Your Own Model** — Claude, OpenAI, Azure OpenAI, AWS Bedrock, Groq, OpenRouter, xAI
- **Read-only guardrails** — explicit validation layers block known write operations across SQL, MongoDB, DynamoDB, and DuckDB flows
- **MCP Server** — works with Claude Code, Cursor, and other MCP-compatible tools
- **Dashboard exports** — standalone HTML dashboards, PDFs, or shareable links
- **Secure API skills** — connect third-party APIs with built-in secrets management and domain whitelisting — the agent only calls endpoints you explicitly approve
- **Scheduled queries** — automate recurring reports and analyses
- **Desktop app** — download the Mac app and analyze data from your own machine

## Quick Start

<p><a href="#mac-app"><img src="https://img.shields.io/badge/Mac_App-Download-blue?style=for-the-badge" /></a></p>
<p><a href="#community-version"><img src="https://img.shields.io/badge/Community_Version-Docker-green?style=for-the-badge" /></a></p>
<p><a href="#team-version"><img src="https://img.shields.io/badge/Team_Version-Docker-orange?style=for-the-badge" /></a></p>

| You want… | Use this |
|---|---|
| Byaan on my Mac, just for me | [Mac App](#mac-app) |
| Byaan in Docker, single shared instance, no auth | [Community Version](#community-version) |
| Byaan for my team — auth, RBAC, Slack, HTTPS | [Team Version](#team-version) ← most teams want this |

---

### Mac App

Download Byaan for macOS from the [latest release](https://github.com/byaan-ai/byaan/releases) or from [byaan.ai](https://www.byaan.ai).

Open the app, connect a database, and start asking questions. No account needed — configure your preferred LLM provider from within the app.

---

### Community Version

**Docker (fastest)**

```bash
git clone https://github.com/byaan-ai/byaan.git
cd byaan
docker compose up -d
```

Open http://localhost:17434 and start querying.

**Development**

```bash
git clone https://github.com/byaan-ai/byaan.git
cd byaan
make setup        # Build Docker images (community/SQLite version)
make dev          # Start backend (port 17433) + frontend (port 17434) with logs
make dev-detach   # Start in background
make stop         # Stop services
```

If you use Claude Code, Cursor, Codex CLI, or Gemini CLI, run `/byaan:start` to automate the full setup: it installs dependencies, frees ports, starts services, analyzes your codebase, and configures MCP. Run `/byaan:learn` after schema changes to re-analyze.

| Command | What it does |
| --- | --- |
| `make setup` | Build Docker images (community version) |
| `make dev` | Start community version (SQLite, ports 17433/17434) with logs |
| `make dev-detach` | Start community version in background |
| `make stop` | Stop community version |
| `/byaan:start` | Full onboarding (dependencies, services, MCP, codebase analysis) |
| `/byaan:learn` | Re-analyze codebase after schema changes |

---

### Team Version

<p align="center">
  <video
    src="https://github.com/user-attachments/assets/e3c79173-bf57-4242-b8f1-51c735299e31"
    autoplay
    loop
    muted
    playsinline
    width="800"
  ></video>
</p>

The full multi-user deployment. One container ships PostgreSQL, the FastAPI backend, the React frontend, and Caddy. Live on port 8080 in five minutes.

**Requirements:** Linux server (Ubuntu 20.04+, Debian 11+, or any Docker-compatible OS), 2 GB RAM (4 GB recommended), 10 GB disk, Docker installed, ports 80/443 (or 8080) free.

**1. Install** — drops `start.sh` and `.env` into a `byaan` directory:

```bash
curl -fsSL https://downloads.byaan.ai/docker/install.sh | bash
cd byaan
```

**2. Configure** — open `.env` and set the four required values. `APP_SECRET` is auto-generated.

```bash
MASTER_USER_EMAIL=admin@yourcompany.com
MASTER_USER_PASSWORD=<8+ characters>
ORG_NAME=YourCompany
DOMAIN=app.yourcompany.com   # optional — enables Let's Encrypt HTTPS
```

**3. Start:**

```bash
./start.sh
```

Open `http://your-server:8080` (or your `DOMAIN`). Sign in as the master admin you just configured, then invite teammates from **Settings → Members → Invite**.

> **Note:** SMTP is optional. Without it, invitations are still created and the admin shares the generated link manually from the Members page. To send invitation emails automatically, add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_USE_TLS` to `.env`. See [`docs/self-hosted/env.example`](docs/self-hosted/env.example) for the full reference.

**What you get:**

- Multi-user auth with invitations and RBAC roles (SMTP optional — share invitation links manually if email isn't configured)
- Slack integration — add `@byaan` to any channel, answers post in-thread
- Optional Google OAuth SSO (drop in client ID + secret)
- Automatic HTTPS via Let's Encrypt when `DOMAIN` is set
- Blue-green zero-downtime updates: `./start.sh update`
- All data in a single Docker volume — easy `pg_dump` backups

**Common commands:**

| Command | What it does |
| --- | --- |
| `./start.sh` | Start Byaan |
| `./start.sh stop` | Stop Byaan |
| `./start.sh update` | Pull latest image and recreate container (blue-green, zero-downtime) |
| `./start.sh status` | Check if running |
| `./start.sh logs` | Tail logs from all services |
| `./start.sh logs backend` | Tail FastAPI backend logs |
| `./start.sh logs caddy` | Tail Caddy reverse-proxy logs |
| `./start.sh logs postgres` | Tail PostgreSQL logs |
| `./start.sh remove` | Remove container, keep data volume |
| `./start.sh remove --data` | Remove container and wipe all data |

Full reference: [docs/self-hosted/README.md](docs/self-hosted/README.md).

**Development (contributors):**

```bash
make hosted-build # Build images and start hosted version (ports 8000/5173) in background
make hosted       # Start hosted version in background
make hosted-logs  # Start with visible logs
make hosted-stop  # Stop hosted services
```

| Command | What it does |
| --- | --- |
| `make hosted-build` | Build images and start hosted version (PostgreSQL, ports 8000/5173) in background |
| `make hosted` | Start hosted version (PostgreSQL, ports 8000/5173) in background |
| `make hosted-logs` | Start hosted version with logs |
| `make hosted-stop` | Stop hosted version |

Open http://localhost:5173 (frontend) or http://localhost:8000 (backend API).

## MCP Integration (Model Context Protocol)

Byaan exposes an MCP interface that lets AI coding assistants query your connected databases through natural language. MCP clients talk to your local or hosted Byaan instance; model-provider requests follow the provider configuration you choose in Byaan.

### How it works

1. Open Byaan and connect your databases (Datasources page)
2. Configure an AI model (Profile menu > AI Models)
3. Add the MCP server to your AI client using the instructions below

### Desktop App (stdio)

The desktop app bundles an MCP stdio server. No API key needed — it connects directly to your local database. The bundled binary auto-detects its database and configuration.

You can copy the config from the MCP icon in the app, or use the examples below. The binary is at `~/Library/Application Support/com.byaan.desktop/runtime/current/backend/backend` (the `runtime/current` symlink is updated automatically on each app launch).

**Claude Code:**
```bash
claude mcp add-json byaan '{"type":"stdio","command":"'"$HOME"'/Library/Application Support/com.byaan.desktop/runtime/current/backend/backend","args":["-m","server.mcp.stdio_server"]}' --scope user
```

**Cursor** (`~/.cursor/mcp.json` or `.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "byaan": {
      "command": "~/Library/Application Support/com.byaan.desktop/runtime/current/backend/backend",
      "args": ["-m", "server.mcp.stdio_server"]
    }
  }
}
```

**Codex CLI** (`~/.codex/config.toml`):
```toml
[mcp_servers.byaan]
command = "~/Library/Application Support/com.byaan.desktop/runtime/current/backend/backend"
args = ["-m", "server.mcp.stdio_server"]
```

### Local / Community Mode (stdio)

When running Byaan locally via `make dev`, connect AI assistants using the `uv` command directly. Replace `<project_root>` with your actual Byaan project path (e.g., `/Users/you/byaan`), or copy the config from the MCP setup modal in the app which fills in the path automatically.

**Claude Code:**
```bash
claude mcp add-json byaan '{"type":"stdio","command":"uv","args":["--directory","<project_root>","run","python","-m","server.mcp.stdio_server"]}' --scope user
```

**Cursor** (`~/.cursor/mcp.json` or `.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "byaan": {
      "command": "uv",
      "args": ["--directory", "<project_root>", "run", "python", "-m", "server.mcp.stdio_server"]
    }
  }
}
```

**Codex CLI** (`~/.codex/config.toml`):
```toml
[mcp_servers.byaan]
command = "uv"
args = ["--directory", "<project_root>", "run", "python", "-m", "server.mcp.stdio_server"]
```

### Byaan Cloud (HTTP)

For Byaan's managed cloud at analytics.byaan.ai (not the self-hosted team version), generate an MCP API key (Profile menu > MCP Keys) and use the HTTP endpoint:

| Mode                        | URL                                  |
| --------------------------- | ------------------------------------ |
| Byaan Cloud (analytics.byaan.ai) | `https://analytics.byaan.ai/api/mcp/` |

**Claude Code:**
```bash
claude mcp add-json byaan '{"type":"http","url":"https://analytics.byaan.ai/api/mcp/","headers":{"Authorization":"Bearer YOUR_BYAAN_API_KEY"}}' --scope user
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "byaan": {
      "url": "https://analytics.byaan.ai/api/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_BYAAN_API_KEY"
      }
    }
  }
}
```

**Codex CLI** (`~/.codex/config.toml`):
```toml
[mcp_servers.byaan]
url = "https://analytics.byaan.ai/api/mcp/"
http_headers = { "Authorization" = "Bearer YOUR_BYAAN_API_KEY" }
```

### Testing the connection

After configuring your client, try asking it to "list all tables in my database" or "describe the schema." If Byaan is running, your client will receive results through the MCP tools.

## Running Tests

```bash
# Run backend tests locally
cd server && PYTHONPATH=..:tests uv run pytest

# Run backend tests inside Docker
docker compose exec server uv run pytest
```

## Exporting Demo Notebooks

Export existing notebooks from the database to seed new demo data:

```bash
# 1. Edit the NOTEBOOK_IDS array in the script with your notebook UUIDs
#    Open: server/scripts/export_notebooks_to_demo.py
#    Edit line 39: NOTEBOOK_IDS = ["your-notebook-uuid-here"]

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Run the export script
python3 server/scripts/export_notebooks_to_demo.py
```

This exports all notebook data (datasets, messages, queries, dashboards) into `server/example_data/demo_notebooks.json` and auto-increments the version. On app restart, the system will detect the version change and seed the updated notebooks.

For detailed documentation, see: `server/scripts/README_EXPORT_NOTEBOOKS.md`

## Team Version Deployment

For production team deployments with PostgreSQL, Caddy, authentication, invitations, RBAC, Google OAuth, Slack integration, and shared dashboards, see the [Team Version setup above](#team-version) or the full reference at [docs/self-hosted/README.md](docs/self-hosted/README.md).

For local community development, use `make dev` and open http://localhost:17434.

## What Leaves Your Machine?

In local desktop and community deployments:

- Byaan connects directly to the databases and files you configure.
- Query results and relevant schema/context may be sent to the model provider you configure when an AI workflow needs model assistance.
- Database traffic is not routed through Byaan-hosted infrastructure.
- LLM API keys are configured inside the app, not in environment files.

For hosted or team deployments, review your deployment configuration, model-provider settings, telemetry settings, and organizational policies before connecting production data.

## Security And Read-Only Posture

Byaan is designed for read-only analytical workflows. It includes prompt rules and validation layers that block known write operations across SQL, MongoDB, DynamoDB, and DuckDB execution paths. See [docs/security/read-only-guardrails.md](docs/security/read-only-guardrails.md) for the current implementation details and limits.

For production databases, use a database user with read-only permissions. Application-level guardrails are a defense-in-depth layer, not a replacement for least-privilege database credentials.

## Architecture

### How the Agent Learns

Byaan isn't a stateless wrapper around an LLM. It maintains a persistent context layer that grows with every interaction:

```
  Ask a question
        │
        ▼
┌─────────────────┐    ┌──────────────────────────────────┐
│   Agent Core    │◄───│        Persistent Context        │
│                 │    │                                  │
│  • Parse query  │    │  Schema + annotations            │
│  • Select DB    │    │  Saved queries & patterns        │
│  • Generate SQL │    │  Workspace memory                │
│  • Build charts │    │  User style preferences          │
│                 │    │  Custom skills & API tools       │
└────────┬────────┘    │  GitHub repo knowledge           │
         │             └──────────────┬───────────────────┘
         ▼                            │
  Execute read-only                   │
  query on your DB          ┌─────────┴─────────┐
         │                  │   Learning Loop    │
         ▼                  │                    │
  Dashboard with            │ Corrections → memory
  dynamic filters           │ Queries → saved patterns
         │                  │ Annotations → schema context
         ▼                  │ Skills → reusable tools
  Export HTML / PDF         └────────────────────┘
```

Every correction you make, every successful query, every annotation — it all feeds back into the context for the next conversation. The agent compounds knowledge instead of resetting.

### Context Layers

| Layer                  | What it stores                                                         | How it learns                                                       |
| ---------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Schema annotations** | Table and column descriptions, business meaning, data quality notes    | You annotate or the agent discovers during schema exploration       |
| **Workspace memory**   | Metric definitions, query patterns, data quirks, standing instructions | Agent saves corrections and successful approaches automatically     |
| **Saved queries**      | Past SQL with output schemas, reusable across dashboards               | Every successful query becomes context for future conversations     |
| **Custom skills**      | API integrations, reusable tools, org-shared capabilities              | You create skills with credentials; agent uses them across sessions |
| **GitHub knowledge**   | Codebase structure, language breakdown, repo-linked analysis           | Connected repos are analyzed and fed into the agent's context       |

### Deployment Modes

```
Mac App       Tauri → React 19 + FastAPI + SQLite (all bundled, runs locally)
Self-Hosted   Docker → Caddy + React 19 + FastAPI + PostgreSQL (single container)
MCP Server    Any MCP client → Byaan API (ask_byaan tool over HTTP)
```

**Tech stack:** React 19 &middot; TypeScript &middot; FastAPI &middot; SQLAlchemy &middot; DuckDB &middot; Tauri &middot; Python 3.11+

### MCP Server

Byaan exposes an `ask_byaan` MCP tool that lets external clients query your databases through the agent. Works with Claude Code, Cursor, and any MCP-compatible tool.

Generate an API key in the app, add it to your MCP client config, and your IDE can query your databases through the same Byaan context layer.

## Environment Configuration

Two example environment files are provided:

- **[`.env.example`](.env.example)** — for Docker and local development
- **[`docs/self-hosted/env.example`](docs/self-hosted/env.example)** — for Byaan for Teams deployment (auth, domain, SMTP, OAuth)

Copy the relevant file to `.env` and fill in your values. LLM API keys are configured inside the app, not in environment files.

## Star History

If Byaan is useful to you, consider giving it a star — you'll get notified of new releases automatically.

<!-- Uncomment once you have traction:
[![Star History Chart](https://api.star-history.com/svg?repos=byaan-ai/byaan&type=Date)](https://star-history.com/#byaan-ai/byaan&Date)
-->

## Contributing

Contributions are welcome! Whether it's bug fixes, new features, documentation, or feedback — every bit helps.

1. Fork the repo and create a branch
2. Make your changes
3. Submit a pull request

Look for issues labeled [`good first issue`](https://github.com/byaan-ai/byaan/labels/good%20first%20issue) if you're looking for a place to start.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Community

- [GitHub Issues](https://github.com/byaan-ai/byaan/issues) — bug reports and feature requests
- [GitHub Discussions](https://github.com/byaan-ai/byaan/discussions) — questions and ideas
- [Website](https://www.byaan.ai) — product info and downloads

## Support

For support boundaries, security reporting, and the split between community and teams features, see:

- [SUPPORT.md](SUPPORT.md)
- [SECURITY.md](SECURITY.md)
- [docs/licensing.md](docs/licensing.md)

## Contributors

Created by [Hadi Javeed](https://github.com/hadijaveed), [Usama Javed](https://github.com/raousama391), and [Soha Sarwar](https://github.com/SohaSarwar1).

## Acknowledgements

Byaan is built on the shoulders of excellent open-source projects including [FastAPI](https://github.com/tiangolo/fastapi), [React](https://github.com/facebook/react), [Tauri](https://github.com/tauri-apps/tauri), [DuckDB](https://github.com/duckdb/duckdb), [LiteLLM](https://github.com/BerriAI/litellm), and [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy).

## License

Byaan Community code is [MIT licensed](LICENSE). The `server/ee/` directory contains Byaan for Teams features under the [Elastic License 2.0](server/ee/LICENSE). See [docs/licensing.md](docs/licensing.md) for the practical split between community and teams code.
