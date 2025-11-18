"""
Shared configuration and constants for laundry sorter
"""

# Pins (BCM numbering)
S0, S1, S2, S3, OUT = 17, 18, 27, 22, 23   # TCS3200
DHT_PIN = "D4"                              # DHT22 on GPIO4
SERVO_PINS = {
	"Bottom": 18,
	"Elbow": 17,
	"Wrist":22,
	"Claw":27
}

SERVO_POSITIONS = {
    "IDLE": {
        "Bottom": 0,   # Center (within 45–150)
        "Elbow": 45,
       
        "Wrist": 135,   # Mid in range
        "Claw": 20     # Slightly open (>=20)
    },

    "HUMIDITY_READ": {
        "Bottom": 20,
        "Elbow": 30,
      
        "Wrist": 90,   # Tilt toward sensor
        "Claw": 20
    },

    "COLOR_READ": {
        "Bottom": 40,
        "Elbow": 30,
        
        "Wrist": 90,    # Different tilt than humidity
        "Claw": 20
    },

    "BASKET_DAMP_RED": {
        "Bottom": 60,  # Turn left → min
        "Elbow": 0,
        
        "Wrist": 60,
        "Claw": 120     # Closed (min safe)
    },
    "BASKET_DAMP_GREEN": {
        "Bottom": 80,  # Forward
        "Elbow": 0,
    
        "Wrist": 60,
        "Claw": 120
    },
    "BASKET_DAMP_BLUE": {
        "Bottom": 100, # Turn right → max
        "Elbow": 0,
        
        "Wrist": 60,
        "Claw": 120
    },

    "BASKET_DRY_RED": {
        "Bottom": 120,
        "Elbow": 0,
        
        "Wrist": 60, 
        "Claw": 120
    },
    "BASKET_DRY_GREEN": {
        "Bottom": 140,
        "Elbow": 0,
        "Wrist": 60,
        "Claw": 120
    },
    "BASKET_DRY_BLUE": {
        "Bottom": 160,
        "Elbow": 0,
        "Wrist": 60,
        "Claw": 0
    }
}


BASKET_POSITION_MAP = {
    "DAMP_RED":   "BASKET_DAMP_RED",
    "DRY_RED":    "BASKET_DRY_RED",
    "DAMP_GREEN": "BASKET_DAMP_GREEN",
    "DRY_GREEN":  "BASKET_DRY_GREEN",
    "DAMP_BLUE":  "BASKET_DAMP_BLUE",
    "DRY_BLUE":   "BASKET_DRY_BLUE",
}


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
