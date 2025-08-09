#ifndef SIMPLE_TURTLESIM_KINEMATICS_HPP // Start of include guard to prevent multiple inclusion
#define SIMPLE_TURTLESIM_KINEMATICS_HPP // Define the include guard macro

#include <rclcpp/rclcpp.hpp>            // Include ROS 2 C++ client library APIs
#include <turtlesim/msg/pose.hpp>       // Include turtlesim pose message definition

/**
 * @brief Minimal ROS 2 node that subscribes to turtle1 and turtle2 poses and
 *        prints the translation from turtle1 to turtle2. // Class purpose
 */
class SimpleTurtlesimKinematics : public rclcpp::Node { // Class inherits from rclcpp::Node
 public: // Public interface of the class
  /**
   * @brief Construct the node with a custom name. // Constructor docs
   * @param name Node name to use when creating the rclcpp::Node base. // Parameter description
   */
  explicit SimpleTurtlesimKinematics(const std::string &name); // Constructor taking node name

 private: // Private members and methods
  /**
   * @brief Callback for /turtle1/pose subscription. Stores the last pose. // turtle1 pose handler
   */
  void turtle1PoseCallback(const turtlesim::msg::Pose &pose); // Called when a new turtle1 pose arrives

  /**
   * @brief Callback for /turtle2/pose subscription. Stores the last pose and
   *        logs the XY translation relative to the last turtle1 pose. // turtle2 pose handler
   */
  void turtle2PoseCallback(const turtlesim::msg::Pose &pose); // Called when a new turtle2 pose arrives

  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle1_pose_sub_; // Subscription to /turtle1/pose
  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle2_pose_sub_; // Subscription to /turtle2/pose

  turtlesim::msg::Pose last_turtle1_pose_; // Cached last pose of turtle1
  turtlesim::msg::Pose last_turtle2_pose_; // Cached last pose of turtle2
}; // End of class SimpleTurtlesimKinematics

#endif // End of include guard
