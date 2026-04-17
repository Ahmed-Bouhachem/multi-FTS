"""
rviz_robot1.launch.py

RViz2 for robot1. TF topics are remapped so RViz subscribes to /robot1/tf
instead of the global /tf.  Fixed frame is "map" (robot1's map frame).
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    pkg   = get_package_share_directory("multi_robot_bringup")
    rviz_config = os.path.join(pkg, "rviz", "nav2_robot1.rviz")

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_robot1",
        namespace="robot1",
        arguments=["-d", rviz_config],
        output="screen",
        parameters=[{"use_sim_time": True}],
        remappings=[
            ("/tf",        "/robot1/tf"),
            ("/tf_static", "/robot1/tf_static"),
        ],
    )

    return LaunchDescription([rviz])
