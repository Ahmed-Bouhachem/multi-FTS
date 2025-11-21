// Implementation of the noisy odometry publisher. It mirrors SimpleController's
// encoder integration but injects Gaussian noise into each measurement so that
// localization filters can be tested against imperfect wheel feedback.

#include "noisy_controller.hpp"  // local header

#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <Eigen/Geometry>
#include <tf2/LinearMath/Quaternion.hpp>
#include <chrono>
#include <random>

using std::placeholders::_1;  // for std::bind subscriptions

// Constructor: declares parameters, sets up subscriptions, and prepares message state.
NoisyController::NoisyController(const std::string & name)
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

    joint_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "/joint_states", 10,
        std::bind(&NoisyController::jointCallback, this, _1));
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>(
         "/bumperbot_controller/odom_noisy", 10);

    odom_msg_.header.frame_id = "odom";
    odom_msg_.child_frame_id = "base_footprint_ekf";
    odom_msg_.pose.pose.orientation.x = 0.0;
    odom_msg_.pose.pose.orientation.y = 0.0;
    odom_msg_.pose.pose.orientation.z = 0.0;
    odom_msg_.pose.pose.orientation.w = 1.0;

    transform_boardcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    transform_stamped_.header.frame_id = "odom";
    transform_stamped_.child_frame_id = "base_footprint_noisy";
    

}


// Integrate encoder positions to maintain a simple planar pose estimate and log it.
void NoisyController::jointCallback(const sensor_msgs::msg::JointState &msg)
{
    // Re-seed each callback so the noise is independently distributed.
    unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
    std::default_random_engine noise_generator(seed);
    std::normal_distribution<double> left_encoder_noise(0.0, 0.005);  // radians
    std::normal_distribution<double> right_encoder_noise(0.0, 0.005); // radians
    auto compute_average_position =
        [&](const std::vector<std::string> &joint_names,
            std::normal_distribution<double> &noise_distribution,
            double &noisy_average,
            double &true_average) -> bool {
            if (joint_names.empty()) {
                return false;
            }
            double sum = 0.0;
            double noisy_sum = 0.0;
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
                double position = msg.position.at(index);
                sum += position;
                noisy_sum += position + noise_distribution(noise_generator);
            }
            true_average = sum / static_cast<double>(joint_names.size());
            noisy_average = noisy_sum / static_cast<double>(joint_names.size());
            return true;
        };

    double left_position = 0.0;
    double right_position = 0.0;
    double noisy_left_position = 0.0;
    double noisy_right_position = 0.0;

    if (!compute_average_position(
            left_wheel_joints_, left_encoder_noise, noisy_left_position, left_position) ||
        !compute_average_position(
            right_wheel_joints_, right_encoder_noise, noisy_right_position, right_position)) {
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

    // Grab wheel position deltas (radians) using noisy observations to emulate encoder error
    double dp_left = noisy_left_position - left_wheel_prev_pos_;
    double dp_right = noisy_right_position - right_wheel_prev_pos_;

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
    auto node = std::make_shared<NoisyController>("noisy_controller");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
