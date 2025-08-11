#!/usr/bin/env bash                                  # Use bash shell
set -euo pipefail                                    # Strict error modes

# Stops the turtlesim kinematics launch started via ros2 launch  # Script purpose
# Looks for PID in log/turtlesim_launch.pid and falls back to pkill # Strategy

PID_FILE="log/turtlesim_launch.pid"                  # Path to PID file

if [[ -f "$PID_FILE" ]]; then                       # If PID file exists
  PID=$(cat "$PID_FILE" || true)                    # Read PID (if any)
  if [[ -n "${PID:-}" ]] && ps -p "$PID" > /dev/null 2>&1; then # If PID valid
    echo "Stopping turtlesim kinematics launch (PID $PID)" # Notify
    kill "$PID" || true                               # Send SIGTERM
  else                                               # Else PID not valid
    echo "PID in $PID_FILE not running; cleaning up file." # Notify
  fi                                                 # End validity check
  rm -f "$PID_FILE"                                  # Remove PID file
fi                                                  # End PID file check

# Best-effort cleanup in case PID file is missing or stale  # Fallback cleanup
pkill -f turtlesim_kinematics.launch.py 2>/dev/null || true # Kill launch process
pkill -f simple_turtlesim_kinematics 2>/dev/null || true    # Kill node process
pkill -f spawn_turtle.py 2>/dev/null || true                # Kill helper
echo "Stopped turtlesim kinematics launch."                 # Done message
