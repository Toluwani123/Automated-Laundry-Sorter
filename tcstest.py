import RPi.GPIO as GPIO
import time

# === Pin Assignments (BCM) ===
from config import S0, S1, S2, S3, OUT                   # OUT pin

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up pins
GPIO.setup(S0, GPIO.OUT)
GPIO.setup(S1, GPIO.OUT)
GPIO.setup(S2, GPIO.OUT)
GPIO.setup(S3, GPIO.OUT)
GPIO.setup(OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === TCS3200 Scaling: S0/S1 ===
# 100% scaling → S0 HIGH, S1 HIGH
GPIO.output(S0, GPIO.HIGH)
GPIO.output(S1, GPIO.HIGH)

def pulse_in():
    """Measure output frequency from TCS3200"""
    start = time.time()
    pulses = 0
    timeout = 0.040  # 40 ms window

    while time.time() - start < timeout:
        GPIO.wait_for_edge(OUT, GPIO.FALLING, timeout=50)
        pulses += 1

    # pulses / time = Hz
    duration = time.time() - start
    if duration == 0:
        return 0
    return int(pulses / duration)

def set_filter(mode):
    """Set S2/S3 filter mode"""
    if mode == "RED":
        GPIO.output(S2, GPIO.LOW)
        GPIO.output(S3, GPIO.LOW)
    elif mode == "BLUE":
        GPIO.output(S2, GPIO.LOW)
        GPIO.output(S3, GPIO.HIGH)
    elif mode == "CLEAR":
        GPIO.output(S2, GPIO.HIGH)
        GPIO.output(S3, GPIO.HIGH)
    elif mode == "GREEN":
        GPIO.output(S2, GPIO.HIGH)
        GPIO.output(S3, GPIO.LOW)
    time.sleep(0.005)

try:
    print("Reading TCS3200... Move colored objects in front of sensor.")
    while True:
        for mode in ["RED", "GREEN", "BLUE", "CLEAR"]:
            set_filter(mode)
            hz = pulse_in()
            print(f"{mode:6}: {hz:6} Hz")
        print("-" * 30)
        time.sleep(0.5)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    print("GPIO cleaned up.")
