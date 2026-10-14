import subprocess
import os
import numpy as np
from scipy.spatial.transform import Rotation as R

# Update this to your absolute Blender path
BLENDER_PATH = "/home/franklin/Downloads/blender-5.0.1-linux-x64/blender"


class DualModelGenerator:
    def __init__(self, output_base_name="robot_assembly"):
        self.base_name = output_base_name
        self.usd_path = os.path.abspath(f"{output_base_name}.usda")
        self.xml_path = os.path.abspath(f"{output_base_name}.xml")

        # Decomposed transform data
        self.pos = [0, 0, 0]
        self.quat = [1, 0, 0, 0]  # w, x, y, z
        self.scale = [1, 1, 1]
        self.joint_type = "fixed"
        self.parent_obj_name = ""
        self.child_obj_name = ""

    def _convert_to_usdc(self, obj_path):
        """
        Converts OBJ to USDC using a clean environment to avoid
        MaterialX/USD library symbol conflicts.
        """
        if not os.path.exists(obj_path):
            print(f"Error: {obj_path} not found.")
            return None

        abs_obj = os.path.abspath(obj_path)
        usd_path = abs_obj.replace(".obj", ".usdc")

        # If it exists, we skip to save time, but you can remove this check to force re-conversion
        if os.path.exists(usd_path):
            return usd_path

        python_cmd = (
            f"import bpy; "
            f"bpy.ops.wm.read_factory_settings(use_empty=True); "
            f"bpy.ops.wm.obj_import(filepath='{abs_obj}'); "
            f"bpy.ops.wm.usd_export(filepath='{usd_path}', export_materials=True)"
        )

        # --- ENVIRONMENT ISOLATION ---
        # Strip system/conda paths so Blender uses its internal libraries
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
        self.pos = T[:3, 3]
        self.scale = [np.linalg.norm(T[:3, i]) for i in range(3)]
        # Normalize rotation matrix by scale
        rot_mat = T[:3, :3] / np.array(self.scale)
        r = R.from_matrix(rot_mat)
        q = r.as_quat()  # x, y, z, w
        self.quat = (q[3], q[0], q[1], q[2])  # w, x, y, z (USD/MuJoCo standard)

    def generate_usd(self, rel_p, rel_c):
        """Writes ASCII USDA with multi-line header to avoid parsing errors."""
        joint_map = {
            "fixed": "PhysicsFixedJoint",
            "revolute": "PhysicsRevoluteJoint",
            "prismatic": "PhysicsPrismaticJoint",
            "continuous": "PhysicsRevoluteJoint"
        }
        selected_joint = joint_map.get(self.joint_type, "PhysicsFixedJoint")

        # Revolute joints often require limit attributes
        joint_extra = ""
        if self.joint_type == "revolute":
            joint_extra = """
        float physics:lowerLimit = -180
        float physics:upperLimit = 180"""

        content = f"""#usda 1.0
(
    defaultPrim = "Root"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "Root"
{{
    def Xform "Link_Parent" (
        prepend references = @./{rel_p}@
    )
    {{
    }}

    def Xform "Link_Child" (
        prepend references = @./{rel_c}@
    )
    {{
        double3 xformOp:translate = {tuple(self.pos)}
        quatd xformOp:orient = {tuple(self.quat)}
        double3 xformOp:scale = {tuple(self.scale)}
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
    }}

    def {selected_joint} "Joint_Constraint"
    {{
        rel physics:body0 = </Root/Link_Parent>
        rel physics:body1 = </Root/Link_Child>
        point3f physics:localPos0 = {tuple(self.pos)}
        quatf physics:localRot0 = {tuple(self.quat)}
        point3f physics:localPos1 = (0, 0, 0)
        quatf physics:localRot1 = (1, 0, 0, 0)
        uniform token physics:axis = "Z"{joint_extra}
    }}
}}
"""
        with open(self.usd_path, "w") as f:
            f.write(content)



    def build(self, parent_obj, child_obj, transform_matrix, joint_type="fixed"):
        """Main execution flow for dual model generation."""
        self.joint_type = joint_type.lower()
        self._decompose_matrix(transform_matrix)

        # 1. Convert assets via Blender
        p_usdc = self._convert_to_usdc(parent_obj)
        c_usdc = self._convert_to_usdc(child_obj)

        if p_usdc and c_usdc:
            # 2. Generate USDA (Visualization)
            self.generate_usd(os.path.basename(p_usdc), os.path.basename(c_usdc))
            print(f"--- [SUCCESS] ---")
            print(f"USD: {self.usd_path}\n")


if __name__ == "__main__":
    generator = DualModelGenerator("robot_assembly")

    # Example Transform: 45 deg rotation, 1.5x scale, 0.2m up
    rot = R.from_euler('z', 45, degrees=True).as_matrix()
    T = np.eye(4)
    T[:3, :3] = rot * 1.5
    T[2, 3] = 0.2

    # Run the generator
    generator.build(
        parent_obj="cartoon_gradient_ring_test.obj",
        child_obj="cartoon_gradient_cone_test.obj",
        transform_matrix=T,
        joint_type="revolute"
    )