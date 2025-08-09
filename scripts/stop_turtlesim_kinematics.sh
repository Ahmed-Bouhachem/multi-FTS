#!/usr/bin/env bash
set -euo pipefail

# Stops the turtlesim kinematics launch started via ros2 launch
# Looks for PID in log/turtlesim_launch.pid and falls back to pkill

PID_FILE="log/turtlesim_launch.pid"

if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE" || true)
  if [[ -n "${PID:-}" ]] && ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping turtlesim kinematics launch (PID $PID)"
    kill "$PID" || true
  else
    echo "PID in $PID_FILE not running; cleaning up file."
  fi
  rm -f "$PID_FILE"
fi

# Best-effort cleanup in case PID file is missing or stale
pkill -f turtlesim_kinematics.launch.py 2>/dev/null || true
pkill -f simple_turtlesim_kinematics 2>/dev/null || true
pkill -f spawn_turtle.py 2>/dev/null || true
echo "Stopped turtlesim kinematics launch."

