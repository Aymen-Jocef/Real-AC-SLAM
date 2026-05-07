#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from gpiozero import PWMOutputDevice

# Condition PWM values for direction signaling to Robotino
PWM_COND_FORWARD = 0.1
PWM_COND_REVERSE = 0.9
PWM_COND_STOP    = 0.0   

class CmdVelToPWM(Node):

    def __init__(self):
        super().__init__("cmd_vel_to_pwm")

        # PWM outputs
        self.pwm_vx       = PWMOutputDevice(pin=12, frequency=10000)
        self.pwm_vx_cond  = PWMOutputDevice(pin=13, frequency=10000)
        self.pwm_vy       = PWMOutputDevice(pin=18, frequency=10000)
        self.pwm_vy_cond  = PWMOutputDevice(pin=19, frequency=10000)
        self.pwm_ang      = PWMOutputDevice(pin=20, frequency=10000)
        self.pwm_ang_cond = PWMOutputDevice(pin=21, frequency=10000)

        self.subscription = self.create_subscription(
            Twist, "/robot2/cmd_vel", self.cmd_vel_callback, 10
        )

        # prints at most once per second
        self._last_log = self.get_clock().now()

        self.get_logger().info("CmdVel to PWM node started. Subscribed to /robot2/cmd_vel")

    @staticmethod
    def vel_to_pwm(value):
        return max(0.0, min(1.0, abs(value)))

    @staticmethod
    def cond(value):
        if value > 0.0:
            return PWM_COND_FORWARD
        elif value < 0.0:
            return PWM_COND_REVERSE
        else:
            return PWM_COND_STOP

    def cmd_vel_callback(self, msg: Twist):
        vx  = msg.linear.x
        vy  = msg.linear.y
        ang = msg.angular.z

        # Each axis is independent 
        self.pwm_vx.value       = self.vel_to_pwm(vx)
        self.pwm_vx_cond.value  = self.cond(vx)

        self.pwm_vy.value       = self.vel_to_pwm(vy)
        self.pwm_vy_cond.value  = self.cond(vy)

        self.pwm_ang.value      = self.vel_to_pwm(ang)
        self.pwm_ang_cond.value = self.cond(ang)

        # Log at most once per second to avoid flooding
        now = self.get_clock().now()
        if (now - self._last_log).nanoseconds >= 1_000_000_000:
            self._last_log = now
            self.get_logger().info(
                f"vx={vx:.3f} (pwm={self.pwm_vx.value:.2f} cond={self.pwm_vx_cond.value:.1f}) | "
                f"vy={vy:.3f} (pwm={self.pwm_vy.value:.2f} cond={self.pwm_vy_cond.value:.1f}) | "
                f"ang={ang:.3f} (pwm={self.pwm_ang.value:.2f} cond={self.pwm_ang_cond.value:.1f})"
            )

    def destroy_node(self):
        # Set all outputs to safe stop state then release GPIO resources
        for dev in (
            self.pwm_vx, self.pwm_vx_cond,
            self.pwm_vy, self.pwm_vy_cond,
            self.pwm_ang, self.pwm_ang_cond,
        ):
            dev.off()
            dev.close()  
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToPWM()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()


