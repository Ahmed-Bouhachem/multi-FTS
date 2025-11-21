#!/usr/bin/env bash
# Stop a Gazebo Sim run started by scripts/run_gazebo.sh, if running.
set -euo pipefail

if [[ -f log/gazebo_run.pid ]]; then
  PID=$(cat log/gazebo_run.pid || true)
  if [[ -n "${PID:-}" ]] && ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping launch PID $PID"
    kill "$PID" || true
  fi
  rm -f log/gazebo_run.pid
fi

echo "Killing any remaining Gazebo Sim processes..."
pkill -f "gz sim" 2>/dev/null || true
pkill -f "ign gazebo" 2>/dev/null || true
echo "Done."
