
# #!/usr/bin/env python3
# """
# Find a tabletop cube position that neither arm can approach.

# - Both left and right arms are tested independently using IK.
# - The non-tested arm stays at its original joint configuration.
# - The visible robot remains at the original POSE.
# - The cube is placed at the first candidate where BOTH arms fail the
#   approach-pose test.
# - IK failure is not proof of collision-free or physical inaccessibility.
# """

# import json
# from datetime import datetime
# from pathlib import Path

# import mujoco
# import mujoco.viewer
# import numpy as np


# # ============================================================
# # CONFIGURATION
# # ============================================================

# ROOT = Path(__file__).resolve().parents[3]
# MODEL_PATH = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

# TABLE_GEOM_NAME = "table_collision_0"
# CUBE_NAME = "phase1_cube"

# LEFT_TOOL_NAME = "l_gripper_tool_frame"
# RIGHT_TOOL_NAME = "r_gripper_tool_frame"

# LEFT_ARM = [
#     "left_shoulder_pan_joint",
#     "left_shoulder_lift_joint",
#     "left_elbow_joint",
#     "left_wrist_1_joint",
#     "left_wrist_2_joint",
#     "left_wrist_3_joint",
# ]

# RIGHT_ARM = [
#     "right_shoulder_pan_joint",
#     "right_shoulder_lift_joint",
#     "right_elbow_joint",
#     "right_wrist_1_joint",
#     "right_wrist_2_joint",
#     "right_wrist_3_joint",
# ]

# # Do not change these initial joint positions.
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

# APPROACH_HEIGHT = 0.15
# GRASP_ABOVE_SURFACE = 0.02

# DAMPING = 0.03
# MAX_IK_STEPS = 300
# POSITION_TOL = 0.008
# ROTATION_TOL = 0.04
# ROTATION_WEIGHT = 0.25

# # Candidate spacing in the tabletop's local X/Y plane.
# GRID_STEP = 0.05

# LOG_PATH = Path.cwd() / "both_arms_unreachable_failure.json"


# # ============================================================
# # MUJOCO HELPERS
# # ============================================================

# def get_id(model, object_type, name):
#     """Return an object ID or raise a useful error."""
#     object_id = mujoco.mj_name2id(model, object_type, name)
#     if object_id < 0:
#         raise ValueError(
#             f"Could not find {object_type.name} named {name!r} "
#             f"in {MODEL_PATH}"
#         )
#     return object_id


# def get_arm_joint_data(model, joint_names):
#     """Return joint IDs, qpos addresses, and DOF addresses."""
#     joint_ids = []
#     qpos_addresses = []
#     dof_addresses = []

#     for name in joint_names:
#         jid = get_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)

#         if model.jnt_type[jid] != mujoco.mjtJoint.mjJNT_HINGE:
#             raise ValueError(f"{name} is not a hinge joint.")

#         joint_ids.append(jid)
#         qpos_addresses.append(model.jnt_qposadr[jid])
#         dof_addresses.append(model.jnt_dofadr[jid])

#     return (
#         np.asarray(joint_ids, dtype=int),
#         np.asarray(qpos_addresses, dtype=int),
#         np.asarray(dof_addresses, dtype=int),
#     )


# def rotation_error(current, target):
#     """Small-angle orientation error in world coordinates."""
#     return 0.5 * (
#         np.cross(current[:, 0], target[:, 0])
#         + np.cross(current[:, 1], target[:, 1])
#         + np.cross(current[:, 2], target[:, 2])
#     )


# def align_vector_rotation(source, target):
#     """Rotation matrix that aligns one 3D vector with another."""
#     source = np.asarray(source, dtype=float)
#     target = np.asarray(target, dtype=float)

#     source /= np.linalg.norm(source)
#     target /= np.linalg.norm(target)

#     cross = np.cross(source, target)
#     dot = np.clip(np.dot(source, target), -1.0, 1.0)

#     if dot > 1.0 - 1e-9:
#         return np.eye(3)

#     if dot < -1.0 + 1e-9:
#         axis = np.cross(source, [1.0, 0.0, 0.0])
#         if np.linalg.norm(axis) < 1e-8:
#             axis = np.cross(source, [0.0, 1.0, 0.0])
#         axis /= np.linalg.norm(axis)
#         return (
#             2.0 * np.outer(axis, axis) - np.eye(3)
#         )

#     skew = np.array([
#         [0.0, -cross[2], cross[1]],
#         [cross[2], 0.0, -cross[0]],
#         [-cross[1], cross[0], 0.0],
#     ])

#     return np.eye(3) + skew + (skew @ skew) / (1.0 + dot)


# def get_free_joint(model, body_id):
#     """Find the free joint that controls the cube body."""
#     for jid in range(model.njnt):
#         if (
#             model.jnt_bodyid[jid] == body_id
#             and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE
#         ):
#             return jid

#     raise ValueError(
#         f"Body {CUBE_NAME!r} has no free joint. "
#         "Update the cube-placement helper for this model."
#     )


# def find_cube_box_geom(model, cube_body_id):
#     """Find a box geometry attached directly to the cube body."""
#     for gid in range(model.ngeom):
#         if (
#             model.geom_bodyid[gid] == cube_body_id
#             and model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_BOX
#         ):
#             return gid

#     raise ValueError(
#         f"No box geom was found directly on body {CUBE_NAME!r}."
#     )


# def set_cube_geom_center(model, data, free_joint_id, cube_geom_id,
#                          center_world):
#     """
#     Move the cube so the box geom's center is at center_world.

#     The cube's existing orientation is preserved.
#     """
#     qadr = model.jnt_qposadr[free_joint_id]

#     body_quat = data.qpos[qadr + 3:qadr + 7].copy()
#     body_quat /= np.linalg.norm(body_quat)

#     rotation = np.empty(9, dtype=float)
#     mujoco.mju_quat2Mat(rotation, body_quat)
#     rotation = rotation.reshape(3, 3)

#     local_geom_offset = model.geom_pos[cube_geom_id]
#     body_position = (
#         np.asarray(center_world, dtype=float)
#         - rotation @ local_geom_offset
#     )

#     data.qpos[qadr:qadr + 3] = body_position
#     mujoco.mj_forward(model, data)


# def cube_half_height_world(data, cube_geom_id):
#     """Vertical half-extent of the cube's oriented box."""
#     rotation = data.geom_xmat[cube_geom_id].reshape(3, 3)
#     half_sizes = data.model.geom_size[cube_geom_id]

#     return float(np.sum(np.abs(rotation[2, :]) * half_sizes))


# # ============================================================
# # TABLETOP SEARCH
# # ============================================================

# def make_tabletop_candidates(model, data, table_geom_id,
#                              cube_geom_id, reference_xy):
#     """
#     Generate candidate cube centers inside the tabletop bounds.

#     Assumes the tabletop collision geometry is a box and the table
#     is approximately horizontal.
#     """
#     if model.geom_type[table_geom_id] != mujoco.mjtGeom.mjGEOM_BOX:
#         raise ValueError(
#             f"{TABLE_GEOM_NAME!r} is not a box geom. "
#             "Adapt candidate generation to the table geometry."
#         )

#     table_center = data.geom_xpos[table_geom_id].copy()
#     table_rotation = data.geom_xmat[table_geom_id].reshape(3, 3)
#     table_half_sizes = model.geom_size[table_geom_id].copy()

#     # Account for the cube's footprint by leaving a margin from edges.
#     cube_half_sizes = model.geom_size[cube_geom_id]
#     margin_x = float(cube_half_sizes[0]) + 0.01
#     margin_y = float(cube_half_sizes[1]) + 0.01

#     x_min = -table_half_sizes[0] + margin_x
#     x_max = table_half_sizes[0] - margin_x
#     y_min = -table_half_sizes[1] + margin_y
#     y_max = table_half_sizes[1] - margin_y

#     if x_min >= x_max or y_min >= y_max:
#         raise ValueError(
#             "Cube footprint is too large for the tabletop search area."
#         )

#     local_x_values = np.arange(
#         x_min, x_max + GRID_STEP * 0.5, GRID_STEP
#     )
#     local_y_values = np.arange(
#         y_min, y_max + GRID_STEP * 0.5, GRID_STEP
#     )

#     # Compute the tabletop's top-center reference.
#     table_top_local = np.array([
#         0.0, 0.0, table_half_sizes[2]
#     ])
#     table_top_world = table_center + table_rotation @ table_top_local

#     candidates = []

#     for local_x in local_x_values:
#         for local_y in local_y_values:
#             local_surface_point = np.array([
#                 local_x, local_y, table_half_sizes[2]
#             ])
#             surface_world = (
#                 table_center + table_rotation @ local_surface_point
#             )

#             # The cube sits on a horizontal tabletop.
#             # Its center is above the surface by its vertical half-height.
#             center_world = surface_world.copy()
#             center_world[2] = (
#                 table_top_world[2]
#                 + float(cube_half_sizes[2])
#             )

#             distance = np.linalg.norm(
#                 center_world[:2] - reference_xy
#             )

#             candidates.append({
#                 "center": center_world,
#                 "surface": surface_world,
#                 "distance": float(distance),
#             })

#     # Test far-away candidates first, while searching the whole table.
#     candidates.sort(
#         key=lambda item: item["distance"],
#         reverse=True,
#     )

#     return candidates


# # ============================================================
# # IK CHECK
# # ============================================================

# def solve_ik(model, probe, tool_body_id, joint_ids,
#              qpos_addresses, dof_addresses,
#              target_position, target_rotation):
#     """
#     Test whether one arm can reach a target pose.

#     The probe state is reset before this call. Only the specified
#     arm's joints are changed; the other arm remains at POSE.
#     """
#     initial_qpos = probe.qpos.copy()
#     initial_qvel = probe.qvel.copy()

#     try:
#         for _ in range(MAX_IK_STEPS):
#             mujoco.mj_forward(model, probe)

#             current_position = probe.xpos[tool_body_id].copy()
#             current_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()

#             position_error = target_position - current_position
#             orientation_error = rotation_error(
#                 current_rotation, target_rotation
#             )

#             position_norm = np.linalg.norm(position_error)
#             rotation_norm = np.linalg.norm(orientation_error)

#             if (
#                 position_norm <= POSITION_TOL
#                 and rotation_norm <= ROTATION_TOL
#             ):
#                 return {
#                     "reachable": True,
#                     "position_error_m": float(position_norm),
#                     "rotation_error_rad": float(rotation_norm),
#                     "iterations": _ + 1,
#                 }

#             jacp = np.zeros((3, model.nv), dtype=float)
#             jacr = np.zeros((3, model.nv), dtype=float)

#             mujoco.mj_jacBody(
#                 model, probe, jacp, jacr, tool_body_id
#             )

#             # Use only this arm's six joint columns.
#             Jp = jacp[:, dof_addresses]
#             Jr = jacr[:, dof_addresses] * ROTATION_WEIGHT

#             J = np.vstack((Jp, Jr))
#             error = np.concatenate((
#                 position_error,
#                 orientation_error * ROTATION_WEIGHT,
#             ))

#             # Damped least-squares step.
#             lhs = J @ J.T + (DAMPING ** 2) * np.eye(6)
#             delta = J.T @ np.linalg.solve(lhs, error)

#             # Limit each iteration for numerical stability.
#             delta = np.clip(delta, -0.08, 0.08)
#             probe.qpos[qpos_addresses] += delta

#             # Respect each hinge joint's limits.
#             for index, jid in enumerate(joint_ids):
#                 if model.jnt_limited[jid]:
#                     low, high = model.jnt_range[jid]
#                     qadr = qpos_addresses[index]
#                     probe.qpos[qadr] = np.clip(
#                         probe.qpos[qadr], low, high
#                     )

#         mujoco.mj_forward(model, probe)

#         final_position = probe.xpos[tool_body_id].copy()
#         final_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()

#         return {
#             "reachable": bool(
#                 np.linalg.norm(target_position - final_position)
#                 <= POSITION_TOL
#                 and np.linalg.norm(
#                     rotation_error(final_rotation, target_rotation)
#                 ) <= ROTATION_TOL
#             ),
#             "position_error_m": float(
#                 np.linalg.norm(target_position - final_position)
#             ),
#             "rotation_error_rad": float(
#                 np.linalg.norm(
#                     rotation_error(final_rotation, target_rotation)
#                 )
#             ),
#             "iterations": MAX_IK_STEPS,
#         }

#     finally:
#         # Restore the complete probe state after this IK test.
#         probe.qpos[:] = initial_qpos
#         probe.qvel[:] = initial_qvel
#         mujoco.mj_forward(model, probe)


# def check_arm_at_candidate(
#     model,
#     probe,
#     fixed_qpos,
#     fixed_qvel,
#     free_joint_id,
#     cube_geom_id,
#     candidate_center,
#     tool_body_id,
#     joint_ids,
#     qpos_addresses,
#     dof_addresses,
# ):
#     """Test approach and grasp targets for a single arm."""
#     probe.qpos[:] = fixed_qpos
#     probe.qvel[:] = fixed_qvel
#     mujoco.mj_forward(model, probe)

#     set_cube_geom_center(
#         model, probe, free_joint_id, cube_geom_id, candidate_center
#     )

#     # Compute the top of the cube from its actual geom orientation.
#     cube_top = probe.geom_xpos[cube_geom_id].copy()
#     cube_top[2] += cube_half_height_world(probe, cube_geom_id)

#     grasp_target = cube_top.copy()
#     grasp_target[2] += GRASP_ABOVE_SURFACE

#     approach_target = grasp_target.copy()
#     approach_target[2] += APPROACH_HEIGHT

#     # Make a top-down orientation based on this arm's initial tool pose.
#     mujoco.mj_forward(model, probe)
#     initial_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()

#     down_alignment = align_vector_rotation(
#         initial_rotation[:, 2],
#         np.array([0.0, 0.0, -1.0]),
#     )
#     target_rotation = down_alignment @ initial_rotation

#     approach_result = solve_ik(
#         model, probe, tool_body_id,
#         joint_ids, qpos_addresses, dof_addresses,
#         approach_target, target_rotation,
#     )

#     grasp_result = solve_ik(
#         model, probe, tool_body_id,
#         joint_ids, qpos_addresses, dof_addresses,
#         grasp_target, target_rotation,
#     )

#     return {
#         "approach": approach_result,
#         "grasp": grasp_result,
#         "approach_target_m": approach_target.tolist(),
#         "grasp_target_m": grasp_target.tolist(),
#     }


# # ============================================================
# # MAIN
# # ============================================================

# def main():
#     if not MODEL_PATH.exists():
#         raise FileNotFoundError(
#             f"MuJoCo model not found: {MODEL_PATH}\n"
#             "Check ROOT and MODEL_PATH at the top of the script."
#         )

#     model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
#     data = mujoco.MjData(model)

#     mujoco.mj_forward(model, data)

#     table_geom_id = get_id(
#         model, mujoco.mjtObj.mjOBJ_GEOM, TABLE_GEOM_NAME
#     )
#     cube_body_id = get_id(
#         model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME
#     )
#     left_tool_id = get_id(
#         model, mujoco.mjtObj.mjOBJ_BODY, LEFT_TOOL_NAME
#     )
#     right_tool_id = get_id(
#         model, mujoco.mjtObj.mjOBJ_BODY, RIGHT_TOOL_NAME
#     )

#     free_joint_id = get_free_joint(model, cube_body_id)
#     cube_geom_id = find_cube_box_geom(model, cube_body_id)

#     left_joint_ids, left_qpos, left_dof = get_arm_joint_data(
#         model, LEFT_ARM
#     )
#     right_joint_ids, right_qpos, right_dof = get_arm_joint_data(
#         model, RIGHT_ARM
#     )

#     # Apply the original, fixed initial joint pose.
#     for joint_name, angle in POSE.items():
#         jid = get_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
#         data.qpos[model.jnt_qposadr[jid]] = angle

#     mujoco.mj_forward(model, data)

#     # Preserve the robot's initial state. The visible robot will never
#     # be commanded toward any IK target.
#     fixed_qpos = data.qpos.copy()
#     fixed_qvel = data.qvel.copy()

#     left_initial_xy = data.xpos[left_tool_id][:2].copy()
#     right_initial_xy = data.xpos[right_tool_id][:2].copy()
#     reference_xy = 0.5 * (left_initial_xy + right_initial_xy)

#     probe = mujoco.MjData(model)
#     probe.qpos[:] = fixed_qpos
#     probe.qvel[:] = fixed_qvel
#     mujoco.mj_forward(model, probe)

#     candidates = make_tabletop_candidates(
#         model, probe, table_geom_id, cube_geom_id, reference_xy
#     )

#     print("=" * 68)
#     print("DUAL-ARM UNREACHABLE CUBE SEARCH")
#     print("=" * 68)
#     print(f"Model: {MODEL_PATH}")
#     print(f"Table geometry: {TABLE_GEOM_NAME}")
#     print(f"Candidate positions: {len(candidates)}")
#     print("Robot joint pose: FIXED")
#     print("Testing left and right arms independently...")
#     print()

#     selected = None

#     for index, candidate in enumerate(candidates, start=1):
#         center = candidate["center"]

#         left_result = check_arm_at_candidate(
#             model, probe, fixed_qpos, fixed_qvel,
#             free_joint_id, cube_geom_id, center,
#             left_tool_id, left_joint_ids, left_qpos, left_dof,
#         )

#         right_result = check_arm_at_candidate(
#             model, probe, fixed_qpos, fixed_qvel,
#             free_joint_id, cube_geom_id, center,
#             right_tool_id, right_joint_ids, right_qpos, right_dof,
#         )

#         left_approach_reachable = left_result["approach"]["reachable"]
#         right_approach_reachable = right_result["approach"]["reachable"]

#         print(
#             f"[{index:03d}/{len(candidates):03d}] "
#             f"cube_center={np.round(center, 3)} | "
#             f"left approach={left_approach_reachable}, "
#             f"left grasp={left_result['grasp']['reachable']} | "
#             f"right approach={right_approach_reachable}, "
#             f"right grasp={right_result['grasp']['reachable']}"
#         )

#         # Required condition: neither arm can reach the approach pose.
#         if (
#             not left_approach_reachable
#             and not right_approach_reachable
#         ):
#             selected = {
#                 "cube_center_m": center.tolist(),
#                 "left_arm": left_result,
#                 "right_arm": right_result,
#                 "candidate_index": index,
#             }
#             break

#     if selected is None:
#         print()
#         print("NO QUALIFYING POSITION FOUND.")
#         print(
#             "No tested tabletop candidate made the approach pose "
#             "unreachable for both arms."
#         )
#         print(
#             "Try a finer GRID_STEP or inspect the model/table geometry "
#             "and the IK tolerances."
#         )
#         return

#     # Place the cube in the visible simulation at the selected location.
#     # The robot's original joint positions remain unchanged.
#     set_cube_geom_center(
#         model,
#         data,
#         free_joint_id,
#         cube_geom_id,
#         np.array(selected["cube_center_m"]),
#     )

#     # Reassert the robot's original joint positions and velocities.
#     # Only the cube placement is intended to differ.
#     for joint_names in (LEFT_ARM, RIGHT_ARM):
#         for joint_name in joint_names:
#             jid = get_id(
#                 model, mujoco.mjtObj.mjOBJ_JOINT, joint_name
#             )
#             qadr = model.jnt_qposadr[jid]
#             dadr = model.jnt_dofadr[jid]
#             data.qpos[qadr] = fixed_qpos[qadr]
#             data.qvel[dadr] = fixed_qvel[dadr]

#     mujoco.mj_forward(model, data)

#     report = {
#         "timestamp": datetime.now().isoformat(timespec="seconds"),
#         "failure_type": "BOTH_ARMS_IK_UNREACHABLE_APPROACH",
#         "model_path": str(MODEL_PATH),
#         "table_geom": TABLE_GEOM_NAME,
#         "cube_body": CUBE_NAME,
#         "cube_geom_center_world_m": selected["cube_center_m"],
#         "candidate_index": selected["candidate_index"],
#         "left_arm": selected["left_arm"],
#         "right_arm": selected["right_arm"],
#         "pose_unchanged": True,
#         "robot_motion": "NONE",
#         "interpretation": (
#             "Both arms failed the IK approach-pose test for this "
#             "candidate. This does not prove collision-free path "
#             "infeasibility or physical grasp failure."
#         ),
#     }

#     LOG_PATH.write_text(json.dumps(report, indent=2))

#     print()
#     print("=" * 68)
#     print("DUAL-ARM FAILURE FOUND")
#     print("=" * 68)
#     print(
#         "Cube geom center (world metres): "
#         f"{np.round(selected['cube_center_m'], 4)}"
#     )
#     print(
#         "Left arm: "
#         f"approach reachable = "
#         f"{selected['left_arm']['approach']['reachable']}, "
#         f"grasp reachable = "
#         f"{selected['left_arm']['grasp']['reachable']}"
#     )
#     print(
#         "Right arm: "
#         f"approach reachable = "
#         f"{selected['right_arm']['approach']['reachable']}, "
#         f"grasp reachable = "
#         f"{selected['right_arm']['grasp']['reachable']}"
#     )
#     print(f"Failure log: {LOG_PATH}")
#     print("Robot motion: NONE")
#     print()
#     print("Opening viewer. Close the viewer window to exit.")

#     # Viewer state: cube is at the selected location; both arms stay fixed.
#     with mujoco.viewer.launch_passive(model, data) as viewer:
#         while viewer.is_running():
#             # Reassert the initial arm pose so the visible robot remains
#             # fixed even while the simulation viewer is running.
#             for joint_names in (LEFT_ARM, RIGHT_ARM):
#                 for joint_name in joint_names:
#                     jid = get_id(
#                         model,
#                         mujoco.mjtObj.mjOBJ_JOINT,
#                         joint_name,
#                     )
#                     qadr = model.jnt_qposadr[jid]
#                     dadr = model.jnt_dofadr[jid]
#                     data.qpos[qadr] = fixed_qpos[qadr]
#                     data.qvel[dadr] = fixed_qvel[dadr]

#             mujoco.mj_forward(model, data)
#             viewer.sync()


# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
"""
F1 failure injection: hardcoded cube location.

Cube geom center: [0.150, -0.500, 0.895] metres.

Expected from the user's candidate search:
    Left arm:  approach reachable, grasp reachable
    Right arm: approach unreachable, grasp unreachable

The script verifies these results with IK. It does not move either arm.
"""

import json
from datetime import datetime
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np


# ============================================================
# MODEL CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

CUBE_NAME = "phase1_cube"
TABLE_GEOM_NAME = "table_collision_0"

LEFT_TOOL_NAME = "l_gripper_tool_frame"
RIGHT_TOOL_NAME = "r_gripper_tool_frame"

# Hardcoded world coordinates of the cube GEOMETRY CENTER.
CUBE_TARGET = np.array([0.150, -0.500, 0.895], dtype=float)

LEFT_ARM = [
    "left_shoulder_pan_joint",
    "left_shoulder_lift_joint",
    "left_elbow_joint",
    "left_wrist_1_joint",
    "left_wrist_2_joint",
    "left_wrist_3_joint",
]

RIGHT_ARM = [
    "right_shoulder_pan_joint",
    "right_shoulder_lift_joint",
    "right_elbow_joint",
    "right_wrist_1_joint",
    "right_wrist_2_joint",
    "right_wrist_3_joint",
]

# Original initial pose. DO NOT CHANGE THESE VALUES.
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

APPROACH_HEIGHT = 0.15
GRASP_ABOVE_SURFACE = 0.02

DAMPING = 0.03
MAX_IK_STEPS = 300
POSITION_TOL = 0.008
ROTATION_TOL = 0.04
ROTATION_WEIGHT = 0.25

LOG_PATH = Path.cwd() / "f1_dual_arm_test_failure.json"


# ============================================================
# HELPERS
# ============================================================

def get_id(model, object_type, name):
    object_id = mujoco.mj_name2id(model, object_type, name)
    if object_id < 0:
        raise ValueError(
            f"MuJoCo object not found: {object_type.name} '{name}'. "
            "Check the object name in the model XML."
        )
    return object_id


def get_arm_joint_data(model, joint_names):
    joint_ids = []
    qpos_addresses = []
    dof_addresses = []

    for name in joint_names:
        jid = get_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)

        if model.jnt_type[jid] != mujoco.mjtJoint.mjJNT_HINGE:
            raise ValueError(f"Expected hinge joint: {name}")

        joint_ids.append(jid)
        qpos_addresses.append(model.jnt_qposadr[jid])
        dof_addresses.append(model.jnt_dofadr[jid])

    return (
        np.asarray(joint_ids, dtype=int),
        np.asarray(qpos_addresses, dtype=int),
        np.asarray(dof_addresses, dtype=int),
    )


def rotation_error(current, target):
    return 0.5 * (
        np.cross(current[:, 0], target[:, 0])
        + np.cross(current[:, 1], target[:, 1])
        + np.cross(current[:, 2], target[:, 2])
    )


def align_vector_rotation(source, target):
    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)

    source = source / np.linalg.norm(source)
    target = target / np.linalg.norm(target)

    cross = np.cross(source, target)
    dot = np.clip(np.dot(source, target), -1.0, 1.0)

    if dot > 1.0 - 1e-9:
        return np.eye(3)

    if dot < -1.0 + 1e-9:
        axis = np.cross(source, [1.0, 0.0, 0.0])
        if np.linalg.norm(axis) < 1e-8:
            axis = np.cross(source, [0.0, 1.0, 0.0])
        axis /= np.linalg.norm(axis)
        return 2.0 * np.outer(axis, axis) - np.eye(3)

    skew = np.array([
        [0.0, -cross[2], cross[1]],
        [cross[2], 0.0, -cross[0]],
        [-cross[1], cross[0], 0.0],
    ])

    return np.eye(3) + skew + (skew @ skew) / (1.0 + dot)


def find_free_joint(model, body_id):
    for jid in range(model.njnt):
        if (
            model.jnt_bodyid[jid] == body_id
            and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE
        ):
            return jid

    raise ValueError(
        f"Cube body '{CUBE_NAME}' does not have a free joint."
    )


def find_cube_box_geom(model, cube_body_id):
    for gid in range(model.ngeom):
        if (
            model.geom_bodyid[gid] == cube_body_id
            and model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_BOX
        ):
            return gid

    raise ValueError(
        f"No box geom found directly on cube body '{CUBE_NAME}'."
    )


def set_cube_geom_center(model, data, free_joint_id,
                         cube_geom_id, center_world):
    """Position the cube geom center while preserving cube orientation."""
    qadr = model.jnt_qposadr[free_joint_id]

    quat = data.qpos[qadr + 3:qadr + 7].copy()
    quat /= np.linalg.norm(quat)

    rotation_flat = np.empty(9)
    mujoco.mju_quat2Mat(rotation_flat, quat)
    rotation = rotation_flat.reshape(3, 3)

    local_geom_offset = model.geom_pos[cube_geom_id]
    body_position = (
        np.asarray(center_world, dtype=float)
        - rotation @ local_geom_offset
    )

    data.qpos[qadr:qadr + 3] = body_position
    mujoco.mj_forward(model, data)


def cube_half_height_world(data, cube_geom_id):
    rotation = data.geom_xmat[cube_geom_id].reshape(3, 3)
    half_sizes = data.model.geom_size[cube_geom_id]
    return float(np.sum(np.abs(rotation[2, :]) * half_sizes))


# ============================================================
# INVERSE KINEMATICS
# ============================================================

def solve_ik(
    model,
    probe,
    tool_body_id,
    joint_ids,
    qpos_addresses,
    dof_addresses,
    target_position,
    target_rotation,
):
    """
    Test one arm with damped least-squares IK.

    Only the selected arm's joints are updated. The caller restores
    the probe state after the test.
    """
    for iteration in range(MAX_IK_STEPS):
        mujoco.mj_forward(model, probe)

        current_position = probe.xpos[tool_body_id].copy()
        current_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()

        pos_error = target_position - current_position
        rot_error = rotation_error(current_rotation, target_rotation)

        pos_norm = float(np.linalg.norm(pos_error))
        rot_norm = float(np.linalg.norm(rot_error))

        if pos_norm <= POSITION_TOL and rot_norm <= ROTATION_TOL:
            return {
                "reachable": True,
                "position_error_m": pos_norm,
                "rotation_error_rad": rot_norm,
                "iterations": iteration + 1,
            }

        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jacBody(
            model, probe, jacp, jacr, tool_body_id
        )

        Jp = jacp[:, dof_addresses]
        Jr = jacr[:, dof_addresses] * ROTATION_WEIGHT

        J = np.vstack((Jp, Jr))
        error = np.concatenate((
            pos_error,
            rot_error * ROTATION_WEIGHT,
        ))

        lhs = J @ J.T + DAMPING**2 * np.eye(6)
        delta = J.T @ np.linalg.solve(lhs, error)
        delta = np.clip(delta, -0.08, 0.08)

        probe.qpos[qpos_addresses] += delta

        # Clamp joints to model-defined limits.
        for index, jid in enumerate(joint_ids):
            if model.jnt_limited[jid]:
                low, high = model.jnt_range[jid]
                probe.qpos[qpos_addresses[index]] = np.clip(
                    probe.qpos[qpos_addresses[index]], low, high
                )

    mujoco.mj_forward(model, probe)

    final_position = probe.xpos[tool_body_id].copy()
    final_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()

    final_pos_error = float(
        np.linalg.norm(target_position - final_position)
    )
    final_rot_error = float(
        np.linalg.norm(
            rotation_error(final_rotation, target_rotation)
        )
    )

    return {
        "reachable": (
            final_pos_error <= POSITION_TOL
            and final_rot_error <= ROTATION_TOL
        ),
        "position_error_m": final_pos_error,
        "rotation_error_rad": final_rot_error,
        "iterations": MAX_IK_STEPS,
    }


def check_arm(
    model,
    probe,
    fixed_qpos,
    fixed_qvel,
    free_joint_id,
    cube_geom_id,
    cube_center,
    tool_body_id,
    joint_ids,
    qpos_addresses,
    dof_addresses,
):
    """Check approach and grasp reachability for one arm."""
    probe.qpos[:] = fixed_qpos
    probe.qvel[:] = fixed_qvel
    mujoco.mj_forward(model, probe)

    set_cube_geom_center(
        model, probe, free_joint_id, cube_geom_id, cube_center
    )

    cube_top = probe.geom_xpos[cube_geom_id].copy()
    cube_top[2] += cube_half_height_world(probe, cube_geom_id)

    grasp_target = cube_top.copy()
    grasp_target[2] += GRASP_ABOVE_SURFACE

    approach_target = grasp_target.copy()
    approach_target[2] += APPROACH_HEIGHT

    initial_rotation = probe.xmat[tool_body_id].reshape(3, 3).copy()
    align_down = align_vector_rotation(
        initial_rotation[:, 2],
        np.array([0.0, 0.0, -1.0]),
    )
    target_rotation = align_down @ initial_rotation

    initial_probe_qpos = probe.qpos.copy()
    initial_probe_qvel = probe.qvel.copy()

    try:
        approach_result = solve_ik(
            model, probe, tool_body_id,
            joint_ids, qpos_addresses, dof_addresses,
            approach_target, target_rotation,
        )

        # Reset before the grasp test so it starts from the same
        # original robot configuration.
        probe.qpos[:] = initial_probe_qpos
        probe.qvel[:] = initial_probe_qvel
        mujoco.mj_forward(model, probe)

        grasp_result = solve_ik(
            model, probe, tool_body_id,
            joint_ids, qpos_addresses, dof_addresses,
            grasp_target, target_rotation,
        )

    finally:
        probe.qpos[:] = initial_probe_qpos
        probe.qvel[:] = initial_probe_qvel
        mujoco.mj_forward(model, probe)

    return {
        "approach": approach_result,
        "grasp": grasp_result,
        "approach_target_m": approach_target.tolist(),
        "grasp_target_m": grasp_target.tolist(),
    }


# ============================================================
# MAIN FAILURE-INJECTION TEST
# ============================================================

def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Update ROOT or MODEL_PATH to match your workspace."
        )

    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    # Resolve scene objects.
    get_id(model, mujoco.mjtObj.mjOBJ_GEOM, TABLE_GEOM_NAME)

    cube_body_id = get_id(
        model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME
    )
    cube_geom_id = find_cube_box_geom(model, cube_body_id)
    free_joint_id = find_free_joint(model, cube_body_id)

    left_tool_id = get_id(
        model, mujoco.mjtObj.mjOBJ_BODY, LEFT_TOOL_NAME
    )
    right_tool_id = get_id(
        model, mujoco.mjtObj.mjOBJ_BODY, RIGHT_TOOL_NAME
    )

    left_ids, left_qpos, left_dof = get_arm_joint_data(
        model, LEFT_ARM
    )
    right_ids, right_qpos, right_dof = get_arm_joint_data(
        model, RIGHT_ARM
    )

    # Set the original robot pose exactly.
    for joint_name, angle in POSE.items():
        jid = get_id(
            model, mujoco.mjtObj.mjOBJ_JOINT, joint_name
        )
        data.qpos[model.jnt_qposadr[jid]] = angle

    mujoco.mj_forward(model, data)

    # Save the robot's initial state. The visible robot is never driven
    # by the IK solver.
    fixed_qpos = data.qpos.copy()
    fixed_qvel = data.qvel.copy()

    # Place the cube at the hardcoded world coordinate.
    set_cube_geom_center(
        model, data, free_joint_id, cube_geom_id, CUBE_TARGET
    )

    # Build an isolated IK probe.
    probe = mujoco.MjData(model)
    probe.qpos[:] = data.qpos
    probe.qvel[:] = data.qvel
    mujoco.mj_forward(model, probe)

    print("=" * 64)
    print("F1 FAILURE-INJECTION TEST")
    print("=" * 64)
    print(f"Hardcoded cube geom center: {CUBE_TARGET.tolist()}")
    print("Original robot POSE: unchanged")
    print("Robot motion: NONE")
    print()

    left_result = check_arm(
        model, probe, fixed_qpos, fixed_qvel,
        free_joint_id, cube_geom_id, CUBE_TARGET,
        left_tool_id, left_ids, left_qpos, left_dof,
    )

    right_result = check_arm(
        model, probe, fixed_qpos, fixed_qvel,
        free_joint_id, cube_geom_id, CUBE_TARGET,
        right_tool_id, right_ids, right_qpos, right_dof,
    )

    print("LEFT ARM")
    print(f"  Approach reachable: {left_result['approach']['reachable']}")
    print(f"  Grasp reachable:    {left_result['grasp']['reachable']}")
    print(
        f"  Approach position error: "
        f"{left_result['approach']['position_error_m']:.4f} m"
    )
    print(
        f"  Grasp position error: "
        f"{left_result['grasp']['position_error_m']:.4f} m"
    )

    print()
    print("RIGHT ARM")
    print(f"  Approach reachable: {right_result['approach']['reachable']}")
    print(f"  Grasp reachable:    {right_result['grasp']['reachable']}")
    print(
        f"  Approach position error: "
        f"{right_result['approach']['position_error_m']:.4f} m"
    )
    print(
        f"  Grasp position error: "
        f"{right_result['grasp']['position_error_m']:.4f} m"
    )

    # Failure condition: right arm cannot reach approach or grasp,
    # while the left arm remains capable of both.
    right_failed = (
        not right_result["approach"]["reachable"]
        or not right_result["grasp"]["reachable"]
    )
    left_passed = (
        left_result["approach"]["reachable"]
        and left_result["grasp"]["reachable"]
    )

    if right_failed and left_passed:
        failure_type = "F1_RIGHT_ARM_IK_UNREACHABLE"
        recovery_suggestion = "REPLAN_ACTION"
        print()
        print("F1 FAILURE CONFIRMED: RIGHT ARM IK UNREACHABLE")
        print("Left arm passes the approach and grasp IK checks.")
        print("Recovery suggestion: REPLAN_ACTION")
    else:
        failure_type = "F1_EXPECTED_CONDITION_NOT_CONFIRMED"
        recovery_suggestion = "RECHECK_CONFIGURATION"
        print()
        print("EXPECTED FAILURE CONDITION NOT CONFIRMED.")
        print(
            "The IK results differ from the earlier candidate search. "
            "Inspect the tool names, target orientation, joint limits, "
            "and IK convergence before interpreting this as a failure."
        )

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "failure_type": failure_type,
        "cube_geom_center_world_m": CUBE_TARGET.tolist(),
        "left_arm": left_result,
        "right_arm": right_result,
        "pose_unchanged": True,
        "robot_motion": "NONE",
        "recovery_suggestion": recovery_suggestion,
        "note": (
            "IK reachability is a kinematic test, not proof of "
            "collision-free path feasibility or physical grasp success."
        ),
    }

    LOG_PATH.write_text(json.dumps(report, indent=2))
    print(f"Failure report saved to: {LOG_PATH}")

    # Reassert fixed robot joint positions for the viewer.
    for joint_names in (LEFT_ARM, RIGHT_ARM):
        for joint_name in joint_names:
            jid = get_id(
                model, mujoco.mjtObj.mjOBJ_JOINT, joint_name
            )
            qadr = model.jnt_qposadr[jid]
            dadr = model.jnt_dofadr[jid]
            data.qpos[qadr] = fixed_qpos[qadr]
            data.qvel[dadr] = fixed_qvel[dadr]

    mujoco.mj_forward(model, data)

    print("Opening viewer. Close the viewer window to exit.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            # Keep the robot at its original pose. No IK commands are
            # ever applied to the visible simulation.
            for joint_names in (LEFT_ARM, RIGHT_ARM):
                for joint_name in joint_names:
                    jid = get_id(
                        model,
                        mujoco.mjtObj.mjOBJ_JOINT,
                        joint_name,
                    )
                    qadr = model.jnt_qposadr[jid]
                    dadr = model.jnt_dofadr[jid]
                    data.qpos[qadr] = fixed_qpos[qadr]
                    data.qvel[dadr] = fixed_qvel[dadr]

            mujoco.mj_forward(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
