"""
Classification logic for laundry sorting
Converts RGB to HSV and classifies based on humidity and color value
"""

from colorsys import rgb_to_hsv
from config import HUMIDITY_THRESHOLD, V_THRESHOLD
import time

def classify_basket(humidity_pct, color_family):
    """Classify laundry into one of six categories based on color family"""
    is_damp = humidity_pct >= HUMIDITY_THRESHOLD
    
    if color_family == "RED":
        return "DAMP_RED" if is_damp else "DRY_RED"
    elif color_family == "GREEN":
        return "DAMP_GREEN" if is_damp else "DRY_GREEN"
    elif color_family == "BLUE":
        return "DAMP_BLUE" if is_damp else "DRY_BLUE"
    else:
        return "UNKNOWN"

def get_color_family(h_deg, s, v, rn, gn, bn):
    """
    Map colors to RGB family for bins
    """
    
    if v < 0.2:
        total = rn + gn + bn
        if total > 0:
            r_ratio = rn / total
            g_ratio = gn / total
            b_ratio = bn / total
            max_ratio = max(r_ratio, g_ratio, b_ratio)
            
            if max_ratio == r_ratio and r_ratio > 0.35:
                return "RED"
            elif max_ratio == g_ratio and g_ratio > 0.35:
                return "GREEN"
            elif max_ratio == b_ratio and b_ratio > 0.35:
                return "BLUE"
    
    # Normal colors - use hue ranges
    if (h_deg < 60) or (h_deg >= 330):  # Red, Orange, Yellow, Pink, Magenta
        return "RED"
    elif h_deg < 180:  # Green, Yellow-Green, Cyan
        return "GREEN"
    else:  # Blue, Purple, Blue-Green
        return "BLUE"

"""def get_enhanced_color_label(h_deg, s, v, rn, gn, bn):
   
    # First determine the shade based on value
    if v < 0.11: 
        return "VERY_DARK"
    elif v < 0.3:
        shade = "DARK_"
    elif v < 0.55:
        shade = "MEDIUM_"
    else:
        shade = "LIGHT_"
    
    # Handle low saturation colors (grays/whites)
    if s < 0.22:
        if v > 0.7:
            return "WHITE"
        elif v > 0.3:
            return "GRAY"
        else:
            return "DARK_GRAY"
    
    # Calculate RGB ratios to help with blue-green differentiation
    total = rn + gn + bn
    if total > 0:
        r_ratio = rn / total
        g_ratio = gn / total
        b_ratio = bn / total
    else:
        return "BLACK"
    
    # Enhanced color detection with blue-green differentiation
    if (h_deg < 15) or (h_deg >= 345):
        return shade + "RED"
    elif h_deg < 45:
        return shade + "ORANGE"
    elif h_deg < 70:
        return shade + "YELLOW"
    elif h_deg < 170:
        # Green region - check if it's more blue-green or yellow-green
        if h_deg > 140 and b_ratio > g_ratio * 0.8:
            return shade + "BLUE_GREEN"
        else:
            return shade + "GREEN"
    elif h_deg < 200:
        return shade + "CYAN"
    elif h_deg < 255:
        # Blue region - check if it's more green-blue
        if h_deg < 230 and g_ratio > b_ratio * 0.8:
            return shade + "GREEN_BLUE"
        else:
            return shade + "BLUE"
    elif h_deg < 290:
        return shade + "PURPLE"
    else:
        return shade + "MAGENTA"
"""
def get_enhanced_color_label(h_deg, s, v, rn, gn, bn):
    # First determine the shade based on value
    if v < 0.11: 
        return "VERY_DARK"
    elif v < 0.3:
        shade = "DARK_"
    elif v < 0.55:
        shade = "MEDIUM_"
    else:
        shade = "LIGHT_"
    
    # Handle low saturation colors (grays/whites)
    if s < 0.22:
        if v > 0.7:
            return "WHITE"
        elif v > 0.3:
            return "GRAY"
        else:
            return "DARK_GRAY"
    
    # Calculate RGB ratios to help with blue-green differentiation
    total = rn + gn + bn
    if total > 0:
        r_ratio = rn / total
        g_ratio = gn / total
        b_ratio = bn / total
    else:
        return "BLACK"
    
    
    if v < 0.2:
        # For very dark colors, use RGB dominance instead of hue
        max_ratio = max(r_ratio, g_ratio, b_ratio)
        if max_ratio == g_ratio and g_ratio > 0.35:
            return "DARK_GREEN"
        elif max_ratio == r_ratio and r_ratio > 0.35:
            return "DARK_RED"
        elif max_ratio == b_ratio and b_ratio > 0.35:
            return "DARK_BLUE"
    
    
    elif h_deg < 170:  # Green region
        # Using hue nd rgb
        if g_ratio > r_ratio and g_ratio > b_ratio:
            # Green-dominated
            if h_deg > 140 and b_ratio > 0.25:
                return shade + "BLUE_GREEN"
            elif h_deg < 90 and r_ratio > 0.25:
                return shade + "YELLOW_GREEN"
            else:
                return shade + "GREEN"
        else:
            # Not green-dominated -> use ratios
            if g_ratio > 0.3:
                return shade + "GREENISH"
            else:
                # Hues only
                if h_deg < 45:
                    return shade + "ORANGE"
                elif h_deg < 70:
                    return shade + "YELLOW"
                else:
                    return shade + "GREEN"
    
   
    elif (h_deg < 15) or (h_deg >= 345):
        return shade + "RED"
    elif h_deg < 45:
        return shade + "ORANGE"
    elif h_deg < 70:
        return shade + "YELLOW"
    elif h_deg < 200:
        return shade + "CYAN"
    elif h_deg < 255:
       
        if h_deg < 230 and g_ratio > b_ratio * 0.8:
            return shade + "GREEN_BLUE"
        else:
            return shade + "BLUE"
    elif h_deg < 290:
        return shade + "PURPLE"
    else:
        return shade + "MAGENTA"

def rgb_to_hsv_normalized(r, g, b):
    """Convert RGB to HSV with hue in degrees"""
    h, s, v = rgb_to_hsv(r, g, b)
    return h * 360.0, s, v
