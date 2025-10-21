#!/usr/bin/env python3
"""
Raspberry Pi Laundry Sorter - Main Program
Modular version with separate components
"""

import RPi.GPIO as GPIO
from tcs3200 import TCS3200
from dht22_module import DHT22Sensor
from state_machine import LaundrySorter
import time

def main():
    # Create sensor objects
    color_sensor = TCS3200()
    humidity_sensor = DHT22Sensor()
    
    # Create the main sorter
    sorter = LaundrySorter(color_sensor, humidity_sensor)
    
    try:
        # Initialize everything
        sorter.setup()
        
        # Main loop
        while True:
            sorter.run_once()
            time.sleep(0.05)  # Small loop delay
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete")

if __name__ == "__main__":
    main()
