import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("bumperbot_description")
    spawn = os.path.join(pkg_share, "launch", "spawn_robot.launch.py")

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(spawn),
            launch_arguments={
                "name": "robot2",
                "namespace": "robot2",
                "x": "1.5",
                "y": "0.0",
                "yaw": "0.0",
                "use_sim_time": "true",
            }.items(),
        )
    ])
