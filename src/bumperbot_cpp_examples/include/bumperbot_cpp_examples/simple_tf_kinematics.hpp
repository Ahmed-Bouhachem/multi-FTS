#ifndef SIMPLE_TF_KINEMATICS_HPP
#define SIMPLE_TF_KINEMATICS_HPP

#include <rclcpp/rclcpp.hpp>
#include <tf2_ros/static_transform_broadcaster.h>
#include <memory>
#include<geometry_msgs/msg/transform_stamped.hpp>

class SimpleTfKinematics : public rclcpp :: Node {
    public :
        SimpleTfKinematics(const std::string &name);


    private:
        std::shared_ptr<tf2_ros::StaticTransformBroadcaster> static_tf_broadcaster_;
        geometry_msgs::msg::TransformStamped static_transfrom_stamped_;
};

#endif
