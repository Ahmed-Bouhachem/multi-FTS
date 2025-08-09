// Minimal publisher node: publishes a string message to 'chatter' once per second.
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <chrono>
#include <memory>

using namespace std::chrono_literals; // enables 1s literal for timer period

class SimplePublisher : public rclcpp::Node {
public:
    // Create the node, a publisher, and a 1 Hz timer to trigger publishes
    SimplePublisher() : Node("simple_publisher"), counter_(0) {
        // QoS depth 10 is sufficient for a demo text topic
        pub_ = this->create_publisher<std_msgs::msg::String>("chatter", 10);
        timer_ = this->create_wall_timer(
            1s, std::bind(&SimplePublisher::timer_callback, this));
    }

private:
    // Timer callback: create and publish a message, then increment the counter
    void timer_callback() {
        auto message = std_msgs::msg::String();
        message.data = "Hello ROS2 - counter: " + std::to_string(counter_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        pub_->publish(message);
    }

    // Publisher handle and timer for periodic publishing
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    unsigned int counter_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SimplePublisher>();
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Node started");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
