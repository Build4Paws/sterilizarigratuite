#!/usr/bin/env bash
set -euo pipefail

# Build + ship the API Lambda from this repo.
#   Run from anywhere:  ./lambda/deploy.sh
#
# What it does:
#   1. Reads the function's CURRENT runtime + architecture from AWS, so the
#      dependency wheels we bundle match exactly (no "works on my mac" surprises).
#   2. Installs requirements.txt as Linux wheels for that target (no Docker).
#   3. Adds lambda_function.py + email_templates.py on top.
#   4. Zips and calls update-function-code, then waits for the update to settle.
#
# This script NEVER touches environment variables / secrets. The Turnstile
# secret, DB creds, TOKEN_PEPPER etc. live in the function's configuration
# (ideally Secrets Manager / SSM) and are managed out-of-band — see README.md.
#
# Requirements on your machine: awscli (authenticated), python3, pip, zip.

FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-process-user-data}"
REGION="${AWS_REGION:-eu-central-1}"

HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/build"
DIST="$HERE/dist"
ZIP="$DIST/function.zip"

echo "▶ Target: $FUNCTION_NAME ($REGION)"

# 1. Discover the deployed runtime + architecture.
read -r RUNTIME ARCH <<<"$(aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" --region "$REGION" \
  --query '[Runtime, Architectures[0]]' --output text)"

if [[ -z "${RUNTIME:-}" || "$RUNTIME" == "None" ]]; then
  echo "✖ Could not read the function configuration. Are your AWS creds set?" >&2
  exit 1
fi

PYVER="${RUNTIME#python}"                 # python3.13 -> 3.13
case "$ARCH" in
  arm64) PLAT="manylinux2014_aarch64" ;;
  *)     PLAT="manylinux2014_x86_64" ;;   # x86_64 / unset -> x86_64
esac
echo "▶ Building for $RUNTIME / $ARCH  (platform=$PLAT, python=$PYVER)"

# 2. Clean + install matching Linux wheels.
rm -rf "$BUILD" "$ZIP"
mkdir -p "$BUILD" "$DIST"
python3 -m pip install \
  --requirement "$HERE/requirements.txt" \
  --target "$BUILD" \
  --platform "$PLAT" \
  --python-version "$PYVER" \
  --implementation cp \
  --only-binary=:all: \
  --upgrade \
  --quiet

# 3. App code on top of the deps.
cp "$HERE/lambda_function.py" "$HERE/email_templates.py" "$BUILD/"

# 4. Zip (exclude bytecode/caches for a lean, reproducible artifact).
( cd "$BUILD" && zip -qr "$ZIP" . -x '*.pyc' -x '*/__pycache__/*' )
echo "▶ Package: $ZIP ($(du -h "$ZIP" | cut -f1))"

# 5. Ship.
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" --region "$REGION" \
  --zip-file "fileb://$ZIP" \
  --query '{Function:FunctionName, Status:LastUpdateStatus, Runtime:Runtime, CodeSize:CodeSize}' \
  --output table

echo "▶ Waiting for the update to finish…"
aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"
echo "✓ Deployed $FUNCTION_NAME."
