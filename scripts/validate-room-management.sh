#!/usr/bin/env bash

set -e

# Load SAM CLI path for Git Bash on Windows
export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"

echo "======================================"
echo " Room Management Module Validation"
echo "======================================"

echo ""
echo "[1/2] Validating SAM Template..."

sam.cmd validate --lint \
  --template-file infrastructure/modules/room-management.yaml

echo ""
echo "[2/2] Running Unit Tests..."

python -m pip install -r tests/requirements-test.txt
python -m pip install pytest

python -m pytest tests/test_room_management_template.py -v

echo ""
echo "======================================"
echo " Validation completed successfully!"
echo "======================================"
