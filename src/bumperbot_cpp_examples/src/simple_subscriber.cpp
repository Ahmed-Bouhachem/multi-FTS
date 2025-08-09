// Minimal subscriber node: subscribes to 'chatter' and logs received strings.
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

using std::placeholders::_1; // placeholder for std::bind

class SimpleSubscriber : public rclcpp::Node {
public:
    // Create the node and subscription with depth-10 QoS
    SimpleSubscriber() : Node("simple_subscriber") {
        sub_ = this->create_subscription<std_msgs::msg::String>(
            "chatter", 10, std::bind(&SimpleSubscriber::msgCallback, this, _1));
    }

private:
    // Subscription handle
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;

    // Message callback: print the message content
    void msgCallback(const std_msgs::msg::String &msg) const {
        RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg.data.c_str());
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SimpleSubscriber>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
