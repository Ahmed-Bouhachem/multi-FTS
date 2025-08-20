#!/usr/bin/env bash
# Stop a Gazebo run started by scripts/run_gazebo.sh, if running.
set -euo pipefail

if [[ -f log/gazebo_run.pid ]]; then
  PID=$(cat log/gazebo_run.pid || true)
  if [[ -n "${PID:-}" ]] && ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping launch PID $PID"
    kill "$PID" || true
  fi
  rm -f log/gazebo_run.pid
fi

echo "Killing any remaining Gazebo processes..."
pkill -f gzserver 2>/dev/null || true
pkill -f gzclient 2>/dev/null || true
echo "Done."
