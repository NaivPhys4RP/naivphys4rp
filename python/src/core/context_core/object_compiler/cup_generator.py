#!/usr/bin/env python3

import math
import numpy as np


# A class to generate a hollow sphere stalk
class SphereGenerator:
    def __init__(self, output_name="textured_thick_spherical_ring",
                 outer_radius=1.0, inner_radius=0.8,
                 start_latitude_deg=-30.0, end_latitude_deg=30.0,
                 segments=40, rings=10, texture_filename="thick_ring_texture.png"):
        if not (0 < inner_radius < outer_radius):
            raise ValueError("Inner radius must be positive and less than outer radius.")
        if not (-90 <= start_latitude_deg < end_latitude_deg <= 90):
            raise ValueError("Invalid latitude range. Must be -90 <= start_lat < end_lat <= 90.")
        if not (segments >= 3 and rings >= 1):
            raise ValueError("Segments must be at least 3, and rings at least 1.")

        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"
        self.texture_filename = texture_filename
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_latitude_rad = math.radians(start_latitude_deg)
        self.end_latitude_rad = math.radians(end_latitude_deg)
        self.segments = segments
        self.rings = rings

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

    def _generate_geometry(self):
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        num_lon_points = self.segments + 1
        num_lat_points = self.rings + 1

        outer_v_start_idx = len(self._vertices)
        outer_n_start_idx = len(self._normals)
        outer_uv_start_idx = len(self._texture_coords)

        for j in range(num_lat_points):
            current_latitude_rad = self.start_latitude_rad + \
                                   (self.end_latitude_rad - self.start_latitude_rad) * j / self.rings
            sin_lat = math.sin(current_latitude_rad)
            cos_lat = math.cos(current_latitude_rad)

            for i in range(num_lon_points):
                current_longitude_rad = 2 * math.pi * i / self.segments
                sin_lon = math.sin(current_longitude_rad)
                cos_lon = math.cos(current_longitude_rad)

                x = self.outer_radius * cos_lat * cos_lon
                y = self.outer_radius * sin_lat
                z = self.outer_radius * cos_lat * sin_lon
                self._vertices.append([x, y, z])

                self._normals.append([-x / self.outer_radius, -y / self.outer_radius, -z / self.outer_radius])

                u = float(i) / self.segments
                v = float(j) / self.rings
                self._texture_coords.append([u, v])

        inner_v_start_idx = len(self._vertices)
        inner_n_start_idx = len(self._normals)
        inner_uv_start_idx = len(self._texture_coords)

        for j in range(num_lat_points):
            current_latitude_rad = self.start_latitude_rad + \
                                   (self.end_latitude_rad - self.start_latitude_rad) * j / self.rings
            sin_lat = math.sin(current_latitude_rad)
            cos_lat = math.cos(current_latitude_rad)

            for i in range(num_lon_points):
                current_longitude_rad = 2 * math.pi * i / self.segments

                sin_lon = math.sin(current_longitude_rad)
                cos_lon = math.cos(current_longitude_rad)

                x = self.inner_radius * cos_lat * cos_lon
                y = self.inner_radius * sin_lat
                z = self.inner_radius * cos_lat * sin_lon
                self._vertices.append([x, y, z])

                self._normals.append([x / self.inner_radius, y / self.inner_radius, z / self.inner_radius])

                u = float(i) / self.segments
                v = float(j) / self.rings
                self._texture_coords.append([u, v])

        top_cap_n_idx = len(self._normals)
        self._normals.append([0.0, 1.0, 0.0])

        bottom_cap_n_idx = len(self._normals)
        self._normals.append([0.0, -1.0, 0.0])

        cap_uv_start_idx = len(self._texture_coords)

        for i in range(num_lon_points):
            x_outer_top = self.outer_radius * math.cos(self.end_latitude_rad) * math.cos(
                2 * math.pi * i / self.segments)
            z_outer_top = self.outer_radius * math.cos(self.end_latitude_rad) * math.sin(
                2 * math.pi * i / self.segments)
            self._texture_coords.append(
                [x_outer_top / (2 * self.outer_radius) + 0.5, z_outer_top / (2 * self.outer_radius) + 0.5])

            x_inner_top = self.inner_radius * math.cos(self.end_latitude_rad) * math.cos(
                2 * math.pi * i / self.segments)
            z_inner_top = self.inner_radius * math.cos(self.end_latitude_rad) * math.sin(
                2 * math.pi * i / self.segments)
            self._texture_coords.append(
                [x_inner_top / (2 * self.outer_radius) + 0.5, z_inner_top / (2 * self.outer_radius) + 0.5])

        for i in range(num_lon_points):
            x_outer_bottom = self.outer_radius * math.cos(self.start_latitude_rad) * math.cos(
                2 * math.pi * i / self.segments)
            z_outer_bottom = self.outer_radius * math.cos(self.start_latitude_rad) * math.sin(
                2 * math.pi * i / self.segments)
            self._texture_coords.append(
                [x_outer_bottom / (2 * self.outer_radius) + 0.5, z_outer_bottom / (2 * self.outer_radius) + 0.5])

            x_inner_bottom = self.inner_radius * math.cos(self.start_latitude_rad) * math.cos(
                2 * math.pi * i / self.segments)
            z_inner_bottom = self.inner_radius * math.cos(self.start_latitude_rad) * math.sin(
                2 * math.pi * i / self.segments)
            self._texture_coords.append(
                [x_inner_bottom / (2 * self.outer_radius) + 0.5, z_inner_bottom / (2 * self.outer_radius) + 0.5])

        for j in range(self.rings):
            for i in range(self.segments):
                p1 = j * num_lon_points + i
                p2 = j * num_lon_points + (i + 1)
                p3 = (j + 1) * num_lon_points + (i + 1)
                p4 = (j + 1) * num_lon_points + i

                v1_idx = outer_v_start_idx + p1
                v2_idx = outer_v_start_idx + p2
                v3_idx = outer_v_start_idx + p3
                v4_idx = outer_v_start_idx + p4

                n1_idx = outer_n_start_idx + p1
                n2_idx = outer_n_start_idx + p2
                n3_idx = outer_n_start_idx + p3
                n4_idx = outer_n_start_idx + p4

                uv1_idx = outer_uv_start_idx + p1
                uv2_idx = outer_uv_start_idx + p2
                uv3_idx = outer_uv_start_idx + p3
                uv4_idx = outer_uv_start_idx + p4

                self._faces.append([
                    add_face_vertex(v1_idx, uv1_idx, n1_idx),
                    add_face_vertex(v4_idx, uv4_idx, n4_idx),
                    add_face_vertex(v3_idx, uv3_idx, n3_idx),
                    add_face_vertex(v2_idx, uv2_idx, n2_idx)
                ])

        for j in range(self.rings):
            for i in range(self.segments):
                p1 = j * num_lon_points + i
                p2 = j * num_lon_points + (i + 1)
                p3 = (j + 1) * num_lon_points + (i + 1)
                p4 = (j + 1) * num_lon_points + i

                v1_idx = inner_v_start_idx + p1
                v2_idx = inner_v_start_idx + p2
                v3_idx = inner_v_start_idx + p3
                v4_idx = inner_v_start_idx + p4

                n1_idx = inner_n_start_idx + p1
                n2_idx = inner_n_start_idx + p2
                n3_idx = inner_n_start_idx + p3
                n4_idx = inner_n_start_idx + p4

                uv1_idx = inner_uv_start_idx + p1
                uv2_idx = inner_uv_start_idx + p2
                uv3_idx = inner_uv_start_idx + p3
                uv4_idx = inner_uv_start_idx + p4

                self._faces.append([
                    add_face_vertex(v1_idx, uv1_idx, n1_idx),
                    add_face_vertex(v2_idx, uv2_idx, n2_idx),
                    add_face_vertex(v3_idx, uv3_idx, n3_idx),
                    add_face_vertex(v4_idx, uv4_idx, n4_idx)
                ])

        uv_outer_top_offset = cap_uv_start_idx
        uv_inner_top_offset = cap_uv_start_idx + num_lon_points
        for i in range(self.segments):
            v1_outer_top_idx = outer_v_start_idx + self.rings * num_lon_points + i
            v2_outer_top_idx = outer_v_start_idx + self.rings * num_lon_points + (i + 1)
            v1_inner_top_idx = inner_v_start_idx + self.rings * num_lon_points + i
            v2_inner_top_idx = inner_v_start_idx + self.rings * num_lon_points + (i + 1)

            uv1_outer_top_idx = uv_outer_top_offset + i
            uv2_outer_top_idx = uv_outer_top_offset + (i + 1)
            uv1_inner_top_idx = uv_inner_top_offset + i
            uv2_inner_top_idx = uv_inner_top_offset + (i + 1)

            self._faces.append([
                add_face_vertex(v1_inner_top_idx, uv1_inner_top_idx, top_cap_n_idx),
                add_face_vertex(v2_inner_top_idx, uv2_inner_top_idx, top_cap_n_idx),
                add_face_vertex(v2_outer_top_idx, uv2_outer_top_idx, top_cap_n_idx),
                add_face_vertex(v1_outer_top_idx, uv1_outer_top_idx, top_cap_n_idx)
            ])

        uv_outer_bottom_offset = cap_uv_start_idx + 2 * num_lon_points
        uv_inner_bottom_offset = cap_uv_start_idx + 3 * num_lon_points
        for i in range(self.segments):
            v1_outer_bottom_idx = outer_v_start_idx + 0 * num_lon_points + i
            v2_outer_bottom_idx = outer_v_start_idx + 0 * num_lon_points + (i + 1)
            v1_inner_bottom_idx = inner_v_start_idx + 0 * num_lon_points + i
            v2_inner_bottom_idx = inner_v_start_idx + 0 * num_lon_points + (i + 1)

            uv1_outer_bottom_idx = uv_outer_bottom_offset + i
            uv2_outer_bottom_idx = uv_outer_bottom_offset + (i + 1)
            uv1_inner_bottom_idx = uv_inner_bottom_offset + i
            uv2_inner_bottom_idx = uv_inner_bottom_offset + (i + 1)

            self._faces.append([
                add_face_vertex(v1_outer_bottom_idx, uv1_outer_bottom_idx, bottom_cap_n_idx),
                add_face_vertex(v2_outer_bottom_idx, uv2_outer_bottom_idx, bottom_cap_n_idx),
                add_face_vertex(v2_inner_bottom_idx, uv2_inner_bottom_idx, bottom_cap_n_idx),
                add_face_vertex(v1_inner_bottom_idx, uv1_inner_bottom_idx, bottom_cap_n_idx)
            ])

    def write_obj_file(self):
        self._generate_geometry()
        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Textured Thick Spherical Ring .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")
                f.write("o ThickSphericalRing\n")
                f.write("g ThickSphericalRingBody\n")

                for v in self._vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                f.write("\n")
                for vt in self._texture_coords:
                    f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                f.write("\n")
                for vn in self._normals:
                    f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
                f.write("\n")

                f.write("usemtl ThickSphericalRingMaterial\n")
                f.write("s 1\n")

                for face in self._faces:
                    f.write("f")
                    for v_idx, vt_idx, vn_idx in face:
                        f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                    f.write("\n")
                print(f"Successfully generated {self.output_obj_filepath}")

        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def write_mtl_file(self):
        try:
            with open(self.output_mtl_filepath, 'w') as f:
                f.write(f"# Generated Material Library for {self.output_obj_filepath}\n\n")
                f.write("newmtl ThickSphericalRingMaterial\n")
                f.write("Ns 96.078431\n")
                f.write("Ka 1.000000 1.000000 1.000000\n")
                f.write("Kd 1.000000 1.000000 1.000000\n")
                f.write("Ks 0.500000 0.500000 0.500000\n")
                f.write("d 1.0\n")
                f.write("illum 2\n")
                f.write(f"map_Kd {self.texture_filename}\n")
            print(f"Successfully generated {self.output_mtl_filepath}")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        self.write_obj_file()
        self.write_mtl_file()


# A class to generate a hollow torus arc
class TorusGenerator:
    def __init__(self, output_name="textured_hollow_torus_arc",
                 major_radius=3.0, minor_radius=0.5, inner_radius=0.3,
                 arc_degrees=270,
                 major_segments=32,
                 minor_segments=16,
                 texture_filename="torus_arc_texture.png"):
        if not (major_radius > 0 and minor_radius > 0 and inner_radius > 0):
            raise ValueError("Radii must be positive.")
        if not (inner_radius < minor_radius):
            raise ValueError("Inner radius must be less than minor radius for a hollow tube.")
        if not (major_segments >= 3 and minor_segments >= 3):
            raise ValueError("Segments must be at least 3 for valid polygons.")
        if not (0 < arc_degrees <= 360):
            raise ValueError("Arc degrees must be between 0 (exclusive) and 360 (inclusive).")

        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"
        self.texture_filename = texture_filename

        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.inner_radius = inner_radius
        self.arc_degrees = arc_degrees
        self.major_segments = major_segments
        self.minor_segments = minor_segments

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

    def _generate_geometry(self):
        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

        def add_face_vertex(v_idx, uv_idx, n_idx):
            return (v_idx + 1, uv_idx + 1, n_idx + 1)

        major_angle_step_rad = (self.arc_degrees / self.major_segments) * (math.pi / 180)
        minor_angle_step_rad = (2 * math.pi) / self.minor_segments

        num_major_points = self.major_segments + 1
        num_minor_points = self.minor_segments + 1

        for i in range(num_major_points):
            major_angle = i * major_angle_step_rad
            cos_major = math.cos(major_angle)
            sin_major = math.sin(major_angle)

            for j in range(num_minor_points):
                minor_angle = j * minor_angle_step_rad
                cos_minor = math.cos(minor_angle)
                sin_minor = math.sin(minor_angle)

                x_outer = (self.major_radius + self.minor_radius * cos_minor) * cos_major
                y_outer = self.minor_radius * sin_minor
                z_outer = (self.major_radius + self.minor_radius * cos_minor) * sin_major
                self._vertices.append([x_outer, y_outer, z_outer])

                norm_x_outer = -cos_minor * cos_major
                norm_y_outer = -sin_minor
                norm_z_outer = -cos_minor * sin_major
                self._normals.append([norm_x_outer, norm_y_outer, norm_z_outer])

                u = float(i) / self.major_segments
                v = float(j) / self.minor_segments
                self._texture_coords.append([u, v])

                x_inner = (self.major_radius + self.inner_radius * cos_minor) * cos_major
                y_inner = self.inner_radius * sin_minor
                z_inner = (self.major_radius + self.inner_radius * cos_minor) * sin_major
                self._vertices.append([x_inner, y_inner, z_inner])

                norm_x_inner = cos_minor * cos_major
                norm_y_inner = sin_minor
                norm_z_inner = cos_minor * sin_major
                self._normals.append([norm_x_inner, norm_y_inner, norm_z_inner])

                self._texture_coords.append([u, v])

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

                self._faces.append([
                    add_face_vertex(idx_o_curr_curr, idx_o_curr_curr, idx_o_curr_curr),
                    add_face_vertex(idx_o_curr_next, idx_o_curr_next, idx_o_curr_next),
                    add_face_vertex(idx_o_next_next, idx_o_next_next, idx_o_next_next),
                    add_face_vertex(idx_o_next_curr, idx_o_next_curr, idx_o_next_curr)
                ])

                self._faces.append([
                    add_face_vertex(idx_i_curr_curr, idx_i_curr_curr, idx_i_curr_curr),
                    add_face_vertex(idx_i_next_curr, idx_i_next_curr, idx_i_next_curr),
                    add_face_vertex(idx_i_next_next, idx_i_next_next, idx_i_next_next),
                    add_face_vertex(idx_i_curr_next, idx_i_curr_next, idx_i_curr_next)
                ])

        j_top_segment = round(0.25 * self.minor_segments)
        j_bottom_segment = round(0.75 * self.minor_segments)

        for i in range(self.major_segments):
            idx_o_curr_top = (i * num_minor_points + j_top_segment) * 2
            idx_o_next_top = ((i + 1) * num_minor_points + j_top_segment) * 2
            idx_i_curr_top = idx_o_curr_top + 1
            idx_i_next_top = idx_o_next_top + 1

            v_o_curr_top = np.array(self._vertices[idx_o_curr_top])
            v_o_next_top = np.array(self._vertices[idx_o_next_top])
            v_i_next_top = np.array(self._vertices[idx_i_next_top])
            v_i_curr_top = np.array(self._vertices[idx_i_curr_top])

            edge1 = v_i_curr_top - v_o_curr_top
            edge2 = v_o_next_top - v_o_curr_top

            normal_top_rim = np.cross(edge1, edge2)
            normal_top_rim = normal_top_rim / np.linalg.norm(normal_top_rim)

            top_rim_n_idx = len(self._normals)
            self._normals.append(normal_top_rim.tolist())

            self._faces.append([
                add_face_vertex(idx_o_curr_top, idx_o_curr_top, top_rim_n_idx),
                add_face_vertex(idx_i_curr_top, idx_i_curr_top, top_rim_n_idx),
                add_face_vertex(idx_i_next_top, idx_i_next_top, top_rim_n_idx),
                add_face_vertex(idx_o_next_top, idx_o_next_top, top_rim_n_idx)
            ])

            idx_o_curr_bottom = (i * num_minor_points + j_bottom_segment) * 2
            idx_o_next_bottom = ((i + 1) * num_minor_points + j_bottom_segment) * 2
            idx_i_curr_bottom = idx_o_curr_bottom + 1
            idx_i_next_bottom = idx_o_next_bottom + 1

            v_o_curr_bottom = np.array(self._vertices[idx_o_curr_bottom])
            v_o_next_bottom = np.array(self._vertices[idx_o_next_bottom])
            v_i_next_bottom = np.array(self._vertices[idx_i_next_bottom])
            v_i_curr_bottom = np.array(self._vertices[idx_i_curr_bottom])

            edge1 = v_o_next_bottom - v_o_curr_bottom
            edge2 = v_i_curr_bottom - v_o_curr_bottom

            normal_bottom_rim = np.cross(edge1, edge2)
            normal_bottom_rim = normal_bottom_rim / np.linalg.norm(normal_bottom_rim)

            bottom_rim_n_idx = len(self._normals)
            self._normals.append(normal_bottom_rim.tolist())

            self._faces.append([
                add_face_vertex(idx_o_curr_bottom, idx_o_curr_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_o_next_bottom, idx_o_next_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_i_next_bottom, idx_i_next_bottom, bottom_rim_n_idx),
                add_face_vertex(idx_i_curr_bottom, idx_i_curr_bottom, bottom_rim_n_idx)
            ])

        if self.arc_degrees < 360:
            start_cap_normal = np.array([-1.0, 0.0, 0.0])
            start_cap_n_idx = len(self._normals)
            self._normals.append(start_cap_normal.tolist())

            for j in range(self.minor_segments):
                idx_o_curr = (0 * num_minor_points + j) * 2
                idx_o_next = (0 * num_minor_points + (j + 1)) * 2
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

                temp_uv_o_curr_idx = len(self._texture_coords)
                self._texture_coords.append(uv_o_curr)
                temp_uv_o_next_idx = len(self._texture_coords)
                self._texture_coords.append(uv_o_next)
                temp_uv_i_curr_idx = len(self._texture_coords)
                self._texture_coords.append(uv_i_curr)
                temp_uv_i_next_idx = len(self._texture_coords)
                self._texture_coords.append(uv_i_next)

                self._faces.append([
                    add_face_vertex(idx_o_curr, temp_uv_o_curr_idx, start_cap_n_idx),
                    add_face_vertex(idx_i_curr, temp_uv_i_curr_idx, start_cap_n_idx),
                    add_face_vertex(idx_i_next, temp_uv_i_next_idx, start_cap_n_idx),
                    add_face_vertex(idx_o_next, temp_uv_o_next_idx, start_cap_n_idx)
                ])

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

                temp_uv_o_curr_idx = len(self._texture_coords)
                self._texture_coords.append(uv_o_curr)
                temp_uv_o_next_idx = len(self._texture_coords)
                self._texture_coords.append(uv_o_next)
                temp_uv_i_curr_idx = len(self._texture_coords)
                self._texture_coords.append(uv_i_curr)
                temp_uv_i_next_idx = len(self._texture_coords)
                self._texture_coords.append(uv_i_next)

                self._faces.append([
                    add_face_vertex(idx_o_curr, temp_uv_o_curr_idx, end_cap_n_idx),
                    add_face_vertex(idx_o_next, temp_uv_o_next_idx, end_cap_n_idx),
                    add_face_vertex(idx_i_next, temp_uv_i_next_idx, end_cap_n_idx),
                    add_face_vertex(idx_i_curr, temp_uv_i_curr_idx, end_cap_n_idx)
                ])

    def write_obj_file(self):
        self._generate_geometry()
        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Textured Hollow Torus Arc .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")
                f.write("o TorusArc\n")
                f.write("g TorusArcBody\n")

                for v in self._vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                f.write("\n")
                for vt in self._texture_coords:
                    f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                f.write("\n")
                for vn in self._normals:
                    f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
                f.write("\n")

                f.write("usemtl TorusArcMaterial\n")
                f.write("s 1\n")

                for face in self._faces:
                    f.write("f")
                    for v_idx, vt_idx, vn_idx in face:
                        f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                    f.write("\n")
                print(f"Successfully generated {self.output_obj_filepath}")

        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def write_mtl_file(self):
        try:
            with open(self.output_mtl_filepath, 'w') as f:
                f.write(f"# Generated Material Library for {self.output_obj_filepath}\n\n")
                f.write("newmtl TorusArcMaterial\n")
                f.write("Ns 96.078431\n")
                f.write("Ka 1.000000 1.000000 1.000000\n")
                f.write("Kd 1.000000 1.000000 1.000000\n")
                f.write("Ks 0.500000 0.500000 0.500000\n")
                f.write("d 1.0\n")
                f.write("illum 2\n")
                f.write(f"map_Kd {self.texture_filename}\n")
            print(f"Successfully generated {self.output_mtl_filepath}")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        self.write_obj_file()
        self.write_mtl_file()


# The final class to generate a cup by combining the two above
class CupGenerator:
    def __init__(self, output_name="cup", cup_height=1.5, cup_radius=1.5, cup_wall_thickness=0.2,
                 handle_major_radius=1.8, handle_minor_radius=0.2, handle_arc=180,
                 handle_y_offset=0.25):
        self.output_name = output_name
        self.output_obj_filepath = f"{output_name}.obj"
        self.output_mtl_filepath = f"{output_name}.mtl"

        self.cup_height = cup_height
        self.cup_radius = cup_radius
        self.cup_wall_thickness = cup_wall_thickness
        self.cup_outer_radius = cup_radius
        self.cup_inner_radius = cup_radius - cup_wall_thickness

        self.handle_major_radius = handle_major_radius
        self.handle_minor_radius = handle_minor_radius
        self.handle_arc = handle_arc
        self.handle_y_offset = handle_y_offset

        self._vertices = []
        self._texture_coords = []
        self._normals = []
        self._faces = []

    def _generate_cup_body(self):
        if self.cup_height > self.cup_outer_radius:
            raise ValueError("Cup height cannot be greater than the outer radius for this geometry.")

        start_latitude_deg = 0.0
        end_latitude_deg = math.degrees(math.asin(self.cup_height / self.cup_outer_radius))

        sphere_generator = SphereGenerator(
            outer_radius=self.cup_outer_radius,
            inner_radius=self.cup_inner_radius,
            start_latitude_deg=start_latitude_deg,
            end_latitude_deg=end_latitude_deg,
            segments=64,
            rings=32,
            output_name="cup_body"
        )
        sphere_generator._generate_geometry()
        return sphere_generator._vertices, sphere_generator._normals, sphere_generator._texture_coords, sphere_generator._faces

    def _generate_cup_handle(self):
        torus_generator = TorusGenerator(
            major_radius=self.handle_major_radius,
            minor_radius=self.handle_minor_radius,
            inner_radius=self.handle_minor_radius * 0.5,
            arc_degrees=self.handle_arc,
            major_segments=32,
            minor_segments=16,
            output_name="cup_handle"
        )
        torus_generator._generate_geometry()

        handle_vertices = np.array(torus_generator._vertices)
        handle_normals = np.array(torus_generator._normals)
        handle_faces = torus_generator._faces
        handle_uvs = torus_generator._texture_coords

        # Calculate attachment points on the cup body
        lat_rad = math.asin(self.handle_y_offset / self.cup_outer_radius)
        z_offset = self.cup_outer_radius * math.cos(lat_rad)

        point1 = np.array([0, self.handle_y_offset, -z_offset])
        point2 = np.array([0, self.handle_y_offset, z_offset])

        # Calculate start and end points of the raw handle
        major_angle_rad = self.handle_arc * (math.pi / 180)
        start_handle_point = np.array([
            (self.handle_major_radius + self.handle_minor_radius * math.cos(0)) * math.cos(0),
            self.handle_minor_radius * math.sin(0),
            (self.handle_major_radius + self.handle_minor_radius * math.cos(0)) * math.sin(0)
        ])

        end_handle_point = np.array([
            (self.handle_major_radius + self.handle_minor_radius * math.cos(0)) * math.cos(major_angle_rad),
            self.handle_minor_radius * math.sin(0),
            (self.handle_major_radius + self.handle_minor_radius * math.cos(0)) * math.sin(major_angle_rad)
        ])

        # Determine the transformation matrix to align the handle
        center_of_handle = (start_handle_point + end_handle_point) / 2

        translation_vec = (point1 + point2) / 2 - center_of_handle

        # Transform the handle
        transformed_vertices = handle_vertices + translation_vec

        # Calculate rotation to point handle away from cup center
        handle_direction = end_handle_point - start_handle_point
        handle_direction = handle_direction / np.linalg.norm(handle_direction)

        cup_direction = point2 - point1
        cup_direction = cup_direction / np.linalg.norm(cup_direction)

        # Create a rotation matrix to align the handle with the cup
        rotation_axis = np.cross(handle_direction, cup_direction)
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

        angle = np.arccos(np.dot(handle_direction, cup_direction))

        if np.isclose(np.linalg.norm(rotation_axis), 0):
            rotation_matrix = np.identity(3)
        else:
            s = math.sin(angle)
            c = math.cos(angle)
            C = 1 - c
            x, y, z = rotation_axis
            rotation_matrix = np.array([
                [x * x * C + c, x * y * C - z * s, x * z * C + y * s],
                [y * x * C + z * s, y * y * C + c, y * z * C - x * s],
                [z * x * C - y * s, z * y * C + x * s, z * z * C + c]
            ])

        rotated_vertices = np.dot(transformed_vertices, rotation_matrix.T)
        rotated_normals = np.dot(handle_normals, rotation_matrix.T)

        return rotated_vertices.tolist(), rotated_normals.tolist(), handle_uvs, handle_faces

    def _merge_geometry(self, body_data, handle_data):
        body_vertices, body_normals, body_uvs, body_faces = body_data
        handle_vertices, handle_normals, handle_uvs, handle_faces = handle_data

        handle_v_start_idx = len(body_vertices)
        handle_n_start_idx = len(body_normals)
        handle_uv_start_idx = len(body_uvs)

        self._vertices = body_vertices + handle_vertices
        self._normals = body_normals + handle_normals
        self._texture_coords = body_uvs + handle_uvs

        self._faces = body_faces
        for face in handle_faces:
            new_face = []
            for v_idx, uv_idx, n_idx in face:
                new_face.append((v_idx + handle_v_start_idx, uv_idx + handle_uv_start_idx, n_idx + handle_n_start_idx))
            self._faces.append(new_face)

    def write_obj_file(self):
        body_data = self._generate_cup_body()
        handle_data = self._generate_cup_handle()
        self._merge_geometry(body_data, handle_data)

        try:
            with open(self.output_obj_filepath, 'w') as f:
                f.write(f"# Generated Cup .obj file\n")
                f.write(f"mtllib {self.output_mtl_filepath.split('/')[-1]}\n\n")
                f.write("o Cup\n")
                f.write("g CupBody\n")

                for v in self._vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                f.write("\n")
                for vt in self._texture_coords:
                    f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                f.write("\n")
                for vn in self._normals:
                    f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
                f.write("\n")

                f.write("usemtl CupMaterial\n")
                f.write("s 1\n")
                for face in self._faces:
                    f.write("f")
                    for v_idx, vt_idx, vn_idx in face:
                        f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                    f.write("\n")
                print(f"Successfully generated {self.output_obj_filepath}")
        except Exception as e:
            print(f"An error occurred while writing the .obj file: {e}")

    def write_mtl_file(self):
        try:
            with open(self.output_mtl_filepath, 'w') as f:
                f.write(f"# Generated Material Library for {self.output_obj_filepath}\n\n")
                f.write("newmtl CupMaterial\n")
                f.write("Ns 96.078431\n")
                f.write("Ka 1.000000 1.000000 1.000000\n")
                f.write("Kd 1.000000 1.000000 1.000000\n")
                f.write("Ks 0.500000 0.500000 0.500000\n")
                f.write("d 1.0\n")
                f.write("illum 2\n")
            print(f"Successfully generated {self.output_mtl_filepath}")
        except Exception as e:
            print(f"An error occurred while writing the .mtl file: {e}")

    def generate_files(self):
        self.write_obj_file()
        self.write_mtl_file()


if __name__ == "__main__":
    cup_generator = CupGenerator(
        cup_height=1.5,
        cup_radius=2,
        cup_wall_thickness=0.1,
        handle_major_radius=1.8,
        handle_minor_radius=0.1,
        handle_arc=180,
        handle_y_offset=0.25
    )
    cup_generator.generate_files()
    print("Check your directory for 'cup.obj' and '.mtl' files.")