#!/usr/bin/env bash
set -e

# MoneyPrinter Centralized Server Launcher for LingZi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-/home/lingzi/.local/share/MoneyPrinterTurbo/.venv}"
export MPT_WEBUI_HOST="${MPT_WEBUI_HOST:-0.0.0.0}"
export MPT_WEBUI_PORT="${MPT_WEBUI_PORT:-8501}"

echo "========================================================"
echo " Starting MoneyPrinter Centralized Server on LingZi"
echo " Host: $MPT_WEBUI_HOST | Port: $MPT_WEBUI_PORT"
echo " Environment: $UV_PROJECT_ENVIRONMENT"
echo "========================================================"

exec ./webui.sh
