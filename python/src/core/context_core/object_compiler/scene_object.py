import math
import numpy as np
# Assuming the previous generator classes are available from this module
from container_and_support_generators import ConeContainerGenerator, SphereContainerGenerator, ConeSupportGenerator


class MugGenerator:
    def __init__(self, output_name="mug", height=1.0, diameter=0.8, wall_thickness=0.05, segments=50, rings=20):
        """
        Generates the components for a classic cylindrical mug (body and base).

        Args:
            output_name (str): Base name for the output files (e.g., 'mug_body.obj', 'mug_base.obj').
            height (float): The total height of the mug body.
            diameter (float): The outer diameter of the mug.
            wall_thickness (float): The thickness of the mug walls.
            segments (int): Number of subdivisions around the circumference.
            rings (int): Number of subdivisions along the height/rings.
        """
        self.output_name = output_name
        radius = diameter / 2.0
        base_height = 0.05  # A small height for the solid base

        # 1. Main Mug Body (Hollow Cylinder, Open Top, Closed Bottom enforced by wall thickness calculation)
        self.body = ConeContainerGenerator(
            output_name=f"{output_name}_body",
            bottom_outer_radius=radius,
            top_outer_radius=radius,
            height=height,
            wall_thickness=wall_thickness,
            closed_bottom=True,  # Near-solid closure at the bottom
            segments=segments,
            height_subdivisions=rings,
            texture_filename="ceramic_texture.png"
        )
        # 2. Mug Base (Solid Disc/Cylinder)
        self.base = ConeSupportGenerator(
            output_name=f"{output_name}_base",
            bottom_outer_radius=radius + wall_thickness * 0.5,  # Slightly wider base for stability
            top_outer_radius=radius + wall_thickness * 0.5,
            height=base_height,
            segments=segments,
            height_subdivisions=5,
            texture_filename="ceramic_texture.png"
        )
        # Note: A handle would require more complex shape generation (e.g., Torus or custom curve)
        # and merging is left to the user's PyMesh logic.

    def generate_files(self):
        """Generates the component OBJ files."""
        print(f"Generating components for {self.output_name}...")
        self.body.generate_files()
        self.base.generate_files()
        print(f"Mug components generated: {self.output_name}_body.obj and {self.output_name}_base.obj.")


class PlateGenerator:
    def __init__(self, output_name="plate", diameter=3.0, wall_thickness=0.04, segments=60, rings=5):
        """
        Generates a flat plate with a slightly curved edge using a shallow Sphere Container.

        Args:
            output_name (str): Base name for the output file.
            diameter (float): The outer diameter of the plate.
            wall_thickness (float): The thickness of the plate material.
            segments (int): Number of subdivisions around the circumference.
            rings (int): Number of subdivisions vertically.
        """
        self.output_name = output_name
        outer_radius = diameter / 2.0

        # Use a very shallow section of a large sphere to create a flat, subtle curve.
        # height_ratio = 0.1 means 10% of a hemisphere's height, making it very flat.
        self.plate = SphereContainerGenerator(
            output_name=output_name,
            outer_radius=outer_radius * 2,  # Use a larger virtual sphere to get a flatter curve
            wall_thickness=wall_thickness,
            height_ratio=0.1,
            segments=segments,
            rings=rings,
            texture_filename="porcelain_texture.png"
        )

    def generate_files(self):
        """Generates the plate OBJ file."""
        print(f"Generating plate {self.output_name}...")
        self.plate.generate_files()
        print(f"Plate generated: {self.output_name}.obj.")


class BottleGenerator:
    def __init__(self, output_name="bottle", base_diameter=1.0, neck_diameter=0.3, height=3.0, wall_thickness=0.04,
                 segments=60):
        """
        Generates the components for a bottle shape (base, body, neck).

        Args:
            output_name (str): Base name for the output files.
            base_diameter (float): The maximum diameter of the bottle body.
            neck_diameter (float): The diameter of the bottle neck opening.
            height (float): The total height of the bottle (excluding the base curve).
            wall_thickness (float): The thickness of the bottle walls.
            segments (int): Number of subdivisions around the circumference.
        """
        self.output_name = output_name
        base_radius = base_diameter / 2.0
        neck_radius = neck_diameter / 2.0

        body_height = height * 0.6
        neck_transition_height = height * 0.2
        neck_height = height * 0.2

        # 1. Bottle Body (Truncated Cone, Tapers from base diameter to neck transition diameter)
        self.body = ConeContainerGenerator(
            output_name=f"{output_name}_body",
            bottom_outer_radius=base_radius,
            top_outer_radius=base_radius,  # Keep body same width
            height=body_height,
            wall_thickness=wall_thickness,
            closed_bottom=True,
            segments=segments,
            height_subdivisions=int(body_height * 10),
            texture_filename="glass_texture.png"
        )

        # 2. Neck Transition (Tapers from body width to neck width)
        self.transition = ConeContainerGenerator(
            output_name=f"{output_name}_transition",
            bottom_outer_radius=base_radius,
            top_outer_radius=neck_radius * 1.5,  # Slightly wider than neck
            height=neck_transition_height,
            wall_thickness=wall_thickness,
            closed_bottom=False,  # Open tube
            segments=segments,
            height_subdivisions=int(neck_transition_height * 10),
            texture_filename="glass_texture.png"
        )

        # 3. Bottle Neck (Cylindrical and Hollow, Open Top/Bottom)
        self.neck = ConeContainerGenerator(
            output_name=f"{output_name}_neck",
            bottom_outer_radius=neck_radius,
            top_outer_radius=neck_radius,
            height=neck_height,
            wall_thickness=wall_thickness,
            closed_bottom=False,  # Open tube
            segments=segments,
            height_subdivisions=int(neck_height * 10),
            texture_filename="glass_texture.png"
        )

    def generate_files(self):
        """Generates the component OBJ files."""
        print(f"Generating components for {self.output_name}...")
        self.body.generate_files()
        self.transition.generate_files()
        self.neck.generate_files()
        print("Bottle components generated: body, transition, and neck .obj files.")


class FunnelGenerator:
    def __init__(self, output_name="funnel", top_diameter=2.0, spout_diameter=0.2, height=2.5, wall_thickness=0.03,
                 segments=40):
        """
        Generates a conical funnel shape.

        Args:
            output_name (str): Base name for the output file.
            top_diameter (float): The diameter of the top opening.
            spout_diameter (float): The diameter of the bottom spout opening.
            height (float): The height of the funnel.
            wall_thickness (float): The thickness of the funnel walls.
            segments (int): Number of subdivisions around the circumference.
        """
        self.output_name = output_name
        top_radius = top_diameter / 2.0
        spout_radius = spout_diameter / 2.0

        # Use ConeContainerGenerator with a large top radius and small bottom radius
        self.funnel = ConeContainerGenerator(
            output_name=output_name,
            bottom_outer_radius=spout_radius,
            top_outer_radius=top_radius,
            height=height,
            wall_thickness=wall_thickness,
            closed_bottom=False,  # Keep both ends open
            segments=segments,
            height_subdivisions=int(height * 8),
            texture_filename="metal_texture.png"
        )

    def generate_files(self):
        """Generates the funnel OBJ file."""
        print(f"Generating funnel {self.output_name}...")
        self.funnel.generate_files()
        print(f"Funnel generated: {self.output_name}.obj.")


if __name__ == "__main__":
    print("=" * 50)
    print("--- Defining and Generating Complex Object Components ---")
    print("=" * 50)

    # 1. Generate Mug Components
    my_mug = MugGenerator(output_name="classic_mug", height=1.2, diameter=0.9)
    my_mug.generate_files()

    print("\n" + "-" * 30 + "\n")

    # 2. Generate Plate Component
    my_plate = PlateGenerator(output_name="dinner_plate", diameter=4.0)
    my_plate.generate_files()

    print("\n" + "-" * 30 + "\n")

    # 3. Generate Bottle Components
    my_bottle = BottleGenerator(output_name="tall_bottle", base_diameter=1.0, neck_diameter=0.3, height=3.5)
    my_bottle.generate_files()

    print("\n" + "-" * 30 + "\n")

    # 4. Generate Funnel Component
    my_funnel = FunnelGenerator(output_name="lab_funnel")
    my_funnel.generate_files()

    print(
        "\nTo assemble these objects, use your PyMesh script to merge the component files (e.g., 'classic_mug_body.obj' and 'classic_mug_base.obj') using the calculated face IDs.")
    print("=" * 50)
