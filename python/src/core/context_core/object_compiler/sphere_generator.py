import math
import numpy as np
import cv2
import random  # NEW: For probabilistic selection
from typing import Dict, Any, List, Tuple
from common import *

class SphereGenerator:
    def __init__(self, output_name="textured_thick_spherical_ring",
                 outer_radius=1.0, inner_radius=0.8,
                 start_latitude_deg=-60.0, end_latitude_deg=30.0,
                 segments=8, rings=10,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):

        if not (0 < inner_radius < outer_radius):
            raise ValueError("Inner radius must be positive and less than outer radius.")
        if not (-90 <= start_latitude_deg < end_latitude_deg <= 90):
            raise ValueError("Invalid latitude range. Must be -90 <= start_lat < end_lat <= 90.")
        if not (segments >= 3 and rings >= 1):
            raise ValueError("Segments must be at least 3, and rings at least 1.")

        self.output_name = output_name
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_latitude_rad = math.radians(start_latitude_deg)
        self.end_latitude_rad = math.radians(end_latitude_deg)
        self.segments = segments
        self.rings = rings

        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"

        default_aesthetics = {
            "colors": [],  # Changed default to empty list to trigger probabilistic selection
            "texture_type": TEXTURE_TYPE["SOLID_T"],
            "texture_data": {"rgb": (1.0, 1.0, 1.0)}
        }
        self.aesthetics_params = default_aesthetics
        if aesthetics_params:
            self.aesthetics_params.update(aesthetics_params)

        default_structural = {
            "material": "DEFAULT", "fragility_rate": 1.0, "absolute_fragility": 0.0,
            "density": 1.0, "friction": 0.5, "restitution": 0.5,
            # Structural parameter for transparency (0.0 to 1.0)
            "transparency": 1.0
        }
        self.structural_params = default_structural
        if structural_params:
            self.structural_params.update(structural_params)

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []
        self.object_semantic = {}
        self.body = None

    def _get_mapped_colors(self) -> Dict[str, str]:
        """Maps input colors to the four sides circularly, using probabilistic selection if no colors are provided."""
        faces = ['out_side', 'in_side', 'top_side', 'bottom_side']
        input_colors = self.aesthetics_params.get('colors', [])

        # NEW: Probabilistic color selection if input colors are empty
        if not input_colors:
            # Randomly select a base color, and use variations for the other three sides
            base_color = probabilistic_color_selector()
            input_colors = [base_color, probabilistic_color_selector(), probabilistic_color_selector(),
                            probabilistic_color_selector()]
            # This ensures we always have 4 colors, even if they might be duplicates

        # Convert color names to OBJ RGB strings (e.g., "1.0 0.65 0.0")
        rgb_colors = [COLOR_MAP.get(c.upper(), "1.0 1.0 1.0") for c in input_colors]

        mapped_colors = {}
        for i, side in enumerate(faces):
            mapped_colors[side] = rgb_colors[i % len(rgb_colors)]
        return mapped_colors

    def _generate_texture_file(self, texture_type: str) -> str:
        """
        Generates the texture map (PNG) based on the quadrant mapping using cv2.
        """
        texture_map_filename = f"{self.output_name}_{texture_type.lower()}.png"

        if texture_type in [TEXTURE_TYPE["SOLID_T"], TEXTURE_TYPE["PATTERN_T"], TEXTURE_TYPE["GRADIENT_T"]]:
            mapped_colors = self._get_mapped_colors()

            # CALL THE REAL IMAGE GENERATOR USING CV2, now passing texture_type
            generate_quadrant_texture(texture_map_filename, mapped_colors, texture_type=texture_type)
            return texture_map_filename

        # If PICTURE_T, return the external filename provided
        texture_data = self.aesthetics_params.get("texture_data", {})
        return texture_data.get("file_path", "")

    def _generate_geometry(self):
        """
        Generates the vertices, texture coordinates, normals, and faces for the thick spherical ring.
        (Omitted for brevity, assumed unchanged)
        """
        self._vertices = [];
        self._texture_coords = [];
        self._normals = [];
        self._faces = []
        self.object_semantic = {'out_side': [], 'in_side': [], 'top_side': [], 'bottom_side': []}

        def add_face_vertex(v_idx, uv_idx, n_idx):
            # OBJ file indices are 1-based (array index + 1)
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        num_lon_points = self.segments + 1
        num_lat_points = self.rings + 1

        # Indices are 0-based array indices
        outer_v_start_idx = len(self._vertices)
        outer_n_start_idx = len(self._normals)
        outer_uv_start_idx = len(self._texture_coords)

        # -----------------------------------------------------------
        # 1. Outer Surface (Maps to UV U:[0.0, 0.5], V:[0.0, 0.5])
        # -----------------------------------------------------------
        u_min, u_max, v_min, v_max = UV_QUADRANTS['out_side']
        u_scale = u_max - u_min
        v_scale = v_max - v_min
        for j in range(num_lat_points):
            current_latitude_rad = self.start_latitude_rad + \
                                   (self.end_latitude_rad - self.start_latitude_rad) * j / self.rings
            sin_lat = math.sin(current_latitude_rad);
            cos_lat = math.cos(current_latitude_rad)

            for i in range(num_lon_points):
                current_longitude_rad = 2 * math.pi * i / self.segments
                sin_lon = math.sin(current_longitude_rad);
                cos_lon = math.cos(current_longitude_rad)

                # Outer Vertex
                x = self.outer_radius * cos_lat * cos_lon;
                y = self.outer_radius * sin_lat;
                z = self.outer_radius * cos_lat * sin_lon
                self._vertices.append([x, y, z])

                # Outer Normal (points away from center)
                self._normals.append([-x / self.outer_radius, -y / self.outer_radius, -z / self.outer_radius])

                # VT CALCULATION
                u = float(i) / self.segments;
                v = float(j) / self.rings
                u_prime = u_min + u * u_scale;
                v_prime = v_min + v * v_scale
                self._texture_coords.append([u_prime, v_prime])

        # -----------------------------------------------------------
        # 2. Inner Surface (Maps to UV U:[0.5, 1.0], V:[0.0, 0.5])
        # -----------------------------------------------------------
        inner_v_start_idx = len(self._vertices)
        inner_n_start_idx = len(self._normals)
        inner_uv_start_idx = len(self._texture_coords)
        u_min, u_max, v_min, v_max = UV_QUADRANTS['in_side']
        u_scale = u_max - u_min;
        v_scale = v_max - v_min
        for j in range(num_lat_points):
            current_latitude_rad = self.start_latitude_rad + \
                                   (self.end_latitude_rad - self.start_latitude_rad) * j / self.rings
            sin_lat = math.sin(current_latitude_rad);
            cos_lat = math.cos(current_latitude_rad)

            for i in range(num_lon_points):
                current_longitude_rad = 2 * math.pi * i / self.segments
                sin_lon = math.sin(current_longitude_rad);
                cos_lon = math.cos(current_longitude_rad)

                # Inner Vertex
                x = self.inner_radius * cos_lat * cos_lon;
                y = self.inner_radius * sin_lat;
                z = self.inner_radius * cos_lat * sin_lon
                self._vertices.append([x, y, z])

                # Inner Normal (points toward center)
                self._normals.append([x / self.inner_radius, y / self.inner_radius, z / self.inner_radius])

                # VT CALCULATION
                u = float(i) / self.segments;
                v = float(j) / self.rings
                u_prime = u_min + u * u_scale;
                v_prime = v_min + v * v_scale
                self._texture_coords.append([u_prime, v_prime])

        # Note: No separate cap normals are generated. The cap faces will reuse the
        # normals from the vertices they share with the outer/inner curved surfaces.

        # -----------------------------------------------------------
        # 3. Cap UVs (Planar Projection, Scaled to Quadrants)
        # -----------------------------------------------------------
        cap_uv_start_idx = len(self._texture_coords)
        num_cap_uv_points = num_lon_points * 2  # Outer rim + inner rim

        # --- TOP CAP UVs (Maps to U:[0.0, 0.5], V:[0.5, 1.0]) ---
        u_min_t, u_max_t, v_min_t, v_max_t = UV_QUADRANTS['top_side']
        u_scale_t = u_max_t - u_min_t;
        v_scale_t = v_max_t - v_min_t
        for i in range(num_lon_points):
            current_longitude_rad = 2 * math.pi * i / self.segments

            # Outer Rim Point UV
            x_o = self.outer_radius * math.cos(self.end_latitude_rad) * math.cos(current_longitude_rad)
            z_o = self.outer_radius * math.cos(self.end_latitude_rad) * math.sin(current_longitude_rad)

            # Normalize XZ coordinates (planar projection)
            u_xz_o = x_o / (2 * self.outer_radius) + 0.5  # 0.0 to 1.0
            v_xz_o = z_o / (2 * self.outer_radius) + 0.5  # 0.0 to 1.0

            # Scale and shift to quadrant (Outer Rim is index i*2)
            self._texture_coords.append([u_min_t + u_xz_o * u_scale_t, v_min_t + v_xz_o * v_scale_t])

            # Inner Rim Point UV
            x_i = self.inner_radius * math.cos(self.end_latitude_rad) * math.cos(current_longitude_rad)
            z_i = self.inner_radius * math.cos(self.end_latitude_rad) * math.sin(current_longitude_rad)

            u_xz_i = x_i / (2 * self.outer_radius) + 0.5  # 0.0 to 1.0
            v_xz_i = z_i / (2 * self.outer_radius) + 0.5  # 0.0 to 1.0

            # Scale and shift to quadrant (Inner Rim is index i*2 + 1)
            self._texture_coords.append([u_min_t + u_xz_i * u_scale_t, v_min_t + v_xz_i * v_scale_t])

        # --- BOTTOM CAP UVs (Maps to U:[0.5, 1.0], V:[0.5, 1.0]) ---
        u_min_b, u_max_b, v_min_b, v_max_b = UV_QUADRANTS['bottom_side']
        u_scale_b = u_max_b - u_min_b;
        v_scale_b = v_max_b - v_min_b

        for i in range(num_lon_points):
            current_longitude_rad = 2 * math.pi * i / self.segments

            # Outer Rim Point UV
            x_o = self.outer_radius * math.cos(self.start_latitude_rad) * math.cos(current_longitude_rad)
            z_o = self.outer_radius * math.cos(self.start_latitude_rad) * math.sin(current_longitude_rad)

            u_xz_o = x_o / (2 * self.outer_radius) + 0.5
            v_xz_o = z_o / (2 * self.outer_radius) + 0.5

            # Scale and shift to quadrant (Outer Rim is index i*2)
            self._texture_coords.append([u_min_b + u_xz_o * u_scale_b, v_min_b + v_xz_o * v_scale_b])

            # Inner Rim Point UV
            x_i = self.inner_radius * math.cos(self.start_latitude_rad) * math.cos(current_longitude_rad)
            z_i = self.inner_radius * math.cos(self.start_latitude_rad) * math.sin(current_longitude_rad)

            u_xz_i = x_i / (2 * self.outer_radius) + 0.5
            v_xz_i = z_i / (2 * self.outer_radius) + 0.5

            # Scale and shift to quadrant (Inner Rim is index i*2 + 1)
            self._texture_coords.append([u_min_b + u_xz_i * u_scale_b, v_min_b + v_xz_i * v_scale_b])

        face_id = 0
        # 1. Outer Surface Faces (Quads)
        for j in range(self.rings):
            for i in range(self.segments):
                p1 = j * num_lon_points + i;
                p2 = j * num_lon_points + (i + 1)
                p3 = (j + 1) * num_lon_points + (i + 1);
                p4 = (j + 1) * num_lon_points + i
                v1, v2, v3, v4 = [outer_v_start_idx + p for p in [p1, p2, p3, p4]]
                n1, n2, n3, n4 = [outer_n_start_idx + p for p in [p1, p2, p3, p4]]  # Reuse normal indices
                uv1, uv2, uv3, uv4 = [outer_uv_start_idx + p for p in [p1, p2, p3, p4]]

                # Outer surface faces (winding order reversed to point out)
                self._faces.append([
                    add_face_vertex(v1, uv1, n1), add_face_vertex(v4, uv4, n4),
                    add_face_vertex(v3, uv3, n3), add_face_vertex(v2, uv2, n2)
                ])
                self.object_semantic['out_side'].append({'id': face_id, 'ring': j, 'segment': i});
                face_id += 1

        # 2. Inner Surface Faces (Quads)
        for j in range(self.rings):
            for i in range(self.segments):
                p1 = j * num_lon_points + i;
                p2 = j * num_lon_points + (i + 1)
                p3 = (j + 1) * num_lon_points + (i + 1);
                p4 = (j + 1) * num_lon_points + i
                v1, v2, v3, v4 = [inner_v_start_idx + p for p in [p1, p2, p3, p4]]
                n1, n2, n3, n4 = [inner_n_start_idx + p for p in [p1, p2, p3, p4]]  # Reuse normal indices
                uv1, uv2, uv3, uv4 = [inner_uv_start_idx + p for p in [p1, p2, p3, p4]]

                # Inner surface faces (winding order points in)
                self._faces.append([
                    add_face_vertex(v1, uv1, n1), add_face_vertex(v2, uv2, n2),
                    add_face_vertex(v3, uv3, n3), add_face_vertex(v4, uv4, n4)
                ])
                self.object_semantic['in_side'].append({'id': face_id, 'ring': j, 'segment': i});
                face_id += 1

        # --- Setup indices for Cap Face generation ---

        # Base index for points on the top cap (ring = self.rings)
        top_cap_point_p = self.rings * num_lon_points
        # Base index for points on the bottom cap (ring = 0)
        bottom_cap_point_p = 0 * num_lon_points

        uv_outer_top_start = cap_uv_start_idx
        uv_inner_top_start = cap_uv_start_idx + 1  # First inner UV point
        uv_outer_bottom_start = cap_uv_start_idx + num_cap_uv_points
        uv_inner_bottom_start = cap_uv_start_idx + num_cap_uv_points + 1

        # 3. Top Cap Faces (Quads) - Using existing smoothed normals
        for i in range(self.segments):
            # Vertex indices from the last latitude ring
            v1_o = outer_v_start_idx + top_cap_point_p + i
            v2_o = outer_v_start_idx + top_cap_point_p + (i + 1)
            v1_i = inner_v_start_idx + top_cap_point_p + i
            v2_i = inner_v_start_idx + top_cap_point_p + (i + 1)

            # Normal indices (same relative position as vertices)
            n1_o = outer_n_start_idx + top_cap_point_p + i
            n2_o = outer_n_start_idx + top_cap_point_p + (i + 1)
            n1_i = inner_n_start_idx + top_cap_point_p + i
            n2_i = inner_n_start_idx + top_cap_point_p + (i + 1)

            # UV indices (Outer UVs are at i*2, Inner UVs are at i*2 + 1)
            uv1_o = uv_outer_top_start + i * 2;
            uv2_o = uv_outer_top_start + (i + 1) * 2
            uv1_i = uv_outer_top_start + i * 2 + 1;
            uv2_i = uv_outer_top_start + (i + 1) * 2 + 1

            self._faces.append([
                add_face_vertex(v1_i, uv1_i, n1_i), add_face_vertex(v2_i, uv2_i, n2_i),
                add_face_vertex(v2_o, uv2_o, n2_o), add_face_vertex(v1_o, uv1_o, n1_o)
            ])
            self.object_semantic['top_side'].append({'id': face_id, 'ring': 0, 'segment': i});
            face_id += 1

        # 4. Bottom Cap Faces (Quads) - Using existing smoothed normals
        for i in range(self.segments):
            # Vertex indices from the first latitude ring (ring = 0)
            v1_o = outer_v_start_idx + bottom_cap_point_p + i
            v2_o = outer_v_start_idx + bottom_cap_point_p + (i + 1)
            v1_i = inner_v_start_idx + bottom_cap_point_p + i
            v2_i = inner_v_start_idx + bottom_cap_point_p + (i + 1)

            # Normal indices (same relative position as vertices)
            n1_o = outer_n_start_idx + bottom_cap_point_p + i
            n2_o = outer_n_start_idx + bottom_cap_point_p + (i + 1)
            n1_i = inner_n_start_idx + bottom_cap_point_p + i
            n2_i = inner_n_start_idx + bottom_cap_point_p + (i + 1)

            # UV indices (Outer UVs are at i*2, Inner UVs are at i*2 + 1)
            uv1_o = uv_outer_bottom_start + i * 2;
            uv2_o = uv_outer_bottom_start + (i + 1) * 2
            uv1_i = uv_outer_bottom_start + i * 2 + 1;
            uv2_i = uv_outer_bottom_start + (i + 1) * 2 + 1

            self._faces.append([
                add_face_vertex(v1_o, uv1_o, n1_o), add_face_vertex(v2_o, uv2_o, n2_o),
                add_face_vertex(v2_i, uv2_i, n2_i), add_face_vertex(v1_i, uv1_i, n1_i)
            ])
            self.object_semantic['bottom_side'].append({'id': face_id, 'ring': 0, 'segment': i});
            face_id += 1
        self.body = self

    def write_obj_file(self):
        """Writes the generated thick spherical ring geometry to an .obj file."""
        self._generate_geometry()
        # (Omitted for brevity, assumed unchanged)
        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Parametrized Spherical Ring .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")

                f.write("o ThickSphericalRing\n")
                f.write("g ThickSphericalRingBody\n")

                for data, prefix in zip([self._vertices, self._texture_coords, self._normals], ['v', 'vt', 'vn']):
                    for item in data:
                        f.write(f"{prefix} {' '.join(f'{x:.6f}' for x in item)}\n")
                    f.write("\n")

                face_groups_to_mtl = {
                    'out_side': 'OuterMaterial', 'in_side': 'InnerMaterial',
                    'top_side': 'TopMaterial', 'bottom_side': 'BottomMaterial'
                }

                for side, mtl_name in face_groups_to_mtl.items():
                    f.write(f"\n# Faces for {side}\n")
                    f.write(f"usemtl {mtl_name}\n")
                    f.write("s 1\n")

                    face_indices_for_side = [d['id'] for d in self.object_semantic.get(side, [])]

                    for face_idx in face_indices_for_side:
                        if face_idx < len(self._faces):
                            face = self._faces[face_idx]
                            f.write("f")
                            for v_idx, vt_idx, vn_idx in face:
                                f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                            f.write("\n")

            print(f"Successfully generated {self.output_obj_filepath} with per-side materials.")

        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def write_mtl_file(self):
        """Generates the .mtl file."""
        mapped_colors = self._get_mapped_colors()
        aesthetic_lines = self._generate_mtl_aesthetic_params()

        structural_lines = []
        for key, value in self.structural_params.items():
            # Special handling for the X_ prefix in the MTL file
            key_name = f"X_{key}"
            if isinstance(value, str):
                structural_lines.append(f"{key_name} {value}")
            else:
                structural_lines.append(f"{key_name} {value:.4f}")

        try:
            with open(self.output_mtl_filepath, 'w') as f:
                f.write(f"# Generated Material Library for {self.output_name}\n\n")

                # --- 1. Dedicated Structural Metadata Block ---
                f.write("# --- Structural/Physics Properties (Single Definition) ---\n")
                f.write("newmtl StructuralMetadata\n")
                for line in structural_lines:
                    f.write(f"{line}\n")
                f.write("\n")

                # --- 2. Aesthetic Material Blocks ---
                material_defs: List[Tuple[str, str]] = [
                    ('OuterMaterial', mapped_colors['out_side']),
                    ('InnerMaterial', mapped_colors['in_side']),
                    ('TopMaterial', mapped_colors['top_side']),
                    ('BottomMaterial', mapped_colors['bottom_side']),
                ]

                f.write("# --- Aesthetic Properties (Four Definitions for Per-Side Color) ---\n")
                for mtl_name, diffuse_color_rgb in material_defs:
                    f.write(f"newmtl {mtl_name}\n")

                    # Write all aesthetic lines except Kd (which uses the per-side color) and map_Kd
                    for line_type, line_value in aesthetic_lines.items():
                        if line_type not in ["Kd", "map_Kd"]:
                            f.write(f"{line_value}\n")

                    # Kd is the fallback diffuse color, but we must include map_Kd to use the texture
                    f.write(f"Kd {diffuse_color_rgb}\n")

                    # Ensure Ka is included (it's probabilistic now)
                    f.write(f"{aesthetic_lines.get('Ka')}\n")

                    # Write the map_Kd line
                    map_kd_line = aesthetic_lines.get('map_Kd', '')
                    if map_kd_line:
                        f.write(f"{map_kd_line}\n")

                    f.write("\n")

            print(f"Successfully generated {self.output_mtl_filepath} with 1 metadata and 4 aesthetic materials.")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def _generate_mtl_aesthetic_params(self) -> Dict[str, str]:
        """
        Translates high-level aesthetics into low-level MTL rendering parameters,
        including conditional transparency logic and PROBABILISTIC Ka/Kd/Illum.
        """
        mtl_lines: Dict[str, str] = {}

        material_key = self.structural_params.get("material", "DEFAULT").upper()

        # --- 1. Handle Shininess/Reflection (Ns / Ks) - Deterministic ---
        ns, ks_r, ks_g, ks_b = MATERIAL_PROPERTIES.get(
            material_key, MATERIAL_PROPERTIES["DEFAULT"]
        )
        mtl_lines["Ns"] = f"Ns {ns:.4f}"
        mtl_lines["Ks"] = f"Ks {ks_r:.6f} {ks_g:.6f} {ks_b:.6f}"

        # --- 2. Handle Ambient (Ka) and Illumination (illum) - PROBABILISTIC BASE ---
        ka_rgb_str, kd_factor, probabilistic_illum = probabilistic_ka_kd_illum_mapping(material_key)
        mtl_lines["Ka"] = f"Ka {ka_rgb_str}"  # Ambient color is now probabilistic

        # --- 3. Handle Transparency (d / illum) with overrides ---
        transparency_value = self.structural_params.get("transparency", 1.0)
        d_value = 1.0  # Default is fully opaque
        illum_value = probabilistic_illum  # Start with the probabilistic illum model

        # Override Illum/d based on material type for correctness in rendering engines
        if material_key in [MATERIAL_TYPE["GLASS"], MATERIAL_TYPE["PLASTIC"]]:
            # Set the Dissolve factor (d) directly from X_transparency
            d_value = transparency_value

            # If it's intended to be transparent, force a refractive illum model
            if d_value < 1.0:
                illum_value = random.choice([6, 7])  # Refractive or full reflection/transmission
            elif illum_value < 2:
                # If opaque but still glass/plastic, ensure it has specularity
                illum_value = 2

        else:
            # For all other materials (CARTOON, WOOD, STEEL, etc.), force opaque
            d_value = 1.0
            # Clamp illum to standard opaque models (1: Flat, 2: Specular)
            if illum_value > 2:
                illum_value = 2

        mtl_lines["d"] = f"d {d_value:.4f}"
        mtl_lines["illum"] = f"illum {illum_value}"

        # --- 4. Handle Diffuse Texture Map (map_Kd) ---
        texture_type = self.aesthetics_params.get("texture_type")

        texture_map_filename = None
        if texture_type == TEXTURE_TYPE["PICTURE_T"]:
            texture_data = self.aesthetics_params.get("texture_data", {})
            texture_map_filename = texture_data.get("file_path")
        elif texture_type in [TEXTURE_TYPE["SOLID_T"], TEXTURE_TYPE["PATTERN_T"], TEXTURE_TYPE["GRADIENT_T"]]:
            # This is where the image generation is triggered using CV2
            texture_map_filename = self._generate_texture_file(texture_type)

        if texture_map_filename:
            mtl_lines["map_Kd"] = f"map_Kd {texture_map_filename}"
        else:
            mtl_lines["map_Kd"] = ""

        return mtl_lines

    def generate_files(self):
        """
        Generates the .obj, .mtl, and any necessary texture files.
        """
        self.write_obj_file()
        self.write_mtl_file()


if __name__ == "__main__":
    # --- EXAMPLE 1: CARTOON with GRADIENT Texture (Probabilistic Color/Illum) ---
    # NOTE: "colors": [] is passed to trigger the new probabilistic color selection.
    aesthetics_gradient = {
        "colors": [],
        "texture_type": TEXTURE_TYPE["GRADIENT_T"],
        "texture_data": {}
    }

    structural_gradient = {
        "material": MATERIAL_TYPE["CARTOON"],
        "fragility_rate": 3.19,
        "density": 7.48,
        "friction": 0.5, "restitution": 0.5, "absolute_fragility": 0.0,
        "transparency": 0.3
    }

    generator_gradient = SphereGenerator(
        output_name="cartoon_gradient_ring_test",
        outer_radius=1.5, inner_radius=1.2,
        segments=16, rings=8,
        start_latitude_deg=-10.0, end_latitude_deg=10.0,
        aesthetics_params=aesthetics_gradient,
        structural_params=structural_gradient
    )
    generator_gradient.generate_files()

    # --- EXAMPLE 2: PLASTIC with PATTERN Texture (Probabilistic Color/Illum) ---
    # NOTE: "colors": [] is passed to trigger the new probabilistic color selection.
    aesthetics_pattern = {
        "colors": [],
        "texture_type": TEXTURE_TYPE["PATTERN_T"],
        "texture_data": {}
    }

    structural_pattern = {
        "material": MATERIAL_TYPE["PLASTIC"],
        "fragility_rate": 1.0,
        "density": 1.0,
        "friction": 0.5, "restitution": 0.5, "absolute_fragility": 0.0,
        "transparency": 1.0  # Fully opaque
    }

    generator_pattern = SphereGenerator(
        output_name="plastic_pattern_ring_test",
        outer_radius=1.5, inner_radius=1.2,
        segments=12, rings=4,
        aesthetics_params=aesthetics_pattern,
        structural_params=structural_pattern
    )
    generator_pattern.generate_files()

    # --- EXAMPLE 3: WOOD with SOLID Texture (Fixed Color, Probabilistic Illum) ---
    # Colors are fixed, but Ka and Illum will still be probabilistically determined for WOOD.
    aesthetics_solid = {
        "colors": ["RED", "WHITE", "BLUE"],
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }

    structural_solid = {
        "material": MATERIAL_TYPE["WOOD"],
        "fragility_rate": 1.0,
        "density": 1.0,
        "friction": 0.5, "restitution": 0.5, "absolute_fragility": 0.0,
        "transparency": 0.5
    }

    generator_solid = SphereGenerator(
        output_name="wood_solid_ring_test",
        outer_radius=1.8, inner_radius=1.0,
        segments=20, rings=10,
        start_latitude_deg=-30.0, end_latitude_deg=50.0,
        aesthetics_params=aesthetics_solid,
        structural_params=structural_solid
    )
    generator_solid.generate_files()

    # --- EXAMPLE 4: GLASS with SOLID Texture (Fixed Color, Probabilistic Illum and Applied Transparency) ---
    aesthetics_glass = {
        "colors": ["CYAN"],
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }

    structural_glass = {
        "material": MATERIAL_TYPE["GLASS"],
        "fragility_rate": 5.0,
        "density": 2.5,
        "friction": 0.1, "restitution": 0.9, "absolute_fragility": 0.0,
        "transparency": 0.5  # Applied: will render as d=0.5 with Illum 6 or 7
    }

    generator_glass = SphereGenerator(
        output_name="glass_transparent_ring_test",
        outer_radius=1.8, inner_radius=1.0,
        segments=20, rings=10,
        start_latitude_deg=-30.0, end_latitude_deg=50.0,
        aesthetics_params=aesthetics_glass,
        structural_params=structural_glass
    )
    generator_glass.generate_files()
