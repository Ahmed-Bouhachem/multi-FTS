from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from webots_ros2_driver.webots_launcher import WebotsLauncher

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
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': '<robot name="bumperbot"><link name="base_link"/></robot>'
        }]
    )
    
    return LaunchDescription([
        world_arg,
        webots,
        robot_state_publisher
    ])