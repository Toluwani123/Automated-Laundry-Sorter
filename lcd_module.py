# lcd_module.py

from RPLCD.i2c import CharLCD

# lcd_module.py

from RPLCD.i2c import CharLCD

class LCDDisplay:
    def __init__(self, i2c_addr=0x27, cols=16, rows=2):
        """
        i2c_addr: usually 0x27 or 0x3F for common backpacks.
        """
        self.lcd = CharLCD(
            i2c_expander='PCF8574',
            address=i2c_addr,
            port=1,          # /dev/i2c-1
            cols=cols,
            rows=rows,
            charmap='A00'
        )
        self.cols = cols
        self.rows = rows

        # Start with "waiting" display
        self.show_status(humidity=None, wet_dry_label=None, color_family=None)

    def _write_lines(self, line1: str, line2: str):
        """Clear LCD and write two lines (auto-truncate/pad to width)."""
        self.lcd.clear()

        line1 = (line1 or "")[:self.cols].ljust(self.cols)
        line2 = (line2 or "")[:self.cols].ljust(self.cols)

        self.lcd.write_string(line1)
        self.lcd.crlf()
        self.lcd.write_string(line2)

    def show_status(self, humidity=None, wet_dry_label=None, color_family=None):
        """
        humidity: numeric humidity (%) or None if not yet measured
        wet_dry_label: string like "Wet" / "Dry" based on your logic, or None
        color_family: color family from TCS logic ("RED", "GREEN", etc.) or None

        Behavior:
        - If humidity or wet_dry_label is None  -> "humidity: wait"
        - Else                                  -> "humidity: 56% Wet"

        - If color_family is None               -> "color: wait"
        - Else                                  -> "color: RED" (or whatever family)
        """
        if humidity is None or wet_dry_label is None:
            line1 = "humidity: wait"
        else:
            line1 = f"humidity: {int(humidity)}%{wet_dry_label}"

        if color_family is None:
            line2 = "color: wait"
        else:
            line2 = f"color: {color_family.upper()}"

        self._write_lines(line1, line2)

    def show_waiting(self):
        """Explicit helper to put LCD into 'waiting' message."""
        self.show_status(humidity=None, wet_dry_label=None, color_family=None)
class LCDDisplay:
    def __init__(self, i2c_addr=0x27, cols=16, rows=2):
        """
        i2c_addr: usually 0x27 or 0x3F for common backpacks.
        """
        self.lcd = CharLCD(
            i2c_expander='PCF8574',
            address=i2c_addr,
            port=1,          # /dev/i2c-1
            cols=cols,
            rows=rows,
            charmap='A00'
        )
        self.cols = cols
        self.rows = rows

        # Start with "waiting" display
        self.show_status(humidity=None, wet_dry_label=None, color_family=None)

    def _write_lines(self, line1: str, line2: str):
        """Clear LCD and write two lines (auto-truncate/pad to width)."""
        self.lcd.clear()

        line1 = (line1 or "")[:self.cols].ljust(self.cols)
        line2 = (line2 or "")[:self.cols].ljust(self.cols)

        self.lcd.write_string(line1)
        self.lcd.crlf()
        self.lcd.write_string(line2)

    def show_status(self, humidity=None, wet_dry_label=None, color_family=None):
        """
        humidity: numeric humidity (%) or None if not yet measured
        wet_dry_label: string like "Wet" / "Dry" based on your logic, or None
        color_family: color family from TCS logic ("RED", "GREEN", etc.) or None

        Behavior:
        - If humidity or wet_dry_label is None  -> "humidity: wait"
        - Else                                  -> "humidity: 56% Wet"

        - If color_family is None               -> "color: wait"
        - Else                                  -> "color: RED" (or whatever family)
        """
        if humidity is None or wet_dry_label is None:
            line1 = "humidity: wait"
        else:
            line1 = f"humidity: {int(humidity)}%{wet_dry_label}"

        if color_family is None:
            line2 = "color: wait"
        else:
            line2 = f"color: {color_family.upper()}"

        self._write_lines(line1, line2)

    def show_waiting(self):
        """Explicit helper to put LCD into 'waiting' message."""
        self.show_status(humidity=None, wet_dry_label=None, color_family=None)
