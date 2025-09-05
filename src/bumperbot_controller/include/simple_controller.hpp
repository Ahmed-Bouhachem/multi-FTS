// NOTE: Legacy header stub (not wired in CMake). Kept for reference only.
// Implements a Node that would convert TwistStamped into wheel commands.

#ifndef SIMPLE_CONTROLLER_HPP
#define SIMPLE_CONTROLLER_HPPs  // (sic) legacy include guard as originally written

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <Eigen/Core>

class SimpleController : public rclcpp::Node {
 public:
  explicit SimpleController(const std::string &name);

 private:
  // Subscription callback receiving cmd_vel (stamped)
  void velCallback(const geometry_msgs::msg::TwistStamped &msg);

  void jointCallback(const sensor_msgs::msg::JointState &msg);
  // I/O interfaces
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr vel_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr wheel_cmd_pub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_sub_;

  // Robot geometry and conversion matrix
  double wheel_radius_;
  double wheel_separation_;
  Eigen::Matrix2d speed_conversion_;

  double left_wheel_prev_pos_;
  double right_wheel_prev_pos_;
  rclcpp::Time prev_time_;

};
#endif
