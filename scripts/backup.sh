#!/usr/bin/env bash
set -euo pipefail

# =========================
# PawCare backup script
# - DB dump (PostgreSQL)
# - media/ archive
# - retention cleanup (default: 30 days)
# - logs
#
# Designed for cron usage.
# Works with either:
# - Postgres in Docker Compose service `db` (preferred in this repo)
# - Local pg_dump available in PATH
# =========================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
DB_BACKUP_DIR="$BACKUP_DIR/db"
MEDIA_BACKUP_DIR="$BACKUP_DIR/media"
LOG_DIR="$BACKUP_DIR/logs"

RETENTION_DAYS="${RETENTION_DAYS:-30}"

TIMESTAMP="$(date +'%Y-%m-%d_%H-%M-%S')"
DATE_ONLY="$(date +'%Y-%m-%d')"

mkdir -p "$DB_BACKUP_DIR" "$MEDIA_BACKUP_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/backup_${DATE_ONLY}.log"

log() {
  # ISO-like timestamp
  printf '[%s] %s\n' "$(date +'%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

fail() {
  log "ERROR: $*"
  exit 1
}

# --- Load .env if present (handy for POSTGRES_* variables) ---
# shellcheck disable=SC1091
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

POSTGRES_DB="${POSTGRES_DB:-shelter_db}"
POSTGRES_USER="${POSTGRES_USER:-shelter_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-2112}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5433}"

DB_DUMP_FILE="$DB_BACKUP_DIR/${POSTGRES_DB}_${TIMESTAMP}.dump"
MEDIA_ARCHIVE_FILE="$MEDIA_BACKUP_DIR/media_${TIMESTAMP}.tar.gz"

log "Backup started"
log "Project root: $PROJECT_ROOT"
log "Backup dir: $BACKUP_DIR"
log "Retention days: $RETENTION_DAYS"

# --- 1) Database dump ---
log "DB dump: starting"

# Prefer docker compose if available and service db exists
use_docker_db=false
if command -v docker >/dev/null 2>&1; then
  # Avoid failing on systems without compose plugin
  if docker compose version >/dev/null 2>&1; then
    # Only use docker path if a compose file exists and db service is defined
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
      if docker compose config --services 2>/dev/null | grep -qx 'db'; then
        use_docker_db=true
      fi
    fi
  fi
fi

if [[ "$use_docker_db" == true ]]; then
  log "DB dump mode: docker compose exec db"
  # -T disables pseudo-tty (important for cron)
  # We pass PGPASSWORD to avoid interactive prompt.
  if ! PGPASSWORD="$POSTGRES_PASSWORD" docker compose exec -T db pg_dump -U "$POSTGRES_USER" -F c "$POSTGRES_DB" > "$DB_DUMP_FILE"; then
    fail "pg_dump via docker failed"
  fi
else
  log "DB dump mode: local pg_dump"
  if ! command -v pg_dump >/dev/null 2>&1; then
    fail "pg_dump not found. Install PostgreSQL client tools or use Docker Compose db service."
  fi
  if ! PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -F c -f "$DB_DUMP_FILE" "$POSTGRES_DB"; then
    fail "pg_dump failed"
  fi
fi

DB_SIZE_BYTES="$(wc -c < "$DB_DUMP_FILE" | tr -d ' ')"
log "DB dump: OK -> $DB_DUMP_FILE (${DB_SIZE_BYTES} bytes)"

# --- 2) Archive media/ ---
log "Media archive: starting"
if [[ -d "$PROJECT_ROOT/media" ]]; then
  # Archive folder contents (not the absolute path)
  if tar -czf "$MEDIA_ARCHIVE_FILE" -C "$PROJECT_ROOT" media; then
    MEDIA_SIZE_BYTES="$(wc -c < "$MEDIA_ARCHIVE_FILE" | tr -d ' ')"
    log "Media archive: OK -> $MEDIA_ARCHIVE_FILE (${MEDIA_SIZE_BYTES} bytes)"
  else
    fail "media archive failed"
  fi
else
  log "Media archive: skipped (media/ folder not found)"
fi

# --- 3) Cleanup old backups/logs ---
log "Cleanup: removing files older than ${RETENTION_DAYS} days"

# On Linux/macOS, find -mtime works as expected. For cron that's fine.
# Remove old db dumps, media archives and old daily log files.
find "$DB_BACKUP_DIR" -type f -mtime "+$RETENTION_DAYS" -name '*.dump' -print -delete 2>/dev/null || true
find "$MEDIA_BACKUP_DIR" -type f -mtime "+$RETENTION_DAYS" -name 'media_*.tar.gz' -print -delete 2>/dev/null || true
find "$LOG_DIR" -type f -mtime "+$RETENTION_DAYS" -name 'backup_*.log' -print -delete 2>/dev/null || true

log "Backup finished successfully"
