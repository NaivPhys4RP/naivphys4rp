#!/usr/bin/env python3

import math


class PyramidGenerator:
    def __init__(self, output_name="textured_thick_pyramidal_stalk",
                 outer_base_side_length=3.0, outer_top_side_length=3.0, height=1.5,
                 inner_base_side_length=2.9, inner_top_side_length=2.9,
                 texture_filename="thick_pyramid_stalk_texture.png"):
        """
        Initializes the PyramidGenerator.

        Args:
            output_name (str): Base name for the output .obj and .mtl files.
            outer_base_side_length (float): The side length of the outer frustum's base.
            outer_top_side_length (float): The side length of the outer frustum's top.
            height (float): The height of the stalk.
            inner_base_side_length (float): The side length of the inner frustum's base.
            inner_top_side_length (float): The side length of the inner frustum's top.
            texture_filename (str): The filename of the texture image to reference in the .mtl file.
        """
        # Validate side lengths and radii
        if not (0 < inner_base_side_length < outer_base_side_length):
            raise ValueError("Inner base side length must be positive and less than outer base side length.")
        if not (0 <= inner_top_side_length < outer_top_side_length):
            raise ValueError("Inner top side length must be less than outer top side length (or 0 for a point).")
        if not (height > 0):
            raise ValueError("Height must be positive.")

        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"
        self.texture_filename = texture_filename

        self.outer_base_side_length = outer_base_side_length
        self.outer_top_side_length = outer_top_side_length
        self.height = height
        self.inner_base_side_length = inner_base_side_length
        self.inner_top_side_length = inner_top_side_length

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

    def _normalize_vector(self, vec):
        """Normalizes a 3D vector."""
        magnitude = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
        if magnitude == 0:
            return [0.0, 0.0, 0.0]  # Avoid division by zero
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
        Generates the vertices, texture coordinates, normals, and faces for the thick pyramidal stalk.
        """
        # Clear previous geometry to allow multiple calls if needed (e.g., for testing)
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

        # Helper to add vertex, normal, and UV indices to a face tuple (for OBJ 1-based indexing)
        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        # --- Generate Vertices ---

        # Outer frustum vertices (4 base, 4 top)
        half_obl = self.outer_base_side_length / 2.0
        half_otl = self.outer_top_side_length / 2.0

        # Base vertices (y=0), counter-clockwise when viewed from top (Z+ is front)
        # 0: Back-Left (-X, -Z)
        # 1: Back-Right (+X, -Z)
        # 2: Front-Right (+X, +Z)
        # 3: Front-Left (-X, +Z)
        self._vertices.append([-half_obl, 0.0, -half_obl])  # v0: Outer Base BL
        self._vertices.append([half_obl, 0.0, -half_obl])  # v1: Outer Base BR
        self._vertices.append([half_obl, 0.0, half_obl])  # v2: Outer Base FR
        self._vertices.append([-half_obl, 0.0, half_obl])  # v3: Outer Base FL

        # Top vertices (y=height), corresponding order
        # 4: Back-Left (-X, -Z)
        # 5: Back-Right (+X, -Z)
        # 6: Front-Right (+X, +Z)
        # 7: Front-Left (-X, +Z)
        self._vertices.append([-half_otl, self.height, -half_otl])  # v4: Outer Top BL
        self._vertices.append([half_otl, self.height, -half_otl])  # v5: Outer Top BR
        self._vertices.append([half_otl, self.height, half_otl])  # v6: Outer Top FR
        self._vertices.append([-half_otl, self.height, half_otl])  # v7: Outer Top FL

        # Inner frustum vertices (4 base, 4 top) - start after outer vertices
        # 8: Back-Left (-X, -Z)
        # 9: Back-Right (+X, -Z)
        # 10: Front-Right (+X, +Z)
        # 11: Front-Left (-X, +Z)
        half_ibl = self.inner_base_side_length / 2.0
        half_itl = self.inner_top_side_length / 2.0

        self._vertices.append([-half_ibl, 0.0, -half_ibl])  # v8: Inner Base BL
        self._vertices.append([half_ibl, 0.0, -half_ibl])  # v9: Inner Base BR
        self._vertices.append([half_ibl, 0.0, half_ibl])  # v10: Inner Base FR
        self._vertices.append([-half_ibl, 0.0, half_ibl])  # v11: Inner Base FL

        # 12: Back-Left (-X, -Z)
        # 13: Back-Right (+X, -Z)
        # 14: Front-Right (+X, +Z)
        # 15: Front-Left (-X, +Z)
        self._vertices.append([-half_itl, self.height, -half_itl])  # v12: Inner Top BL
        self._vertices.append([half_itl, self.height, -half_itl])  # v13: Inner Top BR
        self._vertices.append([half_itl, self.height, half_itl])  # v14: Inner Top FR
        self._vertices.append([-half_itl, self.height, half_itl])  # v15: Inner Top FL

        # --- Define Vertex Index Constants for Clarity (0-based) ---
        # Outer Frustum
        v0_idx, v1_idx, v2_idx, v3_idx = 0, 1, 2, 3  # Outer Base BL, BR, FR, FL
        v4_idx, v5_idx, v6_idx, v7_idx = 4, 5, 6, 7  # Outer Top BL, BR, FR, FL

        # Inner Frustum
        v8_idx, v9_idx, v10_idx, v11_idx = 8, 9, 10, 11  # Inner Base BL, BR, FR, FL
        v12_idx, v13_idx, v14_idx, v15_idx = 12, 13, 14, 15  # Inner Top BL, BR, FR, FL

        # --- Generate Normals ---

        # 1. Normals for Outer Side Faces (4 normals)
        # Calculate normal for each face by taking cross product of two edge vectors.
        # Ensure consistent winding (CCW for outward faces).

        # Outer Front Face (+Z) - Vertices: v3(FL), v2(FR), v6(TR), v7(TL)
        vec1 = self._vector_sub(self._vertices[v2_idx], self._vertices[v3_idx])  # v2 - v3
        vec2 = self._vector_sub(self._vertices[v7_idx], self._vertices[v3_idx])  # v7 - v3
        self._normals.append(self._normalize_vector(self._cross_product(vec2, vec1)))  # n0: Outer Front Normal

        # Outer Back Face (-Z) - Vertices: v1(BR), v0(BL), v4(TL), v5(TR)
        vec1 = self._vector_sub(self._vertices[v0_idx], self._vertices[v1_idx])  # v0 - v1
        vec2 = self._vector_sub(self._vertices[v5_idx], self._vertices[v1_idx])  # v5 - v1
        self._normals.append(self._normalize_vector(self._cross_product(vec2, vec1)))  # n1: Outer Back Normal

        # Outer Right Face (+X) - Vertices: v2(FR), v1(BR), v5(TR), v6(TL)
        vec1 = self._vector_sub(self._vertices[v1_idx], self._vertices[v2_idx])  # v1 - v2
        vec2 = self._vector_sub(self._vertices[v6_idx], self._vertices[v2_idx])  # v6 - v2
        self._normals.append(self._normalize_vector(self._cross_product(vec2, vec1)))  # n2: Outer Right Normal

        # Outer Left Face (-X) - Vertices: v0(BL), v3(FL), v7(TL), v4(TR)
        vec1 = self._vector_sub(self._vertices[v3_idx], self._vertices[v0_idx])  # v3 - v0
        vec2 = self._vector_sub(self._vertices[v4_idx], self._vertices[v0_idx])  # v4 - v0
        self._normals.append(self._normalize_vector(self._cross_product(vec2, vec1)))  # n3: Outer Left Normal

        # 2. Normals for Inner Side Faces (4 normals)
        # Calculate normal for each face, ensure consistent winding (CW for inward faces).

        # Inner Front Face (+Z) - Vertices: v11(FL), v10(FR), v14(TR), v15(TL)
        vec1 = self._vector_sub(self._vertices[v10_idx], self._vertices[v11_idx])  # v10 - v11
        vec2 = self._vector_sub(self._vertices[v15_idx], self._vertices[v11_idx])  # v15 - v11
        self._normals.append(
            self._normalize_vector(self._cross_product(vec1, vec2)))  # n4: Inner Front Normal (reversed for inwards)

        # Inner Back Face (-Z) - Vertices: v9(BR), v8(BL), v12(TL), v13(TR)
        vec1 = self._vector_sub(self._vertices[v8_idx], self._vertices[v9_idx])  # v8 - v9
        vec2 = self._vector_sub(self._vertices[v13_idx], self._vertices[v9_idx])  # v13 - v9
        self._normals.append(
            self._normalize_vector(self._cross_product(vec1, vec2)))  # n5: Inner Back Normal (reversed for inwards)

        # Inner Right Face (+X) - Vertices: v10(FR), v9(BR), v13(TR), v14(TL)
        vec1 = self._vector_sub(self._vertices[v9_idx], self._vertices[v10_idx])  # v9 - v10
        vec2 = self._vector_sub(self._vertices[v14_idx], self._vertices[v10_idx])  # v14 - v10
        self._normals.append(
            self._normalize_vector(self._cross_product(vec1, vec2)))  # n6: Inner Right Normal (reversed for inwards)

        # Inner Left Face (-X) - Vertices: v8(BL), v11(FL), v15(TL), v12(TR)
        vec1 = self._vector_sub(self._vertices[v11_idx], self._vertices[v8_idx])  # v11 - v8
        vec2 = self._vector_sub(self._vertices[v12_idx], self._vertices[v8_idx])  # v12 - v8
        self._normals.append(
            self._normalize_vector(self._cross_product(vec1, vec2)))  # n7: Inner Left Normal (reversed for inwards)

        # 3. Normals for Cap Faces (2 normals)
        self._normals.append([0.0, -1.0, 0.0])  # n8: Bottom Cap Normal (points down)
        self._normals.append([0.0, 1.0, 0.0])  # n9: Top Cap Normal (points up)

        # --- Generate UVs ---
        # A single set of 4 UVs for mapping a 0-1 texture to each quad face
        # This will be repeated for all 12 quad faces (8 sides + 4 caps)

        # 0: Bottom-Left
        # 1: Bottom-Right
        # 2: Top-Right
        # 3: Top-Left
        self._texture_coords.append([0.0, 0.0])  # uv0
        self._texture_coords.append([1.0, 0.0])  # uv1
        self._texture_coords.append([1.0, 1.0])  # uv2
        self._texture_coords.append([0.0, 1.0])  # uv3

        # --- Generate Faces ---
        # All indices are 1-based for .obj file.
        # v_idx, vt_idx, vn_idx

        # 1. Outer Surface Faces (4 Quads)
        # Use single UV set (uv0-uv3) for all side faces.
        # Winding: Counter-Clockwise (CCW) when viewed from outside.

        # Front Face (+Z) - Outer V3, V2, V6, V7 (FL, FR, TR, TL)
        self._faces.append([
            add_face_vertex(v3_idx, 0, 0),  # FL
            add_face_vertex(v2_idx, 1, 0),  # FR
            add_face_vertex(v6_idx, 2, 0),  # TR
            add_face_vertex(v7_idx, 3, 0)  # TL
        ])

        # Back Face (-Z) - Outer V1, V0, V4, V5 (BR, BL, TL, TR)
        self._faces.append([
            add_face_vertex(v1_idx, 0, 1),  # BR
            add_face_vertex(v0_idx, 1, 1),  # BL
            add_face_vertex(v4_idx, 2, 1),  # TL
            add_face_vertex(v5_idx, 3, 1)  # TR
        ])

        # Right Face (+X) - Outer V2, V1, V5, V6 (FR, BR, TR, TL)
        self._faces.append([
            add_face_vertex(v2_idx, 0, 2),  # FR
            add_face_vertex(v1_idx, 1, 2),  # BR
            add_face_vertex(v5_idx, 2, 2),  # TR
            add_face_vertex(v6_idx, 3, 2)  # TL
        ])

        # Left Face (-X) - Outer V0, V3, V7, V4 (BL, FL, TL, TR)
        self._faces.append([
            add_face_vertex(v0_idx, 0, 3),  # BL
            add_face_vertex(v3_idx, 1, 3),  # FL
            add_face_vertex(v7_idx, 2, 3),  # TL
            add_face_vertex(v4_idx, 3, 3)  # TR
        ])

        # 2. Inner Surface Faces (4 Quads)
        # Winding: Clockwise (CW) when viewed from outside (equivalent to CCW from inside, for inward normals).

        # Front Face (+Z) - Inner V11, V15, V14, V10 (FL, TL, TR, FR) - CW from outside
        self._faces.append([
            add_face_vertex(v11_idx, 0, 4),  # FL
            add_face_vertex(v15_idx, 3, 4),  # TL
            add_face_vertex(v14_idx, 2, 4),  # TR
            add_face_vertex(v10_idx, 1, 4)  # FR
        ])

        # Back Face (-Z) - Inner V9, V13, V12, V8 (BR, TR, TL, BL) - CW from outside
        self._faces.append([
            add_face_vertex(v9_idx, 0, 5),  # BR
            add_face_vertex(v13_idx, 3, 5),  # TR
            add_face_vertex(v12_idx, 2, 5),  # TL
            add_face_vertex(v8_idx, 1, 5)  # BL
        ])

        # Right Face (+X) - Inner V10, V14, V13, V9 (FR, TL, TR, BR) - CW from outside
        self._faces.append([
            add_face_vertex(v10_idx, 0, 6),  # FR
            add_face_vertex(v14_idx, 3, 6),  # TL
            add_face_vertex(v13_idx, 2, 6),  # TR
            add_face_vertex(v9_idx, 1, 6)  # BR
        ])

        # Left Face (-X) - Inner V8, V12, V15, V11 (BL, TR, TL, FL) - CW from outside
        self._faces.append([
            add_face_vertex(v8_idx, 0, 7),  # BL
            add_face_vertex(v12_idx, 3, 7),  # TR
            add_face_vertex(v15_idx, 2, 7),  # TL
            add_face_vertex(v11_idx, 1, 7)  # FL
        ])

        # 3. Bottom Cap Faces (4 Quads)
        # Normal for bottom cap (n8) points down (-Y). Winding: CW when viewed from above.

        # Front Face (+Z) - Outer V3, V2 and Inner V10, V11
        self._faces.append([
            add_face_vertex(v3_idx, 0, 8),  # Outer FL
            add_face_vertex(v11_idx, 3, 8),  # Inner FL
            add_face_vertex(v10_idx, 2, 8),  # Inner FR
            add_face_vertex(v2_idx, 1, 8)  # Outer FR
        ])

        # Back Face (-Z) - Outer V1, V0 and Inner V8, V9
        self._faces.append([
            add_face_vertex(v1_idx, 0, 8),  # Outer BR
            add_face_vertex(v9_idx, 3, 8),  # Inner BR
            add_face_vertex(v8_idx, 2, 8),  # Inner BL
            add_face_vertex(v0_idx, 1, 8)  # Outer BL
        ])

        # Right Face (+X) - Outer V2, V1 and Inner V9, V10
        self._faces.append([
            add_face_vertex(v2_idx, 0, 8),  # Outer FR
            add_face_vertex(v10_idx, 3, 8),  # Inner FR
            add_face_vertex(v9_idx, 2, 8),  # Inner BR
            add_face_vertex(v1_idx, 1, 8)  # Outer BR
        ])

        # Left Face (-X) - Outer V0, V3 and Inner V11, V8
        self._faces.append([
            add_face_vertex(v0_idx, 0, 8),  # Outer BL
            add_face_vertex(v8_idx, 3, 8),  # Inner BL
            add_face_vertex(v11_idx, 2, 8),  # Inner FL
            add_face_vertex(v3_idx, 1, 8)  # Outer FL
        ])

        # 4. Top Cap Faces (4 Quads)
        # Normal for top cap (n9) points up (+Y). Winding: CCW when viewed from above.

        # Front Face (+Z) - Outer V7, V6 and Inner V14, V15
        self._faces.append([
            add_face_vertex(v7_idx, 0, 9),  # Outer TL
            add_face_vertex(v6_idx, 1, 9),  # Outer TR
            add_face_vertex(v14_idx, 2, 9),  # Inner TR
            add_face_vertex(v15_idx, 3, 9)  # Inner TL
        ])

        # Back Face (-Z) - Outer V5, V4 and Inner V12, V13
        self._faces.append([
            add_face_vertex(v5_idx, 0, 9),  # Outer TR
            add_face_vertex(v4_idx, 1, 9),  # Outer TL
            add_face_vertex(v12_idx, 2, 9),  # Inner TL
            add_face_vertex(v13_idx, 3, 9)  # Inner TR
        ])

        # Right Face (+X) - Outer V6, V5 and Inner V13, V14
        self._faces.append([
            add_face_vertex(v6_idx, 0, 9),  # Outer TR
            add_face_vertex(v5_idx, 1, 9),  # Outer BR
            add_face_vertex(v13_idx, 2, 9),  # Inner BR
            add_face_vertex(v14_idx, 3, 9)  # Inner TR
        ])

        # Left Face (-X) - Outer V4, V7 and Inner V15, V12
        self._faces.append([
            add_face_vertex(v4_idx, 0, 9),  # Outer TL
            add_face_vertex(v7_idx, 1, 9),  # Outer FL
            add_face_vertex(v15_idx, 2, 9),  # Inner FL
            add_face_vertex(v12_idx, 3, 9)  # Inner TL
        ])

    def write_obj_file(self):
        """
        Writes the generated thick pyramidal stalk geometry to an .obj file, including texture info.
        """
        self._generate_geometry()  # Ensure geometry is generated

        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Textured Thick Pyramidal Stalk .obj file\n")
                f.write(f"# Name: {self.output_obj_filepath}\n")
                f.write(f"# Outer: Base={self.outer_base_side_length}, Top={self.outer_top_side_length}\n")
                f.write(f"# Inner: Base={self.inner_base_side_length}, Top={self.inner_top_side_length}\n")
                f.write(f"# Height: {self.height}\n\n")

                # Link to the .mtl file
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")

                f.write("o ThickPyramidalStalk\n")
                f.write("g ThickPyramidalStalkBody\n")

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
                f.write("usemtl ThickPyramidalStalkMaterial\n")
                f.write("s 0\n")  # Set smoothing group 0 for no smoothing (faceted look for pyramid)

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
                f.write("newmtl ThickPyramidalStalkMaterial\n")
                f.write("Ns 96.078431\n")  # Shininess
                f.write("Ka 1.000000 1.000000 1.000000\n")  # Ambient color (white)
                f.write("Kd 1.000000 1.000000 1.000000\n")  # Diffuse color (white)
                f.write("Ks 0.500000 0.500000 0.500000\n")  # Specular color (gray)
                f.write("d 1.0\n")  # Dissolve (opaque)
                f.write("illum 2\n")  # Illumination model (specular highlight)
                f.write(f"map_Kd {self.texture_filename}\n")  # Diffuse texture map
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
    generator = PyramidGenerator()
    generator.generate_files()
    print("Check your directory for 'textured_thick_pyramidal_stalk.obj' and '.mtl' files.")