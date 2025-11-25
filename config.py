"""
Shared configuration and constants for laundry sorter
"""

# Pins (BCM numbering)
S0, S1, S2, S3, OUT = 19, 26, 13, 6, 11   # TCS3200
DHT_PIN = "D23"                              # DHT22 on GPIO4
SERVO_PINS = {
	"Bottom": 17,
	"Elbow": 27,
	"Wrist":22,
	"Claw":5
}


SERVO_POSITIONS = {
     # a. Idle state: S1 - 0, S2 - 0, S3 - 120, S4 - 120
    "IDLE": {
        "Bottom": 0,
        "Elbow": 75,
        "Wrist": 120,
        "Claw": 100,
    },

    # b. Pick up cloth state:
    #    S1 stays at 0, S2 0→30, S3 120→80, S4 120→0
    "PICKUP_CLOTH": {
        "Bottom": 0,
        "Elbow": 125,
        "Wrist": 85,
        "Claw": 0,
    },

    # c. Move to humidity:
    #    S3 80→120, S2 30→0, S1 0→20, S4 stays at 0
    
    "MOVE_TO_HUMIDITY": {
        "Bottom": 12,
        "Elbow": 100,
        "Wrist": 120,
        "Claw": 0,
    },

    # d. Moisture read:
    #    S2 0→40, S3 120→80, S1 stays 20, S4 stays 0
    "MOISTURE_READ": {
        "Bottom": 12,
        "Elbow": 120,
        "Wrist": 85,
        "Claw": 0,
    },

    # e. Move to color sensor:
    #    S3 80→120, S2 40→0, S1 20→40, S4 stays 0
    "MOVE_TO_COLOR_SENSOR": {
        "Bottom": 30,
        "Elbow": 55,
        "Wrist": 120,
        "Claw": 0,
    },

    # f. Color read:
    #    S2 0→30, S3 120→80, S4 stays 0, S1 stays 40
    "COLOR_READ": {
        "Bottom": 30,
        "Elbow": 120,
        "Wrist": 95,
        "Claw": 0,
    },

    # g. Move to bin state:
    #    S3 80→120, S2 30→0, S1 40→100, S4 stays 0
    "MOVE_TO_BIN": {
        "Bottom": 35,
        "Elbow": 55,
        "Wrist": 120,
        "Claw": 0,
    },
    
    "BASKET_DAMP_RED":{
    
        "Bottom": 50,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    "BASKET_DAMP_GREEN":{
    
        "Bottom": 75,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    "BASKET_DAMP_BLUE":{
    
        "Bottom": 100,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    
    "BASKET_DRY_RED":{
    
        "Bottom": 100,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    "BASKET_DRY_GREEN":{
    
        "Bottom": 125,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    "BASKET_DRY_BLUE":{
    
        "Bottom": 135,
        "Elbow": 100,
        "Wrist": 80,
        "Claw": 120,
    
    },
    

    # i. Return to idle position:
    #    S2 30→0, S3 80→120, S1 100→0, S4 stays 120
    #    (this is effectively the same as IDLE)
    "RETURN_TO_IDLE": {
        "Bottom": 0,
        "Elbow": 55,
        "Wrist": 120,

    },
    

    
    
    
}


BASKET_POSITION_MAP = {
    "DAMP_RED":   "BASKET_DAMP_RED",
    "DRY_RED":    "BASKET_DRY_RED",
    "DAMP_GREEN": "BASKET_DAMP_GREEN",
    "DRY_GREEN":  "BASKET_DRY_GREEN",
    "DAMP_BLUE":  "BASKET_DAMP_BLUE",
    "DRY_BLUE":   "BASKET_DRY_BLUE",
}

STATE_SERVO_ORDER = {
    "IDLE":               ["Bottom", "Elbow", "Wrist", "Claw"],
    "PICKUP_CLOTH":       ["Elbow", "Wrist", "Claw"],         # S1 stays
    "MOVE_TO_HUMIDITY":   ["Wrist", "Elbow", "Bottom"],         # S4 stays
    "MOISTURE_READ":      ["Wrist","Elbow"],               # S1 & S4 stay
    "MOVE_TO_COLOR_SENSOR":["Wrist", "Elbow", "Bottom"],        # S4 stays
    "COLOR_READ":         ["Wrist","Elbow"],               # S1 & S4 stay
    "MOVE_TO_BIN":        ["Wrist", "Elbow", "Bottom"],         # S4 stays
    "BASKET_DAMP_RED":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "BASKET_DRY_RED":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "BASKET_DAMP_GREEN":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "BASKET_DRY_GREEN":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "BASKET_DAMP_BLUE":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "BASKET_DRY_BLUE":     ["Bottom","Wrist","Elbow",  "Claw"],         # S1 stays
    "RETURN_TO_IDLE":     ["Wrist","Elbow", "Bottom"],         # S4 stays
}

PER_SERVO_DELAY = 1.0     # seconds between each servo move
READ_STATE_EXTRA_DELAY = 5.0  # seconds after MOISTURE_READ & COLOR_READ

# Whole-cycle order (a → j)
STATE_SEQUENCE = [
    "IDLE",
    "PICKUP_CLOTH",
    "MOVE_TO_HUMIDITY",
    "MOISTURE_READ",
    "MOVE_TO_COLOR_SENSOR",
    "COLOR_READ",
    "MOVE_TO_BIN",
    "DROP_OFF_CLOTH",
    "RETURN_TO_IDLE",
    "IDLE",
]

# Calibration file for TCS
CAL_FILE = "tcs_cal.json"

# Timings
DHT_MIN_INTERVAL = 2.5      
TCS_SETTLE = 0.02
TCS_SAMPLE = 0.12
TCS_REPEATS = 3

# Classification thresholds
HUMIDITY_THRESHOLD = 58     
HUMIDITY_MARGIN = 3
V_THRESHOLD = 0.40         

# State constants
STATE_IDLE = 0
STATE_READ_HUMIDITY = 1
STATE_READ_COLOR = 2
STATE_DECIDE_BASKET = 3
STATE_ACTUATE = 4
STATE_ERROR = 5
