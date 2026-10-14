# =========================================================================
# deep_containers.py
# =========================================================================

import random
import json
from dataclasses import dataclass, field
from typing import Union, Optional, List, Dict, Any

from functional_parts import *


# =========================================================================
# 1. DEEP CONTAINER CLASSES
# =========================================================================

@dataclass
class Mug(CompiledSymbol):
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition
    handles: List[Handle]
    handle_joints: List[JointDefinition]
    closure: Optional[Closure] = None
    closure_joint: Optional[JointDefinition] = None
    spout: Optional[Spout] = None
    spout_joint: Optional[JointDefinition] = None
    feet: Optional[Feet] = None
    feet_joint: Optional[JointDefinition] = None

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Mug":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Aperture
        ap_dims = ApertureDimensions.generate(radius=0.06, position_z=0.12)
        aperture = Aperture.generate(dimensions=ap_dims, aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.12)

        # Mandatory Handle(s)
        num_handles = random.randint(1, 2)
        handles = [Handle.generate(aesthetics=aesthetics, structural=structural) for _ in range(num_handles)]
        handle_joints = [JointDefinition.generate(joint_type="fixed", pos_x=0.07, pos_z=0.06) for _ in
                         range(num_handles)]

        # Optional Parts
        closure, closure_joint = (None, None)
        if random.random() < 0.3:
            closure = Closure.generate(aesthetics=aesthetics, structural=structural)
            closure_joint = JointDefinition.generate(joint_type="revolute", pos_z=0.12)

        spout, spout_joint = (None, None)
        if random.random() < 0.2:
            spout = Spout.generate(aesthetics=aesthetics, structural=structural)
            spout_joint = JointDefinition.generate(joint_type="fixed", pos_x=0.06, pos_z=0.1)

        feet, feet_joint = (None, None)
        if random.random() < 0.3:
            feet = Feet.generate(aesthetics=aesthetics, structural=structural)
            feet_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.0)

        return cls(body, aperture, aperture_joint, handles, handle_joints,
                   closure, closure_joint, spout, spout_joint, feet, feet_joint)

    def compile(self) -> Dict[str, Any]:
        inner = {
            "body": self.body.compile()["body"],
            "aperture": {**self.aperture.compile()["aperture"], **self.aperture_joint.compile()},
            "handle": [{**h.compile()["handle"], **j.compile()} for h, j in zip(self.handles, self.handle_joints)]
        }
        if self.closure: inner["closure"] = {**self.closure.compile()["closure"], **self.closure_joint.compile()}
        if self.spout: inner["spout"] = {**self.spout.compile()["spout"], **self.spout_joint.compile()}
        if self.feet: inner["feet"] = {**self.feet.compile()["feet"], **self.feet_joint.compile()}
        return {"mug": inner}


@dataclass
class Bowl(CompiledSymbol):
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition
    closure: Optional[Closure] = None
    closure_joint: Optional[JointDefinition] = None
    feet: Optional[Feet] = None
    feet_joint: Optional[JointDefinition] = None

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Bowl":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        body = Body.generate(aesthetics=aesthetics, structural=structural)
        aperture = Aperture.generate(dimensions=ApertureDimensions.generate(radius=0.1, position_z=0.08),
                                     aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.08)

        closure, closure_joint = (None, None)
        if random.random() < 0.2:
            closure = Closure.generate(aesthetics=aesthetics, structural=structural)
            closure_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.08)

        feet, feet_joint = (None, None)
        if random.random() < 0.4:
            feet = Feet.generate(aesthetics=aesthetics, structural=structural)
            feet_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.0)

        return cls(body, aperture, aperture_joint, closure, closure_joint, feet, feet_joint)

    def compile(self) -> Dict[str, Any]:
        inner = {
            "deep_body": self.body.compile()["body"],
            "aperture": {**self.aperture.compile()["aperture"], **self.aperture_joint.compile()}
        }
        if self.closure: inner["closure"] = {**self.closure.compile()["closure"], **self.closure_joint.compile()}
        if self.feet: inner["feet"] = {**self.feet.compile()["feet"], **self.feet_joint.compile()}
        return {"bowl": inner}


@dataclass
class Pot(CompiledSymbol):
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition
    handles: List[Handle]
    handle_joints: List[JointDefinition]
    closure: Optional[Closure] = None
    closure_joint: Optional[JointDefinition] = None
    feet: Optional[Feet] = None
    feet_joint: Optional[JointDefinition] = None

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Pot":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        body = Body.generate(aesthetics=aesthetics, structural=structural)
        aperture = Aperture.generate(dimensions=ApertureDimensions.generate(radius=0.15, position_z=0.2),
                                     aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.2)

        # Two handles for a pot
        handles = [Handle.generate(aesthetics=aesthetics, structural=structural) for _ in range(2)]
        handle_joints = [
            JointDefinition.generate(joint_type="fixed", pos_x=0.16, pos_z=0.15),
            JointDefinition.generate(joint_type="fixed", pos_x=-0.16, pos_z=0.15)
        ]

        closure, closure_joint = (None, None)
        if random.random() < 0.8:
            closure = Closure.generate(aesthetics=aesthetics, structural=structural)
            closure_joint = JointDefinition.generate(joint_type="revolute", pos_z=0.2)

        feet, feet_joint = (None, None)
        if random.random() < 0.3:
            feet = Feet.generate(aesthetics=aesthetics, structural=structural)
            feet_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.0)

        return cls(body, aperture, aperture_joint, handles, handle_joints, closure, closure_joint, feet, feet_joint)

    def compile(self) -> Dict[str, Any]:
        inner = {
            "body": self.body.compile()["body"],
            "aperture": {**self.aperture.compile()["aperture"], **self.aperture_joint.compile()},
            "handle": [{**h.compile()["handle"], **j.compile()} for h, j in zip(self.handles, self.handle_joints)]
        }
        if self.closure: inner["closure"] = {**self.closure.compile()["closure"], **self.closure_joint.compile()}
        if self.feet: inner["feet"] = {**self.feet.compile()["feet"], **self.feet_joint.compile()}
        return {"pot": inner}


@dataclass
class Bottle(CompiledSymbol):
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition
    closure: Closure
    closure_joint: JointDefinition
    spout: Spout
    spout_joint: JointDefinition

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Bottle":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        body = Body.generate(aesthetics=aesthetics, structural=structural)

        neck_z = 0.25
        ap_dims = ApertureDimensions.generate(radius=0.02, position_z=neck_z)
        aperture = Aperture.generate(dimensions=ap_dims, aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=neck_z)

        closure = Closure.generate(aesthetics=aesthetics, structural=structural)
        closure_joint = JointDefinition.generate(joint_type="revolute", pos_z=neck_z + 0.01)

        spout = Spout.generate(aesthetics=aesthetics, structural=structural)
        spout_joint = JointDefinition.generate(joint_type="fixed", pos_z=neck_z)

        return cls(body, aperture, aperture_joint, closure, closure_joint, spout, spout_joint)

    # In Bottle class
    def compile(self) -> Dict[str, Any]:
        closure_data = self.closure.compile()["closure"]
        joint_data = self.closure_joint.compile()

        # Push the joint data specifically into the lid's base
        if "lid" in closure_data and "base" in closure_data["lid"]:
            closure_data["lid"]["base"].update(joint_data)
        else:
            # Fallback if the closure is a single shape
            closure_data.update(joint_data)

        return {
            "bottle": {
                "deep_body": self.body.compile()["body"],
                "aperture": {**self.aperture.compile()["aperture"], **self.aperture_joint.compile()},
                "closure": closure_data,
                "spout": {**self.spout.compile()["spout"], **self.spout_joint.compile()}
            }
        }


# =========================================================================
# 2. TOP LEVEL FACTORY
# =========================================================================

class DeepContainerFactory:
    @staticmethod
    def generate() -> Dict[str, Any]:
        choice = random.choice([Mug, Bowl, Pot, Bottle])
        container_instance = choice.generate()
        return container_instance

    #def compile(self):
        return {"deep_container": self.container_instance.compile()}


if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 10
    samples = []
    for _ in range(nb_samples):
        symbol = DeepContainerFactory.generate()
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