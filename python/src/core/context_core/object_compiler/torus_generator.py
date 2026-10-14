import math
import numpy as np
from typing import Dict, Any
from common import *  # For TEXTURE_TYPE, COLOR_MAP, MATERIAL_TYPE, etc.


class TorusGenerator:
    def __init__(self,
                 output_name="textured_hollow_torus_arc",
                 major_radius=3.0, minor_radius=0.5, inner_radius=0.3,
                 arc_degrees=180,
                 major_segments=3,
                 minor_segments=6,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        # Original geometry parameters
        if not (major_radius > 0 and minor_radius > 0 and inner_radius > 0):
            raise ValueError("Radii must be positive.")
        if not (inner_radius < minor_radius):
            raise ValueError("Inner radius must be less than minor radius for a hollow tube.")
        if not (major_segments >= 3 and minor_segments >= 3):
            raise ValueError("Segments must be at least 3 for valid polygons.")
        if not (0 < arc_degrees <= 360):
            raise ValueError("Arc degrees must be between 0 (exclusive) and 360 (inclusive).")

        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.inner_radius = inner_radius
        self.arc_degrees = arc_degrees
        self.major_segments = major_segments
        self.minor_segments = minor_segments

        self.output_name=output_name
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

    # -------------------------
    # Geometry remains unchanged
    # -------------------------

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
        Generates the vertices, texture coordinates, normals, and faces for the hollow torus arc,
        with UV mapping based on UV_QUADRANTS.
        """
        import numpy as np
        import math

        # Clear previous geometry
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []
        self.object_semantic = {
            'out_side': [],
            'in_side': [],
            'top_side': [],
            'bottom_side': []
        }

        face_id = 0

        # Helper to add vertex, normal, and UV indices to a face tuple (OBJ 1-based indexing)
        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        # Angular steps
        major_angle_step_rad = (self.arc_degrees / self.major_segments) * (math.pi / 180)
        minor_angle_step_rad = (2 * math.pi) / self.minor_segments

        num_major_points = self.major_segments + 1
        num_minor_points = self.minor_segments + 1

        # UV quadrant info
        u_min_o, u_max_o, v_min_o, v_max_o = UV_QUADRANTS['out_side']
        u_min_i, u_max_i, v_min_i, v_max_i = UV_QUADRANTS['in_side']
        u_min_t, u_max_t, v_min_t, v_max_t = UV_QUADRANTS['top_side']
        u_min_b, u_max_b, v_min_b, v_max_b = UV_QUADRANTS['bottom_side']

        # --- Generate Vertices, Normals, UVs ---
        for i in range(num_major_points):
            major_angle = i * major_angle_step_rad
            cos_major = math.cos(major_angle)
            sin_major = math.sin(major_angle)

            for j in range(num_minor_points):
                minor_angle = j * minor_angle_step_rad
                cos_minor = math.cos(minor_angle)
                sin_minor = math.sin(minor_angle)

                # Outer surface
                x_outer = (self.major_radius + self.minor_radius * cos_minor) * cos_major
                y_outer = self.minor_radius * sin_minor
                z_outer = (self.major_radius + self.minor_radius * cos_minor) * sin_major
                self._vertices.append([x_outer, y_outer, z_outer])

                norm_x_outer = -cos_minor * cos_major
                norm_y_outer = -sin_minor
                norm_z_outer = -cos_minor * sin_major
                self._normals.append([norm_x_outer, norm_y_outer, norm_z_outer])

                # UV for outer surface mapped to quadrant
                u_outer = float(i) / self.major_segments
                v_outer = float(j) / self.minor_segments
                self._texture_coords.append([u_min_o + u_outer * (u_max_o - u_min_o),
                                             v_min_o + v_outer * (v_max_o - v_min_o)])

                # Inner surface
                x_inner = (self.major_radius + self.inner_radius * cos_minor) * cos_major
                y_inner = self.inner_radius * sin_minor
                z_inner = (self.major_radius + self.inner_radius * cos_minor) * sin_major
                self._vertices.append([x_inner, y_inner, z_inner])

                norm_x_inner = cos_minor * cos_major
                norm_y_inner = sin_minor
                norm_z_inner = cos_minor * sin_major
                self._normals.append([norm_x_inner, norm_y_inner, norm_z_inner])

                # UV for inner surface mapped to quadrant
                u_inner = float(i) / self.major_segments
                v_inner = float(j) / self.minor_segments
                self._texture_coords.append([u_min_i + u_inner * (u_max_i - u_min_i),
                                             v_min_i + v_inner * (v_max_i - v_min_i)])

        # --- Generate Faces ---
        for i in range(self.major_segments):
            for j in range(self.minor_segments):
                idx_o_curr_curr = (i * num_minor_points + j) * 2
                idx_o_curr_next = (i * num_minor_points + (j + 1)) * 2
                idx_o_next_next = ((i + 1) * num_minor_points + (j + 1)) * 2
                idx_o_next_curr = ((i + 1) * num_minor_points + j) * 2

                idx_i_curr_curr = idx_o_curr_curr + 1
                idx_i_curr_next = idx_o_curr_next + 1
                idx_i_next_next = idx_o_next_next + 1
                idx_i_next_curr = idx_o_next_curr + 1

                # Outer surface
                self._faces.append([
                    add_face_vertex(idx_o_curr_curr, idx_o_curr_curr, idx_o_curr_curr),
                    add_face_vertex(idx_o_curr_next, idx_o_curr_next, idx_o_curr_next),
                    add_face_vertex(idx_o_next_next, idx_o_next_next, idx_o_next_next),
                    add_face_vertex(idx_o_next_curr, idx_o_next_curr, idx_o_next_curr)
                ])
                self.object_semantic['out_side'].append({'id': face_id, 'ring': i, 'segment': j})
                face_id += 1

                # Inner surface
                self._faces.append([
                    add_face_vertex(idx_i_curr_curr, idx_i_curr_curr, idx_i_curr_curr),
                    add_face_vertex(idx_i_next_curr, idx_i_next_curr, idx_i_next_curr),
                    add_face_vertex(idx_i_next_next, idx_i_next_next, idx_i_next_next),
                    add_face_vertex(idx_i_curr_next, idx_i_curr_next, idx_i_curr_next)
                ])
                self.object_semantic['in_side'].append({'id': face_id, 'ring': i, 'segment': j})
                face_id += 1

        # --- Top and Bottom Rim Faces ---
        j_top_segment = round(0.25 * self.minor_segments)
        j_bottom_segment = round(0.75 * self.minor_segments)

        for i in range(self.major_segments):
            # Top rim
            idx_o_curr_top = (i * num_minor_points + j_top_segment) * 2
            idx_o_next_top = ((i + 1) * num_minor_points + j_top_segment) * 2
            idx_i_curr_top = idx_o_curr_top + 1
            idx_i_next_top = idx_o_next_top + 1

            # Normal
            v_o_curr_top = np.array(self._vertices[idx_o_curr_top])
            v_o_next_top = np.array(self._vertices[idx_o_next_top])
            v_i_next_top = np.array(self._vertices[idx_i_next_top])
            v_i_curr_top = np.array(self._vertices[idx_i_curr_top])

            normal_top_rim = np.cross(v_i_curr_top - v_o_curr_top, v_o_next_top - v_o_curr_top)
            normal_top_rim /= np.linalg.norm(normal_top_rim)
            top_rim_n_idx = len(self._normals)
            self._normals.append(normal_top_rim.tolist())

            # Face
            self._faces.append([
                add_face_vertex(idx_o_curr_top, idx_o_curr_top, top_rim_n_idx),
                add_face_vertex(idx_i_curr_top, idx_i_curr_top, top_rim_n_idx),
                add_face_vertex(idx_i_next_top, idx_i_next_top, top_rim_n_idx),
                add_face_vertex(idx_o_next_top, idx_o_next_top, top_rim_n_idx)
            ])
            face_id += 1

            # Bottom rim
            idx_o_curr_bottom = (i * num_minor_points + j_bottom_segment) * 2
            idx_o_next_bottom = ((i + 1) * num_minor_points + j_bottom_segment) * 2
            idx_i_curr_bottom = idx_o_curr_bottom + 1
            idx_i_next_bottom = idx_o_next_bottom + 1

            v_o_curr_bottom = np.array(self._vertices[idx_o_curr_bottom])
            v_o_next_bottom = np.array(self._vertices[idx_o_next_bottom])
            v_i_next_bottom = np.array(self._vertices[idx_i_next_bottom])
            v_i_curr_bottom = np.array(self._vertices[idx_i_curr_bottom])

            normal_bottom_rim = np.cross(v_o_next_bottom - v_o_curr_bottom, v_i_curr_bottom - v_o_curr_bottom)
            normal_bottom_rim /= np.linalg.norm(normal_bottom_rim)
            bottom_rim_n_idx = len(self._normals)
            self._normals.append(normal_bottom_rim.tolist())

            # Face
            self._faces.append([
                add_face_vertex(idx_o_curr_bottom, idx_o_curr_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_o_next_bottom, idx_o_next_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_i_next_bottom, idx_i_next_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_i_curr_bottom, idx_i_curr_bottom, bottom_rim_n_idx)
            ])
            face_id += 1

        # --- End Caps if arc_degrees < 360 ---
        if self.arc_degrees < 360:
            # Start cap
            start_cap_normal = np.array([-1.0, 0.0, 0.0])
            start_cap_n_idx = len(self._normals)
            self._normals.append(start_cap_normal.tolist())

            for j in range(self.minor_segments):
                idx_o_curr = j * 2
                idx_o_next = (j + 1) * 2
                idx_i_curr = idx_o_curr + 1
                idx_i_next = idx_o_next + 1

                uv_o_curr = [(self._vertices[idx_o_curr][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_o_curr][2] / (2 * self.minor_radius)) + 0.5]
                uv_o_next = [(self._vertices[idx_o_next][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_o_next][2] / (2 * self.minor_radius)) + 0.5]
                uv_i_curr = [(self._vertices[idx_i_curr][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_i_curr][2] / (2 * self.minor_radius)) + 0.5]
                uv_i_next = [(self._vertices[idx_i_next][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_i_next][2] / (2 * self.minor_radius)) + 0.5]

                temp_uv_o_curr_idx = len(self._texture_coords);
                self._texture_coords.append(uv_o_curr)
                temp_uv_o_next_idx = len(self._texture_coords);
                self._texture_coords.append(uv_o_next)
                temp_uv_i_curr_idx = len(self._texture_coords);
                self._texture_coords.append(uv_i_curr)
                temp_uv_i_next_idx = len(self._texture_coords);
                self._texture_coords.append(uv_i_next)

                self._faces.append([
                    add_face_vertex(idx_o_curr, temp_uv_o_curr_idx, start_cap_n_idx),
                    add_face_vertex(idx_i_curr, temp_uv_i_curr_idx, start_cap_n_idx),
                    add_face_vertex(idx_i_next, temp_uv_i_next_idx, start_cap_n_idx),
                    add_face_vertex(idx_o_next, temp_uv_o_next_idx, start_cap_n_idx)
                ])
                self.object_semantic['top_side'].append({'id': face_id, 'ring': 0, 'segment': j})
                face_id += 1

            # End cap
            end_major_angle_rad = self.arc_degrees * (math.pi / 180)
            end_cap_normal = np.array([math.cos(end_major_angle_rad), 0.0, math.sin(end_major_angle_rad)])
            end_cap_n_idx = len(self._normals)
            self._normals.append(end_cap_normal.tolist())

            for j in range(self.minor_segments):
                idx_o_curr = (self.major_segments * num_minor_points + j) * 2
                idx_o_next = (self.major_segments * num_minor_points + (j + 1)) * 2
                idx_i_curr = idx_o_curr + 1
                idx_i_next = idx_o_next + 1

                uv_o_curr = [(self._vertices[idx_o_curr][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_o_curr][2] / (2 * self.minor_radius)) + 0.5]
                uv_o_next = [(self._vertices[idx_o_next][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_o_next][2] / (2 * self.minor_radius)) + 0.5]
                uv_i_curr = [(self._vertices[idx_i_curr][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_i_curr][2] / (2 * self.minor_radius)) + 0.5]
                uv_i_next = [(self._vertices[idx_i_next][1] / (2 * self.minor_radius)) + 0.5,
                             (self._vertices[idx_i_next][2] / (2 * self.minor_radius)) + 0.5]

                temp_uv_o_curr_idx = len(self._texture_coords);
                self._texture_coords.append(uv_o_curr)
                temp_uv_o_next_idx = len(self._texture_coords);
                self._texture_coords.append(uv_o_next)
                temp_uv_i_curr_idx = len(self._texture_coords);
                self._texture_coords.append(uv_i_curr)
                temp_uv_i_next_idx = len(self._texture_coords);
                self._texture_coords.append(uv_i_next)

                self._faces.append([
                    add_face_vertex(idx_o_curr, temp_uv_o_curr_idx, end_cap_n_idx),
                    add_face_vertex(idx_o_next, temp_uv_o_next_idx, end_cap_n_idx),
                    add_face_vertex(idx_i_next, temp_uv_i_next_idx, end_cap_n_idx),
                    add_face_vertex(idx_i_curr, temp_uv_i_curr_idx, end_cap_n_idx)
                ])
                self.object_semantic['bottom_side'].append({'id': face_id, 'ring': 0, 'segment': j})
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
    aesthetics_steel_gradient = {
        "colors": ["BLUE", "YELLOW", "RED"],
        "texture_type": TEXTURE_TYPE["GRADIENT_T"],
        "texture_data": {}
    }
    structural_steel_gradient = {
        "material": MATERIAL_TYPE["STEEL"],
        "fragility_rate": 0.5,
        "density": 7.8,
        "friction": 0.3, "restitution": 0.2, "absolute_fragility": 0.0,
        "transparency": 1.0
    }
    torus_steel = TorusGenerator(
        output_name="steel_gradient_torus_arc",
        major_radius=2.0,
        minor_radius=0.5,
        inner_radius=0.3,  # Required for hollow tube
        arc_degrees=180,  # Arc length
        major_segments=24,  # Around major circle
        minor_segments=12,  # Around tube cross-section
        aesthetics_params=aesthetics_steel_gradient,
        structural_params=structural_steel_gradient
    )

    torus_steel.generate_files()

    aesthetics_glass_solid = {
        "colors": ["GREEN"],
        "texture_type": TEXTURE_TYPE["SOLID_T"],
        "texture_data": {}
    }
    structural_glass_solid = {
        "material": MATERIAL_TYPE["GLASS"],
        "fragility_rate": 5.0,
        "density": 2.5,
        "friction": 0.1, "restitution": 0.9, "absolute_fragility": 0.0,
        "transparency": 0.2
    }
    torus_glass = TorusGenerator(
        output_name="glass_solid_torus",
        major_radius=1.8, minor_radius=0.4,
        major_segments=20, minor_segments=10,
        aesthetics_params=aesthetics_glass_solid,
        structural_params=structural_glass_solid
    )
    torus_glass.generate_files()
