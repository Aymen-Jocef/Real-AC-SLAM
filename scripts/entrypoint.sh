#!/bin/bash
set -e

source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash

echo "=============================="
echo " Starting robot nodes..."
echo "=============================="

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
# TF STATIC (namespaced)
# ==============================

start_node "tf_base" \
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_footprint base_link --ros-args --remap __ns:=/robot2"

start_node "tf_imu" \
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link imu_link --ros-args --remap __ns:=/robot2"

start_node "tf_laser" \
"ros2 run tf2_ros static_transform_publisher 0.1 0 0 0 0 0 base_link laser --ros-args --remap __ns:=/robot2"

# ==============================
# CORE NODES
# ==============================

start_node "serial_bridge" \
"ros2 run serial_bridge robotino_bridge"

start_node "odometry" \
"ros2 run serial_bridge odom_bridge"

start_node "imu_node" \
"ros2 launch ros2_mpu6050 ros2_mpu6050.launch.py"

start_node "madgwick" \
"ros2 run imu_filter_madgwick imu_filter_madgwick_node \
--ros-args \
--remap imu/data_raw:=/robot2/imu/mpu6050 \
--remap imu/data:=/robot2/imu_filtered \
-p use_mag:=false \
-p publish_tf:=false"

start_node "ekf" \
"ros2 launch robot_loc ekf.launch.py"

start_node "rplidar" \
"ros2 launch rplidar_ros rplidar_a2m12_launch.py"

start_node "SLAM" \
"ros2 launch robot_loc online_async.launch.py"

echo "=============================="
echo " All nodes started successfully"
echo "=============================="

tail -f /tmp/*.log
