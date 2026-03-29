import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("bumperbot_description")

    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(pkg_share, "worlds", "empty.world"),
        description="World file",
    )

    gui_arg = DeclareLaunchArgument("gui", default_value="true")
    world = LaunchConfiguration("world")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": PythonExpression(["'", world, " -v 4 -r'"])
        }.items(),
    )

    robot1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "robot1.launch.py"))
    )
    robot2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "robot2.launch.py"))
    )

    return LaunchDescription([
        world_arg, gui_arg,
        gazebo,
        robot1,
        robot2,
    ])
