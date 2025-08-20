#ifndef BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP
#define BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP

#include <Eigen/Core>  // Core Eigen types like Vector2d

namespace bumperbot_controller {

// Small helper for differential drive kinematics.
// Converts a body-frame linear velocity (v) and yaw rate (omega)
// into left/right wheel linear speeds using the track width.
class SimpleController {
public:
  // track_width: distance between the two drive wheels (meters)
  explicit SimpleController(double track_width)
      : track_width_(track_width) {}

  // Compute [v_left, v_right]^T from linear v and angular omega.
  Eigen::Vector2d compute(double v, double omega) const;

  // Accessor for configured track width
  double track_width() const { return track_width_; }

private:
  double track_width_;
};

}  // namespace bumperbot_controller

#endif  // BUMPERBOT_CONTROLLER_SIMPLE_CONTROLLER_HPP
