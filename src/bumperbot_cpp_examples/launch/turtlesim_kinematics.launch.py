"""
Launch turtlesim and the kinematics example node together.

This script:
  - Starts turtlesim_node
  - Spawns a second turtle (configurable position/name)
  - Starts the simple_turtlesim_kinematics node which prints the XY translation
    from turtle1 to the spawned turtle
"""

from launch import LaunchDescription
from launch.actions import TimerAction, DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description() -> LaunchDescription:
    # Launch arguments for turtle2 spawn
    arg_x = DeclareLaunchArgument('x', default_value='5.0', description='turtle2 x')
    arg_y = DeclareLaunchArgument('y', default_value='5.0', description='turtle2 y')
    arg_theta = DeclareLaunchArgument('theta', default_value='0.0', description='turtle2 heading (rad)')
    arg_name = DeclareLaunchArgument('name', default_value='turtle2', description='turtle2 name')
    # Base turtlesim window with the first turtle (turtle1)
    turtlesim = Node(
        package="turtlesim",
        executable="turtlesim_node",
        name="turtlesim"
    )

    # Spawn turtle2 after turtlesim starts
    # Delay spawn slightly to ensure the /spawn service is available
    spawn_turtle2 = TimerAction(
        period=1.0,
        actions=[
            Node(
                package="bumperbot_cpp_examples",
                executable="spawn_turtle.py",
                name="spawn_turtle2_client",
                arguments=[
                    '--x', LaunchConfiguration('x'),
                    '--y', LaunchConfiguration('y'),
                    '--theta', LaunchConfiguration('theta'),
                    '--name', LaunchConfiguration('name'),
                ],
                output="screen",
            )
        ],
    )

    # Node computing and logging the translation between turtle1 and turtle2
    kinematics = Node(
        package="bumperbot_cpp_examples",
        executable="simple_turtlesim_kinematics",
        name="simple_turtlesim_kinematics",
    )

    return LaunchDescription([
        arg_x,
        arg_y,
        arg_theta,
        arg_name,
        turtlesim,
        spawn_turtle2,
        kinematics,
    ])
