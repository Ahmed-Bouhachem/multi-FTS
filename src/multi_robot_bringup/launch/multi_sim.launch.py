"""
multi_sim.launch.py

Main entry point for the two-robot simulation.

Startup sequence:
  t=0    Gazebo (small_house world) + IGN bridge + both RSPs + both spawns
  t+8s   robot_bringup for robot1 (controllers → localization → Nav2)
  t+8s   robot_bringup for robot2 (controllers → localization → Nav2)
  t+25s  RViz for robot1

Launch:
  ros2 launch multi_robot_bringup multi_sim.launch.py
"""

import importlib.util
import os
from pathlib import Path
from os import pathsep

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():

    pkg             = get_package_share_directory("multi_robot_bringup")
    bumperbot_desc  = get_package_share_directory("bumperbot_description")

    # ── Gazebo resource path ──────────────────────────────────────────────────
    model_path = str(Path(bumperbot_desc).parent.resolve())
    model_path += pathsep + os.path.join(bumperbot_desc, "models")

    gz_resource_path = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", model_path)
    ign_resource_path = SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", model_path)

    # ── World ─────────────────────────────────────────────────────────────────
    world_name_arg = DeclareLaunchArgument("world_name", default_value="small_house")
    world_path = PathJoinSubstitution([
        bumperbot_desc, "worlds",
        PythonExpression(["'", LaunchConfiguration("world_name"), "' + '.world'"])
    ])

    # ── Gazebo ────────────────────────────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch"),
            "/gz_sim.launch.py"
        ]),
        launch_arguments={
            "gz_args": PythonExpression(["'", world_path, " -v 4 -r'"])
        }.items(),
    )

    # ── IGN bridge (clock + per-robot IMU and scan) ───────────────────────────
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/robot1/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/robot1/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/robot2/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/robot2/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ],
        remappings=[
            ("/robot1/imu", "/robot1/imu/out"),
            ("/robot2/imu", "/robot2/imu/out"),
        ],
    )

    # ── Spawn robot1 (x=0, y=0) ──────────────────────────────────────────────
    spawn_robot1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(bumperbot_desc, "launch", "spawn_robot.launch.py")
        ]),
        launch_arguments={
            "namespace": "robot1",
            "name":      "robot1",
            "x":         "0.0",
            "y":         "0.0",
            "z":         "0.0",
            "yaw":       "0.0",
            "model":     os.path.join(pkg, "urdf", "robot1.urdf.xacro"),
        }.items(),
    )

    # ── Spawn robot2 (x=1.5, y=0) ────────────────────────────────────────────
    spawn_robot2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(bumperbot_desc, "launch", "spawn_robot.launch.py")
        ]),
        launch_arguments={
            "namespace": "robot2",
            "name":      "robot2",
            "x":         "1.5",
            "y":         "0.0",
            "z":         "0.0",
            "yaw":       "0.0",
            "model":     os.path.join(pkg, "urdf", "robot2.urdf.xacro"),
        }.items(),
    )

    # ── Per-robot bringup (controllers + Nav2), staggered after spawn ─────────
    # Load robot_bringup_actions() from the co-installed launch file and call it
    # directly with concrete Python strings — no LaunchConfiguration leaks.
    _spec = importlib.util.spec_from_file_location(
        "robot_bringup", os.path.join(pkg, "launch", "robot_bringup.launch.py"))
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    bringup_robot1_actions = _mod.robot_bringup_actions("robot1", 0.0, 0.0)
    bringup_robot2_actions = _mod.robot_bringup_actions("robot2", 1.5, 0.0)

    # ── RViz for robot1 ───────────────────────────────────────────────────────
    rviz_robot1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg, "launch", "rviz_robot1.launch.py")
        ]),
    )

    return LaunchDescription([
        world_name_arg,
        gz_resource_path,
        ign_resource_path,

        # Gazebo + bridge + both robot spawns start immediately
        gazebo,
        gz_bridge,
        spawn_robot1,
        spawn_robot2,

        # Bringup robot1 first, then robot2 staggered to avoid lifecycle timeouts
        TimerAction(period=8.0, actions=bringup_robot1_actions),
        TimerAction(period=14.0, actions=bringup_robot2_actions),

        # RViz after both Nav2 stacks are fully warmed up (~45s total)
        TimerAction(period=45.0, actions=[rviz_robot1]),
    ])
