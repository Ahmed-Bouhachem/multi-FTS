// Minimal publisher node: publishes a string message to 'chatter' once per second. // File purpose
#include <rclcpp/rclcpp.hpp>            // ROS 2 client library // Include rclcpp
#include <std_msgs/msg/string.hpp>      // Standard string message // Include String msg
#include <chrono>                       // For time literals // Include chrono
#include <memory>                       // For std::make_shared // Include memory

using namespace std::chrono_literals;   // enables 1s literal for timer period // Use chrono literals

class SimplePublisher : public rclcpp::Node { // Define node class // Inherit rclcpp::Node
public: // Public section // Accessible methods
    // Create the node, a publisher, and a 1 Hz timer to trigger publishes // Constructor comment
    SimplePublisher() : Node("simple_publisher"), counter_(0) { // Initialize node name and counter // Ctor init list
        pub_ = this->create_publisher<std_msgs::msg::String>("chatter", 10); // Create publisher on 'chatter' with QoS depth 10 // Publisher
        timer_ = this->create_wall_timer( // Create periodic timer // Timer
            1s, std::bind(&SimplePublisher::timer_callback, this)); // 1 Hz, bind callback // Bind cb
    } // End constructor // End ctor

private: // Private section // Internal details
    // Timer callback: create and publish a message, then increment the counter // Callback purpose
    void timer_callback() { // Define timer callback // Method start
        auto message = std_msgs::msg::String(); // Create message instance // Msg var
        message.data = "Hello ROS2 - counter: " + std::to_string(counter_++); // Fill message with text and counter // Set data
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str()); // Log the outgoing message // Log
        pub_->publish(message); // Publish the message // Publish
    } // End timer_callback // End method

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_; // Publisher handle // Member
    rclcpp::TimerBase::SharedPtr timer_;                       // Timer for periodic publishing // Member
    unsigned int counter_;                                     // Counter for messages // Member
}; // End class SimplePublisher // End class

int main(int argc, char* argv[]) { // Program entry point // main
    rclcpp::init(argc, argv); // Initialize ROS 2 // Init
    auto node = std::make_shared<SimplePublisher>(); // Create node instance // New node
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Node started"); // Log startup // Info
    rclcpp::spin(node); // Process callbacks // Spin
    rclcpp::shutdown(); // Shutdown ROS 2 // Shutdown
    return 0; // Exit success // Return
} // End main // End
