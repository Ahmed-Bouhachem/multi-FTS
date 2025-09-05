cmake_minimum_required(VERSION 3.8)
project(bumperbot_controller)

# Compiler warnings
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(Eigen3 REQUIRED)


# Include directories
include_directories(
  include
  ${EIGEN3_INCLUDE_DIRS}
)

# Executable
add_executable(simple_controller src/simple_controller.cpp)

ament_target_dependencies(simple_controller
  rclcpp
  geometry_msgs
  std_msgs
  sensor_msgs
)

# Install headers
install(
  DIRECTORY include/
  DESTINATION include
)

# Install executable
install(TARGETS
  simple_controller
  DESTINATION lib/${PROJECT_NAME}
)

# Install config & launch files
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
