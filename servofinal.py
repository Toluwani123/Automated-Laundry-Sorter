import RPi.GPIO as GPIO
import time

# === CONFIG ===
SERVO_PIN = 22
PWM_FREQ = 50        # Standard servo frequency (50 Hz)
MIN_DC = 2.5         # duty cycle for ~0°
MID_DC = 7.5         # duty cycle for ~90°
MAX_DC = 12.5        # duty cycle for ~180°

def angle_to_duty(angle):
    """Convert an angle (0–180) to duty cycle (2.5–12.5)."""
    return MIN_DC + (angle / 180.0) * (MAX_DC - MIN_DC)

def move_servo(pwm, angle, wait=0.5):
    """Move servo to angle instantly."""
    duty = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty)
    time.sleep(wait)

def smooth_move(pwm, start, end, steps=50, delay=0.02):
    """Move smoothly between angles."""
    if start < end:
        rng = range(start, end + 1)
    else:
        rng = range(start, end - 1, -1)

    for angle in rng:
        pwm.ChangeDutyCycle(angle_to_duty(angle))
        time.sleep(delay)

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, PWM_FREQ)
pwm.start(0)
time.sleep(0.5)

try:
    # --- SMOOTH SERVO MOTION SEQUENCE ---
    smooth_move(pwm,0,130)
    time.sleep(0.9)
    
    smooth_move(pwm,130,60)
    time.sleep(0.9)
    
    
   
  
    

    




finally:
    pwm.ChangeDutyCycle(0)
    pwm.stop()
    GPIO.cleanup()
