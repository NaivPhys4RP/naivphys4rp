#!/usr/bin/env python3
"""Randomized Tracy pick-and-place reachability audit for MuJoCo.

Workspace-rejected or IK-unreachable trials are never executed.
Cube carrying is a kinematic attachment surrogate, not physical grasp dynamics.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

try:
    import mujoco.viewer
except ImportError:
    mujoco_viewer_available = False
else:
    mujoco_viewer_available = True


ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "tracy_ws" / "tracy_mjcf" / "tracy_collision_phase1.xml"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

CUBE_BODY_NAME = "phase1_cube"
TABLE_GEOM_NAME = "table_collision_0"
LEFT_TOOL_BODY_NAME = "l_gripper_tool_frame"
RIGHT_TOOL_BODY_NAME = "r_gripper_tool_frame"

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

# Keep the initial pose exactly as specified.
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

N_TRIALS = 10
RANDOM_SEED = 40
TABLE_EDGE_MARGIN = 0.04
PLACE_EXCLUSION_RADIUS = 0.09

# Workspace gate: reject cubes beyond the far side of the table.
# Positive projection means toward the robot; negative means away from it.
MAX_FAR_SIDE_PAST_TABLE_CENTER = 0.08  # metres

APPROACH_HEIGHT = 0.15
GRASP_CLEARANCE = 0.02
ANIMATION_FRAMES = 55
FRAME_DELAY = 0.01
REJECTION_PAUSE_SECONDS = 5.0
DAMPING = 0.03
MAX_IK_STEPS = 300
POSITION_TOL = 0.008
ROTATION_TOL = 0.04
ROTATION_WEIGHT = 0.25
MAX_DQ_PER_STEP = 0.035

RECOVERY_STRATEGY = "CHANGE_OBJECT_POSITION"
EXECUTION_MODE = "kinematic_attachment_surrogate"


def name2id(
    model: mujoco.MjModel,
    obj_type: Any,
    name: str,
    required: bool = True,
) -> int:
    idx = int(mujoco.mj_name2id(model, obj_type, name))
    if idx < 0 and required:
        raise RuntimeError(f"MuJoCo object not found: {name!r}")
    return idx


def joint_info(
    model: mujoco.MjModel,
    joint_names: list[str],
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    joint_ids = []
    qpos_addresses = []
    dof_addresses = []

    for name in joint_names:
        jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        joint_ids.append(jid)
        qpos_addresses.append(int(model.jnt_qposadr[jid]))
        dof_addresses.append(int(model.jnt_dofadr[jid]))

    return (
        np.asarray(qpos_addresses, dtype=int),
        np.asarray(dof_addresses, dtype=int),
        joint_ids,
    )


def get_free_joint(
    model: mujoco.MjModel,
    body_id: int,
) -> tuple[int, int]:
    for joint_id in range(int(model.njnt)):
        if int(model.jnt_bodyid[joint_id]) != int(body_id):
            continue
        if int(model.jnt_type[joint_id]) == int(mujoco.mjtJoint.mjJNT_FREE):
            return joint_id, int(model.jnt_qposadr[joint_id])

    body_name = mujoco.mj_id2name(
        model, mujoco.mjtObj.mjOBJ_BODY, int(body_id)
    )
    raise RuntimeError(
        f"No free joint found for cube body {body_name!r}. "
        "The cube must have a free joint."
    )


def rotation_error(
    target: np.ndarray,
    current: np.ndarray,
) -> np.ndarray:
    """World-frame axis-angle orientation error from current to target."""
    relative = target @ current.T
    cosine = float(np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0))
    angle = math.acos(cosine)

    if angle < 1e-8:
        return np.zeros(3)

    if math.pi - angle < 1e-5:
        vals, vecs = np.linalg.eig(relative)
        axis = np.real(vecs[:, int(np.argmin(np.abs(vals - 1.0)))])
        axis /= max(float(np.linalg.norm(axis)), 1e-12)
        return angle * axis

    return (angle / (2.0 * math.sin(angle))) * np.array([
        relative[2, 1] - relative[1, 2],
        relative[0, 2] - relative[2, 0],
        relative[1, 0] - relative[0, 1],
    ])


def set_arm_pose(
    data: mujoco.MjData,
    qpos_addresses: np.ndarray,
    q: np.ndarray,
) -> None:
    data.qpos[qpos_addresses] = q


def clip_arm_to_joint_limits(
    model: mujoco.MjModel,
    q: np.ndarray,
    joint_ids: list[int],
) -> np.ndarray:
    q = q.copy()

    for k, jid in enumerate(joint_ids):
        if bool(model.jnt_limited[jid]):
            low, high = model.jnt_range[jid]
            q[k] = np.clip(q[k], low, high)

    return q


def get_tool_rotation_for_arm(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    tool_body_id: int,
    qpos_addresses: np.ndarray,
    home_q: np.ndarray,
) -> np.ndarray:
    set_arm_pose(data, qpos_addresses, home_q)
    mujoco.mj_forward(model, data)
    return data.xmat[tool_body_id].reshape(3, 3).copy()


def solve_ik(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    tool_body_id: int,
    qpos_addresses: np.ndarray,
    dof_addresses: np.ndarray,
    joint_ids: list[int],
    seed_q: np.ndarray,
    target_position: np.ndarray,
    target_rotation: np.ndarray,
) -> tuple[bool, np.ndarray, dict[str, float]]:
    """Damped least-squares IK for one six-joint arm."""
    q = seed_q.copy()
    jac_pos = np.zeros((3, model.nv), dtype=float)
    jac_rot = np.zeros((3, model.nv), dtype=float)

    for _ in range(MAX_IK_STEPS):
        set_arm_pose(data, qpos_addresses, q)
        mujoco.mj_forward(model, data)

        current_position = data.xpos[tool_body_id].copy()
        current_rotation = data.xmat[tool_body_id].reshape(3, 3).copy()

        pos_error = target_position - current_position
        rot_error = rotation_error(target_rotation, current_rotation)

        pos_norm = float(np.linalg.norm(pos_error))
        rot_norm = float(np.linalg.norm(rot_error))

        if pos_norm <= POSITION_TOL and rot_norm <= ROTATION_TOL:
            return True, q.copy(), {
                "position_error_m": pos_norm,
                "rotation_error_rad": rot_norm,
            }

        mujoco.mj_jacBody(
            model, data, jac_pos, jac_rot, tool_body_id
        )

        jp = jac_pos[:, dof_addresses]
        jr = jac_rot[:, dof_addresses]
        jacobian = np.vstack((jp, ROTATION_WEIGHT * jr))
        error = np.concatenate((
            pos_error,
            ROTATION_WEIGHT * rot_error,
        ))

        lhs = jacobian @ jacobian.T + DAMPING**2 * np.eye(6)

        try:
            dq = jacobian.T @ np.linalg.solve(lhs, error)
        except np.linalg.LinAlgError:
            break

        q += np.clip(dq, -MAX_DQ_PER_STEP, MAX_DQ_PER_STEP)
        q = clip_arm_to_joint_limits(model, q, joint_ids)

    set_arm_pose(data, qpos_addresses, q)
    mujoco.mj_forward(model, data)

    final_pos_error = float(
        np.linalg.norm(target_position - data.xpos[tool_body_id])
    )
    final_rot_error = float(np.linalg.norm(rotation_error(
        target_rotation,
        data.xmat[tool_body_id].reshape(3, 3).copy(),
    )))

    success = (
        final_pos_error <= POSITION_TOL
        and final_rot_error <= ROTATION_TOL
    )

    return success, q.copy(), {
        "position_error_m": final_pos_error,
        "rotation_error_rad": final_rot_error,
    }


def find_cube_geom(
    model: mujoco.MjModel,
    cube_body_id: int,
) -> int:
    attached = [
        g for g in range(int(model.ngeom))
        if int(model.geom_bodyid[g]) == int(cube_body_id)
    ]

    if not attached:
        raise RuntimeError("No geometry is attached to phase1_cube.")

    box_geoms = [
        g for g in attached
        if int(model.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX)
    ]
    return int(box_geoms[0] if box_geoms else attached[0])


def cube_geom_center_offset(
    model: mujoco.MjModel,
    cube_geom_id: int,
) -> np.ndarray:
    return model.geom_pos[cube_geom_id].copy()


def set_cube_geom_center(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    cube_body_id: int,
    cube_geom_id: int,
    cube_qpos_address: int,
    desired_geom_center: np.ndarray,
) -> None:
    """Move the cube's free body so its geometry centre reaches the target."""
    body_rotation = data.xmat[cube_body_id].reshape(3, 3).copy()
    geom_offset_world = (
        body_rotation @ cube_geom_center_offset(model, cube_geom_id)
    )

    data.qpos[cube_qpos_address:cube_qpos_address + 3] = (
        desired_geom_center - geom_offset_world
    )
    mujoco.mj_forward(model, data)


def get_cube_geom_center(
    data: mujoco.MjData,
    cube_geom_id: int,
) -> np.ndarray:
    return data.geom_xpos[cube_geom_id].copy()


def projected_box_half_extents(
    rotation: np.ndarray,
    half_sizes: np.ndarray,
) -> np.ndarray:
    return np.abs(rotation) @ half_sizes


def get_table_bounds_and_top(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    table_geom_id: int,
) -> tuple[float, float, float, float, float]:
    if int(model.geom_type[table_geom_id]) != int(mujoco.mjtGeom.mjGEOM_BOX):
        raise RuntimeError(
            f"Table geom {TABLE_GEOM_NAME!r} is not a box. "
            "This script expects a box table geometry."
        )

    mujoco.mj_forward(model, data)

    center = data.geom_xpos[table_geom_id].copy()
    rotation = data.geom_xmat[table_geom_id].reshape(3, 3).copy()
    half = model.geom_size[table_geom_id].copy()
    world_half = projected_box_half_extents(rotation, half)

    return (
        float(center[0] - world_half[0]),
        float(center[0] + world_half[0]),
        float(center[1] - world_half[1]),
        float(center[1] + world_half[1]),
        float(center[2] + world_half[2]),
    )


def cube_half_height(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    cube_geom_id: int,
) -> float:
    if int(model.geom_type[cube_geom_id]) == int(mujoco.mjtGeom.mjGEOM_BOX):
        rotation = data.geom_xmat[cube_geom_id].reshape(3, 3).copy()
        world_half = projected_box_half_extents(
            rotation, model.geom_size[cube_geom_id]
        )
        return float(world_half[2])

    return float(model.geom_size[cube_geom_id][2])


def get_robot_reference_xy(
    model: mujoco.MjModel,
    data: mujoco.MjData,
) -> np.ndarray:
    """Estimate the robot's reference point from its shoulder-pan bodies."""
    shoulder_positions = []

    for joint_name in (LEFT_ARM[0], RIGHT_ARM[0]):
        joint_id = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        body_id = int(model.jnt_bodyid[joint_id])
        shoulder_positions.append(data.xpos[body_id, :2].copy())

    return np.mean(np.asarray(shoulder_positions, dtype=float), axis=0)


def check_workspace(
    cube_center: np.ndarray,
    table_bounds: tuple[float, float, float, float, float],
    robot_reference_xy: np.ndarray,
) -> dict[str, Any]:
    """Reject cubes too far beyond the table centre, away from the robot."""
    xmin, xmax, ymin, ymax, _ = table_bounds
    table_center = np.array([
        (xmin + xmax) / 2.0,
        (ymin + ymax) / 2.0,
    ])

    toward_table = table_center - np.asarray(robot_reference_xy, dtype=float)
    norm = float(np.linalg.norm(toward_table))

    if norm < 1e-8:
        return {
            "allowed": False,
            "reason": "Could not determine robot-to-table direction.",
            "far_side_projection_m": None,
            "threshold_m": -MAX_FAR_SIDE_PAST_TABLE_CENTER,
            "table_center_xy_m": table_center.tolist(),
            "robot_reference_xy_m": robot_reference_xy.tolist(),
        }

    toward_table /= norm

    # Negative values are beyond the table centre on the far side.
    projection = float(np.dot(
        np.asarray(cube_center[:2]) - table_center,
        toward_table,
    ))

    allowed = projection >= -MAX_FAR_SIDE_PAST_TABLE_CENTER

    return {
        "allowed": bool(allowed),
        "reason": (
            "Target is within the approved workspace region."
            if allowed
            else "Target is too far beyond the table centre on the side away from the robot."
        ),
        "far_side_projection_m": projection,
        "threshold_m": -MAX_FAR_SIDE_PAST_TABLE_CENTER,
        "table_center_xy_m": table_center.tolist(),
        "robot_reference_xy_m": robot_reference_xy.tolist(),
    }


def sample_distinct_positions(
    rng: np.random.Generator,
    bounds: tuple[float, float, float, float, float],
    place_center: np.ndarray,
    count: int,
) -> list[np.ndarray]:
    xmin, xmax, ymin, ymax, _ = bounds

    xmin += TABLE_EDGE_MARGIN
    xmax -= TABLE_EDGE_MARGIN
    ymin += TABLE_EDGE_MARGIN
    ymax -= TABLE_EDGE_MARGIN

    if xmin >= xmax or ymin >= ymax:
        raise RuntimeError("Table is too small after applying TABLE_EDGE_MARGIN.")

    samples: list[np.ndarray] = []
    rounded_seen: set[tuple[float, float]] = set()
    attempts = 0
    max_attempts = max(5000, count * 1000)

    while len(samples) < count and attempts < max_attempts:
        attempts += 1
        x = float(rng.uniform(xmin, xmax))
        y = float(rng.uniform(ymin, ymax))

        if math.hypot(
            x - float(place_center[0]),
            y - float(place_center[1]),
        ) < PLACE_EXCLUSION_RADIUS:
            continue

        key = (round(x, 4), round(y, 4))
        if key in rounded_seen:
            continue

        rounded_seen.add(key)
        samples.append(np.array([x, y, 0.0], dtype=float))

    if len(samples) != count:
        raise RuntimeError(
            f"Could only sample {len(samples)} distinct positions "
            f"after {attempts} attempts."
        )

    return samples


def target_waypoints(
    cube_center: np.ndarray,
    place_center: np.ndarray,
    half_height: float,
) -> dict[str, np.ndarray]:
    pick_tool_z = float(
        cube_center[2] + half_height + GRASP_CLEARANCE
    )
    place_tool_z = float(
        place_center[2] + half_height + GRASP_CLEARANCE
    )

    return {
        "pick_approach": np.array([
            cube_center[0], cube_center[1],
            pick_tool_z + APPROACH_HEIGHT,
        ]),
        "pick_grasp": np.array([
            cube_center[0], cube_center[1], pick_tool_z,
        ]),
        "pick_lift": np.array([
            cube_center[0], cube_center[1],
            pick_tool_z + APPROACH_HEIGHT,
        ]),
        "place_approach": np.array([
            place_center[0], place_center[1],
            place_tool_z + APPROACH_HEIGHT,
        ]),
        "place": np.array([
            place_center[0], place_center[1], place_tool_z,
        ]),
        "place_retreat": np.array([
            place_center[0], place_center[1],
            place_tool_z + APPROACH_HEIGHT,
        ]),
    }


def evaluate_arm(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    arm_name: str,
    joint_names: list[str],
    tool_body_id: int,
    waypoints: dict[str, np.ndarray],
    initial_pose_by_name: dict[str, float],
) -> dict[str, Any]:
    qpos_addresses, dof_addresses, joint_ids = joint_info(
        model, joint_names
    )
    home_q = np.array(
        [initial_pose_by_name[n] for n in joint_names],
        dtype=float,
    )

    target_rotation = get_tool_rotation_for_arm(
        model, data, tool_body_id, qpos_addresses, home_q
    )

    solutions: dict[str, list[float]] = {}
    errors: dict[str, dict[str, float]] = {}
    all_pass = True
    seed = home_q.copy()
    joint_travel_cost_rad = 0.0

    for waypoint_name, target in waypoints.items():
        success, solution, error = solve_ik(
            model, data, tool_body_id,
            qpos_addresses, dof_addresses, joint_ids,
            seed, target, target_rotation,
        )

        errors[waypoint_name] = error
        solutions[waypoint_name] = solution.tolist()
        # Measure the joint-space motion needed to visit the waypoints in order.
        # A lower cost is a useful feasibility preference when both arms pass IK.
        joint_travel_cost_rad += float(np.linalg.norm(solution - seed))
        seed = solution

        if not success:
            all_pass = False

    return {
        "arm": arm_name,
        "reachable": bool(all_pass),
        "joint_travel_cost_rad": joint_travel_cost_rad,
        "waypoint_errors": errors,
        "solutions": solutions,
        "joint_names": joint_names,
        "qpos_addresses": qpos_addresses.tolist(),
        "dof_addresses": dof_addresses.tolist(),
        "joint_ids": joint_ids,
        "target_rotation": target_rotation.tolist(),
    }


def animate_segment(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    viewer: Any,
    tool_body_id: int,
    qpos_addresses: np.ndarray,
    start_q: np.ndarray,
    end_q: np.ndarray,
    cube_body_id: int,
    cube_geom_id: int,
    cube_qpos_address: int,
    carry_offset: np.ndarray | None = None,
    frames: int = ANIMATION_FRAMES,
    delay: float = FRAME_DELAY,
) -> np.ndarray:
    """Animate joint interpolation; optionally carry the cube kinematically."""
    for frame in range(1, frames + 1):
        alpha = frame / float(frames)
        q = (1.0 - alpha) * start_q + alpha * end_q

        set_arm_pose(data, qpos_addresses, q)
        mujoco.mj_forward(model, data)

        if carry_offset is not None:
            carried_center = data.xpos[tool_body_id].copy() + carry_offset
            set_cube_geom_center(
                model, data, cube_body_id, cube_geom_id,
                cube_qpos_address, carried_center,
            )

        if viewer is not None:
            if not viewer.is_running():
                raise KeyboardInterrupt("Viewer was closed by the user.")
            viewer.sync()
            time.sleep(delay)

    return end_q.copy()


def pause_on_rejected_pose(viewer: Any, seconds: float = REJECTION_PAUSE_SECONDS) -> None:
    """Keep a rejected cube pose visible in the passive MuJoCo viewer.

    Re-sync periodically during the pause so the viewer continues rendering.
    Headless runs do not pause.
    """
    if viewer is None or seconds <= 0:
        return

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not viewer.is_running():
            return
        viewer.sync()
        remaining = deadline - time.monotonic()
        time.sleep(min(0.02, max(0.0, remaining)))


def execute_trial(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    viewer: Any,
    cube_body_id: int,
    cube_geom_id: int,
    cube_qpos_address: int,
    cube_start_center: np.ndarray,
    place_center: np.ndarray,
    arm_result: dict[str, Any],
) -> dict[str, Any]:
    """Execute only an already-approved, IK-reachable arm plan."""
    joint_names = arm_result["joint_names"]
    qpos_addresses = np.asarray(arm_result["qpos_addresses"], dtype=int)

    tool_name = (
        LEFT_TOOL_BODY_NAME
        if arm_result["arm"] == "left"
        else RIGHT_TOOL_BODY_NAME
    )
    tool_body_id = name2id(model, mujoco.mjtObj.mjOBJ_BODY, tool_name)

    solutions = {
        key: np.asarray(value, dtype=float)
        for key, value in arm_result["solutions"].items()
    }
    home_q = np.asarray([POSE[name] for name in joint_names], dtype=float)

    set_arm_pose(data, qpos_addresses, home_q)
    set_cube_geom_center(
        model, data, cube_body_id, cube_geom_id,
        cube_qpos_address, cube_start_center,
    )
    mujoco.mj_forward(model, data)

    current_q = home_q.copy()
    carry_offset = None

    # Approach and descend; cube must not move during these stages.
    for waypoint in ("pick_approach", "pick_grasp"):
        current_q = animate_segment(
            model, data, viewer, tool_body_id, qpos_addresses,
            current_q, solutions[waypoint],
            cube_body_id, cube_geom_id, cube_qpos_address,
            carry_offset=None,
        )

    # Kinematic attachment surrogate, not physical grasp simulation.
    cube_center_now = get_cube_geom_center(data, cube_geom_id)
    carry_offset = cube_center_now - data.xpos[tool_body_id].copy()

    for waypoint in ("pick_lift", "place_approach", "place"):
        current_q = animate_segment(
            model, data, viewer, tool_body_id, qpos_addresses,
            current_q, solutions[waypoint],
            cube_body_id, cube_geom_id, cube_qpos_address,
            carry_offset=carry_offset,
        )

    released_center = get_cube_geom_center(data, cube_geom_id).copy()
    final_error = float(np.linalg.norm(released_center - place_center))

    animate_segment(
        model, data, viewer, tool_body_id, qpos_addresses,
        current_q, solutions["place_retreat"],
        cube_body_id, cube_geom_id, cube_qpos_address,
        carry_offset=None,
    )

    return {
        "executed": True,
        "execution_mode": EXECUTION_MODE,
        "final_cube_center_m": released_center.tolist(),
        "place_target_center_m": place_center.tolist(),
        "final_place_error_m": final_error,
        "placement_within_2cm": bool(final_error <= 0.02),
        "arm": arm_result["arm"],
    }


def write_json_atomic(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(content, indent=2), encoding="utf-8")
    tmp.replace(path)


def flatten_trial_for_csv(trial: dict[str, Any]) -> dict[str, Any]:
    cube_position = trial.get("cube_position_m") or [None, None, None]
    execution = trial.get("execution") or {}
    recovery = trial.get("recovery") or {}
    workspace = trial.get("workspace") or {}
    arms = trial.get("arms") or {}
    left_arm = arms.get("left") or {}
    right_arm = arms.get("right") or {}

    return {
        "trial": trial.get("trial"),
        "cube_x_m": cube_position[0],
        "cube_y_m": cube_position[1],
        "cube_z_m": cube_position[2],
        "reachable": trial.get("reachable"),
        "ik_reachable": trial.get("ik_reachable"),
        "workspace_allowed": workspace.get("allowed"),
        "workspace_rejected": trial.get("workspace_rejected"),
        "workspace_reason": workspace.get("reason"),
        "selected_arm": trial.get("selected_arm"),
        "executed": execution.get("executed", False),
        "placement_within_2cm": execution.get("placement_within_2cm"),
        "final_place_error_m": execution.get("final_place_error_m"),
        "recovery_strategy": recovery.get("strategy"),
        "recovery_reason": recovery.get("reason"),
        "left_reachable": left_arm.get("reachable"),
        "right_reachable": right_arm.get("reachable"),
        "left_joint_travel_cost_rad": left_arm.get("joint_travel_cost_rad"),
        "right_joint_travel_cost_rad": right_arm.get("joint_travel_cost_rad"),
        "status": trial.get("status"),
    }


def write_csv(path: Path, trials: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [flatten_trial_for_csv(t) for t in trials]

    fields = [
        "trial",
        "cube_x_m",
        "cube_y_m",
        "cube_z_m",
        "reachable",
        "ik_reachable",
        "workspace_allowed",
        "workspace_rejected",
        "workspace_reason",
        "selected_arm",
        "executed",
        "placement_within_2cm",
        "final_place_error_m",
        "recovery_strategy",
        "recovery_reason",
        "left_reachable",
        "right_reachable",
        "left_joint_travel_cost_rad",
        "right_joint_travel_cost_rad",
        "status",
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trials", type=int, default=N_TRIALS,
        help="Number of distinct random cube positions.",
    )
    parser.add_argument(
        "--seed", type=int, default=RANDOM_SEED,
        help="Random seed for reproducible positions.",
    )
    parser.add_argument(
        "--no-viewer", action="store_true",
        help="Run headlessly without opening the MuJoCo viewer.",
    )
    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be at least 1")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"MuJoCo model not found: {MODEL_PATH}")

    if not args.no_viewer and not mujoco_viewer_available:
        raise RuntimeError(
            "mujoco.viewer is unavailable; pass --no-viewer for headless execution."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "randomized_pick_place_audit.json"
    csv_path = OUTPUT_DIR / "randomized_pick_place_audit.csv"

    print(f"MuJoCo model: {MODEL_PATH}")
    print(f"Output folder: {OUTPUT_DIR}")

    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)

    # Initialize both arms to the exact specified pose.
    for name, value in POSE.items():
        jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        data.qpos[int(model.jnt_qposadr[jid])] = float(value)

    mujoco.mj_forward(model, data)

    cube_body_id = name2id(model, mujoco.mjtObj.mjOBJ_BODY, CUBE_BODY_NAME)
    table_geom_id = name2id(model, mujoco.mjtObj.mjOBJ_GEOM, TABLE_GEOM_NAME)
    cube_geom_id = find_cube_geom(model, cube_body_id)
    _, cube_qpos_address = get_free_joint(model, cube_body_id)

    # Validate that both tool bodies exist.
    name2id(model, mujoco.mjtObj.mjOBJ_BODY, LEFT_TOOL_BODY_NAME)
    name2id(model, mujoco.mjtObj.mjOBJ_BODY, RIGHT_TOOL_BODY_NAME)

    table_bounds = get_table_bounds_and_top(model, data, table_geom_id)
    table_top = table_bounds[4]
    robot_reference_xy = get_robot_reference_xy(model, data)
    half_height = cube_half_height(model, data, cube_geom_id)

    place_center = np.array(
        [0.590, 0.000, table_top + half_height],
        dtype=float,
    )
    # Preserve the historical placement height when it matches this model.
    if abs(0.897 - place_center[2]) < 0.03:
        place_center[2] = 0.897

    print(f"Place target: {np.round(place_center, 4)}")

    rng = np.random.default_rng(args.seed)
    sampled_xy = sample_distinct_positions(
        rng, table_bounds, place_center, args.trials
    )
    initial_cube_quat = data.qpos[
        cube_qpos_address + 3:cube_qpos_address + 7
    ].copy()

    results: dict[str, Any] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_path": str(MODEL_PATH),
        "random_seed": args.seed,
        "requested_trials": args.trials,
        "place_target_center_m": place_center.tolist(),
        "table_bounds_xy_m": {
            "xmin": table_bounds[0],
            "xmax": table_bounds[1],
            "ymin": table_bounds[2],
            "ymax": table_bounds[3],
            "table_top_z": table_top,
        },
        "execution_mode": EXECUTION_MODE,
        "workspace_policy": {
            "type": "far_side_table_filter",
            "max_far_side_past_table_center_m": MAX_FAR_SIDE_PAST_TABLE_CENTER,
            "robot_reference_xy_m": robot_reference_xy.tolist(),
            "note": (
                "Conservative geometric filter; it does not certify "
                "collision-free motion."
            ),
        },
        "limitations": [
            "IK reachability does not certify collision-free paths.",
            "Workspace-rejected targets are never passed to execute_trial.",
            "Cube carrying is a kinematic surrogate, not physical gripper dynamics.",
            "Recovery is recommended but the script does not automatically reposition the cube.",
        ],
        "trials": [],
    }

    viewer_context = None
    viewer = None

    if not args.no_viewer:
        viewer_context = mujoco.viewer.launch_passive(model, data)
        viewer = viewer_context

    try:
        print(f"Starting {args.trials} randomized trials.")

        for trial_index, xyz in enumerate(sampled_xy, start=1):
            cube_center = np.array(
                [xyz[0], xyz[1], table_top + half_height],
                dtype=float,
            )

            set_cube_geom_center(
                model, data, cube_body_id, cube_geom_id,
                cube_qpos_address, cube_center,
            )
            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat
            mujoco.mj_forward(model, data)
            cube_center = get_cube_geom_center(data, cube_geom_id).copy()

            print(
                f"\n[{trial_index:02d}/{args.trials:02d}] "
                f"Cube position: {np.round(cube_center, 4)}"
            )

            # Reset both arms before independent IK checks.
            for name, value in POSE.items():
                jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                data.qpos[int(model.jnt_qposadr[jid])] = float(value)
            mujoco.mj_forward(model, data)

            waypoints = target_waypoints(
                cube_center, place_center, half_height
            )

            left_result = evaluate_arm(
                model,
                data,
                "left",
                LEFT_ARM,
                name2id(model, mujoco.mjtObj.mjOBJ_BODY, LEFT_TOOL_BODY_NAME),
                waypoints,
                POSE,
            )

            # Restore the initial state before checking the other arm.
            for name, value in POSE.items():
                jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                data.qpos[int(model.jnt_qposadr[jid])] = float(value)
            mujoco.mj_forward(model, data)

            right_result = evaluate_arm(
                model,
                data,
                "right",
                RIGHT_ARM,
                name2id(model, mujoco.mjtObj.mjOBJ_BODY, RIGHT_TOOL_BODY_NAME),
                waypoints,
                POSE,
            )

            # Restore the independent trial state after IK probing.
            for name, value in POSE.items():
                jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                data.qpos[int(model.jnt_qposadr[jid])] = float(value)

            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat
            set_cube_geom_center(
                model, data, cube_body_id, cube_geom_id,
                cube_qpos_address, cube_center,
            )
            mujoco.mj_forward(model, data)

            # Workspace approval is independent of IK reachability.
            workspace = check_workspace(
                cube_center, table_bounds, robot_reference_xy
            )
            ik_reachable_arms = [
                arm for arm in (left_result, right_result)
                if arm["reachable"]
            ]
            # Rank only arms that passed every pick/lift/place IK waypoint.
            # Prefer the arm requiring less total joint-space motion; this makes
            # selection depend on target-specific feasibility, not left/right order.
            ranked_reachable_arms = sorted(
                ik_reachable_arms,
                key=lambda arm: arm["joint_travel_cost_rad"],
            )

            # CRITICAL EXECUTION GATE:
            # Workspace approval and complete IK feasibility are both required.
            selected_arm = None
            if workspace["allowed"] and ranked_reachable_arms:
                selected_arm = ranked_reachable_arms[0]

            trial: dict[str, Any] = {
                "trial": trial_index,
                "cube_position_m": cube_center.tolist(),
                "place_target_center_m": place_center.tolist(),
                "workspace": workspace,
                "workspace_rejected": not bool(workspace["allowed"]),
                "ik_reachable": bool(ik_reachable_arms),
                "reachable": bool(
                    workspace["allowed"] and selected_arm is not None
                ),
                "selected_arm": (
                    selected_arm["arm"] if selected_arm else None
                ),
                "arms": {
                    "left": {
                        k: v for k, v in left_result.items()
                        if k != "joint_ids"
                    },
                    "right": {
                        k: v for k, v in right_result.items()
                        if k != "joint_ids"
                    },
                },
                "execution": {"executed": False},
                "recovery": None,
                "status": "pending",
            }

            if not workspace["allowed"]:
                # No execution call, no arm animation, no cube attachment.
                # Leave the cube at this sampled target and arms at the initial pose.
                for name, value in POSE.items():
                    jid = name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                    data.qpos[int(model.jnt_qposadr[jid])] = float(value)

                set_cube_geom_center(
                    model, data, cube_body_id, cube_geom_id,
                    cube_qpos_address, cube_center,
                )
                data.qpos[
                    cube_qpos_address + 3:cube_qpos_address + 7
                ] = initial_cube_quat
                mujoco.mj_forward(model, data)

                if viewer is not None and viewer.is_running():
                    viewer.sync()

                print(
                    "  WORKSPACE REJECTED — pick-and-place skipped. "
                    + workspace["reason"]
                )
                print(
                    f"  Holding rejected cube pose for "
                    f"{REJECTION_PAUSE_SECONDS:.0f} seconds so it is visible..."
                )
                pause_on_rejected_pose(viewer)

                trial["status"] = "workspace_rejected_recovery_recommended"
                trial["recovery"] = {
                    "strategy": RECOVERY_STRATEGY,
                    "reason": workspace["reason"],
                    "action": (
                        "Do not execute. Reposition or resample the cube "
                        "within the approved workspace and validate again."
                    ),
                    "automatic_reposition_performed": False,
                }

            elif selected_arm is None:
                # Workspace is allowed, but neither arm passed every IK waypoint.
                print(
                    "  IK UNREACHABLE — pick-and-place skipped; "
                    "neither arm passed every waypoint."
                )
                print(
                    f"  Holding rejected cube pose for "
                    f"{REJECTION_PAUSE_SECONDS:.0f} seconds so it is visible..."
                )
                pause_on_rejected_pose(viewer)

                trial["status"] = "unreachable_recovery_recommended"
                trial["recovery"] = {
                    "strategy": RECOVERY_STRATEGY,
                    "reason": (
                        "No arm passed IK at every pick, lift, and place waypoint."
                    ),
                    "action": (
                        "Choose a new cube position and rerun reachability "
                        "checks before executing."
                    ),
                    "automatic_reposition_performed": False,
                }

            else:
                # Only approved, IK-reachable trials reach this branch.
                print(
                    f"  Workspace PASS; IK PASS. Selected {selected_arm['arm']} arm "
                    f"(joint-travel cost: "
                    f"{selected_arm['joint_travel_cost_rad']:.3f} rad; "
                    f"left: {left_result['joint_travel_cost_rad']:.3f} rad, "
                    f"right: {right_result['joint_travel_cost_rad']:.3f} rad)."
                )
                try:
                    execution = execute_trial(
                        model,
                        data,
                        viewer,
                        cube_body_id,
                        cube_geom_id,
                        cube_qpos_address,
                        cube_center,
                        place_center,
                        selected_arm,
                    )
                    trial["execution"] = execution
                    trial["status"] = (
                        "executed_success"
                        if execution["placement_within_2cm"]
                        else "executed_placement_error"
                    )
                    print(
                        "  Execution completed; final placement error = "
                        f"{execution['final_place_error_m']:.4f} m"
                    )

                except KeyboardInterrupt:
                    trial["execution"] = {
                        "executed": False,
                        "error": "viewer_closed",
                    }
                    trial["status"] = "interrupted"
                    results["trials"].append(trial)
                    write_json_atomic(json_path, results)
                    write_csv(csv_path, results["trials"])
                    print("Viewer closed; stopping and saving audit.")
                    break

                except Exception as exc:
                    trial["execution"] = {
                        "executed": False,
                        "error": repr(exc),
                        "traceback": traceback.format_exc(),
                    }
                    trial["status"] = "execution_error"
                    print(f"  Execution error: {exc}")

            # All trials are recorded, including rejected and unexecuted trials.
            results["trials"].append(trial)
            write_json_atomic(json_path, results)
            write_csv(csv_path, results["trials"])

            if viewer is not None and viewer.is_running():
                viewer.sync()

    finally:
        if viewer_context is not None:
            try:
                viewer_context.close()
            except Exception:
                pass

    trials = results["trials"]
    completed = len(trials)

    results["summary"] = {
        "completed_trials": completed,

        # Workspace-approved AND IK-reachable.
        "reachable_trials": sum(
            bool(t.get("reachable")) for t in trials
        ),

        # IK diagnostic, even when a target was rejected by the workspace gate.
        "ik_reachable_trials": sum(
            bool(t.get("ik_reachable")) for t in trials
        ),

        "executed_trials": sum(
            bool((t.get("execution") or {}).get("executed"))
            for t in trials
        ),

        # Workspace-approved trials where no arm passed all IK waypoints.
        "unreachable_trials": sum(
            bool((t.get("workspace") or {}).get("allowed"))
            and not bool(t.get("ik_reachable"))
            for t in trials
        ),

        "workspace_rejected_trials": sum(
            bool(t.get("workspace_rejected")) for t in trials
        ),

        "placement_successes": sum(
            bool((t.get("execution") or {}).get("placement_within_2cm"))
            for t in trials
        ),
    }

    write_json_atomic(json_path, results)
    write_csv(csv_path, trials)

    print("\nAudit complete:")
    print(json.dumps(results["summary"], indent=2))
    print(f"JSON audit: {json_path}")
    print(f"CSV audit:  {csv_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {exc}")
        raise