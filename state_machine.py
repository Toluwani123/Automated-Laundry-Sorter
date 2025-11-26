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
    BASKET_POSITION_MAP,
    HUMIDITY_THRESHOLD,
)
from classifier import (
    classify_basket,
    get_enhanced_color_label,
    get_color_family,
    rgb_to_hsv_normalized,
)


class LaundrySorter:
    def __init__(self, tcs_sensor, dht_sensor, servo_arm=None, lcd_display=None):
        self.state = STATE_IDLE
        self.tcs_sensor = tcs_sensor
        self.dht_sensor = dht_sensor
        self.servo_arm = servo_arm
        self.lcd = lcd_display

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

        # Put arm in IDLE pose at construction-time if available
        if self.servo_arm is not None:
            try:
                self.servo_arm.run_state("IDLE", move_duration=1.0, steps=60)
            except Exception as e:
                print(f"[WARN] Servo init failed: {e}")

        print("Init complete. Call setup() before run loop.\n")

    def setup(self):
        """Initialize the sorter with sensors and (optionally) LCD."""
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

        # LCD: show initial waiting state
        if self.lcd is not None:
            # if lcd_module has show_waiting(), prefer that; otherwise fall back
            try:
                self.lcd.show_waiting()
            except AttributeError:
                self.update_lcd_status()

        print("Init complete. Ready to start loop...\n")

    # === LCD helper ===
    def update_lcd_status(self):
        """
        Push current known info to the LCD using sensor logic:

        - Wet/Dry is computed from self.humidity vs HUMIDITY_THRESHOLD
        - Color comes from self.last_ok["color_family"]
        """
        if self.lcd is None:
            return

        # Moisture logic based on sensor reading
        if self.humidity is None:
            humidity = None
            wet_dry_label = None
        else:
            humidity = self.humidity
            is_damp = humidity >= HUMIDITY_THRESHOLD   # same threshold used in classification
            wet_dry_label = "Wet" if is_damp else "Dry"

        # Color logic from TCS classification
        color_family = self.last_ok.get("color_family")

        # Send fully dynamic values to LCD
        self.lcd.show_status(
            humidity=humidity,
            wet_dry_label=wet_dry_label,
            color_family=color_family,
        )

    # === multi-sample humidity helper ===
    def measure_laundry_humidity(
        self,
        total_time: float = 10.0,
        min_samples: int = 3,
        retries: int = 3,
        pause: float = 0.8,
    ):
        """
        Keep the cloth at the MOISTURE_READ pose and take multiple DHT22 readings.
        Returns (effective_humidity, effective_temperature).

        - total_time: total window (seconds) to collect samples
        - min_samples: ensure at least this many valid samples
        """
        if self.dht_sensor is None:
            raise RuntimeError("DHT22 sensor not initialized")

        readings = []
        temps = []
        start = time.time()

        print(
            f"[MOISTURE] Starting multi-sample humidity measurement "
            f"(window={total_time}s, min_samples={min_samples})"
        )

        # Collect readings until we have enough samples AND the time window is done
        while (time.time() - start) < total_time or len(readings) < min_samples:
            try:
                h, t = self.dht_sensor.read_with_retries(
                    retries=retries,
                    pause=pause,
                )
                readings.append(h)
                temps.append(t)
                print(f"[MOISTURE] sample {len(readings)}: {h}% @ {t:.1f}°C")
            except RuntimeError as e:
                # Log but keep trying within the window
                print(f"[MOISTURE] read error: {e}")

        if not readings:
            raise RuntimeError("No valid humidity readings collected")

        # Discard the very first reading (sensor still adjusting to the cloth)
        if len(readings) > 1:
            stable = readings[1:]
        else:
            stable = readings

        # If we have a lot of samples, just use the last few (sensor has stabilized)
        if len(stable) >= 3:
            stable = stable[-3:]

        effective_h = sum(stable) / len(stable)
        effective_h = int(round(effective_h))

        # Use last valid temperature (or average if you prefer)
        eff_temp = temps[-1] if temps else None

        print(
            f"[MOISTURE] effective humidity = {effective_h}% "
            f"(based on {len(stable)} stable samples)"
        )
        return effective_h, eff_temp

    # === main state-machine step ===
    def run_once(self):
        """Execute one cycle of the state machine (one state transition)."""
        try:
            # ---------------- STATE_IDLE ----------------
            if self.state == STATE_IDLE:
                print("=== Starting Measurement ===")

                # Clear previous results for this new garment
                self.humidity = None
                self.temperature = None
                self.last_ok["color_family"] = None
                self.last_ok["detailed_label"] = None

                # LCD: both lines show "wait"
                self.update_lcd_status()

                if self.servo_arm is not None:
                    self.servo_arm.run_state("IDLE", move_duration=1.5, steps=60)
                self.state = STATE_READ_HUMIDITY

            # ---------------- STATE_READ_HUMIDITY ----------------
            elif self.state == STATE_READ_HUMIDITY:
                print("\n=== STATE_READ_HUMIDITY ===")
                print("Moving to humidity sensor and measuring cloth moisture...")

                # b. PICKUP_CLOTH
                # c. MOVE_TO_HUMIDITY
                # d. MOISTURE_READ (hold near sensor)
                if self.servo_arm is not None:
                    self.servo_arm.run_state(
                        "PICKUP_CLOTH", move_duration=1.5, steps=60
                    )
                    self.servo_arm.run_state(
                        "MOVE_TO_HUMIDITY", move_duration=1.5, steps=60
                    )
                    self.servo_arm.run_state(
                        "MOISTURE_READ", move_duration=1.5, steps=60
                    )

                try:
                    # New multi-sample, time-window measurement
                    self.humidity, self.temperature = self.measure_laundry_humidity(
                        total_time=10.0,   # seconds; tweak as needed
                        min_samples=6,
                        retries=3,
                        pause=0.8,
                    )
                    print(f"[STATE_READ_HUMIDITY] Effective humidity = {self.humidity}%")
                    if self.temperature is not None:
                        print(
                            f"[STATE_READ_HUMIDITY] Temperature ≈ "
                            f"{self.temperature:.1f}°C"
                        )

                    # LCD: show humidity value (Wet/Dry), color still "wait"
                    self.update_lcd_status()

                    # On success → next state
                    self.state = STATE_READ_COLOR

                except RuntimeError as e:
                    print(f"[ERROR] Humidity measurement failed: {e}")
                    self.state = STATE_ERROR

            # ---------------- STATE_READ_COLOR ----------------
            elif self.state == STATE_READ_COLOR:
                print("\n=== STATE_READ_COLOR ===")
                print("Reading color (TCS3200)...")

                # e. MOVE_TO_COLOR_SENSOR
                # f. COLOR_READ (hold over sensor)
                if self.servo_arm is not None:
                    self.servo_arm.run_state(
                        "MOVE_TO_COLOR_SENSOR", move_duration=1.0, steps=60
                    )
                    self.servo_arm.run_state(
                        "COLOR_READ", move_duration=1.0, steps=60
                    )

                # Read and process color data
                r, g, b = self.tcs_sensor.read_raw_rgb()
                self.rgb_hz = (r, g, b)

                rn, gn, bn = self.tcs_sensor.normalize_rgb(self.rgb_hz)
                h_deg, s, v = rgb_to_hsv_normalized(rn, gn, bn)

                self.hsv = (h_deg, s, v)

                detailed_label = get_enhanced_color_label(
                    h_deg, s, v, rn, gn, bn
                )
                color_family = get_color_family(
                    h_deg, s, v, rn, gn, bn
                )

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

                # LCD: now we know both humidity and color
                self.update_lcd_status()

                self.state = STATE_DECIDE_BASKET

            # ---------------- STATE_DECIDE_BASKET ----------------
            elif self.state == STATE_DECIDE_BASKET:
                print("\n=== STATE_DECIDE_BASKET ===")

                color_family = self.last_ok["color_family"]
                self.classification = classify_basket(self.humidity, color_family)

                print(f"Classification result: {self.classification}")
                print(f"  (H={self.humidity}% Family={color_family})")

                self.state = STATE_ACTUATE

            # ---------------- STATE_ACTUATE ----------------
            elif self.state == STATE_ACTUATE:
                print("\n=== STATE_ACTUATE ===")

                # g. MOVE_TO_BIN
                # h. DROP_OFF_CLOTH
                # i. RETURN_TO_IDLE
                basket_state = BASKET_POSITION_MAP.get(self.classification)
                if self.servo_arm is not None and basket_state is not None:
                    self.servo_arm.run_state(
                        basket_state, move_duration=1.0, steps=60
                    )
                    self.servo_arm.run_state(
                        "RETURN_TO_IDLE", move_duration=1.0, steps=60
                    )
                    self.servo_arm.run_state(
                        "IDLE", move_duration=1.0, steps=60
                    )

                # Keep LCD showing final humidity/color while we actuate
                self.update_lcd_status()

                print(f"ACTION: Move garment to basket: {self.classification}")
                print("=== Measurement Complete ===\n")

                time.sleep(1.0)  # dwell before next cycle
                self.state = STATE_IDLE

            # ---------------- STATE_ERROR ----------------
            elif self.state == STATE_ERROR:
                print("\n=== STATE_ERROR ===")
                print("SYSTEM ERROR - Resetting in 3 seconds...")
                time.sleep(3)
                self.state = STATE_IDLE

        except KeyboardInterrupt:
            # Let main() handle Ctrl+C cleanup
            raise
        except Exception as e:
            print(f"[ERROR] {e}")
            self.state = STATE_ERROR
