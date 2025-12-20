#include <chrono>     // for std::chrono::milliseconds
#include <algorithm>  // for std::clamp

#include "bumperbot_motion/pure_pursuit.hpp"           // node class declaration
#include "tf2/utils.h"                                      // tf2::TimePointZero
#include "geometry_msgs/msg/transform_stamped.hpp"          // TransformStamped for TF lookups
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"          // tf2::fromMsg / tf2::doTransform helpers

namespace bumperbot_motion
{

// Constructor: set up parameters, TF, subscriptions, publishers, and timer for pure pursuit.
PurePursuit::PurePursuit()
: Node("pure_puzsuit_node"),                // initialize base rclcpp::Node with a name                                      // default derivative gain
  look_ahead_distance_(0.5),                               // default step size along the path (m)
  max_linear_velocity_(0.3),                     // linear speed saturation (m/s)
  max_angular_velocity_(1.0)                        // initialize previous linear error
{
  // Allocate TF buffer and listener so we can query the robot pose in "odom".
  tf_buffer_ = std::make_shared<tf2_ros::Buffer>(get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

  // Declare pure-pursuit motion parameters (these can be overridden via YAML or CLI).
  declare_parameter<double>("look_ahead_distance", look_ahead_distance_);
  declare_parameter<double>("max_linear_velocity", max_linear_velocity_);
  declare_parameter<double>("max_angular_velocity", max_angular_velocity_);

  // Read back the parameter values, possibly overridden from defaults.
  look_ahead_distance_ = get_parameter("look_ahead_distance").as_double();
  max_linear_velocity_ = get_parameter("max_linear_velocity").as_double();
  max_angular_velocity_ = get_parameter("max_angular_velocity").as_double();

  // Subscribe to the global path produced by the A* planner.
  path_sub_ = create_subscription<nav_msgs::msg::Path>(
    "/a_star/path",                           // topic name
    10,                                       // queue depth
    std::bind(&PurePursuit::pathCallback, // member function pointer
      this, std::placeholders::_1));          // bind "this" and the incoming message

  // Publish velocity commands directly into the Bumperbot diff-drive controller's
  // unstamped cmd_vel input. This is the same topic used by twist_mux / joystick.
  cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>(
    "/bumperbot_controller/cmd_vel_unstamped",  // controller input
    10);                                        // queue depth

  // Publish the next target pose (marker on the path) for visualization in RViz.
  carrot_pose_pub_= create_publisher<geometry_msgs::msg::PoseStamped>(
    "/pure_pursuit/carrot", 10);

  // Create a periodic timer (10 Hz) to run the control loop.
  control_loop_ = create_wall_timer(
    std::chrono::milliseconds(100),            // period
    std::bind(&PurePursuit::controlLoop,   // callback to execute
      this));                                  // "this" instance

}

// Path callback: store the most recent global plan to be tracked.
void PurePursuit::pathCallback(const nav_msgs::msg::Path::SharedPtr path)
{
  global_plan_ = *path;  // copy entire path so controlLoop can use it
}

// Main control loop: compute a pure-pursuit velocity command that drives the robot along global_plan_.
void PurePursuit::controlLoop()
{
  // If there is no plan, do nothing.
  if (global_plan_.poses.empty()) {
    return;
  }

  // --- 1) Get the robot pose in the odom frame ---

  geometry_msgs::msg::TransformStamped robot_pose;  // transform from odom -> base_footprint
  try {
    robot_pose = tf_buffer_->lookupTransform(
      "odom",            // target frame
      "base_footprint",  // source frame
      tf2::TimePointZero // latest available transform
    );
  } catch (tf2::TransformException & ex) {
    RCLCPP_WARN(get_logger(), "Could not transform: %s", ex.what());
    return;  // skip this cycle if TF is unavailable
  }

  // Ensure the stored plan is expressed in the same frame as robot_pose.
  if (!transformPlan(robot_pose.header.frame_id)) {
    RCLCPP_ERROR(get_logger(), "Unable to transform plan into robot frame");
    return;
  }

  // Build a PoseStamped representation of the robot pose (same frame as plan).
  geometry_msgs::msg::PoseStamped robot_pose_stamped;
  robot_pose_stamped.header.frame_id = robot_pose.header.frame_id;
  robot_pose_stamped.pose.position.x = robot_pose.transform.translation.x;
  robot_pose_stamped.pose.position.y = robot_pose.transform.translation.y;
  robot_pose_stamped.pose.position.z = robot_pose.transform.translation.z;
  robot_pose_stamped.pose.orientation = robot_pose.transform.rotation;

  // --- 2) Pick the next target pose along the plan ---

  auto carrot_pose = getCarrotPose(robot_pose_stamped);  // look ahead along path

  // Compute straight-line distance between robot and this target.
  double dx = carrot_pose.pose.position.x - robot_pose_stamped.pose.position.x;
  double dy = carrot_pose.pose.position.y - robot_pose_stamped.pose.position.y;
  double distance = std::sqrt(dx * dx + dy * dy);

  // If we are close enough to the last target, consider the goal reached.
  if (distance <= 0.1) {  // 10 cm tolerance
    RCLCPP_INFO(get_logger(), "Goal reached!");
    global_plan_.poses.clear();  // drop plan so we stop commanding motion
    return;
  }

  // Publish the chosen next pose, so you can visualize the tracking target in RViz.
  carrot_pose_pub_->publish(carrot_pose);

  // --- 3) Compute pose error in the robot frame using TF transforms ---

  tf2::Transform robot_tf;        // pose of robot in world
  tf2::Transform carrot_pose_tf;    // pose of target in world
  tf2::Transform carrot_pose_robot_tf;  // pose of target in robot frame

  // Convert geometry_msgs pose messages into tf2::Transform objects.
  tf2::fromMsg(robot_pose_stamped.pose, robot_tf);
  tf2::fromMsg(carrot_pose.pose, carrot_pose_tf);

  // Compute target pose relative to robot (robot frame).
  carrot_pose_robot_tf = robot_tf.inverse() * carrot_pose_tf;
  tf2::toMsg(carrot_pose_robot_tf, carrot_pose.pose);
  double curvature = getCurvature(carrot_pose.pose);
  geometry_msgs::msg::Twist cmd_vel;
  cmd_vel.linear.x = max_linear_velocity_;
  cmd_vel.angular.z = curvature * max_angular_velocity_;
  cmd_pub_->publish(cmd_vel);
}

// Choose a "look-ahead" pose on the global plan that is at least look_ahead_distance_ away.
geometry_msgs::msg::PoseStamped PurePursuit::getCarrotPose(
  const geometry_msgs::msg::PoseStamped & robot_pose)
{
  // Start from the last pose (goal) as a fallback.
  geometry_msgs::msg::PoseStamped carrot_pose = global_plan_.poses.back();

  // Walk backward along the path until we find a pose far enough from the robot.
  for (auto pose_it = global_plan_.poses.rbegin();
    pose_it != global_plan_.poses.rend(); ++pose_it)
  {
    double dx = pose_it->pose.position.x - robot_pose.pose.position.x;
    double dy = pose_it->pose.position.y - robot_pose.pose.position.y;
    double distance = std::sqrt(dx * dx + dy * dy);

    if (distance > look_ahead_distance_) {
      // Found a pose at least look_ahead_distance_ away; use that as the next target.
      carrot_pose = *pose_it;
    } else {
      // As soon as we find a pose that is too close, stop searching.
      break;
    }
  }

  return carrot_pose;
}
// Compute the curvature k of the circular arc passing through the carrot point.
// The carrot pose is expressed in the robot frame; curvature k = 2*y / (x^2 + y^2).
double PurePursuit::getCurvature(const geometry_msgs::msg::Pose & carrot_pose)
{
  const double carrot_dist =
    (carrot_pose.position.x * carrot_pose.position.x) +
    (carrot_pose.position.y * carrot_pose.position.y);

  // If the carrot is too close to the robot, treat curvature as zero.
  if (carrot_dist > 0.001) {
    return 2.0 * carrot_pose.position.y / carrot_dist;
  } else {
    return 0.0;
  }
}
// Ensure the current global plan is expressed in the desired frame (e.g., "odom").
bool PurePursuit::transformPlan(const std::string & frame)
{
  // If the plan is already in the requested frame, nothing to do.
  if (global_plan_.header.frame_id == frame) {
    return true;
  }

  geometry_msgs::msg::TransformStamped transform;
  try {
    // Find a transform from the plan's original frame into the requested one.
    transform = tf_buffer_->lookupTransform(
      frame,                         // target frame
      global_plan_.header.frame_id,  // source frame
      tf2::TimePointZero);           // latest transform
  } catch (tf2::ExtrapolationException & ex) {
    RCLCPP_ERROR_STREAM(
      get_logger(),
      "Couldn't transform plan from frame " << global_plan_.header.frame_id <<
        " to frame " << frame << ": " << ex.what());
    return false;
  }

  // Transform every pose in the path into the new frame.
  for (auto & pose : global_plan_.poses) {
    tf2::doTransform(pose, pose, transform);
  }

  // Update the header frame to reflect the new frame.
  global_plan_.header.frame_id = frame;
  return true;
}

}  // namespace bumperbot_motion

// Program entry point: initialize ROS 2, spin the node, then shut down.
int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);  // initialize ROS 2 client library

  // Create the PurePursuit node.
  auto node = std::make_shared<bumperbot_motion::PurePursuit>();

  // Spin the node so callbacks and the timer are processed.
  rclcpp::spin(node);

  // Cleanly shut down ROS 2.
  rclcpp::shutdown();
  return 0;
}
