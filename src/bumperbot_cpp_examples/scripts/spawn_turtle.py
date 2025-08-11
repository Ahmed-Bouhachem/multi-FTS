#!/usr/bin/env python3  # Use Python 3 interpreter
"""
Small helper to call turtlesim's /spawn service with arguments.  # Module docstring
"""
import argparse  # Parse command line arguments
import sys       # Access exit and argv

import rclpy     # ROS 2 Python client library
from rclpy.node import Node  # Base class for ROS 2 nodes
from turtlesim.srv import Spawn  # Service type for spawning turtles


class SpawnClient(Node):  # Define a node class for invoking the service
    def __init__(self, x: float, y: float, theta: float, name: str):  # Constructor with spawn params
        super().__init__('spawn_client')  # Initialize node with name
        self.cli = self.create_client(Spawn, '/spawn')  # Create service client for /spawn
        while not self.cli.wait_for_service(timeout_sec=1.0):  # Wait until service is available
            self.get_logger().info('Waiting for /spawn service...')  # Log waiting status
        self.req = Spawn.Request()  # Instantiate request object
        self.req.x = float(x)       # Assign x coordinate
        self.req.y = float(y)       # Assign y coordinate
        self.req.theta = float(theta)  # Assign heading (rad)
        self.req.name = name        # Assign turtle name

    def send_request(self):  # Method to invoke async service call
        return self.cli.call_async(self.req)  # Return future for the call


def main(argv=None):  # Entrypoint for script
    parser = argparse.ArgumentParser(description='Spawn a turtle in turtlesim', add_help=True)  # Parser
    parser.add_argument('--x', type=float, default=5.0)      # x arg
    parser.add_argument('--y', type=float, default=5.0)      # y arg
    parser.add_argument('--theta', type=float, default=0.0)  # theta arg
    parser.add_argument('--name', type=str, default='turtle2')  # name arg
    # Separate our args from ROS args passed by launch  # Split args
    args, ros_args = parser.parse_known_args(argv)  # Known vs ROS args

    rclpy.init(args=ros_args)  # Initialize rclpy with ROS args
    node = SpawnClient(args.x, args.y, args.theta, args.name)  # Create client node
    future = node.send_request()  # Send request
    rclpy.spin_until_future_complete(node, future)  # Wait for result
    if future.result() is not None:  # If call succeeded
        node.get_logger().info(f"Spawned: {future.result().name}")  # Log success
    else:  # On failure
        node.get_logger().error(f"Service call failed: {future.exception()}")  # Log error
        rclpy.shutdown()  # Shutdown rclpy
        sys.exit(1)  # Exit with error code
    rclpy.shutdown()  # Clean shutdown


if __name__ == '__main__':  # Script executed directly
    main()  # Call main
