#include "bumperbot_controller/simple_controller.hpp"

namespace bumperbot_controller {

Eigen::Vector2d SimpleController::compute(double v, double omega) const {
  const double half = 0.5 * track_width_;
  const double v_left = v - omega * half;
  const double v_right = v + omega * half;
  return Eigen::Vector2d(v_left, v_right);
}

}  // namespace bumperbot_controller
