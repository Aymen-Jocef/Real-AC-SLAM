#!/bin/bash
set -e

source /opt/ros/humble/setup.bash
colcon build --packages-select robot_nav
source /workspace/install/setup.bash


echo "=============================="
echo " Starting robot nodes..."
echo "=============================="

start_node() {
    name=$1
    cmd=$2

    # Only append tf remappings to `ros2 run` commands (skip `ros2 launch`),
    # and skip commands referencing excluded package directories.
    if [[ "$cmd" == ros2\ run* && "$cmd" != *"multi-agent-system-AC-SLAM"* && "$cmd" != *"cpp_explorer"* ]]; then
        if [[ "$cmd" == *"--ros-args"* ]]; then
            cmd="$cmd"
        else
            cmd="$cmd --ros-args"
        fi
    fi

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
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 robot1/base_footprint robot1/base_link --ros-args"

start_node "tf_imu" \
"ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 robot1/base_link robot1/imu_link --ros-args"

start_node "tf_laser" \
"ros2 run tf2_ros static_transform_publisher 0.1 0 0 0 0 0 robot1/base_link robot1/laser --ros-args"

# start_node "tf_world" \
# "ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 world robot1/map --ros-args"
# ==============================
# CORE NODES
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

 start_node "rplidar" \
 "ros2 launch rplidar_ros rplidar_a2m12_launch.py"

start_node "SLAM" \
"ros2 launch robot_loc online_async.launch.py"

 start_node "nav" \
 "ros2 launch robot_nav navigation_launch.py use_sim_time:=false namespace:=robot1"

#  sleep 5

# start_node "explorer" \
# "ros2 launch cpp_explorer cpp_explorer.launch.py namespace:=robot1"

echo "=============================="
echo " All nodes started successfully"
echo "=============================="

tail -f /tmp/*.log
