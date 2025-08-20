"""
Start joystick driver and joy_teleop using package-provided configs.

Reads joy and joy_teleop YAMLs from bumperbot_controller/config.
"""

from launch import LaunchDescription
from launch_ros.actions import Node 
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description() :

    # Joystick device driver
    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joystick",
        parameters=[os.path.join(get_package_share_directory("bumperbot_controller"), "config", "joy_config.yaml")]
    )

    # Teleoperation mapping from joystick to ROS topics
    joy_teleop = Node(
        package="joy_teleop",
        executable="joy_teleop",
        parameters=[os.path.join(get_package_share_directory("bumperbot_controller"), "config", "joy_teleop.yaml")]
    )

    return LaunchDescription([
        joy_node,
        joy_teleop
    ])
