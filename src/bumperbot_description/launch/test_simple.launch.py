"""
Spawn a very simple URDF (test_simple.urdf) into Gazebo Sim (Ignition).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_bumper = get_package_share_directory('bumperbot_description')

    default_world = os.path.join(pkg_bumper, 'worlds', 'empty.world')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(pkg_bumper, 'urdf', 'test_simple.urdf'),
        description='Absolute path to the URDF to spawn'
    )

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

    spawn_x_arg = DeclareLaunchArgument(
        name='spawn_x',
        default_value='0.0',
        description='Initial X position'
    )

    spawn_y_arg = DeclareLaunchArgument(
        name='spawn_y',
        default_value='0.0',
        description='Initial Y position'
    )

    spawn_z_arg = DeclareLaunchArgument(
        name='spawn_z',
        default_value='0.2',
        description='Initial Z position'
    )

    entity_arg = DeclareLaunchArgument(
        name='entity',
        default_value='simple_test',
        description='Entity name for the spawned robot'
    )

    include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bumper, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'model': LaunchConfiguration('model'),
            'gui': LaunchConfiguration('gui'),
            'world': LaunchConfiguration('world'),
            'with_controllers': 'false',
            'start_helper_nodes': 'false',
            'spawn_x': LaunchConfiguration('spawn_x'),
            'spawn_y': LaunchConfiguration('spawn_y'),
            'spawn_z': LaunchConfiguration('spawn_z'),
            'entity': LaunchConfiguration('entity')
        }.items()
    )

    return LaunchDescription([
        model_arg,
        gui_arg,
        world_arg,
        spawn_x_arg,
        spawn_y_arg,
        spawn_z_arg,
        entity_arg,
        include
    ])
