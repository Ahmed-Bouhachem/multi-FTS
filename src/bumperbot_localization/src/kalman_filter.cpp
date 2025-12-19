#include "bumperbot_localization/kalman_filter.hpp"

using std::placeholders::_1;

// Construct the Kalman filter node and initialize filter state and interfaces.
OdometryMotionModel::OdometryMotionModel(const std::string & name)
    : Node(name)
    , mean_(0.0)
    , variance_(1000.0)
    , imu_angular_z_(0.0)
    , is_first_odom_(true)
    , last_angular_z_(0.0)
    , motion_(0.0)
    , motion_variance_(4.0)
    , measurement_variance_(0.5)
{
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>("bumperbot_controller/odom_noisy", 10 ,std::bind(&OdometryMotionModel::odomCallback, this, _1));
    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>("imu/out", 10, std::bind(&OdometryMotionModel::imuCallback, this, _1));
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("bumperbot_controller/odom_kalman", 10);
};

// Odometry callback: compute motion increment, run predict/update and publish filtered odom.
void OdometryMotionModel::odomCallback(const nav_msgs::msg::Odometry & odom)
    {
        kalman_odom_ = odom;
        if(is_first_odom_) {
            mean_ = odom.twist.twist.angular.z;
            last_angular_z_ = odom.twist.twist.angular.z;
            is_first_odom_ = false;
            return;
        }

        motion_ = odom.twist.twist.angular.z - last_angular_z_;

        statePrediction();
        measurementUpdate();

        kalman_odom_.twist.twist.angular.z = mean_;
        odom_pub_->publish(kalman_odom_);
    };

// IMU callback: store the latest angular velocity measurement.
void OdometryMotionModel::imuCallback(const sensor_msgs::msg::Imu & imu)
    {
        imu_angular_z_ = imu.angular_velocity.z;
    }

// Measurement update: fuse prediction with IMU using scalar Kalman filter equations.
void OdometryMotionModel::measurementUpdate()
    {
        mean_ = (measurement_variance_ * mean_ + variance_ * imu_angular_z_) / (variance_ + measurement_variance_) ;
        variance_ = (variance_ * measurement_variance_) / (variance_ + measurement_variance_);
    }

// State prediction: propagate the mean and variance using the motion model.
void OdometryMotionModel::statePrediction()
    {
        mean_ = mean_ + motion_;
    variance_ = variance_ + motion_variance_;
    }

// Program entry point: initialize ROS 2 and spin the Kalman filter node.
int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<OdometryMotionModel>("kalman_filter");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
