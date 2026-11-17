#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Load SAM CLI path for Git Bash on Windows
export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"

echo "======================================"
echo " Building CSTU Room Booking V5"
echo "======================================"

echo ""
echo "[1/2] Validating SAM Template..."

sam.cmd validate --lint \
  --template-file infrastructure/template.yaml

echo ""
echo "[2/2] Building SAM Application..."

sam.cmd build \
  --template-file infrastructure/template.yaml

echo ""
echo "======================================"
echo " Build completed successfully!"
echo "======================================"
