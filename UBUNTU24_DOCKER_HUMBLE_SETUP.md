# Ubuntu 24.04 + Docker + ROS 2 Humble (Official Migration Runbook)

Use this runbook on native Ubuntu 24.04 to work fully on Linux with ROS 2 Humble in Docker.

## 0) Target branch

Use this branch as the starting point:

- `migration_humble_baseline_prep`

If you merge it to `main` later, replace the branch name in clone commands.

## 1) Host setup on Ubuntu 24.04

Install basic host tools:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates gnupg lsb-release x11-xserver-utils
```

Install Docker Engine:

```bash
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

Log out and log back in once, then verify:

```bash
docker --version
docker run --rm hello-world
```

## 2) Clone repository on host

```bash
mkdir -p ~/dev
cd ~/dev

# SSH
git clone -b migration_humble_baseline_prep git@github.com:Ahmed-Bouhachem/multi-FTS.git

# OR HTTPS
# git clone -b migration_humble_baseline_prep https://github.com/Ahmed-Bouhachem/multi-FTS.git

cd multi-FTS
git status
```

## 3) Start Humble container (GUI-capable)

Allow local Docker containers to use your X display:

```bash
xhost +local:docker
```

Pull base ROS image:

```bash
docker pull osrf/ros:humble-desktop
```

Create and enter dev container:

```bash
docker run -it --name multi-fts-humble \
  --network host \
  --ipc host \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v ~/dev/multi-FTS:/workspaces/multi-FTS \
  osrf/ros:humble-desktop bash
```

## 4) Install required packages inside container

Run once inside container:

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

Initialize rosdep (inside container):

```bash
rosdep init || true
rosdep update
```

## 5) Build workspace inside container

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/setup.bash
```

## 6) Daily workflow

From host terminal:

```bash
docker start multi-fts-humble
docker exec -it multi-fts-humble bash
```

Inside container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
```

## 7) Notes and rules

- Do not apt-install local workspace packages: `bumperbot_description`, `bumperbot_motion`, `bumperbot_msgs`, `bumperbot_planning`.
- Keep repository on host (`~/dev/multi-FTS`) and mount it into Docker. Do not use container-only clones for development.
- If GUI apps fail, rerun `xhost +local:docker` on host and verify `echo $DISPLAY`.
