# FTS

## Latest Updates

### ✅ Working ros2_control Integration (Gazebo Classic)
- Successfully implemented differential drive controller
- Fixed controller configuration issues
- Robot now responds to velocity commands in Gazebo
- Mock hardware simulation working properly

### Quick Test
```bash
# Launch robot with controllers
ros2 launch bumperbot_description gazebo_simple_control.launch.py

# Control the robot
ros2 topic pub /diff_drive_controller/cmd_vel geometry_msgs/msg/Twist \
  "linear: {x: 0.5} angular: {z: 0.2}" --rate 10
```

## Project Structure
- `src/bumperbot_description/`: Robot URDF and launch files
- `src/bumperbot_controller/`: ros2_control configuration
- `src/bumperbot_cpp_examples/`: C++ example nodes

## Simulation Options

You can simulate with either Gazebo Classic or Webots.

### Gazebo Classic
- Headless with controllers:
  - `source install/setup.bash`
  - `bash scripts/run_gazebo.sh --control`

- GUI client as well:
  - `bash scripts/run_gazebo.sh --control --gui`

- Simple spawn (no controllers):
  - `bash scripts/run_gazebo.sh --simple`

- Stop Gazebo:
  - `bash scripts/stop_gazebo.sh`

Notes: You can also launch directly with `ros2 launch bumperbot_description gazebo_simple_control.launch.py`. The scripts help kill stale processes and manage logs.

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

## Dependencies (ROS 2 Humble on Ubuntu)

Install the required packages for building and running with Gazebo Classic and Webots.

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

# Gazebo Classic + ROS integration
sudo apt install -y \
  gazebo \
  ros-humble-gazebo-ros \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control

# Webots + ROS integration
sudo apt install -y \
  webots \
  ros-humble-webots-ros2-driver
```

Build workspace:

```bash
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```
