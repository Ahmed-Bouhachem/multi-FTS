#!/usr/bin/env python3
"""
Small helper to call turtlesim's /spawn service with arguments.
"""
import argparse
import sys

import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn


class SpawnClient(Node):
    def __init__(self, x: float, y: float, theta: float, name: str):
        super().__init__('spawn_client')
        self.cli = self.create_client(Spawn, '/spawn')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /spawn service...')
        self.req = Spawn.Request()
        self.req.x = float(x)
        self.req.y = float(y)
        self.req.theta = float(theta)
        self.req.name = name

    def send_request(self):
        return self.cli.call_async(self.req)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Spawn a turtle in turtlesim', add_help=True)
    parser.add_argument('--x', type=float, default=5.0)
    parser.add_argument('--y', type=float, default=5.0)
    parser.add_argument('--theta', type=float, default=0.0)
    parser.add_argument('--name', type=str, default='turtle2')
    # Separate our args from ROS args passed by launch
    args, ros_args = parser.parse_known_args(argv)

    rclpy.init(args=ros_args)
    node = SpawnClient(args.x, args.y, args.theta, args.name)
    future = node.send_request()
    rclpy.spin_until_future_complete(node, future)
    if future.result() is not None:
        node.get_logger().info(f"Spawned: {future.result().name}")
    else:
        node.get_logger().error(f"Service call failed: {future.exception()}")
        rclpy.shutdown()
        sys.exit(1)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
