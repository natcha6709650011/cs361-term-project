#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running Room Information & Search template checks..."
python3 tests/test_room_template.py

if command -v sam >/dev/null 2>&1; then
  sam validate --lint --template-file infrastructure/template.yaml
else
  echo "SAM CLI is not installed; static checks passed but SAM validation was skipped." >&2
fi
