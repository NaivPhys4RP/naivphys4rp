import math
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, ClosedConeDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign
import numpy as np

class SimpleChairAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. SETTINGS & DIMENSIONS ---
        t_spec = spec.get("torso", {})
        b_spec = spec.get("back", {})
        f_spec = spec.get("feet", {})

        s_width = get_val(spec, "width") or 0.4
        s_depth = get_val(spec, "depth") or 0.4
        s_thickness = get_val(t_spec, "thickness") or 0.02

        # Scale factor for 4-segment cuboid (Diamond to Square)
        s_radius = (s_width / 2) * math.sqrt(2)

        b_height = get_val(b_spec, "height") or s_thickness
        b_thickness = get_val(b_spec, "thickness") or 0.02

        f_height = get_val(f_spec, "height") or 0.45
        f_radius_val = get_val(f_spec, "radius") or 0.02
        f_radius = f_radius_val * math.sqrt(2)

        SEGMENTS = 8
        SQ_YAW = math.pi / 4

        # --- 2. SHARED IDENTICAL DEFINITIONS ---
        foot_aesthetic = ContainerAestheticDesign.generate(colors=get_val(f_spec, "color"))
        foot_structural = ContainerStructuralDesign.generate(
            material=get_val(f_spec, "material"),
            density=get_val(f_spec, "mass")
        )

        # --- 3. GEOMETRY DEFINITIONS ---
        seat_dims = ClosedConeDimensions.generate(
            height=s_thickness, outer_bottom_radius=s_radius,
            outer_top_radius=s_radius, segments=SEGMENTS
        )

        back_dims = ClosedConeDimensions.generate(
            height=b_height, outer_bottom_radius=s_radius,
            outer_top_radius=s_radius, segments=SEGMENTS
        )

        foot_dims = ClosedConeDimensions.generate(
            height=f_height, outer_bottom_radius=f_radius,
            outer_top_radius=f_radius, segments=SEGMENTS
        )

        # --- 4. GENERATION ---

        # TORSO: The Seat
        seat_z = 0
        torso_shape = ShapeFactory.generate_conical_closed(
            dimensions=seat_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
            structural=ContainerStructuralDesign.generate(
                material=get_val(t_spec, "material"),
                density=get_val(t_spec, "mass")
            ),
            transform=TransformDefinition.generate(pos_z=seat_z, yaw=SQ_YAW)
        )
        torso = torso_shape.compile()

        siblings = {}

        # FEET: Positioned at the 4 vertices of the diamond
        v_dist = s_radius - f_radius_val
        corners = [
            ("front", v_dist, 0), ("back", -v_dist, 0),
            ("left", 0, v_dist), ("right", 0, -v_dist)
        ]

        for name, cx, cy in corners:
            # Safer logic: top of leg at seat bottom
            fz = -f_height - (s_thickness / 2)

            foot_shape = ShapeFactory.generate_conical_closed(
                dimensions=foot_dims,
                aesthetics=foot_aesthetic,
                structural=foot_structural,
                transform=TransformDefinition.generate(pos_x=cx, pos_y=cy, pos_z=fz, yaw=SQ_YAW)
            )
            foot = foot_shape.compile()

            joint = JointDefinition.generate(
                joint_type="fixed", pos_x=cx, pos_y=cy, pos_z=fz, yaw=SQ_YAW
            ).compile()

            siblings[f"foot_{name}"] = {**foot, **joint}

        # --- BACK SUPPORT ROTATION LOGIC ---
        bx = -v_dist + 0.5*s_radius/np.sqrt(2)
        by = -0.5 * s_radius / np.sqrt(2)-f_radius*2
        bz = (b_height / 2) + (s_thickness / 2) +s_radius/np.sqrt(2)

        # Note: In an intrinsic RPY system, to rotate a pitched object (90 deg)
        # around its own long axis, you must apply the rotation to 'roll'.
        back_transform = TransformDefinition.generate(
            pos_x=bx, pos_y=by, pos_z=bz,
            roll=0*SQ_YAW-1*np.pi/2,
            pitch=0*np.pi/2+math.pi / 4,
            yaw=0-np.pi/4
        )

        back_shape = ShapeFactory.generate_conical_closed(
            dimensions=back_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(b_spec, "color")),
            structural=ContainerStructuralDesign.generate(
                material=get_val(b_spec, "material"),
                density=get_val(b_spec, "mass")
            ),
            transform=back_transform
        )
        back = back_shape.compile()

        back_joint = JointDefinition.generate(
            joint_type="revolute",
            pos_x=bx, pos_y=0, pos_z=bz,
            roll=SQ_YAW,
            pitch=math.pi / 2,
            yaw=0
        ).compile()

        siblings["back_support"] = {**back, **back_joint}

        return {
            "scene_object": {
                "mechanical_chair": {
                    "torso": {
                        **torso,
                        **siblings
                    }
                }
            }
        }

if __name__ == '__main__':
    chair_obj = SimpleChairAssembler()
    import json
    print(json.dumps(chair_obj.generate({
        "torso": {"color": ["BROWN"], "material": "WOOD"},
        "back": {"color": ["BROWN"], "material": "WOOD", "height": 0.5, "thickness": 0.03},
        "feet": {"color": ["BLACK"], "material": "STEEL", "radius": 0.02},
        "width": 0.45,
        "depth": 0.45
    }), indent=4))