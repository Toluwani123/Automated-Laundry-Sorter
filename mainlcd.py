#!/usr/bin/env python3
import time
import smbus

# =========================
# CONFIG
# =========================
I2C_ADDR = 0x27      # Change to 0x3F if your scan shows that instead
I2C_BUS = 1          # Bus 1 on Raspberry Pi 3

LCD_WIDTH = 16       # Max characters per line

LCD_CHR = 1          # Send data
LCD_CMD = 0          # Send command

LCD_LINE_1 = 0x80    # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0    # LCD RAM address for the 2nd line

LCD_BACKLIGHT = 0x08 # On
# LCD_BACKLIGHT = 0x00  # Off (if you want to test backlight off)

ENABLE = 0x04        # Enable bit

E_PULSE = 0.0005
E_DELAY = 0.0005

# Open I2C interface
bus = smbus.SMBus(I2C_BUS)


def lcd_byte(bits, mode):
    """
    Send byte to data pins.
    bits = data
    mode = 1 for data, 0 for command
    """
    # High nibble
    high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    # Low nibble
    low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

    bus.write_byte(I2C_ADDR, high)
    lcd_toggle_enable(high)

    bus.write_byte(I2C_ADDR, low)
    lcd_toggle_enable(low)


def lcd_toggle_enable(bits):
    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
    time.sleep(E_DELAY)


def lcd_init():
    """
    Initialise display (4-bit mode, 2 lines, etc.)
    """
    lcd_byte(0x33, LCD_CMD)  # Initialize
    lcd_byte(0x32, LCD_CMD)  # Set to 4-bit mode
    lcd_byte(0x06, LCD_CMD)  # Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # Turn cursor off
    lcd_byte(0x28, LCD_CMD)  # 2 line display
    lcd_byte(0x01, LCD_CMD)  # Clear display
    time.sleep(E_DELAY)


def lcd_string(message, line):
    """
    Send string to display on a specific line.
    Pads or cuts to LCD_WIDTH characters.
    """
    message = message.ljust(LCD_WIDTH, " ")[:LCD_WIDTH]

    lcd_byte(line, LCD_CMD)
    for char in message:
        lcd_byte(ord(char), LCD_CHR)


def main():
    try:
        lcd_init()

        lcd_string("Raspberry Pi 3", LCD_LINE_1)
        lcd_string("LCD Test OK!", LCD_LINE_2)
        time.sleep(3)

        lcd_string("Line 1: Hello", LCD_LINE_1)
        lcd_string("Line 2: World", LCD_LINE_2)
        time.sleep(3)

        # Simple counter test
        for i in range(0, 21):
            lcd_string(f"Count: {i}".ljust(LCD_WIDTH), LCD_LINE_1)
            lcd_string("Testing display".ljust(LCD_WIDTH), LCD_LINE_2)
            time.sleep(0.5)

        # Clear at the end
        lcd_byte(0x01, LCD_CMD)
        lcd_string("Done!", LCD_LINE_1)
        time.sleep(2)

        # Optionally turn backlight off
        # bus.write_byte(I2C_ADDR, 0x00)

    except KeyboardInterrupt:
        # Clear on CTRL+C
        lcd_byte(0x01, LCD_CMD)
        lcd_string("Interrupted", LCD_LINE_1)
    finally:
        # Clear & turn off backlight when done
        lcd_byte(0x01, LCD_CMD)
        bus.write_byte(I2C_ADDR, 0x00)


if __name__ == "__main__":
    main()
