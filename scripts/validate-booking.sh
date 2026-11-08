#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/3] Checking Booking Lambda source compiles..."
python3 -m py_compile \
  lambda/booking/lambda_function.py \
  lambda/booking_facility_management/lambda_function.py \
  lambda/booking_no_show/lambda_function.py

echo "[2/3] Running Booking & Booking Lifecycle template checks..."
python3 tests/test_booking_template.py

echo "[3/3] Running SAM validation..."
if command -v sam >/dev/null 2>&1; then
  sam validate --lint --template-file infrastructure/template.yaml
else
  echo "SAM CLI is not installed; static checks passed but SAM validation was skipped." >&2
fi

echo "Booking module validation passed."
