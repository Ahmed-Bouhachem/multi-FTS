"""
robot_bringup.launch.py

Per-robot full bringup: controller spawners + map_server + AMCL + Nav2 stack.
All nodes run under the robot's namespace so topic names resolve correctly.

Exposes a Python helper `robot_bringup_actions(namespace, initial_x, initial_y)`
that returns a list of launch actions. Prefer calling that directly from
parent launch files — it sidesteps the LaunchConfiguration scope issues that
appear when a single launch file includes this one multiple times.

Standalone usage is also supported:
  ros2 launch multi_robot_bringup robot_bringup.launch.py namespace:=robot1 initial_x:=0.0 initial_y:=0.0
"""

import os
import tempfile
import yaml
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace


def _write_costmap_overrides(namespace: str) -> str:
    """Write a temp YAML that fixes costmap topic resolution for a namespace.

    Costmap sub-nodes resolve relative topics under their own namespace
    (e.g. /robot1/global_costmap/map instead of /robot1/map).  This
    override file provides the correct absolute paths.
    """
    overrides = {
        "/**": {
            "local_costmap": {
                "local_costmap": {
                    "ros__parameters": {
                        "obstacle_layer": {
                            "scan": {
                                "topic": f"/{namespace}/scan",
                            }
                        }
                    }
                }
            },
            "global_costmap": {
                "global_costmap": {
                    "ros__parameters": {
                        "static_layer": {
                            "map_topic": f"/{namespace}/map",
                        },
                        "obstacle_layer": {
                            "scan": {
                                "topic": f"/{namespace}/scan",
                            }
                        }
                    }
                }
            },
        }
    }
    f = tempfile.NamedTemporaryFile(
        mode="w", prefix=f"nav2_{namespace}_", suffix=".yaml", delete=False)
    yaml.dump(overrides, f, default_flow_style=False)
    f.flush()
    return f.name


def robot_bringup_actions(namespace: str, initial_x: float, initial_y: float):
    """Return the list of launch actions that bring up one robot."""

    pkg = get_package_share_directory("multi_robot_bringup")
    nav2_params = os.path.join(pkg, "config", "nav2_params.yaml")
    costmap_overrides = _write_costmap_overrides(namespace)

    map_yaml = os.path.join(
        get_package_share_directory("bumperbot_mapping"),
        "maps", "small_house", "map.yaml",
    )

    nav2_pkg = get_package_share_directory("bumperbot_navigation")
    bt_nav_to_pose = os.path.join(
        nav2_pkg, "behavior_tree", "simple_navigation_w_replanning_and_recovery.xml"
    )
    bt_nav_through_poses = os.path.join(
        nav2_pkg, "behavior_tree", "simple_navigation.xml"
    )

    tf_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]
    cm_path = f"/{namespace}/controller_manager"

    # ── Controller spawners ───────────────────────────────────────────────────
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", cm_path],
        output="screen",
    )

    bumperbot_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["bumperbot_controller", "--controller-manager", cm_path],
        output="screen",
    )

    # ── Localization (map_server + AMCL) ──────────────────────────────────────
    localization_nodes = GroupAction([
        PushRosNamespace(namespace),

        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            output="screen",
            parameters=[
                {"yaml_filename": map_yaml},
                {"use_sim_time": True},
            ],
            remappings=tf_remappings,
        ),

        Node(
            package="nav2_amcl",
            executable="amcl",
            name="amcl",
            output="screen",
            emulate_tty=True,
            parameters=[
                nav2_params,
                {"use_sim_time": True},
                {"initial_pose.x": float(initial_x)},
                {"initial_pose.y": float(initial_y)},
            ],
            remappings=tf_remappings,
        ),

        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_localization",
            output="screen",
            parameters=[
                {"node_names": ["map_server", "amcl"]},
                {"use_sim_time": True},
                {"autostart": True},
                {"bond_timeout": 0.0},
            ],
        ),
    ])

    # ── Nav2 stack ────────────────────────────────────────────────────────────
    navigation_nodes = GroupAction([
        PushRosNamespace(namespace),

        Node(
            package="nav2_controller",
            executable="controller_server",
            name="controller_server",
            output="screen",
            remappings=tf_remappings + [("cmd_vel", "bumperbot_controller/cmd_vel_unstamped")],
            parameters=[nav2_params, costmap_overrides, {"use_sim_time": True}],
        ),

        Node(
            package="nav2_planner",
            executable="planner_server",
            name="planner_server",
            output="screen",
            remappings=tf_remappings,
            parameters=[nav2_params, costmap_overrides, {"use_sim_time": True}],
        ),

        Node(
            package="nav2_smoother",
            executable="smoother_server",
            name="smoother_server",
            output="screen",
            remappings=tf_remappings,
            parameters=[nav2_params, {"use_sim_time": True}],
        ),

        Node(
            package="nav2_behaviors",
            executable="behavior_server",
            name="behavior_server",
            output="screen",
            remappings=tf_remappings + [("cmd_vel", "bumperbot_controller/cmd_vel_unstamped")],
            parameters=[nav2_params, {"use_sim_time": True}],
        ),

        Node(
            package="nav2_bt_navigator",
            executable="bt_navigator",
            name="bt_navigator",
            output="screen",
            remappings=tf_remappings,
            parameters=[
                nav2_params,
                {"use_sim_time": True},
                {"default_nav_to_pose_bt_xml": bt_nav_to_pose},
                {"default_nav_through_poses_bt_xml": bt_nav_through_poses},
            ],
        ),

        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_navigation",
            output="screen",
            parameters=[
                {"node_names": [
                    "controller_server",
                    "planner_server",
                    "smoother_server",
                    "bt_navigator",
                    "behavior_server",
                ]},
                {"use_sim_time": True},
                {"autostart": True},
                {"bond_timeout": 0.0},
            ],
        ),
    ])

    return [
        # Controllers start immediately (controller_manager is already up).
        joint_state_broadcaster,
        bumperbot_controller,

        # Localization at +3s (give controllers time to activate).
        TimerAction(period=3.0, actions=[localization_nodes]),

        # Nav2 at +9s (give map_server time to activate and publish /map).
        TimerAction(period=9.0, actions=[navigation_nodes]),
    ]


def generate_launch_description():
    """Stand-alone launch entry point (uses default args robot1 @ origin)."""

    ns_arg = DeclareLaunchArgument("namespace", default_value="robot1")
    x_arg  = DeclareLaunchArgument("initial_x", default_value="0.0")
    y_arg  = DeclareLaunchArgument("initial_y", default_value="0.0")

    # When run stand-alone, resolve LaunchConfigurations eagerly via
    # OpaqueFunction so robot_bringup_actions sees concrete strings.
    from launch.actions import OpaqueFunction

    def _launch(context):
        ns = LaunchConfiguration("namespace").perform(context)
        ix = LaunchConfiguration("initial_x").perform(context)
        iy = LaunchConfiguration("initial_y").perform(context)
        return robot_bringup_actions(ns, ix, iy)

    return LaunchDescription([ns_arg, x_arg, y_arg, OpaqueFunction(function=_launch)])
