#!/usr/bin/env bash
# Start the Flask + Socket.IO web UI that publishes cmd_vel to ROS 2.
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

if [[ ! -f webui/app.py ]]; then
  echo "webui/app.py not found (run from repo root)" >&2
  exit 1
fi

# Source ROS 2 to make message types available to rclpy
# setup.bash may reference unset vars; temporarily relax nounset
set +u
source /opt/ros/humble/setup.bash || true
set -u

if [[ -z "${NO_VENV:-}" ]]; then
  if ! python3 -m venv .venv 2>/dev/null; then
    echo "Could not create Python venv (ensurepip missing)." >&2
    echo "Install venv support then re-run:" >&2
    echo "  sudo apt update && sudo apt install -y python3-venv" >&2
    echo "Or run without venv: NO_VENV=1 bash scripts/run_web_ui.sh" >&2
    exit 1
  fi
  source .venv/bin/activate
  # Install/upgrade dependencies quietly
  pip -q install --upgrade pip
  pip -q install -r webui/requirements.txt
else
  echo "NO_VENV=1 set: using system Python packages."
  python3 -m pip -q install --user -r webui/requirements.txt || true
fi

echo "Starting Web UI at http://localhost:5000"
python webui/app.py
