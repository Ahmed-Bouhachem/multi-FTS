# Ubuntu 24.04 + Docker + ROS 2 Humble Setup

This file is the post-migration reference for running this workspace on native Ubuntu 24.04 with a Humble Docker container.

## 1) Install Docker on Ubuntu 24.04 host

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and log back in once to apply Docker group permissions.

## 2) Base packages to install inside the Humble container

```bash
apt update && apt install -y \
  build-essential git curl gnupg2 lsb-release locales \
  python3-colcon-common-extensions python3-rosdep python3-vcstool python3-pip \
  libeigen3-dev \
  ros-humble-action-msgs \
  ros-humble-ament-cmake \
  ros-humble-controller-manager \
  ros-humble-geometry-msgs \
  ros-humble-gz-ros2-control \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-launch \
  ros-humble-launch-ros \
  ros-humble-nav-msgs \
  ros-humble-nav2-amcl \
  ros-humble-nav2-bt-navigator \
  ros-humble-nav2-controller \
  ros-humble-nav2-core \
  ros-humble-nav2-costmap-2d \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-nav2-map-server \
  ros-humble-nav2-msgs \
  ros-humble-nav2-planner \
  ros-humble-nav2-rviz-plugins \
  ros-humble-nav2-smoother \
  ros-humble-nav2-util \
  ros-humble-nav2-waypoint-follower \
  ros-humble-pluginlib \
  ros-humble-rcl-interfaces \
  ros-humble-rclcpp \
  ros-humble-rclcpp-action \
  ros-humble-rclcpp-components \
  ros-humble-rclcpp-lifecycle \
  ros-humble-rclpy \
  ros-humble-robot-localization \
  ros-humble-robot-state-publisher \
  ros-humble-ros-gz-bridge \
  ros-humble-ros-gz-sim \
  ros-humble-ros2-controllers \
  ros-humble-ros2launch \
  ros-humble-rosidl-default-generators \
  ros-humble-rosidl-default-runtime \
  ros-humble-rviz2 \
  ros-humble-sensor-msgs \
  ros-humble-slam-toolbox \
  ros-humble-std-msgs \
  ros-humble-tf-transformations \
  ros-humble-tf2 \
  ros-humble-tf2-geometry-msgs \
  ros-humble-tf2-ros \
  ros-humble-turtlesim \
  ros-humble-twist-mux-msgs \
  ros-humble-visualization-msgs \
  ros-humble-webots-ros2-driver \
  ros-humble-xacro
```

## 3) Workspace build sequence inside container

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/setup.bash
```

## 4) Notes

- Do not apt-install local workspace packages: `bumperbot_description`, `bumperbot_motion`, `bumperbot_msgs`, `bumperbot_planning`.
- Keep development on Linux host + Docker only, and treat Windows/WSL as legacy fallback.
