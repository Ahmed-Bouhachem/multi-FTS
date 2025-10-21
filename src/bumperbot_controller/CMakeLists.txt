cmake_minimum_required(VERSION 3.8)
project(bumperbot_controller)

# Build glue for the controller nodes (simple + noisy variants) and ship
# associated launch/config assets. Keep this file comment-heavy to clarify the
# ament bits for newer ROS developers.

# Compiler warnings
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ---- Dependencies ----
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(Eigen3 REQUIRED)


# ---- Include directories ----
include_directories(
  include
  ${EIGEN3_INCLUDE_DIRS}
)

# ---- Executables ----
# Simple controller: converts commanded body twist into wheel velocities and
# publishes a plain odom estimate.
add_executable(simple_controller src/simple_controller.cpp)

ament_target_dependencies(simple_controller
  rclcpp
  geometry_msgs
  std_msgs
  ${Eigen_LIBRARIES}
  sensor_msgs
  tf2
  tf2_ros
  nav_msgs
)

# Noisy controller: reuses the odom pipeline but injects encoder noise.
add_executable(noisy_controller src/noisy_controller.cpp)

ament_target_dependencies(noisy_controller
  rclcpp
  geometry_msgs
  ${Eigen_LIBRARIES}
  sensor_msgs
  tf2
  tf2_ros
  nav_msgs
)


# ---- Install headers for downstream includes ----
install(
  DIRECTORY include/
  DESTINATION include
)

# ---- Install executables so they can be used with `ros2 run` ----
install(TARGETS
  simple_controller
  noisy_controller
  DESTINATION lib/${PROJECT_NAME}
)

# ---- Install config & launch files (kept flat) ----
install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)


# Linting & testing
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
