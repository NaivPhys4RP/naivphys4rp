import subprocess
import os
import math
import datetime

# Update this to your absolute Blender path
BLENDER_PATH = "/home/franklin/Downloads/blender-5.0.1-linux-x64/blender"


class MultiModelGenerator:
    def __init__(self, output_base_name="complex_assembly"):
        self.base_name = output_base_name
        self.usd_path = os.path.abspath(f"{output_base_name}.usda")

    def _extract_physics_from_mtl(self, obj_path):
        """Parses the companion .mtl file for StructuralMetadata."""
        mtl_path = obj_path.replace(".obj", ".mtl")
        phys_data = {}

        if not os.path.exists(mtl_path):
            return phys_data

        with open(mtl_path, "r") as f:
            lines = f.readlines()
            is_metadata_block = False
            for line in lines:
                line = line.strip()
                # RESTORED: Core logic filter for StructuralMetadata block
                if line.startswith("newmtl StructuralMetadata"):
                    is_metadata_block = True
                    continue
                if is_metadata_block and line.startswith("newmtl") and "StructuralMetadata" not in line:
                    break

                if is_metadata_block and line.startswith("X_"):
                    parts = line.split()
                    if len(parts) < 2: continue
                    key, value = parts[0], parts[1]

                    # Only convert to float if it's one of the expected numerical keys
                    try:
                        if key == "X_density":
                            phys_data["mass"] = float(value)
                        elif key == "X_friction":
                            phys_data["static_friction"] = float(value)
                        elif key == "X_restitution":
                            phys_data["restitution"] = float(value)
                    except ValueError:
                        # Skip non-numeric values like 'STEEL' gracefully
                        continue

        return phys_data

    def _convert_to_usdc(self, obj_path):
        """Converts OBJ to USDC via Blender."""
        if not os.path.exists(obj_path):
            print(f"Error: {obj_path} not found.")
            return None

        abs_obj = os.path.abspath(obj_path)
        usd_path = abs_obj.replace(".obj", ".usdc")

        if os.path.exists(usd_path):
            return usd_path

        python_cmd = (
            f"import bpy; "
            f"bpy.ops.wm.read_factory_settings(use_empty=True); "
            f"bpy.ops.wm.obj_import(filepath='{abs_obj}'); "
            f"bpy.ops.wm.usd_export(filepath='{usd_path}', export_materials=True)"
        )

        clean_env = os.environ.copy()
        for key in ["LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME"]:
            if key in clean_env:
                del clean_env[key]

        print(f"--- [BLENDER] Converting: {os.path.basename(obj_path)} ---")
        try:
            subprocess.run(
                [BLENDER_PATH, "-b", "--python-expr", python_cmd],
                env=clean_env, capture_output=True, check=True
            )
            return usd_path
        except subprocess.CalledProcessError as e:
            print(f"Blender conversion failed: {e.stderr.decode()}")
            return None

    def _decompose_matrix(self, T):
        """Extracts translation, scale, and wxyz quaternion."""
        pos = (float(T[0][3]), float(T[1][3]), float(T[2][3]))
        sx = math.sqrt(T[0][0] ** 2 + T[1][0] ** 2 + T[2][0] ** 2)
        sy = math.sqrt(T[0][1] ** 2 + T[1][1] ** 2 + T[2][1] ** 2)
        sz = math.sqrt(T[0][2] ** 2 + T[1][2] ** 2 + T[2][2] ** 2)
        scale = (float(sx), float(sy), float(sz))

        r11, r12, r13 = T[0][0] / sx, T[0][1] / sy, T[0][2] / sz
        r21, r22, r23 = T[1][0] / sx, T[1][1] / sy, T[1][2] / sz
        r31, r32, r33 = T[2][0] / sx, T[2][1] / sy, T[2][2] / sz

        tr = r11 + r22 + r33
        if tr > 0:
            s = math.sqrt(tr + 1.0) * 2
            qw, qx, qy, qz = 0.25 * s, (r32 - r23) / s, (r13 - r31) / s, (r21 - r12) / s
        elif (r11 > r22) and (r11 > r33):
            s = math.sqrt(1.0 + r11 - r22 - r33) * 2
            qw, qx, qy, qz = (r32 - r23) / s, 0.25 * s, (r12 + r21) / s, (r13 + r31) / s
        elif r22 > r33:
            s = math.sqrt(1.0 + r22 - r11 - r33) * 2
            qw, qx, qy, qz = (r13 - r31) / s, (r12 + r21) / s, 0.25 * s, (r23 + r32) / s
        else:
            s = math.sqrt(1.0 + r33 - r11 - r22) * 2
            qw, qx, qy, qz = (r21 - r12) / s, (r13 + r31) / s, (r23 + r32) / s, 0.25 * s

        return pos, (float(qw), float(qx), float(qy), float(qz)), scale

    def build_assembly(self, obj_paths, joints):
        usdc_basenames = []
        phys_metadata = []

        for path in obj_paths:
            converted = self._convert_to_usdc(path)
            usdc_basenames.append(os.path.basename(converted) if converted else None)
            phys_metadata.append(self._extract_physics_from_mtl(path))

        child_to_jnt = {jnt["child_idx"]: jnt for jnt in joints}

        content = """#usda 1.0
    (
        defaultPrim = "Root"
        metersPerUnit = 1
        upAxis = "Z"
    )

    def Xform "Root"
    {"""

        for i, name in enumerate(usdc_basenames):
            if not name: continue
            link_id = f"Link_{i}_{name.split('.')[0]}"
            phys = phys_metadata[i]

            phys_lines = ["float physics:density = 1.0"]

            if "mass" in phys:
                phys_lines.append(f"float physics:mass = {phys['mass']}")
            if "static_friction" in phys:
                phys_lines.append(f"float physics:staticFriction = {phys['static_friction']}")
            if "restitution" in phys:
                phys_lines.append(f"float physics:restitution = {phys['restitution']}")

            if "hollow" in name.lower():
                phys_lines.append('uniform token physics:approximation = "convexDecomposition"')
            else:
                phys_lines.append('uniform token physics:approximation = "convexHull"')

            phys_lines.append('bool physics:collisionEnabled = true')
            phys_str = "\n        ".join(phys_lines)

            if i == 0:
                transform_props = """
            double3 xformOp:translate = (0.0, 0.0, 0.0)
            quatd xformOp:orient = (1.0, 0.0, 0.0, 0.0)
            double3 xformOp:scale = (1.0, 1.0, 1.0)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]"""

            elif i in child_to_jnt:
                jnt = child_to_jnt[i]
                pos_rel, quat_rel, scale_rel = self._decompose_matrix(jnt["rel_transform"])
                transform_props = f"""
            double3 xformOp:translate = {pos_rel}
            quatd xformOp:orient = {quat_rel}
            double3 xformOp:scale = {scale_rel}
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]"""
            else:
                transform_props = ""

            content += f"""
        def Xform "{link_id}" (
            prepend references = @./{name}@
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsMassAPI", "PhysicsCollisionAPI"]
        )
        {{{transform_props}
            {phys_str}
        }}"""

        # Updated joint map to include prismatic
        joint_map = {
            "fixed": "PhysicsFixedJoint",
            "revolute": "PhysicsRevoluteJoint",
            "prismatic": "PhysicsPrismaticJoint"
        }

        for i, jnt in enumerate(joints):
            p_idx, c_idx = jnt["parent_idx"], jnt["child_idx"]
            p_name = usdc_basenames[p_idx].split('.')[0]
            c_name = usdc_basenames[c_idx].split('.')[0]
            p_path = f"/Root/Link_{p_idx}_{p_name}"
            c_path = f"/Root/Link_{c_idx}_{c_name}"

            pos_p, quat_p, _ = self._decompose_matrix(jnt["rel_transform"])
            j_type = jnt.get("type", "fixed").lower()
            selected_schema = joint_map.get(j_type, "PhysicsFixedJoint")

            joint_props = []

            # Handle limits for both Revolute (degrees) and Prismatic (meters)
            if jnt.get("limits") is not None:
                l_val = jnt["limits"].get("lower", -3.14)
                u_val = jnt["limits"].get("upper", 3.14)

                if j_type == "revolute":
                    joint_props.append(f"float physics:lowerLimit = {math.degrees(l_val)}")
                    joint_props.append(f"float physics:upperLimit = {math.degrees(u_val)}")
                elif j_type == "prismatic":
                    joint_props.append(f"float physics:lowerLimit = {l_val}")
                    joint_props.append(f"float physics:upperLimit = {u_val}")

            # Explicit 'is not None' checks for physics efforts
            if jnt.get("break_force") is not None:
                joint_props.append(f"float physics:breakForce = {jnt['break_force']}")
            if jnt.get("break_torque") is not None:
                joint_props.append(f"float physics:breakTorque = {jnt['break_torque']}")
            if jnt.get("max_force") is not None:
                joint_props.append(f"float physics:jointMaxForce = {jnt['max_force']}")

            props_str = "\n        ".join(joint_props)

            content += f"""
        def {selected_schema} "Joint_{i}"
        {{
            rel physics:body0 = <{p_path}>
            rel physics:body1 = <{c_path}>
            point3f physics:localPos0 = {pos_p}
            quatf physics:localRot0 = {quat_p}
            point3f physics:localPos1 = (0, 0, 0)
            quatf physics:localRot1 = (1, 0, 0, 0)
            uniform token physics:axis = "Z"
            {props_str}
        }}"""

        content += "\n}"

        with open(self.usd_path, "w") as f:
            f.write(content)
        print(f"--- [SUCCESS] ---\nUSD: {self.usd_path}")