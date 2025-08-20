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
source /opt/ros/humble/setup.bash || true

python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
# Install/upgrade dependencies quietly
pip -q install --upgrade pip
pip -q install -r webui/requirements.txt

echo "Starting Web UI at http://localhost:5000"
python webui/app.py
