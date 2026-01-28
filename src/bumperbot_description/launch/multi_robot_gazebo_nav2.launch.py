import os
from os import pathsep
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)

from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """
    Multi-robot Gazebo + Nav2 bringup.

    This launches a single Gazebo world and spawns two bumperbot instances:
      - robot1
      - robot2

    For each robot, a separate namespace is used (robot1/, robot2/) and within
    that namespace we start:
      - robot_state_publisher
      - ros2_control controllers (via bumperbot_controller/controller.launch.py)
      - a Nav2 stack (via bumperbot_navigation/navigation.launch.py)

    Notes:
      - Sensor and TF wiring follows the existing single-robot setup; this file
        is intended as a skeleton starting point and may need additional topic
        remaps (e.g. /scan, /tf, /tf_static) for a production multi-robot setup.
    """

    # ---- Launch arguments ----
    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="false",
        description="Use SLAM instead of localization.",
    )
    use_slam = LaunchConfiguration("use_slam")

    world_name_arg = DeclareLaunchArgument(
        name="world_name",
        default_value="empty",
        description="World name from bumperbot_description/worlds (without .world).",
    )
    world_name = LaunchConfiguration("world_name")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(
            get_package_share_directory("bumperbot_description"),
            "urdf",
            "bumperbot.urdf.xacro",
        ),
        description="Absolute path to robot URDF/xacro file.",
    )
    model = LaunchConfiguration("model")

    robot1_spawn_x_arg = DeclareLaunchArgument(
        "robot1_spawn_x",
        default_value="0.0",
        description="Initial X position for robot1.",
    )
    robot1_spawn_y_arg = DeclareLaunchArgument(
        "robot1_spawn_y",
        default_value="0.0",
        description="Initial Y position for robot1.",
    )

    robot2_spawn_x_arg = DeclareLaunchArgument(
        "robot2_spawn_x",
        default_value="1.0",
        description="Initial X position for robot2.",
    )
    robot2_spawn_y_arg = DeclareLaunchArgument(
        "robot2_spawn_y",
        default_value="0.0",
        description="Initial Y position for robot2.",
    )

    robot1_spawn_x = LaunchConfiguration("robot1_spawn_x")
    robot1_spawn_y = LaunchConfiguration("robot1_spawn_y")
    robot2_spawn_x = LaunchConfiguration("robot2_spawn_x")
    robot2_spawn_y = LaunchConfiguration("robot2_spawn_y")

    # ---- Package paths ----
    bumperbot_description = get_package_share_directory("bumperbot_description")
    bumperbot_controller = get_package_share_directory("bumperbot_controller")
    bumperbot_navigation = get_package_share_directory("bumperbot_navigation")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    # ---- World and resources ----
    world_path = PathJoinSubstitution(
        [
            bumperbot_description,
            "worlds",
            PythonExpression(
                ["'", world_name, "'", " + '.world'"],
            ),
        ]
    )

    model_path = str(Path(bumperbot_description).parent.resolve())
    model_path += pathsep + os.path.join(
        get_package_share_directory("bumperbot_description"), "models"
    )

    gazebo_resource_path = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        model_path,
    )

    ros_distro = os.environ.get("ROS_DISTRO", "")
    is_ignition = "True" if ros_distro == "humble" else "False"

    # Robot description shared for both instances (geometry is identical).
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                model,
                " is_ignition:=",
                is_ignition,
            ]
        ),
        value_type=str,
    )

    # Use simulation time for all nodes launched here
    use_sim_time = True

    # Top-level robot_state_publisher to provide the robot_description
    # parameter for the spawners, mirroring the single-robot gazebo.launch.py
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    # ---- Core Gazebo world ----
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("ros_gz_sim"), "launch"
                ),
                "/gz_sim.launch.py",
            ]
        ),
        launch_arguments={
            "gz_args": PythonExpression(["'", world_path, " -v 4 -r'"])
        }.items(),
    )

    # Spawn both robots into the running Gazebo world.
    gz_spawn_robot1 = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "robot1",
            "-x",
            robot1_spawn_x,
            "-y",
            robot1_spawn_y,
            "-z",
            "0.05",
        ],
    )

    gz_spawn_robot2 = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "robot2",
            "-x",
            robot2_spawn_x,
            "-y",
            robot2_spawn_y,
            "-z",
            "0.05",
        ],
    )

    # Bridge clock and core sensors. For a full multi-robot setup you may want
    # to add per-robot scan / IMU topics here.
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ],
        remappings=[
            ("/imu", "/imu/out"),
        ],
    )

    # ---- Per-robot stacks (controllers + Nav2) ----
    navigation_launch_path = os.path.join(
        bumperbot_navigation, "launch", "navigation.launch.py"
    )

    robot1_stack = GroupAction(
        actions=[
            PushRosNamespace("robot1"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(navigation_launch_path),
                launch_arguments={
                    "use_sim_time": "true",
                }.items(),
            ),
        ]
    )

    robot2_stack = GroupAction(
        actions=[
            PushRosNamespace("robot2"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(navigation_launch_path),
                launch_arguments={
                    "use_sim_time": "true",
                }.items(),
            ),
        ]
    )

    # Start each robot's stack only after its entity has been spawned.
    start_robot1_stack = RegisterEventHandler(
        OnProcessExit(
            target_action=gz_spawn_robot1,
            on_exit=[robot1_stack],
        )
    )
    start_robot2_stack = RegisterEventHandler(
        OnProcessExit(
            target_action=gz_spawn_robot2,
            on_exit=[robot2_stack],
        )
    )

    # Optional safety and visualization nodes (single instance).
    safety_stop = Node(
        package="bumperbot_utils",
        executable="safety_stop",
        output="screen",
    )

    rviz_localization = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(
                nav2_bringup_share,
                "rviz",
                "nav2_default_view.rviz",
            ),
        ],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Localization / SLAM are kept close to the single-robot launch: one map
    # server / localization stack, not namespaced. Adjust as needed.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("bumperbot_localization"),
                    "launch",
                    "global_localization_launch.py",
                )
            ]
        ),
        condition=UnlessCondition(use_slam),
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("bumperbot_mapping"),
                    "launch",
                    "slam.launch.py",
                )
            ]
        ),
        condition=IfCondition(use_slam),
    )

    return LaunchDescription(
        [
            use_slam_arg,
            world_name_arg,
            model_arg,
            robot1_spawn_x_arg,
            robot1_spawn_y_arg,
            robot2_spawn_x_arg,
            robot2_spawn_y_arg,
            gazebo_resource_path,
            robot_state_publisher_node,
            gazebo,
            gz_spawn_robot1,
            gz_spawn_robot2,
            gz_ros2_bridge,
            start_robot1_stack,
            start_robot2_stack,
            safety_stop,
            localization,
            slam,
            rviz_localization,
        ]
    )
