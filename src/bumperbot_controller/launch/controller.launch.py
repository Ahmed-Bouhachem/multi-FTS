"""
Launch controller manager spawners for joint_state_broadcaster and a drive controller.

It assumes robot_state_publisher and hardware (sim or real) are already running.
By default it spawns the YAML-declared "bumperbot_controller"; optionally, it can
spawn the "simple_velocity_controller" instead via a launch arg.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    # ---- Launch args ----
    wheel_radius_arg = DeclareLaunchArgument(
        "wheel_radius",
        default_value="0.033"
    )

    wheel_separation_arg = DeclareLaunchArgument(
        "wheel_separation",
        default_value="0.17"
    )

    use_simple_controller_arg = DeclareLaunchArgument(
        "use_simple_controller",
        default_value="False",
        description="If True, spawn simple_velocity_controller; else spawn bumperbot_controller."
    )

    # ---- Launch configs ----
    wheel_radius = LaunchConfiguration("wheel_radius")
    wheel_separation = LaunchConfiguration("wheel_separation")
    use_simple_controller = LaunchConfiguration("use_simple_controller")

    # ---- Spawner: joint_state_broadcaster ----
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager", "/controller_manager"
        ],
        output="screen"
    )

    # ---- Spawner: choose which drive controller to load in controller_manager ----
    # A) YAML-declared diff drive controller
    diff_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "bumperbot_controller",
            "--controller-manager", "/controller_manager"
        ],
        condition=IfCondition(
            PythonExpression([use_simple_controller, " == 'False'"])
        ),
        output="screen"
    )

    # B) Simple velocity controller (alternative)
    simple_velocity_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "simple_velocity_controller",
            "--controller-manager", "/controller_manager"
        ],
        condition=IfCondition(
            PythonExpression([use_simple_controller, " == 'True'"])
        ),
        output="screen"
    )

    # Note: No separate "simple controller" application node is shipped in this
    # package; the alternative here only switches which controller plugin is
    # spawned within controller_manager.

    # ---- Assemble LD ----
    return LaunchDescription([
        wheel_radius_arg,
        wheel_separation_arg,
        use_simple_controller_arg,

        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,
        simple_velocity_controller_spawner,
    ])
