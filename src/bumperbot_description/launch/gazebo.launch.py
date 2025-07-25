from launch import LaunchDescription
from pathlib import Path
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
import os

def generate_launch_description():
    # Path to bumperbot_description package
    bumperbot_description_dir = get_package_share_directory('bumperbot_description')
    
    # Declare model file argument
    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(
            bumperbot_description_dir,
            'urdf',
            'bumperbot.urdf.xacro'),
        description="Absolute path to the bumperbot URDF model file."
    )

    # Run xacro to convert to robot_description
    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str
    )

    # Robot State Publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
    )

    # Set Gazebo resource path so it finds meshes
    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[str(Path(bumperbot_description_dir).parent.resolve())]
    )

    # Launch Gazebo (gz sim) with empty world
    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-v', '4', 'empty.sdf'],
        output='screen'
    )

    # Spawn robot from robot_description topic
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'bumperbot'
        ]
    )

    return LaunchDescription([
        model_arg,
        gazebo_resource_path,
        robot_state_publisher_node,
        gz_sim,
        gz_spawn_entity
    ])
