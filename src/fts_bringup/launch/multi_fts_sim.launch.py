import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    desc_pkg = get_package_share_directory("bumperbot_description")
    bringup_pkg = get_package_share_directory("fts_bringup")
    # Path used by Ignition / Gazebo to resolve model://bumperbot_description URIs
    model_resource_root = os.path.dirname(desc_pkg)

    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(desc_pkg, "worlds", "empty.world"),
        description="World SDF to load in Gazebo",
    )
    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="true")

    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Ensure Gazebo can find the bumperbot_description meshes when using
    # model://bumperbot_description/meshes/... URIs.
    ign_resource_env = SetEnvironmentVariable(
        "IGN_GAZEBO_RESOURCE_PATH",
        f"{model_resource_root}:{os.environ.get('IGN_GAZEBO_RESOURCE_PATH', '')}"
        if os.environ.get("IGN_GAZEBO_RESOURCE_PATH")
        else model_resource_root,
    )
    gz_resource_env = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        f"{model_resource_root}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}"
        if os.environ.get("GZ_SIM_RESOURCE_PATH")
        else model_resource_root,
    )

    # Gazebo (gz sim launch)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={"gz_args": PythonExpression(["'", world, " -v 4 -r'"])}.items(),
    )

    # Robots list (extend this list to add more robots)
    robots = [
        {"name": "robot1", "ns": "robot1", "x": "0.0", "y": "0.0", "yaw": "0.0"},
        {"name": "robot2", "ns": "robot2", "x": "1.5", "y": "0.0", "yaw": "0.0"},
    ]

    spawn_launch = os.path.join(desc_pkg, "launch", "spawn_robot.launch.py")
    # Per-robot ros2_control controllers are provided by the bumperbot_controller
    # package and are loaded via the Ignition ros2_control plugin. We still need
    # to spawn the controllers for each robot's namespaced controller_manager.
    controller_pkg_share = get_package_share_directory("bumperbot_controller")
    controllers_yaml = os.path.join(
        controller_pkg_share, "config", "bumperbot_controllers.yaml"
    )

    nav2_robot_launch = os.path.join(bringup_pkg, "launch", "nav2_robot.launch.py")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")
    nav2_rviz_launch = os.path.join(nav2_bringup_share, "launch", "rviz_launch.py")
    nav2_rviz_config = os.path.join(nav2_bringup_share, "rviz", "nav2_namespaced_view.rviz")

    # Bridge Gazebo Sim topics (clock, IMU, laser scan) into ROS 2.
    # Each robot publishes /<ns>/imu and /<ns>/scan from its Gazebo sensors,
    # which we bridge to matching ROS topics so Nav2 can consume them.
    bridge_args = [
        "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
    ]
    for r in robots:
        ns = r["ns"]
        bridge_args.extend(
            [
                f"/{ns}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
                f"/{ns}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            ]
        )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=bridge_args,
        output="screen",
    )

    robot_actions = []
    for r in robots:
        robot_actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(spawn_launch),
                launch_arguments={
                    "name": r["name"],
                    "namespace": r["ns"],
                    "x": r["x"],
                    "y": r["y"],
                    "yaw": r["yaw"],
                    "use_sim_time": use_sim_time,
                }.items(),
            )
        )

        # ros2_control: joint_state_broadcaster and diff-drive controller for this robot.
        # The IgnitionROS2ControlPlugin creates a controller_manager node in the
        # robot's namespace (<ns>/controller_manager). We spawn the controllers
        # against that manager so Nav2's /<ns>/cmd_vel can drive the wheels.
        controller_manager_name = f"/{r['ns']}/controller_manager"

        robot_actions.append(
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "joint_state_broadcaster",
                    "--controller-manager",
                    controller_manager_name,
                ],
                output="screen",
            )
        )
        robot_actions.append(
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "bumperbot_controller",
                    "--controller-manager",
                    controller_manager_name,
                ],
                output="screen",
            )
        )
        robot_actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_robot_launch),
                launch_arguments={
                    "namespace": r["ns"],
                    "use_sim_time": use_sim_time,
                    "map": os.path.join(bringup_pkg, "config", "map.yaml"),
                    "params_file": os.path.join(
                        bringup_pkg, "config", "nav2_params.yaml"
                    ),
                }.items(),
            )
        )

        # Launch a namespaced RViz instance for this robot using Nav2's
        # standard nav2_namespaced_view.rviz configuration. This RViz subscribes
        # to the namespaced TF (/robotX/tf) and topics.
        robot_actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_rviz_launch),
                launch_arguments={
                    "namespace": r["ns"],
                    "use_namespace": "True",
                    "rviz_config": nav2_rviz_config,
                }.items(),
            )
        )

    return LaunchDescription(
        [
            # World + sim-time configuration
            world_arg,
            use_sim_time_arg,
            ign_resource_env,
            gz_resource_env,

            # Gazebo and bridges
            gazebo,
            gz_bridge,

            # Per-robot spawn + controllers + Nav2 + RViz
            *robot_actions,
        ]
    )
