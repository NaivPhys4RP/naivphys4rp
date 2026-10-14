import random
from typing import Dict, Any
from terminals import (
    TransformDefinition,
    HollowConeDimensions, ClosedConeDimensions,
    HollowSphereDimensions, ClosedSphereDimensions,
    HollowTorusDimensions, ClosedTorusDimensions
)
from shapes import ShapeFactory, ContainerAestheticDesign, ContainerStructuralDesign
import json

class SimplePrimitiveAssembler:
    @staticmethod
    def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a monolithic primitive.
        Uses 'outer_radius' for spheres to match terminal definitions.
        Randomizes any missing specifications.
        """
        # --- 1. EXTRACT SPECS WITH RANDOM FALLBACKS ---
        obj_class = spec.get("class") or random.choice(["cone", "torus", "sphere"])
        obj_class = obj_class.lower()

        obj_type = spec.get("type") or random.choice(["closed", "hollow"])
        obj_type = obj_type.lower()

        # Dimensions (m) - Randomly between 5cm and 30cm if missing
        width = spec.get("width") or random.uniform(0.05, 0.3)
        depth = spec.get("depth") or random.uniform(0.05, 0.3)
        height = spec.get("height") or random.uniform(0.05, 0.3)

        # Appearance & Physics
        is_partial = spec.get("partial") if "partial" in spec else random.choice([True, False])

        color = spec.get("color")
        if not color:
            color = [random.choice(["RED", "GREEN", "BLUE", "YELLOW", "WHITE", "BLACK", "SILVER"])]

        material = spec.get("material") or random.choice(["PLASTIC", "METAL", "WOOD", "GLASS"])
        mass = spec.get("mass") or random.uniform(0.1, 2.0)

        # --- 2. GEOMETRIC TRANSLATION ---
        # Radii are generally half of width/depth
        avg_radius = (width + depth) / 4.0

        aesthetic = ContainerAestheticDesign.generate(colors=color)
        structural = ContainerStructuralDesign.generate(material=material, density=mass)
        # Ground the object (Z=0 at the bottom)
        transform = TransformDefinition.generate(pos_z=height / 2.0)

        # --- 3. DYNAMIC DISPATCH ---
        try:
            if obj_class == "cone":
                # Cones can be cylinders (top=bottom) or tapered
                top_rad_mult = 1.0 if random.random() > 0.5 else random.uniform(0.0, 1.0)
                if obj_type == "hollow":
                    dims = HollowConeDimensions.generate(
                        height=height,
                        outer_bottom_radius=avg_radius,
                        outer_top_radius=avg_radius * top_rad_mult
                    )
                    primitive = ShapeFactory.generate_conical_hollow(dims, aesthetic, structural, transform)
                else:
                    dims = ClosedConeDimensions.generate(
                        height=height,
                        outer_bottom_radius=avg_radius,
                        outer_top_radius=avg_radius * top_rad_mult
                    )
                    primitive = ShapeFactory.generate_conical_closed(dims, aesthetic, structural, transform)

            elif obj_class == "sphere":
                # Use max dimension to ensure it fits the requested bounding box
                sphere_radius = max(width, depth, height) / 2.0
                if obj_type == "hollow":
                    # Corrected keyword to match terminal: 'outer_radius'
                    dims = HollowSphereDimensions.generate(outer_radius=sphere_radius)
                    primitive = ShapeFactory.generate_spherical_hollow(dims, aesthetic, structural, transform)
                else:
                    # Corrected keyword to match terminal: 'outer_radius'
                    dims = ClosedSphereDimensions.generate(outer_radius=sphere_radius)
                    primitive = ShapeFactory.generate_spherical_closed(dims, aesthetic, structural, transform)

            elif obj_class == "torus":
                major = avg_radius
                minor = min(height / 2.0, avg_radius / 3.0)
                arc = 360.0
                if is_partial:
                    arc = random.choice([90.0, 180.0, 270.0])

                if obj_type == "hollow":
                    dims = HollowTorusDimensions.generate(major_radius=major, minor_radius=minor, arc_degrees=arc)
                    primitive = ShapeFactory.generate_torus_hollow(dims, aesthetic, structural, transform)
                else:
                    dims = ClosedTorusDimensions.generate(major_radius=major, minor_radius=minor, arc_degrees=arc)
                    primitive = ShapeFactory.generate_torus_closed(dims, aesthetic, structural, transform)

            else:
                raise ValueError(f"Unknown primitive class: {obj_class}")

            # --- 4. COMPILE AND RETURN ---
            return {
                "scene_object": {
                    f"primitive_{obj_class}_{obj_type}": {
                        **primitive.compile(),
                        "metadata": {
                            "generated_class": obj_class,
                            "generated_type": obj_type,
                            "material": material,
                            "is_partial": is_partial
                        }
                    }
                }
            }

        except Exception as e:
            return {"error": f"Compilation failed in {obj_class}: {str(e)}"}


if __name__ == '__main__':
    assembler = SimplePrimitiveAssembler()
    # Test random generation with an empty spec
    print(json.dumps(assembler.generate({}), indent=4))