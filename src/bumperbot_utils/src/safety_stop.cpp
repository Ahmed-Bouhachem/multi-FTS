#include <string>
#include <memory>
#include <chrono>
#include <thread>
#include <math.h>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/bool.hpp"
#include "twist_mux_msgs/action/joy_turbo.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "visualization_msgs/msg/marker_array.hpp"

using namespace std::chrono_literals;
using std::placeholders::_1;

// Simple finite state machine describing how close an obstacle is.
// FREE    : no nearby obstacle
// WARNING : obstacle within warning_distance_ but outside danger_distance_
// DANGER  : obstacle within danger_distance_ (trigger stop behaviour)
enum State{
  FREE = 0,
  WARNING,
  DANGER
};

class SafetyStop : public rclcpp::Node
{
public:
  // Construct the safety-stop node and initialize parameters, topics and visualization markers.
  SafetyStop()
  : Node("safety_stop_node"),
    is_first_msg_(true),
    state_{State::FREE},
    prev_state_{State::FREE}
  {
    // Distances are expressed in metres in the sensor frame of the incoming LaserScan.
    declare_parameter<double>("warning_distance", 0.6);
    declare_parameter<double>("danger_distance", 0.2);
    declare_parameter<std::string>("scan_topic", "scan");
    declare_parameter<std::string>("safety_stop_topic", "safety_stop");
    warning_distance_ = get_parameter("warning_distance").as_double();
    danger_distance_ = get_parameter("danger_distance").as_double();
    std::string scan_topic = get_parameter("scan_topic").as_string();
    std::string safety_stop_topic = get_parameter("safety_stop_topic").as_string();

    // Subscribe to the LaserScan used to monitor obstacles in front of the robot.
    laser_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
        scan_topic, 10, std::bind(&SafetyStop::laserCallback, this, _1));
    // Publish a simple Bool lock used by twist_mux (locks.safety_stop) to stop the robot.
    safety_stop_pub_ = create_publisher<std_msgs::msg::Bool>(safety_stop_topic, 10);
    // Publish RViz markers showing the warning and danger zones.
    zones_pub_ = create_publisher<visualization_msgs::msg::MarkerArray>("zones", 10);
    // Optional integration with twist_mux JoyTurbo actions:
    // - joy_turbo_decrease  : reduce commanded velocity in WARNING state
    // - joy_turbo_increase  : restore commanded velocity when back to FREE
    decrease_speed_client_ = rclcpp_action::create_client<twist_mux_msgs::action::JoyTurbo>(this, "joy_turbo_decrease");
    increase_speed_client_ = rclcpp_action::create_client<twist_mux_msgs::action::JoyTurbo>(this, "joy_turbo_increase");

    // Prepare Zones for Visualization (a yellow outer cylinder and red inner cylinder).
    visualization_msgs::msg::Marker warning_zone;
    warning_zone.id = 0;
    warning_zone.type = visualization_msgs::msg::Marker::CYLINDER;
    warning_zone.action = visualization_msgs::msg::Marker::ADD;
    warning_zone.scale.z = 0.001;
    warning_zone.scale.x = warning_distance_ * 2;
    warning_zone.scale.y = warning_distance_ * 2;
    warning_zone.color.r = 1.0;
    warning_zone.color.g = 0.984;
    warning_zone.color.b = 0.0;
    warning_zone.color.a = 0.5;
    zones_.markers.push_back(warning_zone);
    visualization_msgs::msg::Marker danger_zone = warning_zone;
    danger_zone.id = 1;
    danger_zone.scale.x = danger_distance_ * 2;
    danger_zone.scale.y = danger_distance_ * 2;
    danger_zone.color.r = 1.0;
    danger_zone.color.g = 0.0;
    danger_zone.color.b = 0.0;
    danger_zone.color.a = 0.5;
    danger_zone.pose.position.z = 0.001;
    zones_.markers.push_back(danger_zone);
  }

private:
  double warning_distance_, danger_distance_;
  bool is_first_msg_;
  State state_, prev_state_;
  visualization_msgs::msg::MarkerArray zones_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr laser_sub_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr safety_stop_pub_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr zones_pub_;
  rclcpp_action::Client<twist_mux_msgs::action::JoyTurbo>::SharedPtr decrease_speed_client_;
  rclcpp_action::Client<twist_mux_msgs::action::JoyTurbo>::SharedPtr increase_speed_client_;

  // LaserScan callback: classify obstacle distance and publish safety_stop/zones (and optional actions).
  void laserCallback(const sensor_msgs::msg::LaserScan &msg)
  {
    // Compute the new state based on the minimum valid range in the scan.
    state_ = State::FREE;
    for (const auto &range : msg.ranges)
    {
      if (!std::isinf(range) && range <= warning_distance_)
      {
        state_ = State::WARNING;
        
        if (range <= danger_distance_)
        {
          state_ = State::DANGER;
          // Stop immediately!
          break;
        }
      }
    }

    // Only react when state changes to avoid spamming topic/actions.
    if(state_ != prev_state_)
    {
      std_msgs::msg::Bool is_safety_stop;
      if(state_ == State::WARNING)
      {
        is_safety_stop.data = false;
        // If the joy_turbo_decrease action server is available, request a speed decrease.
        if (decrease_speed_client_ &&
            decrease_speed_client_->wait_for_action_server(0s)) {
          decrease_speed_client_->async_send_goal(twist_mux_msgs::action::JoyTurbo::Goal());
        }
        zones_.markers.at(0).color.a = 1.0;
        zones_.markers.at(1).color.a = 0.5;
      }
      else if(state_ == State::DANGER)
      {
        is_safety_stop.data = true;
        zones_.markers.at(0).color.a = 1.0;
        zones_.markers.at(1).color.a = 1.0;
      }
      else if(state_ == State::FREE)
      {
        is_safety_stop.data = false;
        // If the joy_turbo_increase action server is available, request a speed increase.
        if (increase_speed_client_ &&
            increase_speed_client_->wait_for_action_server(0s)) {
          increase_speed_client_->async_send_goal(twist_mux_msgs::action::JoyTurbo::Goal());
        }
        zones_.markers.at(0).color.a = 0.5;
        zones_.markers.at(1).color.a = 0.5;
      }

      prev_state_ = state_;
      safety_stop_pub_->publish(is_safety_stop);
    }

    
    if(is_first_msg_)
    {
      for(auto & zone : zones_.markers)
      {
        zone.header.frame_id = msg.header.frame_id;
      }
      is_first_msg_ = false;
    }
    zones_pub_->publish(zones_);
  }
};

// Program entry point: create and spin the SafetyStop node.
int main(int argc, char *argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SafetyStop>());
  rclcpp::shutdown();
  return 0;
}
