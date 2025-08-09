#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<EOF
Usage: bash scripts/run_turtlesim_kinematics.sh [options]

Options:
  --x <float>         Spawn x (default: 5.0)
  --y <float>         Spawn y (default: 5.0)
  --theta <float>     Spawn heading (rad) (default: 0.0)
  --name <string>     Turtle name (default: turtle2)
  --background        Run in background and log to log/turtlesim_launch.log
  -h, --help          Show this help

Examples:
  bash scripts/run_turtlesim_kinematics.sh                          # foreground
  bash scripts/run_turtlesim_kinematics.sh --background             # background
  bash scripts/run_turtlesim_kinematics.sh --x 8.0 --y 3.0 --theta 1.57 --name buddy
EOF
}

X=5.0
Y=5.0
THETA=0.0
NAME="turtle2"
BACKGROUND=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --x) X="$2"; shift 2 ;;
    --y) Y="$2"; shift 2 ;;
    --theta) THETA="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --background) BACKGROUND=true; shift ;;
    -h|--help) show_help; exit 0 ;;
    *) echo "Unknown option: $1"; show_help; exit 1 ;;
  esac
done

if [[ ! -f install/setup.bash ]]; then
  echo "install/setup.bash not found. Build first: colcon build --packages-select bumperbot_cpp_examples" >&2
  exit 1
fi

source /opt/ros/humble/setup.bash || true
source install/setup.bash || true

mkdir -p log
LOGFILE="log/turtlesim_launch.log"
PIDFILE="log/turtlesim_launch.pid"

echo "Launching turtlesim kinematics (x=${X}, y=${Y}, theta=${THETA}, name=${NAME})"
if $BACKGROUND; then
  nohup ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py \
    x:=${X} y:=${Y} theta:=${THETA} name:=${NAME} \
    > "$LOGFILE" 2>&1 &
  LPID=$!
  echo $LPID > "$PIDFILE"
  echo "Launch running in background (PID: $LPID). Logs: $LOGFILE"
else
  ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py \
    x:=${X} y:=${Y} theta:=${THETA} name:=${NAME}
fi

