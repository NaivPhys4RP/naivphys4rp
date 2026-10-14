import math
from typing import Dict, Any, Optional
from terminals import JointDefinition, TransformDefinition, HollowSphereDimensions, ClosedConeDimensions
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign


class SimpleSpoonAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        get_val = lambda d, k: d.get(k) if d else None

        # --- 1. SETTINGS & DIMENSIONS ---
        t_spec = spec.get("torso", {})  # The Bowl Ring
        h_spec = spec.get("handle", {})  # The Long Handle

        t_radius = get_val(t_spec, "radius") or 0.03
        t_start_lat = get_val(t_spec, "start_lat") or 30.0
        t_end_lat = get_val(t_spec, "end_lat") or 60.0

        # Mechanical Calculation for the Base Plug
        # Opening radius at the bottom of the ring
        b_radius = t_radius * math.sin(math.radians(t_start_lat))
        b_height = 0.0002  # Thin flat disk

        # Vertical position of that opening relative to sphere center
        # (Z-axis offset to meet the ring bottom)
        b_pos_z = t_radius * math.cos(math.radians(t_start_lat))

        # Handle Dimensions
        h_length = get_val(h_spec, "length") or 0.1
        h_radius = get_val(h_spec, "radius") or 0.003

        # --- 2. HANDLE SURFACE TRANSLATION CALCULATIONS ---
        # Calculate X and Z coordinates for the surface at t_end_lat
        lat_rad = math.radians(t_end_lat)

        # Z coordinate: Vertical height of the ring's top edge
        h_trans_z = t_radius * math.cos(lat_rad)

        # X coordinate: Radial distance at that height + half length to sit on surface
        surface_radius = t_radius * math.sin(lat_rad)
        h_trans_x = surface_radius + (h_length / 2)*0

        # --- 2. GEOMETRY DEFINITIONS ---
        bowl_dims = HollowSphereDimensions.generate(
            outer_radius=t_radius,
            inner_radius=t_radius - 0.002,
            start_latitude_deg=t_start_lat,
            end_latitude_deg=t_end_lat,
            segments=32,
            rings=16
        )

        base_dims = ClosedConeDimensions.generate(
            height=b_height,
            outer_bottom_radius=b_radius,
            outer_top_radius=b_radius,
            segments=32
        )

        handle_dims = ClosedConeDimensions.generate(
            height=h_length,
            outer_bottom_radius=h_radius,
            outer_top_radius=h_radius*1.5,
            segments=16
        )

        # --- 3. GENERATION ---
        # TORSO: The Hollow Ring
        torso = ShapeFactory.generate_spherical_hollow(
            dimensions=bowl_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
            structural=ContainerStructuralDesign.generate(material="STEEL"),
            transform=TransformDefinition.generate(pos_z=0.0)
        ).compile()

        # BASE: The plug directly below/at the bottom of the torso ring
        base = ShapeFactory.generate_conical_closed(
            dimensions=base_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(t_spec, "color")),
            structural=ContainerStructuralDesign.generate(material="STEEL"),
            transform=TransformDefinition.generate(pos_z=b_pos_z)
        ).compile()

        base_joint = JointDefinition.generate(
            joint_type="fixed", pos_z=b_pos_z
        ).compile()

        # HANDLE: Attached to Torso with 0 0 0 rotation
        # Shifted to the edge of the bowl radius
        h_pos_y = t_radius
        handle = ShapeFactory.generate_conical_closed(
            dimensions=handle_dims,
            aesthetics=ContainerAestheticDesign.generate(colors=get_val(h_spec, "color")),
            structural=ContainerStructuralDesign.generate(material="STEEL"),
            transform=TransformDefinition.generate(
                pos_y=0.0,
                pos_z=h_trans_z,
                pos_x=h_trans_x,
                roll=1.57, pitch=0.0, yaw=1.57  # Clean rotation baseline
            )
        ).compile()

        handle_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_y=0.0,
            pos_z=h_trans_z,
            pos_x=h_trans_x,
            roll=1.57, pitch=0.0, yaw=1.57  # Clean rotation baseline
        ).compile()

        return {
            "scene_object": {
                "mechanical_spoon": {
                    "torso": {
                        **torso,
                        "base": {**base, **base_joint},
                        "handle": {**handle, **handle_joint}
                    }
                }
            }
        }


if __name__ == '__main__':
    spoon_obj = SimpleSpoonAssembler()
    import json

    # Corrected relation: Base radius will be R * sin(15°)
    print(json.dumps(spoon_obj.generate({
        "torso": {"color": ["SILVER"], "start_lat": 15, "end_lat": 45},
        "handle": {"color": ["SILVER"]}
    }), indent=4))