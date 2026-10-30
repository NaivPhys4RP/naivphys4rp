from setuptools import find_packages, setup
from glob import glob
import os

package_name = "tracy_rviz"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "tracy.urdf"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="coco",
    maintainer_email="coco@localhost",
    description="RViz visualization for the TRACY dual UR10 setup",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "joint_states = tracy_rviz.joint_states:main",
        ],
    },
)
