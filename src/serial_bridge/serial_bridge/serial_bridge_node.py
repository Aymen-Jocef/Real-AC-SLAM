#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import serial, struct, time

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge')
        
        # 1) Open serial port
        self.ser = serial.Serial('/dev/ttyUSB0',921600, timeout=0.1)

        # 2) Create a subscriber to /cmd_vel
        self.latest_linear = 0.0
        self.latest_angular = 0.0
        self.create_subscription(
            Twist, '/robot1/cmd_vel', self.cmd_vel_cb, 10
        )

        # 3) Create publishers for left and right wheel RPM
        self.left_rpm_pub = self.create_publisher(Float64, '/robot1/left_wheel_rpm', 10)
        self.right_rpm_pub = self.create_publisher(Float64, '/robot1/right_wheel_rpm', 10)

        # 4) Timer at 20 Hz for send/receive
        self.send_hz = 20.0
        self.period = 1.0 / self.send_hz
        self.timer = self.create_timer(self.period, self.timer_cb)

        self.get_logger().info(f"Serial bridge running at {self.send_hz}Hz")

    def cmd_vel_cb(self, msg: Twist):
        """Store latest cmd_vel values for the next send."""
        self.latest_linear  = msg.linear.x
        self.latest_angular = msg.angular.z

    def timer_cb(self):
        cmd_packet = struct.pack('<ff', self.latest_linear, self.latest_angular)
        self.ser.write(cmd_packet)
        self.ser.flush()

        # 2) Wait for start byte
        header = self.ser.read(1)
        if header != b'\xAA':
            self.get_logger().warn("Invalid or missing start byte")
            return

        # 3) Read exactly 8 bytes for 2 floats
        data = self.ser.read(8)
        if len(data) != 8:
            self.get_logger().warn("Incomplete packet")
            return

        try:
            rpm_l, rpm_r = struct.unpack('<ff', data)

            # Sanity check
            if not all(map(lambda v: abs(v) < 10000 and v == v, [rpm_l, rpm_r])):
                self.get_logger().warn(f"Ignoring corrupted RPMs: L={rpm_l:.2f} R={rpm_r:.2f}")
                return

            #self.get_logger().info(f"L={rpm_l:7.2f} rpm | R={rpm_r:7.2f} rpm")
            self.left_rpm_pub.publish(Float64(data=rpm_l))
            self.right_rpm_pub.publish(Float64(data=rpm_r))

        except struct.error as e:
            self.get_logger().error(f"Failed to unpack RPM data: {e}")
    def destroy_node(self):
        """Clean up serial port on shutdown."""
        try:
            self.ser.close()
        except Exception:
            pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
