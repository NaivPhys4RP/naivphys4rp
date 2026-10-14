import math
import numpy as np
import cv2
import random
from typing import Dict, Any, List, Tuple

# Import all constants and helper lambdas from common.py
# (Assuming common.py defines the necessary constants like UV_QUADRANTS, etc.)
from common import *



class TorusGenerator:
    def __init__(self, output_name="textured_torus_arc",
                 major_radius=5.0,
                 minor_radius=1.5,
                 arc_degrees=270,
                 major_segments=60,
                 minor_segments=20,
                 aesthetics_params: Dict[str, Any] = None,
                 structural_params: Dict[str, Any] = None):
        """
        Initializes the TorusGenerator, accepting geometric parameters as direct arguments
        and merging them into the internal structural_params dictionary.
        """

        # Initialize aesthetics_params first.
        self.aesthetics_params = aesthetics_params if aesthetics_params is not None else {}

        # --- 1. Define Geometry from direct arguments ---
        geometry_params = {
            "major_radius": major_radius,
            "minor_radius": minor_radius,
            "arc_degrees": arc_degrees,
            "major_segments": major_segments,
            "minor_segments": minor_segments,
        }

        # --- 2. Define Default Physical/Material Properties ---
        default_structural_physics = {
            "material": "DEFAULT",
            "fragility_rate": 1.0,
            "absolute_fragility": 0.0,
            "density": 1.0,
            "friction": 0.5,
            "restitution": 0.5,
            "transparency": 1.0
        }

        # --- 3. Initialize self.structural_params with Geometry and Physics defaults ---
        self.structural_params = {}
        self.structural_params.update(geometry_params)
        self.structural_params.update(default_structural_physics)

        # --- 4. Apply any user-provided structural_params (overrides only physical properties) ---
        if structural_params:
            self.structural_params.update(structural_params)

        # Map structural geometry parameters for easy access (all are derived from the dictionary)
        self.major_radius = self.structural_params['major_radius']
        self.minor_radius = self.structural_params['minor_radius']
        self.arc_degrees = self.structural_params['arc_degrees']
        self.major_segments = self.structural_params['major_segments']
        self.minor_segments = self.structural_params['minor_segments']

        # Validation
        if not (self.major_radius > 0 and self.minor_radius > 0):
            raise ValueError("Radii must be positive.")
        if not (0 < self.arc_degrees <= 360):
            raise ValueError("Arc degrees must be between 0 (exclusive) and 360 (inclusive).")

        self.output_name = output_name
        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []
        self.object_semantic = {}
        self.body = None

    def _get_mapped_colors(self) -> Dict[str, str]:
        """
        Maps input colors to the three logical surfaces using UV quadrant keys:
        'out_side' (main surface), 'in_side' (start cap), 'top_side' (end cap).
        """
        faces_to_map = ['out_side', 'in_side', 'top_side']
        input_colors = self.aesthetics_params.get('colors', [])

        if not input_colors:
            base_color = probabilistic_color_selector()
            input_colors = [base_color, probabilistic_color_selector(), probabilistic_color_selector()]

        rgb_colors = [COLOR_MAP.get(c.upper(), "1.0 1.0 1.0") for c in input_colors]

        mapped_colors = {}
        for i, side in enumerate(faces_to_map):
            mapped_colors[side] = rgb_colors[i % len(rgb_colors)]
        return mapped_colors

    def _generate_texture_file(self, texture_type: str) -> str:
        """
        Generates the texture map (PNG) based on the quadrant mapping, or returns external path.
        """
        texture_map_filename = f"{self.output_name}_{texture_type.lower()}.png"

        if texture_type in [TEXTURE_TYPE["SOLID_T"], TEXTURE_TYPE["PATTERN_T"], TEXTURE_TYPE["GRADIENT_T"]]:
            mapped_colors = self._get_mapped_colors()
            generate_quadrant_texture(texture_map_filename, mapped_colors, texture_type=texture_type)
            return texture_map_filename

        texture_data = self.aesthetics_params.get("texture_data", {})
        return texture_data.get("file_path", "")

    def _generate_geometry(self):
        """
        Generates the vertices, texture coordinates, normals, and faces for the solid torus arc.
        This replaces the simple plane placeholder geometry.
        """
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []
        # Use UV quadrant keys for semantic grouping
        self.object_semantic = {'out_side': [], 'in_side': [], 'top_side': []}
        face_id = 0

        # Helper for OBJ 1-based indexing
        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        # Angular steps
        major_angle_step_rad = (self.arc_degrees / self.major_segments) * (math.pi / 180)
        minor_angle_step_rad = (2 * math.pi) / self.minor_segments

        num_major_points = self.major_segments + 1
        num_minor_points = self.minor_segments + 1

        # --- 1. Generate Vertices, Normals, and UVs for the Torus Surface (Arc) ---
        # Map main surface to 'out_side' quadrant
        u_min_a, u_max_a, v_min_a, v_max_a = UV_QUADRANTS['out_side']
        u_scale_a = u_max_a - u_min_a
        v_scale_a = v_max_a - v_min_a

        for i in range(num_major_points):  # Major sweep (along the arc)
            major_angle = i * major_angle_step_rad
            cos_major = math.cos(major_angle)
            sin_major = math.sin(major_angle)

            for j in range(num_minor_points):  # Minor sweep (around the tube)
                minor_angle = j * minor_angle_step_rad
                cos_minor = math.cos(minor_angle)
                sin_minor = math.sin(minor_angle)

                # Vertices (V)
                x = (self.major_radius + self.minor_radius * cos_minor) * cos_major
                y = self.minor_radius * sin_minor
                z = (self.major_radius + self.minor_radius * cos_minor) * sin_major
                self._vertices.append([x, y, z])

                # Normals (VN)
                norm_x = cos_minor * cos_major
                norm_y = sin_minor
                norm_z = cos_minor * sin_major
                self._normals.append([norm_x, norm_y, norm_z])

                # UVs (VT) - Mapped to the 'out_side' quadrant
                u_arc = float(i) / self.major_segments
                v_arc = float(j) / self.minor_segments
                self._texture_coords.append([u_min_a + u_arc * u_scale_a, v_min_a + v_arc * v_scale_a])

        # --- 2. Generate Faces for the Torus Surface (Arc) ---
        for i in range(self.major_segments):
            for j in range(self.minor_segments):
                # Indices for current major ring (i) and next major ring (i+1)
                idx_cc = (i * num_minor_points + j)
                idx_cn = (i * num_minor_points + (j + 1))
                idx_nc = ((i + 1) * num_minor_points + j)
                idx_nn = ((i + 1) * num_minor_points + (j + 1))

                # Quad (CCW winding: BL, TL, TR, BR)
                face = [
                    add_face_vertex(idx_cc, idx_cc, idx_cc),  # Bottom-Left
                    add_face_vertex(idx_nc, idx_nc, idx_nc),  # Top-Left (Next major)
                    add_face_vertex(idx_nn, idx_nn, idx_nn),  # Top-Right
                    add_face_vertex(idx_cn, idx_cn, idx_cn)  # Bottom-Right
                ]
                self._faces.append(face)
                # Assign to 'out_side' semantic group
                self.object_semantic['out_side'].append({'id': face_id, 'major_ring': i, 'minor_segment': j})
                face_id += 1

        # --- 3. Generate End Cap Faces (Start Cap i=0, End Cap i=self.major_segments) ---

        def generate_cap(i_major: int, side_key: str, uv_quadrant: Tuple[float, float, float, float]):
            """Generates the geometry and faces for one of the caps."""
            nonlocal face_id

            v_ring_start_idx = i_major * num_minor_points

            # Cap UV setup (Planar projection, mapped to quadrant)
            u_min, u_max, v_min, v_max = uv_quadrant
            u_scale = u_max - u_min
            v_scale = v_max - v_min

            cap_n_idx = len(self._normals)
            # Normal: Points along the sweep direction (Start Cap: -Z, End Cap: +Z)
            major_angle = i_major * major_angle_step_rad
            cap_norm_x = math.sin(major_angle)
            cap_norm_z = -math.cos(major_angle)

            # Reverse for End Cap to point outwards
            if side_key == 'top_side': # This is the End Cap
                cap_norm_x = -cap_norm_x
                cap_norm_z = -cap_norm_z

            self._normals.append([cap_norm_x, 0.0, cap_norm_z])

            cap_uv_start_idx = len(self._texture_coords)

            # Generate UV coordinates for the cap (simple planar projection, center is (0.5, 0.5) in quadrant)
            for j in range(num_minor_points):
                minor_angle = j * minor_angle_step_rad
                cos_minor = math.cos(minor_angle)
                sin_minor = math.sin(minor_angle)

                # UVs: Map to a circle inside the quadrant (0..1)
                u_cap = (cos_minor * 0.5 + 0.5) * u_scale + u_min
                v_cap = (sin_minor * 0.5 + 0.5) * v_scale + v_min
                self._texture_coords.append([u_cap, v_cap])

            # Generate a center vertex for the cap
            v_center_idx = len(self._vertices)
            # Find the mean position of the ring vertices
            center_pos = np.array([0.0, 0.0, 0.0])
            for j in range(self.minor_segments):
                center_pos += np.array(self._vertices[v_ring_start_idx + j])
            center_pos /= self.minor_segments
            self._vertices.append(center_pos.tolist())

            # Generate center UV
            uv_center = [u_min + 0.5 * u_scale, v_min + 0.5 * v_scale]
            self._texture_coords.append(uv_center)
            uv_center_idx = len(self._texture_coords) - 1

            # Generate faces (Triangles connecting circumference to center point)
            for j in range(self.minor_segments):
                # V indices are from the torus surface generation
                v_curr = v_ring_start_idx + j
                # Use modulo for the next vertex to wrap around the tube
                v_next = v_ring_start_idx + (j + 1) % self.minor_segments

                # UV indices are from the cap UV generation
                uv_curr = cap_uv_start_idx + j
                uv_next = cap_uv_start_idx + (j + 1) % self.minor_segments

                # Triangle face definition
                face = [
                    add_face_vertex(v_center_idx, uv_center_idx, cap_n_idx),
                    add_face_vertex(v_curr, uv_curr, cap_n_idx),
                    add_face_vertex(v_next, uv_next, cap_n_idx),
                ]

                # Ensure consistent winding for caps (reverse order for inner cap to face outwards)
                if side_key == 'in_side':
                    face.reverse()

                self._faces.append(face)
                self.object_semantic[side_key].append({'id': face_id, 'segment': j})
                face_id += 1


        # Generate the two caps using the correct UV quadrant keys
        if self.arc_degrees < 360:
            generate_cap(0, 'in_side', UV_QUADRANTS['in_side']) # Start Cap
            generate_cap(self.major_segments, 'top_side', UV_QUADRANTS['top_side']) # End Cap

        self.body = self

    def write_obj_file(self):
        """
        Writes the generated torus arc geometry to an .obj file, using per-side materials.
        """
        self._generate_geometry() # Now calls the real geometry logic

        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Parametrized Torus Arc .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")

                f.write("o TorusArcBody\n")
                f.write("g TorusArcBody\n")

                # Write V, VT, VN
                for data, prefix in zip([self._vertices, self._texture_coords, self._normals], ['v', 'vt', 'vn']):
                    for item in data:
                        f.write(f"{prefix} {' '.join(f'{x:.6f}' for x in item)}\n")
                    f.write("\n")

                # Mapping the semantic groups (UV quadrant keys) to the MTL names
                face_groups_to_mtl = {
                    'out_side': 'SurfaceMaterial',
                    'in_side': 'StartCapMaterial',
                    'top_side': 'EndCapMaterial'
                }

                # Write F (Faces)
                for side, mtl_name in face_groups_to_mtl.items():
                    f.write(f"\n# Faces for {side}\n")
                    f.write(f"usemtl {mtl_name}\n")
                    f.write("s 1\n")

                    face_indices_for_side = [d['id'] for d in self.object_semantic.get(side, [])]

                    for face_idx in face_indices_for_side:
                        if face_idx < len(self._faces):
                            face = self._faces[face_idx]
                            f.write("f")
                            # Face format: v/vt/vn
                            for v_idx, vt_idx, vn_idx in face:
                                f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                            f.write("\n")

            print(f"Successfully generated {self.output_obj_filepath} with per-side materials (Full Torus Geometry).")

        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def _generate_mtl_aesthetic_params(self) -> Dict[str, str]:
        """
        Translates high-level aesthetics into low-level MTL rendering parameters.
        """
        mtl_lines: Dict[str, str] = {}
        material_key = self.structural_params.get("material", "DEFAULT").upper()

        # --- 1. Shininess/Reflection (Ns / Ks) ---
        ns, ks_r, ks_g, ks_b = MATERIAL_PROPERTIES.get(
            material_key, MATERIAL_PROPERTIES["DEFAULT"]
        )
        mtl_lines["Ns"] = f"Ns {ns:.4f}"
        mtl_lines["Ks"] = f"Ks {ks_r:.6f} {ks_g:.6f} {ks_b:.6f}"

        # --- 2. Ambient (Ka) and Illumination (illum) ---
        ka_rgb_str, kd_factor, probabilistic_illum = probabilistic_ka_kd_illum_mapping(material_key)
        mtl_lines["Ka"] = f"Ka {ka_rgb_str}"

        # --- 3. Transparency (d / illum) with overrides ---
        transparency_value = self.structural_params.get("transparency", 1.0)
        d_value = 1.0
        illum_value = probabilistic_illum

        if material_key in [MATERIAL_TYPE["GLASS"], MATERIAL_TYPE["PLASTIC"]]:
            d_value = transparency_value
            if d_value < 1.0:
                illum_value = random.choice([6, 7])
            elif illum_value < 2:
                illum_value = 2
        else:
            d_value = 1.0
            if illum_value > 2:
                illum_value = 2

        mtl_lines["d"] = f"d {d_value:.4f}"
        mtl_lines["illum"] = f"illum {illum_value}"

        # --- 4. Diffuse Texture Map (map_Kd) ---
        texture_type = self.aesthetics_params.get("texture_type")
        texture_map_filename = None
        if texture_type == TEXTURE_TYPE["PICTURE_T"]:
            texture_data = self.aesthetics_params.get("texture_data", {})
            texture_map_filename = texture_data.get("file_path")
        elif texture_type in [TEXTURE_TYPE["SOLID_T"], TEXTURE_TYPE["PATTERN_T"], TEXTURE_TYPE["GRADIENT_T"]]:
            texture_map_filename = self._generate_texture_file(texture_type)

        if texture_map_filename:
            mtl_lines["map_Kd"] = f"map_Kd {texture_map_filename}"
        else:
            # Set to blank if no map is used, as the color will come from Kd
            mtl_lines["map_Kd"] = ""

        return mtl_lines

    def write_mtl_file(self):
        """
        Generates the .mtl file with a structural metadata block and three aesthetic material blocks.
        """
        mapped_colors = self._get_mapped_colors()
        aesthetic_lines = self._generate_mtl_aesthetic_params()

        structural_lines = []
        for key, value in self.structural_params.items():
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
                # Use the UV quadrant keys for consistency
                material_defs: List[Tuple[str, str]] = [
                    ('SurfaceMaterial', mapped_colors.get('out_side', "1.0 1.0 1.0")),
                    ('StartCapMaterial', mapped_colors.get('in_side', "1.0 1.0 1.0")),
                    ('EndCapMaterial', mapped_colors.get('top_side', "1.0 1.0 1.0")),
                ]

                f.write("# --- Aesthetic Properties (Three Definitions for Per-Side Color) ---\n")
                for mtl_name, diffuse_color_rgb in material_defs:
                    f.write(f"newmtl {mtl_name}\n")

                    for line_type, line_value in aesthetic_lines.items():
                        if line_type not in ["Kd", "map_Kd"]:
                            f.write(f"{line_value}\n")

                    f.write(f"Kd {diffuse_color_rgb}\n")

                    map_kd_line = aesthetic_lines.get('map_Kd', '')
                    if map_kd_line:
                        f.write(f"{map_kd_line}\n")

                    f.write("\n")

            print(f"Successfully generated {self.output_mtl_filepath} with 1 metadata and 3 aesthetic materials.")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        """
        Generates the .obj, .mtl, and any necessary texture files.
        """
        self.write_obj_file()
        self.write_mtl_file()


if __name__ == "__main__":
    # --- EXAMPLE 1: STEEL with GRADIENT Texture ---
    # GEOMETRY defined as direct arguments
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

    generator_steel = TorusGenerator(
        output_name="steel_gradient_torus_arc_test",
        major_radius=6.0, minor_radius=2.0, arc_degrees=120,
        major_segments=40, minor_segments=16,
        aesthetics_params=aesthetics_steel_gradient,
        structural_params=structural_steel_gradient
    )
    generator_steel.generate_files()

    # --- EXAMPLE 2: GLASS with SOLID Texture (Full Torus) ---
    aesthetics_glass_solid = {
        "colors": ["PURPLE"],
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

    generator_glass = TorusGenerator(
        output_name="glass_transparent_torus_test",
        major_radius=4.0, minor_radius=1.0, arc_degrees=360,
        major_segments=50, minor_segments=25,
        aesthetics_params=aesthetics_glass_solid,
        structural_params=structural_glass_solid
    )
    generator_glass.generate_files()

    print("\nFile generation complete with fixed parameter initialization.")

