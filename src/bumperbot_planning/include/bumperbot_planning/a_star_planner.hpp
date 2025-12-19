#ifndef A_STAR_PLANNER_HPP
#define A_STAR_PLANNER_HPP

#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "nav_msgs/msg/path.hpp"
#include "geometry_msgs/msg/pose.hpp"

#include "tf2_ros/buffer.hpp"
#include "tf2_ros/transform_listener.hpp"
namespace bumperbot_planning {

    // Graph node used by the A* search; stores cost, heuristic and back-pointer.
    struct GraphNode
        {
            int x;
            int y;
            int cost;
            double heuristic;
            std::shared_ptr<GraphNode> prev;

            GraphNode() : GraphNode(0,0) {}

            // Construct a node at (in_x, in_y) with zero cost and heuristic.
            GraphNode(int in_x, int in_y) : x(in_x), y(in_y), cost(0){}

            // Priority-queue comparison using f = g + h.
            bool operator>(const GraphNode & other) const { 
                return cost + heuristic > other.cost + other.heuristic;
            }

            // Two nodes are equal if they share the same grid coordinates.
            bool operator==(const GraphNode & other) const {
                return x == other.x && y == other.y;
            }

            // Add an integer (dx, dy) offset to obtain a neighbour node.
            GraphNode operator+(std::pair<int, int> const & other) {
                GraphNode res(x + other.first, y + other.second);
                return res;
            }
        };

    // Node implementing a simple A* grid planner over an OccupancyGrid.
    class AStarPlanner : public rclcpp::Node
    {
        public: 
            // Construct the planner node and set up subscriptions and publishers.
            AStarPlanner();

        private:
            rclcpp::Subscription<nav_msgs::msg::OccupancyGrid>::SharedPtr map_sub_;
            rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr pose_sub_;
            rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr path_pub_;
            rclcpp::Publisher<nav_msgs::msg::OccupancyGrid>::SharedPtr map_pub_;

            nav_msgs::msg::OccupancyGrid::SharedPtr map_;
            nav_msgs::msg::OccupancyGrid visited_map_;

            std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
            std::unique_ptr<tf2_ros::Buffer> tf_buffer_;

            // OccupancyGrid callback: cache the map and reset visited nodes.
            void mapCallback(const nav_msgs::msg::OccupancyGrid::SharedPtr map);
            // Goal callback: compute an A* path between robot and clicked goal.
            void goalCallback(const geometry_msgs::msg::PoseStamped::SharedPtr pose);

            // Convert a world pose to a grid node.
            GraphNode worldToGrid(const geometry_msgs::msg::Pose & pose);
            // Convert a grid node back into a world pose.
            geometry_msgs::msg::Pose gridToWorld(const GraphNode & node);
            // True if the node lies inside the map bounds.
            bool poseOnMap(const GraphNode & node);
            // Convert a node into a linear OccupancyGrid index.
            unsigned poseToCell(const GraphNode & node);

            // Manhattan distance heuristic used by A*.
            double manhattanDistance(const GraphNode & node, const GraphNode & goal_node);

            // Core A* search routine between start and goal poses.
            nav_msgs::msg::Path plan(const geometry_msgs::msg::Pose & start, const geometry_msgs::msg::Pose & goal);

    };
}


#endif // A_STAR_PLANNER_HPP
