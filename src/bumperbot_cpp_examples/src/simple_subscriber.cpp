// Minimal subscriber node: subscribes to 'chatter' and logs received strings. // File purpose
#include <rclcpp/rclcpp.hpp>           // ROS 2 client library // Include rclcpp
#include <std_msgs/msg/string.hpp>     // Standard string message // Include String msg

using std::placeholders::_1;          // placeholder for std::bind // Use _1

class SimpleSubscriber : public rclcpp::Node { // Define node class // Inherit Node
public: // Public section // Methods
    // Create the node and subscription with depth-10 QoS // Constructor comment
    SimpleSubscriber() : Node("simple_subscriber") { // Initialize node name // Ctor init
        sub_ = this->create_subscription<std_msgs::msg::String>( // Create subscriber // Subscription
            "chatter", 10, std::bind(&SimpleSubscriber::msgCallback, this, _1)); // Topic/QoS and bind callback // Bind cb
    } // End constructor // End ctor

private: // Private section // Members/callbacks
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_; // Subscription handle // Member

    // Message callback: print the message content // Callback purpose
    void msgCallback(const std_msgs::msg::String &msg) const { // Callback definition // Method
        RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg.data.c_str()); // Log incoming data // Log
    } // End msgCallback // End method
}; // End class SimpleSubscriber // End class

int main(int argc, char* argv[]) { // Program entry // main
    rclcpp::init(argc, argv); // Initialize ROS 2 // Init
    auto node = std::make_shared<SimpleSubscriber>(); // Create node // New node
    rclcpp::spin(node); // Process callbacks // Spin
    rclcpp::shutdown(); // Shutdown ROS 2 // Shutdown
    return 0; // Exit success // Return
} // End main // End
