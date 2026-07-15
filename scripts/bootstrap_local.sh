#!/usr/bin/env bash
# One-command local dev bootstrap: start the stack and run migrations.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it with your API keys before continuing."
fi

docker compose -f infra/docker-compose.yml up -d --build

echo "Waiting for Postgres to be ready..."
until docker compose -f infra/docker-compose.yml exec -T postgres pg_isready -U fingpt > /dev/null 2>&1; do
  sleep 1
done

echo "Running Alembic migrations..."
docker compose -f infra/docker-compose.yml exec -T api alembic upgrade head

echo "Ready! API docs: http://localhost:8000/docs"
