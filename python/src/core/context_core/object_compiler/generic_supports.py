# =========================================================================
# generic_supports.py
# =========================================================================

import random
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union

from functional_parts import Support, Feet
from shapes import ContainerAestheticDesign, ContainerStructuralDesign
from terminals import CompiledSymbol, JointDefinition


# =========================================================================
# 1. FURNITURE CLASSES
# =========================================================================

@dataclass
class Chair(CompiledSymbol):
    """
    Matches Grammar:
    LBRACE CHAIR COLON LBRACE SEAT_SUPPORT COLON support
    [COMMA BACK_SUPPORT COLON support] [COMMA FEET COLON feet_list] RBRACE RBRACE
    """
    seat_support: Support
    back_support: Optional[Support] = None
    feet: List[Feet] = field(default_factory=list)
    feet_joints: List[JointDefinition] = field(default_factory=list)

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Chair":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Mandatory Seat
        seat = Support.generate(aesthetics=aesthetics, structural=structural)

        # Optional Back Support (50% chance)
        back = None
        if random.random() > 0.5:
            back = Support.generate(aesthetics=aesthetics, structural=structural)

        # Optional Feet List (70% chance for 4 legs)
        feet_list = []
        feet_joints = []
        if random.random() > 0.3:
            for _ in range(4):
                f = Feet.generate(aesthetics=aesthetics, structural=structural)
                j = JointDefinition.generate(joint_type="fixed")
                feet_list.append(f)
                feet_joints.append(j)

        return cls(seat_support=seat, back_support=back, feet=feet_list, feet_joints=feet_joints)

    def compile(self) -> Dict[str, Any]:
        data = {
            "seat_surface": self.seat_support.compile()["support"]  # Changed key
        }
        if self.back_support:
            data["backrest_surface"] = self.back_support.compile()["support"]  # Changed key

        if self.feet:
            data["feet"] = [
                {**f.compile()["feet"], **j.compile()}
                for f, j in zip(self.feet, self.feet_joints)
            ]
        return {"chair": data}


@dataclass
class Table(CompiledSymbol):
    """
    Matches Grammar:
    LBRACE TABLE COLON LBRACE TABLE_SUPPORT COLON support [COMMA FEET COLON feet_list] RBRACE RBRACE
    """
    table_support: Support
    feet: List[Feet] = field(default_factory=list)
    feet_joints: List[JointDefinition] = field(default_factory=list)

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Table":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        table_top = Support.generate(aesthetics=aesthetics, structural=structural)

        feet_list = []
        feet_joints = []
        # Tables usually have legs
        for _ in range(4):
            feet_list.append(Feet.generate(aesthetics=aesthetics, structural=structural))
            feet_joints.append(JointDefinition.generate(joint_type="fixed"))

        return cls(table_support=table_top, feet=feet_list, feet_joints=feet_joints)

    def compile(self) -> Dict[str, Any]:
        data = {
            "table_support": self.table_support.compile()["support"]
        }
        if self.feet:
            data["feet"] = [
                {**f.compile()["feet"], **j.compile()}
                for f, j in zip(self.feet, self.feet_joints)
            ]
        return {"table": data}


# =========================================================================
# 2. START SYMBOL IMPLEMENTATION
# =========================================================================

@dataclass
class GenericSupport(CompiledSymbol):
    """
    The 'start_support' implementation.
    """
    furniture_instance: Union[Chair, Table]

    @classmethod
    def generate(cls,
                 furniture_type: Optional[str] = None,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "GenericSupport":
        """
        STAGE 1: GENERATE
        Handles the logic of picking and creating the furniture object.
        """
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        if furniture_type == "chair":
            instance = Chair.generate(aesthetics, structural)
        elif furniture_type == "table":
            instance = Table.generate(aesthetics, structural)
        else:
            instance = random.choice([Chair, Table]).generate(aesthetics, structural)

        return cls(furniture_instance=instance)

    def compile(self) -> Dict[str, Any]:
        """
        STAGE 2: COMPILE
        Matches Grammar: start_support: LBRACE SCENE_SUPPORT COLON furniture RBRACE
        """
        return {
            "scene_support": {
                "furniture": self.furniture_instance.compile()
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
        symbol = GenericSupport.generate()
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