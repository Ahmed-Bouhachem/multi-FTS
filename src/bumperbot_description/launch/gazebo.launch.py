import os
from os import pathsep
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
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

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="false"
    )

    use_slam = LaunchConfiguration("use_slam")

    bumperbot_description = get_package_share_directory("bumperbot_description")
    bumperbot_controller = get_package_share_directory("bumperbot_controller")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    model_arg = DeclareLaunchArgument(
        name="model", default_value=os.path.join(
                bumperbot_description, "urdf", "bumperbot.urdf.xacro"
            ),
        description="Absolute path to robot urdf file"
    )

    start_helper_nodes_arg = DeclareLaunchArgument(
        name="start_helper_nodes",
        default_value="true",
        description="Start helper nodes (e.g. Web UI cmd_vel relay)",
    )

    start_helper_nodes = LaunchConfiguration("start_helper_nodes")

    world_name_arg = DeclareLaunchArgument(name="world_name", default_value="empty")

    world_path = PathJoinSubstitution([
            bumperbot_description,
            "worlds",
            PythonExpression(expression=["'", LaunchConfiguration("world_name"), "'", " + '.world'"])
        ]
    )

    model_path = str(Path(bumperbot_description).parent.resolve())
    model_path += pathsep + os.path.join(get_package_share_directory("bumperbot_description"), 'models')

    gazebo_resource_path = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        model_path
        )

    ros_distro = os.environ["ROS_DISTRO"]
    is_ignition = "True" if ros_distro == "humble" else "False"

    robot_description = ParameterValue(Command([
            "xacro ",
            LaunchConfiguration("model"),
            " is_ignition:=",
            is_ignition
        ]),
        value_type=str
    )
    # Use simulation time for all nodes launched here
    use_sim_time = True

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description,
                     "use_sim_time": use_sim_time}]
    )

    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
                launch_arguments={
                    "gz_args": PythonExpression(["'", world_path, " -v 4 -r'"])
                }.items()
             )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic", "robot_description",
                   "-name", "bumperbot"],
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"
        ],
        remappings=[
            ('/imu', '/imu/out'),
        ]
    )

    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(bumperbot_controller, "launch", "controller.launch.py")
        ])
    )

    # Bridge Web UI velocity commands (Twist on /cmd_vel_unstamped) to the controller
    # (TwistStamped on /cmd_vel) so that running webui/app.py moves the robot
    # when Gazebo + controllers are running.
    cmd_vel_relay_node = Node(
        package="bumperbot_controller",
        executable="twist_relay",
        name="cmd_vel_relay",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(start_helper_nodes),
    )

    start_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=gz_spawn_entity,
            on_exit=[controller_launch]
        )
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("bumperbot_localization"),
                "launch",
                "global_localization_launch.py",
            )
        ]),
        condition=UnlessCondition(use_slam),
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("bumperbot_mapping"),
                "launch",
                "slam.launch.py",
            )
        ]),
        condition=IfCondition(use_slam),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("bumperbot_navigation"),
                "launch",
                "navigation.launch.py",
            )
        ])
    )

    safety_stop = Node(
        package="bumperbot_utils",
        executable="safety_stop",
        output="screen"
    )

    rviz_localization = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(
            nav2_bringup_share,
            "rviz",
            "nav2_default_view.rviz"
        )],
        output="screen",
        parameters=[{"use_sim_time": True}]
    )

    return LaunchDescription([
        use_slam_arg,
        model_arg,
        start_helper_nodes_arg,
        world_name_arg,
        gazebo_resource_path,
        robot_state_publisher_node,
        gazebo,
        gz_spawn_entity,
        gz_ros2_bridge,
        cmd_vel_relay_node,
        start_controllers,
        safety_stop,
        localization,
        slam,
        navigation,
        rviz_localization
    ])
