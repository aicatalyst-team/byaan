.PHONY: setup dev dev-build dev-logs rebuild stop clean hosted hosted-build hosted-logs hosted-stop hosted-rebuild hosted-clean format lint format-check test run-server sync-skills install-hooks

# =============================================================================
# Local/Community development (default, SQLite, ports 17433/17434)
# =============================================================================
setup:
	docker compose build

dev:
	docker compose up

dev-detach:
	docker compose up -d

dev-build:
	docker compose build
	docker compose up

rebuild:
	docker compose down -v
	docker compose build --no-cache
	docker compose up

stop:
	docker compose down

clean:
	docker compose down -v
	docker system prune -f

# =============================================================================
# Self-Hosted development (PostgreSQL, multi-tenant/teams features)
# =============================================================================
COMPOSE_HOSTED = docker compose -f docker-compose.hosted.yml -p byaan-hosted

hosted:
	$(COMPOSE_HOSTED) up -d

hosted-build:
	$(COMPOSE_HOSTED) build
	$(COMPOSE_HOSTED) up -d

hosted-logs:
	$(COMPOSE_HOSTED) up

hosted-stop:
	$(COMPOSE_HOSTED) down

hosted-rebuild:
	$(COMPOSE_HOSTED) down -v
	$(COMPOSE_HOSTED) build --no-cache
	$(COMPOSE_HOSTED) up

hosted-clean:
	$(COMPOSE_HOSTED) down -v

# =============================================================================
# Python formatting and linting commands
# =============================================================================
format:
	@echo "Formatting Python code with Ruff..."
	cd server && uv run ruff format .
	cd server && uv run ruff check --fix .

lint:
	cd server && uv run ruff check .

format-check:
	cd server && uv run ruff format --check .
	cd server && uv run ruff check .

test:
	cd server && PYTHONPATH=..:tests uv run pytest

run-server:
	uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8000

# =============================================================================
# Skills sync (.claude/skills -> .agents/skills for Codex/Gemini compatibility)
# =============================================================================
sync-skills:
	@rsync -a --delete .claude/skills/ .agents/skills/
	@if [ -d "$$HOME/.codex/skills" ]; then \
		rsync -a --delete .claude/skills/ "$$HOME/.codex/skills/"; \
		echo "Skills synced: .claude/skills -> .agents/skills, $$HOME/.codex/skills"; \
	else \
		echo "Skills synced: .claude/skills -> .agents/skills"; \
	fi

install-hooks:
	@cp scripts/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed"
