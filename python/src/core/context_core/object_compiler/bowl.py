import random
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, HollowConeDimensions, ClosedConeDimensions, ClosedTorusDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimpleBowlAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. TORSO (The Deep Basin) ---
        t_spec = spec.get("torso", {})
        t_height = get_val(t_spec, "height") or 0.06
        t_radius_bottom = get_val(t_spec, "radius_bottom") or 0.05
        t_radius_top = get_val(t_spec, "radius_top") or 0.09

        torso_dims = HollowConeDimensions.generate(
            height=t_height,
            outer_bottom_radius=t_radius_bottom,
            outer_top_radius=t_radius_top
        )

        torso = ShapeFactory.generate_conical_hollow(
            dimensions=torso_dims,
            transform=TransformDefinition.generate(pos_z=t_height / 2)
        ).compile()

        # --- 2. BASE (The Foot - Child of Torso) ---
        b_spec = spec.get("base", {})
        b_height = get_val(b_spec, "height") or 0.008

        base_dims = ClosedConeDimensions.generate(
            height=b_height,
            outer_bottom_radius=t_radius_bottom * 0.9,
            outer_top_radius=t_radius_bottom * 0.9
        )

        base = ShapeFactory.generate_conical_closed(
            dimensions=base_dims,
            transform=TransformDefinition.generate(pos_z=0.0)
        ).compile()

        base_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_z=0.0
        ).compile()

        return {
            "scene_object": {
                "simple_bowl": {
                    "torso": {
                        **torso,
                        "base": {**base, **base_joint}
                    }
                }
            }
        }