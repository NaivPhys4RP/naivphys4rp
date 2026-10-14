import math
from shape_generator import *


class ConeContainerGenerator:
    def __init__(self, output_name="conical_container",
                 bottom_outer_radius=1.0, top_outer_radius=0.5, height=2.0,
                 wall_thickness=0.1, closed_bottom=False,
                 segments=60, height_subdivisions=20,
                 texture_filename="cone_container_texture.png"):
        """
        Initializes the ConeContainerGenerator.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            bottom_outer_radius (float): The outer radius of the container's base.
            top_outer_radius (float): The outer radius of the container's top.
            height (float): The height of the container.
            wall_thickness (float): The uniform thickness of the container walls.
            closed_bottom (bool): If True, the bottom face will be closed with a solid base.
            segments (int): Number of subdivisions around the circumference.
            height_subdivisions (int): Number of subdivisions along the height.
            texture_filename (str): The filename of the texture image to reference in the .mtl file.
        """
        if not (bottom_outer_radius > 0 and top_outer_radius >= 0):
            raise ValueError("Outer radii must be positive or zero for top radius.")
        if not (height > 0):
            raise ValueError("Height must be positive.")
        if not (wall_thickness > 0 and wall_thickness < min(bottom_outer_radius,
                                                            top_outer_radius) if top_outer_radius > 0 else wall_thickness < bottom_outer_radius):
            raise ValueError(
                "Wall thickness must be positive and less than both outer radii (or only bottom if top is zero).")
        if not (segments >= 3):
            raise ValueError("Segments must be at least 3 for a valid shape.")
        if not (height_subdivisions >= 1):
            raise ValueError("Height subdivisions must be at least 1.")

        self.output_name = output_name
        self.bottom_outer_radius = bottom_outer_radius
        self.top_outer_radius = top_outer_radius
        self.height = height
        self.wall_thickness = wall_thickness
        self.closed_bottom = closed_bottom
        self.segments = segments
        self.height_subdivisions = height_subdivisions
        self.texture_filename = texture_filename
        self.body=None
        self.object_semantic = {}

    def generate_files(self):
        """
        Generates the conical container's OBJ and MTL files by calling ConeGenerator.
        """
        inner_top_radius = 1e-4 if self.closed_bottom else self.top_outer_radius - self.wall_thickness
        inner_bottom_radius = self.bottom_outer_radius - self.wall_thickness

        if self.closed_bottom and inner_top_radius < 0:
            raise ValueError(
                "Cannot create a closed-bottom container with a negative inner top radius. Decrease wall thickness.")

        if not self.closed_bottom and (inner_bottom_radius <= 0 or inner_top_radius < 0):
            raise ValueError(
                "Calculated inner radius is non-positive. Decrease wall_thickness or increase outer radii.")

        self.body = ConeGenerator(
            output_name=self.output_name,
            outer_bottom_radius=self.bottom_outer_radius,
            outer_top_radius=self.top_outer_radius,
            height=self.height,
            inner_bottom_radius=inner_bottom_radius,
            inner_top_radius=inner_top_radius,
            segments=self.segments,
            height_subdivisions=self.height_subdivisions,
            texture_filename=self.texture_filename
        )
        self.body.generate_files()
        self.object_semantic=self.body.object_semantic.copy()


### Main Program


if __name__ == "__main__":
    # Example 1: Generate a standard conical bucket with an open bottom
    print("Generating a conical bucket with an open bottom...")
    open_bucket = ConeContainerGenerator(
        output_name="open_bucket",
        bottom_outer_radius=1.0,
        top_outer_radius=1.0,
        height=1.5,
        wall_thickness=0.05,
        closed_bottom=False,
        segments=4,
        height_subdivisions=15,
        texture_filename="plastic_texture.png"
    )
    open_bucket.generate_files()
    print("\n'open_bucket.obj' and 'open_bucket.mtl' generated.")

    # Example 2: Generate a standard conical bucket with a closed, solid bottom
    print("\n" + "-" * 30 + "\n")
    print("Generating a conical container with a solid base...")
    closed_bucket = ConeContainerGenerator(
        output_name="closed_bucket",
        bottom_outer_radius=1.0,
        top_outer_radius=0.7,
        height=1.5,
        wall_thickness=0.05,
        closed_bottom=False,
        segments=4,
        height_subdivisions=15,
        texture_filename="plastic_texture.png"
    )
    closed_bucket.generate_files()
    print("\n'closed_bucket.obj' and 'closed_bucket.mtl' generated.")

    # Example 3: Generate a closed funnel
    print("\n" + "-" * 30 + "\n")
    print("Generating a closed funnel...")
    closed_funnel = ConeContainerGenerator(
        output_name="closed_funnel",
        bottom_outer_radius=1.2,
        top_outer_radius=0.1,
        height=2.0,
        wall_thickness=0.03,
        closed_bottom=True,
        segments=4,
        height_subdivisions=5,
        texture_filename="metal_texture.png"
    )
    closed_funnel.generate_files()
    print("\n'closed_funnel.obj' and 'closed_funnel.mtl' generated.")