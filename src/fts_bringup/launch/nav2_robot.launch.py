import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace, Node
from launch_ros.descriptions import ParameterFile
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("fts_bringup")

    ns_arg = DeclareLaunchArgument("namespace", default_value="robot1")
    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="true")
    map_arg = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(pkg_share, "config", "map.yaml"),
        description="Map yaml (shared by all robots)",
    )
    params_arg = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(pkg_share, "config", "nav2_params.yaml"),
        description="Nav2 params template",
    )

    ns = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    # Shared Nav2 parameters file defining sections per node name
    # (amcl, controller_server, planner_server, etc.).
    configured_params = ParameterFile(params_file, allow_substs=True)

    # Frames: use standard names; TF topics are namespaced.
    # Use base_footprint to match the diff-drive controller's base_frame_id.
    base_frame = ParameterValue("base_footprint", value_type=str)
    odom_frame = ParameterValue("odom", value_type=str)

    # Remap TF so each robot uses /<namespace>/tf and /<namespace>/tf_static
    tf_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    group = GroupAction(
        [
            PushRosNamespace(ns),

            # Map server per robot
            Node(
                package="nav2_map_server",
                executable="map_server",
                name="map_server",
                output="screen",
                parameters=[
                    configured_params,
                    {
                        "use_sim_time": use_sim_time,
                        "yaml_filename": map_yaml,
                    }
                ],
            ),

            # AMCL per robot
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "base_frame_id": base_frame,
                        "odom_frame_id": odom_frame,
                        "global_frame_id": "map",
                        "scan_topic": "scan",
                    },
                    configured_params,
                ],
                remappings=tf_remappings,
            ),

            Node(
                package="nav2_controller",
                executable="controller_server",
                name="controller_server",
                output="screen",
                parameters=[
                    configured_params,
                    {"use_sim_time": use_sim_time},
                    {
                        "FollowPath": {
                            "critics": [
                                "RotateToGoal",
                                "Oscillation",
                                "BaseObstacle",
                                "GoalAlign",
                                "PathAlign",
                                "PathDist",
                                "GoalDist",
                            ]
                        }
                    },
                ],
                # In addition to namespacing TF, route Nav2's cmd_vel output into
                # the diff-drive controller's expected input topic so that
                # /<namespace>/bumperbot_controller/cmd_vel_unstamped receives
                # the velocity commands.
                remappings=tf_remappings
                + [("cmd_vel", "bumperbot_controller/cmd_vel_unstamped")],
            ),

            Node(
                package="nav2_planner",
                executable="planner_server",
                name="planner_server",
                output="screen",
                parameters=[configured_params, {"use_sim_time": use_sim_time}],
                remappings=tf_remappings,
            ),

            Node(
                package="nav2_smoother",
                executable="smoother_server",
                name="smoother_server",
                output="screen",
                parameters=[configured_params, {"use_sim_time": use_sim_time}],
                remappings=tf_remappings,
            ),

            Node(
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator",
                output="screen",
                parameters=[
                    configured_params,
                    {
                        "use_sim_time": use_sim_time,
                        "global_frame": "map",
                        "robot_base_frame": base_frame,
                    },
                ],
                remappings=tf_remappings,
            ),

            Node(
                package="nav2_waypoint_follower",
                executable="waypoint_follower",
                name="waypoint_follower",
                output="screen",
                parameters=[configured_params, {"use_sim_time": use_sim_time}],
                remappings=tf_remappings,
            ),

            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_navigation",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "autostart": True,
                        "node_names": [
                            "map_server",
                            "amcl",
                            "controller_server",
                            "planner_server",
                            "smoother_server",
                            "bt_navigator",
                            "waypoint_follower",
                        ],
                    }
                ],
                remappings=tf_remappings,
            ),
        ]
    )

    return LaunchDescription(
        [
            ns_arg,
            use_sim_time_arg,
            map_arg,
            params_arg,
            group,
        ]
    )
