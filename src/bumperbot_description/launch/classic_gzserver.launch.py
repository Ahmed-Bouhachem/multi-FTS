"""
Start classic Gazebo server (gzserver) with ROS factory/init plugins.

This is a small helper launch included by other launch files.
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    extra_gazebo_args = DeclareLaunchArgument(
        'extra_gazebo_args',
        default_value='',
        description='Extra arguments for Gazebo'
    )
    
    return LaunchDescription([
        extra_gazebo_args,
        ExecuteProcess(
            cmd=[
                'gzserver',
                '/usr/share/gazebo-11/worlds/empty.world',
                '-s', 'libgazebo_ros_init.so',
                '-s', 'libgazebo_ros_factory.so',
                LaunchConfiguration('extra_gazebo_args')
            ],
            output='screen'
        )
    ])
