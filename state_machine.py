"""
State machine for laundry sorting process
Coordinates all sensors and makes classification decisions
"""

import time
from config import STATE_IDLE, STATE_READ_HUMIDITY, STATE_READ_COLOR, STATE_DECIDE_BASKET, STATE_ACTUATE, STATE_ERROR
from classifier import classify_basket, get_enhanced_color_label, rgb_to_hsv_normalized

class LaundrySorter:
    def __init__(self, tcs_sensor, dht_sensor):
        self.state = STATE_IDLE
        self.tcs_sensor = tcs_sensor
        self.dht_sensor = dht_sensor
        
        # Data storage
        self.last_ok = {"H": None, "S": None, "V": None, "label": None}
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
            
        print("Init complete. Starting loop...\n")
        
    def run_once(self):
        """Execute one cycle of the state machine"""
        try:
            if self.state == STATE_IDLE:
                print("=== Starting Measurement ===")
                self.state = STATE_READ_HUMIDITY

            elif self.state == STATE_READ_HUMIDITY:
                print("Reading humidity...")
                self.humidity, self.temperature = self.dht_sensor.read_with_retries()
                print(f"  H={self.humidity}%  T={self.temperature:.1f}°C")
                self.state = STATE_READ_COLOR

            elif self.state == STATE_READ_COLOR:
                print("Reading color (TCS3200)...")
                # Read and process color data
                r, g, b = self.tcs_sensor.read_raw_rgb()
                self.rgb_hz = (r, g, b)
                
                rn, gn, bn = self.tcs_sensor.normalize_rgb(self.rgb_hz)
                h_deg, s, v = rgb_to_hsv_normalized(rn, gn, bn)
                
                self.hsv = (h_deg, s, v)
                
                # Use enhanced color labeling with RGB ratios
                label = get_enhanced_color_label(h_deg, s, v, rn, gn, bn)
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
                # TODO: Add servo/motor control here
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
