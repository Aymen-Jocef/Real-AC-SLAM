#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import serial, struct, time

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge')
        
        # 1) Open serial port with optimized timeout for high baud rate
        self.ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0.01)

        # 2) Create a subscriber to /cmd_vel
        self.latest_linear = 0.0
        self.latest_angular = 0.0
        self.create_subscription(
            Twist, '/robot1/cmd_vel', self.cmd_vel_cb, 10
        )

        # 3) Create publishers for left and right wheel RPM
        self.left_rpm_pub = self.create_publisher(Float64, '/robot1/left_wheel_rpm', 10)
        self.right_rpm_pub = self.create_publisher(Float64, '/robot1/right_wheel_rpm', 10)

        # 4) Initialize receive buffer for packet assembly
        self.rx_buffer = b''

        # 5) Timer at 20 Hz for send/receive
        self.send_hz = 20.0
        self.period = 1.0 / self.send_hz
        self.timer = self.create_timer(self.period, self.timer_cb)

        self.get_logger().info(f"Serial bridge running at {self.send_hz}Hz")

    def cmd_vel_cb(self, msg: Twist):
        """Store latest cmd_vel values for the next send."""
        self.latest_linear  = msg.linear.x
        self.latest_angular = msg.angular.z

    def timer_cb(self):
        try:
            # Send command packet
            try:
                cmd_packet = struct.pack('<ff', self.latest_linear, self.latest_angular)
                self.ser.write(cmd_packet)
                self.ser.flush()
                self.get_logger().debug(f"[SEND] cmd_vel: linear={self.latest_linear:.3f}, angular={self.latest_angular:.3f}")
            except serial.SerialException as e:
                self.get_logger().error(f"Serial write error: {e}")
                return
            except Exception as e:
                self.get_logger().error(f"Unexpected error during write: {e}")
                return

            # Read all available bytes
            try:
                bytes_available = self.ser.in_waiting
                if bytes_available > 0:
                    data = self.ser.read(bytes_available)
                    self.rx_buffer += data
                    self.get_logger().debug(f"[READ] Received {bytes_available} bytes, buffer size: {len(self.rx_buffer)}")
                else:
                    self.get_logger().debug(f"[READ] No data available, buffer size: {len(self.rx_buffer)}")
            except serial.SerialException as e:
                self.get_logger().error(f"Serial read error: {e}")
                return
            except Exception as e:
                self.get_logger().error(f"Unexpected error during read: {e}")
                return

            # Process packets
            packet_count = 0
            while True:
                # Look for start byte
                start = self.rx_buffer.find(b'\xAA')
                if start == -1:
                    # No start byte found - keep buffer and wait for more data
                    self.get_logger().debug(f"[PROCESS] No start byte, buffer: {len(self.rx_buffer)} bytes")
                    if len(self.rx_buffer) > 100:
                        # Buffer is filling with garbage, discard it
                        self.get_logger().warn(f"[PROCESS] Buffer overflow, clearing ({len(self.rx_buffer)} bytes). First 20 bytes: {self.rx_buffer[:20].hex()}")
                        self.rx_buffer = b''
                    return

                # Remove junk before start byte
                if start > 0:
                    self.get_logger().warn(f"[PROCESS] Found {start} junk bytes before start byte, discarding")
                    self.rx_buffer = self.rx_buffer[start:]

                # Check if full packet is available
                if len(self.rx_buffer) < 9:  # 1 + 8 bytes
                    self.get_logger().debug(f"[PROCESS] Incomplete packet: {len(self.rx_buffer)}/9 bytes")
                    return

                # Extract packet
                packet = self.rx_buffer[1:9]
                self.rx_buffer = self.rx_buffer[9:]
                packet_count += 1

                try:
                    rpm_l, rpm_r = struct.unpack('<ff', packet)
                    self.get_logger().debug(f"[PACKET {packet_count}] Unpacked: L={rpm_l:.2f} rpm, R={rpm_r:.2f} rpm")

                    if abs(rpm_l) < 10000 and abs(rpm_r) < 10000:
                        self.left_rpm_pub.publish(Float64(data=rpm_l))
                        self.right_rpm_pub.publish(Float64(data=rpm_r))
                      #  self.get_logger().info(f"[PUBLISH] Left={rpm_l:7.2f} rpm | Right={rpm_r:7.2f} rpm")
                    else:
                        self.get_logger().warn(f"[PACKET {packet_count}] RPM out of range: L={rpm_l:.2f}, R={rpm_r:.2f}")

                except struct.error as e:
                    self.get_logger().error(f"[PACKET {packet_count}] Failed to unpack: {packet.hex()}, error: {e}")
                    continue

        except Exception as e:
            self.get_logger().error(f"Fatal error in timer_cb: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())

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
