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

import os
import atexit
import threading
import subprocess
import signal
from dataclasses import dataclass
from typing import Optional, Tuple

from flask import Flask, render_template, redirect, request   # Flask core APIs
from flask_socketio import SocketIO                           # Socket.IO server for real-time web comms

# ROS 2 Python client library
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist, TwistStamped
from std_msgs.msg import Bool

# Decide at runtime whether to use stamped or unstamped commands based on env.
# By default, we send UNSTAMPED Twist to match your diff_drive_controller YAML (use_stamped_vel: false).
USE_STAMPED_VEL = os.getenv("USE_STAMPED_VEL", "0").lower() in ("1", "true", "yes")
USE_SIM_TIME = os.getenv("WEBUI_USE_SIM_TIME", "1").lower() in ("1", "true", "yes")

# Optional integration with twist_mux + safety_stop. When enabled, the Web UI
# publishes geometry_msgs/Twist to the twist_mux input (joy_vel by default)
# instead of directly to /bumperbot_controller/cmd_vel_unstamped.
USE_TWIST_MUX = os.getenv("WEBUI_USE_TWIST_MUX", "0").lower() in ("1", "true", "yes")
TWIST_MUX_INPUT_TOPIC = os.getenv("WEBUI_TWIST_MUX_TOPIC", "joy_vel")

# Allow the web UI to start/stop Gazebo via subprocess if desired.
DEFAULT_SIM_COMMAND = [
    "ros2",
    "launch",
    "bumperbot_description",
    "gazebo.launch.py",
]
DEFAULT_SIM_WORLD = os.getenv("WEBUI_SIM_WORLD", "")
DEFAULT_SIM_GUI = os.getenv("WEBUI_SIM_GUI", "true").lower() in ("1", "true", "yes")
DEFAULT_SIM_CONTROLLERS = os.getenv("WEBUI_SIM_WITH_CONTROLLERS", "true").lower() in ("1", "true", "yes")
DEFAULT_SIM_HELPERS = os.getenv("WEBUI_SIM_HELPERS", "false").lower() in ("1", "true", "yes")
SIM_LOG_PATH = os.getenv("WEBUI_SIM_LOG", "log/webui_gazebo.log")


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
        super().__init__(
            'webui_cmd_vel_publisher',
            parameter_overrides=[
                Parameter('use_sim_time', Parameter.Type.BOOL, USE_SIM_TIME)
            ]
        )

        # Remember the mode (stamped vs unstamped) as a flag on the node.
        # When routing through twist_mux, we always use unstamped Twist.
        if USE_TWIST_MUX:
            self._use_stamped = False
        else:
            self._use_stamped = USE_STAMPED_VEL

        # Choose message type and topic name:
        # - If using twist_mux: geometry_msgs/Twist on joy_vel (or override)
        #   so safety_stop and other locks can act on the command stream.
        # - Otherwise:
        #   - Stamped: geometry_msgs/TwistStamped on /bumperbot_controller/cmd_vel
        #   - Unstamped: geometry_msgs/Twist on /bumperbot_controller/cmd_vel_unstamped
        if USE_TWIST_MUX:
            msg_type = Twist
            topic = f'/{TWIST_MUX_INPUT_TOPIC.lstrip("/")}'
        else:
            if self._use_stamped:
                msg_type = TwistStamped
                topic = '/bumperbot_controller/cmd_vel'
            else:
                msg_type = Twist
                topic = '/bumperbot_controller/cmd_vel_unstamped'

        # Create the ROS 2 publisher with queue size 10 (depth of outgoing messages).
        self._publisher = self.create_publisher(msg_type, topic, 10)
        self.get_logger().info(
            f"WebUI RosBridge publishing {msg_type.__name__} commands to '{topic}'"
        )

        # Track safety_stop state (true when an obstacle is in the danger zone).
        self._safety_stop_active = False
        self._safety_sub = self.create_subscription(
            Bool,
            'safety_stop',
            self._on_safety_stop,
            10,
        )

        # Initialize the last commanded velocity to zero (robot stays still initially).
        self._last_cmd = VelCmd(0.0, 0.0)

        # Create a periodic timer that calls _tick() every 0.05 s (20 Hz).
        # This continuously re-publishes the latest command to avoid controller timeout.
        self._timer = self.create_timer(0.05, self._tick)

    def _on_safety_stop(self, msg: Bool) -> None:
        """
        Remember whether safety_stop is active.

        We use this only to gate forward commands from the Web UI so that:
        - When safety_stop is true (danger zone), we block forward motion.
        - Backwards and pure rotation are still allowed so the user can escape.
        """
        self._safety_stop_active = bool(msg.data)

    def _tick(self):
        """
        Timer callback executed at 20 Hz.
        It packages the last commanded velocity into the correct message type
        and publishes it on the selected cmd_vel topic.
        """
        # Apply safety_stop: when active, block forward motion but still allow
        # backing up and pure rotation so the user can move away from obstacles.
        linear = float(self._last_cmd.linear)
        angular = float(self._last_cmd.angular)
        if self._safety_stop_active and linear > 0.0:
            linear = 0.0

        if self._use_stamped:
            # Build a TwistStamped message when stamped mode is enabled.
            msg = TwistStamped()
            # Stamp with the node's clock (sim time in Gazebo if /clock is active).
            msg.header.stamp = self.get_clock().now().to_msg()
            # frame_id is optional for cmd_vel; can be set to 'base_footprint' if desired.
            msg.twist.linear.x = linear   # forward/backward
            msg.twist.angular.z = angular # yaw left/right
        else:
            # Build a classic (unstamped) Twist message.
            msg = Twist()
            msg.linear.x = linear         # forward/backward
            msg.angular.z = angular       # yaw left/right

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
_sim_process: Optional[subprocess.Popen] = None
_sim_log_handle: Optional[object] = None
_sim_lock = threading.Lock()


def _build_sim_command(world: Optional[str], gui: Optional[bool],
                       with_controllers: Optional[bool],
                       helper_nodes: Optional[bool]) -> list[str]:
    cmd = list(DEFAULT_SIM_COMMAND)
    if world:
        cmd.append(f"world:={world}")
    if gui is not None:
        cmd.append(f"gui:={'true' if gui else 'false'}")
    if with_controllers is not None:
        cmd.append(f"with_controllers:={'true' if with_controllers else 'false'}")
    if helper_nodes is not None:
        cmd.append(f"start_helper_nodes:={'true' if helper_nodes else 'false'}")
    return cmd


def start_simulation(world: Optional[str] = None,
                     gui: Optional[bool] = None,
                     with_controllers: Optional[bool] = None,
                     helper_nodes: Optional[bool] = None) -> Tuple[bool, str]:
    """
    Launch gazebo.launch.py in a subprocess so the web UI can drive the sim.
    """
    world = world or DEFAULT_SIM_WORLD or None
    gui = DEFAULT_SIM_GUI if gui is None else gui
    with_controllers = DEFAULT_SIM_CONTROLLERS if with_controllers is None else with_controllers
    helper_nodes = DEFAULT_SIM_HELPERS if helper_nodes is None else helper_nodes

    os.makedirs(os.path.dirname(SIM_LOG_PATH), exist_ok=True)

    with _sim_lock:
        global _sim_process
        global _sim_log_handle
        if _sim_process and _sim_process.poll() is None:
            return False, "Simulation already running"

        cmd = _build_sim_command(world, gui, with_controllers, helper_nodes)
        logfile = open(SIM_LOG_PATH, "w")
        try:
            _sim_process = subprocess.Popen(
                cmd,
                stdout=logfile,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd(),
                env=os.environ.copy(),
            )
            _sim_log_handle = logfile
        except Exception as exc:
            logfile.close()
            _sim_process = None
            _sim_log_handle = None
            return False, f"Failed to start Gazebo: {exc}"

    return True, f"Started Gazebo (PID {_sim_process.pid if _sim_process else 'unknown'})"


def stop_simulation() -> Tuple[bool, str]:
    with _sim_lock:
        global _sim_process
        global _sim_log_handle
        if not _sim_process or _sim_process.poll() is not None:
            _sim_process = None
            if _sim_log_handle:
                _sim_log_handle.close()
                _sim_log_handle = None
            return False, "Simulation not running"

        _sim_process.send_signal(signal.SIGINT)
        try:
            _sim_process.wait(timeout=10.0)
            msg = "Simulation stopped"
        except subprocess.TimeoutExpired:
            _sim_process.terminate()
            msg = "Simulation forced to stop"
        _sim_process = None
        if _sim_log_handle:
            _sim_log_handle.close()
            _sim_log_handle = None

        return True, msg


def simulation_status() -> dict:
    with _sim_lock:
        running = _sim_process is not None and _sim_process.poll() is None
        pid = _sim_process.pid if running and _sim_process else None
    return {
        "running": running,
        "pid": pid,
        "logfile": SIM_LOG_PATH if running else None,
    }


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


@app.route('/api/sim/status')
def api_sim_status():
    """
    Report whether gazebo.launch.py is currently running (PID, logfile).
    """
    return simulation_status()


@app.route('/api/sim/start', methods=['POST'])
def api_sim_start():
    """
    Start gazebo.launch.py with optional overrides from the JSON payload:
      { "world": "...", "gui": true/false, "with_controllers": true/false,
        "start_helper_nodes": true/false }
    """
    payload = request.get_json(silent=True) or {}
    ok, msg = start_simulation(
        world=payload.get("world"),
        gui=payload.get("gui"),
        with_controllers=payload.get("with_controllers"),
        helper_nodes=payload.get("start_helper_nodes"),
    )
    return {"ok": ok, "message": msg} | simulation_status()


@app.route('/api/sim/stop', methods=['POST'])
def api_sim_stop():
    """
    Stop the gazebo subprocess if it is running.
    """
    ok, msg = stop_simulation()
    return {"ok": ok, "message": msg} | simulation_status()


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
    atexit.register(stop_simulation)
    socketio.run(app, host='0.0.0.0', port=5000)                 # Start the dev server


# Standard Python pattern: only run main() if this file is executed directly,
# not when it is imported as a module.
if __name__ == '__main__':
    main()
