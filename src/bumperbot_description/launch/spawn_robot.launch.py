import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, TextSubstitution
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("bumperbot_description")

    model_arg = DeclareLaunchArgument(
        "model",
        default_value=os.path.join(pkg_share, "urdf", "bumperbot.urdf.xacro"),
        description="Absolute path to robot URDF XACRO",
    )

    name_arg = DeclareLaunchArgument("name", default_value="robot1")
    ns_arg = DeclareLaunchArgument("namespace", default_value="robot1")

    x_arg = DeclareLaunchArgument("x", default_value="0.0")
    y_arg = DeclareLaunchArgument("y", default_value="0.0")
    z_arg = DeclareLaunchArgument("z", default_value="0.0")
    yaw_arg = DeclareLaunchArgument("yaw", default_value="0.0")

    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="true")

    model = LaunchConfiguration("model")
    name = LaunchConfiguration("name")
    ns = LaunchConfiguration("namespace")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    yaw = LaunchConfiguration("yaw")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Generate a namespaced robot_description with ros2_control enabled.
    robot_description = Command(
        [
            "xacro ",
            model,
            " with_ros2_control:=true",
            " is_sim:=true",
            " is_ignition:=true",
            " ros_namespace:=",
            ns,
        ]
    )

    # Namespaced robot_state_publisher. We rely on namespaced TF topics
    # (tf / tf_static) instead of frame_prefix so that multiple robots
    # can share frame IDs like "base_link" without conflicting.
    tf_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=ns,
        parameters=[
            {"robot_description": robot_description},
            {"use_sim_time": use_sim_time},
        ],
        remappings=tf_remappings,
        output="screen",
    )

    # Spawn robot from the namespaced robot_description topic
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            [TextSubstitution(text="/"), ns, TextSubstitution(text="/robot_description")],
            "-name",
            name,
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-Y",
            yaw,
        ],
    )

    return LaunchDescription(
        [
            model_arg,
            name_arg,
            ns_arg,
            x_arg,
            y_arg,
            z_arg,
            yaw_arg,
            use_sim_time_arg,
            rsp,
            spawn,
        ]
    )
