FROM ros:humble

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install useful tools
RUN apt-get update && apt-get install -y --no-install-recommends \
  # Build tools
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ca-certificates \
    gnupg2 \
    lsb-release \
    # Python development
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    # ROS2 development tools
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    # USB device access
    usbutils \
    # Network diagnostics
    net-tools \
    iputils-ping \
    iproute2 \
    # Text editors (development)
    vim \
    nano \
    # Process management
    htop \
    tmux \
    # Hardware interface libraries
    libi2c-dev \
    libusb-1.0-0-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* 
   
    
# Install ROS2 packages required for industrial mobile robot
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core ROS2 tools
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    
    \
    # TF2 (required for localization)
    ros-humble-tf2-ros \
    ros-humble-tf2-tools \
    ros-humble-tf2-geometry-msgs \
    \
    # ros2_control (motor control stack)
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-controller-manager \
    ros-humble-diff-drive-controller \
    ros-humble-joint-state-broadcaster \
    \
    # Navigation (Nav2)
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    \
    # SLAM
    ros-humble-slam-toolbox \
    \
    # Localization (robot_localization for EKF)
    ros-humble-robot-localization \
    \
    # Teleop
    ros-humble-teleop-twist-keyboard \
    \
    # Sensors
    ros-humble-laser-filters \
    ros-humble-laser-geometry \
    \
    # Diagnostics
    ros-humble-diagnostic-updater \
    ros-humble-diagnostic-aggregator \
    \
    # fastrtps 
    ros-humble-rmw-fastrtps-cpp \
    \
    # ROSBridge Suite
    ros-humble-rosbridge-suite \
    \
    # TF Transformations
    ros-humble-tf-transformations \
    \
    # IMU Filter Madgwick
    ros-humble-imu-filter-madgwick \
    \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Set CycloneDDS as default DDS implementation
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# CycloneDDS configuration will be mounted at runtime
ENV CYCLONEDDS_URI=file:///workspace/docker/cyclonedds.xml

# Create non-root user for security
# UID/GID 1000 matches most Linux host users
ARG USERNAME=ac-slam
ARG USER_UID=1000
ARG USER_GID=$USER_UID
# Create user and group (handle existing GID gracefully)
RUN set -e; \
    # Get or create group
    if getent group $USER_GID > /dev/null 2>&1; then \
        EXISTING_GROUP=$(getent group $USER_GID | cut -d: -f1); \
        echo "Group GID $USER_GID already exists as '$EXISTING_GROUP'"; \
        GROUPNAME=$EXISTING_GROUP; \
    else \
        groupadd --gid $USER_GID $USERNAME; \
        GROUPNAME=$USERNAME; \
    fi; \
    # Create or modify user
    if getent passwd $USER_UID > /dev/null 2>&1; then \
        EXISTING_USER=$(getent passwd $USER_UID | cut -d: -f1); \
        echo "User UID $USER_UID already exists as '$EXISTING_USER', renaming to '$USERNAME'"; \
        usermod -l $USERNAME -d /home/$USERNAME -m $EXISTING_USER; \
    else \
        useradd --uid $USER_UID --gid $USER_GID -m $USERNAME; \
    fi; \
    # Create video and render groups if they don't exist
    groupadd -f video; \
    groupadd -f render; \
    # Add user to dialout group for serial/USB access (STM32 flashing)
    usermod -aG dialout $USERNAME || true; \
    # Add user to video and render groups for GPU access
    usermod -aG video $USERNAME || true; \
    usermod -aG render $USERNAME || true; \
    # Setup sudo
    apt-get update && \
    apt-get install -y sudo && \
    echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    rm -rf /var/lib/apt/lists/*

# Create workspace directory and set ownership using UID:GID
RUN mkdir -p /workspace/src \
    && chown -R $USER_UID:$USER_GID /workspace


RUN pip3 install --no-cache-dir  \
    numpy \
    scipy \
    pyyaml \
    transforms3d \
    pyserial

# Copy entrypoint and setup scripts with correct ownership
COPY --chown=$USER_UID:$USER_GID docker/entrypoint.sh /entrypoint.sh


# Configure ROS2 environment in bashrc for interactive shells
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp" >> /home/$USERNAME/.bashrc \
    && echo "export CYCLONEDDS_URI=file:///workspace/docker/cyclonedds.xml" >> /home/$USERNAME/.bashrc

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER $USERNAME

# Expose common ROS2 ports (informational - host network mode bypasses this)
# DDS Discovery: 7400-7499
# DDS Data: 7600-7699
EXPOSE 7400-7499/udp
EXPOSE 7600-7699/udp

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (will be overridden by docker-compose)
CMD ["bash"]

