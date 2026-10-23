#!/usr/bin/env bash
# Connect your Oracle Fusion pod to Claude Code (read-only "oracle-fusion" MCP server).
# Works on macOS and Linux. On Windows, use Connect-Oracle-Fusion.cmd instead.
#
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$ROOT/mcp-servers/fusion-mcp"
HELPER="$MCP_DIR/fusion_setup_helper.py"

# --- Check for uv ---
if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed."
    echo "Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# --- Read .env if it exists ---
POD=""
USER=""
ENV_FILE="$ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs | sed "s/^[\"']//;s/[\"']$//")
        case "$key" in
            FUSION_POD_URL) POD="$value" ;;
            FUSION_USER)    USER="$value" ;;
        esac
    done < <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
fi

# --- Prompt for missing values ---
if [ -z "$POD" ] || [[ "$POD" == *"your-pod"* ]]; then
    read -rp "Enter your Fusion pod URL (e.g. https://abcd-dev1.fa.us2.oraclecloud.com): " POD
fi
if [ -z "$USER" ] || [[ "$USER" == *"example.com"* ]]; then
    read -rp "Enter your Fusion user name (e.g. integration.user@company.com): " USER
fi

if [ -z "$POD" ] || [ -z "$USER" ]; then
    echo "Error: Pod URL and user name are required. Set them in .env or enter them above."
    exit 1
fi

# --- Ensure Python venv ---
PY="$MCP_DIR/.venv/bin/python"
if [ ! -f "$PY" ]; then
    echo "Python environment missing — building it ..."
    uv --directory "$MCP_DIR" sync --frozen
    if [ ! -f "$PY" ]; then
        echo "Error: Could not build the Python environment. Is Python >= 3.12 available?"
        exit 1
    fi
fi

echo ""
echo "[1/3] Saving the pod URL and user name (no password) ..."
"$PY" "$HELPER" config "$POD" "$USER"

echo ""
echo "[2/3] Type the Fusion password for $USER and press Enter ..."
"$PY" "$HELPER" store

echo ""
echo "[3/3] Checking and repairing the whole connection ..."
"$PY" "$HELPER" doctor --fix

echo ""
echo "Done. Open this folder in VS Code or run 'claude' to start using Oracle Fusion with Claude Code."
