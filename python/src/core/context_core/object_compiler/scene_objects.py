# =========================================================================
# scene_objects.py
# =========================================================================

import random
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union

# Import the top-level generic classes
from generic_containers import GenericContainer
from generic_supports import GenericSupport

from shapes import ContainerAestheticDesign, ContainerStructuralDesign
from terminals import CompiledSymbol


@dataclass
class SceneObject(CompiledSymbol):
    """
    The 'start' symbol implementation.
    Matches Grammar: start: LBRACE SCENE_OBJECT COLON scene_object RBRACE
    """
    # scene_object is either a start_container or a start_support
    content: Union[GenericContainer, GenericSupport]

    @classmethod
    def generate(cls,
                 object_type: Optional[str] = None,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "SceneObject":
        """
        STAGE 1: GENERATE
        Unifies all sub-categories under one parametrizable call.
        """
        # 1. Global Parameter Initialization
        # Passing these down ensures the entire scene (container or support)
        # shares the same aesthetic/structural DNA if desired.
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # 2. Selection Logic
        if object_type == "container":
            instance = GenericContainer.generate(aesthetics=aesthetics, structural=structural)
        elif object_type == "support":
            instance = GenericSupport.generate(aesthetics=aesthetics, structural=structural)
        else:
            # Randomly pick between the two main grammar branches
            choice = random.choice([GenericContainer, GenericSupport])
            instance = choice.generate(aesthetics=aesthetics, structural=structural)

        return cls(content=instance)

    def compile(self) -> Dict[str, Any]:
        """
        STAGE 2: COMPILE
        Matches Grammar: SCENE_OBJECT: "\"scene_object\""
        """
        return {
            "scene_object": self.content.compile()
        }


# =========================================================================
# 3. GLOBAL ENTRY POINT (Main Start)
# =========================================================================


if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 1
    samples = []
    for _ in range(nb_samples):
        symbol = SceneObject.generate()
        if symbol:
            print(f"\nGenerated: {type(symbol).__name__}")
            sample = symbol.compile()
            sample = json.dumps(sample, indent=1)
            samples.append(sample)
            print(sample)

    for s in samples:
        try:
            parsed = json.loads(s)
            print(f" ✅ Valid JSON")
        except json.JSONDecodeError as e:
            print(f" ❌ Invalid JSON ({e})")