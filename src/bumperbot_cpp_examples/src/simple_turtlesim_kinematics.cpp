// Implementation file for SimpleTurtlesimKinematics node. // File-level comment
// Subscribes to both turtles' pose topics and prints the XY translation // High-level behavior
// from turtle1 to turtle2 whenever a new turtle2 pose arrives. // Trigger condition
#include "bumperbot_cpp_examples/simple_turtlesim_kinematics.hpp" // Include matching header
#include <functional>  // for std::bind and placeholders // Needed for std::bind
#include <cmath>       // for std::hypot and angle normalization // Math utilities

using std::placeholders::_1; // Bring placeholder _1 into scope for std::bind

SimpleTurtlesimKinematics::SimpleTurtlesimKinematics(const std::string &name) // Constructor definition
    : rclcpp::Node(name) { // Initialize base rclcpp::Node with provided name
  // Subscribe to pose of turtle1 (used as reference frame) // Subscription setup comment
  turtle1_pose_sub_ = create_subscription<turtlesim::msg::Pose>( // Create subscriber for turtle1 pose
      "/turtle1/pose", 10, // Topic name and QoS depth
      std::bind(&SimpleTurtlesimKinematics::turtle1PoseCallback, this, _1)); // Bind callback method

  // Subscribe to pose of turtle2; on updates, compute translation relative to turtle1 // Second subscription
  turtle2_pose_sub_ = create_subscription<turtlesim::msg::Pose>( // Create subscriber for turtle2 pose
      "/turtle2/pose", 10, // Topic name and QoS depth
      std::bind(&SimpleTurtlesimKinematics::turtle2PoseCallback, this, _1)); // Bind callback method
} // End constructor

void SimpleTurtlesimKinematics::turtle1PoseCallback( // turtle1 callback definition
    const turtlesim::msg::Pose &pose) { // Pose message parameter
  last_turtle1_pose_ = pose; // Cache the latest pose of turtle1
} // End turtle1 callback

void SimpleTurtlesimKinematics::turtle2PoseCallback( // turtle2 callback definition
    const turtlesim::msg::Pose &pose) { // Pose message parameter
  last_turtle2_pose_ = pose; // Cache the latest pose of turtle2

  // Compute XY translation from turtle1 to turtle2 // Translation calculation comment
  float Tx = last_turtle2_pose_.x - last_turtle1_pose_.x; // Delta X
  float Ty = last_turtle2_pose_.y - last_turtle1_pose_.y; // Delta Y

  // Relative heading delta (turtle2 - turtle1), normalized to [-pi, pi] // Heading delta description
  auto normalize = [](double a) { // Lambda to wrap angle into [-pi, pi]
    while (a > M_PI) a -= 2.0 * M_PI; // Wrap positive overflow
    while (a < -M_PI) a += 2.0 * M_PI; // Wrap negative overflow
    return a; // Return normalized angle
  }; // End lambda
  double theta_rad = normalize(static_cast<double>(last_turtle2_pose_.theta) - // Compute delta heading (rad)
                               static_cast<double>(last_turtle1_pose_.theta)); // Subtract turtle1 heading
  double theta_deg = theta_rad * 180.0 / M_PI; // Convert radians to degrees
  double c = std::cos(theta_rad); // cos(theta)
  double s = std::sin(theta_rad); // sin(theta)

  // Also compute Euclidean distance between turtles // Distance computation comment
  double dist = std::hypot(static_cast<double>(Tx), static_cast<double>(Ty)); // sqrt(Tx^2 + Ty^2)

  // Log the translation and rotation components // Logging block description
  RCLCPP_INFO_STREAM(this->get_logger(), // Use node logger
                     "\nRelative Kinematics (turtle1 -> turtle2)\n" // Heading line
                     << "Tx: " << Tx << "\n" // Print Tx
                     << "Ty: " << Ty << "\n" // Print Ty
                     << "Distance: " << dist << "\n" // Print Euclidean distance
                     << "theta (rad): " << theta_rad << "\n" // Print delta heading in radians
                     << "theta (deg): " << theta_deg << "\n" // Print delta heading in degrees
                     << "Rotation matrix Rz(theta):\n" // Title for rotation matrix
                     << "| " << c << "\t" << -s << " |\n" // First row of 2x2 rotation matrix
                     << "| " << s << "\t" <<  c << " |\n"); // Second row of 2x2 rotation matrix
} // End turtle2 callback

// Standard ROS 2 C++ entry point // main() description
int main(int argc, char* argv[]) { // Program entry signature
    rclcpp::init(argc, argv); // Initialize ROS 2
    auto node = std::make_shared<SimpleTurtlesimKinematics>("SimpleTurtlesimKinematics"); // Create node instance
    rclcpp::spin(node); // Spin the node to process callbacks
    rclcpp::shutdown(); // Shutdown ROS 2

    return 0; // Return success
} // End main
