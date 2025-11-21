// High-level: Differential drive controller node interface.
//
// This header declares a minimal controller node that:
// - Subscribes to a commanded body twist (linear x, angular z) as TwistStamped
// - Converts that into individual wheel speeds (left/right) using a simple
//   differential-drive kinematic model
// - Publishes the wheel speeds as a Float64MultiArray to a controller topic
// - Subscribes to /joint_states to integrate encoder positions into a simple
//   pose estimate (x, y, theta) and logs it for visibility
//
// Notes:
// - The implementation focuses on clarity rather than completeness; no PID.

#ifndef SIMPLE_CONTROLLER_HPP
#define SIMPLE_CONTROLLER_HPP  // standard include guard

#include <rclcpp/rclcpp.hpp>                         // Base ROS 2 node API
#include <geometry_msgs/msg/twist_stamped.hpp>       // Commanded body twist (v, omega)
#include <std_msgs/msg/float64_multi_array.hpp>      // Wheel speed command array
#include <sensor_msgs/msg/joint_state.hpp>           // Encoders for odometry integration
#include <nav_msgs/msg/odometry.hpp>
#include <Eigen/Core>                                // 2x2 matrices and vectors
#include <string>
#include <vector>
#include <tf2_ros/transform_broadcaster.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp> 

// SimpleController: converts body-frame velocities to wheel velocities and logs odometry.
class SimpleController : public rclcpp::Node {
 public:
  // Construct with a ROS 2 node name; parameters are declared inside the ctor.
  explicit SimpleController(const std::string &name);

 private:
  // Callback for commanded body twist (linear.x, angular.z).
  // Computes left/right wheel speeds and publishes them.
  void velCallback(const geometry_msgs::msg::TwistStamped &msg);

  // Callback for joint states; integrates wheel positions into (x, y, theta)
  // using a simple differential-drive kinematic update and logs results.
  void jointCallback(const sensor_msgs::msg::JointState &msg);
  
  // I/O interfaces
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr vel_sub_; // in: cmd_vel
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr wheel_cmd_pub_; // out: wheel speeds (per joint)
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_sub_; // in: wheel encoder positions
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_; // out: integrated odom estimate

  // Robot geometry (meters) and conversion matrix mapping [v, omega] <-> [wr, wl]
  double wheel_radius_;      // radius of a drive wheel (m)
  double wheel_separation_;  // distance between wheel contact points (track width, m)
  Eigen::Matrix2d speed_conversion_; // convenience matrix used for conversion

  std::vector<std::string> left_wheel_joints_;   // joint names on the left side
  std::vector<std::string> right_wheel_joints_;  // joint names on the right side

  // Previous wheel positions and timestamp for delta computations
  double left_wheel_prev_pos_;
  double right_wheel_prev_pos_;
  rclcpp::Time prev_time_;
  bool have_prev_time_{false};

  // Integrated planar pose estimate (world frame)
  double x_;
  double y_;
  double theta_;

  nav_msgs::msg::Odometry odom_msg_;

  std::unique_ptr<tf2_ros::TransformBroadcaster> transform_boardcaster_;
  geometry_msgs::msg::TransformStamped transform_stamped_;

};
#endif
