import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


PARK = {
    "left_shoulder_pan_joint": 3.0,
    "left_shoulder_lift_joint": -1.0,
    "left_elbow_joint": 1.2,
    "left_wrist_1_joint": -0.5,
    "left_wrist_2_joint": 1.57,
    "left_wrist_3_joint": 0.0,

    "right_shoulder_pan_joint": 3.0,
    "right_shoulder_lift_joint": -2.1,
    "right_elbow_joint": -1.57,
    "right_wrist_1_joint": 0.5,
    "right_wrist_2_joint": 1.57,
    "right_wrist_3_joint": 0.0,
}


class TracyJointStates(Node):
    def __init__(self):
        super().__init__("tracy_joint_states")

        self.declare_parameter(
            "urdf_path",
            "/home/coco/robot_research/mujoco_sandbox/tracy_rviz_ws/src/tracy_rviz/tracy.urdf",
        )
        urdf_path = self.get_parameter("urdf_path").value
        root = ET.parse(urdf_path).getroot()

        self.names = []
        self.positions = []

        for joint in root.findall("joint"):
            name = joint.get("name")
            kind = joint.get("type")

            if kind not in ("revolute", "continuous", "prismatic"):
                continue

            self.names.append(name)
            self.positions.append(PARK.get(name, 0.0))

        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        self.timer = self.create_timer(0.1, self.publish_state)

        self.get_logger().info(
            f"Publishing {len(self.names)} joint states from {urdf_path}"
        )

    def publish_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.names
        msg.position = self.positions
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = TracyJointStates()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
