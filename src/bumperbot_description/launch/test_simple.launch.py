from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_bumper = get_package_share_directory('bumperbot_description')
    gazebo_ros = get_package_share_directory('gazebo_ros')

    urdf_file = os.path.join(pkg_bumper, 'urdf', 'test_simple.urdf')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bumper, 'launch', 'classic_gzserver.launch.py')),
        launch_arguments={
            'extra_gazebo_args': ''
        }.items()
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzclient.launch.py'))
    )

    spawn_entity_delayed = TimerAction(
        period=3.0,  # Wait 3 seconds
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                name='spawn_entity',
                arguments=[
                    '-entity', 'simple_test',
                    '-file', urdf_file,
                    '-x', '0.0', '-y', '0.0', '-z', '10.0'
                ],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        gzserver,
        gzclient,
        spawn_entity_delayed
    ])
