#!/bin/bash
set -e

# ==============================
# Source ROS
# ==============================
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash

echo "=============================="
echo " Starting robot nodes..."
echo "=============================="

# ==============================
# Function to start node
# ==============================
start_node() {
    name=$1
    cmd=$2

    echo "[STARTING] $name"
    bash -c "$cmd" > /tmp/${name}.log 2>&1 &

    pid=$!
    sleep 2

    if ps -p $pid > /dev/null
    then
        echo "[OK] $name started (PID $pid)"
    else
        echo "[ERROR] $name failed"
        cat /tmp/${name}.log
        exit 1
    fi
}

# ==============================
# Start TF static transforms FIRST
# ==============================

start_node "tf_base" \
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_footprint base_link"

start_node "tf_imu" \
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link imu_link"

start_node "tf_laser" \
"ros2 run tf2_ros static_transform_publisher 0.1 0 0 0 0 0 base_link laser"

# ==============================
# Start core nodes
# ==============================

start_node "serial_bridge" \
"ros2 run serial_bridge serial_bridge"

start_node "odometry" \
"ros2 run serial_bridge odometry"

start_node "imu_node" \
"ros2 launch ros2_mpu6050 ros2_mpu6050.launch.py"

start_node "madgwick" \
"ros2 run imu_filter_madgwick imu_filter_madgwick_node \
--ros-args \
--remap imu/data_raw:=/robot1/imu/mpu6050 \
--remap imu/data:=/robot1/imu_filtered \
-p use_mag:=false \
-p publish_tf:=false" 

start_node "ekf" \
"ros2 launch robot_loc ekf.launch.py"

echo "=============================="
echo " All nodes started successfully"
echo "=============================="

# ==============================
# Show logs live
# ==============================
tail -f /tmp/*.log
