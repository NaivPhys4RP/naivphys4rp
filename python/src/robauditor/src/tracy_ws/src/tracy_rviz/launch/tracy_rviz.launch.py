
from launch import LaunchDescription
from launch_ros.actions import Node
from pathlib import Path


def generate_launch_description():
    urdf_path = str(Path(__file__).resolve().parents[1] / "tracy.urdf")
    robot_description = Path(urdf_path).read_text()

    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
            output="screen",
        ),

        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            parameters=[
                {"robot_description": robot_description},
                {
                    "zeros": {
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
                },
            ],
            output="screen",
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            output="screen",
        ),
    ])
