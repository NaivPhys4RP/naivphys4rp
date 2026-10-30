
#!/usr/bin/env python3
"""
Camera-guided Tracy robot pick-and-place.

1. Initialize Tracy robot.
2. Capture RGB-D camera observation.
3. Segment cube using MuJoCo segmentation.
4. Reconstruct cube position in world coordinates.
5. Calculate pick target from perceived coordinates.
6. Solve inverse kinematics.
7. Execute pick, lift, transfer, place and return home.

NOTE:
- Uses MuJoCo oracle segmentation.
- Assumes an axis-aligned 8 cm cube.
- Uses kinematic attachment, not physical grasp dynamics.
"""

from pathlib import Path
from datetime import datetime, timezone
import json
import time

import numpy as np
import mujoco
import mujoco.viewer
from PIL import Image


# ============================================================
# 1. PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

MODEL = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

OUTPUT_ROOT = (
    ROOT
    / "experiments/tracy_pick_place_phase1/scripts/output"
    / "live_observations"
)

CAMERA_NAME = "tracy_rgbd_camera"
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540

TOOL_NAME = "l_gripper_tool_frame"
CUBE_NAME = "phase1_cube"
CUBE_GEOM_NAME = "phase1_cube_geom"

CUBE_SIZE = 0.08
CUBE_HALF_SIZE = CUBE_SIZE / 2.0

# Gripper target is 4 cm above cube center,
# plus 5 mm clearance.
GRIPPER_OFFSET = np.array([0.0, 0.0, 0.045])

# Fixed placement target.
PLACE = np.array([0.550, 0.150, 0.920])

APPROACH_HEIGHT = 0.15

FRAMES = 70
FRAME_DELAY = 0.015

DAMPING = 0.03
MAX_IK_STEPS = 300

POSITION_TOL = 0.008
ROTATION_TOL = 0.04
ROTATION_WEIGHT = 0.25

MAX_FINAL_POSITION_ERROR = 0.015
MAX_FINAL_ROTATION_ERROR = 0.10

MIN_CUBE_PIXELS = 100


# ============================================================
# 2. ROBOT CONFIGURATION
# ============================================================

ARM = [
    "left_shoulder_pan_joint",
    "left_shoulder_lift_joint",
    "left_elbow_joint",
    "left_wrist_1_joint",
    "left_wrist_2_joint",
    "left_wrist_3_joint",
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
# 3. ROTATION UTILITIES
# ============================================================

def rotation_error(target, current):

    R = target @ current.T

    c = np.clip(
        (np.trace(R) - 1.0) / 2.0,
        -1.0,
        1.0,
    )

    angle = np.arccos(c)

    if angle < 1e-8:
        return np.zeros(3)

    if np.pi - angle < 1e-5:

        vals, vecs = np.linalg.eig(R)

        axis = np.real(
            vecs[:, np.argmin(np.abs(vals - 1.0))]
        )

        axis /= max(np.linalg.norm(axis), 1e-12)

        return angle * axis

    return angle / (2.0 * np.sin(angle)) * np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1],
    ])


def align_vector_rotation(source, target):

    a = source / np.linalg.norm(source)
    b = target / np.linalg.norm(target)

    v = np.cross(a, b)

    c = np.clip(np.dot(a, b), -1.0, 1.0)
    s = np.linalg.norm(v)

    if s < 1e-9:

        if c > 0:
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

    return (
        np.eye(3)
        + K
        + K @ K * ((1.0 - c) / (s * s))
    )


# ============================================================
# 4. CAMERA-BASED PERCEPTION
# ============================================================

def perceive_cube_center(model, data):

    print("\n====================================")
    print("        CAMERA PERCEPTION")
    print("====================================")

    camera_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_CAMERA,
        CAMERA_NAME,
    )

    geom_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        CUBE_GEOM_NAME,
    )

    if camera_id < 0:
        raise RuntimeError("Camera not found")

    if geom_id < 0:
        raise RuntimeError("Cube geometry not found")

    renderer = mujoco.Renderer(
        model,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
    )

    try:

        # Capture RGB.
        renderer.update_scene(data, camera=CAMERA_NAME)
        rgb = renderer.render().copy()

        # Capture segmentation.
        renderer.enable_segmentation_rendering()

        renderer.update_scene(data, camera=CAMERA_NAME)
        segmentation = renderer.render().copy()

        renderer.disable_segmentation_rendering()

        # Capture metric depth.
        renderer.enable_depth_rendering()

        renderer.update_scene(data, camera=CAMERA_NAME)
        depth = renderer.render().copy()

        renderer.disable_depth_rendering()

    finally:
        renderer.close()

    # Identify cube pixels.
    mask = (
        (segmentation[:, :, 0] == geom_id)
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

    pixel_count = len(xs)

    print("Detected cube pixels:", pixel_count)

    if pixel_count < MIN_CUBE_PIXELS:
        raise RuntimeError("Insufficient cube pixels detected")

    if (
        xs.min() == 0
        or ys.min() == 0
        or xs.max() == CAMERA_WIDTH - 1
        or ys.max() == CAMERA_HEIGHT - 1
    ):
        raise RuntimeError("Cube is clipped by camera image boundary")

    # Camera intrinsics.
    height, width = depth.shape

    fovy = np.deg2rad(
        float(model.cam_fovy[camera_id])
    )

    fy = height / (2.0 * np.tan(fovy / 2.0))
    fx = fy

    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0

    z = depth[valid].astype(np.float64)

    # Back-project pixels into camera coordinates.
    points_camera = np.column_stack((
        (xs - cx) * z / fx,
        -(ys - cy) * z / fy,
        -z,
    ))

    # Transform camera points into world coordinates.
    camera_position = data.cam_xpos[camera_id].copy()

    camera_rotation = (
        data.cam_xmat[camera_id]
        .reshape(3, 3)
        .copy()
    )

    points_world = (
        camera_position
        + points_camera @ camera_rotation.T
    )

    # Estimate axis-aligned cube center.
    minimum = points_world.min(axis=0)
    maximum = points_world.max(axis=0)

    estimated_center = np.array([
        (minimum[0] + maximum[0]) / 2.0,
        (minimum[1] + maximum[1]) / 2.0,
        maximum[2] - CUBE_HALF_SIZE,
    ])

    if not np.all(np.isfinite(estimated_center)):
        raise RuntimeError("Invalid perception coordinates")

    # Save observation.
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%S_%fZ")

    output = OUTPUT_ROOT / timestamp
    output.mkdir(parents=True, exist_ok=True)

    Image.fromarray(rgb).save(output / "rgb.png")

    Image.fromarray(
        (mask * 255).astype(np.uint8)
    ).save(output / "cube_mask.png")

    np.save(output / "depth.npy", depth)

    np.savez(
        output / "cube_pointcloud.npz",
        points_camera=points_camera,
        points_world=points_world,
        surface_minimum=minimum,
        surface_maximum=maximum,
        estimated_center=estimated_center,
    )

    metadata = {
        "timestamp_utc": timestamp,
        "camera": CAMERA_NAME,
        "image_width": width,
        "image_height": height,
        "cube_pixels": pixel_count,
        "depth_unit": "metres",
        "estimated_cube_center_world": estimated_center.tolist(),
        "surface_minimum_world": minimum.tolist(),
        "surface_maximum_world": maximum.tolist(),
        "method": "MuJoCo segmentation and RGB-D reconstruction",
    }

    with open(output / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("\nEstimated cube center:")
    print(estimated_center)

    print("\nObservation saved:")
    print(output)

    return estimated_center


# ============================================================
# 5. MAIN PROGRAM
# ============================================================

def main():

    if not MODEL.exists():
        raise FileNotFoundError(MODEL)

    print("\n====================================")
    print(" CAMERA-GUIDED TRACY PICK AND PLACE")
    print("====================================")

    model = mujoco.MjModel.from_xml_path(str(MODEL))
    data = mujoco.MjData(model)

    # Joint indexing.
    def joint_id(name):

        idx = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )

        if idx < 0:
            raise RuntimeError(f"Joint not found: {name}")

        return idx

    qadr = np.array([
        model.jnt_qposadr[joint_id(name)]
        for name in ARM
    ])

    dadr = np.array([
        model.jnt_dofadr[joint_id(name)]
        for name in ARM
    ])

    # Initialize robot.
    for name, value in POSE.items():

        jid = joint_id(name)

        data.qpos[
            model.jnt_qposadr[jid]
        ] = value

    home_q = data.qpos[qadr].copy()

    # Find tool and cube.
    tool = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        TOOL_NAME,
    )

    cube = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        CUBE_NAME,
    )

    if tool < 0 or cube < 0:
        raise RuntimeError("Tool or cube body not found")

    # Find cube free joint.
    free_joint = next(
        (
            j for j in range(model.njnt)
            if model.jnt_bodyid[j] == cube
            and model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE
        ),
        None,
    )

    if free_joint is None:
        raise RuntimeError("Cube free joint not found")

    cube_qadr = model.jnt_qposadr[free_joint]

    # Update the simulation before camera capture.
    mujoco.mj_forward(model, data)

    cube_start = data.qpos[
        cube_qadr:cube_qadr + 3
    ].copy()

    cube_rotation = data.qpos[
        cube_qadr + 3:cube_qadr + 7
    ].copy()

    # --------------------------------------------------------
    # CAMERA PERCEPTION
    # --------------------------------------------------------

    perceived_cube_center = perceive_cube_center(
        model,
        data,
    )

    # Calculate pick coordinates dynamically.
    pick_position = (
        perceived_cube_center + GRIPPER_OFFSET
    )

    print("\n====================================")
    print("           PICK TARGET")
    print("====================================")

    print("Perceived cube center:", perceived_cube_center)
    print("Calculated pick target:", pick_position)
    print("Place target:", PLACE)

    # --------------------------------------------------------
    # TOOL ORIENTATION
    # --------------------------------------------------------

    initial_rotation = (
        data.xmat[tool]
        .reshape(3, 3)
        .copy()
    )

    initial_axis = (
        initial_rotation @ np.array([0.0, 0.0, 1.0])
    )

    top_down_rotation = (
        align_vector_rotation(
            initial_axis,
            np.array([0.0, 0.0, -1.0]),
        )
        @ initial_rotation
    )

    jac_pos = np.zeros((3, model.nv))
    jac_rot = np.zeros((3, model.nv))

    # --------------------------------------------------------
    # INVERSE KINEMATICS
    # --------------------------------------------------------

    def solve_ik(target_position):

        for _ in range(MAX_IK_STEPS):

            mujoco.mj_forward(model, data)

            pos_error = (
                target_position - data.xpos[tool]
            )

            current_rotation = (
                data.xmat[tool].reshape(3, 3)
            )

            rot_error = rotation_error(
                top_down_rotation,
                current_rotation,
            )

            if (
                np.linalg.norm(pos_error) < POSITION_TOL
                and np.linalg.norm(rot_error) < ROTATION_TOL
            ):
                return True

            mujoco.mj_jacBody(
                model,
                data,
                jac_pos,
                jac_rot,
                tool,
            )

            Jp = jac_pos[:, dadr]
            Jr = jac_rot[:, dadr]

            J = np.vstack((
                Jp,
                ROTATION_WEIGHT * Jr,
            ))

            error = np.concatenate((
                pos_error,
                ROTATION_WEIGHT * rot_error,
            ))

            dq = J.T @ np.linalg.solve(
                J @ J.T + DAMPING**2 * np.eye(6),
                error,
            )

            data.qpos[qadr] += np.clip(
                dq,
                -0.035,
                0.035,
            )

            # Respect joint limits.
            for k, name in enumerate(ARM):

                jid = joint_id(name)

                if model.jnt_limited[jid]:

                    lo, hi = model.jnt_range[jid]

                    data.qpos[qadr[k]] = np.clip(
                        data.qpos[qadr[k]],
                        lo,
                        hi,
                    )

        mujoco.mj_forward(model, data)

        pos_residual = np.linalg.norm(
            target_position - data.xpos[tool]
        )

        rot_residual = np.linalg.norm(
            rotation_error(
                top_down_rotation,
                data.xmat[tool].reshape(3, 3),
            )
        )

        print(
            "IK residual:",
            f"{pos_residual:.4f} m,",
            f"{rot_residual:.4f} rad",
        )

        return (
            pos_residual <= MAX_FINAL_POSITION_ERROR
            and rot_residual <= MAX_FINAL_ROTATION_ERROR
        )

    # --------------------------------------------------------
    # VIEWER AND ANIMATION
    # --------------------------------------------------------

    with mujoco.viewer.launch_passive(
        model,
        data,
    ) as viewer:

        def animate_joint_target(target_q, carrying=False):

            start_q = data.qpos[qadr].copy()
            target_q = target_q.copy()

            for i in range(FRAMES):

                t = (i + 1) / FRAMES
                smooth = t * t * (3.0 - 2.0 * t)

                data.qpos[qadr] = (
                    start_q
                    + smooth * (target_q - start_q)
                )

                mujoco.mj_forward(model, data)

                if carrying:

                    # Kinematic cube attachment.
                    data.qpos[
                        cube_qadr:cube_qadr + 3
                    ] = (
                        cube_start
                        + data.xpos[tool]
                        - pick_position
                    )

                    data.qpos[
                        cube_qadr + 3:cube_qadr + 7
                    ] = cube_rotation

                    mujoco.mj_forward(model, data)

                viewer.sync()
                time.sleep(FRAME_DELAY)

        def move(target_position, carrying=False):

            start_q = data.qpos[qadr].copy()

            reached = solve_ik(target_position)

            goal_q = data.qpos[qadr].copy()

            # Restore start configuration.
            data.qpos[qadr] = start_q

            mujoco.mj_forward(model, data)

            if not reached:
                raise RuntimeError(
                    "IK failed. Pick-and-place aborted."
                )

            animate_joint_target(
                goal_q,
                carrying=carrying,
            )

        # ----------------------------------------------------
        # PICK AND PLACE
        # ----------------------------------------------------

        def pick_and_place():

            print("\n1/7: Approach cube from above")

            move(
                pick_position
                + np.array([0.0, 0.0, APPROACH_HEIGHT])
            )

            print("\n2/7: Descend to cube")

            move(pick_position)

            print("\n3/7: Lift cube")

            move(
                pick_position
                + np.array([0.0, 0.0, APPROACH_HEIGHT]),
                carrying=True,
            )

            print("\n4/7: Transfer above placement location")

            move(
                PLACE
                + np.array([0.0, 0.0, APPROACH_HEIGHT]),
                carrying=True,
            )

            print("\n5/7: Descend and place cube")

            move(
                PLACE,
                carrying=True,
            )

            # Release kinematic attachment.
            data.qpos[
                cube_qadr:cube_qadr + 3
            ] = (
                cube_start
                + PLACE
                - pick_position
            )

            data.qpos[
                cube_qadr + 3:cube_qadr + 7
            ] = cube_rotation

            mujoco.mj_forward(model, data)

            viewer.sync()

            print(
                "Cube placed at:",
                data.xpos[cube],
            )

            print("\n6/7: Retreat vertically")

            move(
                PLACE
                + np.array([0.0, 0.0, APPROACH_HEIGHT])
            )

            print("\n7/7: Return left arm home")

            animate_joint_target(home_q)

            print("\n====================================")
            print("       PICK AND PLACE COMPLETE")
            print("====================================")

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        viewer.sync()

        print("\nPerception completed.")
        print("Starting pick-and-place...")

        time.sleep(1.0)

        pick_and_place()

        print("\nViewer remains open. Close it to exit.")

        while viewer.is_running():

            viewer.sync()
            time.sleep(0.03)


if __name__ == "__main__":
    main()
