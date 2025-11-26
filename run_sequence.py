# run_sequence.py
from servo5 import ServoArm
import time

# This is the exact order you specified (a → i → then back to IDLE)
STATE_SEQUENCE = [
    "IDLE",              # a
    "PICKUP_CLOTH",      # b
    "MOVE_TO_HUMIDITY",  # c
    "MOISTURE_READ",     # d
    "MOVE_TO_COLOR_SENSOR",  # e
    "COLOR_READ",        # f
    "MOVE_TO_BIN",       # g
    "DROP_OFF_CLOTH",    # h
    "RETURN_TO_IDLE",    # i
    "IDLE",              # j (back to IDLE)
]


def main():
    arm = ServoArm()

    try:
        print("Running full laundry-arm sequence...")
        for state_name in STATE_SEQUENCE:
            arm.run_state(state_name, move_duration=1.0, steps=60)
        print("Sequence complete.")

    finally:
        arm.cleanup()


if __name__ == "__main__":
    main()
