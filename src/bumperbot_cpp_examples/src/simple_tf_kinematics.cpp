#include "bumperbot_cpp_examples/simple_tf_kinematics.hpp"

SimpleTfKinematics::SimpleTfKinematics(const std::string &name) : Node(name) 
{
    static_tf_broadcaster_ = std::make_shared<tf2_ros::StaticTransformBroadcaster>(this);
    static_transfrom_stamped_.header.stamp = get_clock()->now();
    static_transfrom_stamped_.header.frame_id = "bumperbot_base";
    static_transfrom_stamped_.child_frame_id = "bumperbot_top";
    static_transfrom_stamped_.transform.translation.x = 0.0;
    static_transfrom_stamped_.transform.translation.y = 0.0;
    static_transfrom_stamped_.transform.translation.z = 0.3;
    static_transfrom_stamped_.transform.rotation.x = 0.0;
    static_transfrom_stamped_.transform.rotation.y = 0.0;
    static_transfrom_stamped_.transform.rotation.z = 0.0;
    static_transfrom_stamped_.transform.rotation.w = 1.0;


    static_tf_broadcaster_->sendTransform(static_transfrom_stamped_);


    RCLCPP_INFO_STREAM(get_logger(), "Publishing static transform between" <<
        static_transfrom_stamped_.header.frame_id << " and " <<static_transfrom_stamped_.child_frame_id);
}

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SimpleTfKinematics>("SimpleTfKinematics");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}; 
