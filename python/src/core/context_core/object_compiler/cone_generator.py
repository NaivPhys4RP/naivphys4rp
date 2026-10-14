import math
import numpy as np
import cv2
import random
from typing import Dict, Any, List, Tuple
# Assuming common.py contains:
# UV_QUADRANTS, COLOR_MAP, TEXTURE_TYPE, MATERIAL_TYPE, MATERIAL_PROPERTIES
# generate_quadrant_texture, probabilistic_color_selector, probabilistic_ka_kd_illum_mapping
from common import *


class ConeGenerator:
    def __init__(self, output_name="textured_thick_conical_stalk",
                 outer_bottom_radius=1.0, outer_top_radius=0.3, height=2.0,
                 inner_bottom_radius=0.3, inner_top_radius=0.2,
                 segments=30, height_subdivisions=10,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        """
        Initializes the ConeGenerator with structural and aesthetic parameters.
        """
        # Validate radii for outer and inner frustums
        if not (0 < inner_bottom_radius < outer_bottom_radius):
            raise ValueError("Inner bottom radius must be positive and less than outer bottom radius.")
        if not (0 <= inner_top_radius < outer_top_radius or inner_top_radius == 0 and outer_top_radius > 0):
            raise ValueError("Inner top radius must be less than outer top radius (or 0 for a cone tip).")
        if not (height > 0):
            raise ValueError("Height must be positive.")
        if not (segments >= 3):
            raise ValueError("Segments must be at least 3 for a valid shape.")
        if not (height_subdivisions >= 1):
            raise ValueError("Height subdivisions must be at least 1.")

        self.output_name = output_name
        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"

        self.outer_bottom_radius = outer_bottom_radius
        self.outer_top_radius = outer_top_radius
        self.height = height
        self.inner_bottom_radius = inner_bottom_radius
        self.inner_top_radius = inner_top_radius
        self.segments = segments
        self.height_subdivisions = height_subdivisions

        # --- Aesthetics Parameters (Unified System) ---
        default_aesthetics = {
            "colors": [],  # Changed default to empty list to trigger probabilistic selection
            "texture_type": TEXTURE_TYPE["SOLID_T"],
            "texture_data": {"rgb": (1.0, 1.0, 1.0)}
        }
        self.aesthetics_params = default_aesthetics
        if aesthetics_params:
            self.aesthetics_params.update(aesthetics_params)

        # --- Structural Parameters (Unified System) ---
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

        # Probabilistic color selection if input colors are empty
        if not input_colors:
            # Randomly select a base color, and use variations for the other three sides
            base_color = probabilistic_color_selector()
            input_colors = [base_color, probabilistic_color_selector(), probabilistic_color_selector(),
                            probabilistic_color_selector()]

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
        Generates the vertices, texture coordinates, normals, and faces for the thick conical stalk.
        UV coordinates are mapped to the four quadrants of the texture map.
        """
        # Clear previous geometry
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []
        # Re-initialize the semantic dictionary
        self.object_semantic = {
            'out_side': [], 'in_side': [], 'top_side': [], 'bottom_side': []
        }
        face_id = 0  # Initialize face ID counter

        # Helper to add vertex, normal, and UV indices to a face
        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)  # OBJ is 1-based indexing

        # Store starting indices for OBJ 1-based indexing
        outer_side_v_start_idx = len(self._vertices)
        outer_side_n_start_idx = len(self._normals)
        outer_side_uv_start_idx = len(self._texture_coords)

        # --- 1. Outer Surface (Maps to UV U:[0.0, 0.5], V:[0.0, 0.5]) ---
        u_min_o, u_max_o, v_min_o, v_max_o = UV_QUADRANTS['out_side']
        u_scale_o = u_max_o - u_min_o;
        v_scale_o = v_max_o - v_min_o

        delta_r_outer = self.outer_bottom_radius - self.outer_top_radius
        slant_len_outer = math.sqrt(self.height ** 2 + delta_r_outer ** 2)
        norm_y_component_outer = delta_r_outer / slant_len_outer
        norm_xz_component_outer = self.height / slant_len_outer

        for j in range(self.height_subdivisions + 1):  # Loop through height subdivisions
            h_ratio = j / self.height_subdivisions
            current_height = self.height * h_ratio
            current_radius = self.outer_bottom_radius - delta_r_outer * h_ratio

            for i in range(self.segments + 1):  # Loop through segments
                angle = 2 * math.pi * i / self.segments
                cos_angle = math.cos(angle)
                sin_angle = math.sin(angle)

                # Vertices
                self._vertices.append([current_radius * cos_angle, current_height, current_radius * sin_angle])

                # Normals (pointing outwards)
                norm_x_outer = -norm_xz_component_outer * cos_angle
                norm_z_outer = -norm_xz_component_outer * sin_angle
                self._normals.append([norm_x_outer, -norm_y_component_outer, norm_z_outer])

                # UVs for outer frustum side (Cylindrical map, scaled to quadrant)
                u_outer = float(i) / self.segments
                v_outer = float(j) / self.height_subdivisions
                self._texture_coords.append([u_min_o + u_outer * u_scale_o, v_min_o + v_outer * v_scale_o])

        # --- 2. Inner Surface (Maps to UV U:[0.5, 1.0], V:[0.0, 0.5]) ---
        inner_side_v_start_idx = len(self._vertices)
        inner_side_n_start_idx = len(self._normals)
        inner_side_uv_start_idx = len(self._texture_coords)

        u_min_i, u_max_i, v_min_i, v_max_i = UV_QUADRANTS['in_side']
        u_scale_i = u_max_i - u_min_i;
        v_scale_i = v_max_i - v_min_i

        delta_r_inner = self.inner_bottom_radius - self.inner_top_radius
        slant_len_inner = math.sqrt(self.height ** 2 + delta_r_inner ** 2)
        norm_y_component_inner = delta_r_inner / slant_len_inner
        norm_xz_component_inner = self.height / slant_len_inner

        for j in range(self.height_subdivisions + 1):
            h_ratio = j / self.height_subdivisions
            current_height = self.height * h_ratio
            current_radius = self.inner_bottom_radius - delta_r_inner * h_ratio

            for i in range(self.segments + 1):
                angle = 2 * math.pi * i / self.segments
                cos_angle = math.cos(angle)
                sin_angle = math.sin(angle)

                # Vertices
                self._vertices.append([current_radius * cos_angle, current_height, current_radius * sin_angle])

                # Normals (pointing inwards)
                norm_x_inner = norm_xz_component_inner * cos_angle
                norm_z_inner = norm_xz_component_inner * sin_angle
                self._normals.append([norm_x_inner, norm_y_component_inner, norm_z_inner])

                # UVs for inner frustum side (Cylindrical map, scaled to quadrant)
                u_inner = float(i) / self.segments
                v_inner = float(j) / self.height_subdivisions
                self._texture_coords.append([u_min_i + u_inner * u_scale_i, v_min_i + v_inner * v_scale_i])

        # --- 3. Cap Normals ---
        normal_bottom_cap_idx = len(self._normals)
        self._normals.append([0.0, 1.0, 0.0])  # Bottom cap normal (points up)

        normal_top_cap_idx = len(self._normals)
        self._normals.append([0.0, -1.0, 0.0])  # Top cap normal (points down)

        # --- 4. Cap UVs (Planar Projection, Scaled to Quadrants) ---
        cap_uv_start_idx = len(self._texture_coords)
        max_r = self.outer_bottom_radius  # Use the largest radius for consistent scaling (0..1)

        # 4a. BOTTOM CAP UVs (Maps to U:[0.5, 1.0], V:[0.5, 1.0])
        u_min_b, u_max_b, v_min_b, v_max_b = UV_QUADRANTS['bottom_side']
        u_scale_b = u_max_b - u_min_b;
        v_scale_b = v_max_b - v_min_b

        for i in range(self.segments + 1):
            angle = 2 * math.pi * i / self.segments
            cos_angle = math.cos(angle);
            sin_angle = math.sin(angle)

            # Outer Rim Point UV (Planar projection, normalized by max_r)
            x_o_b = self.outer_bottom_radius * cos_angle / (2 * max_r) + 0.5
            z_o_b = self.outer_bottom_radius * sin_angle / (2 * max_r) + 0.5
            self._texture_coords.append([u_min_b + x_o_b * u_scale_b, v_min_b + z_o_b * v_scale_b])

            # Inner Rim Point UV
            x_i_b = self.inner_bottom_radius * cos_angle / (2 * max_r) + 0.5
            z_i_b = self.inner_bottom_radius * sin_angle / (2 * max_r) + 0.5
            self._texture_coords.append([u_min_b + x_i_b * u_scale_b, v_min_b + z_i_b * v_scale_b])

        # 4b. TOP CAP UVs (Maps to U:[0.0, 0.5], V:[0.5, 1.0])
        u_min_t, u_max_t, v_min_t, v_max_t = UV_QUADRANTS['top_side']
        u_scale_t = u_max_t - u_min_t;
        v_scale_t = v_max_t - v_min_t

        for i in range(self.segments + 1):
            angle = 2 * math.pi * i / self.segments
            cos_angle = math.cos(angle);
            sin_angle = math.sin(angle)

            # Outer Rim Point UV
            # Note: Max radius for top cap is outer_top_radius, but we normalize by max_r (outer_bottom_radius)
            x_o_t = self.outer_top_radius * cos_angle / (2 * max_r) + 0.5
            z_o_t = self.outer_top_radius * sin_angle / (2 * max_r) + 0.5
            self._texture_coords.append([u_min_t + x_o_t * u_scale_t, v_min_t + z_o_t * v_scale_t])

            # Inner Rim Point UV
            x_i_t = self.inner_top_radius * cos_angle / (2 * max_r) + 0.5
            z_i_t = self.inner_top_radius * sin_angle / (2 * max_r) + 0.5
            self._texture_coords.append([u_min_t + x_i_t * u_scale_t, v_min_t + z_i_t * v_scale_t])

        # --- 5. Generate Faces (using face_id and object_semantic) ---

        # 5.1 Outer Surface Faces (Quads) - Material: OuterMaterial
        for j in range(self.height_subdivisions):
            for i in range(self.segments):
                v_bl_idx = outer_side_v_start_idx + (j * (self.segments + 1)) + i
                v_br_idx = outer_side_v_start_idx + (j * (self.segments + 1)) + i + 1
                v_tl_idx = outer_side_v_start_idx + ((j + 1) * (self.segments + 1)) + i
                v_tr_idx = outer_side_v_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                n_bl_idx = outer_side_n_start_idx + (j * (self.segments + 1)) + i
                n_tr_idx = outer_side_n_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                uv_bl_idx = outer_side_uv_start_idx + (j * (self.segments + 1)) + i
                uv_tr_idx = outer_side_uv_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                # Use corner indices for the face
                p1 = (v_bl_idx, uv_bl_idx, n_bl_idx)
                p2 = (v_tl_idx, outer_side_uv_start_idx + ((j + 1) * (self.segments + 1)) + i,
                      outer_side_n_start_idx + ((j + 1) * (self.segments + 1)) + i)
                p3 = (v_tr_idx, uv_tr_idx, n_tr_idx)
                p4 = (v_br_idx, outer_side_uv_start_idx + (j * (self.segments + 1)) + i + 1,
                      outer_side_n_start_idx + (j * (self.segments + 1)) + i + 1)

                self._faces.append([
                    add_face_vertex(*p1), add_face_vertex(*p2),
                    add_face_vertex(*p3), add_face_vertex(*p4)
                ])
                self.object_semantic['out_side'].append({'id': face_id, 'ring': j, 'segment': i})
                face_id += 1

        # 5.2 Inner Surface Faces (Quads) - Material: InnerMaterial
        for j in range(self.height_subdivisions):
            for i in range(self.segments):
                v_bl_idx = inner_side_v_start_idx + (j * (self.segments + 1)) + i
                v_br_idx = inner_side_v_start_idx + (j * (self.segments + 1)) + i + 1
                v_tl_idx = inner_side_v_start_idx + ((j + 1) * (self.segments + 1)) + i
                v_tr_idx = inner_side_v_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                n_bl_idx = inner_side_n_start_idx + (j * (self.segments + 1)) + i
                n_tr_idx = inner_side_n_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                uv_bl_idx = inner_side_uv_start_idx + (j * (self.segments + 1)) + i
                uv_tr_idx = inner_side_uv_start_idx + ((j + 1) * (self.segments + 1)) + i + 1

                p1 = (v_bl_idx, uv_bl_idx, n_bl_idx)
                p2 = (v_br_idx, inner_side_uv_start_idx + (j * (self.segments + 1)) + i + 1,
                      inner_side_n_start_idx + (j * (self.segments + 1)) + i + 1)
                p3 = (v_tr_idx, uv_tr_idx, n_tr_idx)
                p4 = (v_tl_idx, inner_side_uv_start_idx + ((j + 1) * (self.segments + 1)) + i,
                      inner_side_n_start_idx + ((j + 1) * (self.segments + 1)) + i)

                self._faces.append([
                    add_face_vertex(*p1), add_face_vertex(*p2),
                    add_face_vertex(*p3), add_face_vertex(*p4)
                ])
                self.object_semantic['in_side'].append({'id': face_id, 'ring': j, 'segment': i})
                face_id += 1

        # 5.3 Bottom Cap Faces (Quads) - Material: BottomMaterial
        # The UV indices for the bottom cap start at cap_uv_start_idx. Outer UVs are i*2, Inner UVs are i*2 + 1
        uv_bottom_start_idx = cap_uv_start_idx

        for i in range(self.segments):
            v_outer_curr_idx = outer_side_v_start_idx + i
            v_outer_next_idx = outer_side_v_start_idx + i + 1
            v_inner_curr_idx = inner_side_v_start_idx + i
            v_inner_next_idx = inner_side_v_start_idx + i + 1

            uv_outer_curr_idx = uv_bottom_start_idx + i * 2
            uv_outer_next_idx = uv_bottom_start_idx + (i + 1) * 2
            uv_inner_curr_idx = uv_bottom_start_idx + i * 2 + 1
            uv_inner_next_idx = uv_bottom_start_idx + (i + 1) * 2 + 1

            n_idx = normal_bottom_cap_idx

            self._faces.append([
                add_face_vertex(v_inner_curr_idx, uv_inner_curr_idx, n_idx),
                add_face_vertex(v_outer_curr_idx, uv_outer_curr_idx, n_idx),
                add_face_vertex(v_outer_next_idx, uv_outer_next_idx, n_idx),
                add_face_vertex(v_inner_next_idx, uv_inner_next_idx, n_idx)
            ])
            self.object_semantic['bottom_side'].append({'id': face_id, 'ring': 0, 'segment': i})
            face_id += 1

        # 5.4 Top Cap Faces (Quads) - Material: TopMaterial
        # The UV indices for the top cap start after the bottom cap UVs (2 * (segments + 1) points later)
        uv_top_start_idx = cap_uv_start_idx + 2 * (self.segments + 1)

        for i in range(self.segments):
            # Vertices are from the last subdivision (j=height_subdivisions)
            last_ring_offset = (self.height_subdivisions * (self.segments + 1))
            v_outer_curr_idx = outer_side_v_start_idx + last_ring_offset + i
            v_outer_next_idx = outer_side_v_start_idx + last_ring_offset + i + 1
            v_inner_curr_idx = inner_side_v_start_idx + last_ring_offset + i
            v_inner_next_idx = inner_side_v_start_idx + last_ring_offset + i + 1

            uv_outer_curr_idx = uv_top_start_idx + i * 2
            uv_outer_next_idx = uv_top_start_idx + (i + 1) * 2
            uv_inner_curr_idx = uv_top_start_idx + i * 2 + 1
            uv_inner_next_idx = uv_top_start_idx + (i + 1) * 2 + 1

            n_idx = normal_top_cap_idx

            self._faces.append([
                add_face_vertex(v_inner_curr_idx, uv_inner_curr_idx, n_idx),
                add_face_vertex(v_inner_next_idx, uv_inner_next_idx, n_idx),
                add_face_vertex(v_outer_next_idx, uv_outer_next_idx, n_idx),
                add_face_vertex(v_outer_curr_idx, uv_outer_curr_idx, n_idx)
            ])
            self.object_semantic['top_side'].append({'id': face_id, 'ring': 0, 'segment': i})
            face_id += 1
        self.body = self

    def write_obj_file(self):
        """
        Writes the generated thick conical stalk geometry to an .obj file, using per-side materials.
        """
        self._generate_geometry()

        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Parametrized Conical Stalk .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")

                f.write("o ThickConicalStalk\n")
                f.write("g ThickConicalStalkBody\n")

                for data, prefix in zip([self._vertices, self._texture_coords, self._normals], ['v', 'vt', 'vn']):
                    for item in data:
                        f.write(f"{prefix} {' '.join(f'{x:.6f}' for x in item)}\n")
                    f.write("\n")

                face_groups_to_mtl = {
                    'out_side': 'OuterMaterial', 'in_side': 'InnerMaterial',
                    'top_side': 'TopMaterial', 'bottom_side': 'BottomMaterial'
                }

                face_offset = 0
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

    def write_mtl_file(self):
        """
        Generates the .mtl file with a structural metadata block and four aesthetic material blocks.
        """
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

                    # Write the map_Kd line
                    map_kd_line = aesthetic_lines.get('map_Kd', '')
                    if map_kd_line:
                        f.write(f"{map_kd_line}\n")

                    f.write("\n")

            print(f"Successfully generated {self.output_mtl_filepath} with 1 metadata and 4 aesthetic materials.")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        """
        Generates the .obj, .mtl, and any necessary texture files.
        """
        self.write_obj_file()
        self.write_mtl_file()

    def get_satisfiable_joints(self, faces=['out_side'], rings=[0], segments=[0]):
        face_id = []
        for face in faces:
            try:
                for face_dict in self.object_semantic[face]:
                    ring = face_dict['ring']
                    segment = face_dict['segment']
                    if ring in rings and segment in segments:
                        face_id.append(face_dict['id'] + 1)

            except Exception as e:
                print("Error occured when retrieving faces: " + str(e))
        return face_id


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

    generator_gradient = ConeGenerator(
        output_name="cartoon_gradient_cone_test",
        outer_bottom_radius=2.0, outer_top_radius=0.1, height=3.0,
        inner_bottom_radius=1.0, inner_top_radius=0.05,
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

    generator_glass = ConeGenerator(
        output_name="glass_transparent_cone_test",
        outer_bottom_radius=1.5, outer_top_radius=0.5, height=2.5,
        inner_bottom_radius=1.3, inner_top_radius=0.4,
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
          generator_glass.get_satisfiable_joints(faces=['out_side'], rings=[5], segments=[3]))
