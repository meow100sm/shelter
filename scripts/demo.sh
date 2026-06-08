#!/usr/bin/env bash
set -euo pipefail

# Cross-platform-ish (Linux/macOS) helper to start/stop demo stack via Docker.
# Usage:
#   ./scripts/demo.sh            # start
#   ./scripts/demo.sh --superuser  # start and create superuser
#   ./scripts/demo.sh --down       # stop

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

CREATE_SUPERUSER=false
DOWN=false

for arg in "$@"; do
  case "$arg" in
    --superuser) CREATE_SUPERUSER=true ;;
    --down) DOWN=true ;;
    *) echo "Unknown arg: $arg"; exit 2 ;;
  esac
done

if [[ "$DOWN" == true ]]; then
  echo "Stopping containers..."
  docker compose down
  exit 0
fi

echo "Starting PawCare (Docker)..."
docker compose up -d --build

echo "Open: http://127.0.0.1:8000/"

if [[ "$CREATE_SUPERUSER" == true ]]; then
  echo "Creating Django superuser (interactive)..."
  docker compose run --rm web python manage.py createsuperuser
fi
