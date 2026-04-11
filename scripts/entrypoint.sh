#!/bin/bash
set -e

# Source ROS
source /opt/ros/humble/setup.bash

# Source workspace
source /workspace/install/setup.bash

echo "Starting robot nodes..."

# Run nodes
#ros2 run serial_bridge serial_bridge &
#ros2 run serial_bridge odometry_node &

# Keep container alive
wait
