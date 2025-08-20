"""
Spawn the simple bumperbot with ros2_control in classic Gazebo and start controllers.

This launch:
- Processes a minimal URDF with ros2_control and publishes robot_description
- Starts gzserver (headless) and optionally gzclient
- Spawns the robot into Gazebo
- Spawns joint_state_broadcaster and diff_drive_controller
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
    controller_dir = get_package_share_directory('bumperbot_controller')
    
    # Use the simple URDF with ros2_control
    xacro_file = os.path.join(pkg_dir, 'urdf', 'bumperbot_simple.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # Controller configuration
    controller_config = os.path.join(controller_dir, 'config', 'bumperbot_controllers.yaml')

    # GUI toggle
    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo client (GUI)'
    )

    # Gazebo server with ROS plugins (factory for spawn, init for ROS clock)
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

    # Robot state publisher (publishes TF using robot_description)
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

    # Start controllers after spawning
    start_controllers = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['joint_state_broadcaster'],
                output='screen'
            ),
            Node(
                package='controller_manager',
                executable='spawner',
                # Match the controller name defined in bumperbot_controllers.yaml
                arguments=['bumperbot_controller'],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        gui_arg,
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity,
        start_controllers
    ])
