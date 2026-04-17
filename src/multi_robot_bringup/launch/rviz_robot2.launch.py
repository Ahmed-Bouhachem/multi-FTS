"""
rviz_robot2.launch.py

RViz2 for robot2. TF topics are remapped so RViz subscribes to /robot2/tf
instead of the global /tf.  Fixed frame is "map" (robot2's map frame).
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    pkg   = get_package_share_directory("multi_robot_bringup")
    rviz_config = os.path.join(pkg, "rviz", "nav2_robot2.rviz")

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_robot2",
        namespace="robot2",
        arguments=["-d", rviz_config],
        output="screen",
        parameters=[{"use_sim_time": True}],
        remappings=[
            ("/tf",        "/robot2/tf"),
            ("/tf_static", "/robot2/tf_static"),
        ],
    )

    return LaunchDescription([rviz])
