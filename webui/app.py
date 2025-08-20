#!/usr/bin/env python3
"""
Flask + Socket.IO web UI to teleoperate the robot via ROS 2.

Events:
- 'cmd_vel': {linear: float (m/s), angular: float (rad/s)} → publish Twist

Usage:
  source /opt/ros/humble/setup.bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r webui/requirements.txt
  python webui/app.py
Then open http://localhost:5000

Design notes:
- Runs rclpy in a background thread so Flask's main thread can handle Socket.IO.
- Uses threading async_mode to avoid extra dependencies (eventlet/gevent optional).
- Publishes to /diff_drive_controller/cmd_vel by default (Gazebo diff drive).
"""

import atexit
import threading
from dataclasses import dataclass  # Lightweight struct for velocity commands

from flask import Flask, render_template  # Web app and template rendering
from flask_socketio import SocketIO       # WebSocket (Socket.IO) server

# ROS 2
import rclpy                      # ROS 2 Python client library
from rclpy.node import Node       # Base class for ROS 2 nodes
from geometry_msgs.msg import Twist  # Message type for velocity commands


@dataclass
class VelCmd:
    """Simple container for cmd_vel inputs from the browser."""
    linear: float
    angular: float


class RosBridge(Node):
    """ROS 2 node that publishes Twist to common diff-drive controller topics.

    Publishes to both /bumperbot_controller/cmd_vel and /diff_drive_controller/cmd_vel
    so the UI works regardless of which controller name is active.
    """

    def __init__(self):
        # Initialize node with a deterministic name; single publisher only
        super().__init__('webui_cmd_vel_publisher')
        # Create publishers for both common controller names
        self.publishers = [
            self.create_publisher(Twist, '/bumperbot_controller/cmd_vel', 10),
            self.create_publisher(Twist, '/diff_drive_controller/cmd_vel', 10),
        ]

    def publish_cmd(self, cmd: VelCmd) -> None:
        """Publish a Twist using linear.x and angular.z components only."""
        msg = Twist()
        msg.linear.x = float(cmd.linear)
        msg.angular.z = float(cmd.angular)
        for pub in self.publishers:
            pub.publish(msg)


def start_rclpy_in_background():
    """Initialize rclpy and spin in a background thread.

    Returns the RosBridge node so handlers can publish from Flask thread.
    """
    rclpy.init(args=None)
    node = RosBridge()
    # Daemon thread ensures process can exit cleanly when Flask stops
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    return node


app = Flask(__name__)
# Use threading mode to avoid extra dependencies; websockets optional.
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

ros_node: RosBridge | None = None


@app.route('/')
def index():
    """Serve the control page."""
    return render_template('index.html')


@socketio.on('connect')
def on_connect():
    """Log connection; could emit initial state here if needed."""
    app.logger.info('Client connected')


@socketio.on('disconnect')
def on_disconnect():
    """Log disconnection."""
    app.logger.info('Client disconnected')


@socketio.on('cmd_vel')
def on_cmd_vel(data):
    """Receive velocity commands from the browser and publish them."""
    try:
        lin = float(data.get('linear', 0.0))
        ang = float(data.get('angular', 0.0))
        if ros_node is not None:
            ros_node.publish_cmd(VelCmd(lin, ang))
    except Exception as e:
        app.logger.exception(f"Failed to handle cmd_vel: {e}")


def shutdown_ros():
    """Best-effort shutdown of rclpy on process exit."""
    try:
        if rclpy.ok():
            rclpy.shutdown()
    except Exception:
        pass


def main():
    """Entrypoint used by `python webui/app.py`."""
    global ros_node
    # Spin ROS 2 in background before starting the web server
    ros_node = start_rclpy_in_background()
    atexit.register(shutdown_ros)
    # Development server. For production, consider gunicorn with eventlet.
    socketio.run(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
