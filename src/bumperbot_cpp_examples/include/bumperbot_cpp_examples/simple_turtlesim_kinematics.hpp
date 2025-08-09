#ifndef SIMPLE_TURTLESIM_KINEMATICS_HPP
#define SIMPLE_TURTLESIM_KINEMATICS_HPP

#include <rclcpp/rclcpp.hpp>            // Core ROS 2 C++ client library
#include <turtlesim/msg/pose.hpp>       // Pose message published by turtlesim turtles

/**
 * @brief Minimal ROS 2 node that subscribes to turtle1 and turtle2 poses and
 *        prints the translation from turtle1 to turtle2.
*/
class SimpleTurtlesimKinematics : public rclcpp::Node {
public:
/**
 * @brief Construct the node with a custom name.
 * @param name Node name to use when creating the rclcpp::Node base.
 */
explicit SimpleTurtlesimKinematics(const std::string &name);

private:
/**
 * @brief Callback for /turtle1/pose subscription. Stores the last pose.
 */
void turtle1PoseCallback(const turtlesim::msg::Pose &pose);

/**
 * @brief Callback for /turtle2/pose subscription. Stores the last pose and
 *        logs the XY translation relative to the last turtle1 pose.
 */
void turtle2PoseCallback(const turtlesim::msg::Pose &pose);

// Subscriptions to both turtles' pose topics
rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle1_pose_sub_;
rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle2_pose_sub_;

// Cached last poses received from the topics
turtlesim::msg::Pose last_turtle1_pose_;
turtlesim::msg::Pose last_turtle2_pose_;
};

#endif
