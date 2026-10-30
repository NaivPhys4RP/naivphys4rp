# RobAuditor: Failure Recovery for Robotic Execution

RobAuditor is a research project focused on context-adaptive verification, failure detection, recovery-plan synthesis, and traceable decision-making for robotic systems.

This project uses Tracy, ROS 2, RViz, and MuJoCo as the initial experimental environment. The goal is to progress from a working robot simulation to a reproducible failure-recovery pipeline that combines multiple independent verifiers and synthesizes a safe, coherent recovery plan.

The central research objective is **Failure Recovery Plan Synthesis from an Ensemble of Verifiers**: reconciling conflicting or incomplete recommendations from multiple verification modules based on execution context, feasibility, evidence quality, and risk.

## Table of Contents

- [Project Goals](#project-goals)
- [Current Environment](#current-environment)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Run the Phase 1 Success Test](#run-the-phase-1-success-test)
- [Research Implementation Phase](#research-implementation-phase)
- [RobAuditor Architecture](#robauditor-architecture)
- [Initial Pick-and-Place Experiment](#initial-pick-and-place-experiment)
- [Verifier Interface](#verifier-interface)
- [Recovery-Plan Synthesis Algorithm](#recovery-plan-synthesis-algorithm)
- [Research Metrics](#research-metrics)
- [First Experimental Campaign](#first-experimental-campaign)
- [Completion Criteria](#completion-criteria)
- [Troubleshooting](#troubleshooting)
- [Next Step](#next-step)

## Project Goals

The central research question is:

> Can context- and risk-aware recovery synthesis produce safer, more feasible, and more successful recovery plans than majority voting or fixed-priority selection?

RobAuditor should observe and assess robot execution without unnecessarily replacing the existing robot controller. It should use execution evidence and independent verification modules to identify failures, explain their causes, and recommend a coherent recovery plan.

Examples of recovery suggestions include:

- Go back to the failed action.
- Return to an earlier step.
- Replan the robot trajectory.
- Retry a grasp.
- Change or reposition an object.
- Introduce additional actions.
- Stop execution and request human intervention.

The system should not simply select the most popular or highest-confidence suggestion. It must account for hard safety constraints, feasibility, action dependencies, task context, and the evidence supporting each recommendation.

## Current Environment

The initial development environment is:

| Component | Configuration |
|---|---|
| Operating system | Ubuntu 24.04 |
| Robot | Tracy |
| Robotics middleware | ROS 2 Jazzy |
| Visualization | RViz 2 |
| Physics simulation | MuJoCo |
| Programming language | Python |
| Main experiment directory | `experiments/` |
| Tracy simulation workspace | `tracy_ws/` |
| MuJoCo Python environment | `tracy_ws/.venv_mujoco/` |

The current environment provides the foundation for execution monitoring and failure-recovery experiments.

**Important:** Seeing Tracy in both RViz and MuJoCo does not, by itself, establish that both systems share synchronized robot states or that a task controller is executing a manipulation plan. Verify the actual interfaces and synchronization before using the environment for quantitative experiments.

The current Phase 1 experiments run through the MuJoCo Python API. ROS 2 is installed, but the existence of ROS 2 does not mean that an autonomous motion-control interface is currently available.

A successful simulation run establishes a baseline only. It does not demonstrate that failure detection, verifier coordination, recovery synthesis, or recovery execution works.

## Repository Structure

The current RobAuditor source directory is:

```text
naivphys4rp/
└── python/
    └── src/
        └── robauditor/
            └── src/
                ├── README.md
                │
                ├── experiments/
                │   └── tracy_pick_place_phase1/
                │       └── scripts/
                │           ├── randomized_pick_place_perception_audit.py
                │           ├── randomized_pick_place_audit.py
                │           ├── camera_guided_pick_place.py
                │           ├── tracy_cube_pick_place.py
                │           ├── f1_unreachable_pick_both_arms.py
                │           ├── f1_unreachable_pick_left.py
                │           ├── read_results.py
                │           └── output/
                │
                ├── tracy_ws/
                │   ├── tracy_mjcf/
                │   │   └── tracy_collision_phase1.xml
                │   └── .venv_mujoco/
                │
                ├── functional_verification/
                ├── neem_interface/
                └── tracebot_audit_trail_generator/
```

The structure above shows the current main directories. Additional files and subdirectories may exist within the workspaces.

### Main directories

**`experiments/`**

Contains the Tracy Phase 1 experimental scripts, perception-guided pick-and-place pipeline, baseline experiments, recovery tests, and generated experiment results.

**`tracy_ws/`**

Contains the Tracy MuJoCo simulation workspace, including the robot model, environment description, and Python virtual environment used for simulation.

The other RobAuditor components, including `functional_verification/`, `neem_interface/`, and `tracebot_audit_trail_generator/`, remain part of the wider project.

### Important Tracy files

The main MuJoCo model is:

```text
tracy_ws/tracy_mjcf/tracy_collision_phase1.xml
```

The main integrated experiment is:

```text
experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py
```

The baseline experiment is:

```text
experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_audit.py
```

The successful standalone pick-and-place test is:

```text
experiments/tracy_pick_place_phase1/scripts/tracy_cube_pick_place.py
```

### Experiment script descriptions

| Script | Purpose |
|---|---|
| `randomized_pick_place_perception_audit.py` | Main integrated perception-guided randomized pick-and-place experiment. |
| `randomized_pick_place_audit.py` | Baseline randomized pick-and-place audit without integrated perception. |
| `camera_guided_pick_place.py` | Camera-guided pick-and-place testing. |
| `tracy_cube_pick_place.py` | Standalone Tracy cube pick-and-place test. |
| `f1_unreachable_pick_left.py` | Tests unreachable-pick recovery with the left arm. |
| `f1_unreachable_pick_both_arms.py` | Tests unreachable-pick recovery with both arms. |
| `read_results.py` | Reads and analyses experiment results. |

## Getting Started

### 1. Prerequisites

Install or configure:

- Ubuntu 24.04.
- ROS 2 Jazzy.
- Git.
- Python 3.
- MuJoCo and the Python dependencies required by the simulation scripts.
- The Tracy workspace and its required packages, where ROS integration is used.

Use the project's Python virtual environment for dependencies associated with MuJoCo.

### 2. Navigate to the project

The repository is located at:

```bash
cd ~/naivphys4rp
```

The RobAuditor source directory is:

```bash
cd ~/naivphys4rp/python/src/robauditor/src
```

### 3. Activate the MuJoCo environment

From the repository root:

```bash
cd ~/naivphys4rp

source python/src/robauditor/src/tracy_ws/.venv_mujoco/bin/activate
```

Verify the MuJoCo installation:

```bash
python -c "import mujoco; print(mujoco.__version__)"
```

### 4. ROS 2 environment

When working with ROS 2 components, source ROS 2 Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
```

If the Tracy workspace contains a built ROS 2 overlay that is required by the particular experiment, source it as well:

```bash
source ~/naivphys4rp/python/src/robauditor/src/tracy_ws/install/setup.bash
```

The ROS overlay command is conditional on the workspace containing a valid `install/setup.bash`.

### 5. Build the ROS workspace when required

If the Tracy workspace contains ROS 2 packages, build the relevant packages from the workspace root:

```bash
cd ~/naivphys4rp/python/src/robauditor/src/tracy_ws

source /opt/ros/jazzy/setup.bash

colcon build --symlink-install
```

Then source the resulting overlay:

```bash
source install/setup.bash
```

The current MuJoCo Python experiments do not require a ROS 2 build merely to run.

## Run the Phase 1 Success Test

To run the standalone RobAuditor Phase 1 pick-and-place test, follow these steps.

### 1. Open the repository

```bash
cd ~/naivphys4rp
```

### 2. Activate the MuJoCo virtual environment

```bash
source python/src/robauditor/src/tracy_ws/.venv_mujoco/bin/activate
```

### 3. Run the success script

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/tracy_cube_pick_place.py
```

### 4. Check the result

- The MuJoCo viewer should open if the script uses the viewer.
- The robot should attempt to pick up the cube and place it at the target location.
- The terminal should report the successful task outcome if the task completes successfully.

**Important:** Keep the standalone success script separate from the failure experiments. The randomized perception-guided audit is the main integrated experiment; the standalone success script is useful for checking the basic pick-and-place behaviour.

If the run fails, save or copy the terminal output and use it to troubleshoot the issue.

### Run the main perception-guided experiment

The main integrated experiment is:

```text
randomized_pick_place_perception_audit.py
```

Run it with 10 trials and random seed 40:

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py --trials 10 --seed 40
```

For headless execution:

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py --trials 10 --seed 40 --no-viewer
```

This experiment integrates camera perception, cube-coordinate estimation, workspace validation, IK evaluation, recovery recommendations, and simulated execution.

### Run the baseline experiment

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_audit.py
```

The baseline provides a comparison against the integrated perception-guided experiment.

## Research Implementation Phase

This phase focuses on developing and evaluating the failure-recovery pipeline using six controlled failure scenarios. Each scenario targets a different part of the robot execution pipeline and is intended to test how independent verifiers detect failures and recommend recovery actions.

The main objective is not simply to demonstrate failure detection. It is to investigate how multiple verifiers identify different aspects of a failure, how their recommendations may agree or conflict, and how the synthesis component selects one coherent and safe recovery plan.

### Proposed failure set

The following six failure types are proposed for the initial experimental framework.

| ID | Failure to induce | How to create it in MuJoCo | Expected verifier findings | Possible recovery |
|---|---|---|---|---|
| **F1** | **Unreachable target** | Place the target outside the robot's reachable workspace or specify an impossible target pose. | Kinematics verifier reports that the target cannot be reached; task verifier reports that the task is incomplete. | Replan to a reachable pose or introduce an alternative action (INA). |
| **F2** | **Missed grasp** | Let the gripper close slightly away from the object, so it fails to attach. | Grasp verifier detects that the object was not attached; task verifier reports grasp failure. | Reposition and retry grasp (GOB). |
| **F3** | **Object displacement** | Move the object after perception but before grasping, making the previously recorded object pose outdated. | Perception verifier detects a mismatch between the expected and observed object pose; grasp verifier may report failure. | Reperceive and return to an earlier step (GBB). |
| **F4** | **Collision risk / unsafe trajectory** | Introduce an obstacle into the planned path or configure a simulated safety monitor to flag an unsafe trajectory. | Safety verifier rejects the trajectory; kinematics verifier may still report that the target is reachable. | Stop, find a collision-free route, or request human intervention (HIC) if no safe route exists. |
| **F5** | **Infeasible motion** | Configure a movement that violates joint limits or cannot be executed along the required trajectory. | Kinematics verifier detects an infeasible movement, while task logic may still consider the action valid. | Replan the trajectory or change the approach action (INA). |
| **F6** | **Object unsuitable for grasping** | Use an object whose dimensions or orientation make it incompatible with the gripper. | Grasp feasibility verifier reports that the object cannot be grasped using the current configuration. | Change the grasp approach, introduce a suitable replacement object (INO), or request human intervention (HIC). |

These are proposed experimental scenarios. They should be implemented and validated individually before being used together in the recovery-synthesis evaluation.

### Which failures should be implemented first?

The recommended implementation order is:

**Stage 1 — Basic failures**

Start with:

1. F1: Unreachable target.
2. F2: Missed grasp.
3. F3: Object displacement.

These scenarios test three different aspects of robot execution: reachability, grasp execution, and object-state consistency.

**Stage 2 — Conflicting verifier recommendations**

After the first three scenarios work reliably, implement:

4. F4: Collision risk / unsafe trajectory.
5. F5: Infeasible motion.

These scenarios are particularly useful for testing whether the synthesis component can resolve conflicting recommendations while respecting safety and motion constraints.

**Stage 3 — More complex recovery**

Finally, implement:

6. F6: Object unsuitable for grasping.

This scenario introduces object suitability and the possibility of changing the object or requesting human intervention.

### F1 — Unreachable Target: Existing Implementation

The current F1 baseline implementation is:

`experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_audit.py`

The main perception-guided experiment is:

`experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py`

The baseline evaluates randomized candidate positions using workspace and IK checks. The perception-guided version adds camera-based object-position estimation before planning.

#### What the baseline script checks

- Randomizes distinct cube positions for each trial.
- Applies a workspace-side heuristic relative to the table center and the arm's shoulder reference.
- Checks inverse-kinematics (IK) feasibility for the candidate arm across the required pick, lift, and place waypoints.
- Executes only targets that pass the workspace and IK checks.
- When both arms are feasible, selects the arm with the lower estimated joint-space travel cost.
- Records each trial and its recovery recommendation in JSON and CSV audit outputs.

#### What the perception-guided script adds

- Captures RGB, depth, and segmentation observations.
- Identifies cube pixels using the simulator's segmentation information.
- Reconstructs a 3D point cloud from the depth image.
- Estimates the cube centre in world coordinates.
- Uses the perceived position for workspace validation and IK planning.
- Compares estimated coordinates with simulator ground truth for perception evaluation.
- Records perception observations and trial outcomes.

**Important perception limitation:** The current segmentation uses MuJoCo-provided geom labels. This is simulator-assisted camera perception, not an independent RGB-based object detector.

#### Important implementation details

- The model is loaded from `tracy_ws/tracy_mjcf/tracy_collision_phase1.xml`.
- The scripts are located under `experiments/tracy_pick_place_phase1/scripts/`.
- The cube body is `phase1_cube`.
- The table collision geometry is `table_collision_0`.
- The tool-frame bodies are `l_gripper_tool_frame` and `r_gripper_tool_frame`.
- The camera used by the perception pipeline is `tracy_rgbd_camera`.
- The grasp target is calculated from the cube's top surface plus 0.02 m.
- The approach target is 0.15 m above the grasp target.
- The cube half-height is calculated from the model geometry.

The IK configuration used in the baseline is:

| Parameter | Value |
|---|---:|
| `DAMPING` | `0.03` |
| `MAX_IK_STEPS` | `300` |
| `POSITION_TOL` | `0.008` |
| `ROTATION_TOL` | `0.04` |
| `ROTATION_WEIGHT` | `0.25` |

If a target is rejected as outside the workspace or unreachable, the baseline records a `CHANGE_OBJECT_POSITION` recovery recommendation. The recommendation is logged; the script does not automatically reposition the cube as a recovery action.

Rejected poses pause for five seconds in the MuJoCo viewer when a viewer is enabled. Headless runs skip the viewer pause.

The cube-carrying behavior uses:

```python
EXECUTION_MODE = "kinematic_attachment_surrogate"
```

This is a kinematic attachment surrogate, not a demonstration of physical grasp/contact dynamics.

#### Run F1 baseline

From the repository root:

```bash
cd ~/naivphys4rp

source python/src/robauditor/src/tracy_ws/.venv_mujoco/bin/activate

python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_audit.py
```

Optional command-line arguments, where supported by the script:

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_audit.py --trials 10 --seed 42
```

#### Run perception-guided F1

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py --trials 10 --seed 40
```

To run without the viewer:

```bash
python python/src/robauditor/src/experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py --trials 10 --seed 40 --no-viewer
```

#### Interpreting the results

For the baseline experiment, relevant metrics include:

- `reachable_trials`: targets that pass the implemented reachability checks.
- `executed_trials`: trials that proceed to execution.
- `unreachable_trials`: targets rejected as unreachable.
- `workspace_rejected_trials`: targets rejected by the workspace heuristic.
- `placement_successes`: recorded placement outcomes.

For the perception-guided experiment, additionally inspect:

- Perception success and failure counts.
- Estimated cube coordinates.
- Ground-truth position error.
- Segmentation pixel count.
- Workspace and IK decisions based on perceived coordinates.
- Recovery recommendations.
- Execution outcomes.

Interpret placement outcomes in light of the kinematic attachment surrogate rather than as evidence of physical contact dynamics.

F1 is an audit of workspace and kinematic reachability plus trial logging. It should not be described as a fully validated physical grasp or as an automatic recovery executor.

### Verifier disagreement example: F2 Missed Grasp

The missed-grasp scenario can be used to test whether the synthesis component can reconcile different recommendations.

| Verifier | Possible recommendation |
|---|---|
| Grasp verifier | Retry grasp |
| Kinematics verifier | Replan approach |
| Task-logic verifier | Repeat grasping action |
| Safety verifier | Stop because the current approach is unsafe |

Your synthesis component should not blindly select the most frequent recommendation. It should consider safety, feasibility, and the current state before selecting a recovery plan.

### Experimental data to record

For every induced failure, record:

- Initial robot and object states.
- The exact failure condition.
- Each verifier's decision and confidence.
- Each verifier's proposed recovery strategy.
- The final synthesized plan.
- Whether recovery succeeded.

The RobAuditor thesis supports the recovery categories GOB, GBB, HIC, INO, and INA. These categories provide the recovery terminology for the experiments.

**Important distinction:** F1 and F5 should remain separate in the experiments. F1 means that the target itself is outside the reachable workspace. F5 means that the target may be reachable, but the required movement or trajectory is infeasible.

## RobAuditor Architecture

Keep the robot execution system separate from the RobAuditor verification and recovery logic. RobAuditor should observe and assess execution, then recommend recovery without unnecessarily replacing Tracy's controller.

```text
Tracy — Robot execution
        |
        v
Execution trace collector
        |
        v
Execution record / episode
        |
        v
Verifier ensemble
   |          |          |
 Task     Kinematics   Safety
 logic     verifier    verifier
   \          |          /
        v
RobAuditor metareasoner
        |
        v
Recovery-plan validation
        |
        v
Recovery execution in simulation
        |
        v
Reverification
        |
        v
Audit trail
```

### Main components

**Tracy — Robot execution**

Provides the available robot actions, joint states, object poses, and task status.

**Execution trace collector**

Collects execution evidence from ROS topics, action events, timestamps, and MuJoCo state.

**Execution record / episode**

Stores intended outcomes, observed outcomes, object state, and failure history.

**Verifier ensemble**

Uses specialized verifiers to assess task logic, kinematics, object state, and safety.

**RobAuditor metareasoner**

Resolves disagreements, evaluates context and risk, and synthesizes a single recovery plan.

**Recovery-plan validator**

Checks feasibility, safety, preconditions, and action coherence before execution.

**Recovery executor**

Executes only approved recovery actions in simulation.

**Audit trail**

Records the evidence, verifier decisions, explanations, candidate plans, selected recovery, and final outcome.

### Longer-term research alignment

The RobAuditor paper describes a framework involving execution traces, a digital twin, SOMTA, NEEMs, distributed verifiers, a metareasoner, and audit generation.

- **SOMTA:** Socio-physical Models of Traceable Activities, extending activity modeling for traceability, verification, recovery, and audit generation.
- **NEEMs:** Narrative-enabled Episodic Memories that capture robot experiences and activity narratives.
- **Digital twin (DT):** A physically grounded model that can augment execution traces and support reasoning about interactions.
- **Distributed verifiers:** Specialized reasoning units selected according to the task and available context.
- **Metareasoner:** Synthesizes verification outcomes and recovery plans.
- **Audit generation:** Produces a traceable account of the execution and verification process.

These components can be introduced incrementally. Begin with a structured execution record in JSON, simple verifiers, and a testable recovery synthesizer before adding a full ontology and episodic-memory infrastructure.

MuJoCo can serve as the simulation environment, provided the interfaces needed for the digital-twin workflow are implemented and validated.

## Initial Pick-and-Place Experiment

The first end-to-end experiment should be small enough to debug and repeat.

### Experimental workflow

1. Initialize Tracy and the object in a known state.
2. Define the intended pick-and-place task.
3. Capture camera observations when using the perception-guided experiment.
4. Estimate the object position.
5. Execute the grasp attempt.
6. Record commanded actions, joint states, gripper state, and object pose where available.
7. Run the task-logic, kinematics, and safety verifiers.
8. Deliberately inject one of the controlled failures: F1, F2, or F3.
9. Collect the verifier recommendations.
10. Ask the metareasoner to synthesize a recovery plan.
11. Validate the plan before execution.
12. Execute the approved recovery in simulation.
13. Re-run verification to determine whether the task recovered successfully.
14. Save the evidence, recommendations, selected plan, and final outcome.

Adapt the object, target pose, and available control interface to the actual Phase 1 scene.

Begin with simulation-only recovery. Do not send unvalidated recovery plans to physical hardware.

## Verifier Interface

Use a common JSON-compatible structure for the output of each verifier.

Example:

```python
verifier_result = {
    "verifier_id": "grasp_verifier",
    "decision": False,
    "confidence": 0.92,
    "decision_explanation": (
        "Object is not attached to the gripper"
    ),
    "recovery_suggestion": {
        "strategy": "GO_BACK_ONE_STEP",
        "actions": [
            "reposition",
            "retry_grasp"
        ]
    }
}
```

This is a proposed starting interface, not an existing Tracy or RobAuditor API.

The fields represent:

- `verifier_id`: identifies the verification module.
- `decision`: whether the tested condition was satisfied.
- `confidence`: the verifier's confidence in its decision.
- `decision_explanation`: the evidence or reasoning supporting the decision.
- `recovery_suggestion`: the proposed strategy and associated actions.

As the system develops, consider adding:

- Evidence references.
- Timestamps.
- Feasibility results.
- Risk assessments.
- Explicit action preconditions.
- A unique action or episode ID.

Preserve individual verifier outputs so that the final decision can be traced to the evidence and recommendations that produced it.

## Recovery-Plan Synthesis Algorithm

Since the research focuses on reconciling recommendations from multiple verifiers, the synthesis method should go beyond majority voting.

A practical first version should use the following order.

### 1. Safety gate

Reject plans that violate hard safety constraints, such as defined joint limits or collision constraints.

### 2. Feasibility check

Evaluate whether the proposed actions can be performed from the current robot and object state.

### 3. Context-aware scoring

Compare the remaining plans using factors such as:

- Verifier confidence.
- Evidence quality.
- Task context.
- Predicted risk.
- Recovery cost.
- Expected success.
- Available actions and resources.

### 4. Coherence check

Ensure that the selected actions are correctly ordered and their preconditions can be satisfied.

### 5. Fallback

If no safe plan can be justified, stop execution and request human intervention.

### 6. Reverification

After an approved recovery is executed, verify the outcome again rather than assuming success.

### Example of conflicting recommendations

| Verifier | Recommendation | Confidence |
|---|---|---:|
| Task logic | Retry grasp | 0.90 |
| Kinematics | Replan approach | 0.85 |
| Safety | Stop because a collision risk was detected | 0.96 |

The highest-confidence recommendation must not automatically win. If the safety verifier identifies a credible hard constraint violation, the system must not blindly retry the grasp.

The synthesizer should select a validated safe action or request intervention if no safe action can be justified.

## Research Metrics

Collect these metrics from the first experiment.

| Metric | What it measures |
|---|---|
| Failure detection rate | How often injected failures are detected correctly |
| False-positive rate | How often successful actions are incorrectly classified as failures |
| Recovery success rate | How often the selected recovery restores the intended task outcome |
| Safety violation rate | How often recovery violates a defined safety constraint |
| Recovery steps | How many actions are needed to recover |
| Decision latency | How long verification and synthesis take |
| Explanation completeness | Whether the decision can be traced to evidence and verifier outputs |

Also record the selected recovery plan and the number of execution steps for each recovery attempt.

Define metric calculations and trial counts before experimentation. Distinguish a recovery attempt from a complete task episode, and report the number of trials used to calculate each rate.

For fair comparisons, use the same initial conditions and failure scenarios across the baseline and proposed methods wherever possible.

## First Experimental Campaign

The first campaign should follow this sequence.

### Experiment 1 — Baseline

Run the successful pick-and-place scenario three times with distinct run IDs. Save logs and summaries.

### Experiment 2 — Failure injection

Implement and test F1 through F6 individually, with a repeatable setup and reset procedure for each. Begin with F1, F2, and F3 before moving to F4, F5, and F6.

### Experiment 3 — Independent verifier evaluation

Run the applicable verifiers independently on the same scenario. Save their decisions, confidence values, explanations, and recovery suggestions.

### Experiment 4 — Synthesis evaluation

Submit the verifier outputs to the synthesis component. Inspect the selected plan, rejected alternatives, feasibility checks, and safety rationale.

### Experiment 5 — Recovery execution

Validate the selected plan, execute it in simulation, and verify the outcome again.

### Experiment 6 — Baseline comparison

Run fixed-priority selection, voting-based selection, and context- and risk-aware synthesis against the same scenarios.

### Experiment 7 — Audit and reporting

Save logs, decisions, plans, outcomes, metrics, and experiment configurations.

### Suggested run record

Each run should have a unique run ID and enough information to reproduce the initial conditions and failure injection.

```json
{
  "run_id": "F2_run_001",
  "scenario": "pick_and_place",
  "failure_type": "missed_grasp",
  "initial_state": {},
  "intended_action": {},
  "observed_state": {},
  "verifier_results": [],
  "candidate_recovery_plans": [],
  "selected_recovery_plan": {},
  "safety_validation": {},
  "recovery_outcome": "not_run",
  "execution_steps": null,
  "decision_latency_ms": null
}
```

This is an example schema. Replace the empty objects and placeholder values with actual data collected by the implementation. Do not report a recovery as successful until its outcome has been verified.

## Completion Criteria

The initial research prototype is ready for evaluation when:

- The baseline task is repeatable and its logs are saved.
- F1 through F6 can be injected and reproduced independently.
- Each verifier returns a structured, traceable result.
- The synthesizer handles both agreeing and conflicting recommendations.
- Recovery plans are checked for safety and feasibility before execution.
- Recovery outcomes are verified rather than assumed.
- Fixed-priority, voting-based, and context- and risk-aware methods can be evaluated on consistent scenarios.
- The results and audit trails can be used to reproduce the experiments.

## Troubleshooting

### ROS commands cannot find packages

Source the ROS distribution:

```bash
source /opt/ros/jazzy/setup.bash
```

If a valid ROS workspace overlay is available, source it:

```bash
source ~/naivphys4rp/python/src/robauditor/src/tracy_ws/install/setup.bash
```

### MuJoCo Python imports fail

Activate the project virtual environment:

```bash
cd ~/naivphys4rp

source python/src/robauditor/src/tracy_ws/.venv_mujoco/bin/activate
```

Check whether the required dependencies are installed in that environment.

### The Phase 1 scene cannot find the robot model

Check the model paths referenced by the experiment script.

The main Phase 1 MJCF model is:

```text
tracy_ws/tracy_mjcf/tracy_collision_phase1.xml
```

Prefer paths resolved relative to the script or an explicitly configured model directory rather than hard-coded paths from another machine.

### RViz and MuJoCo appear inconsistent

Inspect the ROS topics, publishers, subscribers, timestamps, and joint-state sources. Confirm that the two systems are receiving the intended shared state before interpreting visual agreement as synchronization.

### The simulation starts, but the robot does not perform a task

Starting RViz, moving joint-state sliders, or opening MuJoCo does not necessarily launch a task controller. Inspect the available control scripts and ROS interfaces before implementing task execution or recovery.

### A failure test produces the expected result without invoking a verifier

Check whether the scene script directly forces the expected object state or recovery outcome. The experiment should demonstrate that the verifier detects the failure and that the synthesizer selects the recovery, rather than the test script simply producing the desired result.

### Perception fails to detect the cube

Check:

- Whether the camera name `tracy_rgbd_camera` exists in the MJCF model.
- Whether the cube is within the camera's field of view.
- Whether valid depth values are available.
- Whether the segmentation mask contains enough cube pixels.
- Whether the camera pose and intrinsics are being used correctly.

A perception failure should not be silently replaced with simulator ground-truth coordinates during planning.

## Next Step

Continue with the working perception-guided Phase 1 experiment:

```text
experiments/tracy_pick_place_phase1/scripts/randomized_pick_place_perception_audit.py
```

Then extend the existing workspace and IK checks into independent verifier modules.

The next major implementation objective is to develop the first testable recovery-plan synthesis component, capable of receiving several verifier recommendations, resolving conflicts, checking feasibility and risk, and producing one coherent recovery plan.

Start with the smallest complete RobAuditor loop:

**Record execution → verify outcome → detect an injected failure → synthesize a recovery plan → validate → recover → verify again → save the audit trail.**

Keep the initial experiment small and measurable. Expand the framework only after the baseline and recovery loop can be reproduced reliably.