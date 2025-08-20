"""
Launch a Webots simulation of the bumperbot world, publishing robot_description.

This uses webots_ros2_driver's WebotsLauncher to open a .wbt world and runs
robot_state_publisher with the real bumperbot xacro. This does not yet drive
Webots kinematics via ros2_control — it's a visualization/TF setup to get you
started with Webots. Extend with webots_ros2_driver robot controllers as needed.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from webots_ros2_driver.webots_launcher import WebotsLauncher
import os

def generate_launch_description():
    package_dir = FindPackageShare('bumperbot_description')
    
    # Webots world file (we'll create this)
    world = LaunchConfiguration('world')
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([package_dir, 'worlds', 'bumperbot.wbt']),
        description='Choose the world file'
    )
    
    webots = WebotsLauncher(
        world=world
    )
    
    # Publish the same robot_description used in Gazebo/RViz (xacro → URDF)
    xacro_file = os.path.join(FindPackageShare('bumperbot_description').perform(None), 'urdf', 'bumperbot.urdf.xacro')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )
    
    return LaunchDescription([
        world_arg,
        webots,
        robot_state_publisher
    ])
