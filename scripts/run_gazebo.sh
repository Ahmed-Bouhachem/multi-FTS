#!/usr/bin/env bash
# Launch bumperbot in Gazebo (classic), with or without controllers/GUI.
# Provides --background mode to run and log to file.
set -euo pipefail

show_help() {
  cat <<EOF
Usage: bash scripts/run_gazebo.sh [options]

Options:
  --simple         Launch simple Gazebo (no controllers)
  --control        Launch with controllers (default)
  --gui            Also start gzclient GUI (best with --control)
  --background     Run launch in background and log to log/gazebo_run.log
  --no-kill        Do not kill existing gzserver/gzclient
  -h, --help       Show this help

Examples:
  bash scripts/run_gazebo.sh --control             # headless with controllers (default)
  bash scripts/run_gazebo.sh --control --gui       # controllers + GUI client
  bash scripts/run_gazebo.sh --simple              # simple spawn, no controllers
  bash scripts/run_gazebo.sh --background          # run in background, capture logs
EOF
}

MODE="control"
GUI=false
BACKGROUND=false
KILL=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --simple) MODE="simple"; shift ;;
    --control) MODE="control"; shift ;;
    --gui) GUI=true; shift ;;
    --background) BACKGROUND=true; shift ;;
    --no-kill) KILL=false; shift ;;
    -h|--help) show_help; exit 0 ;;
    *) echo "Unknown option: $1"; show_help; exit 1 ;;
  esac
done

if [[ ! -f install/setup.bash ]]; then
  echo "install/setup.bash not found. Build the workspace first: colcon build" >&2
  exit 1
fi

source install/setup.bash || true

if $KILL; then
  pkill -f gzserver 2>/dev/null || true
  pkill -f gzclient 2>/dev/null || true
fi

LAUNCH_PKG="bumperbot_description"
if [[ "$MODE" == "simple" ]]; then
  LAUNCH_FILE="gazebo_simple.launch.py"
else
  LAUNCH_FILE="gazebo_simple_control.launch.py"
fi

mkdir -p log
LOGFILE="log/gazebo_run.log"

echo "Launching: ros2 launch ${LAUNCH_PKG} ${LAUNCH_FILE}"
if $BACKGROUND; then
  nohup ros2 launch "$LAUNCH_PKG" "$LAUNCH_FILE" > "$LOGFILE" 2>&1 &
  LPID=$!
  echo $LPID > log/gazebo_run.pid
  echo "Launch is running in background (PID: $LPID). Logs: $LOGFILE"
else
  # Start gzclient GUI optionally in background when using control launch
  if $GUI; then
    echo "Starting gzclient GUI in background..."
    ros2 launch gazebo_ros gzclient.launch.py >/dev/null 2>&1 &
  fi
  ros2 launch "$LAUNCH_PKG" "$LAUNCH_FILE"
fi
