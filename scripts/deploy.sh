
#!/usr/bin/env bash
set -euo pipefail

# Move to project root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Deployment configuration
TEMPLATE_FILE="infrastructure/modules/room-management.yaml"
STACK_NAME="cstu-room-booking-v5-dev"
REGION="us-east-1"

echo "=========================================="
echo " CSTU Room Management V5 Deployment"
echo "=========================================="
echo ""

# Step 1: Validate SAM Template
echo "[1/3] Validating SAM Template..."

sam validate --lint \
    --template-file "$TEMPLATE_FILE"

echo ""
echo "Validation completed."
echo ""

# Step 2: Build Lambda Functions
echo "[2/3] Building Lambda Functions..."

sam build \
    --template-file "$TEMPLATE_FILE"

echo ""
echo "Build completed."
echo ""

# Step 3: Deploy using existing SAM configuration
echo "[3/3] Deploying CloudFormation Stack..."

echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

sam deploy \
    --config-file infrastructure/samconfig.toml \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --confirm-changeset

echo ""
echo "=========================================="
echo " Deployment command completed."
echo "=========================================="
