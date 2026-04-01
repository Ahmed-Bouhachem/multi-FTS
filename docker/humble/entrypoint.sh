#!/usr/bin/env bash
set -e

source /opt/ros/humble/setup.bash

if [ -f /workspaces/multi-FTS/install/setup.bash ]; then
  source /workspaces/multi-FTS/install/setup.bash
fi

exec "$@"
