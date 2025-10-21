"""
Shared configuration and constants for laundry sorter
"""

# Pins (BCM numbering)
S0, S1, S2, S3, OUT = 17, 18, 27, 22, 23   # TCS3200
DHT_PIN = "D4"                              # DHT22 on GPIO4

# Calibration file for TCS
CAL_FILE = "tcs_cal.json"

# Timings
DHT_MIN_INTERVAL = 2.5      
TCS_SETTLE = 0.02
TCS_SAMPLE = 0.12
TCS_REPEATS = 3

# Classification thresholds
HUMIDITY_THRESHOLD = 62     
V_THRESHOLD = 0.40         

# State constants
STATE_IDLE = 0
STATE_READ_HUMIDITY = 1
STATE_READ_COLOR = 2
STATE_DECIDE_BASKET = 3
STATE_ACTUATE = 4
STATE_ERROR = 5
