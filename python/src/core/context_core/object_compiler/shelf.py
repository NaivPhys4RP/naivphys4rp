import math
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, ClosedConeDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimpleShelfAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. SETTINGS & DIMENSIONS ---
        t_spec = spec.get("torso", {})
        t_height = get_val(t_spec, "height") or 1.2
        t_radius = get_val(t_spec, "radius") or 0.05  # Standard pillar thickness

        shelf_width = get_val(spec, "width") or 0.8
        shelf_depth = get_val(spec, "depth") or 0.4
        SEGMENTS = 30
        SEGMENTS_PLANK=4

        # Pillar Template Dimensions
        pillar_dims = ClosedConeDimensions.generate(
            height=t_height,
            outer_bottom_radius=t_radius,
            outer_top_radius=t_radius,
            segments=SEGMENTS
        )

        # Common Design for all pillars
        pillar_aesthetics = ContainerAestheticDesign.generate(colors=get_val(t_spec, "color"))
        pillar_structural = ContainerStructuralDesign.generate(
            material=get_val(t_spec, "material"),
            density=get_val(t_spec, "mass")
        )

        # --- 2. PILLAR GENERATION ---
        # Torso (The Anchor Pillar - Front Left)
        # Centered at t_height/2 so its base is at Z=0
        torso = ShapeFactory.generate_conical_closed(
            dimensions=pillar_dims,
            aesthetics=pillar_aesthetics,
            structural=pillar_structural,
            transform=TransformDefinition.generate(pos_z=t_height / 2)
        ).compile()

        # Other 3 Pillars (Duplicated structure, different transforms)
        corner_coords = [
            ("front_right", shelf_width, 0),
            ("back_left", 0, shelf_depth),
            ("back_right", shelf_width, shelf_depth)
        ]

        other_pillars = {}
        for name, px, py in corner_coords:
            pillar = ShapeFactory.generate_conical_closed(
                dimensions=pillar_dims,
                aesthetics=pillar_aesthetics,
                structural=pillar_structural,
                transform=TransformDefinition.generate(pos_x=px, pos_y=py, pos_z=0.0)
            ).compile()

            joint = JointDefinition.generate(
                joint_type="fixed", pos_x=px, pos_y=py, pos_z=0.0
            ).compile()
            other_pillars[f"pillar_{name}"] = {**pillar, **joint}

        # --- 3. RECTANGULAR PLANKS (Shifted within Pillar Length) ---
        p_spec = spec.get("plank", {})
        num_planks = get_val(p_spec, "count") or 3
        p_thickness = 0.02

        # Radius calculated to bridge centers; adjusted for pillar thickness
        plank_radius = (shelf_width / 2) + t_radius

        plank_dims = ClosedConeDimensions.generate(
            height=p_thickness,
            outer_bottom_radius=plank_radius,
            outer_top_radius=plank_radius,
            segments=SEGMENTS_PLANK
        )

        planks_dict = {}
        for i in range(num_planks):
            # Shifted within the pillar length:
            # Starts 0.1m from bottom, ends 0.1m from top
            z_pos = 0.1 + (i * (t_height - 0.2) / (max(1, num_planks - 1)))
            relative_z = z_pos - (t_height / 2)*0

            plank = ShapeFactory.generate_conical_closed(
                dimensions=plank_dims,
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(p_spec, "color")),
                structural=ContainerStructuralDesign.generate(
                    material=get_val(p_spec, "material"),
                    density=get_val(p_spec, "mass")
                ),
                transform=TransformDefinition.generate(
                    pos_x=shelf_width / 2,
                    pos_y=shelf_depth / 2,
                    pos_z=relative_z,
                    yaw=math.pi / 4  # Aligns 4-seg cone to rectangular grid
                )
            ).compile()

            plank_joint = JointDefinition.generate(
                joint_type="fixed",
                pos_x=shelf_width / 2,
                pos_y=shelf_depth / 2,
                pos_z=relative_z,
                yaw=math.pi / 4
            ).compile()

            planks_dict[f"plank_{i}"] = {**plank, **plank_joint}

        return {
            "scene_object": {
                "simple_shelf": {
                    "torso": {
                        **torso,
                        **other_pillars,
                        **planks_dict
                    }
                }
            }
        }


if __name__ == '__main__':
    shelf_obj = SimpleShelfAssembler()
    import json

    print(json.dumps(shelf_obj.generate({
        "torso": {"color": ["GRAY"], "height": 1.5, "radius": 0.06},
        "plank": {"count": 5, "color": ["BROWN"]}
    }), indent=4))