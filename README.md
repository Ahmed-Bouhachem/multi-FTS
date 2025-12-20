# FTS

High‑level teleop, simulation, mapping, and localization for the Bumperbot robot using ROS 2 Humble.

---

## 1. Install & Build

### 1.1 Dependencies (ROS 2 Humble on Ubuntu)

Install the required packages for building and running with Gazebo Sim (Ignition), Webots, and tools:

```bash
sudo apt update

# Core build + description tools
sudo apt install -y \
  ros-humble-ament-cmake \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-geometry-msgs \
  ros-humble-std-msgs

# ros2_control and controllers
sudo apt install -y \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-controller-manager

# Gazebo Sim (Ignition) + ROS integration
sudo apt install -y \
  ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge \
  ros-humble-gz-ros2-control

# Webots + ROS integration
sudo apt install -y \
  webots \
  ros-humble-webots-ros2-driver

# Plotting / debugging tools
sudo apt install -y \
  ros-humble-plotjuggler-ros
```

### 1.2 Build the Workspace

```bash
cd ~/FTS-repo
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

---

## 2. Quick Start (Simulation + Web UI + RViz)

```bash
# 1) Source and build (once per shell)
source /opt/ros/humble/setup.bash
cd ~/FTS-repo
colcon build
source install/setup.bash

# 2) Start simulation + controllers (Gazebo Sim / Ignition)
ros2 launch bumperbot_description gazebo.launch.py

# 3) Start Web UI teleop (publishes cmd_vel)
bash scripts/run_web_ui.sh          # starts http://localhost:5000

# 4) Visualize robot in RViz (preconfigured view)
rviz2 -d $(ros2 pkg prefix bumperbot_description)/share/bumperbot_description/rviz/display.rviz
```

---

## 3. Web UI Teleop (cmd_vel)

The Web UI publishes velocity commands to the diff‑drive controller.

- Default (unstamped): publishes `geometry_msgs/msg/Twist` to `/bumperbot_controller/cmd_vel_unstamped`.
- Stamped mode: set `USE_STAMPED_VEL=1` to publish `geometry_msgs/msg/TwistStamped` to `/bumperbot_controller/cmd_vel`.
- Optional `twist_mux` + `safety_stop` integration:
  - Set `WEBUI_USE_TWIST_MUX=1` to publish to the `joy_vel` input of `twist_mux` so locks such as `/safety_stop` can stop the robot.

Run it quickly:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
bash scripts/run_web_ui.sh                # starts http://localhost:5000
# optional stamped mode
# USE_STAMPED_VEL=1 bash scripts/run_web_ui.sh
```

Debug topics while moving the on‑screen joystick:

```bash
# Unstamped (default)
ros2 topic echo /bumperbot_controller/cmd_vel_unstamped

# Stamped mode
ros2 topic echo /bumperbot_controller/cmd_vel geometry_msgs/msg/TwistStamped
```

---

## 4. Visualizing in RViz2

### 4.1 Robot Model + TF

Make sure a model publisher is running, then open RViz2:

```bash
# Model only (no controllers)
ros2 launch bumperbot_description display.launch.py

# Or full sim + controllers
ros2 launch bumperbot_description gazebo.launch.py

# RViz with preconfigured view
rviz2 -d $(ros2 pkg prefix bumperbot_description)/share/bumperbot_description/rviz/display.rviz
```

If you open plain `rviz2`, set:

- Fixed Frame: `base_footprint` (or `base_link`)
- Add displays: TF and RobotModel (Topic: `/robot_description`)

Quick checks:

```bash
ros2 topic list | egrep -x '/robot_description|/tf|/tf_static'
ros2 node list | grep robot_state_publisher
ros2 topic echo -n1 /tf_static
```

### 4.2 Showing the Global Map (`/map`) in RViz2

To visualize the precomputed `small_house` occupancy grid on the `/map` topic:

```bash
# Terminal 1: start map server + lifecycle manager
ros2 launch bumperbot_localization global_localization_launch.py

# Terminal 2: start RViz2
rviz2
```

Then in RViz2:

- Set `Global Options → Fixed Frame` to `map` (type `map` even if it doesn’t appear in the dropdown).
- Add a `Map` display (or select an existing one) and set:
  - `Topic` to `/map`
  - QoS `Reliability Policy` to `Reliable`
  - QoS `Durability Policy` to `Transient Local`

---

## 5. PlotJuggler (Live Telemetry Plots)

Plot noisy controller odometry, wheel speeds, or any other ROS 2 topic in real time.

1. Ensure the helper nodes are running so `/bumperbot_controller/odom_noisy` is being published:
   ```bash
   ros2 launch bumperbot_description gazebo.launch.py start_helper_nodes:=true
   ```
2. Launch PlotJuggler with ROS 2 integration:
   ```bash
   ros2 run plotjuggler plotjuggler --ros2
   ```
3. In PlotJuggler, open the ROS 2 streaming data source and add signals such as
   `/bumperbot_controller/odom_noisy/pose/pose/position/x` or `/joint_states/velocity[wheel_left_joint]`.

Tip: save the layout once you have the plots you like so you can reload them next time.

---

## 6. Project Structure
- `src/bumperbot_description/`: Robot URDF and launch files
- `src/bumperbot_controller/`: ros2_control configuration
- `src/bumperbot_cpp_examples/`: C++ example nodes

---

## 7. Simulation Options

You can simulate with either Gazebo Sim (Ignition) or Webots.

### 7.1 Gazebo Sim (Ignition)
- Headless with controllers (default):
  - `source install/setup.bash`
  - `bash scripts/run_gazebo.sh --control`

- Show the GUI instead of headless:
  - `bash scripts/run_gazebo.sh --control --gui`

- Simple spawn (no controllers):
  - `bash scripts/run_gazebo.sh --simple`

- Load a specific world resource:
  - `bash scripts/run_gazebo.sh --world my_world.sdf`

- Stop Gazebo Sim:
  - `bash scripts/stop_gazebo.sh`

Built-in Ignition worlds (located under `share/bumperbot_description/worlds`) can be referenced directly or by passing their short names to `gazebo.launch.py` / `scripts/run_gazebo.sh`:
- `empty.world` – flat plane with bright lighting (default)
- `small_house.world` – furnished residential interior using AWS RoboMaker assets
- `small_warehouse.world` – warehouse-style layout with pallets, shelving, and clutter

`gazebo.launch.py` is the single entry point for all Gazebo Sim workflows and now launches `ign gazebo` under the hood. Useful arguments:
- `with_controllers:=true|false` – start ros2_control spawners (defaults to `true`)
- `start_helper_nodes:=true|false` – launch `noisy_controller`, `simple_controller`, and localization helpers
- `model:=/abs/path/to/model.xacro` – choose between the detailed (`bumperbot.urdf.xacro`) or simple (`bumperbot_simple.urdf.xacro`) robot
- `world:=/abs/path/to/world.sdf` – load any SDF world file by path
- `world_name:=small_house` – shorthand for built-in worlds shipped in `bumperbot_description/worlds` (`empty`, `small_house`, `small_warehouse`, …). Overrides `world` when set.
- `gui:=true|false`, `world:=<resource>`, `spawn_x/y/z:=<value>` – pass directly to Gazebo Sim

Examples:
```bash
# Detailed robot with controllers (default behavior)
ros2 launch bumperbot_description gazebo.launch.py

# Simple boxy robot without controllers
ros2 launch bumperbot_description gazebo.launch.py \
  model:=$(ros2 pkg prefix bumperbot_description)/share/bumperbot_description/urdf/bumperbot_simple.urdf.xacro \
  with_controllers:=false start_helper_nodes:=false

# Furnished house world with GUI
ros2 launch bumperbot_description gazebo.launch.py gui:=true \
  world:=$(ros2 pkg prefix bumperbot_description)/share/bumperbot_description/worlds/small_house.world

# Same house using shorthand name
ros2 launch bumperbot_description gazebo.launch.py world_name:=small_house gui:=true
```

Notes: The helper scripts now wrap `gazebo.launch.py`, so `scripts/run_gazebo.sh` / `scripts/stop_gazebo.sh` automatically benefit from the options above.
### 7.2 Webots
- Launch Webots with the provided world and publish robot_description:
  - `source install/setup.bash`
  - `ros2 launch bumperbot_description webots.launch.py`
  - Optionally choose a custom world: `ros2 launch bumperbot_description webots.launch.py world:=/path/to/world.wbt`

This Webots launch starts the simulator and publishes the bumperbot model TF tree via `robot_state_publisher`. To control the robot in Webots, add a `webots_ros2_driver`-based controller and interface nodes as needed.

---

## 8. Turtlesim Kinematics Example
This example subscribes to `/turtle1/pose` and `/turtle2/pose` and logs the XY translation, distance, and relative heading (Δθ) from turtle1 to turtle2.

Build the examples:
```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select bumperbot_cpp_examples
source install/setup.bash
```

Launch turtlesim and the kinematics node:
```bash
ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py
```

Customize turtle2 spawn:
```bash
ros2 launch bumperbot_cpp_examples turtlesim_kinematics.launch.py x:=8.0 y:=3.0 theta:=1.57 name:=buddy
```

Stop the turtlesim kinematics launch:
```bash
bash scripts/stop_turtlesim_kinematics.sh
```

Convenience run script (with background option):
```bash
# foreground
bash scripts/run_turtlesim_kinematics.sh --x 8.0 --y 3.0 --theta 1.57 --name buddy

# background with logs to log/turtlesim_launch.log
bash scripts/run_turtlesim_kinematics.sh --background
```

---

## 9. Path Following Controllers (A* + PD / Pure Pursuit)

Two motion controllers are provided in `bumperbot_motion` for following grid paths produced by the A* planner:

- `pd_motion_planner` – PD controller that tracks the path using a look‑ahead point.
- `pure_pursuit` – classic pure‑pursuit controller using a carrot point and curvature.

Both consume the path from `/a_star/path` and publish velocity commands to the diff‑drive controller on `/bumperbot_controller/cmd_vel_unstamped`.

Typical workflow:

```bash
# Terminal 1: Gazebo + controllers (+ optional SLAM or localization)
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch bumperbot_description gazebo.launch.py use_slam:=true   # or :=false with localization

# Terminal 2: A* global planner (publishes /a_star/path)
ros2 run bumperbot_planning a_star_planner

# Terminal 3: PD motion planner OR pure pursuit controller
ros2 run bumperbot_motion pd_motion_planner        # PD tracking
# ros2 run bumperbot_motion pure_pursuit          # alternative pure pursuit tracking
```

In RViz (using `global_localization.rviz` or a similar setup):

- Fixed Frame: `map`
- Use the `2D Goal Pose` tool (topic `/goal_pose`) to set a goal.
- You should see:
  - Global path on `/a_star/path`
  - Next target pose on `/pd/next_pose` (PD) or `/pure_pursuit/carrot` (pure pursuit)
  - Velocity commands on `/bumperbot_controller/cmd_vel_unstamped`

---

## 10. Git: Push Your Changes

Use the standard Git flow to push updates (including doc changes) to GitHub.

```bash
git status
git add -A
git commit -m "Update docs and configs"
git push origin main
```

---

## 11. Costmap Standalone Test Commands

Run the Nav2 costmap node with the bumperbot costmap configuration:

```bash
cd ~/FTS-repo
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run nav2_costmap_2d nav2_costmap_2d --ros-args \
  --params-file ~/FTS-repo/src/bumperbot_navigation/config/costmap.yaml
```

Useful lifecycle commands for the costmap node:

```bash
ros2 lifecycle get /costmap/costmap

# Configure and activate the costmap
ros2 lifecycle set /costmap/costmap configure   # (transition id 1)
ros2 lifecycle set /costmap/costmap activate    # (transition id 3)
```
