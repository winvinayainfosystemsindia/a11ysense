#!/usr/bin/env bash
# =============================================================================
# A11ySense AI — One-command dependency installer (Bash / Linux / WSL / macOS)
#
# Usage (from backend/ directory):
#   ./install.sh
#   ./install.sh --upgrade
#   PIP=python3 -m pip ./install.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_REQUIREMENTS="$SCRIPT_DIR/common/requirements/all.txt"
PIP_CMD="${PIP:-pip}"
UPGRADE_FLAG=""

# Parse args
for arg in "$@"; do
    case $arg in
        --upgrade|-u) UPGRADE_FLAG="--upgrade" ;;
    esac
done

echo ""
echo "========================================================="
echo "  A11ySense AI — Backend Dependency Installer"
echo "========================================================="
echo ""
# Verify and Install OpenClaw CLI if missing
if ! command -v openclaw &> /dev/null; then
    echo "[INFO] OpenClaw CLI not found. Installing OpenClaw..."
    curl -fsSL https://openclaw.ai/install.sh | bash
else
    echo "[INFO] OpenClaw CLI is already installed."
fi

if [ ! -f "$MASTER_REQUIREMENTS" ]; then
    echo "[ERROR] Master requirements not found: $MASTER_REQUIREMENTS"
    exit 1
fi

echo "[INFO] Installing from: common/requirements/all.txt"
echo "[INFO] pip command:      $PIP_CMD"
[ -n "$UPGRADE_FLAG" ] && echo "[INFO] Mode:             UPGRADE" || echo "[INFO] Mode:             INSTALL (pinned)"
echo ""

$PIP_CMD install -r "$MASTER_REQUIREMENTS" $UPGRADE_FLAG

echo ""
echo "========================================================="
echo "  All dependencies installed successfully!"
echo ""
echo "  Services ready to run:"
echo "    Gateway   → uvicorn app.main:app --port 8000 (in services/gateway)"
echo "    Agent     → uvicorn app.main:app --port 8001 (in services/agent)"
echo "    Reporting → uvicorn app.main:app --port 8002 (in services/reporting)"
echo "    Crawler   → uvicorn app.main:app --port 8003 (in services/crawler)"
echo "    Analyzer  → uvicorn app.main:app --port 8004 (in services/analyzer)"
echo "    LLM       → uvicorn app.main:app --port 8005 (in services/llm)"
echo "========================================================="
