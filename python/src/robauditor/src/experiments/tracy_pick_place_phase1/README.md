# Tracy pick-and-place Phase 1 starter kit

This starter kit creates the object model and a passive recorder. It does not
move the robot. First integrate the cube into the exact MuJoCo scene used by
`view_tracy_ros.py`; then use the existing supported control mechanism to perform
the task and mark its milestones.

## Object
- 4 cm cube
- nominal mass 0.08 kg
- URDF: `models/cube.urdf`
- MuJoCo worldbody fragment: `models/cube_mjcf_fragment.xml`

URDF is useful for ROS descriptions/visualization, but the MuJoCo simulator may
not load URDF files directly. The MJCF fragment is intended for insertion into
the existing model's `<worldbody>`. Do not paste the placeholder `X_START`,
`Y_START`, `Z_CENTRE` literally. Choose coordinates only after inspecting the
existing model and table coordinate frame. Ensure the cube starts just above
the table surface and is not interpenetrating the table or robot.

## Record the baseline
Run from a terminal where ROS 2 Jazzy and your Tracy workspace are sourced:

```bash
mkdir -p ~/failure_recovery/phase1
python3 scripts/record_phase1.py --out ~/failure_recovery/phase1/run_001
```

It records:
- every `/joint_states` message to `run_001_joint_states.csv`
- manually marked action/outcome events to `run_001_events.jsonl`
- optional end-effector TF at each event if you supply the correct frames:
  `--base-frame <base_frame> --ee-frame <tool_frame>`

Commands at the prompt:

```text
mark task_start success Baseline run started
mark approach success Moved to pre-grasp
mark grasp_attempt success Gripper closed on cube
mark lift success Cube lifted clear of table
mark transfer success Cube carried toward target
pose target 0.50 0.10 0.20 0 0 0 1
mark release success Cube released at target
mark verify_success success Cube stable at target
quit
```

The numbers in the example pose are illustrative only, NOT validated Tracy
coordinates. Replace them with measured scene coordinates. Use quaternion order
`qx qy qz qw`. Record an object pose before and after if you have measured it.
Do not label a step successful unless you observed it.

## Current integration blocker
The current ROS graph has `/joint_state_publisher` GUI nodes and a
`/tracy_mujoco_joint_bridge` subscriber to `/joint_states`, but no visible
motion action server. This starter kit intentionally does not publish joint
commands or assume a controller. Before autonomous pick/place, inspect
`/home/coco/RobAuditor/tracy_ws/view_tracy_ros.py` and determine how it loads
the MuJoCo model and which controls/actuators it exposes.
