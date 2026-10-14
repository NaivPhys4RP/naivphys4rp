import math
import numpy as np
from shape_generator import *


class SphereContainerGenerator:
    def __init__(self, output_name="spherical_container",
                 outer_radius=1.0, wall_thickness=0.1,
                 height_ratio=1.0,  # 0.0 to 2.0, where 1.0 is a hemisphere and 2.0 is a full sphere
                 segments=60, rings=30, texture_filename="container_texture.png"):
        """
        Initializes the SphereContainerGenerator.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            outer_radius (float): The outer radius of the spherical container.
            wall_thickness (float): The thickness of the container walls.
            height_ratio (float): How "tall" the container is, as a ratio of the full hemisphere's height (0.0 to 2.0).
                                  A ratio of 1.0 is a hemisphere, and 2.0 is a full sphere.
            segments (int): Number of subdivisions around the circumference (longitude).
            rings (int): Number of subdivisions vertically (between start and end latitudes).
            texture_filename (str): The filename of the texture image to reference in the .mtl file.
        """
        if not (outer_radius > 0 and wall_thickness > 0 and wall_thickness < outer_radius):
            raise ValueError("Outer radius must be positive, and wall thickness must be positive and less than outer radius.")
        if not (0.0 < height_ratio <= 2.0):
            raise ValueError("Height ratio must be between 0.0 (exclusive) and 2.0 (inclusive).")
        if not (segments >= 3 and rings >= 1):
            raise ValueError("Segments must be at least 3, and rings at least 1.")

        self.output_name = output_name
        self.outer_radius = outer_radius
        self.inner_radius = outer_radius - wall_thickness
        self.height_ratio = height_ratio
        self.segments = segments
        self.rings = rings
        self.texture_filename = texture_filename
        self.body=None
        self.object_semantic = {}

    def generate_files(self):
        """
        Generates the spherical container's OBJ and MTL files by calling SphereGenerator.
        """
        # The start latitude is always at the bottom pole (-90 degrees)
        start_latitude_deg = -90.0

        # The height is determined by the height_ratio * outer_radius.
        # The y-coordinate for the top edge is calculated based on this height.
        # Height of the container = height_ratio * outer_radius.
        # The bottom of the sphere is at y = -outer_radius.
        # The top edge's y-coordinate = -outer_radius + container_height.
        # The maximum height for a full sphere is 2 * outer_radius.
        y_top_edge = -self.outer_radius + (self.height_ratio * self.outer_radius)

        # Clamping y_top_edge to prevent asin domain errors
        y_top_edge_clamped = max(-self.outer_radius, min(y_top_edge, self.outer_radius))

        end_latitude_rad = math.asin(y_top_edge_clamped / self.outer_radius)
        end_latitude_deg = math.degrees(end_latitude_rad)

        print(f"Generating spherical container with outer_radius={self.outer_radius}, inner_radius={self.inner_radius},")
        print(f"start_latitude_deg={start_latitude_deg}, end_latitude_deg={end_latitude_deg}")

        self.body = SphereGenerator(
            output_name=self.output_name,
            outer_radius=self.outer_radius,
            inner_radius=self.inner_radius,
            start_latitude_deg=start_latitude_deg,
            end_latitude_deg=end_latitude_deg,
            segments=self.segments,
            rings=self.rings,
            texture_filename=self.texture_filename
        )
        self.body.generate_files()
        self.object_semantic = self.body.object_semantic.copy()

# Note: The SphereGenerator class is also required for this code to run.
# You will need to place both classes in the same Python file.
if __name__ == "__main__":
    # Example 1: Generate a bowl-like container (a perfect hemisphere)
    print("Generating a bowl-like container...")
    bowl_generator = SphereContainerGenerator(
        output_name="my_bowl",
        outer_radius=2.0,
        wall_thickness=0.1,
        height_ratio=1.5,  # 1.0 means a full hemisphere
        segments=3,       # Increase for smoother edges
        rings=4,
        texture_filename="ceramic_texture.png"
    )
    bowl_generator.generate_files()
    print("\n'my_bowl.obj' and 'my_bowl.mtl' generated.")

    # Example 2: Generate a shallower container (a wide pot)
    print("\n" + "-"*30 + "\n")
    print("Generating a shallower container...")
    shallow_container_generator = SphereContainerGenerator(
        output_name="shallow_container",
        outer_radius=1.5,
        wall_thickness=0.08,
        height_ratio=1, # 70% of a hemisphere's height
        segments=7,
        rings=4,
        texture_filename="metal_texture.png"
    )
    shallow_container_generator.generate_files()
    print("\n'shallow_container.obj' and 'shallow_container.mtl' generated.")

    # Example 3: Generate a deep, cup-like container
    print("\n" + "-"*30 + "\n")
    print("Generating a deep, cup-like container...")
    cup_generator = SphereContainerGenerator(
        output_name="deep_cup",
        outer_radius=1.0,
        wall_thickness=0.05,
        height_ratio=1.9, # 90% of a hemisphere's height
        segments=5,
        rings=4,
        texture_filename="glass_texture.png"
    )
    cup_generator.generate_files()
    print("\n'deep_cup.obj' and 'deep_cup.mtl' generated.")