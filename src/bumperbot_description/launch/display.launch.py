from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    bumperbot_description_dir = get_package_share_directory('bumperbot_description')
    gazebo_ros = get_package_share_directory('gazebo_ros')
    
    # Process xacro file
    xacro_file = os.path.join(bumperbot_description_dir, 'urdf', 'bumperbot.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
    )

    # Use classic gzserver with factory plugin
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bumperbot_description_dir, 'launch', 'classic_gzserver.launch.py')),
        launch_arguments={'extra_gazebo_args': ''}.items()
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzclient.launch.py'))
    )

    # Add delay to ensure Gazebo is fully started
    spawn_entity_delayed = TimerAction(
        period=5.0,  # Wait 5 seconds
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                name='spawn_entity',
                arguments=['-entity', 'bumperbot',
                           '-topic', 'robot_description',
                           '-x', '0', '-y', '0', '-z', '1.0'],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher_node,
        gzserver,
        gzclient,
        spawn_entity_delayed
    ])
