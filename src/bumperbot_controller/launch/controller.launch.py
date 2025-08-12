from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():

    use_python_arg = DeclareLaunchArgument (
        "use_python",
        default_value="False"
    )

    wheel_radius_arg = DeclareLaunchArgument (
        "wheel_radius",
        default_value="0.033"
    )

    wheel_seperation_arg = DeclareLaunchArgument (
        "wheel_seperation",
        default_value="0.17"
    )

    use_python = LaunchConfiguration("use_python")
    wheel_radius = LaunchConfiguration("wheel_radius")
    wheel_seperation = LaunchConfiguration("wheel_seperation")



    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager',
                   '/controller_manager']
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller',
                   '--controller-manager',
                   '/controller_manager']
    )

    # Note: simple controller nodes are not included because this package
    # currently ships only a library; add an executable before enabling below.

    return LaunchDescription([
        use_python_arg,
        wheel_radius_arg,
        wheel_seperation_arg,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,
    ])
