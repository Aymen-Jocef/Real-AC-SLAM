# Real-AC-SLAM
**Real-AC-SLAM** is the real-world implementation of the **Autonomous Collaborative SLAM (AC-SLAM)** project. It provides a complete ROS 2 software stack for autonomous exploration, navigation, localization, and collaborative mapping using multiple mobile robots. The platform supports both a custom differential-drive robot and the Robotino omnidirectional robot, enabling robots to independently explore unknown environments while collaboratively building a shared global occupancy map.

## Robotino 2.1

This branch contains the implementation of the collaborative SLAM framework adapted to the Robotino omnidirectional mobile robot.

The system enables autonomous exploration, SLAM, navigation, and collaborative map generation using multiple Robotino platforms.

---

# Features

- ROS 2 Humble
- Autonomous exploration
- Nav2
- SLAM Toolbox
- Collaborative SLAM
- Occupancy grid map merging
- Real robot deployment

---

# Hardware

- Robotino 2.1 
- Raspberry pi 4
- RPLidar A2

Integrated

- Omnidirectional drive
- Odometry
- Embedded computer

---

# Requirements

Ubuntu 22.04

ROS 2 Humble

Install

- Docker
- Docker compose

---

# Installation

Clone

```bash
git clone -b robotino_v2 https://github.com/Aymen-Jocef/Real-AC-SLAM
```

Build

```bash
cd ~/Real-AC-SLAM

colcon build 

source install/setup.bash
```

---

# Launch Sequence

## Bringup

```bash
Docker compose build
```

```bash
Docker compose up
```
---
# Contributors

| | |
|:---:|:---:|
| <a href="https://github.com/TheHiCore"><img src="https://github.com/TheHiCore.png" width="100"/><br><b>TheHiCore</b></a> | <a href="https://github.com/Aymen-Jocef"><img src="https://github.com/Aymen-Jocef.png" width="100"/><br><b>Aymen Jocef</b></a> |

---
# Related Repositories

| Repository | Description |
|------------|-------------|
| [Platform-AC-SLAM](https://github.com/TheHiCore/Platform-AC-SLAM) | Hardware platform to visualize the map generation on the borwser. |
