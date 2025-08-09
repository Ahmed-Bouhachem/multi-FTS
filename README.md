# FTS

## Latest Updates

### ✅ Working ros2_control Integration
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

## Quick Launch
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
