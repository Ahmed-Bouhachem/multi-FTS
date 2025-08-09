// Implementation file for SimpleTurtlesimKinematics node.
// Subscribes to both turtles' pose topics and prints the XY translation
// from turtle1 to turtle2 whenever a new turtle2 pose arrives.
#include "bumperbot_cpp_examples/simple_turtlesim_kinematics.hpp"
#include <functional>  // for std::bind and placeholders
#include <cmath>       // for std::hypot and angle normalization

using std::placeholders::_1;

SimpleTurtlesimKinematics::SimpleTurtlesimKinematics(const std::string &name)
    : rclcpp::Node(name) {
  // Subscribe to pose of turtle1 (used as reference frame)
  turtle1_pose_sub_ = create_subscription<turtlesim::msg::Pose>(
      "/turtle1/pose", 10,
      std::bind(&SimpleTurtlesimKinematics::turtle1PoseCallback, this, _1));

  // Subscribe to pose of turtle2; on updates, compute translation relative to turtle1
  turtle2_pose_sub_ = create_subscription<turtlesim::msg::Pose>(
      "/turtle2/pose", 10,
      std::bind(&SimpleTurtlesimKinematics::turtle2PoseCallback, this, _1));
}

void SimpleTurtlesimKinematics::turtle1PoseCallback(
    const turtlesim::msg::Pose &pose) {
  // Cache the latest pose of turtle1
  last_turtle1_pose_ = pose;
}

void SimpleTurtlesimKinematics::turtle2PoseCallback(
    const turtlesim::msg::Pose &pose) {
  // Cache the latest pose of turtle2
  last_turtle2_pose_ = pose;

  // Compute XY translation from turtle1 to turtle2
  float Tx = last_turtle2_pose_.x - last_turtle1_pose_.x;
  float Ty = last_turtle2_pose_.y - last_turtle1_pose_.y;

  // Relative heading delta (turtle2 - turtle1), normalized to [-pi, pi]
  auto normalize = [](double a) {
    while (a > M_PI) a -= 2.0 * M_PI;
    while (a < -M_PI) a += 2.0 * M_PI;
    return a;
  };
  double theta_rad = normalize(static_cast<double>(last_turtle2_pose_.theta) -
                               static_cast<double>(last_turtle1_pose_.theta));
  double theta_deg = theta_rad * 180.0 / M_PI;
  double c = std::cos(theta_rad);
  double s = std::sin(theta_rad);

  // Also compute Euclidean distance between turtles
  double dist = std::hypot(static_cast<double>(Tx), static_cast<double>(Ty));

  // Log the translation and rotation components
  RCLCPP_INFO_STREAM(this->get_logger(),
                     "\nRelative Kinematics (turtle1 -> turtle2)\n"
                     << "Tx: " << Tx << "\n"
                     << "Ty: " << Ty << "\n"
                     << "Distance: " << dist << "\n"
                     << "theta (rad): " << theta_rad << "\n"
                     << "theta (deg): " << theta_deg << "\n"
                     << "Rotation matrix Rz(theta):\n"
                     << "| " << c << "\t" << -s << " |\n"
                     << "| " << s << "\t" <<  c << " |\n");
}

// Standard ROS 2 C++ entry point
int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    // Create and spin the kinematics node
    auto node = std::make_shared<SimpleTurtlesimKinematics>("SimpleTurtlesimKinematics");
    rclcpp::spin(node);
    rclcpp::shutdown();

    return 0;
}
