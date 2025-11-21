# FTS

## Latest Updates

### ✅ Working ros2_control Integration (Gazebo Sim)
- Successfully implemented differential drive controller
- Fixed controller configuration issues
- Robot now responds to velocity commands in Gazebo Sim (Ignition)
- Mock hardware simulation working properly

### Quick Test
```bash
# Launch robot with controllers
ros2 launch bumperbot_description gazebo.launch.py

# Control the robot
ros2 topic pub /diff_drive_controller/cmd_vel geometry_msgs/msg/Twist \
  "linear: {x: 0.5} angular: {z: 0.2}" --rate 10
```

## Quick Start Cheatsheet

```bash
# 1) Source and build
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

# 2) Start simulation + controllers (Gazebo Sim / Ignition)
ros2 launch bumperbot_description gazebo.launch.py

# 3) Start Web UI teleop (publishes cmd_vel)
source ../.venv/bin/activate
bash scripts/run_web_ui.sh

# 4) Visualize in RViz (preconfigured)
rviz2 -d $(ros2 pkg prefix bumperbot_description)/share/bumperbot_description/rviz/display.rviz
```

## Web UI Teleop (cmd_vel)

The Web UI publishes velocity commands to the diff drive controller.

- Default (unstamped): publishes `geometry_msgs/msg/Twist` to `/bumperbot_controller/cmd_vel_unstamped`.
- Stamped mode: set `USE_STAMPED_VEL=1` to publish `geometry_msgs/msg/TwistStamped` to `/bumperbot_controller/cmd_vel`.

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

## Visualizing in RViz2

Make sure a model publisher is running, then open RViz2.

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

## PlotJuggler (Live Telemetry Plots)

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

## Project Structure
- `src/bumperbot_description/`: Robot URDF and launch files
- `src/bumperbot_controller/`: ros2_control configuration
- `src/bumperbot_cpp_examples/`: C++ example nodes

## Simulation Options

You can simulate with either Gazebo Sim (Ignition) or Webots.

### Gazebo Sim (Ignition)
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
```

Notes: The helper scripts now wrap `gazebo.launch.py`, so `scripts/run_gazebo.sh` / `scripts/stop_gazebo.sh` automatically benefit from the options above.
### Webots
- Launch Webots with the provided world and publish robot_description:
  - `source install/setup.bash`
  - `ros2 launch bumperbot_description webots.launch.py`
  - Optionally choose a custom world: `ros2 launch bumperbot_description webots.launch.py world:=/path/to/world.wbt`

This Webots launch starts the simulator and publishes the bumperbot model TF tree via `robot_state_publisher`. To control the robot in Webots, add a `webots_ros2_driver`-based controller and interface nodes as needed.

## Turtlesim Kinematics Example
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

## Git: Push Your Changes

Use the standard Git flow to push updates (including doc changes) to GitHub.

```bash
git status
git add -A
git commit -m "Update docs and configs"
git push origin main
```

## Dependencies (ROS 2 Humble on Ubuntu)

Install the required packages for building and running with Gazebo Sim (Ignition) and Webots.

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

Build workspace:

```bash
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```
