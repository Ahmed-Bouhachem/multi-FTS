from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('bumperbot_description')
    controller_dir = get_package_share_directory('bumperbot_controller')
    
    # Use the simple URDF with ros2_control
    xacro_file = os.path.join(pkg_dir, 'urdf', 'bumperbot_simple.urdf.xacro')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
    # Also render URDF to a file to avoid passing huge XML via CLI params
    generated_urdf = os.path.join(os.getenv('TMPDIR', '/tmp'), 'bumperbot_simple.urdf')
    gen_urdf_proc = ExecuteProcess(
        cmd=['bash', '-lc', f'xacro "{xacro_file}" > "{generated_urdf}"'],
        output='screen'
    )

    # Controller configuration
    controller_config = os.path.join(controller_dir, 'config', 'bumperbot_controllers.yaml')

    # GUI toggle
    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch Gazebo client (GUI)'
    )

    # Gazebo server with ROS plugins (factory for spawn, init for ROS clock)
    gzserver = ExecuteProcess(
        cmd=[
            'gzserver', '--verbose',
            '/usr/share/gazebo-11/worlds/empty.world',
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so'
        ],
        additional_env={'RCL_ASSERT_ARGUMENTS': '0'},
        output='screen'
    )

    gzclient = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('gui')),
        cmd=['gzclient'],
        output='screen'
    )

    # Robot state publisher (publishes TF using robot_description)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
    )


    # Spawn robot after a short delay to ensure Gazebo is ready
    spawn_entity = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                # Spawn from file to avoid long parameter overrides on CLI
                arguments=['-entity', 'bumperbot_simple', '-file', generated_urdf, '-z', '0.05'],
                output='screen'
            )
        ]
    )

    # Start controllers after spawning
    start_controllers = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['joint_state_broadcaster'],
                output='screen'
            ),
            Node(
                package='controller_manager',
                executable='spawner',
                # Match the controller name defined in bumperbot_controllers.yaml
                arguments=['bumperbot_controller'],
                output='screen'
            )
        ]
    )



    start_helper_nodes = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='bumperbot_controller',
                executable='noisy_controller',
                name='noisy_controller',
                output='screen',
                parameters=[{'use_sim_time': True}]
            ),
            Node(
                package='bumperbot_controller',
                executable='simple_controller',
                name='simple_controller',
                output='screen',
                parameters=[{'use_sim_time': True}]
            ),
            Node(
                package='bumperbot_localization',
                executable='kalman_filter',
                name='kalman_filter',
                output='screen',
                parameters=[{'use_sim_time': True}],
                remappings=[('imu_plugin/out', 'imu')]
            )
        ]
    )

    return LaunchDescription([
        gui_arg,
        gen_urdf_proc,
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity,
        start_controllers,
        start_helper_nodes
    ])
