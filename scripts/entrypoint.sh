#!/bin/bash
set -e

# ==============================
# Source ROS environments
# ==============================
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash

echo "=============================="
echo " Starting robot nodes..."
echo "=============================="

# ==============================
# Function to start node safely
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
        echo "[ERROR] $name failed to start"
        echo "---- LOG ($name) ----"
        cat /tmp/${name}.log
        exit 1
    fi
}

# ==============================
# Start nodes one by one
# ==============================

# 1. Serial bridge (STM32 comm)
start_node "serial_bridge" \
"ros2 run serial_bridge serial_bridge"

# 2. Odometry node
start_node "odometry" \
"ros2 run serial_bridge odometry"

# 3. IMU node 
start_node "imu_node" \
"ros2 launch ros2_mpu6050 ros2_mpu6050.launch.py"

# 4. Madgwick filter
start_node "madgwick" \
"ros2 run imu_filter_madgwick imu_filter_madgwick_node \
--ros-args \
--remap imu/data_raw:=/imu/mpu6050 \
-p use_mag:=false"

echo "=============================="
echo " All nodes started successfully"
echo "=============================="

# ==============================
# Show logs (live)
# ==============================
tail -f /tmp/*.log
