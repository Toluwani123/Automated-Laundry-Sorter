#!/usr/bin/env python3
"""
Raspberry Pi 4: DHT22 + TCS3200 state machine
- Reads humidity first (damp/dry)
- Reads color (RGB -> HSV -> V) next (light/dark)
- Classification: DRY/DAMP × LIGHT/DARK
- Saves/loads TCS black/white calibration to JSON
"""

import os, json, time, sys
from statistics import median
from colorsys import rgb_to_hsv

# ---- DHT22 (CircuitPython) ----
import board
import adafruit_dht

# ---- GPIO (TCS3200) ----
import RPi.GPIO as GPIO

# =========================================================
# Configuration
# =========================================================

# Pins (BCM numbering)
S0, S1, S2, S3, OUT = 17, 18, 27, 22, 23   # TCS3200
DHT_PIN = board.D4                          # DHT22 on GPIO4

# Calibration file for TCS
CAL_FILE = "tcs_cal.json"

# Timings
DHT_MIN_INTERVAL = 2.5      # DHT22 spec: >=2s between reads (use 2.5s)
TCS_SETTLE = 0.02
TCS_SAMPLE = 0.12
TCS_REPEATS = 3

# Classification thresholds (tune these from your tests)
HUMIDITY_THRESHOLD = 70     # % relative humidity considered "damp"
V_THRESHOLD = 0.40          # HSV Value threshold for dark vs light

# =========================================================
# Helpers
# =========================================================

def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)

def normalize_rgb(raw, cal):
    """Two-point normalize (black/white) each channel to [0..1]."""
    r, g, b = raw
    rb, gb, bb = cal["black"]
    rw, gw, bw = cal["white"]
    rn = clamp01((r - rb) / max(rw - rb, 1e-6))
    gn = clamp01((g - gb) / max(gw - gb, 1e-6))
    bn = clamp01((b - bb) / max(bw - bb, 1e-6))
    return rn, gn, bn

def label_from_hsv(h_deg, s, v):
    if v < 0.15: return "DARK"
    if s < 0.15: return "GRAY/WHITE"
    if (h_deg < 15) or (h_deg >= 345): return "RED"
    if h_deg < 45:   return "ORANGE"
    if h_deg < 70:   return "YELLOW"
    if h_deg < 170:  return "GREEN"
    if h_deg < 200:  return "CYAN"
    if h_deg < 255:  return "BLUE"
    if h_deg < 290:  return "PURPLE"
    return "MAGENTA"

# =========================================================
# TCS3200 driver (frequency read)
# =========================================================

def tcs_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(S0, GPIO.OUT, initial=GPIO.HIGH)  # 100% scaling
    GPIO.setup(S1, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(S2, GPIO.OUT)
    GPIO.setup(S3, GPIO.OUT)
    GPIO.setup(OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # If your breakout has OE pin, tie it to GND (active-low) or set here.

def tcs_set_filter(rgb):
    # S2 S3 table: 00=Red, 11=Green, 01=Blue
    if rgb == "R":
        GPIO.output(S2, GPIO.LOW);  GPIO.output(S3, GPIO.LOW)
    elif rgb == "G":
        GPIO.output(S2, GPIO.HIGH); GPIO.output(S3, GPIO.HIGH)
    elif rgb == "B":
        GPIO.output(S2, GPIO.LOW);  GPIO.output(S3, GPIO.HIGH)
    else:
        raise ValueError("rgb must be 'R','G','B'")

def tcs_measure_freq(sample_time=TCS_SAMPLE, settle=TCS_SETTLE, repeats=TCS_REPEATS):
    freqs = []
    for _ in range(repeats):
        time.sleep(settle)
        t_end = time.time() + sample_time
        count = 0
        last = GPIO.input(OUT)
        # edge count loop
        while time.time() < t_end:
            s = GPIO.input(OUT)
            if s == 1 and last == 0:
                count += 1
            last = s
        freqs.append(count / sample_time)  # Hz
    return median(freqs)

def tcs_read_rgb_hz():
    tcs_set_filter("R"); r = tcs_measure_freq()
    tcs_set_filter("G"); g = tcs_measure_freq()
    tcs_set_filter("B"); b = tcs_measure_freq()
    return r, g, b

def load_cal():
    return json.load(open(CAL_FILE)) if os.path.exists(CAL_FILE) else None

def save_cal(cal):
    json.dump(cal, open(CAL_FILE, "w"), indent=2)

def tcs_calibrate():
    print("\n=== TCS3200 Calibration ===")
    input("Place sensor ~5–10 mm above MATTE BLACK. Press Enter...")
    rb, gb, bb = tcs_read_rgb_hz()
    print(f"BLACK Hz: R={rb:.0f} G={gb:.0f} B={bb:.0f}")

    input("Place sensor ~5–10 mm above MATTE WHITE (printer paper). Press Enter...")
    rw, gw, bw = tcs_read_rgb_hz()
    print(f"WHITE Hz: R={rw:.0f} G={gw:.0f} B={bw:.0f}")

    cal = {"black": [rb, gb, bb], "white": [rw, gw, bw]}
    save_cal(cal)
    print(f"Saved calibration → {CAL_FILE}\n")
    return cal

# =========================================================
# DHT22 driver (CircuitPython)
# =========================================================

def dht_init():
    # Disable PulseIn to avoid libgpiod timing issues on Bookworm
    return adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)

def dht_read_with_retries(dht, retries=5, pause=0.6):
    for _ in range(retries):
        try:
            h = dht.humidity
            t = dht.temperature
            if h is not None and t is not None:
                return int(round(h)), float(t)
        except RuntimeError:
            pass
        time.sleep(pause)
    raise RuntimeError("DHT read failed after retries")

# =========================================================
# Classification (mirrors your MSP logic)
# =========================================================

def classify_basket(humidity_pct, v_value):
    is_damp = humidity_pct >= HUMIDITY_THRESHOLD
    is_dark = v_value <= V_THRESHOLD
    if is_damp:
        return "DAMP_DARK" if is_dark else "DAMP_LIGHT"
    else:
        return "DRY_DARK" if is_dark else "DRY_LIGHT"

# =========================================================
# State Machine
# =========================================================

STATE_IDLE = 0
STATE_READ_HUMIDITY = 1
STATE_READ_COLOR = 2
STATE_DECIDE_BASKET = 3
STATE_ACTUATE = 4
STATE_ERROR = 5

class LaundrySorter:
    def __init__(self):
        self.state = STATE_IDLE
        self.dht = None
        self.cal = None
        self.last_ok = {"H": None, "S": None, "V": None, "label": None}
        self.humidity = None
        self.temperature = None
        self.rgb_hz = (0,0,0)
        self.hsv = (0,0,0)
        self.classification = "UNKNOWN"
        self.last_dht_time = 0

    def setup(self):
        print("\nInit: GPIO + DHT + TCS")
        tcs_init()
        self.dht = dht_init()
        self.cal = load_cal()
        if not self.cal:
            self.cal = tcs_calibrate()
        print("Init complete. Starting loop...\n")

    def run_once(self):
        try:
            if self.state == STATE_IDLE:
                print("=== Starting Measurement ===")
                self.state = STATE_READ_HUMIDITY

            elif self.state == STATE_READ_HUMIDITY:
                # Respect DHT interval
                since = time.time() - self.last_dht_time
                if since < DHT_MIN_INTERVAL:
                    time.sleep(DHT_MIN_INTERVAL - since)
                print("Reading humidity...")
                self.humidity, self.temperature = dht_read_with_retries(self.dht)
                self.last_dht_time = time.time()
                print(f"  H={self.humidity}%  T={self.temperature:.1f}°C")
                self.state = STATE_READ_COLOR

            elif self.state == STATE_READ_COLOR:
                print("Reading color (TCS3200)...")
                r, g, b = tcs_read_rgb_hz()
                self.rgb_hz = (r, g, b)
                rn, gn, bn = normalize_rgb(self.rgb_hz, self.cal)
                h, s, v = rgb_to_hsv(rn, gn, bn)
                h_deg = h * 360.0
                self.hsv = (h_deg, s, v)
                label = label_from_hsv(h_deg, s, v)
                self.last_ok = {"H": h_deg, "S": s, "V": v, "label": label}
                print(f"  Hz R={r:.0f} G={g:.0f} B={b:.0f} | "
                      f"Norm=({rn:.2f},{gn:.2f},{bn:.2f}) | "
                      f"HSV=({h_deg:.1f}°, {s:.2f}, {v:.2f}) -> {label}")
                self.state = STATE_DECIDE_BASKET

            elif self.state == STATE_DECIDE_BASKET:
                _, _, v = self.hsv
                self.classification = classify_basket(self.humidity, v)
                print(f"Classification: {self.classification} "
                      f"(H={self.humidity}%  V={v:.2f})")
                self.state = STATE_ACTUATE

            elif self.state == STATE_ACTUATE:
                # TODO: actuate servos/motors here
                print(f"ACTION: Move garment to basket: {self.classification}")
                print("=== Measurement Complete ===\n")
                # small dwell before next cycle
                time.sleep(1.0)
                self.state = STATE_IDLE

            elif self.state == STATE_ERROR:
                print("SYSTEM ERROR - Resetting in 3 seconds...")
                time.sleep(3)
                self.state = STATE_IDLE

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[ERROR] {e}")
            self.state = STATE_ERROR

def main():
    sorter = LaundrySorter()
    try:
        sorter.setup()
        while True:
            sorter.run_once()
            time.sleep(0.05)  # small loop delay
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()

