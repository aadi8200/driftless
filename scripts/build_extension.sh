#!/bin/bash
# Driftless Extension Packaging Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ZIP_NAME="$ROOT_DIR/driftless-extension.zip"

echo "Building Driftless Chrome extension zip..."
rm -f "$ZIP_NAME"

cd "$ROOT_DIR/extension"
zip -r "$ZIP_NAME" . -x ".*" -x "__MACOSX"

echo "✓ Extension packaged successfully at: $ZIP_NAME"
