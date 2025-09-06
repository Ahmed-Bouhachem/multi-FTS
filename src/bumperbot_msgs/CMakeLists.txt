cmake_minimum_required(VERSION 3.8)
project(bumperbot_msgs)

# Define custom interfaces (services) used across the workspace.

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generate C++/Python code for our services
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AddTwoInts.srv"      # a, b -> sum
  "srv/GetTransform.srv"    # frame_id, child_frame_id -> TransformStamped, success
  DEPENDENCIES geometry_msgs # GetTransform uses geometry_msgs/TransformStamped
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(rosidl_default_runtime)

ament_package()
