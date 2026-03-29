import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    nav2_bringup_share = get_package_share_directory("nav2_bringup")
    fts_bringup_share = get_package_share_directory("fts_bringup")

    bringup_launch = os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
    default_map = os.path.join(fts_bringup_share, "config", "map.yaml")
    # Use Nav2's standard single-robot params. This includes map_server
    # configuration and avoids extra plugins that may not be installed.
    default_params = os.path.join(nav2_bringup_share, "params", "nav2_params.yaml")
    rviz_config = os.path.join(fts_bringup_share, "config", "rviz_multi_robot.rviz")

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="robot1",
        description="Robot namespace (Nav2 will run under this).",
    )
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use /clock if available.",
    )
    map_arg = DeclareLaunchArgument(
        "map",
        default_value=default_map,
        description="Map YAML file for Nav2.",
    )
    params_arg = DeclareLaunchArgument(
        "params_file",
        default_value=default_params,
        description="Nav2 parameters file (multirobot-friendly).",
    )

    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    # Static TF publishers so Nav2 has a minimal TF tree even without Gazebo
    # map -> odom
    static_map_to_odom = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        namespace=namespace,
        name="static_map_to_odom",
        output="screen",
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
        arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
    )

    # odom -> base_link
    static_odom_to_base = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        namespace=namespace,
        name="static_odom_to_base_link",
        output="screen",
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
        arguments=["0", "0", "0", "0", "0", "0", "odom", "base_link"],
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(bringup_launch),
        launch_arguments={
            "namespace": namespace,
            "use_namespace": "true",
            "slam": "False",
            "map": map_yaml,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
            "use_composition": "False",
            "use_respawn": "False",
            "log_level": "info",
        }.items(),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            namespace_arg,
            use_sim_time_arg,
            map_arg,
            params_arg,
            static_map_to_odom,
            static_odom_to_base,
            nav2,
            rviz,
        ]
    )
