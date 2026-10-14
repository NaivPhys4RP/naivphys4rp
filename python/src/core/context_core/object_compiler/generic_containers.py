# =========================================================================
# generic_containers.py
# =========================================================================

import random
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union

# Import Classes to ensure access to their specific .generate() and .compile()
from deep_containers import Mug, Bowl, Pot, Bottle
from flat_containers import Plate, Spoon
from big_storage_containers import Shelf, Drawer
from small_storage_containers import Box

from shapes import ContainerAestheticDesign, ContainerStructuralDesign
from terminals import CompiledSymbol


@dataclass
class GenericContainer(CompiledSymbol):
    """
    The 'start_container' implementation.
    This class holds the specific container instance and its category key.
    """
    category_key: str
    instance: CompiledSymbol

    @classmethod
    def generate(cls,
                 category: Optional[str] = None,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "GenericContainer":
        """
        STAGE 1: GENERATE (Parametrizable)
        Returns a GenericContainer object holding a specific sub-type.
        """
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Mapping categories to their possible classes
        mapping = {
            "deep_container": [Mug, Bowl, Pot, Bottle],
            "flat_container": [Plate, Spoon],
            "big_storage_container": [Shelf, Drawer],
            "small_storage_container": [Box]
        }

        if category is None:
            category = random.choice(list(mapping.keys()))

        # Pick a class from the chosen category
        chosen_class = random.choice(mapping[category])

        # Call the specific class's generate (Parametrizable)
        container_instance = chosen_class.generate(aesthetics=aesthetics, structural=structural)

        return cls(category_key=category, instance=container_instance)

    def compile(self) -> Dict[str, Any]:
        """
        STAGE 2: COMPILE
        Matches Grammar: start_container: LBRACE SCENE_CONTAINER COLON container RBRACE
        """
        return {
            "scene_container": {
                self.category_key: self.instance.compile()
            }
        }


# =========================================================================
# TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 2
    samples = []
    for _ in range(nb_samples):
        symbol = GenericContainer.generate()
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