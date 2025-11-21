#!/usr/bin/env bash
# Launch bumperbot in Gazebo Sim (Ignition), with or without controllers/GUI.
# Provides --background mode to run and log to file.
set -euo pipefail

show_help() {
  cat <<EOF
Usage: bash scripts/run_gazebo.sh [options]

Options:
  --simple         Launch simple Gazebo Sim scene (disables controllers unless overridden)
  --control        Launch with controllers (default)
  --gui            Show Gazebo Sim GUI (default: headless)
  --world <name>   World resource passed to ign gazebo (default: package empty.world)
  --model <path>   Absolute path to the URDF/xacro model to load
  --with-controllers / --without-controllers
  --with-helpers / --no-helpers
  --spawn-x <value>  Initial X position (default 0.0)
  --spawn-y <value>  Initial Y position (default 0.0)
  --spawn-z <value>  Initial Z position (default 0.05)
  --entity <name>    Gazebo entity name (defaults adjust with mode)
  --background     Run launch in background and log to log/gazebo_run.log
  --no-kill        Do not kill existing gz sim processes
  -h, --help       Show this help

World shortcuts like 'empty', 'small_house', or 'small_warehouse' automatically
resolve to the packaged worlds directory. Pass an absolute path for custom SDFs.

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
WORLD=""
MODEL_OVERRIDE=""
WITH_CONTROLLERS=""
WITH_CONTROLLERS_FORCED=false
HELPERS=""
HELPERS_FORCED=false
SPAWN_X="0.0"
SPAWN_Y="0.0"
SPAWN_Z="0.05"
ENTITY_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --simple)
      MODE="simple"
      if ! $WITH_CONTROLLERS_FORCED; then WITH_CONTROLLERS="false"; fi
      if ! $HELPERS_FORCED; then HELPERS="false"; fi
      shift ;;
    --control)
      MODE="control"
      if ! $WITH_CONTROLLERS_FORCED; then WITH_CONTROLLERS="true"; fi
      if ! $HELPERS_FORCED; then HELPERS="true"; fi
      shift ;;
    --gui) GUI=true; shift ;;
    --world) WORLD="$2"; shift 2 ;;
    --model) MODEL_OVERRIDE="$2"; shift 2 ;;
    --with-controllers) WITH_CONTROLLERS="true"; WITH_CONTROLLERS_FORCED=true; shift ;;
    --without-controllers) WITH_CONTROLLERS="false"; WITH_CONTROLLERS_FORCED=true; shift ;;
    --with-helpers) HELPERS="true"; HELPERS_FORCED=true; shift ;;
    --no-helpers) HELPERS="false"; HELPERS_FORCED=true; shift ;;
    --spawn-x) SPAWN_X="$2"; shift 2 ;;
    --spawn-y) SPAWN_Y="$2"; shift 2 ;;
    --spawn-z) SPAWN_Z="$2"; shift 2 ;;
    --entity) ENTITY_OVERRIDE="$2"; shift 2 ;;
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

# install/setup.bash may reference unset vars; temporarily relax nounset
set +u
source install/setup.bash || true
set -u

if $KILL; then
  pkill -f "gz sim" 2>/dev/null || true
  pkill -f "ign gazebo" 2>/dev/null || true
fi

PKG_PREFIX=$(ros2 pkg prefix bumperbot_description 2>/dev/null || true)
if [[ -z "$PKG_PREFIX" ]]; then
  echo "Unable to locate bumperbot_description. Did you source install/setup.bash?" >&2
  exit 1
fi
PKG_SHARE="${PKG_PREFIX}/share/bumperbot_description"

DEFAULT_WORLD="${PKG_SHARE}/worlds/empty.world"
if [[ -z "$WORLD" ]]; then
  WORLD="$DEFAULT_WORLD"
else
  if [[ ! -f "$WORLD" ]]; then
    if [[ -f "${PKG_SHARE}/worlds/${WORLD}" ]]; then
      WORLD="${PKG_SHARE}/worlds/${WORLD}"
    elif [[ -f "${PKG_SHARE}/worlds/${WORLD}.world" ]]; then
      WORLD="${PKG_SHARE}/worlds/${WORLD}.world"
    fi
  fi
fi

if [[ -n "$MODEL_OVERRIDE" ]]; then
  MODEL_FILE="$MODEL_OVERRIDE"
else
  if [[ "$MODE" == "simple" ]]; then
    MODEL_FILE="${PKG_SHARE}/urdf/bumperbot_simple.urdf.xacro"
  else
    MODEL_FILE="${PKG_SHARE}/urdf/bumperbot.urdf.xacro"
  fi
fi

if [[ -z "$WITH_CONTROLLERS" ]]; then
  if [[ "$MODE" == "simple" ]]; then
    WITH_CONTROLLERS="false"
  else
    WITH_CONTROLLERS="true"
  fi
fi

if [[ -z "$HELPERS" ]]; then
  if [[ "$WITH_CONTROLLERS" == "true" ]]; then
    HELPERS="true"
  else
    HELPERS="false"
  fi
fi

if [[ -n "$ENTITY_OVERRIDE" ]]; then
  ENTITY_NAME="$ENTITY_OVERRIDE"
else
  if [[ "$MODE" == "simple" ]]; then
    ENTITY_NAME="bumperbot_simple"
  else
    ENTITY_NAME="bumperbot"
  fi
fi

LAUNCH_PKG="bumperbot_description"
LAUNCH_FILE="gazebo.launch.py"

mkdir -p log
LOGFILE="log/gazebo_run.log"

LAUNCH_ARGS=()
if $GUI; then
  LAUNCH_ARGS+=("gui:=true")
else
  LAUNCH_ARGS+=("gui:=false")
fi

LAUNCH_ARGS+=("world:=$WORLD")
LAUNCH_ARGS+=("model:=$MODEL_FILE")
LAUNCH_ARGS+=("with_controllers:=$WITH_CONTROLLERS")
LAUNCH_ARGS+=("start_helper_nodes:=$HELPERS")
LAUNCH_ARGS+=("spawn_x:=$SPAWN_X")
LAUNCH_ARGS+=("spawn_y:=$SPAWN_Y")
LAUNCH_ARGS+=("spawn_z:=$SPAWN_Z")
LAUNCH_ARGS+=("entity:=$ENTITY_NAME")

echo "Launching: ros2 launch ${LAUNCH_PKG} ${LAUNCH_FILE} ${LAUNCH_ARGS[*]}"
if $BACKGROUND; then
  nohup ros2 launch "$LAUNCH_PKG" "$LAUNCH_FILE" "${LAUNCH_ARGS[@]}" > "$LOGFILE" 2>&1 &
  LPID=$!
  echo $LPID > log/gazebo_run.pid
  echo "Launch is running in background (PID: $LPID). Logs: $LOGFILE"
else
  ros2 launch "$LAUNCH_PKG" "$LAUNCH_FILE" "${LAUNCH_ARGS[@]}"
fi
