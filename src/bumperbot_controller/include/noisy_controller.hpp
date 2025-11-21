#ifndef NOISY_CONTROLLER_HPP
#define NOISY_CONTROLLER_HPP  // (sic) legacy include guard as originally written

#include <rclcpp/rclcpp.hpp>                         // Base ROS 2 node API
#include <sensor_msgs/msg/joint_state.hpp>           // Encoder feedback
#include <nav_msgs/msg/odometry.hpp>                 // Published noisy odom estimate
#include <tf2_ros/transform_broadcaster.hpp>         // TF broadcaster for noisy odom frame
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <string>
#include <vector>

// NoisyController: clones SimpleController's odometry pipeline but injects
// configurable Gaussian noise into the wheel encoder readings so downstream
// filters can be stress-tested with imperfect sensor data.
class NoisyController : public rclcpp::Node {
 public:
  explicit NoisyController(const std::string &name);

 private:
  // Callback that reads joint states, perturbs them with noise, integrates
  // the pose, and publishes both Odometry and TF frames.
  void jointCallback(const sensor_msgs::msg::JointState &msg);

  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_sub_; // in: wheel encoder positions
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;          // out: noisy odom estimate

  double wheel_radius_;      // wheel radius (m)
  double wheel_separation_;  // axle track (m)
  std::vector<std::string> left_wheel_joints_;
  std::vector<std::string> right_wheel_joints_;

  double left_wheel_prev_pos_;   // previous left wheel encoder (rad)
  double right_wheel_prev_pos_;  // previous right wheel encoder (rad)
  rclcpp::Time prev_time_;
  bool have_prev_time_{false};

  double x_;      // integrated x position in odom frame
  double y_;      // integrated y position in odom frame
  double theta_;  // integrated heading (yaw)

  nav_msgs::msg::Odometry odom_msg_;

  std::unique_ptr<tf2_ros::TransformBroadcaster> transform_boardcaster_;
  geometry_msgs::msg::TransformStamped transform_stamped_;
};

#endif
