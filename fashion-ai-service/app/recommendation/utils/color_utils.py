"""
Mathematical Color Conversion Utilities for Vouge.AI recommendations.
Pure Python implementations of HEX, RGB, HSV, XYZ, CIELAB conversions and Delta-E distance math.
Saves us from colormath dependency compatibility shifts under Python 3.14.
"""
import math
from typing import Tuple

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Converts a HEX string (e.g. '#FFFFFF' or 'FFFFFF') to an RGB tuple (0-255)."""
    h = hex_str.lstrip('#')
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts an RGB tuple (0-255) to a HEX string (e.g. '#ffffff')."""
    return f"#{r:02x}{g:02x}{b:02x}"

def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Converts RGB (0-255) to HSV space.
    H: [0.0, 360.0], S: [0.0, 1.0], V: [0.0, 1.0]
    """
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    c_max = max(r_norm, g_norm, b_norm)
    c_min = min(r_norm, g_norm, b_norm)
    delta = c_max - c_min

    # Hue calculation
    if delta == 0:
        h = 0.0
    elif c_max == r_norm:
        h = (60.0 * ((g_norm - b_norm) / delta) + 360.0) % 360.0
    elif c_max == g_norm:
        h = (60.0 * ((b_norm - r_norm) / delta) + 120.0) % 360.0
    else:
        h = (60.0 * ((r_norm - g_norm) / delta) + 240.0) % 360.0

    # Saturation calculation
    s = 0.0 if c_max == 0 else (delta / c_max)
    
    # Value calculation
    v = c_max

    return h, s, v

def rgb_to_xyz(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Converts RGB (0-255) to CIE XYZ space using standard sRGB matrix formulas."""
    # Pivot RGB values
    var_R = r / 255.0
    var_G = g / 255.0
    var_B = b / 255.0

    if var_R > 0.04045:
        var_R = ((var_R + 0.055) / 1.055) ** 2.4
    else:
        var_R = var_R / 12.92
        
    if var_G > 0.04045:
        var_G = ((var_G + 0.055) / 1.055) ** 2.4
    else:
        var_G = var_G / 12.92
        
    if var_B > 0.04045:
        var_B = ((var_B + 0.055) / 1.055) ** 2.4
    else:
        var_B = var_B / 12.92

    var_R = var_R * 100
    var_G = var_G * 100
    var_B = var_B * 100

    # Observer. = 2°, Illuminant = D65 standard SRGB matrix conversion
    X = var_R * 0.4124 + var_G * 0.3576 + var_B * 0.1805
    Y = var_R * 0.2126 + var_G * 0.7152 + var_B * 0.0722
    Z = var_R * 0.0193 + var_G * 0.1192 + var_B * 0.9505
    return X, Y, Z

def xyz_to_lab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Converts CIE XYZ to CIELAB L*a*b* space using standard D65 reference white points."""
    # Reference white points for D65 observer
    ref_X = 95.047
    ref_Y = 100.000
    ref_Z = 108.883

    var_X = x / ref_X
    var_Y = y / ref_Y
    var_Z = z / ref_Z

    if var_X > 0.008856:
        var_X = var_X ** (1.0/3.0)
    else:
        var_X = (7.787 * var_X) + (16.0 / 116.0)

    if var_Y > 0.008856:
        var_Y = var_Y ** (1.0/3.0)
    else:
        var_Y = (7.787 * var_Y) + (16.0 / 116.0)

    if var_Z > 0.008856:
        var_Z = var_Z ** (1.0/3.0)
    else:
        var_Z = (7.787 * var_Z) + (16.0 / 116.0)

    L = (116.0 * var_Y) - 16.0
    a = 500.0 * (var_X - var_Y)
    b = 200.0 * (var_Y - var_Z)

    return L, a, b

def hex_to_lab(hex_str: str) -> Tuple[float, float, float]:
    """Converts a HEX color directly to CIELAB space."""
    r, g, b = hex_to_rgb(hex_str)
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)

def hex_to_hsv(hex_str: str) -> Tuple[float, float, float]:
    """Converts a HEX color directly to HSV space."""
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hsv(r, g, b)

def cie_delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """
    Computes standard Delta-E (CIE76) Euclidean distance in CIELAB space.
    Delta-E <= 2.3 is considered standard threshold for JND (Just Noticeable Difference).
    """
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2 +
        (lab1[1] - lab2[1]) ** 2 +
        (lab1[2] - lab2[2]) ** 2
    )
