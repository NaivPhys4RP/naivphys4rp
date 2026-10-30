
# #!/usr/bin/env python3
# """Place the cube at an IK-unreachable location on the tabletop.

# The robot stays at the exact initial POSE throughout the experiment.
# Only the cube's free-joint position is changed.
# """

# from pathlib import Path
# import json
# import time
# from datetime import datetime

# import numpy as np
# import mujoco
# import mujoco.viewer


# ROOT = Path(__file__).resolve().parents[3]
# MODEL = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

# ARM = [
#     "left_shoulder_pan_joint",
#     "left_shoulder_lift_joint",
#     "left_elbow_joint",
#     "left_wrist_1_joint",
#     "left_wrist_2_joint",
#     "left_wrist_3_joint",
# ]

# # DO NOT CHANGE THESE VALUES.
# POSE = {
#     "left_shoulder_pan_joint": 2.140,
#     "left_shoulder_lift_joint": -1.317,
#     "left_elbow_joint": 1.375,
#     "left_wrist_1_joint": 5.603,
#     "left_wrist_2_joint": 5.264,
#     "left_wrist_3_joint": -1.053,
#     "right_shoulder_pan_joint": 4.109,
#     "right_shoulder_lift_joint": -1.867,
#     "right_elbow_joint": -1.341,
#     "right_wrist_1_joint": 3.973,
#     "right_wrist_2_joint": 0.849,
#     "right_wrist_3_joint": 1.257,
# }

# TOOL_NAME = "l_gripper_tool_frame"
# CUBE_NAME = "phase1_cube"

# # Set this to the exact tabletop geom name if automatic detection fails.
# TABLE_GEOM_NAME = None

# APPROACH_HEIGHT = 0.15
# DAMPING = 0.03
# MAX_IK_STEPS = 300
# POSITION_TOL = 0.008
# ROTATION_TOL = 0.04
# ROTATION_WEIGHT = 0.25

# # Keep candidate cube centers safely inside the tabletop edges.
# EDGE_MARGIN = 0.035
# GRID_POINTS_X = 9
# GRID_POINTS_Y = 9

# LOG_FILE = Path("f1_unreachable_cube_failure.json")


# def rotation_error(target, current):
#     """World-frame axis-angle orientation error."""
#     R = target @ current.T
#     c = np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0)
#     angle = np.arccos(c)

#     if angle < 1e-8:
#         return np.zeros(3)

#     if np.pi - angle < 1e-5:
#         vals, vecs = np.linalg.eig(R)
#         axis = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
#         axis /= max(np.linalg.norm(axis), 1e-12)
#         return angle * axis

#     return angle / (2.0 * np.sin(angle)) * np.array([
#         R[2, 1] - R[1, 2],
#         R[0, 2] - R[2, 0],
#         R[1, 0] - R[0, 1],
#     ])


# def align_vector_rotation(source, target):
#     """Find the smallest rotation mapping source onto target."""
#     a = source / np.linalg.norm(source)
#     b = target / np.linalg.norm(target)
#     v = np.cross(a, b)
#     c = np.clip(np.dot(a, b), -1.0, 1.0)
#     s = np.linalg.norm(v)

#     if s < 1e-9:
#         if c > 0:
#             return np.eye(3)

#         helper = np.array([1.0, 0.0, 0.0])
#         if abs(a[0]) > 0.9:
#             helper = np.array([0.0, 1.0, 0.0])

#         axis = np.cross(a, helper)
#         axis /= np.linalg.norm(axis)
#         return 2.0 * np.outer(axis, axis) - np.eye(3)

#     K = np.array([
#         [0.0, -v[2], v[1]],
#         [v[2], 0.0, -v[0]],
#         [-v[1], v[0], 0.0],
#     ])

#     return np.eye(3) + K + K @ K * ((1.0 - c) / (s * s))


# def get_id(model, object_type, name):
#     idx = mujoco.mj_name2id(model, object_type, name)
#     if idx < 0:
#         raise RuntimeError(f"Could not find model object: {name}")
#     return idx


# def find_table_geom(model):
#     """Find the largest box geom whose name contains 'table'."""
#     if TABLE_GEOM_NAME:
#         gid = get_id(
#             model, mujoco.mjtObj.mjOBJ_GEOM, TABLE_GEOM_NAME
#         )
#         if model.geom_type[gid] != mujoco.mjtGeom.mjGEOM_BOX:
#             raise RuntimeError(
#                 f"Configured table geom {TABLE_GEOM_NAME!r} is not a box."
#             )
#         return gid

#     matches = []
#     for gid in range(model.ngeom):
#         if model.geom_type[gid] != mujoco.mjtGeom.mjGEOM_BOX:
#             continue

#         name = mujoco.mj_id2name(
#             model, mujoco.mjtObj.mjOBJ_GEOM, gid
#         ) or ""

#         if "table" in name.lower():
#             size = model.geom_size[gid]
#             matches.append((size[0] * size[1], gid, name))

#     if not matches:
#         raise RuntimeError(
#             "Could not identify a box tabletop geom. Set TABLE_GEOM_NAME "
#             "to the exact tabletop geom name in the MJCF model."
#         )

#     matches.sort(reverse=True)
#     _, gid, name = matches[0]
#     print(f"Using tabletop geom: {name!r}")
#     return gid


# def find_cube_box_geom(model, cube_body_id):
#     """Find the largest box geom belonging to the cube body."""
#     matches = []

#     for gid in range(model.ngeom):
#         if model.geom_bodyid[gid] != cube_body_id:
#             continue
#         if model.geom_type[gid] != mujoco.mjtGeom.mjGEOM_BOX:
#             continue

#         size = model.geom_size[gid]
#         matches.append((size[0] * size[1] * size[2], gid))

#     if not matches:
#         raise RuntimeError(
#             "No box geom was found on the cube body. Adapt "
#             "find_cube_box_geom() for the cube's actual geom type."
#         )

#     matches.sort(reverse=True)
#     return matches[0][1]


# def find_free_joint(model, body_id):
#     for jid in range(model.njnt):
#         if (
#             model.jnt_bodyid[jid] == body_id
#             and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE
#         ):
#             return jid

#     raise RuntimeError("The cube body has no free joint.")


# def set_cube_geom_center(
#     model, data, cube_qadr, cube_geom_id, desired_geom_center,
#     cube_quaternion
# ):
#     """Position the cube so its geom center reaches the desired point."""
#     body_id = model.geom_bodyid[cube_geom_id]

#     rotation = np.zeros(9)
#     mujoco.mju_quat2Mat(rotation, cube_quaternion)
#     rotation = rotation.reshape(3, 3)

#     local_geom_offset = model.geom_pos[cube_geom_id]
#     body_position = desired_geom_center - rotation @ local_geom_offset

#     data.qpos[cube_qadr:cube_qadr + 3] = body_position
#     data.qpos[cube_qadr + 3:cube_qadr + 7] = cube_quaternion


# def make_top_down_rotation(model, probe, tool_id):
#     """Derive a fixed top-down tool orientation from the initial pose."""
#     mujoco.mj_forward(model, probe)

#     initial_rotation = probe.xmat[tool_id].reshape(3, 3).copy()
#     initial_axis = initial_rotation @ np.array([0.0, 0.0, 1.0])

#     return (
#         align_vector_rotation(
#             initial_axis, np.array([0.0, 0.0, -1.0])
#         ) @ initial_rotation
#     )


# def solve_ik(
#     model, probe, tool_id, qadr, dadr, joint_ids,
#     target_position, target_rotation, jac_pos, jac_rot
# ):
#     """Test IK on probe data only. This never moves the displayed robot."""
#     for _ in range(MAX_IK_STEPS):
#         mujoco.mj_forward(model, probe)

#         pos_error = target_position - probe.xpos[tool_id]
#         current_rotation = probe.xmat[tool_id].reshape(3, 3)
#         rot_error = rotation_error(target_rotation, current_rotation)

#         if (
#             np.linalg.norm(pos_error) < POSITION_TOL
#             and np.linalg.norm(rot_error) < ROTATION_TOL
#         ):
#             return True, float(np.linalg.norm(pos_error)), float(
#                 np.linalg.norm(rot_error)
#             )

#         mujoco.mj_jacBody(
#             model, probe, jac_pos, jac_rot, tool_id
#         )

#         Jp = jac_pos[:, dadr]
#         Jr = jac_rot[:, dadr]
#         J = np.vstack((Jp, ROTATION_WEIGHT * Jr))
#         error = np.concatenate((
#             pos_error,
#             ROTATION_WEIGHT * rot_error,
#         ))

#         matrix = J @ J.T + DAMPING**2 * np.eye(6)
#         dq = J.T @ np.linalg.solve(matrix, error)
#         probe.qpos[qadr] += np.clip(dq, -0.035, 0.035)

#         for k, jid in enumerate(joint_ids):
#             if model.jnt_limited[jid]:
#                 lo, hi = model.jnt_range[jid]
#                 probe.qpos[qadr[k]] = np.clip(
#                     probe.qpos[qadr[k]], lo, hi
#                 )

#     mujoco.mj_forward(model, probe)
#     pos_residual = float(
#         np.linalg.norm(target_position - probe.xpos[tool_id])
#     )
#     rot_residual = float(np.linalg.norm(
#         rotation_error(
#             target_rotation, probe.xmat[tool_id].reshape(3, 3)
#         )
#     ))

#     # Strict reachability test: do not accept a loose residual.
#     reached = (
#         pos_residual < POSITION_TOL
#         and rot_residual < ROTATION_TOL
#     )
#     return reached, pos_residual, rot_residual


# def generate_back_table_candidates(
#     model, data, table_gid, cube_geom_id, tool_id
# ):
#     """Generate candidate cube centers near the far/back table edge."""
#     table_center = data.geom_xpos[table_gid].copy()
#     table_rotation = data.geom_xmat[table_gid].reshape(3, 3).copy()
#     table_half = model.geom_size[table_gid].copy()

#     cube_half = model.geom_size[cube_geom_id].copy()

#     # Work out which table-local Y direction points away from the robot.
#     tool_local = table_rotation.T @ (
#         data.xpos[tool_id] - table_center
#     )
#     back_sign = -1.0 if tool_local[1] >= 0.0 else 1.0

#     # Keep the complete cube inside the tabletop's X/Y bounds.
#     x_margin = cube_half[0] + EDGE_MARGIN
#     y_margin = cube_half[1] + EDGE_MARGIN

#     x_min = -table_half[0] + x_margin
#     x_max = table_half[0] - x_margin
#     y_near = table_half[1] - y_margin

#     if x_min >= x_max or y_near <= 0:
#         raise RuntimeError(
#             "The tabletop geom is too small for the cube and edge margin."
#         )

#     x_values = np.linspace(x_min, x_max, GRID_POINTS_X)
#     y_fractions = np.linspace(1.0, 0.35, GRID_POINTS_Y)

#     candidates = []
#     for fraction in y_fractions:
#         local_y = back_sign * y_near * fraction

#         for local_x in x_values:
#             # Top surface in table-local coordinates plus half the cube height.
#             local_center = np.array([
#                 local_x,
#                 local_y,
#                 table_half[2] + cube_half[2],
#             ])

#             world_center = table_center + table_rotation @ local_center
#             candidates.append({
#                 "local_xy": [float(local_x), float(local_y)],
#                 "world_center": world_center,
#                 "backness": abs(float(local_y)),
#             })

#     # Prefer positions closest to the far/back edge.
#     candidates.sort(key=lambda c: c["backness"], reverse=True)
#     return candidates


# def main():
#     if not MODEL.exists():
#         raise FileNotFoundError(f"MuJoCo model not found: {MODEL}")

#     model = mujoco.MjModel.from_xml_path(str(MODEL))
#     data = mujoco.MjData(model)

#     def joint_id(name):
#         return get_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)

#     # Initialize all joints to the exact specified pose.
#     for name, value in POSE.items():
#         jid = joint_id(name)
#         data.qpos[model.jnt_qposadr[jid]] = value

#     left_joint_ids = [joint_id(name) for name in ARM]
#     qadr = np.array([
#         model.jnt_qposadr[jid] for jid in left_joint_ids
#     ])
#     dadr = np.array([
#         model.jnt_dofadr[jid] for jid in left_joint_ids
#     ])

#     mujoco.mj_forward(model, data)

#     tool_id = get_id(model, mujoco.mjtObj.mjOBJ_BODY, TOOL_NAME)
#     cube_id = get_id(model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME)

#     cube_free_joint = find_free_joint(model, cube_id)
#     cube_qadr = model.jnt_qposadr[cube_free_joint]

#     table_gid = find_table_geom(model)
#     cube_geom_id = find_cube_box_geom(model, cube_id)

#     # Save the complete initial robot configuration. Never change it in data.
#     fixed_qpos = data.qpos.copy()
#     fixed_qvel = data.qvel.copy()

#     cube_start_position = data.qpos[cube_qadr:cube_qadr + 3].copy()
#     cube_start_quaternion = data.qpos[
#         cube_qadr + 3:cube_qadr + 7
#     ].copy()

#     top_down_rotation = make_top_down_rotation(
#         model, data, tool_id
#     )

#     # A separate MuJoCo data object is used for every IK test.
#     probe = mujoco.MjData(model)
#     jac_pos = np.zeros((3, model.nv))
#     jac_rot = np.zeros((3, model.nv))

#     candidates = generate_back_table_candidates(
#         model, data, table_gid, cube_geom_id, tool_id
#     )

#     selected = None
#     fallback = None

#     print("\nSearching for a cube position on the back of the tabletop...")
#     print("The visible robot will remain at the specified POSE.")

#     for index, candidate in enumerate(candidates, start=1):
#         # Start each test from the same robot pose.
#         probe.qpos[:] = fixed_qpos
#         probe.qvel[:] = fixed_qvel

#         cube_center = candidate["world_center"]
#         set_cube_geom_center(
#             model, probe, cube_qadr, cube_geom_id,
#             cube_center, cube_start_quaternion
#         )
#         mujoco.mj_forward(model, probe)

#         # The cube center is the pick target for this reachability test.
#         pick_target = cube_center.copy()
#         approach_target = pick_target + np.array([
#             0.0, 0.0, APPROACH_HEIGHT
#         ])

#         # Each target starts from the original arm configuration.
#         probe.qpos[:] = fixed_qpos
#         probe.qvel[:] = fixed_qvel
#         approach_ok, approach_pos_error, approach_rot_error = solve_ik(
#             model, probe, tool_id, qadr, dadr, left_joint_ids,
#             approach_target, top_down_rotation, jac_pos, jac_rot
#         )

#         probe.qpos[:] = fixed_qpos
#         probe.qvel[:] = fixed_qvel
#         pick_ok, pick_pos_error, pick_rot_error = solve_ik(
#             model, probe, tool_id, qadr, dadr, left_joint_ids,
#             pick_target, top_down_rotation, jac_pos, jac_rot
#         )

#         result = {
#             "candidate_index": index,
#             "local_xy": candidate["local_xy"],
#             "cube_center_world": cube_center.tolist(),
#             "approach_reachable_by_ik": bool(approach_ok),
#             "pick_reachable_by_ik": bool(pick_ok),
#             "approach_position_residual_m": approach_pos_error,
#             "approach_orientation_residual_rad": approach_rot_error,
#             "pick_position_residual_m": pick_pos_error,
#             "pick_orientation_residual_rad": pick_rot_error,
#         }

#         print(
#             f"Candidate {index:02d}: "
#             f"cube={np.round(cube_center, 3)}, "
#             f"approach_reachable={approach_ok}, "
#             f"pick_reachable={pick_ok}"
#         )

#         # Preferred: both approach and pick targets fail the IK test.
#         if not approach_ok and not pick_ok:
#             selected = result
#             break

#         # Keep a fallback if the search cannot find a position where both fail.
#         if fallback is None and (not approach_ok or not pick_ok):
#             fallback = result

#     if selected is None:
#         selected = fallback

#     if selected is None:
#         raise RuntimeError(
#             "No candidate failed the IK test. The script will not claim "
#             "the cube is unreachable. Expand the search area or check "
#             "the robot model, joint limits, and tabletop geom."
#         )

#     target_center = np.array(selected["cube_center_world"])

#     # Change only the cube free-joint position in the visible simulation.
#     data.qpos[:] = fixed_qpos
#     data.qvel[:] = fixed_qvel
#     set_cube_geom_center(
#         model, data, cube_qadr, cube_geom_id,
#         target_center, cube_start_quaternion
#     )
#     mujoco.mj_forward(model, data)

#     # Record the failure and the recovery suggestion.
#     failure_record = {
#         "timestamp": datetime.now().isoformat(timespec="seconds"),
#         "failure_id": "F1",
#         "failure_type": "cube_outside_arm_ik_reachability",
#         "description": (
#             "Cube placed on the tabletop at a location whose approach "
#             "and/or pick target failed the IK reachability test."
#         ),
#         "robot_moved": False,
#         "pose_fixed": True,
#         "pose": POSE,
#         "cube_initial_position": cube_start_position.tolist(),
#         "cube_selected_center_world": target_center.tolist(),
#         "reachability_test": selected,
#         "recovery_suggestion": {
#             "strategy": "REPLAN_ACTION",
#             "actions": [
#                 "Stop the current pick action",
#                 "Replan the grasp approach or request human intervention",
#             ],
#         },
#     }

#     LOG_FILE.write_text(
#         json.dumps(failure_record, indent=2),
#         encoding="utf-8",
#     )

#     print("\n" + "=" * 64)
#     print("F1 FAILURE: CUBE PLACED AT AN IK-UNREACHABLE TABLETOP LOCATION")
#     print("=" * 64)
#     print(f"Cube center: {np.round(target_center, 4)}")
#     print(
#         "Approach IK reachable:",
#         selected["approach_reachable_by_ik"]
#     )
#     print(
#         "Pick IK reachable:",
#         selected["pick_reachable_by_ik"]
#     )
#     print(f"Failure log saved to: {LOG_FILE.resolve()}")
#     print("Robot motion: NONE")
#     print("Recovery suggestion: REPLAN_ACTION")

#     with mujoco.viewer.launch_passive(model, data) as viewer:
#         viewer.sync()

#         while viewer.is_running():
#             # Guard against any accidental change to robot joint positions.
#             data.qpos[qadr] = fixed_qpos[qadr]
#             mujoco.mj_forward(model, data)
#             viewer.sync()
#             time.sleep(0.03)


# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
"""F1: Hardcode an unreachable cube position and test pick feasibility.

Only the cube is repositioned. The robot stays at the initial POSE.
IK tests run on separate MuJoCo data and never command robot motion.
"""

from pathlib import Path
from datetime import datetime
import json
import time

import numpy as np
import mujoco
import mujoco.viewer


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

TOOL_NAME = "l_gripper_tool_frame"
CUBE_NAME = "phase1_cube"
TABLE_GEOM_NAME = "table_collision_0"

# Hardcoded WORLD coordinates of the cube's geom center, in metres.
CUBE_TARGET = np.array([1.105, -0.725, 0.895], dtype=float)

APPROACH_HEIGHT = 0.15
DAMPING = 0.03
MAX_IK_STEPS = 300
POSITION_TOL = 0.008
ROTATION_TOL = 0.04
ROTATION_WEIGHT = 0.25

LOG_FILE = Path("f1_unreachable_cube_failure.json")

# Do not change any of these values.
POSE = {
    "left_shoulder_pan_joint": 2.140,
    "left_shoulder_lift_joint": -1.317,
    "left_elbow_joint": 1.375,
    "left_wrist_1_joint": 5.603,
    "left_wrist_2_joint": 5.264,
    "left_wrist_3_joint": -1.053,
    "right_shoulder_pan_joint": 4.109,
    "right_shoulder_lift_joint": -1.867,
    "right_elbow_joint": -1.341,
    "right_wrist_1_joint": 3.973,
    "right_wrist_2_joint": 0.849,
    "right_wrist_3_joint": 1.257,
}

ARM = [
    "left_shoulder_pan_joint",
    "left_shoulder_lift_joint",
    "left_elbow_joint",
    "left_wrist_1_joint",
    "left_wrist_2_joint",
    "left_wrist_3_joint",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def get_id(model, object_type, name):
    idx = mujoco.mj_name2id(model, object_type, name)
    if idx < 0:
        raise RuntimeError(f"Model object not found: {name}")
    return idx


def rotation_error(target, current):
    """Return the axis-angle orientation error in world coordinates."""
    R = target @ current.T
    cosine = np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0)
    angle = np.arccos(cosine)

    if angle < 1e-8:
        return np.zeros(3)

    if np.pi - angle < 1e-5:
        values, vectors = np.linalg.eig(R)
        axis = np.real(vectors[:, np.argmin(np.abs(values - 1.0))])
        axis /= max(np.linalg.norm(axis), 1e-12)
        return angle * axis

    return (angle / (2.0 * np.sin(angle))) * np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1],
    ])


def align_vector_rotation(source, target):
    """Smallest rotation mapping source vector to target vector."""
    a = source / np.linalg.norm(source)
    b = target / np.linalg.norm(target)

    v = np.cross(a, b)
    cosine = np.clip(np.dot(a, b), -1.0, 1.0)
    sine = np.linalg.norm(v)

    if sine < 1e-9:
        if cosine > 0:
            return np.eye(3)

        helper = np.array([1.0, 0.0, 0.0])
        if abs(a[0]) > 0.9:
            helper = np.array([0.0, 1.0, 0.0])

        axis = np.cross(a, helper)
        axis /= np.linalg.norm(axis)
        return 2.0 * np.outer(axis, axis) - np.eye(3)

    K = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ])

    return np.eye(3) + K + K @ K * (
        (1.0 - cosine) / (sine * sine)
    )


def find_free_joint(model, body_id):
    for jid in range(model.njnt):
        if (
            model.jnt_bodyid[jid] == body_id
            and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE
        ):
            return jid

    raise RuntimeError("Cube does not have a free joint.")


def find_cube_box_geom(model, body_id):
    """Find the largest box geom attached to the cube body."""
    matches = []

    for gid in range(model.ngeom):
        if model.geom_bodyid[gid] != body_id:
            continue

        if model.geom_type[gid] != mujoco.mjtGeom.mjGEOM_BOX:
            continue

        half_size = model.geom_size[gid]
        volume = float(np.prod(half_size))
        matches.append((volume, gid))

    if not matches:
        raise RuntimeError(
            "No box geom found on the cube. Adapt this function "
            "if the cube uses a different geom type."
        )

    return max(matches)[1]


def place_cube_geom_center(
    model, data, cube_qadr, cube_geom_id, world_center, quaternion
):
    """Put the cube geom center at the specified world coordinates."""
    rotation_flat = np.zeros(9)
    mujoco.mju_quat2Mat(rotation_flat, quaternion)
    body_rotation = rotation_flat.reshape(3, 3)

    # geom_pos is the geom's offset in its body-local frame.
    geom_offset_world = body_rotation @ model.geom_pos[cube_geom_id]
    body_position = world_center - geom_offset_world

    data.qpos[cube_qadr:cube_qadr + 3] = body_position
    data.qpos[cube_qadr + 3:cube_qadr + 7] = quaternion


def make_top_down_rotation(model, data, tool_id):
    """Preserve the tool's initial orientation as much as possible,
    while pointing its local Z axis vertically downward.
    """
    mujoco.mj_forward(model, data)

    initial_rotation = data.xmat[tool_id].reshape(3, 3).copy()
    initial_axis = initial_rotation @ np.array([0.0, 0.0, 1.0])

    return (
        align_vector_rotation(
            initial_axis, np.array([0.0, 0.0, -1.0])
        )
        @ initial_rotation
    )


def solve_ik(
    model,
    probe,
    tool_id,
    qpos_addresses,
    dof_addresses,
    joint_ids,
    target_position,
    target_rotation,
    jac_pos,
    jac_rot,
):
    """Test target reachability without moving the visible robot."""
    for _ in range(MAX_IK_STEPS):
        mujoco.mj_forward(model, probe)

        position_error = target_position - probe.xpos[tool_id]
        current_rotation = probe.xmat[tool_id].reshape(3, 3)
        orientation_error = rotation_error(
            target_rotation, current_rotation
        )

        position_residual = float(np.linalg.norm(position_error))
        rotation_residual = float(np.linalg.norm(orientation_error))

        if (
            position_residual < POSITION_TOL
            and rotation_residual < ROTATION_TOL
        ):
            return {
                "reachable": True,
                "position_residual_m": position_residual,
                "orientation_residual_rad": rotation_residual,
            }

        mujoco.mj_jacBody(
            model, probe, jac_pos, jac_rot, tool_id
        )

        J_position = jac_pos[:, dof_addresses]
        J_rotation = jac_rot[:, dof_addresses]

        J = np.vstack((
            J_position,
            ROTATION_WEIGHT * J_rotation,
        ))

        error = np.concatenate((
            position_error,
            ROTATION_WEIGHT * orientation_error,
        ))

        system = J @ J.T + (DAMPING ** 2) * np.eye(6)
        dq = J.T @ np.linalg.solve(system, error)
        dq = np.clip(dq, -0.035, 0.035)

        probe.qpos[qpos_addresses] += dq

        for index, jid in enumerate(joint_ids):
            if model.jnt_limited[jid]:
                lower, upper = model.jnt_range[jid]
                probe.qpos[qpos_addresses[index]] = np.clip(
                    probe.qpos[qpos_addresses[index]],
                    lower,
                    upper,
                )

    # Final strict tolerance check; no loose residual is accepted.
    mujoco.mj_forward(model, probe)

    position_residual = float(np.linalg.norm(
        target_position - probe.xpos[tool_id]
    ))
    orientation_residual = float(np.linalg.norm(
        rotation_error(
            target_rotation,
            probe.xmat[tool_id].reshape(3, 3),
        )
    ))

    return {
        "reachable": (
            position_residual < POSITION_TOL
            and orientation_residual < ROTATION_TOL
        ),
        "position_residual_m": position_residual,
        "orientation_residual_rad": orientation_residual,
    }


# ---------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------

def main():
    if not MODEL.exists():
        raise FileNotFoundError(f"MuJoCo model not found: {MODEL}")

    model = mujoco.MjModel.from_xml_path(str(MODEL))
    data = mujoco.MjData(model)

    # Initialize every configured robot joint to its fixed value.
    for name, value in POSE.items():
        jid = get_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        data.qpos[model.jnt_qposadr[jid]] = value

    tool_id = get_id(model, mujoco.mjtObj.mjOBJ_BODY, TOOL_NAME)
    cube_id = get_id(model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME)

    cube_free_joint = find_free_joint(model, cube_id)
    cube_qadr = model.jnt_qposadr[cube_free_joint]
    cube_geom_id = find_cube_box_geom(model, cube_id)

    table_gid = get_id(
        model, mujoco.mjtObj.mjOBJ_GEOM, TABLE_GEOM_NAME
    )

    arm_joint_ids = [
        get_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        for name in ARM
    ]

    qpos_addresses = np.array([
        model.jnt_qposadr[jid] for jid in arm_joint_ids
    ])
    dof_addresses = np.array([
        model.jnt_dofadr[jid] for jid in arm_joint_ids
    ])

    mujoco.mj_forward(model, data)

    # Save the robot's initial configuration and the cube orientation.
    fixed_qpos = data.qpos.copy()
    fixed_qvel = data.qvel.copy()
    cube_quaternion = data.qpos[
        cube_qadr + 3:cube_qadr + 7
    ].copy()

    # Hardcode the cube's geom center to the requested world coordinates.
    place_cube_geom_center(
        model,
        data,
        cube_qadr,
        cube_geom_id,
        CUBE_TARGET,
        cube_quaternion,
    )
    mujoco.mj_forward(model, data)

    # Keep the exact cube position and orientation used in the displayed scene.
    actual_cube_center = data.geom_xpos[cube_geom_id].copy()
    cube_rotation = data.geom_xmat[cube_geom_id].reshape(3, 3).copy()

    # Calculate the cube's vertical half-extent, including its orientation.
    cube_half_size = model.geom_size[cube_geom_id]
    vertical_half_extent = float(
        np.abs(cube_rotation[2, :]) @ cube_half_size
    )

    # Target the top-center of the cube for a downward grasp.
    grasp_target = actual_cube_center + np.array([
        0.0, 0.0, vertical_half_extent
    ])
    approach_target = grasp_target + np.array([
        0.0, 0.0, APPROACH_HEIGHT
    ])

    target_rotation = make_top_down_rotation(
        model, data, tool_id
    )

    # Use separate data for IK: no IK iterations affect the visible robot.
    probe = mujoco.MjData(model)
    jac_pos = np.zeros((3, model.nv))
    jac_rot = np.zeros((3, model.nv))

    print("\n" + "=" * 64)
    print("F1: HARD-CODED CUBE PICK REACHABILITY TEST")
    print("=" * 64)
    print(f"Cube target center (world): {actual_cube_center}")
    print(f"Table geom: {TABLE_GEOM_NAME}")
    print(f"Approach target: {approach_target}")
    print(f"Grasp target:    {grasp_target}")
    print("Robot motion: disabled")

    # Check the approach target from the same initial arm pose.
    probe.qpos[:] = fixed_qpos
    probe.qvel[:] = fixed_qvel

    approach_result = solve_ik(
        model,
        probe,
        tool_id,
        qpos_addresses,
        dof_addresses,
        arm_joint_ids,
        approach_target,
        target_rotation,
        jac_pos,
        jac_rot,
    )

    # Reset to the initial pose before checking the grasp target.
    probe.qpos[:] = fixed_qpos
    probe.qvel[:] = fixed_qvel

    grasp_result = solve_ik(
        model,
        probe,
        tool_id,
        qpos_addresses,
        dof_addresses,
        arm_joint_ids,
        grasp_target,
        target_rotation,
        jac_pos,
        jac_rot,
    )

    pick_feasible_by_ik = (
        approach_result["reachable"]
        and grasp_result["reachable"]
    )

    if pick_feasible_by_ik:
        failure_type = None
        print("\nRESULT: IK can reach both approach and grasp targets.")
        print("Note: this does not guarantee a successful physical grasp.")
    else:
        failure_type = "F1_UNREACHABLE_PICK"
        print("\nRESULT: F1 FAILURE — PICK TARGET IS IK-UNREACHABLE.")
        print("The script will not attempt to move the robot.")

    print(
        f"Approach reachable: {approach_result['reachable']} "
        f"(position residual: "
        f"{approach_result['position_residual_m']:.4f} m)"
    )
    print(
        f"Grasp reachable:    {grasp_result['reachable']} "
        f"(position residual: "
        f"{grasp_result['position_residual_m']:.4f} m)"
    )

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "failure_id": "F1" if failure_type else None,
        "failure_type": failure_type,
        "robot_moved": False,
        "pose_fixed": True,
        "pose": POSE,
        "cube_center_world_m": actual_cube_center.tolist(),
        "approach_target_world_m": approach_target.tolist(),
        "grasp_target_world_m": grasp_target.tolist(),
        "approach_ik": approach_result,
        "grasp_ik": grasp_result,
        "pick_feasible_by_ik": pick_feasible_by_ik,
        "recovery_suggestion": (
            {
                "strategy": "REPLAN_ACTION",
                "actions": [
                    "Stop the current pick action",
                    "Replan the approach or request human intervention",
                ],
            }
            if not pick_feasible_by_ik
            else None
        ),
    }

    LOG_FILE.write_text(
        json.dumps(record, indent=2),
        encoding="utf-8",
    )
    print(f"Result log: {LOG_FILE.resolve()}")

    # Viewer displays the cube at the hardcoded position.
    # Restore robot joints every frame so the robot remains fixed.
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            data.qpos[qpos_addresses] = fixed_qpos[qpos_addresses]
            data.qvel[dof_addresses] = fixed_qvel[dof_addresses]
            mujoco.mj_forward(model, data)
            viewer.sync()
            time.sleep(0.03)


if __name__ == "__main__":
    main()
