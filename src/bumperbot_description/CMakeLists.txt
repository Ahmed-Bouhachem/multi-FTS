cmake_minimum_required(VERSION 3.8)
project(bumperbot_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# ------------------------------------------------------------------
# Install static resources straight from the source tree
# ------------------------------------------------------------------
install(
  DIRECTORY meshes urdf launch rviz
  DESTINATION share/${PROJECT_NAME}
)

# ------------------------------------------------------------------
# Generate a plain URDF at build time (so Gazebo can read it quickly)
# ------------------------------------------------------------------
find_program(XACRO xacro REQUIRED)

set(XACRO_INPUT          ${CMAKE_CURRENT_SOURCE_DIR}/urdf/bumperbot.urdf.xacro)
set(GAZEBO_XACRO         ${CMAKE_CURRENT_SOURCE_DIR}/urdf/bumperbot_gazebo.xacro)
# Remove ros2_control dependency completely
# set(ROS2_CONTROL_XACRO   ${CMAKE_CURRENT_SOURCE_DIR}/urdf/bumperbot_ros2_control.xacro)

add_custom_command(
  OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/bumperbot.urdf
  COMMAND ${XACRO} --inorder ${XACRO_INPUT} -o ${CMAKE_CURRENT_BINARY_DIR}/bumperbot.urdf
  DEPENDS ${XACRO_INPUT} ${GAZEBO_XACRO}
  # Remove ros2_control from dependencies: ${ROS2_CONTROL_XACRO}
)

add_custom_target(generate_urdf ALL DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/bumperbot.urdf)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/bumperbot.urdf
        DESTINATION share/${PROJECT_NAME}/urdf)

# ------------------------------------------------------------------
# Tests / linters (optional)
# ------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
