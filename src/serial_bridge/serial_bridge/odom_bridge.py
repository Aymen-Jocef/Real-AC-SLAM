#!/usr/bin/env python3

import socket
import struct
import time
import threading

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion
from tf_transformations import quaternion_from_euler

from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


HOST = "172.26.1.1"   # Robotino IP
PORT = 80

# ─────────────────────────────────────────────
# REAL REC PACKETS (FROM Robotino View)
# ─────────────────────────────────────────────
REC_79 = bytes.fromhex(
    "00 4c 00 00 00 90 1f 00 00 00 00 00 52 45 43 08"
    "01 02 00 00 00 00 00 ff ff ff 01 02 00 00 00 00"
    "00 ff ff ff 01 02 00 00 00 00 00 ff ff ff 01 02"
    "00 00 00 00 00 00 00 00 72 65 63 00 00 00 00 00"
    "00 00 00 00 00 00 00 00 00 00 80 3f 00 00 00"
)

REC_87 = bytes.fromhex(
    "02 05 00 00 00 00 00 00 00 4c 00 00 00 90 1f 00"
    "00 00 00 00 52 45 43 08 01 02 00 00 00 00 00 ff"
    "ff ff 01 02 00 00 00 00 00 ff ff ff 01 02 00 00"
    "00 00 00 ff ff ff 01 02 00 00 00 00 00 00 00 00"
    "72 65 63 00 00 00 00 00 00 00 00 00 00 00 00 00"
    "00 00 80 3f 00 00 00"
)

# ─────────────────────────────────────────────
# ODOMETRY OFFSETS
# ─────────────────────────────────────────────
OFF_PHI = 32
OFF_TS  = 36
OFF_X   = 125
OFF_Y   = 129

PACKET_MAGIC = b"\x01\x8d"
PACKET_SIZE  = 144


def parse(pkt):
    x = struct.unpack_from("<f", pkt, OFF_X)[0] / 1000.0
    y = struct.unpack_from("<f", pkt, OFF_Y)[0] / 1000.0
    phi = struct.unpack_from("<h", pkt, OFF_PHI)[0] / 1000.0
    ts = struct.unpack_from("<I", pkt, OFF_TS)[0]

    return x, y, phi, ts


class Robotino:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)

        self.buf = b""
        self._running = False
        self._keep_thread = None

    def connect(self):
        print("[*] Connecting to Robotino...")
        self.sock.connect((HOST, PORT))

        print("[*] Reading header...")
        header = b""

        while True:
            b1 = self.sock.recv(1)

            if not b1:
                raise RuntimeError("Connection closed")

            header += b1

            if header.endswith(b"\n\x00"):
                break

        print(f"[+] Header size: {len(header)}")

        print("[*] Sending REC packets...")
        self.sock.sendall(REC_79)
        time.sleep(0.05)
        self.sock.sendall(REC_87)

        self._running = True
        self._keep_thread = threading.Thread(
            target=self._keep_alive,
            daemon=True
        )
        self._keep_thread.start()

        print("[+] Stream started")

    def _keep_alive(self):
        while self._running:
            try:
                self.sock.sendall(REC_79)
                time.sleep(0.03)

                self.sock.sendall(REC_87)
                time.sleep(0.03)

            except Exception:
                break

    def recv(self):
        data = self.sock.recv(4096)

        if not data:
            raise RuntimeError("Connection lost")

        return data

    def get_packet(self):
        while PACKET_MAGIC not in self.buf:
            self.buf += self.recv()

        idx = self.buf.index(PACKET_MAGIC)
        self.buf = self.buf[idx:]

        while len(self.buf) < PACKET_SIZE:
            self.buf += self.recv()

        pkt = self.buf[:PACKET_SIZE]
        self.buf = self.buf[PACKET_SIZE:]

        return pkt

    def close(self):
        self._running = False

        if self._keep_thread:
            self._keep_thread.join(timeout=1)

        self.sock.close()


class RobotinoOdomBridge(Node):
    def __init__(self):
        super().__init__("robotino_odom_bridge")

        # Publisher for /odom
        self.odom_pub = self.create_publisher(
            Odometry,
            "/robot2/odom",
            10
        )

        # TF broadcaster for odom -> base_link
        self.tf_broadcaster = TransformBroadcaster(self)

        # Robotino connection
        self.robotino = Robotino()
        self.robotino.connect()

        self.get_logger().info(
            "Publishing /odom and broadcasting TF: odom -> base_link"
        )

        # Timer
        self.timer = self.create_timer(
            0.01,   # 100 Hz
            self.timer_callback
        )

    def create_quaternion(self, yaw):
        q = quaternion_from_euler(0.0, 0.0, yaw)

        quat = Quaternion()
        quat.x = q[0]
        quat.y = q[1]
        quat.z = q[2]
        quat.w = q[3]

        return quat

    def publish_tf(self, x, y, yaw):
        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"

        # Translation
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = 0.0

        # Rotation
        q = self.create_quaternion(yaw)
        t.transform.rotation = q

       # self.tf_broadcaster.sendTransform(t)

    def create_odom_msg(self, x, y, yaw):
        msg = Odometry()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"

        # Position
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0

        # Orientation
        msg.pose.pose.orientation = self.create_quaternion(yaw)

        return msg

    def timer_callback(self):
        try:
            pkt = self.robotino.get_packet()

            x, y, phi, ts = parse(pkt)

            # print(
            #     f"X={x:.3f}   "
            #     f"Y={y:.3f}   "
            #     f"Yaw={phi:.3f}   "
            #     f"TS={ts}"
            # )

            # Publish odometry
            odom_msg = self.create_odom_msg(x, y, phi)
            self.odom_pub.publish(odom_msg)

            # Broadcast TF
            self.publish_tf(x, y, phi)

        except Exception as e:
            self.get_logger().error(f"Error: {str(e)}")

    def destroy_node(self):
        self.robotino.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = RobotinoOdomBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()