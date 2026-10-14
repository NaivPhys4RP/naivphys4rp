import random
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, HollowConeDimensions, ClosedConeDimensions, \
    ClosedTorusDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimplePlateAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        # Helper to get nested values or return None
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. TORSO (The Main Dish) ---
        t_spec = spec.get("torso", {})
        t_height = get_val(t_spec, "height") or 0.015
        t_radius = get_val(t_spec, "radius") or 0.10

        torso_dims = HollowConeDimensions.generate(
            height=t_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius
        )

        torso = ShapeFactory.generate_conical_hollow(
            dimensions=torso_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
            structural=ContainerStructuralDesign.generate(material=get_val(t_spec, "material")),
            transform=TransformDefinition.generate(pos_z=t_height / 2)
        ).compile()

        # --- 2. NECK (The Flared Rim / Spout) ---
        n_spec = spec.get("neck", {})
        n_height = get_val(n_spec, "height") or 0.01
        # Flare adds to the existing torso radius
        n_radius_top = t_radius + (get_val(n_spec, "flare") or 0.04)

        neck_dims = HollowConeDimensions.generate(
            height=n_height,
            outer_bottom_radius=t_radius,  # Matches Torso Top
            outer_top_radius=n_radius_top
        )

        neck = ShapeFactory.generate_conical_hollow(
            dimensions=neck_dims,
            transform=TransformDefinition.generate(pos_z=t_height)
        ).compile()

        neck_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_z=t_height
        ).compile()

        # --- 3. BASE (The Bottom Closure - Now Flush) ---
        b_spec = spec.get("base", {})
        b_height = get_val(b_spec, "height") or 0.005

        # FIXED: Radius now matches t_radius exactly for a flush fit
        base_dims = ClosedConeDimensions.generate(
            height=b_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius
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
                "simple_plate": {
                    "torso": {
                        **torso,
                        "neck": {**neck, **neck_joint},
                        "base": {**base, **base_joint}
                    }
                }
            }
        }