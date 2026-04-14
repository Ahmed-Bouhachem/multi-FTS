# Ubuntu 24.04 + Docker + ROS 2 Humble — Full Setup Guide

This is the complete setup and operations guide for running the multi-FTS workspace
on Ubuntu 24.04 with Docker. Everything runs inside a container; the host only needs
Docker, NVIDIA drivers, and an X server.

**Docker files:**
- `docker/humble/Dockerfile`
- `docker/humble/apt-packages.txt`
- `docker/humble/entrypoint.sh`
- `docker-compose.humble.yml`

---

## 0) Branch

All work lives on:

```
migration_humble_baseline_prep
```

---

## 1) Host: one-time setup

### 1a) Base tools

```bash
sudo apt update
sudo apt install -y git curl ca-certificates gnupg lsb-release x11-xserver-utils
```

### 1b) Docker Engine

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                   docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"
```

Log out and back in, then verify:

```bash
docker --version
docker run --rm hello-world
```

### 1c) NVIDIA Container Toolkit (required for Gazebo GPU rendering)

Without this, Ignition Gazebo will fail to initialise the OGRE2 render engine and
the GPU lidar sensor will never produce scan data.

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verify GPU is accessible to containers:

```bash
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi
```

You should see your GPU listed (e.g. RTX 5060 Laptop).

---

## 2) Clone the repository

```bash
mkdir -p ~/dev
cd ~/dev
git clone -b migration_humble_baseline_prep git@github.com:Ahmed-Bouhachem/multi-FTS.git
cd multi-FTS
```

---

## 3) Build and start the container

### 3a) Allow GUI from Docker

Run this once per host login (or add to `~/.bashrc`):

```bash
xhost +local:docker
```

Without this, Gazebo and RViz will fail to open windows (`cannot open display`).

### 3b) Build image and start container

```bash
cd ~/dev/multi-FTS
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

The container:
- Mounts the repo at `/workspaces/multi-FTS` (edits on the host are live inside)
- Uses `network_mode: host` so ROS 2 DDS discovery works without port mapping
- Passes `DISPLAY` through to the host X server for GUI windows
- Exposes `/dev/shm` for shared memory (required by FastDDS)

### 3c) Verify GPU inside container

```bash
nvidia-smi
```

Should show the GPU with driver version. If it shows `command not found`, the
NVIDIA Container Toolkit was not installed correctly on the host.

---

## 4) First-time workspace bootstrap (inside container, do once)

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/setup.bash
```

`--symlink-install` means Python launch files and config YAMLs are symlinked from
`src/` into `install/`, so editing them does not require a rebuild.

After any C++ change rebuild with:

```bash
colcon build --base-paths src --symlink-install
```

After a Python-only change (launch file, YAML) no rebuild is needed.

---

## 5) Run the simulation

### 5a) Kill any leftover processes first

Stale processes from a previous run cause duplicate nodes and unpredictable
lifecycle state. Always clean up before launching:

```bash
pkill -9 -f 'python3.*launch' 2>/dev/null
pkill -9 -f 'ign gazebo'      2>/dev/null
pkill -9 -f 'rviz2'           2>/dev/null
pkill -9 -f 'lifecycle_manager' 2>/dev/null
pkill -9 -f 'amcl'            2>/dev/null
pkill -9 -f 'map_server'      2>/dev/null
pkill -9 -f 'bt_navigator'    2>/dev/null
pkill -9 -f 'controller_server' 2>/dev/null
pkill -9 -f 'planner_server'  2>/dev/null
pkill -9 -f 'smoother_server' 2>/dev/null
pkill -9 -f 'behavior_server' 2>/dev/null
pkill -9 -f 'robot_state_publisher' 2>/dev/null
pkill -9 -f 'safety_stop'     2>/dev/null
pkill -9 -f 'twist_relay'     2>/dev/null
pkill -9 -f 'parameter_bridge' 2>/dev/null
ros2 daemon stop && ros2 daemon start
true
```

### 5b) Launch

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
ros2 launch bumperbot_description gazebo.launch.py world_name:=small_house
```

### 5c) Expected startup sequence (~45 seconds total)

| Time | What happens |
|------|--------------|
| 0–5s | Ignition Gazebo opens, world loads, OGRE2 render engine initialises |
| ~5s  | Robot spawns in Gazebo, diff-drive and joint controllers activate |
| ~11s | map_server and AMCL activate (`lifecycle_manager_localization`: Managed nodes are active) |
| ~17s | All Nav2 nodes activate (`lifecycle_manager_navigation`: Managed nodes are active) |
| ~17s | RViz opens with the map, robot pose arrow at origin, particle cloud visible |

In RViz you should see:
- The `small_house` map loaded (gray/white/black)
- **Navigation 2** panel bottom-left: `Navigation: active`, `Localization: active`
- AMCL particle cloud at the robot's initial position
- Laser scan points matching the walls around the robot

### 5d) Send a navigation goal

1. In RViz, click **Nav2 Goal** in the toolbar
2. Click and drag on the map to set a goal pose
3. The robot plans a path and drives to the goal
4. The **Feedback** field shows `reached` when done

You do not need to use `2D Pose Estimate` — AMCL is configured with
`set_initial_pose: true` so it auto-initialises at `(0, 0, 0)`.

---

## 6) Daily workflow

### Quick way (recommended) — shell aliases

Add these to your `~/.bashrc` on the host once:

```bash
# multi-FTS shortcuts
alias fts='cd ~/dev/multi-FTS && xhost +local:docker && docker start multi-fts-humble 2>/dev/null; docker exec -it multi-fts-humble bash'
alias fts-stop='docker stop multi-fts-humble'
alias fts-build='docker exec -it multi-fts-humble bash -c "source /opt/ros/humble/setup.bash && cd /workspaces/multi-FTS && colcon build --base-paths src --symlink-install && echo DONE"'
```

Then reload: `source ~/.bashrc`

From then on, entering the sim environment is just:

```bash
fts          # starts container if stopped, opens a shell
fts-stop     # stop when done
fts-build    # rebuild workspace from host terminal
```

---

### Long way (first time or after image rebuild)

First-time or after `docker compose build`:

```bash
cd ~/dev/multi-FTS
xhost +local:docker
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

Subsequent logins (container already exists):

```bash
docker start multi-fts-humble
docker exec -it multi-fts-humble bash
```

Inside the container, source and launch:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
# kill leftovers (see 5a), then:
ros2 launch bumperbot_description gazebo.launch.py world_name:=small_house
```

Stop the container when done:

```bash
docker stop multi-fts-humble
# or full teardown:
docker compose -f docker-compose.humble.yml down
```

---

## 7) Pull code updates and rebuild

From the host:

```bash
cd ~/dev/multi-FTS
git pull
```

Inside the container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
colcon build --base-paths src --symlink-install
source install/setup.bash
```

To rebuild only changed packages (faster):

```bash
colcon build --packages-select bumperbot_navigation bumperbot_localization --symlink-install
```

---

## 8) Adding new apt dependencies

Add the package name (one per line) to `docker/humble/apt-packages.txt`, then
rebuild the image:

```bash
docker compose -f docker-compose.humble.yml build --no-cache
```

---

## 9) Troubleshooting

### RViz: "No map received" or `Localization: inactive`

**Cause A — stale processes running from a previous session.**
Two `lifecycle_manager_localization` processes conflict and one crashes.
Fix: run the full kill block in section 5a, then relaunch.

**Cause B — `map_server` crashed.**
The Nav2 Humble `lifecycle_manager` has a known SIGABRT bug when its bond
heartbeat is delayed by simulation time. This is fixed in this repo by
setting `bond_timeout: 0.0` in both lifecycle managers.

**Cause C — FastDDS TRANSIENT_LOCAL race.**
If `navigation.launch.py` starts before `map_server` finishes activating, the
global costmap misses the latched `/map` message. This is fixed by the staggered
`TimerAction` delays in `gazebo.launch.py` (localization t+6s, navigation t+12s).

---

### Gazebo opens but no laser scan / "Waiting for init" in logs

**Cause:** OGRE2 GPU render context did not initialise.
The `ignition-gazebo-sensors-system` requires GPU rendering to create GPU lidar.

**Fix — verify GPU is active:**
```bash
nvidia-smi
# should show 'ign gazebo' as a GPU process once the world loads
```

If `nvidia-smi` shows no GPU processes, the container is missing GPU access.
Check `docker-compose.humble.yml` has `gpus: all` or the NVIDIA Container
Toolkit is installed correctly (section 1c).

**Do NOT use Mesa software rendering** (`LIBGL_ALWAYS_SOFTWARE=1`) for Gazebo —
OGRE2 cannot create a GL context on Mesa in this setup and the sensor will hang.

---

### `bt_navigator` fails to load behavior tree / Nav2 never reaches `active`

**Cause:** `bt_navigator.yaml` had hardcoded absolute paths (e.g.
`/home/ghost/FTS-repo/...`) that don't exist inside the container.

**Fix (already applied):** `navigation.launch.py` overrides the BT paths using
`get_package_share_directory("bumperbot_navigation")` so the paths resolve
correctly at launch time regardless of host layout.

---

### Robot is out of bounds of the costmap

**Cause:** The global costmap started before `map_server` published the full map,
so it stayed at its default 5 m × 5 m size.

**Fix:** The 6-second gap between localization start and navigation start
(`TimerAction` in `gazebo.launch.py`) gives `map_server` time to activate and
publish the map before the costmap static layer subscribes.

---

### GUI windows do not open (`cannot open display`)

```bash
# on host:
xhost +local:docker
echo $DISPLAY   # should be :1 or :0
```

Then restart the container with `docker compose ... up -d` so the updated
`DISPLAY` value is passed through.

---

### ROS 2 CLI commands return stale data or fail

```bash
ros2 daemon stop
ros2 daemon start
```

---

## 10) Key file locations

| What | Where |
|------|-------|
| Single-robot launch | `src/bumperbot_description/launch/gazebo.launch.py` |
| Nav2 navigation nodes | `src/bumperbot_navigation/launch/navigation.launch.py` |
| AMCL + map_server | `src/bumperbot_localization/launch/global_localization_launch.py` |
| AMCL config | `src/bumperbot_localization/config/amcl.yaml` |
| Global/local costmap | `src/bumperbot_navigation/config/planner_server.yaml` / `controller_server.yaml` |
| bt_navigator config | `src/bumperbot_navigation/config/bt_navigator.yaml` |
| Gazebo world | `src/bumperbot_description/worlds/small_house.world` |
| Pre-built map | `src/bumperbot_mapping/maps/small_house/map.yaml` |
| apt package list | `docker/humble/apt-packages.txt` |
