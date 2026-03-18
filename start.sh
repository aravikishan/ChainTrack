#!/usr/bin/env bash
# ChainTrack -- start script
set -euo pipefail

PORT="${CHAINTRACK_PORT:-8004}"
HOST="${CHAINTRACK_HOST:-0.0.0.0}"

echo "========================================"
echo "  ChainTrack - Supply Chain Tracker"
echo "  Starting on http://${HOST}:${PORT}"
echo "========================================"

# Create instance directory for SQLite
mkdir -p instance

# Run with uvicorn
exec uvicorn app:app --host "$HOST" --port "$PORT" --reload
