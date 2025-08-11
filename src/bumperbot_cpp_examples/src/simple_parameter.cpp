// Demonstrates declaring parameters and reacting to changes via a callback. // File purpose
#include <rclcpp/rclcpp.hpp>                              // ROS 2 client library // Include rclcpp
#include <rcl_interfaces/msg/set_parameters_result.hpp>   // Parameter result message // Include result msg

#include <functional>   // for std::bind // Include functional
#include <string>       // for std::string // Include string
#include <vector>       // for std::vector // Include vector

using std::placeholders::_1; // for add_on_set_parameters_callback binding // Use _1

class SimpleParameter : public rclcpp::Node { // Define node class // Inherit Node
public: // Public section // Methods
  // Create the node, declare two parameters, and register a change callback // Constructor comment
  SimpleParameter() : Node("simple_parameter_node") { // Initialize node name // Ctor init
    declare_parameter<int>("Simple_int_param", 28);              // Declare int parameter with default // Param 1
    declare_parameter<std::string>("Simple_string_param", "Ahmed"); // Declare string parameter with default // Param 2

    // Register a callback invoked when any parameter is set at runtime // Callback registration
    param_callback_handle_ = add_on_set_parameters_callback( // Add callback // Register
      std::bind(&SimpleParameter::paramChangeCallback, this, _1) // Bind member function // Bind cb
    ); // End registration // End call
  } // End constructor // End ctor

private: // Private section // Members/callbacks
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_callback_handle_; // Keep callback handle alive // Member

  // Validate or react to parameter changes and report success/failure // Callback purpose
  rcl_interfaces::msg::SetParametersResult paramChangeCallback( // Callback signature // Method
    const std::vector<rclcpp::Parameter> &parameters) { // Incoming parameters // Arg
    rcl_interfaces::msg::SetParametersResult result; // Result object // Local var
    result.successful = true; // accept all changes in this simple example // Accept all

    for (const auto &param : parameters) { // Iterate over changed params // Loop
      if (param.get_name() == "Simple_int_param") { // Check int param // If
        RCLCPP_INFO(this->get_logger(), "Simple_int_param changed to: %d", static_cast<int>(param.as_int())); // Log new int // Log
      } else if (param.get_name() == "Simple_string_param") { // Check string param // Else-if
        RCLCPP_INFO(this->get_logger(), "Simple_string_param changed to: %s", param.as_string().c_str()); // Log new string // Log
      } // End if-else // End branch
    } // End for // End loop

    return result; // Return success // Return
  } // End paramChangeCallback // End method
}; // End class SimpleParameter // End class

int main(int argc, char **argv) { // Entry point // main
  rclcpp::init(argc, argv); // Initialize ROS 2 // Init
  auto node = std::make_shared<SimpleParameter>(); // Create node instance // New node
  rclcpp::spin(node); // Process callbacks // Spin
  rclcpp::shutdown(); // Shutdown ROS 2 // Shutdown
  return 0; // Success // Return
} // End main // End
