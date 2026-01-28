import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time")
    namespace = LaunchConfiguration("namespace")
    lifecycle_nodes = ["controller_server", "planner_server", "smoother_server", "bt_navigator", "behavior_server"]
    bumperbot_navigation_pkg = get_package_share_directory("bumperbot_navigation")

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true"
    )

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="Namespace to run this Nav2 stack under (e.g. 'robot1').",
    )

    nav2_controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        namespace=namespace,
        output="screen",
        remappings=[
            # Send Nav2 velocity commands directly to the diff-drive controller
            # Use a relative topic so it is properly namespaced for multi-robot.
            ("cmd_vel", "bumperbot_controller/cmd_vel_unstamped"),
        ],
        parameters=[
            os.path.join(
                bumperbot_navigation_pkg,
                "config",
                "controller_server.yaml"),
            {"use_sim_time": use_sim_time}
        ],
    )
    
    nav2_planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        namespace=namespace,
        output="screen",
        parameters=[
            os.path.join(
                bumperbot_navigation_pkg,
                "config",
                "planner_server.yaml"),
            {"use_sim_time": use_sim_time}
        ],
    )

    nav2_behaviors = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        namespace=namespace,
        output="screen",
        remappings=[
            ("cmd_vel", "bumperbot_controller/cmd_vel_unstamped"),
        ],
        parameters=[
            os.path.join(
                bumperbot_navigation_pkg,
                "config",
                "behavior_server.yaml"),
            {"use_sim_time": use_sim_time}
        ],
    )
    
    nav2_bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        namespace=namespace,
        output="screen",
        parameters=[
            os.path.join(
                bumperbot_navigation_pkg,
                "config",
                "bt_navigator.yaml"),
            {"use_sim_time": use_sim_time}
        ],
    )

    nav2_smoother_server = Node(
        package="nav2_smoother",
        executable="smoother_server",
        name="smoother_server",
        namespace=namespace,
        output="screen",
        parameters=[
            os.path.join(
                bumperbot_navigation_pkg,
                "config",
                "smoother_server.yaml"),
            {"use_sim_time": use_sim_time}
        ],
    )

    nav2_lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        namespace=namespace,
        output="screen",
        parameters=[
            {"node_names": lifecycle_nodes},
            {"use_sim_time": use_sim_time},
            {"autostart": True}
        ],
    )

    return LaunchDescription([
        use_sim_time_arg,
        namespace_arg,
        nav2_controller_server,
        nav2_planner_server,
        nav2_smoother_server,
        nav2_behaviors,
        nav2_bt_navigator,
        nav2_lifecycle_manager,
    ])
