#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "Missing virtualenv at $PROJECT_DIR/.venv" >&2
  exit 1
fi

cd "$PROJECT_DIR"
. .venv/bin/activate
exec notebooklm auth refresh --quiet
