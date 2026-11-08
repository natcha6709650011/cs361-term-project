#!/usr/bin/env bash

set -e

# Load SAM CLI path for Git Bash on Windows
export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"

echo "กำลังตรวจสอบ AWS SAM Template..."

sam.cmd validate --lint \
  --template-file infrastructure/template.yaml

echo "ตรวจสอบ Template ผ่านแล้ว"
