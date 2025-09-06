// SimpleTfKinematics: publishes a static transform between bumperbot_base and
// bumperbot_top, and a dynamic transform between odom and bumperbot_base.
// Also exposes a service to query the transform between any two frames using TF2.
//
// This header declares the node interface and primary members used for
// broadcasting and looking up transforms.
#ifndef SIMPLE_TF_KINEMATICS_HPP
#define SIMPLE_TF_KINEMATICS_HPP

#include <rclcpp/rclcpp.hpp>
#include <tf2_ros/static_transform_broadcaster.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <memory>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <bumperbot_msgs/srv/get_transform.hpp>
#include <tf2/LinearMath/Quaternion.h>

class SimpleTfKinematics : public rclcpp :: Node {
    public :
        // Construct the node with a given name; timers and services are created in the ctor.
        SimpleTfKinematics(const std::string &name);


    private:
        // Broadcasters for static and dynamic transforms
        std::shared_ptr<tf2_ros::StaticTransformBroadcaster> static_tf_broadcaster_;
        std::unique_ptr<tf2_ros::TransformBroadcaster> dynamic_tf_broadcaster_;
        geometry_msgs::msg::TransformStamped static_transfrom_stamped_;
        geometry_msgs::msg::TransformStamped dynamic_transfrom_stamped_;

        // Service to query a TransformStamped between arbitrary frames
        rclcpp::Service<bumperbot_msgs::srv::GetTransform>::SharedPtr get_transform_srv_;

        rclcpp::TimerBase::SharedPtr timer_;

        // TF2 buffer + listener to consume transforms for service requests
        std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
        std::shared_ptr<tf2_ros::TransformListener> tf_listener_{nullptr};

        // Parameters driving the example motion
        double x_increment_;
        double last_x_;
        int rotations_counter_;
        tf2::Quaternion last_orientation_;
        tf2::Quaternion orientation_increment_;

        // Periodic update to publish the dynamic transform
        void timerCallback();

        // Service callback: look up the requested transform and populate the response
        void getTransformCallback(
            const std::shared_ptr<bumperbot_msgs::srv::GetTransform::Request> req,
            std::shared_ptr<bumperbot_msgs::srv::GetTransform::Response> res);
    };

#endif
