// Demonstrates declaring parameters and reacting to changes via a callback.
#include <rclcpp/rclcpp.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>

#include <functional>
#include <string>
#include <vector>

using std::placeholders::_1; // for add_on_set_parameters_callback binding

class SimpleParameter : public rclcpp::Node {
public:
  // Create the node, declare two parameters, and register a change callback
  SimpleParameter() : Node("simple_parameter_node") {
    // Declare parameters with default values
    declare_parameter<int>("Simple_int_param", 28);
    declare_parameter<std::string>("Simple_string_param", "Ahmed");

    // Register a callback invoked when any parameter is set at runtime
    param_callback_handle_ = add_on_set_parameters_callback(
      std::bind(&SimpleParameter::paramChangeCallback, this, _1)
    );
  }

private:
  // Keep the callback handle alive as long as the node lives
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_callback_handle_;

  // Validate or react to parameter changes and report success/failure
  rcl_interfaces::msg::SetParametersResult paramChangeCallback(
    const std::vector<rclcpp::Parameter> &parameters) {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true; // accept all changes in this simple example

    for (const auto &param : parameters) {
      if (param.get_name() == "Simple_int_param") {
        RCLCPP_INFO(this->get_logger(), "Simple_int_param changed to: %d", static_cast<int>(param.as_int()));
      } else if (param.get_name() == "Simple_string_param") {
        RCLCPP_INFO(this->get_logger(), "Simple_string_param changed to: %s", param.as_string().c_str());
      }
    }

    return result;
  }
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SimpleParameter>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
