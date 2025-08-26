#!/usr/bin/env python3
# Shebang: allow running this script directly as an executable on UNIX-like systems.

"""
Flask + Socket.IO web UI to teleoperate the robot via ROS 2.

Events:
- 'cmd_vel': {linear: float (m/s), angular: float (rad/s)} → publish Twist/TwistStamped

Usage:
  source /opt/ros/humble/setup.bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r webui/requirements.txt
  python webui/app.py
Then open http://localhost:5000

Design notes:
- Runs rclpy in a background thread so Flask's main thread can handle Socket.IO.
- Uses threading async_mode to avoid extra dependencies (eventlet/gevent optional).
- Publishes to /bumperbot_controller/cmd_vel (unstamped Twist) by default to match YAML
  unless USE_STAMPED_VEL=1 in the environment.
"""

import os                  # Standard lib: read environment variables (e.g., USE_STAMPED_VEL)
import atexit              # Standard lib: register cleanup handlers to run on process exit
import threading           # Standard lib: run ROS event loop in a background thread
from dataclasses import dataclass  # Helper for simple structured data containers

from flask import Flask, render_template, redirect, request   # Flask core APIs
from flask_socketio import SocketIO                           # Socket.IO server for real-time web comms

# ROS 2 Python client library
import rclpy
from rclpy.node import Node                                   # Base class for building ROS 2 nodes
from geometry_msgs.msg import Twist, TwistStamped             # Message types used for velocity commands

# Decide at runtime whether to use stamped or unstamped commands based on env.
# By default, we send UNSTAMPED Twist to match your diff_drive_controller YAML (use_stamped_vel: false).
USE_STAMPED_VEL = os.getenv("USE_STAMPED_VEL", "0").lower() in ("1", "true", "yes")


@dataclass
class VelCmd:
    """A tiny struct to hold linear and angular velocity (m/s and rad/s)."""
    linear: float   # Desired linear velocity in m/s (forward +, backward -)
    angular: float  # Desired angular velocity in rad/s (left +, right -)


class RosBridge(Node):
    """
    ROS 2 node that bridges web UI commands to the diff-drive controller.

    Responsibilities:
    - Create a ROS publisher to /bumperbot_controller/cmd_vel
      (Twist if unstamped, TwistStamped if stamped).
    - Maintain the "last commanded" velocity in memory.
    - Publish that last command at a fixed rate (20 Hz) so the controller
      doesn't timeout and stop (because cmd_vel_timeout=0.25s in your YAML).
    """

    def __init__(self):
        # Initialize the underlying rclpy Node with a unique name.
        super().__init__('webui_cmd_vel_publisher')

        # Remember the mode (stamped vs unstamped) as a flag on the node.
        self._use_stamped = USE_STAMPED_VEL

        # Choose message type and topic name to match diff_drive_controller:
        # - Stamped: geometry_msgs/TwistStamped on /bumperbot_controller/cmd_vel
        # - Unstamped: geometry_msgs/Twist on /bumperbot_controller/cmd_vel_unstamped
        if self._use_stamped:
            msg_type = TwistStamped
            topic = '/bumperbot_controller/cmd_vel'
        else:
            msg_type = Twist
            topic = '/bumperbot_controller/cmd_vel_unstamped'

        # Create the ROS 2 publisher with queue size 10 (depth of outgoing messages).
        self._publisher = self.create_publisher(msg_type, topic, 10)

        # Initialize the last commanded velocity to zero (robot stays still initially).
        self._last_cmd = VelCmd(0.0, 0.0)

        # Create a periodic timer that calls _tick() every 0.05 s (20 Hz).
        # This continuously re-publishes the latest command to avoid controller timeout.
        self._timer = self.create_timer(0.05, self._tick)

    def _tick(self):
        """
        Timer callback executed at 20 Hz.
        It packages the last commanded velocity into the correct message type
        and publishes it on /bumperbot_controller/cmd_vel.
        """
        if self._use_stamped:
            # Build a TwistStamped message when stamped mode is enabled.
            msg = TwistStamped()
            # Stamp with the node's clock (sim time in Gazebo if /clock is active).
            msg.header.stamp = self.get_clock().now().to_msg()
            # frame_id is optional for cmd_vel; can be set to 'base_footprint' if desired.
            msg.twist.linear.x = float(self._last_cmd.linear)   # forward/backward
            msg.twist.angular.z = float(self._last_cmd.angular) # yaw left/right
        else:
            # Build a classic (unstamped) Twist message.
            msg = Twist()
            msg.linear.x = float(self._last_cmd.linear)         # forward/backward
            msg.angular.z = float(self._last_cmd.angular)       # yaw left/right

        # Publish the message to the controller's cmd_vel topic.
        self._publisher.publish(msg)

    def publish_cmd(self, cmd: VelCmd) -> None:
        """
        Update the last commanded velocity.

        Note: We don't publish immediately here—_tick() will publish at 20 Hz.
        This ensures smooth, continuous control and avoids spamming on every UI event.
        """
        self._last_cmd = cmd


def start_rclpy_in_background() -> RosBridge:
    """
    Initialize rclpy (ROS 2 client library) and spin the node in a background thread.

    Why a thread?
    - Flask+Socket.IO runs the web server in the main thread.
    - rclpy's spin (event loop) must run continuously to process timers, publishers, etc.
    - Spinning in a daemon thread lets the process exit cleanly when Flask stops.
    """
    rclpy.init(args=None)                                   # Initialize ROS 2 for this process
    node = RosBridge()                                      # Create our publishing bridge node
    thread = threading.Thread(target=rclpy.spin,            # rclpy.spin blocks and processes callbacks
                              args=(node,),
                              daemon=True)                  # Daemon thread ends with main process
    thread.start()                                          # Start the ROS 2 event loop in background
    return node                                             # Return the node so Flask handlers can use it


# Create the Flask app instance (WSGI application object).
app = Flask(__name__)

# Create the Socket.IO server wrapper around Flask.
# async_mode='threading' uses Python threads (no eventlet/gevent required).
# cors_allowed_origins='*' allows connections from any origin (OK for dev).
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# Global reference to the RosBridge node (set during startup).
ros_node: RosBridge | None = None


@app.route('/')
def index():
    """
    HTTP GET / → Render and return the control page (templates/index.html).
    Flask will look for 'index.html' in the 'templates' directory relative to app root.
    """
    return render_template('index.html')


@app.route('/socket.io/socket.io.js')
def legacy_socketio_client_path():
    """
    Some tutorials expect /socket.io/socket.io.js to serve a client script directly.
    Flask-SocketIO does not host that file by default, so we redirect to a CDN version.
    Browsers requesting this path will be 302-redirected to the CDN script.
    """
    return redirect('https://cdn.socket.io/4.7.5/socket.io.min.js', code=302)


@app.get('/api/cmd')
def http_cmd():
    """
    HTTP fallback to set a single cmd_vel via query string.
    Example: GET /api/cmd?linear=0.3&angular=1.0

    Returns a small JSON object confirming what was set.
    """
    try:
        # Extract 'linear' and 'angular' from query params; default to 0 if missing.
        lin = float(request.args.get('linear', '0') or 0)
        ang = float(request.args.get('angular', '0') or 0)
    except Exception:
        # If parsing fails, fall back to zeros rather than erroring out.
        lin = 0.0
        ang = 0.0

    # Log the command for debug visibility in Flask console.
    app.logger.info(f"http cmd linear={lin} angular={ang}")

    # If the ROS node is ready, update the last command (publisher timer will send it).
    if ros_node is not None:
        ros_node.publish_cmd(VelCmd(lin, ang))

    # Return a JSON response (Flask auto-serializes dicts).
    return {'ok': True, 'linear': lin, 'angular': ang}


@socketio.on('connect')
def on_connect():
    """
    Socket.IO event: a client opened a WebSocket connection.
    Good place to push initial state if your UI needs it.
    """
    app.logger.info('Client connected')


@socketio.on('disconnect')
def on_disconnect():
    """
    Socket.IO event: a client closed the WebSocket connection.
    """
    app.logger.info('Client disconnected')


@socketio.on('cmd_vel')
def on_cmd_vel(data):
    """
    Socket.IO event: receive velocity commands from the browser.

    Expected payload:
    {
      "linear":  <float m/s>,
      "angular": <float rad/s>
    }

    We parse, log for debugging, and update the ROS node’s last command.
    The 20 Hz timer will publish it continuously until changed again.
    """
    try:
        # Extract linear/angular, defaulting to 0.0 if missing.
        lin = float(data.get('linear', 0.0))
        ang = float(data.get('angular', 0.0))

        # Log for visibility
        app.logger.info(f"socketio cmd_vel linear={lin} angular={ang}")

        # Forward to ROS (if node is available)
        if ros_node is not None:
            ros_node.publish_cmd(VelCmd(lin, ang))
    except Exception as e:
        # If anything goes wrong (bad payload, etc.), log stack trace.
        app.logger.exception(f"Failed to handle cmd_vel: {e}")


def shutdown_ros():
    """
    Best-effort shutdown of rclpy when the process exits.

    Registered with atexit so it runs on normal termination (Ctrl+C / server stop).
    """
    try:
        if rclpy.ok():   # Only attempt shutdown if rclpy was initialized.
            rclpy.shutdown()
    except Exception:
        # Swallow any exceptions during shutdown to avoid masking real exit causes.
        pass


def main():
    """
    Script entry point when running `python webui/app.py`.

    Steps:
    1) Start ROS in a background thread (spinning RosBridge node).
    2) Register rclpy shutdown handler.
    3) Start the Flask+Socket.IO development server on 0.0.0.0:5000.
       (In production you’d likely use gunicorn + eventlet or gevent.)
    """
    global ros_node
    ros_node = start_rclpy_in_background()                       # Start ROS node + spin thread
    atexit.register(shutdown_ros)                                # Ensure clean ROS shutdown
    socketio.run(app, host='0.0.0.0', port=5000)                 # Start the dev server


# Standard Python pattern: only run main() if this file is executed directly,
# not when it is imported as a module.
if __name__ == '__main__':
    main()
