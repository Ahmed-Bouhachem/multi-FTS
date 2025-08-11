#ifndef BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP
#define BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP

#include <Eigen/Core>            // Core Eigen types like Vector2d

namespace bumperbot_controller {

// Simple differential drive controller helper.
// Converts (v, omega) into left/right wheel linear speeds given track width.
class SimpleController {
public:
  explicit SimpleController(double track_width)
      : track_width_(track_width) {}

  // Compute [v_left, v_right]^T from linear v and angular omega.
  Eigen::Vector2d compute(double v, double omega) const;

  double track_width() const { return track_width_; }

private:
  double track_width_;
};

}  // namespace bumperbot_controller

#endif  // BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP

