#!/usr/bin/env bash
# TITAN AIO — Quick start script
# Usage: ./run.sh [command]
#   ./run.sh           → run tests
#   ./run.sh serve     → start HTTP API server
#   ./run.sh dashboard → open dashboard
#   ./run.sh launch    → autonomous campaign (provide URL as arg)
#   ./run.sh loop      → continuous autonomous mode

set -euo pipefail
cd "$(dirname "$0")"

MAMBA=~/.local/bin/micromamba
ENV=titan

case "${1:-test}" in
  test)
    $MAMBA run -n $ENV python -m pytest Tests/ -v --tb=short
    ;;
  serve)
    $MAMBA run -n $ENV python -m titan.main
    ;;
  dashboard)
    echo "📊 Dashboard: http://localhost:8080/dashboard"
    $MAMBA run -n $ENV python -m titan.main
    ;;
  launch)
    URL="${2:?Usage: ./run.sh launch <product-url>}"
    $MAMBA run -n $ENV python -m titan.launch "$URL"
    ;;
  loop)
    $MAMBA run -n $ENV python -m titan.autonomous_loop --mode continuous --max-cycles 0
    ;;
  mcp)
    $MAMBA run -n $ENV python MCP/standalone.py
    ;;
  *)
    echo "Usage: ./run.sh [test|serve|dashboard|launch|loop|mcp]"
    exit 1
    ;;
esac
