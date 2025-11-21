"""
Compatibility wrapper around gazebo.launch.py that loads the simple bumperbot model
with controllers enabled.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_dir = get_package_share_directory('bumperbot_description')

    default_world = os.path.join(pkg_dir, 'worlds', 'empty.world')

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

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(pkg_dir, 'urdf', 'bumperbot_simple.urdf.xacro'),
        description='Absolute path to the bumperbot simple URDF/xacro file'
    )

    with_ctrl_arg = DeclareLaunchArgument(
        name='with_controllers',
        default_value='true',
        description='Spawn ros2_control controllers'
    )

    helper_arg = DeclareLaunchArgument(
        name='start_helper_nodes',
        default_value='true',
        description='Start example helper nodes'
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
        default_value='0.05',
        description='Initial Z position'
    )

    entity_arg = DeclareLaunchArgument(
        name='entity',
        default_value='bumperbot_simple',
        description='Entity name for the spawned robot'
    )

    include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'gui': LaunchConfiguration('gui'),
            'world': LaunchConfiguration('world'),
            'model': LaunchConfiguration('model'),
            'with_controllers': LaunchConfiguration('with_controllers'),
            'start_helper_nodes': LaunchConfiguration('start_helper_nodes'),
            'spawn_x': LaunchConfiguration('spawn_x'),
            'spawn_y': LaunchConfiguration('spawn_y'),
            'spawn_z': LaunchConfiguration('spawn_z'),
            'entity': LaunchConfiguration('entity')
        }.items()
    )

    return LaunchDescription([
        gui_arg,
        world_arg,
        model_arg,
        with_ctrl_arg,
        helper_arg,
        spawn_x_arg,
        spawn_y_arg,
        spawn_z_arg,
        entity_arg,
        include
    ])
