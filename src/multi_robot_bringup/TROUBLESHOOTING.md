# Multi-Robot Bringup -- Problems & Fixes

This document covers every issue encountered while building the `multi_robot_bringup` package and the fix applied to each one.

---

## 1. Ogre2 Segfault When Spawning Two Robots

**Symptom:** Gazebo crashes with `libGLdispatch.so.0` segfault as soon as the second robot spawns.

**Root cause:** Both robots loaded the world-level `Sensors` and `IMU` system plugins (defined in `bumperbot_gazebo.xacro`). These are singletons -- loading them twice crashes the Ogre2 rendering engine.

**Fix:** Added an `is_primary` parameter to the `bumperbot_gazebo` xacro macro. Only the first robot (`is_primary=true`) loads the Sensors/IMU plugins. The second robot sets `is_primary=false`.

**File:** `src/bumperbot_description/urdf/bumperbot_gazebo.xacro`

```xml
<xacro:macro name="bumperbot_gazebo" params="ros_namespace is_primary:=true">
  ...
  <xacro:if value="${is_primary}">
    <plugin filename="ignition-gazebo-imu-system" .../>
    <plugin filename="ignition-gazebo-sensors-system" ...>
      <render_engine>ogre2</render_engine>
    </plugin>
  </xacro:if>
</xacro:macro>
```

---

## 2. Controllers Failed to Load Under Namespace

**Symptom:** `ros2_control` controller_manager at `/robot1/controller_manager` could not find controller parameters. Controllers failed to spawn.

**Root cause:** The `bumperbot_controllers.yaml` had parameters at the root level (`controller_manager: ...`). When the controller_manager runs under a namespace (`/robot1/controller_manager`), it can't match root-level params.

**Fix:** Wrapped the entire yaml under the `/**:` wildcard, which matches any namespace.

**File:** `src/bumperbot_controller/config/bumperbot_controllers.yaml`

```yaml
# Before
controller_manager:
  ros__parameters: ...

# After
/**:
  controller_manager:
    ros__parameters: ...
```

---

## 3. TF Frame Names Prefixed With Namespace

**Symptom:** TF frames appeared as `robot1/odom` and `robot1/base_footprint` instead of plain `odom` and `base_footprint`. Nav2 couldn't find them.

**Root cause:** The `diff_drive_controller` auto-prefixes the namespace to frame names when `tf_frame_prefix_enable` is `true` (the default).

**Fix:** Set `tf_frame_prefix_enable: false` in the controller config. Frame names stay generic (`odom`, `base_link`) because each robot's TF is isolated on its own namespaced topic.

**File:** `src/bumperbot_controller/config/bumperbot_controllers.yaml`

```yaml
bumperbot_controller:
  ros__parameters:
    tf_frame_prefix_enable: false
```

---

## 4. TF Leaking to Global `/tf` Topic

**Symptom:** Both robots published transforms to the global `/tf` topic, causing frame collisions (two different `odom -> base_footprint` transforms).

**Root cause:** The `ign_ros2_control` plugin publishes TF to `/tf` by default (absolute topic).

**Fix:** Added `<remapping>` tags inside the plugin's `<ros>` block to redirect TF to relative topics. Under namespace `robot1`, relative `tf` resolves to `/robot1/tf`.

**File:** `src/bumperbot_description/urdf/bumperbot_gazebo.xacro`

```xml
<plugin filename="ign_ros2_control-system" ...>
  <ros>
    <namespace>${ros_namespace}</namespace>
    <remapping>/tf:=tf</remapping>
    <remapping>/tf_static:=tf_static</remapping>
  </ros>
</plugin>
```

The same remapping (`[("/tf", "tf"), ("/tf_static", "tf_static")]`) is applied to every ROS2 node in the launch files: robot_state_publisher, AMCL, map_server, and all Nav2 nodes.

---

## 5. LaunchConfiguration Namespace Leak Between Robots

**Symptom:** Both robots launched with robot2's namespace. All nodes ran as `/robot2/*`.

**Root cause:** When `multi_sim.launch.py` included `robot_bringup.launch.py` twice (for robot1 and robot2), the `LaunchConfiguration` values from the second include overwrote the first. ROS2 launch shares LaunchConfigurations in a flat scope.

**Fix:** Rewrote `robot_bringup.launch.py` to expose a Python function `robot_bringup_actions(namespace, initial_x, initial_y)` that takes concrete Python strings instead of `LaunchConfiguration`. The parent launch file imports it via `importlib.util` and calls it directly for each robot.

**File:** `src/multi_robot_bringup/launch/robot_bringup.launch.py`

```python
def robot_bringup_actions(namespace: str, initial_x: float, initial_y: float):
    # All values are concrete Python strings -- no LaunchConfiguration leaks
    cm_path = f"/{namespace}/controller_manager"
    ...
```

**File:** `src/multi_robot_bringup/launch/multi_sim.launch.py`

```python
_spec = importlib.util.spec_from_file_location(
    "robot_bringup", os.path.join(pkg, "launch", "robot_bringup.launch.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

bringup_robot1_actions = _mod.robot_bringup_actions("robot1", 0.0, 0.0)
bringup_robot2_actions = _mod.robot_bringup_actions("robot2", 1.5, 0.0)
```

---

## 6. Nav2 Lifecycle Manager Service Timeout

**Symptom:** `lifecycle_manager_navigation` for robot1 timed out waiting for `smoother_server/change_state`. One of the two Nav2 stacks failed to activate.

**Root cause:** Both robots' Nav2 stacks started simultaneously, overloading service discovery and lifecycle transitions.

**Fix:** Staggered bringup with `TimerAction`: robot1 at t+8s, robot2 at t+14s, RViz at t+45s.

**File:** `src/multi_robot_bringup/launch/multi_sim.launch.py`

```python
TimerAction(period=8.0,  actions=bringup_robot1_actions),
TimerAction(period=14.0, actions=bringup_robot2_actions),
TimerAction(period=45.0, actions=[rviz_robot1]),
```

---

## 7. Nav2 Nodes Could Not Find Plugin Parameters

**Symptom:** `controller_server` logged "No critics defined for FollowPath". Plugins like `RegulatedPurePursuitController` failed to initialize.

**Root cause:** Same as issue #2 -- the `nav2_params.yaml` had parameters at root level. Namespaced nodes (`/robot1/controller_server`) couldn't find them.

**Fix:** Wrapped the entire `nav2_params.yaml` under `/**:`.

**File:** `src/multi_robot_bringup/config/nav2_params.yaml`

---

## 8. AMCL Not Publishing Particle Cloud or map->odom Transform

**Symptom:** AMCL activated, received the map, created the laser object (one scan got through), but then stopped processing scans entirely. The `map -> odom` transform was published once at activation and then expired from the TF buffer. No `particle_cloud` data.

**Root cause:** AMCL's internal `tf2_ros::MessageFilter` could not reliably resolve the `laser_link` frame when using namespaced TF topics. Without an explicit `laser_frame_id`, AMCL inferred the frame from the scan header, but the MessageFilter's transform lookup intermittently failed with the remapped TF topics.

**Fix:** Added `laser_frame_id: "laser_link"` to the AMCL parameters, explicitly telling AMCL which frame to use for the scan data.

**File:** `src/multi_robot_bringup/config/nav2_params.yaml`

```yaml
amcl:
  ros__parameters:
    scan_topic: scan
    laser_frame_id: "laser_link"
```

---

## 9. Costmap Not Receiving Map or Scan Data

**Symptom:** Global costmap logged "Can't update static costmap layer, no map received" every 10 seconds. Local costmap obstacle layer received no scan data. Both costmaps were subscribing to the wrong topics.

**Root cause:** Nav2 costmap nodes run as sub-nodes with their own namespace (e.g. `/robot1/global_costmap/`). When the static layer subscribes to the relative topic `map`, it resolves to `/robot1/global_costmap/map` instead of the correct `/robot1/map`. Same issue for `scan` resolving to `/robot1/local_costmap/scan`.

**Fix:** Generated a per-robot YAML override file at launch time with absolute topic paths. This file is passed as an additional parameter file to the `controller_server` and `planner_server` nodes, overriding the relative topic names with correct absolute ones.

**File:** `src/multi_robot_bringup/launch/robot_bringup.launch.py`

```python
def _write_costmap_overrides(namespace: str) -> str:
    overrides = {
        "/**": {
            "local_costmap": {
                "local_costmap": {
                    "ros__parameters": {
                        "obstacle_layer": {
                            "scan": {"topic": f"/{namespace}/scan"}
                        }
                    }
                }
            },
            "global_costmap": {
                "global_costmap": {
                    "ros__parameters": {
                        "static_layer": {"map_topic": f"/{namespace}/map"},
                        "obstacle_layer": {
                            "scan": {"topic": f"/{namespace}/scan"}
                        }
                    }
                }
            },
        }
    }
    # Write to tempfile and pass as additional params
```

---

## 10. Nav2 RViz Panel Showing "Unknown" Status

**Symptom:** The Navigation 2 panel in RViz displayed "Navigation: unknown" and "Localization: unknown", even though Nav2 was fully active and navigation goals worked.

**Root cause:** The Nav2 RViz plugin creates its own internal action client at the root namespace (`/navigate_to_pose`), but the actual action servers are namespaced (`/robot1/navigate_to_pose`).

**Fix:** Added `namespace="robot1"` to the RViz node in the launch file. This puts the RViz node under the `/robot1/` namespace, so the Nav2 plugin's action client resolves to `/robot1/navigate_to_pose`.

**File:** `src/multi_robot_bringup/launch/rviz_robot1.launch.py`

```python
rviz = Node(
    package="rviz2",
    executable="rviz2",
    name="rviz2_robot1",
    namespace="robot1",
    ...
)
```

---

## 11. RViz "Frame [map] does not exist"

**Symptom:** RViz displayed "Frame [map] does not exist" error and showed nothing when it launched.

**Root cause:** RViz started before AMCL had published the `map -> odom` transform. Without this transform, the `map` frame didn't exist in the TF tree that RViz subscribed to.

**Fix:** Delayed RViz launch to t+45s (after both Nav2 stacks are fully warmed up).

---

## 12. RobotModel Not Visible in RViz

**Symptom:** The RobotModel display was enabled but showed nothing.

**Root cause:** The RViz config used `Description Source: File` (default), but in the namespaced setup the URDF is published as a topic (`/robot1/robot_description`), not loaded from a file.

**Fix:** Changed the RobotModel display to use `Description Source: Topic` with the correct topic path.

**File:** `src/multi_robot_bringup/rviz/nav2_robot1.rviz`

```yaml
- Class: rviz_default_plugins/RobotModel
  Description Source: Topic
  Description Topic:
    Value: /robot1/robot_description
```

---

## Architecture Summary

```
/robot1/tf          <-- robot1's isolated TF tree (map->odom->base_footprint->base_link->laser_link)
/robot2/tf          <-- robot2's isolated TF tree (same frame names, no conflict)
/robot1/scan        <-- robot1 laser via IGN bridge
/robot1/map         <-- map_server (shared map, namespaced topic)
/robot1/particle_cloud  <-- AMCL particles
/robot1/local_costmap/costmap   <-- rolling obstacle map
/robot1/global_costmap/costmap  <-- static + obstacle map
/robot1/navigate_to_pose        <-- Nav2 action server
```

One `nav2_params.yaml` works for all robots thanks to `/**:` wildcard and relative topic names (except costmap topics which need absolute overrides).
