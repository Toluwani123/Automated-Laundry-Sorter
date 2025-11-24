"""
State machine for laundry sorting process
Coordinates all sensors and makes classification decisions
"""

import time
from config import (
    STATE_IDLE,
    STATE_READ_HUMIDITY,
    STATE_READ_COLOR,
    STATE_DECIDE_BASKET,
    STATE_ACTUATE,
    STATE_ERROR,
    BASKET_POSITION_MAP
)
from classifier import *


class LaundrySorter:
    def __init__(self, tcs_sensor, dht_sensor, servo_arm=None):
        self.state = STATE_IDLE
        self.tcs_sensor = tcs_sensor
        self.dht_sensor = dht_sensor
        self.servo_arm = servo_arm  # <-- new

        # Data storage
        self.last_ok = {
            "H": None,
            "S": None,
            "V": None,
            "detailed_label": None,
            "color_family": None,
        }
        self.humidity = None
        self.temperature = None
        self.rgb_hz = (0, 0, 0)
        self.hsv = (0, 0, 0)
        self.classification = "UNKNOWN"

    def setup(self):
        """Initialize the sorter with sensors"""
        print("\nInit: TCS3200 + DHT22")
        self.tcs_sensor.setup()
        self.dht_sensor.setup()

        # Load or create calibration
        if not self.tcs_sensor.load_calibration():
            print("No calibration found, starting calibration...")
            self.tcs_sensor.calibrate()
        else:
            print("Calibration loaded successfully")

        # Put arm in IDLE pose at startup if available
        if self.servo_arm is not None:
            try:
                self.servo_arm.run_state("IDLE", move_duration=1.0, steps=60)
            except Exception as e:
                print(f"[WARN] Servo init failed: {e}")

        print("Init complete. Starting loop...\n")

    def run_once(self):
        """Execute one cycle of the state machine"""
        try:
            if self.state == STATE_IDLE:
                print("=== Starting Measurement ===")
                # Start with servo in IDLE (optional safety)
                if self.servo_arm is not None:
                    self.servo_arm.run_state("IDLE", move_duration=1.5, steps=60)
                self.state = STATE_READ_HUMIDITY

            elif self.state == STATE_READ_HUMIDITY:
                print("Reading humidity...")

                # Servo sequence for humidity:
                # b. PICKUP_CLOTH
                # c. MOVE_TO_HUMIDITY
                # d. MOISTURE_READ (includes 5s hold)
                if self.servo_arm is not None:
                    self.servo_arm.run_state("PICKUP_CLOTH", move_duration=1.5, steps=60)
                    self.servo_arm.run_state("MOVE_TO_HUMIDITY", move_duration=1.5, steps=60)
                    self.servo_arm.run_state("MOISTURE_READ", move_duration=1.5, steps=60)

                # Now actually read humidity
                self.humidity, self.temperature = self.dht_sensor.read_with_retries()
                print(f"  H={self.humidity}%  T={self.temperature:.1f}°C")
                self.state = STATE_READ_COLOR

            elif self.state == STATE_READ_COLOR:
                print("Reading color (TCS3200)...")

                # Servo sequence for color:
                # e. MOVE_TO_COLOR_SENSOR
                # f. COLOR_READ (includes 5s hold)
                if self.servo_arm is not None:
                    self.servo_arm.run_state("MOVE_TO_COLOR_SENSOR", move_duration=1.0, steps=60)
                    self.servo_arm.run_state("COLOR_READ", move_duration=1.0, steps=60)

                # Read and process color data
                r, g, b = self.tcs_sensor.read_raw_rgb()
                self.rgb_hz = (r, g, b)

                rn, gn, bn = self.tcs_sensor.normalize_rgb(self.rgb_hz)
                h_deg, s, v = rgb_to_hsv_normalized(rn, gn, bn)

                self.hsv = (h_deg, s, v)

                detailed_label = get_enhanced_color_label(h_deg, s, v, rn, gn, bn)
                color_family = get_color_family(h_deg, s, v, rn, gn, bn)

                self.last_ok = {
                    "H": h_deg,
                    "S": s,
                    "V": v,
                    "detailed_label": detailed_label,
                    "color_family": color_family,
                }

                print(
                    f"  Hz R={r:.0f} G={g:.0f} B={b:.0f} | "
                    f"Norm=({rn:.2f},{gn:.2f},{bn:.2f}) | "
                    f"HSV=({h_deg:.1f}°, {s:.2f}, {v:.2f})"
                )
                print(f"  Detailed Color: {detailed_label}")
                print(f"  Color Family: {color_family}")
                self.state = STATE_DECIDE_BASKET

            elif self.state == STATE_DECIDE_BASKET:
                # Use color family for basket classification
                color_family = self.last_ok["color_family"]
                self.classification = classify_basket(self.humidity, color_family)

                print(f"Basket Classification: {self.classification}")
                print(f"  (H={self.humidity}% Family={color_family})")
                self.state = STATE_ACTUATE

            elif self.state == STATE_ACTUATE:
                # Servo sequence for bin drop-off:
                # g. MOVE_TO_BIN
                # h. DROP_OFF_CLOTH
                # i. RETURN_TO_IDLE
                # j. IDLE
                
                basket_state = BASKET_POSITION_MAP.get(self.classification)
                if self.servo_arm is not None and basket_state is not None:
                    self.servo_arm.run_state(basket_state, move_duration=1.0, steps=60)
                    self.servo_arm.run_state("RETURN_TO_IDLE", move_duration=1.0, steps=60)
                    self.servo_arm.run_state("IDLE", move_duration=1.0, steps=60)

                print(f"LCD Display: {self.last_ok['detailed_label']}")
                print(f"ACTION: Move garment to basket: {self.classification}")
                print("=== Measurement Complete ===\n")
                time.sleep(1.0)  # Dwell before next cycle
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
