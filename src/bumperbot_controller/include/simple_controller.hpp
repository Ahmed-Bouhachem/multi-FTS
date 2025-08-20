// NOTE: Legacy header stub (not wired in CMake). Kept for reference only.
// Implements a Node that would convert TwistStamped into wheel commands.

#ifndef SIMPLE_CONTROLLER_HPP
#define SIMPLE_CONTROLLER_HPPs  // (sic) legacy include guard as originally written

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <Eigen/Core>

class SimpleController : public rclcpp::Node {
 public:
  explicit SimpleController(const std::string &name);

 private:
  // Subscription callback receiving cmd_vel (stamped)
  void velcallback(const geometry_msgs::msg::TwistStamped &msg);

  // I/O interfaces
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr vel_sub;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr Wheel_cmd_pub_;

  // Robot geometry and conversion matrix
  double wheel_radios_;
  double wheel_separation_;
  Eigen::Matrix2d speed_conversion_;
};
#endif
