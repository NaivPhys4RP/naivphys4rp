from typing import Dict, Any
import math
from terminals import (JointDefinition, TransformDefinition,
                       HollowConeDimensions, ClosedConeDimensions,
                       ClosedTorusDimensions)
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign
import numpy as np

class SimpleDrawerAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. TORSO (Drawer Walls) ---
        t_spec = spec.get("torso", {})
        t_height = get_val(t_spec, "height") or 0.12
        t_radius = get_val(t_spec, "radius") or 0.15

        # 45-degree rotation to align the 4-segment cone as a square box
        ALIGN_YAW = 0.785398

        drawer_body = ShapeFactory.generate_conical_hollow(
            dimensions=HollowConeDimensions.generate(
                height=t_height,
                outer_bottom_radius=t_radius,
                outer_top_radius=t_radius,
                segments=4
            ),
            aesthetics=ContainerAestheticDesign.generate(colors=["BLUE"]),
            transform=TransformDefinition.generate(
                pos_z=0.0,  # Bottom origin
                yaw=ALIGN_YAW
            )
        ).compile()

        # --- 2. BASE (Drawer Bottom) ---
        drawer_bottom = ShapeFactory.generate_conical_closed(
            dimensions=ClosedConeDimensions.generate(
                height=0.01,
                outer_bottom_radius=t_radius,
                outer_top_radius=t_radius,
                segments=4
            ),
            aesthetics=ContainerAestheticDesign.generate(colors=["GREEN"]),
            transform=TransformDefinition.generate(
                pos_z=0.0,
                yaw=0.0  # Inherits 45deg from joint
            )
        ).compile()

        bottom_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_z=0.0,
            yaw=0.0
        ).compile()

        # --- 3. HANDLE (Perfectly Synchronized Transform) ---
        # The distance to the flat face center is t_radius * cos(45)
        dist_to_face = t_radius * math.cos(ALIGN_YAW)
        mid_height = t_height / 2.0

        handle = ShapeFactory.generate_torus_closed(
            dimensions=ClosedTorusDimensions.generate(
                major_radius=0.025,
                minor_radius=0.008,
                arc_degrees=180.0
            ),
            aesthetics=ContainerAestheticDesign.generate(colors=["SILVER"]),
            transform=TransformDefinition.generate(
                pos_x=dist_to_face/np.sqrt(2),  # Perfect X alignment
                pos_y=dist_to_face/np.sqrt(2),  # Centered on Y
                pos_z=mid_height,  # Perfect Z alignment
                pitch=0,  # Flip to vertical
                yaw= +ALIGN_YAW+np.pi/2  # Aligned with the face normal
            )
        ).compile()

        # Joint must match the handle transform exactly to avoid offsets
        handle_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_x=dist_to_face,
            pos_y=0.0,
            pos_z=mid_height,
            yaw=0.0
        ).compile()

        return {
            "scene_object": {
                "simple_drawer": {
                    "body": {
                        **drawer_body,
                        "bottom": {**drawer_bottom, **bottom_joint},
                        "handle": {**handle, **handle_joint}
                    }
                }
            }
        }
if __name__ == '__main__':
    drawer = SimpleDrawerAssembler()
    import json

    print(json.dumps(drawer.generate({}), indent=4))