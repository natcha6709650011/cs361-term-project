#!/usr/bin/env bash

set -e

# Load SAM CLI path for Git Bash on Windows
export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"

echo "======================================"
echo " Room Management Module Build"
echo "======================================"

echo ""
echo "[1/2] Validating SAM Template..."

sam.cmd validate --lint \
  --template-file infrastructure/modules/room-management.yaml

echo ""
echo "[2/2] Building Lambda functions..."

sam.cmd build \
  --template-file infrastructure/modules/room-management.yaml

echo ""
echo "======================================"
echo " Build completed successfully!"
echo "======================================"