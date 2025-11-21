import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction,
                            IncludeLaunchDescription, SetEnvironmentVariable,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_bumperbot = get_package_share_directory("bumperbot_description")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(pkg_bumperbot, "urdf", "bumperbot.urdf.xacro"),
        description="Absolute path to the robot Xacro/URDF file."
    )

    world_arg = DeclareLaunchArgument(
        name="world",
        default_value=os.path.join(pkg_bumperbot, "worlds", "empty.world"),
        description="Absolute path to the world SDF file to load."
    )

    with_controllers_arg = DeclareLaunchArgument(
        name="with_controllers",
        default_value="true",
        description="Start ros2_control controllers once the robot is spawned."
    )

    helper_nodes_arg = DeclareLaunchArgument(
        name="start_helper_nodes",
        default_value="false",
        description="Start example helper nodes (simple/noisy controller + localization)."
    )

    # Expose the package resources (models/photos/worlds/meshes) to Ignition.
    pkg_root = Path(pkg_bumperbot).parent.resolve()
    resource_entries = [
        os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
        os.environ.get("IGN_GAZEBO_RESOURCE_PATH", ""),
        str(pkg_root),
        os.path.join(pkg_bumperbot, "models"),
        os.path.join(pkg_bumperbot, "photos"),
        os.path.join(pkg_bumperbot, "worlds"),
        pkg_bumperbot,
    ]
    resource_path = os.pathsep.join(entry for entry in resource_entries if entry)

    file_entries = [
        os.environ.get("IGN_FILE_PATH", ""),
        os.path.join(pkg_bumperbot, "meshes"),
        pkg_bumperbot,
    ]
    ign_file_path = os.pathsep.join(entry for entry in file_entries if entry)

    env_actions = [
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_path),
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", resource_path),
        SetEnvironmentVariable("IGN_FILE_PATH", ign_file_path),
    ]

    ros_distro = os.environ.get("ROS_DISTRO", "").lower()
    is_ignition = "true" if ros_distro in ("humble", "rolling", "iron") else "false"

    robot_description = ParameterValue(
        Command([
            "xacro ",
            LaunchConfiguration("model"),
            " is_ignition:=",
            is_ignition
        ]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": True
        }]
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-v 4 -r ", LaunchConfiguration("world")],
            "ign_args": ["-v 4 -r ", LaunchConfiguration("world")]
        }.items()
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-entity", "bumperbot"
        ],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ]
    )

    controllers_group = GroupAction(
        condition=IfCondition(LaunchConfiguration("with_controllers")),
        actions=[
            TimerAction(
                period=5.0,
                actions=[
                    Node(
                        package="controller_manager",
                        executable="spawner",
                        arguments=[
                            "joint_state_broadcaster",
                            "--controller-manager-timeout", "60.0"
                        ],
                        output="screen"
                    )
                ]
            ),
            TimerAction(
                period=7.0,
                actions=[
                    Node(
                        package="controller_manager",
                        executable="spawner",
                        arguments=[
                            "bumperbot_controller",
                            "--controller-manager-timeout", "60.0"
                        ],
                        output="screen"
                    )
                ]
            )
        ]
    )

    helper_group = TimerAction(
        period=9.0,
        actions=[
            GroupAction(
                condition=IfCondition(LaunchConfiguration("start_helper_nodes")),
                actions=[
                    Node(
                        package="bumperbot_controller",
                        executable="noisy_controller",
                        name="noisy_controller",
                        output="screen",
                        parameters=[{"use_sim_time": True}]
                    ),
                    Node(
                        package="bumperbot_controller",
                        executable="simple_controller",
                        name="simple_controller",
                        output="screen",
                        parameters=[{"use_sim_time": True}]
                    ),
                    Node(
                        package="bumperbot_localization",
                        executable="kalman_filter",
                        name="kalman_filter",
                        output="screen",
                        parameters=[{"use_sim_time": True}]
                    ),
                ]
            )
        ]
    )

    return LaunchDescription(
        env_actions + [
            model_arg,
            world_arg,
            with_controllers_arg,
            helper_nodes_arg,
            robot_state_publisher_node,
            gz_sim,
            spawn_entity,
            controllers_group,
            helper_group,
            clock_bridge,
        ]
    )
