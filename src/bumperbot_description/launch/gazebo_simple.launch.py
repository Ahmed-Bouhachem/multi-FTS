"""
Spawn the simple bumperbot in classic Gazebo without controllers.

Publishes robot_description via robot_state_publisher, starts gzserver/gzclient,
and spawns the robot into the empty.world.
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('bumperbot_description')
    
    # Use the simple URDF
    xacro_file = os.path.join(pkg_dir, 'urdf', 'bumperbot_simple.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # GUI toggle
    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo client (GUI)'
    )

    # Gazebo server with ROS plugins (factory/init)
    gzserver = ExecuteProcess(
        cmd=[
            'gzserver', '--verbose',
            '/usr/share/gazebo-11/worlds/empty.world',
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so'
        ],
        output='screen'
    )

    gzclient = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('gui')),
        cmd=['gzclient'],
        output='screen'
    )

    # Robot state publisher: publishes TF from URDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
    )

    # Spawn robot after a short delay to ensure Gazebo is ready
    spawn_entity = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=['-entity', 'bumperbot_simple', '-topic', 'robot_description', '-z', '1.0'],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        gui_arg,
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity
    ])
