#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEEPALIVE_SCRIPT="$PROJECT_DIR/scripts/notebooklm_refresh_keepalive.sh"
LOG_DIR="$PROJECT_DIR/logs"
CRON_LINE="*/15 * * * * cd \"$PROJECT_DIR\" && bash \"$KEEPALIVE_SCRIPT\" >> \"$LOG_DIR/notebooklm_refresh.log\" 2>&1"

mkdir -p "$LOG_DIR"

tmp_cron="$(mktemp)"
trap 'rm -f "$tmp_cron"' EXIT

(crontab -l 2>/dev/null | grep -vF "notebooklm_refresh_keepalive.sh" || true) > "$tmp_cron"
printf '%s\n' "$CRON_LINE" >> "$tmp_cron"
crontab "$tmp_cron"

echo "Installed NotebookLM keepalive cron:"
echo "$CRON_LINE"
