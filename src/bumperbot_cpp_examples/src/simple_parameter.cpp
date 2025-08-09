// Cleaned up includes and comments; add <functional> for std::bind placeholders
#include <rclcpp/rclcpp.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>

#include <functional>
#include <string>
#include <vector>

using std::placeholders::_1;

class SimpleParameter : public rclcpp::Node {
public:
  SimpleParameter() : Node("simple_parameter_node") {
    declare_parameter<int>("Simple_int_param", 28);
    declare_parameter<std::string>("Simple_string_param", "Ahmed");

    param_callback_handle_ = add_on_set_parameters_callback(
      std::bind(&SimpleParameter::paramChangeCallback, this, _1)
    );
  }

private:
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_callback_handle_;

  rcl_interfaces::msg::SetParametersResult paramChangeCallback(
    const std::vector<rclcpp::Parameter> &parameters) {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

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
