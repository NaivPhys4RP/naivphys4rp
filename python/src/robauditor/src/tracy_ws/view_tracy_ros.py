import threading
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


MODEL_PATH = str(Path(__file__).resolve().parent / "tracy_mjcf" / "tracy_collision.xml")

# Receive the latest requested angles from ROS.
latest_positions = {}
positions_lock = threading.Lock()


class JointStateBridge(Node):
    def __init__(self):
        super().__init__("tracy_mujoco_joint_bridge")
        self.subscription = self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            10,
        )
        self.get_logger().info("Listening to /joint_states")

    def joint_state_callback(self, msg):
        updates = dict(zip(msg.name, msg.position))
        with positions_lock:
            latest_positions.update(updates)


def ros_spin(node):
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()


def main():
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    # Build a name -> MuJoCo qpos address map.
    joint_addresses = {}
    for name in (
        "left_shoulder_pan_joint",
        "left_shoulder_lift_joint",
        "left_elbow_joint",
        "left_wrist_1_joint",
        "left_wrist_2_joint",
        "left_wrist_3_joint",
        "right_shoulder_pan_joint",
        "right_shoulder_lift_joint",
        "right_elbow_joint",
        "right_wrist_1_joint",
        "right_wrist_2_joint",
        "right_wrist_3_joint",
    ):
        jid = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_JOINT, name
        )
        if jid < 0:
            raise RuntimeError(
                f"Joint '{name}' was not found in {MODEL_PATH}"
            )
        joint_addresses[name] = int(model.jnt_qposadr[jid])

    # Start in a known pose until the first ROS message arrives.
    initial_pose = {
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
    for name, angle in initial_pose.items():
        data.qpos[joint_addresses[name]] = angle
    mujoco.mj_forward(model, data)

    rclpy.init()
    node = JointStateBridge()
    ros_thread = threading.Thread(
        target=ros_spin, args=(node,), daemon=True
    )
    ros_thread.start()

    print("MuJoCo is connected to ROS 2 /joint_states.")
    print("Move sliders in the RViz Joint State Publisher GUI.")
    print("Close the MuJoCo window or press Ctrl+C to stop.")

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            while viewer.is_running():
                with positions_lock:
                    positions = latest_positions.copy()

                # Apply received joint positions by name.
                for name, angle in positions.items():
                    address = joint_addresses.get(name)
                    if address is not None:
                        data.qpos[address] = angle

                # Recompute kinematics without gravity-driven drift.
                mujoco.mj_forward(model, data)
                viewer.sync()
                time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
