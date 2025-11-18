#!/usr/bin/env python3
"""
Raspberry Pi Laundry Sorter - Main Program
Modular version with separate components
"""

import RPi.GPIO as GPIO
from tcs3200 import TCS3200
from dht22_module import DHT22Sensor
from state_machine import LaundrySorter
from servo import ServoArm
from config import SERVO_POSITIONS
import time

def main():
    # Create sensor objects
    color_sensor = TCS3200()
    humidity_sensor = DHT22Sensor()
    servo_arm = ServoArm()
    servo_arm.move_to("IDLE", duration=2.0, steps=60)


    TEST_SERVOS_ONLY = True   
    if TEST_SERVOS_ONLY:
        try:
            print("Testing servo poses...")

            
            for pose_name in SERVO_POSITIONS.keys():
                print(f"\nMoving to pose: {pose_name}")
                servo_arm.move_to(pose_name, duration=1.5, steps=30)
                time.sleep(1.0)

    

        finally:
            GPIO.cleanup()
            print("GPIO cleanup complete after servo test")
        return
    # --- END SERVO TEST MODE ---

    # Create the main sorter (unchanged)
    #sorter = LaundrySorter(color_sensor, humidity_sensor, servo_arm)

    try:
        #sorter.setup()
        while True:
            #sorter.run_once()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete")

if __name__ == "__main__":
    main()
