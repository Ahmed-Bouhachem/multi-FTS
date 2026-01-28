// Implementation of a minimal differential-drive helper node.
// Responsibilities:
// 1) Convert commanded body twist (v, omega) into individual wheel angular speeds
// 2) Publish wheel speeds to the controller interface
// 3) Integrate joint encoder positions for a basic odometry estimate and log it

#include "simple_controller.hpp"  // local header

#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <Eigen/Geometry>
#include <tf2/LinearMath/Quaternion.hpp>


using std::placeholders::_1;  // for std::bind subscriptions

// Constructor: declares parameters, sets up pubs/subs, and precomputes conversion matrix.
SimpleController::SimpleController(const std::string & name)
: Node(name)
  , left_wheel_prev_pos_(0.0)
  , right_wheel_prev_pos_(0.0)
  , have_prev_time_(false)
  , x_(0.0)
  , y_(0.0)
  , theta_(0.0)

{
    // Declare geometry parameters with defaults (meters)
    declare_parameter("wheel_radius", 0.033);
    declare_parameter("wheel_separation", 0.17);

    wheel_radius_ = get_parameter("wheel_radius").as_double();
    wheel_separation_ = get_parameter("wheel_separation").as_double();

    left_wheel_joints_ = this->declare_parameter<std::vector<std::string>>(
        "left_wheel_joints",
        {"wheel_left_joint"});
    right_wheel_joints_ = this->declare_parameter<std::vector<std::string>>(
        "right_wheel_joints",
        {"wheel_right_joint"});

    if (left_wheel_joints_.empty() || right_wheel_joints_.empty()) {
        throw std::runtime_error("Wheel joint parameter lists must not be empty.");
    }

    auto join_names = [](const std::vector<std::string> &names) {
        std::ostringstream oss;
        for (size_t i = 0; i < names.size(); ++i) {
            if (i > 0) {
                oss << ", ";
            }
            oss << names[i];
        }
        return oss.str();
    };

    RCLCPP_INFO_STREAM(get_logger(), "Using wheel_radius " << wheel_radius_);
    RCLCPP_INFO_STREAM(get_logger(), "Using wheel_separation " << wheel_separation_);
    RCLCPP_INFO_STREAM(get_logger(), "Left wheel joints: [" << join_names(left_wheel_joints_) << "]");
    RCLCPP_INFO_STREAM(get_logger(), "Right wheel joints: [" << join_names(right_wheel_joints_) << "]");

    prev_time_ = get_clock()->now();

    // Publisher for wheel speeds [right, left] as expected by the controller
    wheel_cmd_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
        "/simple_velocity_controller/commands", 10);

    // Subscribe to commanded body-frame velocities (v, omega)
    vel_sub_ = create_subscription<geometry_msgs::msg::TwistStamped>(
        "/bumperbot_controller/cmd_vel", 10,
        std::bind(&SimpleController::velCallback, this, _1));
    // Subscribe to joint states (encoder positions) for odometry integration
    joint_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "/joint_states", 10,
        std::bind(&SimpleController::jointCallback, this, _1));
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>(
         "bumperbot_controller/odom", 10);

    // Derivation for a differential drive:
    // [ v ]   = [ r/2      r/2 ] [ wr ]
    // [ w ]     [ r/b   -r/b ] [ wl ]
    // where r = wheel_radius, b = wheel_separation, wr/wl are right/left wheel angular speeds
    speed_conversion_ << wheel_radius_ / 2,  wheel_radius_ / 2,
                         wheel_radius_ / wheel_separation_, -wheel_radius_ / wheel_separation_;

    odom_msg_.header.frame_id = "odom";
    odom_msg_.child_frame_id = "base_footprint";
    odom_msg_.pose.pose.orientation.x = 0.0;
    odom_msg_.pose.pose.orientation.y = 0.0;
    odom_msg_.pose.pose.orientation.z = 0.0;
    odom_msg_.pose.pose.orientation.w = 1.0;

    transform_boardcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    transform_stamped_.header.frame_id = "odom";
    transform_stamped_.child_frame_id = "base_footprint";
    

    RCLCPP_INFO_STREAM(get_logger(), "The conversion matrix is \n" << speed_conversion_);
}

// Convert commanded body twist into wheel angular speeds and publish.
void SimpleController::velCallback(const geometry_msgs::msg::TwistStamped & msg)
{
    // robot_speed = [v, w] where v is linear.x (m/s) and w is angular.z (rad/s)
    Eigen::Vector2d robot_speed(msg.twist.linear.x, msg.twist.angular.z);

    // Solve for wheel angular speeds [wr, wl]
    Eigen::Vector2d wheel_speed = speed_conversion_.inverse() * robot_speed;

    std_msgs::msg::Float64MultiArray wheel_speed_msg;
    wheel_speed_msg.data.reserve(left_wheel_joints_.size() + right_wheel_joints_.size());

    for (const auto & joint : left_wheel_joints_) {
        (void)joint;
        wheel_speed_msg.data.push_back(wheel_speed.coeff(1)); // identical command for each left wheel
    }
    for (const auto & joint : right_wheel_joints_) {
        (void)joint;
        wheel_speed_msg.data.push_back(wheel_speed.coeff(0)); // identical command for each right wheel
    }

    wheel_cmd_pub_->publish(wheel_speed_msg);
}
// Integrate encoder positions to maintain a simple planar pose estimate and log it.
void SimpleController::jointCallback(const sensor_msgs::msg::JointState &msg)
{
    auto compute_average_position =
        [&](const std::vector<std::string> &joint_names, double &average) -> bool {
            if (joint_names.empty()) {
                return false;
            }
            double sum = 0.0;
            for (const auto &joint_name : joint_names) {
                auto it = std::find(msg.name.begin(), msg.name.end(), joint_name);
                if (it == msg.name.end()) {
                    RCLCPP_WARN_THROTTLE(
                        get_logger(), *get_clock(), 2000,
                        "Joint '%s' not present in JointState message.", joint_name.c_str());
                    return false;
                }
                const auto index = static_cast<size_t>(std::distance(msg.name.begin(), it));
                if (index >= msg.position.size()) {
                    RCLCPP_WARN_THROTTLE(
                        get_logger(), *get_clock(), 2000,
                        "JointState position array shorter than names array.");
                    return false;
                }
                sum += msg.position.at(index);
            }
            average = sum / static_cast<double>(joint_names.size());
            return true;
        };

    double left_position = 0.0;
    double right_position = 0.0;
    if (!compute_average_position(left_wheel_joints_, left_position) ||
        !compute_average_position(right_wheel_joints_, right_position)) {
        return;
    }

    rclcpp::Time msg_time = msg.header.stamp;
    if (!have_prev_time_) {
        prev_time_ = msg_time;
        left_wheel_prev_pos_ = left_position;
        right_wheel_prev_pos_ = right_position;
        have_prev_time_ = true;
        return;
    }

    rclcpp::Duration dt = msg_time - prev_time_;
    if (dt.seconds() <= 0.0) {
        RCLCPP_WARN_THROTTLE(
            get_logger(), *get_clock(), 2000,
            "Non-positive dt detected (%.6f s); skipping odom integration.", dt.seconds());
        return;
    }

    // Grab wheel position deltas (radians) based on averaged joints per side
    double dp_left = left_position - left_wheel_prev_pos_;
    double dp_right = right_position - right_wheel_prev_pos_;

    left_wheel_prev_pos_ = left_position;
    right_wheel_prev_pos_ = right_position;
    prev_time_ = msg_time;

    // Instantaneous wheel angular rates (rad/s)
    double fi_left = dp_left / dt.seconds();
    double fi_right = dp_right / dt.seconds();

    // Body-frame linear and angular velocities
    double linear = (wheel_radius_ * fi_right + wheel_radius_ * fi_left) / 2 ;
    double angular = (wheel_radius_ * fi_right - wheel_radius_ * fi_left) / wheel_separation_ ;

    // Integrate pose increment from wheel position deltas
    double d_s = (wheel_radius_ * dp_right + wheel_radius_ * dp_left) / 2;
    double d_theta = (wheel_radius_ * dp_right - wheel_radius_ * dp_left) / wheel_separation_;

    theta_ += d_theta;
    x_ += d_s * cos(theta_);
    y_ += d_s * sin(theta_);

    tf2::Quaternion q;
    q.setRPY(0, 0, theta_);
    odom_msg_.pose.pose.orientation.x = q.x();
    odom_msg_.pose.pose.orientation.y = q.y();
    odom_msg_.pose.pose.orientation.z = q.z();
    odom_msg_.pose.pose.orientation.w = q.w();
    odom_msg_.header.stamp = get_clock()->now();
    odom_msg_.pose.pose.orientation.x = x_;
    odom_msg_.pose.pose.orientation.y = y_;
    odom_msg_.twist.twist.linear.x = linear;
    odom_msg_.twist.twist.angular.z = angular;

    transform_stamped_.transform.translation.x = x_;
    transform_stamped_.transform.translation.y = y_;
    transform_stamped_.transform.rotation.x = q.x();
    transform_stamped_.transform.rotation.y = q.y();
    transform_stamped_.transform.rotation.z = q.z();
    transform_stamped_.transform.rotation.w = q.w();
    transform_stamped_.header.stamp = get_clock()->now();


    odom_pub_->publish(odom_msg_);
    transform_boardcaster_->sendTransform(transform_stamped_);
    
    // Log current velocity estimate and integrated pose
    RCLCPP_INFO_STREAM(get_logger(), "Linear : "<< linear << " Angular : "<< angular);
    RCLCPP_INFO_STREAM(get_logger(), "x:" << x_ << " y:" << y_ << " theta:" << theta_);

};

// Standalone entry point to spin the node.
int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SimpleController>("simple_controller");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
