import os
import mujoco
import mujoco.viewer
from pxr import Usd, UsdGeom, Gf


def convert_usd_to_mjcf(usd_in, xml_out):
    if not os.path.exists(usd_in):
        print(f"Error: {usd_in} not found.")
        return False

    stage = Usd.Stage.Open(usd_in)

    # MJCF Header
    mjcf = [
        '<mujoco model="converted_assembly">',
        '    <compiler angle="degree" coordinate="local" inertiafromgeom="true"/>',
        '    <option integrator="RK4" timestep="0.01" gravity="0 0 -9.81"/>',
        '    <worldbody>',
        '        <light pos="0 0 3" dir="0 0 -1" diffuse="1 1 1"/>',
        '        <geom name="floor" type="plane" size="10 10 0.1" rgba=".9 .9 .9 1"/>'
    ]

    print(f"Traversing USD: {usd_in}")

    for prim in stage.Traverse():
        # Only process actual geometry prims (Meshes, Cubes, etc.)
        if prim.IsA(UsdGeom.Boundable):
            # 1. Clean the name (MuJoCo forbids @ and .)
            clean_name = prim.GetName().replace("@", "_").replace(".", "_")

            # 2. Extract World Transform
            xformable = UsdGeom.Xformable(prim)
            time = Usd.TimeCode.Default()
            world_transform = xformable.ComputeLocalToWorldTransform(time)

            translation = world_transform.ExtractTranslation()

            # 3. Handle Scaling (Crucial: Convert mm to meters if necessary)
            # Most USDs from Isaac/CAD are in cm or mm.
            # If your assembly is tiny, change 0.001 to 1.0 or 0.01
            scale_factor = 0.001
            pos = [t * scale_factor for t in translation]

            # 4. Create the MuJoCo body and geom
            # We use a box placeholder. To use real meshes, you'd add:
            # <geom type="mesh" mesh="mesh_name"/>
            mjcf.append(f'        <body name="{clean_name}" pos="{pos[0]} {pos[1]} {pos[2]}">')
            mjcf.append('            <freejoint/>')
            mjcf.append('            <geom type="box" size="0.02 0.02 0.02" rgba="0 0.5 1 1"/>')
            mjcf.append('        </body>')
            print(f"  Added: {clean_name} at {pos}")

    mjcf.append('    </worldbody>')
    mjcf.append('</mujoco>')

    # Write to file
    with open(xml_out, "w") as f:
        f.write("\n".join(mjcf))

    return True


# --- EXECUTION ---
usd_input = "/home/franklin/Desktop/ws/src/naivphys4rp/inverse_simulation/scripts/contextualization/question_answering/assembly.usda"
xml_output = "/home/franklin/Desktop/ws/src/naivphys4rp/inverse_simulation/scripts/contextualization/question_answering/assembly.xml"

if convert_usd_to_mjcf(usd_input, xml_output):
    print(f"\nSuccessfully converted to {xml_output}")

    # Load into MuJoCo viewer immediately
    model = mujoco.MjModel.from_xml_path(xml_output)
    data = mujoco.MjData(model)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()