#!/bin/bash
# Start the GEN Investigator Electron app (Vite + Electron).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting GEN Investigator (EESI)..."
echo "  App directory: $SCRIPT_DIR"
echo "  Repository root: $(cd .. && pwd)"
echo ""

npm run build:electron
npm run electron-dev
