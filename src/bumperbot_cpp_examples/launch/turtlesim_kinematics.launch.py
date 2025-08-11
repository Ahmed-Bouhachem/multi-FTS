"""
Launch turtlesim and the kinematics example node together.  # Module docstring

This script:  # Description list intro
  - Starts turtlesim_node  # First bullet
  - Spawns a second turtle (configurable position/name)  # Second bullet
  - Starts the simple_turtlesim_kinematics node which prints the XY translation  # Third bullet line 1
    from turtle1 to the spawned turtle  # Third bullet line 2
"""

from launch import LaunchDescription  # Import LaunchDescription type
from launch.actions import TimerAction, DeclareLaunchArgument  # Timer and arg actions
from launch_ros.actions import Node  # Node action for ROS 2 nodes
from launch.substitutions import LaunchConfiguration  # For accessing launch args


def generate_launch_description() -> LaunchDescription:  # Entry point function for launch
    # Launch arguments for turtle2 spawn  # Comment heading
    arg_x = DeclareLaunchArgument('x', default_value='5.0', description='turtle2 x')  # x arg
    arg_y = DeclareLaunchArgument('y', default_value='5.0', description='turtle2 y')  # y arg
    arg_theta = DeclareLaunchArgument('theta', default_value='0.0', description='turtle2 heading (rad)')  # theta arg
    arg_name = DeclareLaunchArgument('name', default_value='turtle2', description='turtle2 name')  # name arg
    # Base turtlesim window with the first turtle (turtle1)  # turtlesim node
    turtlesim = Node(  # Create Node action
        package="turtlesim",  # Package name
        executable="turtlesim_node",  # Executable name
        name="turtlesim"  # Node name
    )  # End Node

    # Spawn turtle2 after turtlesim starts
    # Delay spawn slightly to ensure the /spawn service is available  # Timer rationale
    spawn_turtle2 = TimerAction(  # Create TimerAction
        period=1.0,  # Wait 1 second
        actions=[  # Actions to run after timer
            Node(  # Spawn helper node
                package="bumperbot_cpp_examples",  # Package containing helper script
                executable="spawn_turtle.py",  # Installed script name
                name="spawn_turtle2_client",  # Node name override
                arguments=[  # Pass spawn arguments
                    '--x', LaunchConfiguration('x'),  # x from launch arg
                    '--y', LaunchConfiguration('y'),  # y from launch arg
                    '--theta', LaunchConfiguration('theta'),  # theta from launch arg
                    '--name', LaunchConfiguration('name'),  # name from launch arg
                ],  # End arguments
                output="screen",  # Print logs to screen
            )  # End Node
        ],  # End actions list
    )  # End TimerAction

    # Node computing and logging the translation between turtle1 and turtle2  # Kinematics node
    kinematics = Node(  # Create Node action
        package="bumperbot_cpp_examples",  # Package name
        executable="simple_turtlesim_kinematics",  # Executable name
        name="simple_turtlesim_kinematics",  # Node name
    )  # End Node

    return LaunchDescription([  # Return assembled launch description
        arg_x,        # x argument declaration
        arg_y,        # y argument declaration
        arg_theta,    # theta argument declaration
        arg_name,     # name argument declaration
        turtlesim,    # turtlesim base node
        spawn_turtle2,# timer + spawn helper
        kinematics,   # kinematics node
    ])  # End return
