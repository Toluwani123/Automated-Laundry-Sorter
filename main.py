#!/usr/bin/env python3
"""
Raspberry Pi Laundry Sorter - Main Program
Modular version with separate components
"""

import RPi.GPIO as GPIO
import os 

from tcs3200 import TCS3200
from dht22_module import DHT22Sensor
from state_machine import LaundrySorter
from servo import ServoArm
from config import SERVO_POSITIONS,CAL_FILE,BASKET_POSITION_MAP
import time

TEST_SERVOS_ONLY = False
TEST_TCS= False
TEST_DHT= False
TEST_LCD= False

def test_servos(servo_arm):
    print("Testing Servos")
    
    #servo_arm.run_state("IDLE", move_duration=2.0, steps=60)
    time.sleep(4.0)
    for pose_name in ["BASKET_DAMP_RED","BASKET_DAMP_GREEN","BASKET_DAMP_BLUE","BASKET_DRY_RED","BASKET_DRY_GREEN","BASKET_DRY_BLUE", ]:
                print(f"\nMoving to pose: {pose_name}")
                servo_arm.run_state(pose_name, move_duration=1.5, steps=40)
                time.sleep(1.0)
    
    
def test_tcs(color_sensor):
    print("Testing TCS")
    
    color_sensor.setup()
    
    if not os.path.exists(CAL_FILE):
        print("No data found")
        color_sensor.calibrate()
        
    else:
        print("Using existing calib")
        
        
    time.sleep(0.5)
    for i in range(5):
        raw = color_sensor.read_raw_rgb()
        norm = color_sensor.normalize_rgb(raw)
        
        print(f"Sample {i+1}: raw={raw}, normalized={norm}")
        time.sleep(0.5)
    
    
def test_dht(humidity_sensor):
    print("Testing DHT")
    
    humidity_sensor.setup()
    
    for i in range(15):
        h,t = humidity_sensor.read_with_retries()
        
        
        print(f"Sample {i+1}: humidity={h:.1f}%, temp={t:.1f}Celsius,")
        time.sleep(2.0)
    

def main():
    # Create sensor objects
    color_sensor = None
    humidity_sensor = None
    servo_arm = None
    



    try:
        if TEST_SERVOS_ONLY:
            servo_arm = ServoArm()
            test_servos(servo_arm)
            return
        if TEST_TCS:
            color_sensor = TCS3200()
            test_tcs(color_sensor)
            return
            
        if TEST_DHT:
            humidity_sensor = DHT22Sensor()
            test_dht(humidity_sensor)
            return
            
            
        color_sensor = TCS3200()
        humidity_sensor = DHT22Sensor()
        servo_arm = ServoArm()
        
        
        sorter = LaundrySorter(color_sensor, humidity_sensor, servo_arm)
        
        sorter.setup()
        
        
        while True:
            sorter.run_once()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        
        #if servo_arm is not None:
            #servo_arm.cleanup()
       
            
        GPIO.cleanup()
        print("GPIO cleanup complete")

if __name__ == "__main__":
    main()
