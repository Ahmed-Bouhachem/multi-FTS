"""
Display the full bumperbot model in Gazebo (classic) using robot_state_publisher.

This launch processes the main xacro into robot_description, starts gzserver/gzclient
via gazebo_ros helper launches, spawns the robot, and supports a GUI toggle.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    bumperbot_description_dir = get_package_share_directory('bumperbot_description')
    gazebo_ros = get_package_share_directory('gazebo_ros')
    
    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(bumperbot_description_dir, 'urdf', 'bumperbot.urdf.xacro'),
        description="Absolute path to the bumperbot URDF model file."
    )

    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo client (GUI)' 
    )

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str
    )

    # Publish robot_description and TF
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
    )

    # Use the same gzserver setup as display.launch.py
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzserver.launch.py')),
        launch_arguments={'extra_gazebo_args': ''}.items()
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzclient.launch.py')),
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    # Spawn the model into Gazebo (slight z offset to avoid ground penetration)
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        arguments=['-entity', 'bumperbot',
                   '-topic', 'robot_description',
                   '-x', '0', '-y', '0', '-z', '1.0'],  # Spawn 1 meter high
        output='screen'
    )

    return LaunchDescription([
        model_arg,
        gui_arg,
        robot_state_publisher_node,
        gzserver,
        gzclient,
        spawn_entity
    ])
