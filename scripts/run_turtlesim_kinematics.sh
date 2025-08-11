#!/usr/bin/env bash                               # Use bash shell
set -euo pipefail                                 # Strict error handling

show_help() {                                     # Function to print usage
  cat <<EOF
Usage: bash scripts/run_turtlesim_kinematics.sh [options]  # Script usage

Options:                                                 # Options section
  --x <float>         Spawn x (default: 5.0)            # x parameter
  --y <float>         Spawn y (default: 5.0)            # y parameter
  --theta <float>     Spawn heading (rad) (default: 0.0) # theta parameter
  --name <string>     Turtle name (default: turtle2)    # name parameter
  --background        Run in background and log to log/turtlesim_launch.log # background mode
  -h, --help          Show this help                     # help option

Examples:                                               # Examples header
  bash scripts/run_turtlesim_kinematics.sh                          # foreground
  bash scripts/run_turtlesim_kinematics.sh --background             # background
  bash scripts/run_turtlesim_kinematics.sh --x 8.0 --y 3.0 --theta 1.57 --name buddy # with args
EOF
}                                                      # End show_help

X=5.0                                                 # Default x
Y=5.0                                                 # Default y
THETA=0.0                                             # Default theta
NAME="turtle2"                                        # Default name
BACKGROUND=false                                      # Default foreground mode

while [[ $# -gt 0 ]]; do                              # Parse CLI args loop
  case "$1" in                                        # Switch on current arg
    --x) X="$2"; shift 2 ;;                          # Set x and shift
    --y) Y="$2"; shift 2 ;;                          # Set y and shift
    --theta) THETA="$2"; shift 2 ;;                  # Set theta and shift
    --name) NAME="$2"; shift 2 ;;                    # Set name and shift
    --background) BACKGROUND=true; shift ;;            # Enable background
    -h|--help) show_help; exit 0 ;;                    # Show help
    *) echo "Unknown option: $1"; show_help; exit 1 ;; # Unknown option
  esac
done                                                  # End arg parsing

if [[ ! -f install/setup.bash ]]; then                # Check build exists
  echo "install/setup.bash not found. Build first: colcon build --packages-select bumperbot_cpp_examples" >&2 # Error message
  exit 1                                              # Exit with error
fi                                                    # End check

source /opt/ros/humble/setup.bash || true             # Source ROS 2 env
source install/setup.bash || true                     # Source workspace env

mkdir -p log                                          # Ensure log dir exists
LOGFILE="log/turtlesim_launch.log"                    # Log file path
PIDFILE="log/turtlesim_launch.pid"                    # PID file path

echo "Launching turtlesim kinematics (x=${X}, y=${Y}, theta=${THETA}, name=${NAME})" # Announce launch
if $BACKGROUND; then                                  # If background mode
  nohup ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py \ # Launch ROS 2 in background
    x:=${X} y:=${Y} theta:=${THETA} name:=${NAME} \    # Pass launch args
    > "$LOGFILE" 2>&1 &                              # Redirect output
  LPID=$!                                              # Capture PID
  echo $LPID > "$PIDFILE"                             # Save PID
  echo "Launch running in background (PID: $LPID). Logs: $LOGFILE" # Print info
else                                                  # Foreground mode
  ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py \ # Launch foreground
    x:=${X} y:=${Y} theta:=${THETA} name:=${NAME}      # Pass launch args
fi                                                    # End if
