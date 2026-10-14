import random
from typing import Tuple, Dict, List

# --- 1. Color Range Definitions ---
# This dictionary maps a color name to its expected RGB ranges.
# The format is: (R_range, G_range, B_range), where each range is a tuple (min, max).
# For GRAY, WHITE, and BLACK, the ranges are kept tight to ensure color consistency.
COLOR_RANGES: Dict[str, Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]] = {
    "RED": ((200, 255), (0, 50), (0, 50)),
    "ORANGE": ((230, 255), (120, 180), (0, 50)),
    "BROWN": ((130, 160), (60, 90), (10, 40)),
    "YELLOW": ((230, 255), (230, 255), (0, 50)),
    "GREEN": ((0, 50), (150, 255), (0, 50)),
    "BLUE": ((0, 50), (0, 50), (180, 255)),
    "WHITE": ((220, 255), (220, 255), (220, 255)),  # High values for light gray/white
    "GRAY": ((120, 160), (120, 160), (120, 160)),  # Equal ranges for a true gray
    "BLACK": ((0, 30), (0, 30), (0, 30)),  # Very low values for dark gray/black
    "VIOLET": ((150, 200), (0, 50), (150, 200)),
    "PINK": ((255, 255), (150, 200), (150, 200)),  # High Red, lightened G/B
}


# --- 2. Generation Function ---

def get_random_rgb(color_name: str) -> Tuple[int, int, int]:
    """
    Takes a color name, looks up its valid RGB ranges, and returns a
    randomized RGB tuple (R, G, B).

    Args:
        color_name: The name of the color (e.g., "RED"). Case-insensitive.

    Returns:
        A tuple (R, G, B) of integers (0-255), or (0, 0, 0) if the color is not found.
    """
    # Normalize input and look up the ranges
    key = color_name.upper().strip().replace('"', '')
    ranges = COLOR_RANGES.get(key)

    if not ranges:
        print(f"Warning: Color '{color_name}' not found in dictionary. Returning black.")
        return 0, 0, 0

    # Unpack the min/max tuples
    (r_min, r_max), (g_min, g_max), (b_min, b_max) = ranges

    # Generate random values within the defined ranges
    r = random.randint(r_min, r_max)
    g = random.randint(g_min, g_max)
    b = random.randint(b_min, b_max)

    return r, g, b


# --- 3. Example Usage ---

if __name__ == '__main__':
    print("--- Testing Random RGB Generation ---")

    test_colors = list(COLOR_RANGES.keys())

    for color in test_colors:
        rgb_value = get_random_rgb(color)
        print(f"{color.ljust(8)}: {rgb_value}")

    print("\n--- Generating multiple shades of a single color ---")
    for _ in range(5):
        rgb_value = get_random_rgb("GREEN")
        print(f"GREEN shade: {rgb_value}")
