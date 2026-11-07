#!/bin/bash
set -e

echo "กำลัง Build AWS SAM..."

sam build -t infrastructure/template.yaml

echo "Build เสร็จแล้ว"