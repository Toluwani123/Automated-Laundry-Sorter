import RPi.GPIO as GPIO
import time

# === SERVO CONFIG ===
PWM_FREQ = 50
MIN_DC = 2.5
MAX_DC = 12.5

SERVO_PINS = {
    "S1": 17,
    "S2": 27,
    "S3": 22,
    "S4": 5
}

def angle_to_duty(angle):
    """Convert angle (0–180) to duty cycle (2.5–12.5%)."""
    return MIN_DC + (angle / 180.0) * (MAX_DC - MIN_DC)

def set_angle(pwm, angle):
    """Instant servo move."""
    pwm.ChangeDutyCycle(angle_to_duty(angle))

# === SETUP ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pwms = {}
for name, pin in SERVO_PINS.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, PWM_FREQ)
    pwm.start(0)
    pwms[name] = pwm

time.sleep(0.5)

try:
    # ======== SEQUENCE STARTS HERE ========

    # S1 starts at 0°
    set_angle(pwms["S1"], 0)
    time.sleep(1)

    # S3 → 120°
    set_angle(pwms["S3"], 120)
    time.sleep(1)

    # S2 → 20°
    set_angle(pwms["S2"], 20)
    time.sleep(1)

    # S4 → 120°
    set_angle(pwms["S4"], 120)
    time.sleep(1)

    # S4 → 0°
    set_angle(pwms["S4"], 0)
    time.sleep(1)

    # S2 → 0°
    set_angle(pwms["S2"], 0)
    time.sleep(1)

    # S3 → 60°
    set_angle(pwms["S3"], 60)
    time.sleep(1)

    # S1 → 40°
    set_angle(pwms["S1"], 40)
    time.sleep(1)

    # S2 → 40°
    set_angle(pwms["S2"], 40)
    time.sleep(1)

    # S2 → 60°
    set_angle(pwms["S2"], 60)
    time.sleep(1)

    # wait 5 seconds
    time.sleep(5)

    # S1 → 140°
    set_angle(pwms["S1"], 140)
    time.sleep(1)

    # S3 → 120°
    set_angle(pwms["S3"], 120)
    time.sleep(1)

    # S2 → 20°
    set_angle(pwms["S2"], 20)
    time.sleep(1)

    # S4 → 120°
    set_angle(pwms["S4"], 120)
    time.sleep(1)

    # ======== END OF SEQUENCE ========

finally:
    # cleanup
    for pwm in pwms.values():
        pwm.ChangeDutyCycle(0)
        pwm.stop()
    GPIO.cleanup()
