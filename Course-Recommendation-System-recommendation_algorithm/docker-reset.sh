#!/usr/bin/env bash
# Make executable once: chmod +x docker-reset.sh

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "[docker-reset] Stopping containers and removing volumes (pgdata + pgadmin_data)..."
docker compose down -v 2>/dev/null || docker-compose down -v

echo "[docker-reset] Starting fresh stack..."
docker compose up -d 2>/dev/null || docker-compose up -d

echo ""
echo "Waiting for Postgres to become healthy..."
until [[ "$(docker inspect --format '{{.State.Health.Status}}' course_db 2>/dev/null || echo unknown)" == "healthy" ]]; do
  sleep 2
done

echo ""
echo "Done."
echo "  Postgres (host): 127.0.0.1:5433  user=admin  password=password123  db=course_recommender"
echo "  pgAdmin:         http://localhost:8080  login=admin@admin.com / admin"
echo "  pgAdmin DB host: db  port 5432  (Docker internal)"
echo ""
echo "Next: cd server && ./seed.sh"
