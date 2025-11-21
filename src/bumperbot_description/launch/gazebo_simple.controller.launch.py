"""
Thin wrapper to forward to gazebo_simple_control.launch.py with a GUI toggle.
"""

from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_dir = get_package_share_directory('bumperbot_description')

    default_world = os.path.join(pkg_dir, 'worlds', 'empty.world')

    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo client (GUI)'
    )

    world_arg = DeclareLaunchArgument(
        name='world',
        default_value=default_world,
        description='Gazebo Sim world resource to load'
    )

    # Delegate to the maintained control launch file
    include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'gazebo_simple_control.launch.py')
        ),
        launch_arguments={
            'gui': LaunchConfiguration('gui'),
            'world': LaunchConfiguration('world')
        }.items()
    )

    return LaunchDescription([
        gui_arg,
        world_arg,
        include
    ])
