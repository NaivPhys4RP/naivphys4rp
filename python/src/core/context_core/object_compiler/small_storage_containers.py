# =========================================================================
# small_storage_containers.py
# =========================================================================

import random
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from functional_parts import Body, Aperture
from shapes import ContainerAestheticDesign, ContainerStructuralDesign
from terminals import CompiledSymbol, JointDefinition, ApertureDimensions


# =========================================================================
# 1. SMALL STORAGE CONTAINER CLASSES
# =========================================================================

@dataclass
class Box(CompiledSymbol):
    """
    Matches Grammar:
    LBRACE BOX COLON LBRACE TORSO COLON conical_full_hollow_shape
    COMMA BASE COLON base_shape COMMA BOX_APERTURE COLON aperture RBRACE RBRACE
    """
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Box":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Generate the body (which contains the torso list and base)
        # Note: Body.generate uses ShapeFactory.generate_conical_hollow by default for torso
        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Box Aperture: Usually covers the top area
        z_top = 0.15  # Default height alignment
        aperture = Aperture.generate(
            dimensions=ApertureDimensions.generate(radius=0.05, position_z=z_top),
            aesthetics=aesthetics,
            structural=structural
        )
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=z_top)

        return cls(body=body, aperture=aperture, aperture_joint=aperture_joint)

    def compile(self) -> Dict[str, Any]:
        # Matches the 'box_functional_design' grammar structure
        body_compiled = self.body.compile()["body"]
        return {
            "box": {
                "torso": body_compiled["torso"],
                "base": body_compiled["base"],
                "box_aperture": {
                    **self.aperture.compile()["aperture"],
                    **self.aperture_joint.compile()
                }
            }
        }


# =========================================================================
# 2. TOP LEVEL FACTORY
# =========================================================================

class SmallStorageContainerFactory:
    @staticmethod
    def generate():
        """Matches 'start: LBRACE BOX_CONTAINER COLON small_storage_container RBRACE'"""
        aesthetics = ContainerAestheticDesign.generate()
        structural = ContainerStructuralDesign.generate()

        # Currently, 'box' is the primary small storage container
        container_instance = Box.generate(aesthetics=aesthetics, structural=structural)

        return container_instance


# =========================================================================
# TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 2
    samples = []
    for _ in range(nb_samples):
        symbol = SmallStorageContainerFactory.generate()
        if symbol:
            print(f"\nGenerated: {type(symbol).__name__}")
            sample = symbol.compile()
            sample = json.dumps(sample, indent=4)
            samples.append(sample)
            print(sample)

    for s in samples:
        try:
            parsed = json.loads(s)
            print(f" ✅ Valid JSON")
        except json.JSONDecodeError as e:
            print(f" ❌ Invalid JSON ({e})")