# README Ubuntu (Exact Steps)

This is the exact workflow to move from Windows/WSL to native Ubuntu 24.04 with Docker and keep using ROS 2 Humble.

## 1) One-time host setup (Ubuntu 24.04)

```bash
sudo apt update
sudo apt install -y git curl ca-certificates gnupg lsb-release x11-xserver-utils

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

Log out and log in once, then verify:

```bash
docker --version
docker run --rm hello-world
```

## 2) Clone project on Ubuntu

```bash
mkdir -p ~/dev
cd ~/dev
git clone -b migration_humble_baseline_prep git@github.com:Ahmed-Bouhachem/multi-FTS.git
cd multi-FTS
```

## 3) Build and start Docker dev container

Allow GUI apps from Docker:

```bash
xhost +local:docker
```

Build and start:

```bash
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

## 4) First-time inside container (do once)

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/setup.bash
```

## 5) Run simulation (inside container)

Before launch, clean any old leftover processes:

```bash
killall -q ign rviz2 amcl bt_navigator controller_server planner_server smoother_server behavior_server lifecycle_manager spawner robot_state_publisher map_server noisy_controller simple_controller parameter_bridge create gzserver gzclient twist_relay safety_stop ros2 || true
```

Run:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
ros2 launch bumperbot_description gazebo.launch.py
```

In RViz:
- Use `2D Pose Estimate` once.
- Then send goal with `Nav2 Goal`.

## 6) Daily workflow

From Ubuntu host:

```bash
cd ~/dev/multi-FTS
xhost +local:docker
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

Inside container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
```

## 7) Pull latest code updates

From host:

```bash
cd ~/dev/multi-FTS
git pull
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

Inside container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
colcon build --base-paths src --symlink-install
source install/setup.bash
```

## 8) Stop everything

From host:

```bash
cd ~/dev/multi-FTS
docker compose -f docker-compose.humble.yml down
```

## 9) If GUI is slow or unstable

On host:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

Then start container again.
