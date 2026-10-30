
#!/usr/bin/env python3
"""
Randomized camera-guided Tracy pick-and-place audit for MuJoCo.

Pipeline:
    Random cube position
    -> RGB-D camera observation
    -> MuJoCo segmentation
    -> 3D cube-center estimation
    -> Workspace validation
    -> Left/right arm IK validation
    -> Select best feasible arm
    -> Kinematic pick-and-place execution
    -> JSON and CSV audit

IMPORTANT:
- Perception uses MuJoCo oracle segmentation, not a neural-network detector.
- Ground-truth cube coordinates are used only for evaluation and
  kinematic execution bookkeeping, NOT for calculating the IK pick target.
- Cube carrying is a kinematic attachment surrogate, not physical grasping.
- IK reachability does not certify collision-free motion.
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
from PIL import Image

try:
    import mujoco.viewer
except ImportError:
    mujoco_viewer_available = False
else:
    mujoco_viewer_available = True


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    ROOT / "tracy_ws" / "tracy_mjcf"
    / "tracy_collision_phase1.xml"
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

OBSERVATION_DIR = OUTPUT_DIR / "camera_observations"


# ============================================================
# MUJOCO OBJECT NAMES
# ============================================================

CUBE_BODY_NAME = "phase1_cube"
LEFT_TOOL_BODY_NAME = "l_gripper_tool_frame"
RIGHT_TOOL_BODY_NAME = "r_gripper_tool_frame"

CAMERA_NAME = "tracy_rgbd_camera"
CUBE_GEOM_NAME = "phase1_cube_geom"

TABLE_GEOM_NAME = "table_collision_0"


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540

MIN_CUBE_PIXELS = 100


# ============================================================
# ROBOT CONFIGURATION
# ============================================================

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


# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

N_TRIALS = 10
RANDOM_SEED = 40

TABLE_EDGE_MARGIN = 0.04
PLACE_EXCLUSION_RADIUS = 0.09

MAX_FAR_SIDE_PAST_TABLE_CENTER = 0.08

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


# ============================================================
# GENERAL MUJOCO UTILITIES
# ============================================================

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

        jid = name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )

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

    for joint_id in range(model.njnt):

        if int(model.jnt_bodyid[joint_id]) != int(body_id):
            continue

        if int(model.jnt_type[joint_id]) == int(
            mujoco.mjtJoint.mjJNT_FREE
        ):
            return (
                joint_id,
                int(model.jnt_qposadr[joint_id]),
            )

    raise RuntimeError("No free joint found for cube body.")


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


# ============================================================
# ROTATION UTILITIES
# ============================================================

def rotation_error(
    target: np.ndarray,
    current: np.ndarray,
) -> np.ndarray:

    relative = target @ current.T

    cosine = float(np.clip(
        (np.trace(relative) - 1.0) / 2.0,
        -1.0,
        1.0,
    ))

    angle = math.acos(cosine)

    if angle < 1e-8:
        return np.zeros(3)

    if math.pi - angle < 1e-5:

        vals, vecs = np.linalg.eig(relative)

        axis = np.real(
            vecs[:, int(np.argmin(np.abs(vals - 1.0)))]
        )

        axis /= max(float(np.linalg.norm(axis)), 1e-12)

        return angle * axis

    return (angle / (2.0 * math.sin(angle)) * np.array([
        relative[2, 1] - relative[1, 2],
        relative[0, 2] - relative[2, 0],
        relative[1, 0] - relative[0, 1],
    ]))


# ============================================================
# CUBE AND TABLE GEOMETRY
# ============================================================

def find_cube_geom(
    model: mujoco.MjModel,
    cube_body_id: int,
) -> int:

    attached = [
        g for g in range(model.ngeom)
        if int(model.geom_bodyid[g]) == int(cube_body_id)
    ]

    if not attached:
        raise RuntimeError("No geometry attached to cube body.")

    box_geoms = [
        g for g in attached
        if int(model.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX)
    ]

    return int(box_geoms[0] if box_geoms else attached[0])


def projected_box_half_extents(
    rotation: np.ndarray,
    half_sizes: np.ndarray,
) -> np.ndarray:

    return np.abs(rotation) @ half_sizes


def cube_half_height(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    cube_geom_id: int,
) -> float:

    if int(model.geom_type[cube_geom_id]) == int(
        mujoco.mjtGeom.mjGEOM_BOX
    ):

        rotation = data.geom_xmat[cube_geom_id].reshape(3, 3).copy()

        world_half = projected_box_half_extents(
            rotation,
            model.geom_size[cube_geom_id],
        )

        return float(world_half[2])

    return float(model.geom_size[cube_geom_id][2])


def get_cube_geom_center(
    data: mujoco.MjData,
    cube_geom_id: int,
) -> np.ndarray:

    return data.geom_xpos[cube_geom_id].copy()


def set_cube_geom_center(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    cube_body_id: int,
    cube_geom_id: int,
    cube_qpos_address: int,
    desired_geom_center: np.ndarray,
) -> None:

    body_rotation = (
        data.xmat[cube_body_id].reshape(3, 3).copy()
    )

    geom_offset_world = (
        body_rotation @ model.geom_pos[cube_geom_id]
    )

    data.qpos[
        cube_qpos_address:cube_qpos_address + 3
    ] = desired_geom_center - geom_offset_world

    mujoco.mj_forward(model, data)


def get_table_bounds_and_top(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    table_geom_id: int,
) -> tuple[float, float, float, float, float]:

    if int(model.geom_type[table_geom_id]) != int(
        mujoco.mjtGeom.mjGEOM_BOX
    ):
        raise RuntimeError("Table geometry must be a box.")

    mujoco.mj_forward(model, data)

    center = data.geom_xpos[table_geom_id].copy()

    rotation = (
        data.geom_xmat[table_geom_id].reshape(3, 3).copy()
    )

    half = model.geom_size[table_geom_id].copy()

    world_half = projected_box_half_extents(rotation, half)

    return (
        float(center[0] - world_half[0]),
        float(center[0] + world_half[0]),
        float(center[1] - world_half[1]),
        float(center[1] + world_half[1]),
        float(center[2] + world_half[2]),
    )


# ============================================================
# CAMERA PERCEPTION
# ============================================================

def perceive_cube_center(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    camera_id: int,
    cube_geom_id: int,
    half_height: float,
    trial_index: int,
) -> dict[str, Any]:
    """
    Estimate cube center from camera RGB-D and segmentation.

    The estimator uses:
      - MuJoCo segmentation to obtain cube pixels.
      - Metric depth to reconstruct camera-space points.
      - Camera extrinsics to transform points into world coordinates.
      - World-coordinate bounds to estimate an axis-aligned cube center.

    Assumption:
      The cube is axis-aligned and its top face is visible.
    """

    print("\n  CAMERA PERCEPTION")

    renderer = mujoco.Renderer(
        model,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
    )

    try:

        # RGB image.
        renderer.update_scene(data, camera=CAMERA_NAME)
        rgb = renderer.render().copy()

        # Segmentation image.
        renderer.enable_segmentation_rendering()
        renderer.update_scene(data, camera=CAMERA_NAME)
        segmentation = renderer.render().copy()
        renderer.disable_segmentation_rendering()

        # Metric depth image.
        renderer.enable_depth_rendering()
        renderer.update_scene(data, camera=CAMERA_NAME)
        depth = renderer.render().copy()
        renderer.disable_depth_rendering()

    finally:
        renderer.close()

    if segmentation.ndim != 3 or segmentation.shape[2] < 2:
        raise RuntimeError(
            f"Unexpected segmentation shape: {segmentation.shape}"
        )

    # MuJoCo segmentation stores object ID and object type.
    mask = (
        (segmentation[:, :, 0] == cube_geom_id)
        &
        (
            segmentation[:, :, 1]
            == int(mujoco.mjtObj.mjOBJ_GEOM)
        )
    )

    valid = (
        mask
        & np.isfinite(depth)
        & (depth > 0)
    )

    ys, xs = np.where(valid)

    pixel_count = int(len(xs))

    print(f"  Cube pixels detected: {pixel_count}")

    if pixel_count < MIN_CUBE_PIXELS:
        raise RuntimeError(
            f"Too few cube pixels detected: {pixel_count}"
        )

    height, width = depth.shape

    # Reject detections clipped by the image boundary.
    if (
        xs.min() == 0
        or ys.min() == 0
        or xs.max() == width - 1
        or ys.max() == height - 1
    ):
        raise RuntimeError(
            "Cube detection touches image boundary; "
            "the object may be partially outside the camera view."
        )

    # Camera intrinsic parameters.
    fovy = np.deg2rad(float(model.cam_fovy[camera_id]))

    fy = height / (2.0 * np.tan(fovy / 2.0))
    fx = fy

    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0

    z = depth[valid].astype(np.float64)

    # MuJoCo camera convention:
    # +X right, +Y up, camera looks along -Z.
    points_camera = np.column_stack((
        (xs - cx) * z / fx,
        -(ys - cy) * z / fy,
        -z,
    ))

    # Camera extrinsics.
    camera_position = data.cam_xpos[camera_id].copy()

    camera_rotation = (
        data.cam_xmat[camera_id].reshape(3, 3).copy()
    )

    points_world = (
        camera_position
        + points_camera @ camera_rotation.T
    )

    # Estimate axis-aligned cube center from visible surface points.
    surface_min = points_world.min(axis=0)
    surface_max = points_world.max(axis=0)

    estimated_center = np.array([
        (surface_min[0] + surface_max[0]) / 2.0,
        (surface_min[1] + surface_max[1]) / 2.0,
        surface_max[2] - half_height,
    ])

    if not np.all(np.isfinite(estimated_center)):
        raise RuntimeError("Perception returned invalid coordinates.")

    # Save observation files.
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%S_%fZ")

    observation_path = (
        OBSERVATION_DIR
        / f"trial_{trial_index:03d}_{timestamp}"
    )

    observation_path.mkdir(parents=True, exist_ok=True)

    Image.fromarray(rgb).save(
        observation_path / "rgb.png"
    )

    Image.fromarray(
        (mask * 255).astype(np.uint8)
    ).save(
        observation_path / "cube_mask.png"
    )

    np.save(
        observation_path / "depth.npy",
        depth,
    )

    np.savez_compressed(
        observation_path / "cube_pointcloud.npz",
        points_camera=points_camera,
        points_world=points_world,
        surface_minimum_world=surface_min,
        surface_maximum_world=surface_max,
        estimated_center_world=estimated_center,
    )

    metadata = {
        "trial": trial_index,
        "timestamp_utc": timestamp,
        "camera": CAMERA_NAME,
        "image_width": width,
        "image_height": height,
        "cube_pixels": pixel_count,
        "depth_unit": "metres",
        "segmentation_source": "MuJoCo oracle segmentation",
        "estimation_method": "RGB-D point-cloud reconstruction",
        "axis_aligned_cube_assumption": True,
        "estimated_cube_center_world_m": estimated_center.tolist(),
        "surface_minimum_world_m": surface_min.tolist(),
        "surface_maximum_world_m": surface_max.tolist(),
    }

    with open(
        observation_path / "metadata.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(metadata, file, indent=4)

    print("  Perceived cube center:", np.round(estimated_center, 5))
    print("  Observation saved:", observation_path)

    return {
        "success": True,
        "estimated_center_m": estimated_center.tolist(),
        "cube_pixels": pixel_count,
        "observation_path": str(observation_path),
        "method": "MuJoCo RGB-D + oracle segmentation",
        "error": None,
    }


# ============================================================
# ROBOT REFERENCE AND WORKSPACE VALIDATION
# ============================================================

def get_robot_reference_xy(
    model: mujoco.MjModel,
    data: mujoco.MjData,
) -> np.ndarray:

    shoulder_positions = []

    for joint_name in (LEFT_ARM[0], RIGHT_ARM[0]):

        joint_id = name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            joint_name,
        )

        body_id = int(model.jnt_bodyid[joint_id])

        shoulder_positions.append(
            data.xpos[body_id, :2].copy()
        )

    return np.mean(
        np.asarray(shoulder_positions, dtype=float),
        axis=0,
    )


def check_workspace(
    cube_center: np.ndarray,
    table_bounds: tuple[float, float, float, float, float],
    robot_reference_xy: np.ndarray,
) -> dict[str, Any]:

    xmin, xmax, ymin, ymax, _ = table_bounds

    table_center = np.array([
        (xmin + xmax) / 2.0,
        (ymin + ymax) / 2.0,
    ])

    toward_table = table_center - robot_reference_xy
    norm = float(np.linalg.norm(toward_table))

    if norm < 1e-8:

        return {
            "allowed": False,
            "reason": "Could not determine robot-to-table direction.",
            "far_side_projection_m": None,
        }

    toward_table /= norm

    projection = float(np.dot(
        cube_center[:2] - table_center,
        toward_table,
    ))

    allowed = (
        projection >= -MAX_FAR_SIDE_PAST_TABLE_CENTER
    )

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


# ============================================================
# RANDOM POSITION GENERATION
# ============================================================

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
        raise RuntimeError(
            "Table is too small after applying edge margin."
        )

    samples = []
    rounded_seen = set()

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

        samples.append(
            np.array([x, y, 0.0], dtype=float)
        )

    if len(samples) != count:
        raise RuntimeError(
            f"Could only sample {len(samples)} distinct positions."
        )

    return samples


# ============================================================
# TARGET WAYPOINTS
# ============================================================

def target_waypoints(
    perceived_cube_center: np.ndarray,
    place_center: np.ndarray,
    half_height: float,
) -> dict[str, np.ndarray]:

    pick_tool_z = (
        float(perceived_cube_center[2])
        + half_height
        + GRASP_CLEARANCE
    )

    place_tool_z = (
        float(place_center[2])
        + half_height
        + GRASP_CLEARANCE
    )

    return {
        "pick_approach": np.array([
            perceived_cube_center[0],
            perceived_cube_center[1],
            pick_tool_z + APPROACH_HEIGHT,
        ]),

        "pick_grasp": np.array([
            perceived_cube_center[0],
            perceived_cube_center[1],
            pick_tool_z,
        ]),

        "pick_lift": np.array([
            perceived_cube_center[0],
            perceived_cube_center[1],
            pick_tool_z + APPROACH_HEIGHT,
        ]),

        "place_approach": np.array([
            place_center[0],
            place_center[1],
            place_tool_z + APPROACH_HEIGHT,
        ]),

        "place": np.array([
            place_center[0],
            place_center[1],
            place_tool_z,
        ]),

        "place_retreat": np.array([
            place_center[0],
            place_center[1],
            place_tool_z + APPROACH_HEIGHT,
        ]),
    }


# ============================================================
# INVERSE KINEMATICS
# ============================================================

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

    q = seed_q.copy()

    jac_pos = np.zeros((3, model.nv))
    jac_rot = np.zeros((3, model.nv))

    for _ in range(MAX_IK_STEPS):

        set_arm_pose(data, qpos_addresses, q)
        mujoco.mj_forward(model, data)

        current_position = data.xpos[tool_body_id].copy()

        current_rotation = (
            data.xmat[tool_body_id].reshape(3, 3).copy()
        )

        pos_error = target_position - current_position

        rot_error = rotation_error(
            target_rotation,
            current_rotation,
        )

        pos_norm = float(np.linalg.norm(pos_error))
        rot_norm = float(np.linalg.norm(rot_error))

        if (
            pos_norm <= POSITION_TOL
            and rot_norm <= ROTATION_TOL
        ):

            return True, q.copy(), {
                "position_error_m": pos_norm,
                "rotation_error_rad": rot_norm,
            }

        mujoco.mj_jacBody(
            model,
            data,
            jac_pos,
            jac_rot,
            tool_body_id,
        )

        jp = jac_pos[:, dof_addresses]
        jr = jac_rot[:, dof_addresses]

        jacobian = np.vstack((
            jp,
            ROTATION_WEIGHT * jr,
        ))

        error = np.concatenate((
            pos_error,
            ROTATION_WEIGHT * rot_error,
        ))

        lhs = (
            jacobian @ jacobian.T
            + DAMPING**2 * np.eye(6)
        )

        try:

            dq = jacobian.T @ np.linalg.solve(
                lhs,
                error,
            )

        except np.linalg.LinAlgError:
            break

        q += np.clip(
            dq,
            -MAX_DQ_PER_STEP,
            MAX_DQ_PER_STEP,
        )

        q = clip_arm_to_joint_limits(
            model,
            q,
            joint_ids,
        )

    set_arm_pose(data, qpos_addresses, q)
    mujoco.mj_forward(model, data)

    final_pos_error = float(
        np.linalg.norm(
            target_position - data.xpos[tool_body_id]
        )
    )

    final_rot_error = float(
        np.linalg.norm(
            rotation_error(
                target_rotation,
                data.xmat[tool_body_id].reshape(3, 3).copy(),
            )
        )
    )

    success = (
        final_pos_error <= POSITION_TOL
        and final_rot_error <= ROTATION_TOL
    )

    return success, q.copy(), {
        "position_error_m": final_pos_error,
        "rotation_error_rad": final_rot_error,
    }


# ============================================================
# ARM EVALUATION
# ============================================================

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
        model,
        joint_names,
    )

    home_q = np.array(
        [initial_pose_by_name[n] for n in joint_names],
        dtype=float,
    )

    target_rotation = get_tool_rotation_for_arm(
        model,
        data,
        tool_body_id,
        qpos_addresses,
        home_q,
    )

    solutions = {}
    errors = {}

    all_pass = True
    seed = home_q.copy()
    joint_travel_cost = 0.0

    for waypoint_name, target in waypoints.items():

        success, solution, error = solve_ik(
            model,
            data,
            tool_body_id,
            qpos_addresses,
            dof_addresses,
            joint_ids,
            seed,
            target,
            target_rotation,
        )

        errors[waypoint_name] = error
        solutions[waypoint_name] = solution.tolist()

        joint_travel_cost += float(
            np.linalg.norm(solution - seed)
        )

        seed = solution

        if not success:
            all_pass = False

    return {
        "arm": arm_name,
        "reachable": bool(all_pass),
        "joint_travel_cost_rad": joint_travel_cost,
        "waypoint_errors": errors,
        "solutions": solutions,
        "joint_names": joint_names,
        "qpos_addresses": qpos_addresses.tolist(),
        "dof_addresses": dof_addresses.tolist(),
        "joint_ids": joint_ids,
        "target_rotation": target_rotation.tolist(),
    }


# ============================================================
# ANIMATION AND EXECUTION
# ============================================================

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

    for frame in range(1, frames + 1):

        alpha = frame / float(frames)

        q = (
            (1.0 - alpha) * start_q
            + alpha * end_q
        )

        set_arm_pose(data, qpos_addresses, q)
        mujoco.mj_forward(model, data)

        if carry_offset is not None:

            carried_center = (
                data.xpos[tool_body_id].copy()
                + carry_offset
            )

            set_cube_geom_center(
                model,
                data,
                cube_body_id,
                cube_geom_id,
                cube_qpos_address,
                carried_center,
            )

        if viewer is not None:

            if not viewer.is_running():
                raise KeyboardInterrupt("Viewer closed.")

            viewer.sync()
            time.sleep(delay)

    return end_q.copy()


def pause_on_rejected_pose(
    viewer: Any,
    seconds: float = REJECTION_PAUSE_SECONDS,
) -> None:

    if viewer is None or seconds <= 0:
        return

    deadline = time.monotonic() + seconds

    while time.monotonic() < deadline:

        if not viewer.is_running():
            return

        viewer.sync()

        time.sleep(0.02)


def execute_trial(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    viewer: Any,
    cube_body_id: int,
    cube_geom_id: int,
    cube_qpos_address: int,
    actual_cube_center: np.ndarray,
    place_center: np.ndarray,
    arm_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a plan whose IK targets were calculated from perception.

    actual_cube_center is used only to initialize the simulated cube
    and evaluate the kinematic attachment. It is not used to generate
    the pick waypoints or IK solutions.
    """

    joint_names = arm_result["joint_names"]

    qpos_addresses = np.asarray(
        arm_result["qpos_addresses"],
        dtype=int,
    )

    tool_name = (
        LEFT_TOOL_BODY_NAME
        if arm_result["arm"] == "left"
        else RIGHT_TOOL_BODY_NAME
    )

    tool_body_id = name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        tool_name,
    )

    solutions = {
        key: np.asarray(value, dtype=float)
        for key, value in arm_result["solutions"].items()
    }

    home_q = np.asarray(
        [POSE[name] for name in joint_names],
        dtype=float,
    )

    set_arm_pose(data, qpos_addresses, home_q)

    set_cube_geom_center(
        model,
        data,
        cube_body_id,
        cube_geom_id,
        cube_qpos_address,
        actual_cube_center,
    )

    mujoco.mj_forward(model, data)

    current_q = home_q.copy()
    carry_offset = None

    # Approach and descend.
    for waypoint in ("pick_approach", "pick_grasp"):

        current_q = animate_segment(
            model,
            data,
            viewer,
            tool_body_id,
            qpos_addresses,
            current_q,
            solutions[waypoint],
            cube_body_id,
            cube_geom_id,
            cube_qpos_address,
            carry_offset=None,
        )

    # Kinematic attachment surrogate.
    cube_center_now = get_cube_geom_center(
        data,
        cube_geom_id,
    )

    carry_offset = (
        cube_center_now - data.xpos[tool_body_id].copy()
    )

    for waypoint in (
        "pick_lift",
        "place_approach",
        "place",
    ):

        current_q = animate_segment(
            model,
            data,
            viewer,
            tool_body_id,
            qpos_addresses,
            current_q,
            solutions[waypoint],
            cube_body_id,
            cube_geom_id,
            cube_qpos_address,
            carry_offset=carry_offset,
        )

    released_center = get_cube_geom_center(
        data,
        cube_geom_id,
    ).copy()

    final_error = float(
        np.linalg.norm(released_center - place_center)
    )

    # Retreat after release.
    animate_segment(
        model,
        data,
        viewer,
        tool_body_id,
        qpos_addresses,
        current_q,
        solutions["place_retreat"],
        cube_body_id,
        cube_geom_id,
        cube_qpos_address,
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


# ============================================================
# OUTPUT UTILITIES
# ============================================================

def write_json_atomic(
    path: Path,
    content: dict[str, Any],
) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")

    tmp.write_text(
        json.dumps(content, indent=2),
        encoding="utf-8",
    )

    tmp.replace(path)


def flatten_trial_for_csv(
    trial: dict[str, Any],
) -> dict[str, Any]:

    actual = trial.get("cube_position_m") or [None, None, None]

    perceived = (
        trial.get("perceived_cube_position_m")
        or [None, None, None]
    )

    perception = trial.get("perception") or {}
    workspace = trial.get("workspace") or {}
    execution = trial.get("execution") or {}
    recovery = trial.get("recovery") or {}
    arms = trial.get("arms") or {}

    left = arms.get("left") or {}
    right = arms.get("right") or {}

    return {
        "trial": trial.get("trial"),

        "actual_x_m": actual[0],
        "actual_y_m": actual[1],
        "actual_z_m": actual[2],

        "perceived_x_m": perceived[0],
        "perceived_y_m": perceived[1],
        "perceived_z_m": perceived[2],

        "perception_success": perception.get("success"),
        "perception_pixels": perception.get("cube_pixels"),
        "perception_error_m": trial.get("perception_error_m"),

        "workspace_allowed": workspace.get("allowed"),
        "workspace_rejected": trial.get("workspace_rejected"),

        "ik_reachable": trial.get("ik_reachable"),
        "reachable": trial.get("reachable"),

        "selected_arm": trial.get("selected_arm"),
        "executed": execution.get("executed", False),

        "placement_within_2cm": execution.get(
            "placement_within_2cm"
        ),

        "final_place_error_m": execution.get(
            "final_place_error_m"
        ),

        "recovery_strategy": recovery.get("strategy"),
        "recovery_reason": recovery.get("reason"),

        "left_reachable": left.get("reachable"),
        "right_reachable": right.get("reachable"),

        "left_joint_travel_cost_rad": left.get(
            "joint_travel_cost_rad"
        ),

        "right_joint_travel_cost_rad": right.get(
            "joint_travel_cost_rad"
        ),

        "status": trial.get("status"),
    }


def write_csv(
    path: Path,
    trials: list[dict[str, Any]],
) -> None:

    rows = [
        flatten_trial_for_csv(t)
        for t in trials
    ]

    fields = list(rows[0].keys()) if rows else [
        "trial",
        "status",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--trials",
        type=int,
        default=N_TRIALS,
        help="Number of random cube positions.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed.",
    )

    parser.add_argument(
        "--no-viewer",
        action="store_true",
        help="Run without the MuJoCo viewer.",
    )

    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be at least 1")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"MuJoCo model not found: {MODEL_PATH}"
        )

    if not args.no_viewer and not mujoco_viewer_available:
        raise RuntimeError(
            "MuJoCo viewer unavailable. Use --no-viewer."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OBSERVATION_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "randomized_pick_place_perception_audit.json"
    csv_path = OUTPUT_DIR / "randomized_pick_place_perception_audit.csv"

    print("MuJoCo model:", MODEL_PATH)
    print("Output directory:", OUTPUT_DIR)
    print("Observation directory:", OBSERVATION_DIR)

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)

    # Validate camera.
    camera_id = name2id(
        model,
        mujoco.mjtObj.mjOBJ_CAMERA,
        CAMERA_NAME,
    )

    # Validate camera image dimensions.
    if CAMERA_WIDTH <= 0 or CAMERA_HEIGHT <= 0:
        raise RuntimeError("Invalid camera image dimensions.")

    # Initialize both arms.
    for name, value in POSE.items():

        jid = name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )

        data.qpos[int(model.jnt_qposadr[jid])] = float(value)

    mujoco.mj_forward(model, data)

    cube_body_id = name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        CUBE_BODY_NAME,
    )

    table_geom_id = name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        TABLE_GEOM_NAME,
    )

    cube_geom_id = find_cube_geom(
        model,
        cube_body_id,
    )

    # The named geometry is expected to be the cube geometry.
    named_cube_geom_id = name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        CUBE_GEOM_NAME,
    )

    if named_cube_geom_id != cube_geom_id:
        print(
            "WARNING: named cube geom differs from selected box geom."
        )

    _, cube_qpos_address = get_free_joint(
        model,
        cube_body_id,
    )

    name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        LEFT_TOOL_BODY_NAME,
    )

    name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        RIGHT_TOOL_BODY_NAME,
    )

    # --------------------------------------------------------
    # Table and cube geometry
    # --------------------------------------------------------

    table_bounds = get_table_bounds_and_top(
        model,
        data,
        table_geom_id,
    )

    table_top = table_bounds[4]

    robot_reference_xy = get_robot_reference_xy(
        model,
        data,
    )

    half_height = cube_half_height(
        model,
        data,
        cube_geom_id,
    )

    # Preserve the previous experiment's placement convention.
    place_center = np.array(
        [0.590, 0.000, table_top + half_height],
        dtype=float,
    )

    if abs(0.897 - place_center[2]) < 0.03:
        place_center[2] = 0.897

    print("\nPlace target:", np.round(place_center, 4))
    print("Cube half-height:", half_height)

    # --------------------------------------------------------
    # Randomized positions
    # --------------------------------------------------------

    rng = np.random.default_rng(args.seed)

    sampled_positions = sample_distinct_positions(
        rng,
        table_bounds,
        place_center,
        args.trials,
    )

    initial_cube_quat = data.qpos[
        cube_qpos_address + 3:cube_qpos_address + 7
    ].copy()

    # --------------------------------------------------------
    # Audit result structure
    # --------------------------------------------------------

    results: dict[str, Any] = {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "model_path": str(MODEL_PATH),

        "random_seed": args.seed,
        "requested_trials": args.trials,

        "camera_name": CAMERA_NAME,

        "perception": {
            "method": "MuJoCo RGB-D + oracle segmentation",
            "uses_ground_truth_for_pick_target": False,
            "cube_assumption": "axis-aligned box with visible top face",
            "depth_unit": "metres",
        },

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
            "max_far_side_past_table_center_m": (
                MAX_FAR_SIDE_PAST_TABLE_CENTER
            ),
            "robot_reference_xy_m": robot_reference_xy.tolist(),
        },

        "limitations": [
            "Segmentation is provided by MuJoCo, not an independent detector.",
            "The estimator assumes an axis-aligned cube and visible top face.",
            "Perception failure prevents IK planning and execution.",
            "Workspace checks do not certify collision-free motion.",
            "IK reachability does not certify collision-free trajectories.",
            "Cube carrying is a kinematic surrogate, not physical grasp dynamics.",
            "Recovery recommendations are recorded but do not automatically reposition the cube.",
            "Ground-truth coordinates are recorded for evaluation only.",
        ],

        "trials": [],
    }

    # --------------------------------------------------------
    # Optional viewer
    # --------------------------------------------------------

    viewer_context = None
    viewer = None

    if not args.no_viewer:

        viewer_context = mujoco.viewer.launch_passive(
            model,
            data,
        )

        viewer = viewer_context

    # --------------------------------------------------------
    # Run randomized trials
    # --------------------------------------------------------

    try:

        print(f"\nStarting {args.trials} randomized trials.")

        for trial_index, xy in enumerate(
            sampled_positions,
            start=1,
        ):

            print("\n" + "=" * 60)
            print(f"TRIAL {trial_index}/{args.trials}")
            print("=" * 60)

            # ------------------------------------------------
            # A. Set random cube position
            # ------------------------------------------------

            actual_cube_center = np.array([
                xy[0],
                xy[1],
                table_top + half_height,
            ])

            # Restore initial cube orientation.
            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat

            set_cube_geom_center(
                model,
                data,
                cube_body_id,
                cube_geom_id,
                cube_qpos_address,
                actual_cube_center,
            )

            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat

            mujoco.mj_forward(model, data)

            # Read actual geometry center for evaluation only.
            actual_cube_center = get_cube_geom_center(
                data,
                cube_geom_id,
            ).copy()

            print(
                "Ground-truth cube center (evaluation only):",
                np.round(actual_cube_center, 5),
            )

            # Reset both arms to initial pose before camera capture.
            for name, value in POSE.items():

                jid = name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_JOINT,
                    name,
                )

                data.qpos[
                    int(model.jnt_qposadr[jid])
                ] = float(value)

            mujoco.mj_forward(model, data)

            # ------------------------------------------------
            # B. Camera perception
            # ------------------------------------------------

            perception = {
                "success": False,
                "estimated_center_m": None,
                "cube_pixels": 0,
                "observation_path": None,
                "method": "MuJoCo RGB-D + oracle segmentation",
                "error": None,
            }

            try:

                perception = perceive_cube_center(
                    model,
                    data,
                    camera_id,
                    cube_geom_id,
                    half_height,
                    trial_index,
                )

            except Exception as exc:

                perception["success"] = False
                perception["error"] = repr(exc)

                print("  PERCEPTION FAILED:", exc)

            # Initialize trial record.
            trial: dict[str, Any] = {
                "trial": trial_index,

                "cube_position_m": actual_cube_center.tolist(),

                "perceived_cube_position_m": (
                    perception.get("estimated_center_m")
                ),

                "perception": perception,

                "perception_error_m": None,

                "place_target_center_m": place_center.tolist(),

                "workspace": None,
                "workspace_rejected": False,

                "ik_reachable": False,
                "reachable": False,

                "selected_arm": None,

                "arms": {},

                "execution": {
                    "executed": False,
                },

                "recovery": None,

                "status": "pending",
            }

            # ------------------------------------------------
            # C. Fail closed if perception failed
            # ------------------------------------------------

            if not perception["success"]:

                print(
                    "  PERCEPTION REJECTED — "
                    "no IK planning or execution."
                )

                trial["status"] = "perception_failed"

                trial["recovery"] = {
                    "strategy": "REACQUIRE_PERCEPTION",

                    "reason": perception.get("error"),

                    "action": (
                        "Capture a new camera observation, verify "
                        "the cube is visible, and estimate its position again."
                    ),

                    "automatic_reposition_performed": False,
                }

                if viewer is not None and viewer.is_running():
                    viewer.sync()

                results["trials"].append(trial)

                write_json_atomic(json_path, results)
                write_csv(csv_path, results["trials"])

                continue

            # ------------------------------------------------
            # D. Use perceived coordinates for planning
            # ------------------------------------------------

            perceived_center = np.asarray(
                perception["estimated_center_m"],
                dtype=float,
            )

            # Ground-truth comparison is evaluation only.
            perception_error = float(
                np.linalg.norm(
                    perceived_center - actual_cube_center
                )
            )

            trial["perception_error_m"] = perception_error

            print(
                "  Perceived cube center:",
                np.round(perceived_center, 5),
            )

            print(
                f"  Perception position error (evaluation): "
                f"{perception_error:.5f} m"
            )

            # ------------------------------------------------
            # E. Build waypoints from perceived center
            # ------------------------------------------------

            waypoints = target_waypoints(
                perceived_center,
                place_center,
                half_height,
            )

            # ------------------------------------------------
            # F. Workspace check uses perceived position
            # ------------------------------------------------

            workspace = check_workspace(
                perceived_center,
                table_bounds,
                robot_reference_xy,
            )

            trial["workspace"] = workspace

            trial["workspace_rejected"] = (
                not bool(workspace["allowed"])
            )

            # ------------------------------------------------
            # G. Evaluate left arm IK
            # ------------------------------------------------

            for name, value in POSE.items():

                jid = name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_JOINT,
                    name,
                )

                data.qpos[
                    int(model.jnt_qposadr[jid])
                ] = float(value)

            mujoco.mj_forward(model, data)

            left_result = evaluate_arm(
                model,
                data,
                "left",
                LEFT_ARM,
                name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_BODY,
                    LEFT_TOOL_BODY_NAME,
                ),
                waypoints,
                POSE,
            )

            # ------------------------------------------------
            # H. Reset before evaluating right arm
            # ------------------------------------------------

            for name, value in POSE.items():

                jid = name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_JOINT,
                    name,
                )

                data.qpos[
                    int(model.jnt_qposadr[jid])
                ] = float(value)

            mujoco.mj_forward(model, data)

            right_result = evaluate_arm(
                model,
                data,
                "right",
                RIGHT_ARM,
                name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_BODY,
                    RIGHT_TOOL_BODY_NAME,
                ),
                waypoints,
                POSE,
            )

            # ------------------------------------------------
            # I. Restore trial state after IK probing
            # ------------------------------------------------

            for name, value in POSE.items():

                jid = name2id(
                    model,
                    mujoco.mjtObj.mjOBJ_JOINT,
                    name,
                )

                data.qpos[
                    int(model.jnt_qposadr[jid])
                ] = float(value)

            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat

            set_cube_geom_center(
                model,
                data,
                cube_body_id,
                cube_geom_id,
                cube_qpos_address,
                actual_cube_center,
            )

            data.qpos[
                cube_qpos_address + 3:cube_qpos_address + 7
            ] = initial_cube_quat

            mujoco.mj_forward(model, data)

            # ------------------------------------------------
            # J. Select feasible arm
            # ------------------------------------------------

            ik_reachable_arms = [
                arm
                for arm in (left_result, right_result)
                if arm["reachable"]
            ]

            ranked_arms = sorted(
                ik_reachable_arms,
                key=lambda arm: arm["joint_travel_cost_rad"],
            )

            selected_arm = None

            # Both workspace and IK gates must pass.
            if workspace["allowed"] and ranked_arms:
                selected_arm = ranked_arms[0]

            trial["ik_reachable"] = bool(ik_reachable_arms)

            trial["reachable"] = bool(
                workspace["allowed"]
                and selected_arm is not None
            )

            trial["selected_arm"] = (
                selected_arm["arm"]
                if selected_arm is not None
                else None
            )

            trial["arms"] = {
                "left": {
                    k: v
                    for k, v in left_result.items()
                    if k != "joint_ids"
                },

                "right": {
                    k: v
                    for k, v in right_result.items()
                    if k != "joint_ids"
                },
            }

            # ------------------------------------------------
            # K. Workspace rejection
            # ------------------------------------------------

            if not workspace["allowed"]:

                print(
                    "  WORKSPACE REJECTED — execution skipped."
                )

                print(" ", workspace["reason"])

                trial["status"] = (
                    "workspace_rejected_recovery_recommended"
                )

                trial["recovery"] = {
                    "strategy": RECOVERY_STRATEGY,

                    "reason": workspace["reason"],

                    "action": (
                        "Do not execute. Reposition or resample "
                        "the cube within the approved workspace "
                        "and validate again."
                    ),

                    "automatic_reposition_performed": False,
                }

                pause_on_rejected_pose(viewer)

            # ------------------------------------------------
            # L. IK rejection
            # ------------------------------------------------

            elif selected_arm is None:

                print(
                    "  IK UNREACHABLE — neither arm passed "
                    "every waypoint. Execution skipped."
                )

                trial["status"] = (
                    "unreachable_recovery_recommended"
                )

                trial["recovery"] = {
                    "strategy": RECOVERY_STRATEGY,

                    "reason": (
                        "No arm passed IK at every pick, lift, "
                        "and place waypoint."
                    ),

                    "action": (
                        "Choose a new cube position and rerun "
                        "perception, workspace, and IK validation."
                    ),

                    "automatic_reposition_performed": False,
                }

                pause_on_rejected_pose(viewer)

            # ------------------------------------------------
            # M. Execute approved trial
            # ------------------------------------------------

            else:

                print(
                    f"  Workspace PASS; IK PASS. "
                    f"Selected {selected_arm['arm']} arm."
                )

                print(
                    "  Joint travel cost:",
                    round(
                        selected_arm["joint_travel_cost_rad"],
                        4,
                    ),
                    "rad",
                )

                print(
                    "  Executing using perceived pick coordinates."
                )

                try:

                    execution = execute_trial(
                        model,
                        data,
                        viewer,
                        cube_body_id,
                        cube_geom_id,
                        cube_qpos_address,
                        actual_cube_center,
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
                        "  Final placement error:",
                        f"{execution['final_place_error_m']:.5f} m",
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

                    print("Viewer closed; audit saved.")
                    break

                except Exception as exc:

                    trial["execution"] = {
                        "executed": False,
                        "error": repr(exc),
                        "traceback": traceback.format_exc(),
                    }

                    trial["status"] = "execution_error"

                    print("  Execution error:", exc)

            # ------------------------------------------------
            # N. Save this trial
            # ------------------------------------------------

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

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    trials = results["trials"]

    completed = len(trials)

    perception_successes = sum(
        bool((t.get("perception") or {}).get("success"))
        for t in trials
    )

    perception_failures = sum(
        not bool((t.get("perception") or {}).get("success"))
        for t in trials
    )

    perception_errors = [
        float(t["perception_error_m"])
        for t in trials
        if t.get("perception_error_m") is not None
    ]

    results["summary"] = {
        "completed_trials": completed,

        "perception_successes": perception_successes,
        "perception_failures": perception_failures,

        "mean_perception_error_m": (
            float(np.mean(perception_errors))
            if perception_errors
            else None
        ),

        "max_perception_error_m": (
            float(np.max(perception_errors))
            if perception_errors
            else None
        ),

        "workspace_and_ik_reachable_trials": sum(
            bool(t.get("reachable"))
            for t in trials
        ),

        "ik_reachable_trials": sum(
            bool(t.get("ik_reachable"))
            for t in trials
        ),

        "executed_trials": sum(
            bool((t.get("execution") or {}).get("executed"))
            for t in trials
        ),

        "workspace_rejected_trials": sum(
            bool(t.get("workspace_rejected"))
            for t in trials
        ),

        "perception_failed_trials": perception_failures,

        "unreachable_trials": sum(
            bool((t.get("workspace") or {}).get("allowed"))
            and not bool(t.get("ik_reachable"))
            for t in trials
        ),

        "placement_successes": sum(
            bool(
                (t.get("execution") or {}).get(
                    "placement_within_2cm"
                )
            )
            for t in trials
        ),
    }

    write_json_atomic(json_path, results)
    write_csv(csv_path, trials)

    print("\n" + "=" * 60)
    print("PERCEPTION-GUIDED RANDOMIZED AUDIT COMPLETE")
    print("=" * 60)

    print(json.dumps(results["summary"], indent=2))

    print("\nJSON audit:", json_path)
    print("CSV audit: ", csv_path)
    print("Camera observations:", OBSERVATION_DIR)

    return 0


if __name__ == "__main__":

    try:
        raise SystemExit(main())

    except Exception as exc:

        print(f"FATAL: {exc}")
        raise
