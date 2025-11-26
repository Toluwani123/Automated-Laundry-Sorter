"""
DHT22 Humidity/Temperature Sensor Module
Handles initialization and reading of DHT22 sensor
"""

import time
import board
import adafruit_dht
from config import DHT_PIN, DHT_MIN_INTERVAL

class DHT22Sensor:
    def __init__(self):
        self.sensor = None
        self.last_read_time = 0
        
    def setup(self):
        """Initialize DHT22 sensor"""
        # Convert pin string to board pin
        pin_map = {"D4": board.D4, "D17": board.D17,"D23": board.D23}
        dht_pin = pin_map.get(DHT_PIN, board.D23)
        
        # Disable PulseIn to avoid libgpiod timing issues
        self.sensor = adafruit_dht.DHT22(dht_pin, use_pulseio=False)
        return self.sensor
    
    def read_with_retries(self, retries=10, pause=0.6):
        """Read humidity and temperature with retry logic"""
        # Respect minimum interval between reads
        time.sleep(pause)
        since_last = time.time() - self.last_read_time
        if since_last < DHT_MIN_INTERVAL:
            time.sleep(DHT_MIN_INTERVAL - since_last)
            
        for attempt in range(retries):
            try:
                humidity = self.sensor.humidity
                temperature = self.sensor.temperature
                if humidity is not None and temperature is not None:
                    self.last_read_time = time.time()
                    return int(round(humidity)), float(temperature)
            except RuntimeError as e:
                if attempt == retries - 1:  # Last attempt
                    raise RuntimeError(f"DHT read failed after {retries} retries: {e}")
            time.sleep(pause)
        
        raise RuntimeError("DHT read failed after retries")
