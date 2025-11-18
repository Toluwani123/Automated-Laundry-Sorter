# servo.py
import time
import RPi.GPIO as GPIO
from config import SERVO_PINS, SERVO_POSITIONS

# === SERVO CONFIG ===
PWM_FREQ = 50        # Standard hobby servo frequency
MIN_DC = 2.5         # ~0°
MAX_DC = 12.5        # ~180°


def angle_to_duty(angle):
    """
    Convert an angle (0–180) to duty cycle (2.5–12.5),
    same mapping as your working single-servo script.
    """
    angle = float(angle)
    # clamp to 0–180
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    return MIN_DC + (angle / 180.0) * (MAX_DC - MIN_DC)


class ServoArm:
    def __init__(self):
        """
        Initialize GPIO and PWM channels for each joint:
        SERVO_PINS = { "Bottom": pin, "Elbow": pin, ... }
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.pwms = {}
        self.current_angles = {}

        # Setup each servo pin and start PWM at 0% duty
        for joint, pin in SERVO_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, PWM_FREQ)
            pwm.start(0)  # 0% duty (no pulse)
            self.pwms[joint] = pwm
            self.current_angles[joint] = 0.0
         

        time.sleep(0.5)

       
    # ----- LOW LEVEL: set one joint angle -----

    def _set_servo_angle(self, joint, angle, wait=0.0):
        """
        Internal helper: directly set a single joint to an angle.
        """
        angle = float(angle)
        duty = angle_to_duty(angle)
        pwm = self.pwms[joint]
        pwm.ChangeDutyCycle(duty)
        self.current_angles[joint] = angle
        if wait > 0:
            time.sleep(wait)

    # ----- PUBLIC: single-joint helpers (for testing) -----

    def move_joint_instant(self, joint, angle, wait=0.5):
        """
        Move one joint to 'angle' and wait a bit.
        Then set duty to 0 to reduce jitter.
        """
        self._set_servo_angle(joint, angle, wait=wait)
        # stop sending pulses (many servos prefer this to avoid buzzing)
        self.pwms[joint].ChangeDutyCycle(0)

    def smooth_move_joint(self, joint, start, end, steps=50, delay=0.02):
        """
        Smoothly move one joint from 'start' to 'end' in small steps,
        using the same idea as your smooth_move(pwm, start, end, ...) function.
        """
        start = float(start)
        end = float(end)
        steps = max(1, int(steps))

        # Decide direction
        if start < end:
            rng = range(int(start), int(end) + 1)
        else:
            rng = range(int(start), int(end) - 1, -1)

        pwm = self.pwms[joint]
        for angle in rng:
            duty = angle_to_duty(angle)
            pwm.ChangeDutyCycle(duty)
            self.current_angles[joint] = float(angle)
            time.sleep(delay)

        # relax servo
        pwm.ChangeDutyCycle(0)

    # ----- PUBLIC: multi-joint pose move -----

    def move_to(self, pose_name, duration=1.0, steps=50):
        """
        Smoothly move *all* joints to the angles defined in SERVO_POSITIONS[pose_name].
        - duration: total time for the move (seconds)
        - steps: number of interpolation steps
        """
        if pose_name not in SERVO_POSITIONS:
            raise ValueError(f"Unknown servo pose: {pose_name}")

        target_angles = SERVO_POSITIONS[pose_name]
        steps = max(1, int(steps))
        step_delay = max(0.0, float(duration)) / steps

        # Ensure we have starting angles stored for all joints
        for joint in SERVO_PINS.keys():
            if joint not in self.current_angles:
                self.current_angles[joint] = 90.0

        # Take a snapshot of starting angles so interpolation is smooth
        start_angles = dict(self.current_angles)

        # Interpolate like your smooth_move, but for all joints together
        for i in range(steps + 1):
            t = i / steps  # goes 0.0 → 1.0
            for joint, pin in SERVO_PINS.items():
                if joint not in target_angles:
                    # If pose didn't specify this joint, keep it where it is
                    continue

                start = float(start_angles[joint])
                end = float(target_angles[joint])
                angle = start + (end - start) * t

                duty = angle_to_duty(angle)
                pwm = self.pwms[joint]
                pwm.ChangeDutyCycle(duty)
                self.current_angles[joint] = angle

            time.sleep(step_delay)

        # After finishing, set duty to 0 on all servos to reduce humming
        for pwm in self.pwms.values():
            pwm.ChangeDutyCycle(0)

    # ----- CLEANUP -----

    def cleanup(self):
        """
        Stop all PWM channels and clean up GPIO.
        Call this from your main program's finally block.
        """
        for pwm in self.pwms.values():
            pwm.ChangeDutyCycle(0)
            pwm.stop()
        GPIO.cleanup()


# Optional: standalone quick test
if __name__ == "__main__":
    arm = ServoArm()
    try:
        # Adjust these to match your SERVO_POSITIONS keys
        test_poses = ["IDLE"]
        for name in test_poses:
            print(f"Moving to pose: {name}")
            arm.move_to(name, duration=1.5, steps=50)
            time.sleep(1.0)
    finally:
        arm.cleanup()
