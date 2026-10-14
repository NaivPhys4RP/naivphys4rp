import math
import numpy as np
from shape_generator import * # Assuming SphereGenerator is available via this import
from typing import Dict, Any, List, Tuple

# Import shared variables from common.py
from common import TEXTURE_TYPE, MATERIAL_TYPE

# New Class: SphereSupportGenerator
class SphereSupportGenerator:
    def __init__(self, output_name="spherical_support",
                 outer_radius=1.0,
                 segments=60, rings=30,
                 start_latitude_deg=-60.0, end_latitude_deg=30.0,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        """
        Initializes the SphereSupportGenerator. This class generates a SOLID spherical
        section (a support) by setting the inner_radius to a near-zero value internally
        and passing all other required parameters to the SphereGenerator.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            outer_radius (float): The maximum outer radius of the spherical support.
            segments (int): Number of subdivisions around the circumference (longitude).
            rings (int): Number of subdivisions vertically (between start and end latitudes).
            start_latitude_deg (float): The bottom latitude of the support in degrees (-90 to 90).
            end_latitude_deg (float): The top latitude of the support in degrees (between -90 and 90).
                                      Must be > start_latitude_deg.
            aesthetics_params (Dict[str, Any], optional): Parameters controlling color/texture.
                                                        (e.g., {"colors": ["RED"], "texture_type": TEXTURE_TYPE["SOLID_T"]}).
            structural_params (Dict[str, Any], optional): Parameters controlling material type, density, etc.
                                                        (e.g., {"material": MATERIAL_TYPE["WOOD"], "transparency": 0.5}).
        """
        # Validate inputs
        if not (outer_radius > 0):
            raise ValueError("Outer radius must be positive.")
        if not (-90 <= start_latitude_deg < end_latitude_deg <= 90):
            raise ValueError("Invalid latitude range. Must be -90 <= start_lat < end_lat <= 90.")
        if not (segments >= 3 and rings >= 1):
            raise ValueError("Segments must be at least 3, and rings at least 1.")

        self.output_name = output_name
        self.outer_radius = outer_radius
        self.segments = segments
        self.rings = rings

        # Store parameters required by SphereGenerator
        self.start_latitude_deg = start_latitude_deg
        self.end_latitude_deg = end_latitude_deg
        self.aesthetics_params = aesthetics_params
        self.structural_params = structural_params

        self.body = None
        self.object_semantic = {}

    def generate_files(self):
        """
        Generates the spherical support's OBJ and MTL files by calling SphereGenerator.
        The inner radius is set to a minimal value (1e-9) to create a solid object.
        """
        # Set inner_radius to a very small value to make it effectively solid
        solid_inner_radius = 1e-9

        print(f"Generating spherical support '{self.output_name}' with:")
        print(f"  Latitude Range: {self.start_latitude_deg:.2f} to {self.end_latitude_deg:.2f} deg")
        print(f"  Outer Radius: {self.outer_radius:.2f}")
        print(f"  Segments: {self.segments}, Rings: {self.rings}")
        print(f"  Internal Inner Radius (Solid): {solid_inner_radius}")


        self.body = SphereGenerator(
            output_name=self.output_name,
            outer_radius=self.outer_radius,
            inner_radius=solid_inner_radius,  # CRITICAL: Forces the object to be solid
            start_latitude_deg=self.start_latitude_deg,
            end_latitude_deg=self.end_latitude_deg,
            segments=self.segments,
            rings=self.rings,
            aesthetics_params=self.aesthetics_params, # Pass through
            structural_params=self.structural_params  # Pass through
        )
        self.body.generate_files()
        self.object_semantic = self.body.object_semantic.copy()

if __name__ == "__main__":
    # --- Shared Aesthetic Parameters for all examples ---
    aesthetics_solid = {
        "colors": ["BLUE"],
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }

    # --- Example 1: Standard (Opaque Wood) Support ---
    structural_wood = {
        "material": MATERIAL_TYPE["WOOD"],
        "fragility_rate": 1.0,
        "density": 1.0,
        "friction": 0.5, "restitution": 0.5, "absolute_fragility": 0.0,
        "transparency": 0.0 # Opaque
    }
    print("--- Example 1: Opaque Wood Support ---")
    try:
        wood_support = SphereSupportGenerator(
            output_name="wood_support_base",
            outer_radius=1.5,
            start_latitude_deg=0,
            end_latitude_deg=60,
            structural_params=structural_wood,
            aesthetics_params=aesthetics_solid
        )
        wood_support.generate_files()
        print("Model setup successful: wood_support_base (Material: Wood).")
    except NameError:
        print("Skipping Example 1: SphereGenerator not found.")

    # --- Example 2: Highly Transparent (Glass) Support ---
    structural_transparent = {
        "material": MATERIAL_TYPE["GLASS"],
        "fragility_rate": 0.2,
        "density": 2.5,
        "friction": 0.1, "restitution": 0.9, "absolute_fragility": 0.0,
        "transparency": 0.8 # CRITICAL: Sets high transparency
    }
    print("\n--- Example 2: Highly Transparent Glass Support ---")
    try:
        glass_support = SphereSupportGenerator(
            output_name="glass_support_pedestal",
            outer_radius=0.8,
            start_latitude_deg=-90,
            end_latitude_deg=45,
            segments=16,
            rings=8,
            structural_params=structural_transparent,
            aesthetics_params={
                "colors": ["CYAN"], # Color applied to the transparent material
                "texture_type": TEXTURE_TYPE["SOLID_T"],
                "texture_data": {}
            }
        )
        glass_support.generate_files()
        print("Model setup successful: glass_support_pedestal (Material: Glass, Transparency: 0.8).")
    except NameError:
        print("Skipping Example 2: SphereGenerator not found.")


    # --- Example 3: Very Shiny (Steel) Support ---
    # STEEL has a high Ns (specular exponent) defined in common.py, making it very reflective/shiny.
    structural_shiny = {
        "material": MATERIAL_TYPE["STEEL"],
        "fragility_rate": 0.8,
        "density": 7.8,
        "friction": 0.6, "restitution": 0.3, "absolute_fragility": 0.0,
        "transparency": 0.0 # Opaque
    }
    print("\n--- Example 3: Very Shiny Steel Support ---")
    try:
        shiny_support = SphereSupportGenerator(
            output_name="shiny_steel_disc",
            outer_radius=2.5,
            start_latitude_deg=-10,
            end_latitude_deg=10, # Flatter disc shape
            segments=60,
            rings=2,
            structural_params=structural_shiny,
            aesthetics_params={
                "colors": ["WHITE"], # White/Gray for metallic look
                "texture_type": TEXTURE_TYPE["SOLID_T"],
                "texture_data": {}
            }
        )
        shiny_support.generate_files()
        print("Model setup successful: shiny_steel_disc (Material: Steel, High Specularity).")
    except NameError:
        print("Skipping Example 3: SphereGenerator not found.")
