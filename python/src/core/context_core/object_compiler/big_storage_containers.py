# =========================================================================
# big_storage_containers.py
# =========================================================================

import random
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from functional_parts import Body, Aperture, Handle
from shapes import ContainerAestheticDesign, ContainerStructuralDesign, ShapeFactory
from terminals import CompiledSymbol, JointDefinition, ApertureDimensions


# =========================================================================
# 1. BIG STORAGE CONTAINER CLASSES
# =========================================================================

@dataclass
class ShelfSegment(CompiledSymbol):
    """
    Matches Grammar:
    LBRACE SHELF_SEGMENT COLON LBRACE TORSO COLON conical_full_hollow_shape
    COMMA BASE COLON base_shape COMMA SHELF_APERTURE COLON aperture RBRACE RBRACE
    """
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "ShelfSegment":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Body provides torso (list) and base
        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Shelf Aperture
        z_ap = 0.2
        aperture = Aperture.generate(
            dimensions=ApertureDimensions.generate(radius=0.1, position_z=z_ap),
            aesthetics=aesthetics,
            structural=structural
        )
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=z_ap)

        return cls(body=body, aperture=aperture, aperture_joint=aperture_joint)

    def compile(self) -> Dict[str, Any]:
        body_data = self.body.compile()["body"]
        return {
            "shelf_segment": {
                "torso": body_data["torso"],
                "base": body_data["base"],
                "shelf_aperture": {
                    **self.aperture.compile()["aperture"],
                    **self.aperture_joint.compile()
                }
            }
        }


@dataclass
class Shelf(CompiledSymbol):
    """Matches Grammar: shelf_body: LBRACK shelf_segment [COMMA shelf_body] RBRACK"""
    segments: List[ShelfSegment]

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Shelf":
        num_segments = random.randint(2, 5)
        segments = [ShelfSegment.generate(aesthetics, structural) for _ in range(num_segments)]
        return cls(segments=segments)

    def compile(self) -> Dict[str, Any]:
        return {
            "shelf": {
                "shelf_body": [seg.compile() for seg in self.segments]
            }
        }


@dataclass
class Drawer(CompiledSymbol):
    """
    Matches Grammar:
    LBRACE TORSO COLON conical_full_hollow_shape COMMA BASE COLON base_shape
    COMMA HANDLE COLON handle COMMA DRAWER_APERTURE COLON aperture RBRACE
    """
    body: Body
    handle: Handle
    handle_joint: JointDefinition
    aperture: Aperture
    aperture_joint: JointDefinition

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Drawer":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Mandatory Handle for Drawer
        handle = Handle.generate(aesthetics=aesthetics, structural=structural)
        handle_joint = JointDefinition.generate(joint_type="fixed", pos_x=0.1, pos_z=0.05)

        # Drawer Aperture
        aperture = Aperture.generate(aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.1)

        return cls(body=body, handle=handle, handle_joint=handle_joint,
                   aperture=aperture, aperture_joint=aperture_joint)

    def compile(self) -> Dict[str, Any]:
        body_data = self.body.compile()["body"]
        return {
            "drawer": {
                "torso": body_data["torso"],
                "base": body_data["base"],
                "handle": {
                    **self.handle.compile()["handle"],
                    **self.handle_joint.compile()
                },
                "shelf_aperture": {  # Keyed as shelf_aperture per your terminal definition
                    **self.aperture.compile()["aperture"],
                    **self.aperture_joint.compile()
                }
            }
        }


# =========================================================================
# 2. TOP LEVEL FACTORY
# =========================================================================

class BigStorageContainerFactory:
    @staticmethod
    def generate():
        """Matches start: LBRACE BIG_STORAGE_CONTAINER COLON big_storage_container RBRACE"""
        choice = random.choice([Shelf, Drawer])
        instance = choice.generate()
        return instance


# =========================================================================
# TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 2
    samples = []
    for _ in range(nb_samples):
        symbol = BigStorageContainerFactory.generate()
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