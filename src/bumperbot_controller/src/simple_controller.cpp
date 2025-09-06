// Implementation of a minimal differential-drive helper node.
// Responsibilities:
// 1) Convert commanded body twist (v, omega) into individual wheel angular speeds
// 2) Publish wheel speeds to the controller interface
// 3) Integrate joint encoder positions for a basic odometry estimate and log it

#include "/home/ghost/FTS-repo/src/bumperbot_controller/include/simple_controller.hpp"  // local header

#include <Eigen/Geometry>

using std::placeholders::_1;  // for std::bind subscriptions

// Constructor: declares parameters, sets up pubs/subs, and precomputes conversion matrix.
SimpleController::SimpleController(const std::string & name)
: Node(name)
  , left_wheel_prev_pos_(0.0)
  , right_wheel_prev_pos_(0.0)
  , x_(0.0)
  , y_(0.0)
  , theta_(0.0)

{
    // Declare geometry parameters with defaults (meters)
    declare_parameter("wheel_radius", 0.033);
    declare_parameter("wheel_separation", 0.17);

    wheel_radius_ = get_parameter("wheel_radius").as_double();
    wheel_separation_ = get_parameter("wheel_separation").as_double();

    RCLCPP_INFO_STREAM(get_logger(), "Using wheel_radius " << wheel_radius_);
    RCLCPP_INFO_STREAM(get_logger(), "Using wheel_separation " << wheel_separation_);

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

    // Derivation for a differential drive:
    // [ v ]   = [ r/2      r/2 ] [ wr ]
    // [ w ]     [ r/b   -r/b ] [ wl ]
    // where r = wheel_radius, b = wheel_separation, wr/wl are right/left wheel angular speeds
    speed_conversion_ << wheel_radius_ / 2,  wheel_radius_ / 2,
                         wheel_radius_ / wheel_separation_, -wheel_radius_ / wheel_separation_;

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
    // Controller expects [right, left]; ensure ordering matches your controller config
    wheel_speed_msg.data.push_back(wheel_speed.coeff(1)); // left
    wheel_speed_msg.data.push_back(wheel_speed.coeff(0)); // right

    wheel_cmd_pub_->publish(wheel_speed_msg);
}
// Integrate encoder positions to maintain a simple planar pose estimate and log it.
void SimpleController::jointCallback(const sensor_msgs::msg::JointState &msg)
{
    // Grab wheel position deltas (radians); assumes indices [right=0, left=1]
    double dp_left = msg.position.at(1) - left_wheel_prev_pos_;
    double dp_right = msg.position.at(0) - right_wheel_prev_pos_;

    rclcpp::Time msg_time = msg.header.stamp;
    rclcpp::Duration dt = msg_time - prev_time_;

    left_wheel_prev_pos_ = msg.position.at(1);
    right_wheel_prev_pos_ = msg.position.at(0);
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
