// A*-based global planner plugin implementation for Nav2.
// This file contains the concrete A* search operating on the Nav2 costmap
// and exposes the planner as a pluginlib component.
#include <cmath>
#include <chrono>
#include <queue>
#include <vector>
#include <algorithm>

#include "bumperbot_planning/a_star_planner.hpp"

namespace bumperbot_planning
{
void AStarPlanner::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name, std::shared_ptr<tf2_ros::Buffer> tf,
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros)
{
  node_ = parent.lock();
  name_ = name;
  tf_ = tf;
  costmap_ = costmap_ros->getCostmap();
  global_frame_ = costmap_ros->getGlobalFrameID();

  smooth_client_ = rclcpp_action::create_client<nav2_msgs::action::SmoothPath>(node_, "smooth_path");
}

void AStarPlanner::cleanup()
{
  RCLCPP_INFO(
    node_->get_logger(), "CleaningUp plugin %s of type AStarPlanner",
    name_.c_str());
}

void AStarPlanner::activate()
{
  RCLCPP_INFO(
    node_->get_logger(), "Activating plugin %s of type AStarPlanner",
    name_.c_str());
  if (!smooth_client_->wait_for_action_server(std::chrono::seconds(3))) {
    RCLCPP_ERROR(node_->get_logger(), "Action server not available after waiting");
  }
}

void AStarPlanner::deactivate()
{
  RCLCPP_INFO(
    node_->get_logger(), "Deactivating plugin %s of type AStarPlanner",
    name_.c_str());
}

nav_msgs::msg::Path AStarPlanner::createPlan(
  const geometry_msgs::msg::PoseStamped & start,
  const geometry_msgs::msg::PoseStamped & goal
  // this for jazzy or newer version std::function<bool()>
  )
{
  // 4-neighbour connectivity (up, down, left, right).
  std::vector<std::pair<int, int>> explore_directions = {
    {-1, 0}, {1, 0}, {0, -1}, {0, 1}
  };

  // Pending nodes ordered by f = g + h (A* frontier).
  std::priority_queue<GraphNode, std::vector<GraphNode>, std::greater<GraphNode>> pending_nodes;
  // Nodes that were already expanded (used to prevent re-processing).
  std::vector<GraphNode> visited_nodes;
  
  GraphNode start_node = worldToGrid(start.pose);
  GraphNode goal_node = worldToGrid(goal.pose);
  // Initialize heuristic for the start node.
  start_node.heuristic = manhattanDistance(start_node, goal_node);
  pending_nodes.push(start_node);

  GraphNode active_node;
  while (!pending_nodes.empty() && rclcpp::ok()) {
    active_node = pending_nodes.top();
    pending_nodes.pop();

    // Stop when the goal grid cell is reached.
    if (active_node == goal_node) {
      break;
    }

    // Explore 4-connected neighbours around the current active node.
    for (const auto & dir : explore_directions) {
        GraphNode new_node = active_node + dir;
        // Only consider nodes that are within map bounds, free (below lethal
        // threshold) and not yet visited.
        if (std::find(visited_nodes.begin(), visited_nodes.end(), new_node) == visited_nodes.end() &&
            poseOnMap(new_node) && costmap_->getCost(new_node.x, new_node.y) < 99) {
            // Accumulate cost as number of steps plus cell cost to bias around obstacles.
            new_node.cost = active_node.cost + 1 + costmap_->getCost(new_node.x, new_node.y);
            // Update heuristic relative to the goal.
            new_node.heuristic = manhattanDistance(new_node, goal_node);
            // Store back-pointer to reconstruct the shortest path later.
            new_node.prev = std::make_shared<GraphNode>(active_node);
            pending_nodes.push(new_node);
            visited_nodes.push_back(new_node);
        }
    }
  }

  nav_msgs::msg::Path path;
  path.header.frame_id = global_frame_;
  // Reconstruct the discrete path by following back-pointers from the goal
  // node to the start node and converting each grid cell back to world poses.
  while(active_node.prev && rclcpp::ok()) {
    geometry_msgs::msg::Pose last_pose = gridToWorld(active_node);
    geometry_msgs::msg::PoseStamped last_pose_stamped;
    last_pose_stamped.header.frame_id = global_frame_;
    last_pose_stamped.pose = last_pose;
    path.poses.push_back(last_pose_stamped);
    active_node = *active_node.prev;
  }
  std::reverse(path.poses.begin(), path.poses.end());

  // If the smooth path action server is available, send the raw A* path
  // to be smoothed and, on success, replace the original plan.
  if(smooth_client_->action_server_is_ready()){
    nav2_msgs::action::SmoothPath::Goal path_smooth;
    path_smooth.path = path;
    path_smooth.check_for_collisions = false;
    path_smooth.smoother_id = "simple_smoother";
    path_smooth.max_smoothing_duration.sec = 10;
    auto future = smooth_client_->async_send_goal(path_smooth);

    if(future.wait_for(std::chrono::seconds(3)) == std::future_status::ready){
      auto goal_handle = future.get();
      if(goal_handle){
        auto result_future = smooth_client_->async_get_result(goal_handle);
        if(result_future.wait_for(std::chrono::seconds(3)) == std::future_status::ready){
          auto result_path = result_future.get();
          if(result_path.code == rclcpp_action::ResultCode::SUCCEEDED){
            path = result_path.result->path;
          }
        }
      }
    }
  }
    
  return path;
}

double AStarPlanner::manhattanDistance(const GraphNode &node, const GraphNode &goal_node)
{
    return abs(node.x - goal_node.x) + abs(node.y - goal_node.y);
}

bool AStarPlanner::poseOnMap(const GraphNode & node)
{
    return node.x < static_cast<int>(costmap_->getSizeInCellsX()) && node.x >= 0 &&
        node.y < static_cast<int>(costmap_->getSizeInCellsY()) && node.y >= 0;
}

GraphNode AStarPlanner::worldToGrid(const geometry_msgs::msg::Pose & pose)
{
    int grid_x = static_cast<int>((pose.position.x - costmap_->getOriginX()) / costmap_->getResolution());
    int grid_y = static_cast<int>((pose.position.y - costmap_->getOriginY()) / costmap_->getResolution());
    return GraphNode(grid_x, grid_y);
}

geometry_msgs::msg::Pose AStarPlanner::gridToWorld(const GraphNode & node)
{
    geometry_msgs::msg::Pose pose;
    pose.position.x = node.x * costmap_->getResolution() + costmap_->getOriginX();
    pose.position.y = node.y * costmap_->getResolution() + costmap_->getOriginY();
    return pose;
}

unsigned int AStarPlanner::poseToCell(const GraphNode & node)
{
    return costmap_->getOriginX() * node.y + node.x;
}

}  // namespace bumperbot_planning

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(bumperbot_planning::AStarPlanner, nav2_core::GlobalPlanner)
