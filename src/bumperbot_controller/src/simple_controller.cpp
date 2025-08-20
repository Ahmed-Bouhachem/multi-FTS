// Implementation of a very small differential-drive helper.
// Given linear velocity v and yaw rate omega, compute left/right wheel speeds.
#include "bumperbot_controller/simple_controller.hpp"

namespace bumperbot_controller {

Eigen::Vector2d SimpleController::compute(double v, double omega) const {
  // Half of the distance between wheels (meters)
  const double half = 0.5 * track_width_;
  // Standard differential drive kinematics: v_L = v - w*b, v_R = v + w*b
  const double v_left = v - omega * half;
  const double v_right = v + omega * half;
  // Return as a 2D vector [v_left, v_right]^T
  return Eigen::Vector2d(v_left, v_right);
}

}  // namespace bumperbot_controller
