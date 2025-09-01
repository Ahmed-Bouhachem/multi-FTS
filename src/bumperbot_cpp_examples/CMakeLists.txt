cmake_minimum_required(VERSION 3.8)
project(bumperbot_cpp_examples)

# Enable common warning flags for GCC/Clang builds
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Export compile_commands.json to help IDEs and clangd find includes
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Dependencies required by the example nodes
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rcl_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(bumperbot_msgs REQUIRED)


# --- Executables that contain a main() ---
add_executable(simple_publisher src/simple_publisher.cpp)
ament_target_dependencies(simple_publisher rclcpp std_msgs)

add_executable(simple_subscriber src/simple_subscriber.cpp)
ament_target_dependencies(simple_subscriber rclcpp std_msgs)

add_executable(simple_parameter src/simple_parameter.cpp)
ament_target_dependencies(simple_parameter rclcpp std_msgs rcl_interfaces)

add_executable(simple_tf_kinematics src/simple_tf_kinematics.cpp)

target_include_directories(simple_tf_kinematics PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(simple_tf_kinematics rclcpp tf2_ros geometry_msgs)

# --- Turtlesim kinematics executable ---
add_executable(simple_turtlesim_kinematics src/simple_turtlesim_kinematics.cpp)
target_include_directories(simple_turtlesim_kinematics PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(simple_turtlesim_kinematics rclcpp geometry_msgs turtlesim)

# --- Service server example ---
add_executable(simple_service_server src/simple_service_server.cpp)
ament_target_dependencies(simple_service_server rclcpp bumperbot_msgs)
add_executable(simple_service_client src/simple_service_client.cpp)
ament_target_dependencies(simple_service_client rclcpp bumperbot_msgs)

# Install binaries so they can be launched with `ros2 run`
install(TARGETS
  simple_publisher
  simple_subscriber
  simple_parameter
  simple_turtlesim_kinematics
  simple_tf_kinematics
  simple_service_server
  simple_service_client
  DESTINATION lib/${PROJECT_NAME}
)

# Install the library + headers (optional but good practice)
# Install headers so downstream packages can include them
install(DIRECTORY include/ DESTINATION include)

# Install launch files for `ros2 launch`
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch)

# Install helper Python scripts as executables
install(PROGRAMS
  scripts/spawn_turtle.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
