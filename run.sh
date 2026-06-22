#!/usr/bin/env bash
# TITAN AIO — Quick start (VPS: Debian 11, 2 CPU, 859MB RAM)
# Usage: ./run.sh [command]
#   ./run.sh           → run tests
#   ./run.sh serve     → start server at :8080
#   ./run.sh dashboard → same as serve
#   ./run.sh launch    → autonomous campaign (provide URL as arg)
#   ./run.sh loop      → continuous autonomous mode
#   ./run.sh mcp       → MCP stdio for Claude Code
#   ./run.sh dbs       → setup Notion databases
#   ./run.sh install   → install deps

set -euo pipefail
cd "$(dirname "$0")"

# ── Auto-detect Python env ──────────────────────────

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif command -v uv &>/dev/null; then
  echo "Creating venv with uv..."
  uv venv .venv --python 3.11
  source .venv/bin/activate
  uv pip install -e ".[dev]"
  uv pip install pymongo notion-client motor
  uv pip install "chromadb==1.1.1" "protobuf==5.29.6"
elif [ -d "$HOME/.local/share/mamba/envs/titan" ]; then
  export PATH="$HOME/.local/share/mamba/envs/titan/bin:$PATH"
else
  echo "❌ No Python environment found."
  echo "   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

case "${1:-test}" in
  test)
    python -m pytest Tests/ -v --tb=short
    ;;
  serve)
    python -m titan.main
    ;;
  dashboard)
    echo "📊 Dashboard: http://localhost:8080/dashboard"
    python -m titan.main
    ;;
  launch)
    URL="${2:?Usage: ./run.sh launch <product-url>}"
    python -m titan.launch "$URL"
    ;;
  loop)
    python -m titan.autonomous_loop --mode continuous --max-cycles 0
    ;;
  mcp)
    python MCP/standalone.py
    ;;
  dbs)
    PARENT="${2:?Usage: ./run.sh dbs <notion-page-id>}"
    python -m Services.notion.setup_dbs "$PARENT"
    ;;
  install)
    uv pip install -e ".[dev]"
    ;;
  *)
    echo "Usage: ./run.sh [test|serve|dashboard|launch|loop|mcp|dbs|install]"
    exit 1
    ;;
esac
