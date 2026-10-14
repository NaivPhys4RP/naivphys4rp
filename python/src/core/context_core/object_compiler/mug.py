import random
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, HollowConeDimensions, ClosedConeDimensions, ClosedTorusDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimpleMugAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        # Helper to get nested values or return None
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. TORSO (The Anchor / The Parent) ---
        t_spec = spec.get("torso", {})

        # Master Dimensions
        t_height = get_val(t_spec, "height") or 0.12
        t_radius = get_val(t_spec, "radius") or 0.05

        # Create dimensions object explicitly to control radii
        torso_dims = HollowConeDimensions.generate(
            height=t_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius
        )

        torso_aesthetic = ContainerAestheticDesign.generate(colors=get_val(t_spec, "color"))
        torso_structural = ContainerStructuralDesign.generate(
            material=get_val(t_spec, "material"),
            density=get_val(t_spec, "mass")
        )

        # Torso sits half-height up so its bottom is at Z=0
        torso = ShapeFactory.generate_conical_hollow(
            dimensions=torso_dims,
            aesthetics=torso_aesthetic,
            structural=torso_structural,
            transform=TransformDefinition.generate(pos_z=t_height / 2)
        ).compile()

        # --- 2. BASE (Child of Torso) ---
        b_spec = spec.get("base", {})

        # Height logic: default to 5% of torso height if spec is empty
        b_height_val = get_val(b_spec, "height")
        b_thickness_mult = 0.1 if b_height_val == "thick" else (0.02 if b_height_val == "thin" else 0.05)
        b_height = t_height * b_thickness_mult

        # FORCE base radius to match torso radius for a flush fit
        base_dims = ClosedConeDimensions.generate(
            height=b_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius
        )

        base = ShapeFactory.generate_conical_closed(
            dimensions=base_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(b_spec, "color")),
            structural=ContainerStructuralDesign.generate(material=get_val(b_spec, "material")),
            transform=TransformDefinition.generate(pos_z=0.0)
        ).compile()

        # Joint snaps base to the bottom center of the torso
        base_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_z=0.0,
            pos_x=0.0,
            pos_y=0.0
        ).compile()

        # --- 3. HANDLE (Child of Torso - Half Torus Fix) ---
        h_spec = spec.get("handle", {})

        # Explicitly setting arc_degrees to 180.0 for a half-torus handle
        # major_radius is derived from torso height to remain proportional
        handle_dims = ClosedTorusDimensions.generate(
            major_radius=t_height / 3.5,
            minor_radius=get_val(h_spec, "thickness") or 0.008,
            arc_degrees=180.0
        )

        handle = ShapeFactory.generate_torus_closed(
            dimensions=handle_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(h_spec, "color")),
            structural=ContainerStructuralDesign.generate(material=get_val(h_spec, "material")),
            transform=TransformDefinition.generate(
                pos_x=t_radius,      # Snapped to outer wall
                pos_z=t_height / 2,  # Centered vertically
                roll=0,              # Upright orientation
                pitch=1.57,
                yaw=1.57             # Rotate ends toward the torso
            )
        ).compile()

        # Joint matches the handle's relative transform for a stable weld
        handle_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_x=t_radius,
            pos_z=t_height / 2,
            roll=1.57,
            yaw=1.57
        ).compile()

        # --- FINAL NESTED ASSEMBLY ---
        return {
            "scene_object": {
                "simple_mug": {
                    "torso": {
                        **torso,
                        "base": {**base, **base_joint},
                        "handle": {**handle, **handle_joint}
                    }
                }
            }
        }


if __name__ == '__main__':
    mug_obj = SimpleMugAssembler()
    # Verification output
    import json
    print(json.dumps(mug_obj.generate({}), indent=4))