import math
from typing import Dict, Any
from shape_generator import TorusGenerator
from common import TEXTURE_TYPE, MATERIAL_TYPE

class TorusSupportGenerator:
    def __init__(self,
                 output_name="solid_torus",
                 major_radius=3.0,
                 minor_radius=0.5,
                 arc_degrees=270,
                 major_segments=24,
                 minor_segments=12,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        """
        Solid Torus Support Generator.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            major_radius (float): Radius of the torus’ main circle.
            minor_radius (float): Radius of the torus tube.
            arc_degrees (float): Arc span (0 < arc <= 360).
            major_segments (int): Segments along major circle.
            minor_segments (int): Segments along tube cross-section.
            aesthetics_params (dict, optional): Texture/color info.
            structural_params (dict, optional): Material/physics info.
        """
        if not (major_radius > 0 and minor_radius > 0):
            raise ValueError("Major and minor radii must be positive.")
        if not (major_segments >= 3 and minor_segments >= 3):
            raise ValueError("Segments must be at least 3.")
        if not (0 < arc_degrees <= 360):
            raise ValueError("Arc degrees must be between 0 and 360.")

        self.output_name = output_name
        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.arc_degrees = arc_degrees
        self.major_segments = major_segments
        self.minor_segments = minor_segments
        self.aesthetics_params = aesthetics_params
        self.structural_params = structural_params

        self.body = None
        self.object_semantic = {}

    def generate_files(self):
        """
        Generates the solid torus OBJ and MTL files by forcing a very small inner radius.
        """
        solid_inner_radius = 1e-9  # Effectively solid

        print(f"Generating solid torus '{self.output_name}' with:")
        print(f"  Major Radius: {self.major_radius}, Minor Radius: {self.minor_radius}")
        print(f"  Arc Degrees: {self.arc_degrees}")
        print(f"  Major Segments: {self.major_segments}, Minor Segments: {self.minor_segments}")
        print(f"  Internal Inner Radius (Solid): {solid_inner_radius}")

        self.body = TorusGenerator(
            output_name=self.output_name,
            major_radius=self.major_radius,
            minor_radius=self.minor_radius,
            inner_radius=solid_inner_radius,
            arc_degrees=self.arc_degrees,
            major_segments=self.major_segments,
            minor_segments=self.minor_segments,
            aesthetics_params=self.aesthetics_params,
            structural_params=self.structural_params
        )

        self.body.generate_files()
        self.object_semantic = self.body.object_semantic.copy()


# --- Example Usage ---
if __name__ == "__main__":
    # Solid steel torus with gradient texture
    aesthetics_steel = {
        "colors": ["BLUE", "YELLOW", "RED"],
        "texture_type": TEXTURE_TYPE["GRADIENT_T"],
        "texture_data": {}
    }
    structural_steel = {
        "material": MATERIAL_TYPE["STEEL"],
        "fragility_rate": 0.5,
        "density": 7.8,
        "friction": 0.3, "restitution": 0.2, "absolute_fragility": 0.0,
        "transparency": 1.0
    }

    torus_steel_support = TorusSupportGenerator(
        output_name="steel_solid_torus",
        major_radius=2.0,
        minor_radius=0.5,
        arc_degrees=180,
        major_segments=24,
        minor_segments=12,
        aesthetics_params=aesthetics_steel,
        structural_params=structural_steel
    )
    torus_steel_support.generate_files()

    # Solid glass torus with solid color
    aesthetics_glass = {
        "colors": ["GREEN"],
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }
    structural_glass = {
        "material": MATERIAL_TYPE["GLASS"],
        "fragility_rate": 5.0,
        "density": 2.5,
        "friction": 0.1, "restitution": 0.9, "absolute_fragility": 0.0,
        "transparency": 0.2
    }

    torus_glass_support = TorusSupportGenerator(
        output_name="glass_solid_torus",
        major_radius=1.8,
        minor_radius=0.4,
        major_segments=20,
        minor_segments=10,
        aesthetics_params=aesthetics_glass,
        structural_params=structural_glass
    )
    torus_glass_support.generate_files()
