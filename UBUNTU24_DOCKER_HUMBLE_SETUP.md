# Ubuntu 24.04 + Docker + ROS 2 Humble (Migration Runbook)

This is the official Linux migration path for this workspace.

It uses repository-native Docker files so setup is reproducible:

- `docker/humble/Dockerfile`
- `docker/humble/apt-packages.txt`
- `docker/humble/entrypoint.sh`
- `docker-compose.humble.yml`

## 0) Target branch

Use this branch:

- `migration_humble_baseline_prep`

## 1) Host setup on Ubuntu 24.04

Install host tools:

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

Log out and back in once, then verify:

```bash
docker --version
docker run --rm hello-world
```

## 2) Clone repository on host

```bash
mkdir -p ~/dev
cd ~/dev
git clone -b migration_humble_baseline_prep git@github.com:Ahmed-Bouhachem/multi-FTS.git
cd multi-FTS
git status
```

## 3) Build and start container

Allow Docker GUI access for Gazebo / RViz:

```bash
xhost +local:docker
```

Build and start the dev container:

```bash
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

## 4) First-time workspace bootstrap (inside container)

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/setup.bash
```

## 5) Daily workflow

From host:

```bash
cd ~/dev/multi-FTS
docker compose -f docker-compose.humble.yml up -d
docker compose -f docker-compose.humble.yml exec fts-dev bash
```

Inside container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/multi-FTS
source install/setup.bash
```

Stop container when done:

```bash
docker compose -f docker-compose.humble.yml down
```

## 6) Dependency source of truth

All apt dependencies installed into the image are listed in:

- `docker/humble/apt-packages.txt`

Update that file when adding new Ubuntu/ROS package dependencies.

## 7) Notes

- Keep repository on host and mount it into container (already done in `docker-compose.humble.yml`).
- Do not install local workspace packages via apt (`bumperbot_description`, `bumperbot_motion`, `bumperbot_msgs`, `bumperbot_planning`).
- If GUI apps fail, rerun `xhost +local:docker` and verify `echo $DISPLAY`.
- If GPU acceleration is unstable, set software rendering before launching:
  - `export LIBGL_ALWAYS_SOFTWARE=1`
