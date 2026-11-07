#!/bin/bash
set -e

echo "กำลังตรวจสอบ AWS SAM Template..."

sam validate --lint -t infrastructure/template.yaml

echo "ตรวจสอบ Template ผ่านแล้ว"