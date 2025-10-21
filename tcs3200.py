"""
TCS3200 Color Sensor Module
Handles initialization, reading, and calibration of TCS3200 sensor
"""

import os, json, time
from statistics import median
import RPi.GPIO as GPIO
from config import S0, S1, S2, S3, OUT, CAL_FILE, TCS_SETTLE, TCS_SAMPLE, TCS_REPEATS

class TCS3200:
    def __init__(self):
        self.calibration = None
        
    def setup(self):
        """Initialize GPIO pins for TCS3200"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(S0, GPIO.OUT, initial=GPIO.HIGH)  # 100% scaling
        GPIO.setup(S1, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(S2, GPIO.OUT)
        GPIO.setup(S3, GPIO.OUT)
        GPIO.setup(OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def _set_filter(self, rgb):
        """Set color filter (R, G, or B)"""
        if rgb == "R":
            GPIO.output(S2, GPIO.LOW);  GPIO.output(S3, GPIO.LOW)
        elif rgb == "G":
            GPIO.output(S2, GPIO.HIGH); GPIO.output(S3, GPIO.HIGH)
        elif rgb == "B":
            GPIO.output(S2, GPIO.LOW);  GPIO.output(S3, GPIO.HIGH)
        else:
            raise ValueError("rgb must be 'R','G','B'")
    
    def _measure_frequency(self, sample_time=TCS_SAMPLE, settle=TCS_SETTLE, repeats=TCS_REPEATS):
        """Measure frequency from sensor output"""
        freqs = []
        for _ in range(repeats):
            time.sleep(settle)
            t_end = time.time() + sample_time
            count = 0
            last = GPIO.input(OUT)
            # Edge count loop
            while time.time() < t_end:
                s = GPIO.input(OUT)
                if s == 1 and last == 0:
                    count += 1
                last = s
            freqs.append(count / sample_time)  # Hz
        return median(freqs)
    
    def read_raw_rgb(self):
        """Read raw RGB frequencies from sensor"""
        self._set_filter("R"); r = self._measure_frequency()
        self._set_filter("G"); g = self._measure_frequency()
        self._set_filter("B"); b = self._measure_frequency()
        return r, g, b
    
    def _clamp01(self, x):
        """Ensure value is between 0 and 1"""
        return 0.0 if x < 0 else (1.0 if x > 1 else x)
    
    def normalize_rgb(self, raw_rgb):
        """Normalize raw RGB using calibration data with simple blue-green correction"""
        if not self.calibration:
            raise ValueError("No calibration data loaded")
            
        r, g, b = raw_rgb
        rb, gb, bb = self.calibration["black"]
        rw, gw, bw = self.calibration["white"]
        
        rn = self._clamp01((r - rb) / max(rw - rb, 1e-6))
        gn = self._clamp01((g - gb) / max(gw - gb, 1e-6))
        bn = self._clamp01((b - bb) / max(bw - bb, 1e-6))
        
        # Simple blue-green correction: reduce crosstalk
        # If blue is high and green is also high, adjust to emphasize the dominant one
        if bn > 0.3 and gn > 0.3:
            if bn > gn:
                gn = max(0, gn * 0.8)  # Reduce green when blue is dominant
            else:
                bn = max(0, bn * 0.8)  # Reduce blue when green is dominant
        
        return rn, gn, bn
    
    def load_calibration(self):
        """Load calibration from file"""
        if os.path.exists(CAL_FILE):
            self.calibration = json.load(open(CAL_FILE))
            return self.calibration
        return None
    
    def save_calibration(self, calibration):
        """Save calibration to file"""
        json.dump(calibration, open(CAL_FILE, "w"), indent=2)
        self.calibration = calibration
    
    def calibrate(self):
        """Run calibration procedure"""
        print("\n=== TCS3200 Calibration ===")
        input("Place sensor ~5–10 mm above MATTE BLACK. Press Enter...")
        rb, gb, bb = self.read_raw_rgb()
        print(f"BLACK Hz: R={rb:.0f} G={gb:.0f} B={bb:.0f}")

        input("Place sensor ~5–10 mm above MATTE WHITE (printer paper). Press Enter...")
        rw, gw, bw = self.read_raw_rgb()
        print(f"WHITE Hz: R={rw:.0f} G={gw:.0f} B={bw:.0f}")

        calibration = {"black": [rb, gb, bb], "white": [rw, gw, bw]}
        self.save_calibration(calibration)
        print(f"Saved calibration → {CAL_FILE}\n")
        return calibration
