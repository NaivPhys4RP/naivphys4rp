import json
import os
import datetime
import math
from cone_generator import ConeGenerator
from shelf import SimpleShelfAssembler
from sphere_generator import SphereGenerator
from spoon import SimpleSpoonAssembler
from torus_generator import TorusGenerator
from torus_support_generator import TorusSupportGenerator
from cone_support_generator import ConeSupportGenerator
from sphere_support_generator import SphereSupportGenerator
from common import *
from scene_objects import *
from usd_generator import MultiModelGenerator
from mug import *
from plate import *
from bowl import *
from table import *
from drawer import *
from bottle import *
from primitive import *
from chair import *
import random


class ObjectCompiler():
    def __init__(self):
        # Define the recognized primitive keys within the class
        self.index=0
        self.primitive_keys = [
            "torus_closed_shape", "spherical_closed_shape", "conical_hollow_shape",
            "conical_closed_shape", "spherical_hollow_shape", "torus_hollow_shape"
        ]

    def clamp_cone_parameters(self, dimensions):
        outer_bottom_radius = max(dimensions.get("outer_bottom_radius", 1.0), 0.01)
        outer_top_radius = max(dimensions.get("outer_top_radius", 0.1), 0.0)
        inner_bottom_radius = max(dimensions.get("inner_bottom_radius", 0.1), 0.01)
        if inner_bottom_radius >= outer_bottom_radius: inner_bottom_radius = outer_bottom_radius * 0.9
        inner_top_radius = max(dimensions.get("inner_top_radius", 0.0), 0.0)
        if inner_top_radius >= outer_top_radius: inner_top_radius = outer_top_radius * 0.9
        height = max(dimensions.get("height", 1.0), 0.01)
        segments = max(int(dimensions.get("segments", 3)), 3)
        height_subdivisions = max(int(dimensions.get("rings", 1)), 1)
        return {
            "outer_bottom_radius": outer_bottom_radius, "outer_top_radius": outer_top_radius,
            "inner_bottom_radius": inner_bottom_radius, "inner_top_radius": inner_top_radius,
            "height": height, "segments": segments, "height_subdivisions": height_subdivisions
        }

    def clamp_closed_sphere_parameters(self, dimensions):
        outer_radius = max(dimensions.get("outer_radius", 1.0), 0.01)
        segments = max(int(dimensions.get("segments", 16)), 3)
        rings = max(int(dimensions.get("rings", 8)), 1)
        start_lat, end_lat = dimensions.get("start_latitude_deg", -90.0), dimensions.get("end_latitude_deg", 90.0)
        if end_lat <= start_lat: start_lat, end_lat = end_lat, start_lat
        return {
            "outer_radius": outer_radius, "segments": segments, "rings": rings,
            "start_latitude_deg": max(-90.0, min(start_lat, 90.0)),
            "end_latitude_deg": max(-90.0, min(end_lat, 90.0))
        }

    def clamp_sphere_parameters(self, dimensions):
        outer_radius = max(dimensions.get("outer_radius", 1.0), 0.01)
        inner_radius = max(dimensions.get("inner_radius", 1.0), 0.01)
        segments, rings = max(int(dimensions.get("segments", 16)), 3), max(int(dimensions.get("rings", 8)), 1)
        start_lat, end_lat = dimensions.get("start_latitude_deg", -90.0), dimensions.get("end_latitude_deg", 90.0)
        if end_lat <= start_lat: start_lat, end_lat = end_lat, start_lat
        if outer_radius <= inner_radius: inner_radius, outer_radius = outer_radius * 0.9, outer_radius
        return {
            "outer_radius": outer_radius, "inner_radius": inner_radius, "segments": segments, "rings": rings,
            "start_latitude_deg": max(-90.0, min(start_lat, 90.0)),
            "end_latitude_deg": max(-90.0, min(end_lat, 90.0))
        }

    def clamp_torus_parameters(self, dimensions):
        major_radius, minor_radius = max(dimensions.get("major_radius", 1.0), 0.01), max(
            dimensions.get("minor_radius", 0.1), 0.01)
        inner_radius = max(dimensions.get("inner_radius", 0.005), 0.005)
        if inner_radius >= minor_radius: inner_radius = minor_radius * 0.9
        return {
            "major_radius": major_radius, "minor_radius": minor_radius, "inner_radius": inner_radius,
            "arc_degrees": max(min(dimensions.get("arc_degrees", 360.0), 360.0), 0.01),
            "major_segments": max(int(dimensions.get("major_segments", 32)), 3),
            "minor_segments": max(int(dimensions.get("minor_segments", 16)), 3)
        }

    def clamp_closed_torus_parameters(self, dimensions):
        return {
            "major_radius": max(dimensions.get("major_radius", 1.0), 0.01),
            "minor_radius": max(dimensions.get("minor_radius", 0.1), 0.01),
            "arc_degrees": max(min(dimensions.get("arc_degrees", 360.0), 360.0), 0.01),
            "major_segments": max(int(dimensions.get("major_segments", 32)), 3),
            "minor_segments": max(int(dimensions.get("minor_segments", 16)), 3)
        }

    def clamp_closed_cone_parameters(self, dimensions):
        return {
            "bottom_outer_radius": max(dimensions.get("outer_bottom_radius", 1.0), 0.00),
            "top_outer_radius": max(dimensions.get("outer_top_radius", 0.1), 0.0),
            "height": max(dimensions.get("height", 1.0), 0.0),
            "segments": max(int(dimensions.get("segments", 3)), 3),
            "height_subdivisions": max(int(dimensions.get("rings", 1)), 1)
        }

    def extract_parameters(self, shape_json):
        shape_key = next(iter(shape_json))
        shape_data = shape_json[shape_key]
        aesthetics = shape_data.get("aesthetics", {})
        structural = shape_data.get("structural", {})

        aesthetics_params = {
            "colors": aesthetics.get("colors", []),
            "texture_type": TEXTURE_TYPE.get(aesthetics.get("texture"), aesthetics.get("texture")),
            "texture_data": {}
        }
        structural_params = {
            "material": MATERIAL_TYPE.get(structural.get("material"), structural.get("material")),
            "fragility_rate": structural.get("fragility_rate", 0.0),
            "density": structural.get("density", 0.0),
            "friction": structural.get("friction", 0.0),
            "restitution": structural.get("restitution", 0.0),
            "absolute_fragility": structural.get("absolute_fragility", 0.0),
            "transparency": structural.get("transparency", 1.0)
        }
        return aesthetics_params, structural_params


    def compile_object_from_json(self, json_data, output_dir="."):
        try:
            unique_id = datetime.datetime.now().strftime("%H%M%S_%f")
            shape_key = next(iter(json_data))
            prefix = shape_key.replace("_shape", "")
            generated_id = f"{prefix}_{unique_id}"
            output_path = os.path.join(output_dir, generated_id)

            if "torus_closed_shape" in json_data:
                shape = json_data["torus_closed_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_closed_torus_parameters(shape.get("dimensions", {}))
                generator = TorusSupportGenerator(output_name=output_path, **params, aesthetics_params=aesthetics,
                                                  structural_params=structure)
            elif "spherical_closed_shape" in json_data:
                shape = json_data["spherical_closed_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_closed_sphere_parameters(shape.get("dimensions", {}))
                generator = SphereSupportGenerator(output_name=output_path, **params, aesthetics_params=aesthetics,
                                                   structural_params=structure)
            elif "conical_hollow_shape" in json_data:
                shape = json_data["conical_hollow_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_cone_parameters(shape.get("dimensions", {}))
                generator = ConeGenerator(output_name=output_path, **params, aesthetics_params=aesthetics,
                                          structural_params=structure)
            elif "conical_closed_shape" in json_data:
                shape = json_data["conical_closed_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_closed_cone_parameters(shape.get("dimensions", {}))
                generator = ConeSupportGenerator(output_name=output_path,
                                                 outer_bottom_radius=params["bottom_outer_radius"],
                                                 outer_top_radius=params["top_outer_radius"], height=params["height"],
                                                 segments=params["segments"],
                                                 height_subdivisions=params["height_subdivisions"],
                                                 aesthetics_params=aesthetics, structural_params=structure)
            elif "spherical_hollow_shape" in json_data:
                shape = json_data["spherical_hollow_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_sphere_parameters(shape.get("dimensions", {}))
                generator = SphereGenerator(output_name=output_path, **params, aesthetics_params=aesthetics,
                                            structural_params=structure)
            elif "torus_hollow_shape" in json_data:
                shape = json_data["torus_hollow_shape"]
                aesthetics, structure = self.extract_parameters(json_data)
                params = self.clamp_torus_parameters(shape.get("dimensions", {}))
                generator = TorusGenerator(output_name=output_path, **params, aesthetics_params=aesthetics,
                                           structural_params=structure)
            else:
                return None, json_data

            generator.generate_files()
            json_data[shape_key]["generated_id"] = generated_id
            return generator, json_data
        except Exception as e:
            print(f"Error compiling shape: {e}")
            return None, json_data

    def _recursive_traverse(self, data, folder_path, results):
        if isinstance(data, dict):
            for key in self.primitive_keys:
                if key in data:
                    temp_shape_dict = {key: data[key]}
                    # This calls your existing compile method logic
                    gen, updated_shape_dict = self.compile_object_from_json(temp_shape_dict, folder_path)
                    if gen:
                        data[key] = updated_shape_dict[key]
                        results.append(gen)
                    # REMOVED 'return' HERE so it keeps looking for base/handle
            for v in data.values():
                self._recursive_traverse(v, folder_path, results)
        elif isinstance(data, list):
            for item in data:
                self._recursive_traverse(item, folder_path, results)

    def compile(self, json_data):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = f"compilation_{timestamp}"
        os.makedirs(session_folder, exist_ok=True)
        if "scene_object" in json_data:
            json_data["generated_id"] = session_folder
        generated_instances = []
        self._recursive_traverse(json_data, session_folder, generated_instances)
        print(f"\nCompilation finished. Generated {len(generated_instances)} instances.")
        print(f"Main Scene ID: {session_folder}")
        return generated_instances, json_data

    def generate_assembly_test(self, indexed_json):
        import datetime
        import os
        session_folder = indexed_json.get("generated_id", "default_session")
        output_name = f"usd_assembly_{datetime.datetime.now().strftime('%H%M%S')}"
        output_path = os.path.join(session_folder, output_name)
        assembly_gen = MultiModelGenerator(output_path)

        parts_paths = []
        collected_dicts = []
        parent_map = {}

        # Step 1: Improved Collection with parenting logic
        def collect_shapes(data, parent_idx=None):
            if isinstance(data, dict):
                found_shape_key = next((k for k in self.primitive_keys if k in data), None)

                current_tracker_idx = parent_idx

                if found_shape_key:
                    # Ensure physical file exists (triggers your blender logic if missing)
                    obj_id = data[found_shape_key].get("generated_id")
                    if not obj_id:
                        # This part was missed by the initial compile pass
                        # We use your existing traverse logic to compile it now
                        temp_results = []
                        self._recursive_traverse(data, session_folder, temp_results)
                        obj_id = data[found_shape_key].get("generated_id")

                    if obj_id:
                        file_path = os.path.join(session_folder, f"{obj_id}.obj")
                        parts_paths.append(file_path)
                        collected_dicts.append(data)

                        new_idx = len(parts_paths) - 1
                        if parent_idx is not None:
                            parent_map[new_idx] = parent_idx
                        current_tracker_idx = new_idx

                # Search siblings/children (base, handle)
                for k, v in data.items():
                    if k not in self.primitive_keys:
                        collect_shapes(v, current_tracker_idx)

            elif isinstance(data, list):
                for item in data:
                    collect_shapes(item, parent_idx)

        collect_shapes(indexed_json)

        if not parts_paths:
            print("No parts found in JSON to assemble.")
            return

        def get_4x4(params):
            import numpy as np
            from scipy.spatial.transform import Rotation as R
            T = np.eye(4)
            pos = [params.get('pos_x', 0.0), params.get('pos_y', 0.0), params.get('pos_z', 0.0)]
            euler = [params.get('roll', 0.0), params.get('pitch', 0.0), params.get('yaw', 0.0)]
            T[:3, :3] = R.from_euler('xyz', euler).as_matrix()
            T[:3, 3] = pos
            return T.tolist()

        # Step 2: Create joints using the parent_map
        joints_data = []
        for child_idx, parent_idx in parent_map.items():
            data = collected_dicts[child_idx]
            found_shape_key = next((k for k in self.primitive_keys if k in data), None)
            shape_data = data[found_shape_key] if found_shape_key else {}

            T_rel = get_4x4(shape_data.get("transform", {}))
            T_joint = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

            j_type = "fixed"
            j_limits = j_break_force = j_break_torque = j_max_force = None

            if "joint" in data:
                j_info = data["joint"]
                offset = j_info.get("alignment", {}).get("offset_transform", {})
                T_joint = get_4x4(offset)
                kin = j_info.get("kinematic", {})
                dyn = j_info.get("dynamic", {})
                j_type = kin.get("type", j_type)
                j_limits = kin.get("limits")
                j_break_force = dyn.get("break_force")
                j_break_torque = dyn.get("break_torque")
                j_max_force = dyn.get("max_force")
            else:
                j_type = "fixed"

            joints_data.append({
                "parent_idx": parent_idx,
                "child_idx": child_idx,
                "rel_transform": T_rel,
                "joint_transform": T_joint,
                "type": j_type,
                "limits": j_limits,
                "break_force": j_break_force,
                "break_torque": j_break_torque,
                "max_force": j_max_force
            })

        print(f"Assembling {len(parts_paths)} primitives with {len(joints_data)} joints...")
        assembly_gen.build_assembly(parts_paths, joints_data)
        print(f"Assembly complete: {assembly_gen.usd_path}")

        # Reading generated usda
        file_path = assembly_gen.usd_path
        content=""
        try:
            with open(file_path, "r") as file:
                content = file.read()
                print(content)
        except FileNotFoundError:
            print(f"Could not find the file at {file_path}")

        return assembly_gen.usd_path, content

    def compile_object_from_json_v2(self, params):
        """
           symbol = SceneObject.generate()
           if symbol:
               print(f"\nGenerated: {type(symbol).__name__}")
               json_input = json.dumps(symbol.compile())
           else:
               json_input = "{}"
           """
        choices = [SimpleMugAssembler,SimplePrimitiveAssembler,SimpleDrawerAssembler,SimpleSpoonAssembler,SimpleShelfAssembler,SimpleTableAssembler, SimpleBowlAssembler, SimplePlateAssembler]
        #Assembler=random.choice(choices)
        # choices = [SimpleChairAssembler,SimpleBottleAssembler,SimpleMugAssembler,SimplePrimitiveAssembler,SimpleDrawerAssembler,SimpleSpoonAssembler,SimpleShelfAssembler,SimpleTableAssembler, SimpleBowlAssembler, SimplePlateAssembler]
        Assembler=choices[self.index % len(choices)]
        symbol = Assembler()
        self.index=self.index+1
        if symbol:
            print(f"\nGenerated: {type(symbol).__name__}")
            json_input = json.dumps(symbol.generate({}))
        else:
            json_input = "{}"

        data = json.loads(json_input)
        instances, indexed_json = self.compile(data)
        print('Indexed JSON:', json.dumps(indexed_json, indent=1))
        return self.generate_assembly_test(indexed_json), json.dumps(indexed_json, indent=1)

if __name__ == "__main__":
    compiler = ObjectCompiler()
    compiler.compile_object_from_json_v2(None)