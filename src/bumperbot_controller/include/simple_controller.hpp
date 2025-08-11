#ifndef SIMPLE_CONTROLLER_HPP
#define

#include<rclcpp/rclcpp.hpp>
#include<geometry_msgs/msg/twist_stamped.hpp>
#include<std_msgs/msg/float64_multi_array.hpp>
#include<Eigen/Core>

class SimpleController : public rclcpp :: Node {

   public:
        SimpleController(const std::string& name);
    

   private:
        void velcallback(const geometry_msgs::msg::TwistStamped& msg);

        rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr vel_sub;
        rclcpp::Publisher<std_msgs::msg::Float64MultiArray>SharedPtr Wheel_cmd_pub_;

        double wheel_radios_;
        double wheel_separation_;
        Eigen::Matrix2d speed_conversion_
};
#endif