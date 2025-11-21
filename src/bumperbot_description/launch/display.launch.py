"""
Display the bumperbot model only (no controllers) using Gazebo Sim (Ignition).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    bumperbot_description_dir = get_package_share_directory('bumperbot_description')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(bumperbot_description_dir, 'urdf', 'bumperbot.urdf.xacro'),
        description="Absolute path to the bumperbot URDF model file."
    )

    default_world = os.path.join(bumperbot_description_dir, 'worlds', 'empty.world')
    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo (Ignition) client GUI'
    )

    world_arg = DeclareLaunchArgument(
        name='world',
        default_value=default_world,
        description='Gazebo Sim world resource to load'
    )

    include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bumperbot_description_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'model': LaunchConfiguration('model'),
            'gui': LaunchConfiguration('gui'),
            'world': LaunchConfiguration('world'),
            'with_controllers': 'false',
            'start_helper_nodes': 'false'
        }.items()
    )

    return LaunchDescription([
        model_arg,
        gui_arg,
        world_arg,
        include
    ])
