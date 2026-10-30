
#!/usr/bin/env python3
"""Tracy arm top-down cube pick-and-place with return to home pose."""

from pathlib import Path
import time
import numpy as np
import mujoco
import mujoco.viewer


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "tracy_ws/tracy_mjcf/tracy_collision_phase1.xml"

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

TOOL_NAME = "l_gripper_tool_frame"
CUBE_NAME = "phase1_cube"

# Cartesian targets for the tool frame (metres).
PICK = np.array([0.590, 0.000, 0.920])
PLACE = np.array([0.550, 0.150, 0.920])
APPROACH_HEIGHT = 0.15

FRAMES = 70
FRAME_DELAY = 0.015
DAMPING = 0.03
MAX_IK_STEPS = 300
POSITION_TOL = 0.008
ROTATION_TOL = 0.04
ROTATION_WEIGHT = 0.25


def rotation_error(target, current):
    """Return the world-frame axis-angle orientation error."""
    R = target @ current.T
    c = np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0)
    angle = np.arccos(c)

    if angle < 1e-8:
        return np.zeros(3)

    if np.pi - angle < 1e-5:
        vals, vecs = np.linalg.eig(R)
        axis = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
        axis /= max(np.linalg.norm(axis), 1e-12)
        return angle * axis

    return angle / (2.0 * np.sin(angle)) * np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1],
    ])


def align_vector_rotation(source, target):
    """Find the smallest rotation mapping one vector onto another."""
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

    return np.eye(3) + K + K @ K * ((1.0 - c) / (s * s))


def main():
    if not MODEL.exists():
        raise FileNotFoundError(f"MuJoCo model not found: {MODEL}")

    model = mujoco.MjModel.from_xml_path(str(MODEL))
    data = mujoco.MjData(model)

    def joint_id(name):
        idx = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_JOINT, name
        )
        if idx < 0:
            raise RuntimeError(f"Joint not found: {name}")
        return idx

    qadr = np.array([
        model.jnt_qposadr[joint_id(name)] for name in ARM
    ])
    dadr = np.array([
        model.jnt_dofadr[joint_id(name)] for name in ARM
    ])

    # Initialize both arms.
    for name, value in POSE.items():
        data.qpos[model.jnt_qposadr[joint_id(name)]] = value

    # Save the exact initial configuration of the left arm.
    home_q = data.qpos[qadr].copy()

    tool = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, TOOL_NAME
    )
    cube = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME
    )

    if tool < 0 or cube < 0:
        raise RuntimeError("Tool or cube body not found in the model.")

    free_joint = next(
        (
            j for j in range(model.njnt)
            if model.jnt_bodyid[j] == cube
            and model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE
        ),
        None,
    )

    if free_joint is None:
        raise RuntimeError("Cube body does not have a free joint.")

    cube_qadr = model.jnt_qposadr[free_joint]
    cube_start = data.qpos[cube_qadr:cube_qadr + 3].copy()
    cube_rotation = data.qpos[cube_qadr + 3:cube_qadr + 7].copy()

    mujoco.mj_forward(model, data)

    # Orient the tool so its local +Z axis points down in world coordinates.
    initial_rotation = data.xmat[tool].reshape(3, 3).copy()
    initial_axis = initial_rotation @ np.array([0.0, 0.0, 1.0])

    top_down_rotation = (
        align_vector_rotation(
            initial_axis, np.array([0.0, 0.0, -1.0])
        ) @ initial_rotation
    )

    jac_pos = np.zeros((3, model.nv))
    jac_rot = np.zeros((3, model.nv))

    def solve_ik(target_position):
        """Solve tool position and top-down orientation using damped least squares."""
        for _ in range(MAX_IK_STEPS):
            mujoco.mj_forward(model, data)

            pos_error = target_position - data.xpos[tool]
            current_rotation = data.xmat[tool].reshape(3, 3)
            rot_error = rotation_error(
                top_down_rotation, current_rotation
            )

            if (
                np.linalg.norm(pos_error) < POSITION_TOL
                and np.linalg.norm(rot_error) < ROTATION_TOL
            ):
                return True

            mujoco.mj_jacBody(
                model, data, jac_pos, jac_rot, tool
            )

            Jp = jac_pos[:, dadr]
            Jr = jac_rot[:, dadr]
            J = np.vstack((Jp, ROTATION_WEIGHT * Jr))
            error = np.concatenate((
                pos_error,
                ROTATION_WEIGHT * rot_error,
            ))

            dq = J.T @ np.linalg.solve(
                J @ J.T + DAMPING**2 * np.eye(6),
                error,
            )

            data.qpos[qadr] += np.clip(dq, -0.035, 0.035)

            # Respect joint limits.
            for k, name in enumerate(ARM):
                jid = joint_id(name)
                if model.jnt_limited[jid]:
                    lo, hi = model.jnt_range[jid]
                    data.qpos[qadr[k]] = np.clip(
                        data.qpos[qadr[k]], lo, hi
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

        if pos_residual > 0.025 or rot_residual > 0.15:
            print(
                f"Warning: IK residual: position={pos_residual:.3f} m, "
                f"orientation={rot_residual:.3f} rad"
            )
            return False

        return True

    with mujoco.viewer.launch_passive(model, data) as viewer:

        def animate_joint_target(target_q, carrying=False):
            """Interpolate smoothly from current joints to target joints."""
            start_q = data.qpos[qadr].copy()
            target_q = target_q.copy()

            for i in range(FRAMES):
                t = (i + 1) / FRAMES
                smooth = t * t * (3.0 - 2.0 * t)

                data.qpos[qadr] = start_q + smooth * (target_q - start_q)
                mujoco.mj_forward(model, data)

                if carrying:
                    # Kinematic attachment for this visual demonstration.
                    data.qpos[cube_qadr:cube_qadr + 3] = (
                        cube_start + data.xpos[tool] - PICK
                    )
                    data.qpos[
                        cube_qadr + 3:cube_qadr + 7
                    ] = cube_rotation
                    mujoco.mj_forward(model, data)

                viewer.sync()
                time.sleep(FRAME_DELAY)

        def move(target_position, carrying=False):
            """Plan a Cartesian target, then animate from the current pose."""
            start_q = data.qpos[qadr].copy()

            reached = solve_ik(target_position)
            goal_q = data.qpos[qadr].copy()

            # Restore the starting configuration before animating to the IK result.
            data.qpos[qadr] = start_q
            mujoco.mj_forward(model, data)

            if not reached:
                print("Warning: moving toward the best available IK solution.")

            animate_joint_target(goal_q, carrying=carrying)

        def pick_and_place():
            """Pick from above, place the cube, retreat, and return the arm home."""

            print("1/7: Approach cube from above")
            move(PICK + np.array([0.0, 0.0, APPROACH_HEIGHT]))

            print("2/7: Descend vertically to the cube")
            move(PICK)

            print("3/7: Lift cube vertically")
            move(
                PICK + np.array([0.0, 0.0, APPROACH_HEIGHT]),
                carrying=True,
            )

            print("4/7: Transfer above placement location")
            move(
                PLACE + np.array([0.0, 0.0, APPROACH_HEIGHT]),
                carrying=True,
            )

            print("5/7: Descend and place cube")
            move(PLACE, carrying=True)

            # Leave the cube at the destination.
            data.qpos[cube_qadr:cube_qadr + 3] = (
                cube_start + PLACE - PICK
            )
            data.qpos[
                cube_qadr + 3:cube_qadr + 7
            ] = cube_rotation
            mujoco.mj_forward(model, data)
            viewer.sync()

            print("6/7: Retreat vertically")
            move(PLACE + np.array([0.0, 0.0, APPROACH_HEIGHT]))

            print("7/7: Return left arm to its original joint configuration")
            animate_joint_target(home_q)

            print("Pick-and-place complete. Left arm has returned home.")

        viewer.sync()
        time.sleep(1.0)

        # Execute the complete task through the dedicated function.
        pick_and_place()

        # Keep the viewer open after the task completes.
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.03)


if __name__ == "__main__":
    main()