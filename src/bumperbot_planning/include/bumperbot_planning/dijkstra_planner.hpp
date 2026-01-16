// Dijkstra-based global planner plugin for Nav2.
// Defines a grid GraphNode helper and DijkstraPlanner, an implementation of
// nav2_core::GlobalPlanner that plans on a 2D costmap using Dijkstra's algorithm.
#ifndef DIJKSTRA_PLANNER_HPP
#define DIJKSTRA_PLANNER_HPP

#include <string>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

#include "nav2_core/global_planner.hpp"
#include "nav_msgs/msg/path.hpp"
#include "nav2_util/robot_utils.hpp"
#include "nav2_util/lifecycle_node.hpp"
#include "nav2_costmap_2d/costmap_2d_ros.hpp"
#include "nav2_msgs/action/smooth_path.hpp"

namespace bumperbot_planning
{
// Graph node used by Dijkstra's algorithm; stores grid indices, path cost and
// a back-pointer to reconstruct the shortest path.
struct GraphNode
{
    int x;
    int y;
    int cost;
    std::shared_ptr<GraphNode> prev;

    // Construct a node at (0, 0) with zero cost.
    GraphNode() : GraphNode(0,0) {}

    // Construct a node at grid coordinates (in_x, in_y) with zero initial cost.
    GraphNode(int in_x, int in_y) : x(in_x), y(in_y), cost(0){}

    // Comparison operator based on total cost so nodes can be ordered in a
    // std::priority_queue for Dijkstra's search.
    bool operator>(const GraphNode & other) const { 
        return cost > other.cost;
    }

    // Equality test based solely on grid position.
    bool operator==(const GraphNode & other) const {
        return x == other.x && y == other.y;
    }

    // Add an (dx, dy) offset to this node to obtain a neighbouring grid cell.
    GraphNode operator+(std::pair<int, int> const & other) {
        GraphNode res(x + other.first, y + other.second);
        return res;
    }
};  

// Global planner plugin implementing Dijkstra search on a 2D Nav2 costmap.
class DijkstraPlanner : public nav2_core::GlobalPlanner
{
public:
  // Default constructor and destructor; heavy initialisation happens in configure().
  DijkstraPlanner() = default;
  ~DijkstraPlanner() = default;

  // Configure the planner from the Nav2 lifecycle node, TF buffer and costmap.
  void configure(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    std::string name, std::shared_ptr<tf2_ros::Buffer> tf,
    std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros) override;

  void cleanup() override;

  void activate() override;

  void deactivate() override;

  // Compute a global plan between start and goal poses in the global frame.
  nav_msgs::msg::Path createPlan(
    const geometry_msgs::msg::PoseStamped & start,
    const geometry_msgs::msg::PoseStamped & goal
    // this for jazzy or newer version std::function<bool()> cancel_checker
    ) override;

private:
  // TF buffer used to transform poses into the global planning frame.
  std::shared_ptr<tf2_ros::Buffer> tf_;
  // Owning lifecycle node handle provided by Nav2.
  nav2_util::LifecycleNode::SharedPtr node_;
  // Pointer to the underlying 2D costmap used for planning.
  nav2_costmap_2d::Costmap2D * costmap_;
  // Name of the global frame used for planning and the plugin instance name.
  std::string global_frame_, name_;
  // Resolution at which the global path is interpolated.
  double interpolation_resolution_;

  // Client used to call the Nav2 smooth path action to post-process the raw plan.
  rclcpp_action::Client<nav2_msgs::action::SmoothPath>::SharedPtr smooth_client_;

  // Return true if the given node lies inside the current costmap bounds.
  bool poseOnMap(const GraphNode & node);

  // Convert a world-frame pose into a grid node on the costmap.
  GraphNode worldToGrid(const geometry_msgs::msg::Pose & pose);

  // Convert a grid node back into a world-frame pose on the costmap.
  geometry_msgs::msg::Pose gridToWorld(const GraphNode & node);

  // Map a grid node to a linear cell index into the costmap data array.
  unsigned int poseToCell(const GraphNode & node);
};

}  // namespace bumperbot_planning

#endif  // DIJKSTRA_PLANNER_HPP
