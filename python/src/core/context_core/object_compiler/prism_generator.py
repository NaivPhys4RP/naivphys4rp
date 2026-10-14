#!/usr/bin/env python3

import math

class PrismGenerator:
    def __init__(self, output_name="textured_hollow_triangular_prism",
                 outer_base_side=2.0, outer_height=3.0,
                 base_wall_thickness=0.2, # Thickness of the walls along the base side (horizontal inset)
                 apex_wall_thickness=0.3, # Thickness of the wall at the apex (vertical offset for top)
                 bottom_wall_thickness=0.1, # Thickness of the bottom face (vertical offset for base)
                 depth=1.0, # The "thickness" of the prism along its length
                 texture_filename="triangular_prism_texture.png"):
        """
        Initializes the PrismGenerator to create a hollow triangular prism with specified wall thicknesses.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            outer_base_side (float): Side length of the outer prism's equilateral triangle base.
            outer_height (float): Height of the outer prism's equilateral triangle base (apex to base).
            base_wall_thickness (float): The horizontal thickness of the side walls near the base.
                                         The inner base side will be outer_base_side - 2 * base_wall_thickness.
            apex_wall_thickness (float): The vertical thickness of the top wall at the apex.
                                           The inner apex's Y-coordinate will be outer_height - apex_wall_thickness.
            bottom_wall_thickness (float): The vertical thickness of the bottom wall.
                                            The inner base's Y-coordinate will be bottom_wall_thickness.
            depth (float): The depth (length) of the prism along the Z-axis.
            texture_filename (str): The filename of the texture image to reference in the .mtl file.
        """
        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"
        self.texture_filename = texture_filename

        self.outer_base_side = outer_base_side
        self.outer_height = outer_height
        self.depth = depth
        self.base_wall_thickness = base_wall_thickness
        self.apex_wall_thickness = apex_wall_thickness
        self.bottom_wall_thickness = bottom_wall_thickness

        # Calculate inner dimensions based on outer dimensions and wall thicknesses
        self.inner_base_side = self.outer_base_side - 2 * self.base_wall_thickness
        self.inner_apex_y = self.outer_height - self.apex_wall_thickness
        self.inner_base_y = self.bottom_wall_thickness

        # Validate dimensions
        if not (self.inner_base_side > 0):
            raise ValueError(f"Calculated inner base side ({self.inner_base_side:.2f}) must be positive. "
                             f"Reduce base_wall_thickness (current: {base_wall_thickness:.2f}).")
        if not (self.inner_apex_y > self.inner_base_y):
            raise ValueError(f"Calculated inner apex Y ({self.inner_apex_y:.2f}) must be greater than "
                             f"inner base Y ({self.inner_base_y:.2f}). Adjust apex_wall_thickness or bottom_wall_thickness.")
        if not (self.base_wall_thickness > 0):
            raise ValueError("Base wall thickness must be positive.")
        if not (self.apex_wall_thickness > 0):
            raise ValueError("Apex wall thickness must be positive.")
        if not (self.bottom_wall_thickness > 0):
            raise ValueError("Bottom wall thickness must be positive.")
        if not (self.depth > 0):
            raise ValueError("Depth must be positive.")

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

    def _normalize_vector(self, vec):
        """Normalizes a 3D vector."""
        magnitude = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
        if magnitude == 0:
            return [0.0, 0.0, 0.0] # Avoid division by zero
        return [c / magnitude for c in vec]

    def _cross_product(self, v1, v2):
        """Calculates the cross product of two 3D vectors."""
        return [
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0]
        ]

    def _vector_sub(self, v1, v2):
        """Subtracts two 3D vectors."""
        return [v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]]

    def _generate_geometry(self):
        """
        Generates the vertices, texture coordinates, normals, and faces for the hollow triangular prism.
        All normal vectors are set to ensure all faces are visible (outward for outer, inward for inner).
        """
        # Clear previous geometry to allow multiple calls if needed (e.g., for testing)
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

        # Helper to add vertex, normal, and UV indices to a face tuple (for OBJ 1-based indexing)
        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        outer_half_base = self.outer_base_side / 2.0
        inner_half_base = self.inner_base_side / 2.0

        # --- Generate Vertices ---
        # Outer Prism Vertices (6 vertices: 3 at front, 3 at back)
        # Front face (Z = -depth/2)
        # v0: Outer Front Apex
        self._vertices.append([0.0, self.outer_height, -self.depth / 2.0])
        # v1: Outer Front Base Left
        self._vertices.append([-outer_half_base, 0.0, -self.depth / 2.0])
        # v2: Outer Front Base Right
        self._vertices.append([ outer_half_base, 0.0, -self.depth / 2.0])

        # Back face (Z = depth/2)
        # v3: Outer Back Apex
        self._vertices.append([0.0, self.outer_height, self.depth / 2.0])
        # v4: Outer Back Base Left
        self._vertices.append([-outer_half_base, 0.0, self.depth / 2.0])
        # v5: Outer Back Base Right
        self._vertices.append([ outer_half_base, 0.0, self.depth / 2.0])

        # Inner Prism Vertices (6 vertices: 3 at front, 3 at back)
        # Front face (Z = -depth/2)
        # v6: Inner Front Apex
        self._vertices.append([0.0, self.inner_apex_y, -self.depth / 2.0])
        # v7: Inner Front Base Left
        self._vertices.append([-inner_half_base, self.inner_base_y, -self.depth / 2.0])
        # v8: Inner Front Base Right
        self._vertices.append([ inner_half_base, self.inner_base_y, -self.depth / 2.0])

        # Back face (Z = depth/2)
        # v9: Inner Back Apex
        self._vertices.append([0.0, self.inner_apex_y, self.depth / 2.0])
        # v10: Inner Back Base Left
        self._vertices.append([-inner_half_base, self.inner_base_y, self.depth / 2.0])
        # v11: Inner Back Base Right
        self._vertices.append([ inner_half_base, self.inner_base_y, self.depth / 2.0])

        # --- Define Vertex Index Constants for Clarity (0-based) ---
        # Outer Vertices
        V_OUTER_FRONT_APEX = 0
        V_OUTER_FRONT_BL = 1
        V_OUTER_FRONT_BR = 2
        V_OUTER_BACK_APEX = 3
        V_OUTER_BACK_BL = 4
        V_OUTER_BACK_BR = 5

        # Inner Vertices
        V_INNER_FRONT_APEX = 6
        V_INNER_FRONT_BL = 7
        V_INNER_FRONT_BR = 8
        V_INNER_BACK_APEX = 9
        V_INNER_BACK_BL = 10
        V_INNER_BACK_BR = 11

        # --- Generate Normals ---
        # Helper to negate a vector
        def negate_vector(vec):
            return [-c for c in vec]

        # 1. Normals for Outer Side Faces (3 normals, calculated per face)
        # These are set to point OUTWARD for proper visibility.

        # Normal for Outer Left Slanted Face (V0, V1, V4, V3) (Apex to Base-Left Edge)
        vec_v0_v1 = self._vector_sub(self._vertices[V_OUTER_FRONT_BL], self._vertices[V_OUTER_FRONT_APEX])
        vec_v0_v3 = self._vector_sub(self._vertices[V_OUTER_BACK_APEX], self._vertices[V_OUTER_FRONT_APEX])
        normal_outer_left_slanted = self._normalize_vector(self._cross_product(vec_v0_v3, vec_v0_v1))
        self._normals.append(negate_vector(normal_outer_left_slanted)) # n0: Outer Left Slanted Normal (OUTWARD)

        # Normal for Outer Right Slanted Face (V0, V2, V5, V3) (Apex to Base-Right Edge)
        vec_v0_v2 = self._vector_sub(self._vertices[V_OUTER_FRONT_BR], self._vertices[V_OUTER_FRONT_APEX])
        normal_outer_right_slanted = self._normalize_vector(self._cross_product(vec_v0_v2, vec_v0_v3))
        self._normals.append(negate_vector(normal_outer_right_slanted)) # n1: Outer Right Slanted Normal (OUTWARD)

        # Normal for Outer Bottom Face (V1, V2, V5, V4)
        vec_v1_v2 = self._vector_sub(self._vertices[V_OUTER_FRONT_BR], self._vertices[V_OUTER_FRONT_BL])
        vec_v1_v4 = self._vector_sub(self._vertices[V_OUTER_BACK_BL], self._vertices[V_OUTER_FRONT_BL])
        normal_outer_bottom = self._normalize_vector(self._cross_product(vec_v1_v2, vec_v1_v4))
        # This normal points downward, which is desired for outer bottom.
        self._normals.append(normal_outer_bottom) # n2: Outer Bottom Normal (DOWNWARD)

        # 2. Normals for Inner Side Faces (3 normals)
        # These are set to point INWARD towards the hollow for proper visibility.

        # Normal for Inner Left Slanted Face (V6, V7, V10, V9)
        vec_v6_v7 = self._vector_sub(self._vertices[V_INNER_FRONT_BL], self._vertices[V_INNER_FRONT_APEX])
        vec_v6_v9 = self._vector_sub(self._vertices[V_INNER_BACK_APEX], self._vertices[V_INNER_FRONT_APEX])
        normal_inner_left_slanted = self._normalize_vector(self._cross_product(vec_v6_v7, vec_v6_v9))
        self._normals.append(negate_vector(normal_inner_left_slanted)) # n3: Inner Left Slanted Normal (INWARD to hollow)

        # Normal for Inner Right Slanted Face (V6, V8, V11, V9)
        vec_v6_v8 = self._vector_sub(self._vertices[V_INNER_FRONT_BR], self._vertices[V_INNER_FRONT_APEX])
        normal_inner_right_slanted = self._normalize_vector(self._cross_product(vec_v6_v9, vec_v6_v8))
        self._normals.append(negate_vector(normal_inner_right_slanted)) # n4: Inner Right Slanted Normal (INWARD to hollow)

        # Normal for Inner Bottom Face (V7, V8, V11, V10)
        # Cross product of (V10-V7) and (V8-V7) gives an upward normal.
        vec_v7_v8 = self._vector_sub(self._vertices[V_INNER_FRONT_BR], self._vertices[V_INNER_FRONT_BL])
        vec_v7_v10 = self._vector_sub(self._vertices[V_INNER_BACK_BL], self._vertices[V_INNER_FRONT_BL])
        normal_inner_bottom = self._normalize_vector(self._cross_product(vec_v7_v10, vec_v7_v8))
        # !!! FINAL CORRECTION: Negate the normal to point DOWNWARD and reverse the winding for consistency.
        self._normals.append(negate_vector(normal_inner_bottom)) # n5: Inner Bottom Normal (DOWNWARD)

        # 3. Normals for Cap Faces (2 fixed normals for front/back)
        # These are now explicitly set to point OUTWARD from the prism's front/back.
        self._normals.append([0.0, 0.0, -1.0]) # n6: Front Cap Normal (points -Z, OUTWARD from front)
        self._normals.append([0.0, 0.0, 1.0])  # n7: Back Cap Normal (points +Z, OUTWARD from back)


        # --- Define UVs ---
        # Standard UVs for a quad (used for all rectangular faces)
        self._texture_coords.append([0.0, 0.0]) # 0: BL
        self._texture_coords.append([1.0, 0.0]) # 1: BR
        self._texture_coords.append([1.0, 1.0]) # 2: TR
        self._texture_coords.append([0.0, 1.0]) # 3: TL

        # UVs for triangular caps (full texture on each triangle)
        self._texture_coords.append([0.5, 1.0]) # 4: Apex
        self._texture_coords.append([0.0, 0.0]) # 5: Base Left
        self._texture_coords.append([1.0, 0.0]) # 6: Base Right


        # --- Define UV Index Constants for Clarity (0-based) ---
        UV_QUAD_BL = 0
        UV_QUAD_BR = 1
        UV_QUAD_TR = 2
        UV_QUAD_TL = 3

        UV_TRI_APEX = 4
        UV_TRI_BASE_L = 5
        UV_TRI_BASE_R = 6


        # --- Generate Faces ---
        # All indices are 1-based for .obj file.
        # Format: (v_idx, vt_idx, vn_idx)
        # Winding orders need to be adjusted based on the normal directions to ensure visibility.

        # 1. Outer Prism Side Faces (3 rectangular quads)
        # Normals for n0, n1 are OUTWARD. Faces need CCW winding when viewed from outside.
        # Normal for n2 is DOWNWARD. Faces need CCW winding when viewed from below.

        # Outer Left Slanted Face (V0, V1, V4, V3)
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_APEX, UV_QUAD_TL, 0),
            add_face_vertex(V_OUTER_FRONT_BL, UV_QUAD_BL, 0),
            add_face_vertex(V_OUTER_BACK_BL, UV_QUAD_BR, 0),
            add_face_vertex(V_OUTER_BACK_APEX, UV_QUAD_TR, 0)
        ])
        # Outer Right Slanted Face (V0, V2, V5, V3)
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_APEX, UV_QUAD_TL, 1),
            add_face_vertex(V_OUTER_BACK_APEX, UV_QUAD_TR, 1),
            add_face_vertex(V_OUTER_BACK_BR, UV_QUAD_BR, 1),
            add_face_vertex(V_OUTER_FRONT_BR, UV_QUAD_BL, 1)
        ])
        # Outer Bottom Face (V1, V2, V5, V4)
        # Normal is DOWNWARD. Faces need CCW winding when viewed from below.
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_BL, UV_QUAD_BL, 2),
            add_face_vertex(V_OUTER_FRONT_BR, UV_QUAD_BR, 2),
            add_face_vertex(V_OUTER_BACK_BR, UV_QUAD_TR, 2),
            add_face_vertex(V_OUTER_BACK_BL, UV_QUAD_TL, 2)
        ])

        # 2. Inner Prism Side Faces (3 rectangular quads)
        # Normals for n3, n4 are INWARD. Faces need CCW winding when viewed from inside the hollow.
        # Normal for n5 is DOWNWARD. This face must now be wound CLOCKWISE when viewed from above to be consistent.

        # Inner Left Slanted Face (V6, V7, V10, V9)
        self._faces.append([
            add_face_vertex(V_INNER_FRONT_APEX, UV_QUAD_TL, 3),
            add_face_vertex(V_INNER_BACK_APEX, UV_QUAD_TR, 3),
            add_face_vertex(V_INNER_BACK_BL, UV_QUAD_BR, 3),
            add_face_vertex(V_INNER_FRONT_BL, UV_QUAD_BL, 3)
        ])
        # Inner Right Slanted Face (V6, V8, V11, V9)
        self._faces.append([
            add_face_vertex(V_INNER_FRONT_APEX, UV_QUAD_TL, 4),
            add_face_vertex(V_INNER_FRONT_BR, UV_QUAD_BL, 4),
            add_face_vertex(V_INNER_BACK_BR, UV_QUAD_BR, 4),
            add_face_vertex(V_INNER_BACK_APEX, UV_QUAD_TR, 4)
        ])
        # Inner Bottom Face (V7, V8, V11, V10)
        # !!! FINAL CORRECTION: Normal n5 is DOWNWARD. Winding is now REVERSED to be CLOCKWISE when viewed from above.
        self._faces.append([
            add_face_vertex(V_INNER_FRONT_BL, UV_QUAD_BL, 5),
            add_face_vertex(V_INNER_BACK_BL, UV_QUAD_TL, 5),
            add_face_vertex(V_INNER_BACK_BR, UV_QUAD_TR, 5),
            add_face_vertex(V_INNER_FRONT_BR, UV_QUAD_BR, 5)
        ])

        # 3. Front Cap Faces (connecting outer front to inner front) (3 quads)
        # Normal for front cap (n6) points -Z (OUTWARD from front).
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_APEX, UV_QUAD_TL, 6),
            add_face_vertex(V_OUTER_FRONT_BR, UV_QUAD_BL, 6),
            add_face_vertex(V_INNER_FRONT_BR, UV_QUAD_BR, 6),
            add_face_vertex(V_INNER_FRONT_APEX, UV_QUAD_TR, 6)
        ])
        # Front Left Connecting Face (Outer_Apex, Inner_Apex, Inner_BL, Outer_BL)
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_APEX, UV_QUAD_TL, 6),
            add_face_vertex(V_INNER_FRONT_APEX, UV_QUAD_TR, 6),
            add_face_vertex(V_INNER_FRONT_BL, UV_QUAD_BR, 6),
            add_face_vertex(V_OUTER_FRONT_BL, UV_QUAD_BL, 6)
        ])
        # Front Bottom Connecting Face (Outer_BL, Inner_BL, Inner_BR, Outer_BR)
        # Vertex order (v1, v7, v8, v2) is preserved. Normal n6 points -Z.
        self._faces.append([
            add_face_vertex(V_OUTER_FRONT_BL, UV_QUAD_TL, 6),
            add_face_vertex(V_INNER_FRONT_BL, UV_QUAD_BL, 6),
            add_face_vertex(V_INNER_FRONT_BR, UV_QUAD_BR, 6),
            add_face_vertex(V_OUTER_FRONT_BR, UV_QUAD_TR, 6)
        ])

        # 4. Back Cap Faces (connecting outer back to inner back) (3 quads)
        # Normal for back cap (n7) points +Z (OUTWARD from back).
        self._faces.append([
            add_face_vertex(V_OUTER_BACK_APEX, UV_QUAD_TL, 7),
            add_face_vertex(V_INNER_BACK_APEX, UV_QUAD_TR, 7),
            add_face_vertex(V_INNER_BACK_BR, UV_QUAD_BR, 7),
            add_face_vertex(V_OUTER_BACK_BR, UV_QUAD_BL, 7)
        ])
        # Back Right Connecting Face (Outer_Apex, Outer_BL, Inner_BL, Inner_Apex)
        self._faces.append([
            add_face_vertex(V_OUTER_BACK_APEX, UV_QUAD_TL, 7),
            add_face_vertex(V_OUTER_BACK_BL, UV_QUAD_BL, 7),
            add_face_vertex(V_INNER_BACK_BL, UV_QUAD_BR, 7),
            add_face_vertex(V_INNER_BACK_APEX, UV_QUAD_TR, 7)
        ])
        # Back Bottom Connecting Face (Inner_BL, Outer_BL, Outer_BR, Inner_BR)
        # Vertex order (v10, v4, v5, v11) is preserved. Normal n7 points +Z.
        self._faces.append([
            add_face_vertex(V_INNER_BACK_BL, UV_QUAD_TL, 7),
            add_face_vertex(V_OUTER_BACK_BL, UV_QUAD_BL, 7),
            add_face_vertex(V_OUTER_BACK_BR, UV_QUAD_BR, 7),
            add_face_vertex(V_INNER_BACK_BR, UV_QUAD_TR, 7)
        ])


    def write_obj_file(self):
        """
        Writes the generated hollow triangular prism geometry to an .obj file.
        """
        self._generate_geometry() # Ensure geometry is generated

        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Textured Hollow Triangular Prism .obj file\n")
                f.write(f"# Name: {self.output_obj_filepath}\n")
                f.write(f"# Outer: Base={self.outer_base_side:.2f}, Height={self.outer_height:.2f}\n")
                f.write(f"# Inner: Base={self.inner_base_side:.2f}, Inner_Apex_Y={self.inner_apex_y:.2f}, Inner_Base_Y={self.inner_base_y:.2f}\n")
                f.write(f"# Depth: {self.depth:.2f}\n")
                f.write(f"# Wall Thicknesses: Base={self.base_wall_thickness:.2f}, Apex={self.apex_wall_thickness:.2f}, Bottom={self.bottom_wall_thickness:.2f}\n\n")

                # Link to the .mtl file
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")

                f.write("o HollowTriangularPrism\n")
                f.write("g HollowTriangularPrismBody\n")

                # Write vertices
                for v in self._vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                f.write("\n")

                # Write texture coordinates
                for vt in self._texture_coords:
                    f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                f.write("\n")

                # Write normals
                for vn in self._normals:
                    f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
                f.write("\n")

                # Use the material defined in the .mtl file
                f.write("usemtl TriangularPrismMaterial\n")
                f.write("s 0\n") # Set smoothing group to 0 for faceted look

                # Write faces (v/vt/vn)
                for face in self._faces:
                    f.write("f")
                    for v_idx, vt_idx, vn_idx in face:
                        f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                    f.write("\n")
                print(f"Successfully generated {self.output_obj_filepath}")

        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def write_mtl_file(self):
        """
        Generates a simple .mtl file that references the texture.
        """
        try:
            with open(self.output_mtl_filepath, 'w') as f:
                f.write(f"# Generated Material Library for {self.output_obj_filepath}\n\n")
                f.write("newmtl TriangularPrismMaterial\n")
                f.write("Ns 96.078431\n") # Shininess
                f.write("Ka 1.000000 1.000000 1.000000\n") # Ambient color (white)
                f.write("Kd 1.000000 1.000000 1.000000\n") # Diffuse color (white)
                f.write("Ks 0.500000 0.500000 0.500000\n") # Specular color (gray)
                f.write("d 1.0\n") # Dissolve (opaque)
                f.write("illum 2\n") # Illumination model (specular highlight)
                f.write(f"map_Kd {self.texture_filename}\n") # Diffuse texture map
            print(f"Successfully generated {self.output_mtl_filepath}")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        """
        Generates both the .obj and .mtl files.
        """
        self.write_obj_file()
        self.write_mtl_file()



if __name__ == "__main__":

    # Example usage:
    generator = PrismGenerator(
    outer_base_side=2.0,
    outer_height=3.0,
    base_wall_thickness=0.2,
    apex_wall_thickness=0.3,
    bottom_wall_thickness=0.1,
    depth=1.0
    )
    generator.generate_files()
    print("Check your directory for 'textured_hollow_triangular_prism.obj' and '.mtl' files.")