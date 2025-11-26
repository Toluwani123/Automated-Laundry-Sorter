# servo.py
import time
import RPi.GPIO as GPIO
from config import (
    SERVO_PINS,
    SERVO_POSITIONS,
    STATE_SERVO_ORDER,
    PER_SERVO_DELAY,
    READ_STATE_EXTRA_DELAY,
)

PWM_FREQ = 50        # Standard hobby servo frequency
MIN_DC = 2.5         # ~0°
MAX_DC = 12.5        # ~180°


def angle_to_duty(angle):
    """Convert an angle (0–180) to duty cycle (2.5–12.5)."""
    angle = float(angle)
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    return MIN_DC + (angle / 180.0) * (MAX_DC - MIN_DC)


class ServoArm:
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.pwms = {}
        self.current_angles = {}

        # Initialize PWM for each servo
        for name, pin in SERVO_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, PWM_FREQ)
            pwm.start(0)           # start with no pulse
            self.pwms[name] = pwm
            self.current_angles[name] = 0.0  # assume starting at 0 for now

    def _move_single_servo_smooth(self, name, target_angle, duration=1.0, steps=60):
        """
        Smoothly move ONE servo from its current angle to target_angle
        over 'duration' seconds, in 'steps' increments.
        """
        pwm = self.pwms[name]
        start_angle = self.current_angles.get(name, 0.0)
        target_angle = float(target_angle)

        if steps < 1:
            steps = 1

        step_time = duration / steps
        delta = (target_angle - start_angle) / steps

        angle = start_angle
        for _ in range(steps):
            angle += delta
            duty = angle_to_duty(angle)
            pwm.ChangeDutyCycle(duty)
            time.sleep(step_time)

        # Final snap to exact target
        duty = angle_to_duty(target_angle)
        pwm.ChangeDutyCycle(duty)
        self.current_angles[name] = target_angle
        
        time.sleep(0.05)
        pwm.ChangeDutyCycle(0.0)

    def run_state(self, state_name, move_duration=1.0, steps=60):
        """
        Run ONE logical servo state:
        - Look up final angles in SERVO_POSITIONS[state_name]
        - Move servos in the order specified by STATE_SERVO_ORDER[state_name]
        - Each servo move is smooth, then wait PER_SERVO_DELAY before the next
        - If state is MOISTURE_READ or COLOR_READ, wait READ_STATE_EXTRA_DELAY
          AFTER all servo moves.
        """
        if state_name not in SERVO_POSITIONS:
            print(f"[WARN] Unknown servo state '{state_name}'")
            return

        pose = SERVO_POSITIONS[state_name]
        try:
            order = STATE_SERVO_ORDER[state_name]
        except KeyError:
            # Fallback: if no explicit order, use dictionary order
            order = list(pose.keys())

        print(f"\n=== SERVO STATE: {state_name} ===")
        print(f"Target pose: {pose}")
        print(f"Servo order: {order}")

        # Move each servo in the defined order (one at a time)
        for servo_name in order:
            if servo_name not in pose:
                continue  # nothing defined for this servo in this state

            target_angle = pose[servo_name]
            print(f"  -> Moving {servo_name} to {target_angle}°")

            self._move_single_servo_smooth(
                servo_name,
                target_angle,
                duration=move_duration,
                steps=steps,
            )

            # 1s delay between servo movements
            time.sleep(PER_SERVO_DELAY)

        # Extra 5s delay after read states (before transitioning to next state)
        if state_name in ("MOISTURE_READ", "COLOR_READ"):
            print(f"  [HOLD] {state_name} – waiting {READ_STATE_EXTRA_DELAY} seconds...")
            time.sleep(READ_STATE_EXTRA_DELAY)

    def cleanup(self):
        for pwm in self.pwms.values():
            pwm.stop()
        GPIO.cleanup()
