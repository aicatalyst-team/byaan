#!/bin/bash
set -e

SERVICE_TYPE=${1:-server}
shift

case "$SERVICE_TYPE" in
    server)
        echo "=== Starting server initialization ==="
        cd /app/server

        mkdir -p .data

        echo "Running database migrations..."
        uv run --frozen --no-sync alembic upgrade head 2>&1

        MIGRATION_EXIT_CODE=$?
        if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
            echo "Migrations up to date"
        else
            echo "Migration failed with exit code: $MIGRATION_EXIT_CODE"
            echo "Server will start but may have database issues"
        fi

        echo "=== Starting server application ==="
        cd /app
        export SKIP_STARTUP_MIGRATIONS=true

        if [ "$VITE_DEV_MODE" = "true" ]; then
            echo "Starting server in DEVELOPMENT mode (hot reload enabled)..."
            exec uv run --frozen --no-sync --directory server uvicorn server.main:app --host 0.0.0.0 --port 8000 --no-server-header --reload "$@"
        else
            echo "Starting server in PRODUCTION mode..."
            exec uv run --frozen --no-sync --directory server uvicorn server.main:app --host 0.0.0.0 --port 8000 --no-server-header --workers 4 "$@"
        fi
        ;;

    client)
        cd /app

        echo "=== Checking for dependency updates ==="

        NODE_MODULES_DIR="/app/node_modules"
        if [ -x "$NODE_MODULES_DIR/.bin/vite" ]; then
            echo "Node modules already present; skipping pnpm install."
        else
            echo "Running pnpm install to ensure all dependencies are installed..."
            echo | pnpm install --frozen-lockfile --prefer-offline || \
            echo | pnpm install --prefer-offline || \
            echo | pnpm install
        fi

        echo "=== Starting client application ==="
        HOST_PORT="${FRONTEND_PORT:-5173}"
        echo ""
        echo "  App available at: http://localhost:${HOST_PORT}/"
        echo ""
        if [ "$VITE_DEV_MODE" = "true" ]; then
            echo "Starting client in DEVELOPMENT mode (Vite dev server)..."
            exec pnpm run dev --host 0.0.0.0 --port 5173 "$@"
        else
            echo "Starting client in PRODUCTION mode..."
            exec pnpm run preview --host 0.0.0.0 --port 5173 "$@"
        fi
        ;;

    *)
        echo "Unknown service type: $SERVICE_TYPE"
        exit 1
        ;;
esac
