import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Bring up two independent Nav2 stacks in separate namespaces.

    This uses the generic navigation.launch.py and starts one stack under
    the `robot1` namespace and another under `robot2`. Each stack runs all
    Nav2 nodes under its own namespace; scan / map remain shared globals
    (/scan, /map) while odom is expected as a per-namespace topic
    (robotX/bumperbot_controller/odom).
    """

    use_sim_time = LaunchConfiguration("use_sim_time")

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation time for both Nav2 stacks.",
    )

    bumperbot_navigation_pkg = get_package_share_directory("bumperbot_navigation")
    navigation_launch_path = os.path.join(
        bumperbot_navigation_pkg, "launch", "navigation.launch.py"
    )

    robot1_group = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(navigation_launch_path),
                launch_arguments={
                    "namespace": "robot1",
                    "use_sim_time": use_sim_time,
                }.items(),
            )
        ]
    )

    robot2_group = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(navigation_launch_path),
                launch_arguments={
                    "namespace": "robot2",
                    "use_sim_time": use_sim_time,
                }.items(),
            )
        ]
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            robot1_group,
            robot2_group,
        ]
    )
