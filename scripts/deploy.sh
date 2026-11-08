#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"

echo "======================================"
echo " CSTU Room Booking V5 - Safety Check"
echo "======================================"

echo ""
echo "[1/2] Validating Main SAM Template..."

sam.cmd validate --lint \
  --template-file infrastructure/template.yaml

echo ""
echo "[2/2] Building Main SAM Application..."

sam.cmd build \
  --template-file infrastructure/template.yaml

echo ""
echo "======================================"
echo " Safety Check Passed"
echo " No AWS deployment was performed."
echo "======================================"
