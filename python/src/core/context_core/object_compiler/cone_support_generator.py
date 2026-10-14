import math
from shape_generator import *
from typing import Dict, Any

class ConeSupportGenerator:
    def __init__(self, output_name="conical_support",
                 outer_bottom_radius=1.0, outer_top_radius=0.5, height=2.0,
                 segments=60, height_subdivisions=20,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        """
        Initializes the ConeSupportGenerator as a solid conical support.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            outer_bottom_radius (float): Outer radius at the base.
            outer_top_radius (float): Outer radius at the top.
            height (float): Height of the cone.
            segments (int): Number of subdivisions around circumference.
            height_subdivisions (int): Number of subdivisions along height.
            texture_filename (str): Filename for the texture.
            aesthetics_params (Dict[str, Any], optional): Texture/color info.
            structural_params (Dict[str, Any], optional): Material/physics info.
        """
        # Validation
        if not (outer_bottom_radius > 0 and outer_top_radius >= 0):
            raise ValueError("Outer radii must be positive or zero for top radius.")
        if not (height > 0):
            raise ValueError("Height must be positive.")
        if not (segments >= 3):
            raise ValueError("Segments must be at least 3.")
        if not (height_subdivisions >= 1):
            raise ValueError("Height subdivisions must be at least 1.")

        self.output_name = output_name
        self.outer_bottom_radius = outer_bottom_radius
        self.outer_top_radius = outer_top_radius
        self.height = height
        self.segments = segments
        self.height_subdivisions = height_subdivisions
        self.aesthetics_params = aesthetics_params
        self.structural_params = structural_params

        self.body = None
        self.object_semantic = {}

    def generate_files(self):
        """
        Generates the solid conical support OBJ and MTL files
        by internally setting inner radii to a minimal value.
        """
        solid_inner_radius = 1e-9  # Effectively solid

        print(f"Generating solid conical support '{self.output_name}' with:")
        print(f"  Outer Bottom Radius: {self.outer_bottom_radius}, Outer Top Radius: {self.outer_top_radius}")
        print(f"  Height: {self.height}, Segments: {self.segments}, Height Subdivisions: {self.height_subdivisions}")
        print(f"  Internal Inner Radii (Solid): {solid_inner_radius}")

        self.body = ConeGenerator(
            output_name=self.output_name,
            outer_bottom_radius=self.outer_bottom_radius,
            outer_top_radius=self.outer_top_radius,
            height=self.height,
            inner_bottom_radius=solid_inner_radius,
            inner_top_radius=solid_inner_radius,
            segments=self.segments,
            height_subdivisions=self.height_subdivisions,
            aesthetics_params=self.aesthetics_params,
            structural_params=self.structural_params
        )
        self.body.generate_files()
        self.object_semantic = self.body.object_semantic.copy()

# --- Example Usage ---
if __name__ == "__main__":
    # --- EXAMPLE 1: CARTOON with GRADIENT Texture (Probabilistic Color/Illum) ---
    aesthetics_gradient = {
        "colors": [],  # Empty list triggers probabilistic selection for all 4 sides
        "texture_type": TEXTURE_TYPE["GRADIENT_T"],
        "texture_data": {}
    }

    structural_gradient = {
        "material": MATERIAL_TYPE["CARTOON"],
        "fragility_rate": 3.19,
        "density": 7.48,
        "friction": 0.5, "restitution": 0.5, "absolute_fragility": 0.0,
        "transparency": 1.0  # Opaque material remains opaque
    }

    generator_gradient = ConeSupportGenerator(
        output_name="cartoon_gradient_cone_test",
        outer_bottom_radius=2.0, outer_top_radius=0.1, height=3.0,
        segments=24, height_subdivisions=12,
        aesthetics_params=aesthetics_gradient,
        structural_params=structural_gradient
    )
    generator_gradient.generate_files()

    # --- EXAMPLE 2: GLASS with SOLID Texture (Fixed Color, Applied Transparency) ---
    aesthetics_glass = {
        "colors": ["GREEN", "GREEN", "GREEN", "GREEN"],  # All sides are green
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }

    structural_glass = {
        "material": MATERIAL_TYPE["GLASS"],
        "fragility_rate": 5.0,
        "density": 2.5,
        "friction": 0.1, "restitution": 0.9, "absolute_fragility": 0.0,
        "transparency": 0.35  # Applied: will render as d=0.35 with Illum 6 or 7
    }

    generator_glass = ConeSupportGenerator(
        output_name="glass_transparent_cone_test",
        outer_bottom_radius=1.5, outer_top_radius=0.5, height=2.5,
        segments=16, height_subdivisions=8,
        aesthetics_params=aesthetics_glass,
        structural_params=structural_glass
    )
    generator_glass.generate_files()

    print("\n--- Semantic Data Examples ---")
    print("Example of a face in the out_side: ", generator_glass.object_semantic['out_side'][0])
    print("Example of a face in the in_side: ", generator_glass.object_semantic['in_side'][0])
    print("Example of a face in the top_side: ", generator_glass.object_semantic['top_side'][0])
    print("Example of a face in the bottom_side: ", generator_glass.object_semantic['bottom_side'][0])
    print("Example of a face joint from filer: ",
          generator_glass.body.get_satisfiable_joints(faces=['out_side'], rings=[5], segments=[3]))
