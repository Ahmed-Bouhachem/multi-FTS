from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PythonExpression

def noisy_controller(context, *args, **kwargs):
    """Create either the Python or C++ noisy controller node with perturbed geometry."""
    wheel_radius = float(LaunchConfiguration("wheel_radius").perform(context))
    wheel_separation = float(LaunchConfiguration("wheel_separation").perform(context))
    wheel_radius_error = float(LaunchConfiguration("wheel_radius_error").perform(context))
    wheel_separation_error = float(LaunchConfiguration("wheel_separation_error").perform(context))

    use_python = LaunchConfiguration("use_python")

    noisy_controller_py = Node(
        package="bumperbot_controller",
        executable="noisy_controller.py",
        parameters=[
            {
                "wheel_radius": wheel_radius + wheel_radius_error,
                "wheel_separation": wheel_separation + wheel_separation_error
            }
        ],
         condition=IfCondition(use_python)
    )

    noisy_controller_cpp = Node(
        package="bumperbot_controller",
        executable="noisy_controller",
        parameters=[
            {
                "wheel_radius": wheel_radius + wheel_radius_error,
                "wheel_separation": wheel_separation + wheel_separation_error
            }
        ],
        condition=UnlessCondition(use_python)
    )

    return [
        noisy_controller_py,
        noisy_controller_cpp
    ]


def generate_launch_description():
    # ---- Launch args ----
    use_python_arg = DeclareLaunchArgument(
        "use_python",
        default_value="False",
        description="When using the simple controller, choose the Python node if True, else C++."
    )

    wheel_radius_arg = DeclareLaunchArgument(
        "wheel_radius",
        default_value="0.033"
    )

    wheel_separation_arg = DeclareLaunchArgument(
        "wheel_separation",
        default_value="0.1402"
    )

    use_simple_controller_arg = DeclareLaunchArgument(
        "use_simple_controller",
        default_value="True",
        description="If True, spawn simple_velocity_controller (+ simple_controller node); else spawn bumperbot_controller."
    )

    wheel_radius_error_arg = DeclareLaunchArgument(
        "wheel_radius_error",
        default_value="0.005"
    )

    wheel_separation_error_arg = DeclareLaunchArgument(
        "wheel_separation_error",
        default_value="0.02"
    )

    # ---- Launch configs ----
    use_python = LaunchConfiguration("use_python")
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

    # ---- Simple controller application nodes (Python or C++) ----
    # Launch these only when the simple controller option is selected.
    # Pick Python or C++ based on use_python.
    simple_controller_py = Node(
        package="bumperbot_controller",
        executable="simple_controller.py",
        parameters=[{
            "wheel_radius": wheel_radius,
            "wheel_separation": wheel_separation
        }],
        condition=IfCondition(
            PythonExpression([
                use_simple_controller, " == 'True' and ",
                use_python, " == 'True'"
            ])
        ),
        output="screen"
    )

    simple_controller_cpp = Node(
        package="bumperbot_controller",
        executable="simple_controller",
        parameters=[{
            "wheel_radius": wheel_radius,
            "wheel_separation": wheel_separation
        }],
        condition=IfCondition(
            PythonExpression([
                use_simple_controller, " == 'True' and not (",
                use_python, " == 'True')"
            ])
        ),
        output="screen"
    )


    noisy_controller_launch = OpaqueFunction(function=noisy_controller)
    # ---- Assemble LD ----
    return LaunchDescription([
        use_python_arg,
        wheel_radius_arg,
        wheel_separation_arg,
        use_simple_controller_arg,
        wheel_radius_error_arg,
        wheel_separation_error_arg,

        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,
        simple_velocity_controller_spawner,

        simple_controller_py,
        simple_controller_cpp,
        noisy_controller_launch,
    ])
