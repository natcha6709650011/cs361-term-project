
#!/usr/bin/env bash

# =====================================================
# CSTU Room Booking V5
# Module 3: Authentication & Security Validation
# =====================================================

set -Eeuo pipefail

# Find project root from this script's location
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

echo "================================================="
echo " CSTU V5 - Module 3 Security Validation"
echo "================================================="

# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------

fail() {
    echo "[FAIL] $1" >&2
    exit 1
}


# Find executables in Git Bash or Windows PATH
find_executable() {
    local name="$1"
    local found=""

    if command -v "$name" >/dev/null 2>&1; then
        command -v "$name"
        return 0
    fi

    if command -v "${name}.exe" >/dev/null 2>&1; then
        command -v "${name}.exe"
        return 0
    fi

    if command -v where.exe >/dev/null 2>&1; then
        found="$(where.exe "$name" 2>/dev/null | tr -d '\r' | head -n 1)"

        if [[ -n "$found" ]]; then
            if command -v cygpath >/dev/null 2>&1; then
                found="$(cygpath -u "$found")"
            fi

            printf '%s\n' "$found"
            return 0
        fi
    fi

    return 1
}

run_python() {
    local python_launcher

    if python_launcher="$(find_executable py)"; then
        "$python_launcher" -3 "$@"
    elif command -v python3 >/dev/null 2>&1; then
        python3 "$@"
    elif command -v python >/dev/null 2>&1; then
        python "$@"
    else
        fail "Python 3 was not found."
    fi
}

run_sam() {
    local sam_executable

    sam_executable="$(find_executable sam)" ||
        fail "AWS SAM CLI was not found in Windows or Git Bash PATH."

    "$sam_executable" "$@"
}


check_file() {
    [[ -f "$1" ]] || fail "Missing file: $1"
}

# -----------------------------------------------------
# 1. Check required tools
# -----------------------------------------------------

echo ""
echo "[1/6] Checking required tools..."

run_python --version

run_sam --version

# -----------------------------------------------------
# 2. Check required files
# -----------------------------------------------------

echo ""
echo "[2/6] Checking Module 3 files..."

check_file "infrastructure/template.yaml"
check_file "tests/test_security_template.py"

check_file "lambda/cstu-user-auth/lambda_function.py"
check_file "lambda/cstu-user-auth/requirements.txt"

check_file "lambda/cstu-jwt-authorizer/lambda_function.py"
check_file "lambda/cstu-jwt-authorizer/requirements.txt"
check_file "lambda/cstu-jwt-authorizer/public.pem"

check_file "lambda/cstu-room-permission/lambda_function.py"
check_file "lambda/cstu-room-permission/requirements.txt"
check_file "lambda/cstu-room-permission/public.pem"

echo "[PASS] Required files exist."

# -----------------------------------------------------
# 3. Check that no Private Key is inside Lambda source
# -----------------------------------------------------

echo ""
echo "[3/6] Checking Private Key security..."

PRIVATE_KEY_FILE="$(find lambda -type f -name 'private.pem' -print -quit)"

if [[ -n "$PRIVATE_KEY_FILE" ]]; then
    fail "Private Key found inside Lambda source: $PRIVATE_KEY_FILE"
fi

echo "[PASS] No private.pem found inside lambda/."

# -----------------------------------------------------
# 4. Python syntax validation
# -----------------------------------------------------

echo ""
echo "[4/6] Checking Python syntax..."

run_python -m py_compile \
    lambda/cstu-user-auth/lambda_function.py \
    lambda/cstu-jwt-authorizer/lambda_function.py \
    lambda/cstu-room-permission/lambda_function.py

echo "[PASS] All three Lambda Python files have valid syntax."

# -----------------------------------------------------
# 5. Run Security Template Tests
# -----------------------------------------------------

echo ""
echo "[5/6] Running Security Template Tests..."

run_python tests/test_security_template.py -v

echo "[PASS] Security Template Tests completed."

# -----------------------------------------------------
# 6. Validate SAM Template
# -----------------------------------------------------

echo ""
echo "[6/6] Validating SAM Template..."

run_sam validate --lint -t infrastructure/template.yaml

echo ""
echo "================================================="
echo " MODULE 3 VALIDATION SUCCEEDED"
echo "================================================="
