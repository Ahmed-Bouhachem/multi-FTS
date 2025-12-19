#ifndef KALMAN_FILTER_HPP

#define  KALMAN_FILTER_HPP
#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/imu.hpp>

// OdometryMotionModel: 1D Kalman filter over the robot's angular velocity
// combining noisy wheel odometry with IMU measurements.
class OdometryMotionModel : public rclcpp::Node 
{
    public : 
        // Construct the Kalman filter node and set up odom/IMU interfaces.
        OdometryMotionModel(const std::string & name);
    private :
        rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_ ;
        rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_ ;
        rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_ ;

        double mean_;
        double variance_;
        double imu_angular_z_;
        bool is_first_odom_;
        double last_angular_z_;
        double motion_;

        nav_msgs::msg::Odometry kalman_odom_;

        double motion_variance_;
        double measurement_variance_;

        // Measurement update step combining prediction with IMU reading.
        void measurementUpdate();

        // State prediction step using odometry motion.
        void statePrediction();
        
        // Odometry callback: update motion estimate and run predict/update cycle.
        void odomCallback(const nav_msgs::msg::Odometry & odom);

        // IMU callback: store latest angular velocity measurement.
        void imuCallback(const sensor_msgs::msg::Imu & imu);


};

#endif //KALMAN_FILTER_HPP
