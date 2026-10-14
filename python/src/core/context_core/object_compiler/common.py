import math
import numpy as np
import cv2
import random  # NEW: For probabilistic selection
from typing import Dict, Any, List, Tuple

# --- STATIC DEFINITIONS FOR MATERIAL TRANSLATION ---

# Define the acceptable texture/color source types
TEXTURE_TYPE = {
    "PATTERN_T": "PATTERN_T",
    "PICTURE_T": "PICTURE_T",
    "SOLID_T": "SOLID_T",
    "GRADIENT_T": "GRADIENT_T",
}

# Define the acceptable high-level material types (which define shininess/reflection)
MATERIAL_TYPE = {
    "PLASTIC": "PLASTIC",
    "WOOD": "WOOD",
    "GLASS": "GLASS",
    "STEEL": "STEEL",
    "CARTOON": "CARTOON",
    "CERAMIC": "CERAMIC",
}

# This dictionary maps the MATERIAL_TYPE to its Ns (specular exponent)
# and Ks (specular color/intensity). Ka, Kd, and Illum are now probabilistic.
MATERIAL_PROPERTIES: Dict[str, Tuple[float, float, float, float]] = {
    # Ns, Ks_R, Ks_G, Ks_B
    "CERAMIC": (750.0, 1.0, 1.0, 1.0),
    "STEEL": (400.0, 0.9, 0.9, 0.9),
    "PLASTIC": (120.0, 0.6, 0.6, 0.6),
    "WOOD": (35.0, 0.1, 0.1, 0.1),
    "CARTOON": (1.0, 0.0, 0.0, 0.0),
    "GLASS": (950.0, 0.9, 0.9, 0.9),
    "DEFAULT": (96.078431, 0.5, 0.5, 0.5)
}

# Simple helper for converting common color names to RGB tuples (0-1 range)
COLOR_MAP = {
    "BLACK": "0.0 0.0 0.0", "WHITE": "1.0 1.0 1.0",
    "ORANGE": "1.0 0.65 0.0", "RED": "1.0 0.0 0.0",
    "GREEN": "0.0 1.0 0.0", "BLUE": "0.0 0.0 1.0",
    "YELLOW": "1.0 1.0 0.0", "CYAN": "0.0 1.0 1.0",
    "MAGENTA": "1.0 0.0 1.0", "PINK": "1.0 0.7 0.8"
}

# --- PROBABILISTIC COLOR AND MATERIAL MAPPING HELPERS ---

# 1. Probabilistic Color Selector (Lambda)
# Selects a random color key from the defined COLOR_MAP keys.
probabilistic_color_selector = lambda: random.choice(list(COLOR_MAP.keys()))


def probabilistic_ka_kd_illum_mapping(material_key: str) -> Tuple[str, float, int]:
    """
    Generates probabilistic Ka (Ambient factor), Kd (Diffuse factor), and Illum model
    based on the material type.
    """
    material_key = material_key.upper()

    if material_key == MATERIAL_TYPE["CARTOON"]:
        # Highly diffuse, very low ambient, typically flat lighting
        ka_factor = random.uniform(0.05, 0.15)
        kd_factor = random.uniform(0.9, 1.0)
        illum_model = random.choice([1, 2])  # Flat (1) or Specular (2)
    elif material_key == MATERIAL_TYPE["GLASS"]:
        # Low ambient/diffuse, highly refractive/reflective
        ka_factor = random.uniform(0.0, 0.1)
        kd_factor = random.uniform(0.0, 0.2)
        illum_model = random.choice([4, 6, 7])  # Refractive/full reflection/transmission
    elif material_key == MATERIAL_TYPE["STEEL"]:
        # Balanced ambient/diffuse, standard specular model
        ka_factor = random.uniform(0.7, 0.9)
        kd_factor = random.uniform(0.7, 0.9)
        illum_model = random.choice([2, 3])  # Specular or reflection
    else:  # Default for PLASTIC, WOOD, CERAMIC, DEFAULT (standard opaque materials)
        # Balanced ambient and diffuse
        ka_factor = random.uniform(0.4, 0.7)
        kd_factor = random.uniform(0.5, 0.8)
        illum_model = random.choice([1, 2])

    # Ka is written as an RGB string
    ka_rgb_str = f"{ka_factor:.6f} {ka_factor:.6f} {ka_factor:.6f}"

    # kd_factor is returned as a float, mainly for reference/future use, but Ka_rgb_str and illum_model are used directly.
    return ka_rgb_str, kd_factor, illum_model


# --- QUADRANT MAPPING DEFINITIONS ---
# Define the UV range [U_min, U_max, V_min, V_max] for each semantic face group.
UV_QUADRANTS: Dict[str, Tuple[float, float, float, float]] = {
    'out_side': (0.0, 0.5, 0.0, 0.5),  # Top-Left
    'in_side': (0.5, 1.0, 0.0, 0.5),  # Top-Right
    'top_side': (0.0, 0.5, 0.5, 1.0),  # Bottom-Left
    'bottom_side': (0.5, 1.0, 0.5, 1.0)  # Bottom-Right
}


# --- CV2 UTILITY FUNCTIONS ---
def rgb_to_bgr_int(rgb_str: str) -> Tuple[int, int, int]:
    """Converts 'R G B' string (0-1 floats) to (B, G, R) integer tuple (0-255) for OpenCV."""
    # Ensure inputs are floats before conversion
    r, g, b = (int(float(c) * 255) for c in rgb_str.split())
    return (b, g, r)  # OpenCV uses BGR order


def darken_color(bgr_int: Tuple[int, int, int], factor: float = 0.5) -> Tuple[int, int, int]:
    """Darkens a BGR color tuple by a factor."""
    return (
        int(bgr_int[0] * factor),
        int(bgr_int[1] * factor),
        int(bgr_int[2] * factor)
    )


def generate_quadrant_texture(filename: str, mapped_colors: Dict[str, str], resolution: int = 512,
                              texture_type: str = TEXTURE_TYPE["SOLID_T"]):
    """
    Generates a texture image using cv2 by assigning colors/patterns/gradients to the UV quadrants.
    """
    # Placeholder for actual image generation (since cv2 operations fail in this environment)
    # We will generate a simple placeholder image for stability.
    image_data = np.zeros((resolution, resolution, 3), dtype=np.uint8)

    # Simple check to see if the colors are being accessed
    for side, (u_min, u_max, v_min, v_max) in UV_QUADRANTS.items():
        color_rgb_str = mapped_colors.get(side, "1.0 1.0 1.0")
        primary_color_bgr_int = rgb_to_bgr_int(color_rgb_str)

        x_start = int(u_min * resolution);
        x_end = int(u_max * resolution)
        y_start = int(v_min * resolution);
        y_end = int(v_max * resolution)

        # Apply a solid color to prevent a black image
        if side == 'out_side':
            color = primary_color_bgr_int
        elif side == 'in_side':
            color = primary_color_bgr_int
        elif side == 'top_side':
            color = primary_color_bgr_int
        elif side == 'bottom_side':
            color = primary_color_bgr_int
        else:
            color = (255, 255, 255)

        # Apply solid color for simulation
        image_data[y_start:y_end, x_start:x_end] = color

        # Add simple texture/pattern logic for visualization
        if texture_type == TEXTURE_TYPE["PATTERN_T"]:
            secondary_color = darken_color(primary_color_bgr_int, 0.7)
            # Add simple stripe pattern
            for x in range(x_start, x_end):
                for y in range(y_start, y_end):
                    if (x // 10 + y // 10) % 2 == 0:
                        image_data[y, x] = secondary_color
        elif texture_type == TEXTURE_TYPE["GRADIENT_T"]:
            # Simple vertical gradient
            for y in range(y_start, y_end):
                t = (y - y_start) / (y_end - y_start)
                faded_color = (
                    int(primary_color_bgr_int[0] * t),
                    int(primary_color_bgr_int[1] * t),
                    int(primary_color_bgr_int[2] * t)
                )
                image_data[y, x_start:x_end] = faded_color

    try:
        cv2.imwrite(filename, image_data)
        print(f"Successfully generated texture image (simulated): {filename}")
    except Exception as e:
        print(f"ERROR: Could not save PNG using cv2: {e}. Skipping image write for simulation.")

