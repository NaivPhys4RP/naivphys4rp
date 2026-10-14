import math
import json
from typing import Dict, Any
from terminals import JointDefinition, TransformDefinition, ClosedConeDimensions, HollowConeDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign

class SimpleBottleAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. DIMENSIONS ---
        t_spec = spec.get("torso", {})
        b_spec = spec.get("base", {})
        n_spec = spec.get("neck", {})
        s_spec = spec.get("spout", {})
        c_spec = spec.get("cap", {})

        segments = get_val(t_spec, "segments") or 32

        t_h = get_val(t_spec, "height") or 0.2
        t_rb = get_val(t_spec, "bottom_radius") or 0.05
        t_rt = get_val(t_spec, "top_radius") or 0.05
        t_thick = get_val(t_spec, "thickness") or 0.002

        base_h = 0.01
        n_h = get_val(n_spec, "height") or 0.05
        n_rt = get_val(n_spec, "top_radius") or 0.015
        s_h = get_val(s_spec, "height") or 0.02
        cap_t_h = get_val(c_spec, "height") or 0.03
        cap_r = n_rt + 0.002
        cap_base_h = 0.005

        # --- 2. HIERARCHY CONSTRUCTION ---
        # Absolute Z for TransformDefinition (Renderer)
        # Relative Z for JointDefinition (Physics Compiler)

        # [5] CAP LID: Fixed to Cap Torso
        cap_lid_node = {
            **ShapeFactory.generate_conical_closed(
                dimensions=ClosedConeDimensions.generate(
                    height=cap_base_h, outer_bottom_radius=cap_r, outer_top_radius=cap_r, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(c_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(c_spec, "material")),
                transform=TransformDefinition.generate(pos_z=t_h + n_h + s_h + cap_t_h)
            ).compile(),
            # anchor at the TOP of the Cap Torso
            **JointDefinition.generate(joint_type="fixed", pos_z=cap_t_h).compile()
        }

        # [4] CAP TORSO: Prismatic on Spout
        cap_torso_node = {
            **ShapeFactory.generate_conical_hollow(
                dimensions=HollowConeDimensions.generate(
                    height=cap_t_h, inner_bottom_radius=cap_r - t_thick, outer_bottom_radius=cap_r,
                    inner_top_radius=cap_r - t_thick, outer_top_radius=cap_r, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(c_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(c_spec, "material")),
                transform=TransformDefinition.generate(pos_z=t_h + n_h + s_h)
            ).compile(),
            "child_lid": cap_lid_node,
            # anchor at the TOP of the Spout
            **JointDefinition.generate(joint_type="prismatic", pos_z=s_h).compile()
        }

        # [3] SPOUT: Fixed to Neck
        spout_node = {
            **ShapeFactory.generate_conical_hollow(
                dimensions=HollowConeDimensions.generate(
                    height=s_h, inner_bottom_radius=n_rt - t_thick, outer_bottom_radius=n_rt,
                    inner_top_radius=n_rt - t_thick, outer_top_radius=n_rt, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(s_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(s_spec, "material")),
                transform=TransformDefinition.generate(pos_z=t_h + n_h)
            ).compile(),
            "child_cap_assembly": cap_torso_node,
            # anchor at the TOP of the Neck
            **JointDefinition.generate(joint_type="fixed", pos_z=n_h).compile()
        }

        # [2] NECK: Fixed to Torso
        neck_node = {
            **ShapeFactory.generate_conical_hollow(
                dimensions=HollowConeDimensions.generate(
                    height=n_h, inner_bottom_radius=t_rt - t_thick, outer_bottom_radius=t_rt,
                    inner_top_radius=n_rt - t_thick, outer_top_radius=n_rt, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(n_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(n_spec, "material")),
                transform=TransformDefinition.generate(pos_z=t_h)
            ).compile(),
            "child_spout": spout_node,
            # anchor at the TOP of the Torso
            **JointDefinition.generate(joint_type="fixed", pos_z=t_h).compile()
        }

        # [1] BASE: Fixed to Torso (underneath)
        base_node = {
            **ShapeFactory.generate_conical_closed(
                dimensions=ClosedConeDimensions.generate(
                    height=base_h, outer_bottom_radius=t_rb, outer_top_radius=t_rb, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(b_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(b_spec, "material")),
                transform=TransformDefinition.generate(pos_z=-base_h)
            ).compile(),
            # anchor at the BOTTOM of the Torso
            **JointDefinition.generate(joint_type="fixed", pos_z=-base_h).compile()
        }

        # [0] TORSO: Root
        torso_node = {
            **ShapeFactory.generate_conical_hollow(
                dimensions=HollowConeDimensions.generate(
                    height=t_h, inner_bottom_radius=t_rb - t_thick, outer_bottom_radius=t_rb,
                    inner_top_radius=t_rt - t_thick, outer_top_radius=t_rt, segments=segments
                ),
                aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
                structural=ContainerStructuralDesign.generate(material=get_val(t_spec, "material")),
                transform=TransformDefinition.generate(pos_z=0)
            ).compile(),
            "part_base": base_node,
            "part_neck": neck_node
        }

        return {
            "scene_object": {
                "simple_bottle": {
                    "torso": torso_node
                }
            }
        }

if __name__ == '__main__':
    test_spec = {
        "torso": {"height": 0.2, "bottom_radius": 0.05, "top_radius": 0.03, "color": ["BLUE"]},
        "neck": {"height": 0.05, "top_radius": 0.02, "color": ["WHITE"]},
        "spout": {"height": 0.02, "color": ["WHITE"]},
        "cap": {"height": 0.03, "color": ["RED"]}
    }
    assembler = SimpleBottleAssembler()
    print(json.dumps(assembler.generate(test_spec), indent=4))