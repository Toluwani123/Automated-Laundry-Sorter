import RPi.GPIO as GPIO
import time

# === SERVO CONFIG ===
PWM_FREQ = 5 
MIN_DC = 2.5
MAX_DC = 12.5

SERVO_PINS = {
    "S1": 17,  # GPIO 17
    "S2": 27,  # GPIO 27
    "S3": 22,  # GPIO 22
    "S4": 5    # GPIO 5
}

def angle_to_duty(angle):
    """Convert angle (0–180) to duty cycle (2.5–12.5%)."""
    return MIN_DC + (angle / 180.0) * (MAX_DC - MIN_DC)

def smooth_move_to(pwms, current_angles, name, target_angle, duration=1.5, steps=75):
    """
    Smoothly move one servo from its current angle to target_angle.
    duration: total time for the move (seconds)
    steps: how many tiny steps to break it into (higher = smoother)
    """
    start_angle = current_angles[name]
    delta = target_angle - start_angle
    if steps <= 0:
        steps = 1
    step_angle = delta / float(steps)
    step_delay = duration / float(steps)

    for i in range(steps + 1):
        angle = start_angle + step_angle * i
        pwms[name].ChangeDutyCycle(angle_to_duty(angle))
        time.sleep(step_delay)

    current_angles[name] = target_angle


# === SETUP ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pwms = {}
current_angles = {}

for name, pin in SERVO_PINS.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, PWM_FREQ)
    pwm.start(0)
    pwms[name] = pwm
    current_angles[name] = 0  # start all at 0° logically

time.sleep(0.5)

'''# Move all servos physically to 0° slowly at the start (optional)
for name in SERVO_PINS.keys():
    smooth_move_to(pwms, current_angles, name, 0, duration=2.5, steps=100)
time.sleep(0.5)'''

try:
    # ======== SEQUENCE WITH SMOOTH MOTION ========

    # S1 starts at 0° (we are already at 0, but we keep the step for clarity)
    smooth_move_to(pwms, current_angles, "S1", 0)
    time.sleep(1)

    # S3 -> 120°
    smooth_move_to(pwms, current_angles, "S3", 80)
    time.sleep(1)

    # S2 -> 20°
    smooth_move_to(pwms, current_angles, "S2",30)
    time.sleep(1)

    # S4 -> 120°
    smooth_move_to(pwms, current_angles, "S4",0)
    time.sleep(1)

    # S4 -> 0°
    smooth_move_to(pwms, current_angles, "S4", 0)
    time.sleep(1)

    # S2 -> 0°
    smooth_move_to(pwms, current_angles, "S3", 80)
    time.sleep(1)

    # S3 -> 60°
    smooth_move_to(pwms, current_angles, "S2", 0)
    time.sleep(1)

    # S1 -> 40°
    smooth_move_to(pwms, current_angles, "S1", 90)
    time.sleep(1)

    '''# S2 -> 40°
    smooth_move_to(pwms, current_angles, "S2", 0)
    time.sleep(1)

    # S2 -> 60°
    smooth_move_to(pwms, current_angles, "S2", 0)
    time.sleep(1)

    # wait 5 seconds
    time.sleep(5)

    # S1 -> 140°
    smooth_move_to(pwms, current_angles, "S1", 140,duration= 2.5,steps=80)
    time.sleep(1)

    # S3 -> 120°
    smooth_move_to(pwms, current_angles, "S3", 120)
    time.sleep(1)

    # S2 -> 20°
    smooth_move_to(pwms, current_angles, "S2", 20)
    time.sleep(1)

    # S4 -> 120°
    smooth_move_to(pwms, current_angles, "S4", 120)
    time.sleep(1)'''

    # ======== END OF SEQUENCE ========

finally:
    for pwm in pwms.values():
        pwm.ChangeDutyCycle(0)
        pwm.stop()
    GPIO.cleanup()
