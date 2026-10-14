import random
import math
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, HollowConeDimensions, ClosedConeDimensions, \
    ClosedTorusDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimpleTableAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        # Helper to get nested values or return None
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. TORSO (The Support Surface / Tabletop) ---
        t_spec = spec.get("torso", {})
        t_height = get_val(t_spec, "thickness") or 0.03
        t_radius = get_val(t_spec, "radius") or 0.4

        torso_dims = ClosedConeDimensions.generate(
            height=t_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius
        )

        torso = ShapeFactory.generate_conical_closed(
            dimensions=torso_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
            structural=ContainerStructuralDesign.generate(
                material=get_val(t_spec, "material"),
                density=get_val(t_spec, "mass")
            ),
            # Tabletop is placed so its center is at 0.7m
            transform=TransformDefinition.generate(pos_z=0.7)
        ).compile()

        # --- 2. FEET (The Legs) ---
        f_spec = spec.get("feet", {})
        num_feet = get_val(f_spec, "count") or 4
        f_height = 0.7
        f_radius = get_val(f_spec, "radius") or 0.03

        foot_dims = ClosedConeDimensions.generate(
            height=f_height,
            outer_bottom_radius=f_radius,
            outer_top_radius=f_radius
        )

        foot_aesthetic = ContainerAestheticDesign.generate(colors=get_val(f_spec, "color"))
        foot_structural = ContainerStructuralDesign.generate(
            material=get_val(f_spec, "material"),
            density=get_val(f_spec, "mass")
        )

        feet_children = {}
        inset = t_radius * 0.7

        # THE FIX:
        # We need the TOP of the leg to be at the BOTTOM of the table.
        # Table center is 0 (relative to torso).
        # Bottom of table is -(t_height / 2).
        # To put the leg's TOP there, we move the leg's CENTER down by another -(f_height / 2).
        final_shift = -(t_height / 2)*0 - (f_height / 2)*0

        for i in range(num_feet):
            angle = (2 * math.pi / num_feet) * i
            lx = inset * math.cos(angle)
            ly = inset * math.sin(angle)

            # Assigning the shift to the transform
            foot = ShapeFactory.generate_conical_closed(
                dimensions=foot_dims,
                aesthetics=foot_aesthetic,
                structural=foot_structural,
                transform=TransformDefinition.generate(
                    pos_x=lx,
                    pos_y=ly,
                    pos_z=final_shift
                )
            ).compile()

            # The Joint MUST match the mesh center exactly to avoid the 'bisecting' behavior
            foot_joint = JointDefinition.generate(
                joint_type="fixed",
                pos_x=lx,
                pos_y=ly,
                pos_z=final_shift
            ).compile()

            feet_children[f"foot_{i}"] = {**foot, **foot_joint}

        return {
            "scene_object": {
                "simple_table": {
                    "torso": {
                        **torso,
                        **feet_children
                    }
                }
            }
        }

if __name__ == '__main__':
    table_obj = SimpleTableAssembler()
    import json
    print(json.dumps(table_obj.generate({}), indent=4))