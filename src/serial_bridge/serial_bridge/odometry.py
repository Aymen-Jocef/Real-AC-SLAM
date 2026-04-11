import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion, TransformStamped
import tf_transformations
import tf2_ros
import math

class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')

        # Robot parameters
        self.wheel_radius = 0.0335  # in meters
        self.wheel_base = 0.325    # distance between wheels in meters

        self.left_rpm = 0.0
        self.right_rpm = 0.0
        self.last_time = self.get_clock().now()

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.create_subscription(Float64, '/robot1/left_wheel_rpm', self.left_rpm_callback, 10)
        self.create_subscription(Float64, '/robot1/right_wheel_rpm', self.right_rpm_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/robot1/odom', 10)

        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.create_timer(0.05, self.update_odometry)  # 20Hz

    def left_rpm_callback(self, msg):
        self.left_rpm = msg.data

    def right_rpm_callback(self, msg):
        self.right_rpm = msg.data

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        # Convert RPM to m/s
        left_vel = (self.left_rpm * 2 * math.pi / 60) * self.wheel_radius
        right_vel = (self.right_rpm * 2 * math.pi / 60) * self.wheel_radius

        # Compute linear and angular velocity
        vx = (right_vel + left_vel) / 2.0
        vth = (right_vel - left_vel) / self.wheel_base

        delta_x = vx * math.cos(self.theta) * dt
        delta_y = vx * math.sin(self.theta) * dt
        delta_theta = vth * dt

        self.x += delta_x
        self.y += delta_y
        self.theta += delta_theta

        # Print odometry values
   #     self.get_logger().info(
   #         f"[ODOM] x: {self.x:.3f}, y: {self.y:.3f}, theta: {self.theta:.3f}, vx: {vx:.3f}, vth: {vth:.3f}"
   #     )

        # Create quaternion from yaw
        quat = tf_transformations.quaternion_from_euler(0, 0, self.theta)

        # Publish transform
        odom_trans = TransformStamped()
        odom_trans.header.stamp = current_time.to_msg()
        odom_trans.header.frame_id = 'odom'
        odom_trans.child_frame_id = 'base_footprint'
        odom_trans.transform.translation.x = self.x
        odom_trans.transform.translation.y = self.y
        odom_trans.transform.translation.z = 0.0
        odom_trans.transform.rotation = Quaternion(x=quat[0], y=quat[1], z=quat[2], w=quat[3])
#        self.tf_broadcaster.sendTransform(odom_trans)

        # Publish odometry
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_footprint'
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation = Quaternion(x=quat[0], y=quat[1], z=quat[2], w=quat[3])
        odom_msg.twist.twist.linear.x = vx
        odom_msg.twist.twist.angular.z = vth
        self.odom_pub.publish(odom_msg)

def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

