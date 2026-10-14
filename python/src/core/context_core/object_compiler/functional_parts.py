# =========================================================================
# functional_parts.py
# =========================================================================

import random
import json
from dataclasses import dataclass, field
from typing import Union, Optional, List, Dict, Any

from shapes import *

# =========================================================================
# 1. APERTURE INFRASTRUCTURE
# =========================================================================

@dataclass
class NumberSegments(CompiledSymbol):
    """Matches grammar: LBRACE NUM_SEGMENTS COLON INT RBRACE"""
    count: int

    @classmethod
    def generate(cls, count: Optional[int] = None) -> "NumberSegments":
        return cls(count=count if count is not None else random.randint(3, 32))

    def compile(self) -> Dict[str, Any]:
        return {"num_segments": self.count}


@dataclass
class ApertureProfile(CompiledSymbol):
    profile_type: str  # "CIRCLE" or "POLYGON"
    segments: Optional[NumberSegments] = None

    @classmethod
    def generate(cls,
                 profile_type: Optional[str] = None,
                 segments: Optional[NumberSegments] = None) -> "ApertureProfile":
        if profile_type is None:
            profile_type = random.choice(["CIRCLE", "POLYGON"])

        if segments is None:
            if profile_type == "POLYGON":
                segments = NumberSegments.generate(count=random.randint(3, 8))
            else:
                segments = NumberSegments.generate(count=random.randint(32, 64))

        return cls(profile_type=profile_type, segments=segments)

    def compile(self) -> Dict[str, Any]:
        if self.profile_type == "CIRCLE":
            inner = "CIRCLE"
        else:
            inner = {"POLYGON": self.segments.compile()}
        return {"aperture_profile": inner}


@dataclass
class Aperture(CompiledSymbol):
    profile: ApertureProfile
    dimensions: ApertureDimensions
    shape: FullShape

    @classmethod
    def generate(cls,
                 profile: Optional[ApertureProfile] = None,
                 dimensions: Optional[ApertureDimensions] = None,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Aperture":

        profile = profile if profile else ApertureProfile.generate()
        dimensions = dimensions if dimensions else ApertureDimensions.generate()

        choice = random.choice(["conical", "spherical"])

        if choice == "conical":
            neck_dims = HollowConeDimensions(
                inner_top_radius=dimensions.radius,
                inner_bottom_radius=dimensions.radius,
                outer_top_radius=dimensions.radius + 0.005,
                outer_bottom_radius=dimensions.radius + 0.01,
                height=0.05
            )
            shape = ShapeFactory.generate_conical_hollow(dimensions=neck_dims, aesthetics=aesthetics, structural=structural)
        else:
            neck_dims = HollowSphereDimensions(
                inner_radius=dimensions.radius,
                outer_radius=dimensions.radius + 0.005
            )
            shape = ShapeFactory.generate_spherical_hollow(dimensions=neck_dims, aesthetics=aesthetics, structural=structural)

        return cls(profile=profile, dimensions=dimensions, shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {
            "aperture": {
                **self.profile.compile(),
                **self.dimensions.compile(),
                **self.shape.compile()
            }
        }

# =========================================================================
# 2. SUPPORT INFRASTRUCTURE
# =========================================================================

@dataclass
class Support(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 shape: Optional[FullShape] = None,
                 dimensions: Optional[Union[ClosedConeDimensions, ClosedSphereDimensions]] = None,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Support":
        if shape is None:
            choice = random.choice(["conical", "spherical"])
            if choice == "conical":
                dims = dimensions if isinstance(dimensions, ClosedConeDimensions) else None
                shape = ShapeFactory.generate_conical_closed(dimensions=dims, aesthetics=aesthetics, structural=structural)
            else:
                dims = dimensions if isinstance(dimensions, ClosedSphereDimensions) else None
                shape = ShapeFactory.generate_spherical_closed(dimensions=dims, aesthetics=aesthetics, structural=structural)

        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"support": self.shape.compile()}


# =========================================================================
# 3. CLOSURE SUPPORTING CLASSES
# =========================================================================

@dataclass
class Handle(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Handle":
        choice = random.choice(["conical", "spherical", "torus"])
        if choice == "conical":
            shape = ShapeFactory.generate_conical_closed(aesthetics=aesthetics, structural=structural)
        elif choice == "spherical":
            shape = ShapeFactory.generate_spherical_closed(aesthetics=aesthetics, structural=structural)
        else:
            shape = ShapeFactory.generate_torus_closed(aesthetics=aesthetics, structural=structural)
        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"handle": self.shape.compile()}


@dataclass
class BaseShape(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "BaseShape":
        choice = random.choice(["conical", "spherical"])
        if choice == "conical":
            shape = ShapeFactory.generate_conical_closed(aesthetics=aesthetics, structural=structural)
        else:
            shape = ShapeFactory.generate_spherical_closed(aesthetics=aesthetics, structural=structural)
        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"base": self.shape.compile()}


@dataclass
class ClosureStopper(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "ClosureStopper":
        choice = random.choice(["conical", "spherical"])
        if choice == "conical":
            shape = ShapeFactory.generate_conical_closed(aesthetics=aesthetics, structural=structural)
        else:
            shape = ShapeFactory.generate_spherical_closed(aesthetics=aesthetics, structural=structural)
        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"stopper": self.shape.compile()}


@dataclass
class ClosureLid(CompiledSymbol):
    torso: FullShape
    base: BaseShape
    base_joint: JointDefinition
    handle: Optional[Handle] = None
    handle_joint: Optional[JointDefinition] = None

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "ClosureLid":
        choice = random.choice(["conical", "spherical"])
        if choice == "conical":
            torso = ShapeFactory.generate_conical_closed(aesthetics=aesthetics, structural=structural)
        else:
            torso = ShapeFactory.generate_spherical_closed(aesthetics=aesthetics, structural=structural)

        base = BaseShape.generate(aesthetics=aesthetics, structural=structural)
        base_joint = JointDefinition.generate(joint_type="fixed", pos_z=-0.01)

        handle = None
        handle_joint = None
        if random.random() < 0.7:
            handle = Handle.generate(aesthetics=aesthetics, structural=structural)
            handle_joint = JointDefinition.generate(joint_type=random.choice(["fixed", "revolute", "prismatic"]), pos_z=0.08)

        return cls(torso=torso, base=base, base_joint=base_joint, handle=handle, handle_joint=handle_joint)

    def compile(self) -> Dict[str, Any]:
        lid_data = {
            "torso": self.torso.compile(),
            "base": {**self.base.compile()["base"], **self.base_joint.compile()}
        }
        if self.handle:
            lid_data["handle"] = {**self.handle.compile()["handle"], **self.handle_joint.compile()}
        return {"lid": lid_data}


@dataclass
class Closure(CompiledSymbol):
    part: Union[ClosureLid, ClosureStopper]

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Closure":
        choice = random.choice([ClosureLid, ClosureStopper])
        return cls(part=choice.generate(aesthetics=aesthetics, structural=structural))

    def compile(self) -> Dict[str, Any]:
        return {"closure": self.part.compile()}


# =========================================================================
# 4. FEET INFRASTRUCTURE
# =========================================================================

@dataclass
class Feet(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 reference_radius: float = 0.1,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Feet":

        foot_radius = reference_radius * 0.15
        foot_height = reference_radius * 0.5
        choice = random.choice(["conical", "spherical", "torus"])

        if choice == "conical":
            dims = ClosedConeDimensions(
                outer_bottom_radius=foot_radius,
                outer_top_radius=foot_radius * 0.7,
                height=foot_height
            )
            shape = ShapeFactory.generate_conical_closed(dimensions=dims, aesthetics=aesthetics, structural=structural)
        elif choice == "spherical":
            # FIX: Use 'outer_radius' as defined in terminals.py
            dims = ClosedSphereDimensions(outer_radius=foot_radius)
            shape = ShapeFactory.generate_spherical_closed(dimensions=dims, aesthetics=aesthetics, structural=structural)
        else:
            dims = ClosedTorusDimensions(major_radius=foot_radius, minor_radius=foot_radius * 0.3)
            shape = ShapeFactory.generate_torus_closed(dimensions=dims, aesthetics=aesthetics, structural=structural)

        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"feet": self.shape.compile()}

# =========================================================================
# 5. SPOUT INFRASTRUCTURE
# =========================================================================

@dataclass
class Spout(CompiledSymbol):
    shape: FullShape

    @classmethod
    def generate(cls,
                 reference_radius: float = 0.1,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Spout":

        spout_radius = reference_radius * 0.2
        spout_height = reference_radius * 0.8
        choice = random.choice(["conical", "torus"])

        if choice == "conical":
            dims = HollowConeDimensions(
                inner_bottom_radius=spout_radius * 0.8,
                inner_top_radius=spout_radius * 0.6,
                outer_bottom_radius=spout_radius,
                outer_top_radius=spout_radius * 0.8,
                height=spout_height
            )
            shape = ShapeFactory.generate_conical_hollow(dimensions=dims, aesthetics=aesthetics, structural=structural)
        else:
            dims = HollowTorusDimensions(major_radius=spout_radius * 2, minor_radius=spout_radius * 0.5)
            shape = ShapeFactory.generate_torus_hollow(dimensions=dims, aesthetics=aesthetics, structural=structural)

        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"spout": self.shape.compile()}


@dataclass
class BodyHollowPart(CompiledSymbol):
    """
    body_hollow_part : LBRACE TORSO COLON (conical_hollow | spherical_hollow | torus_hollow) RBRACE
    """
    shape: FullShape

    @classmethod
    def generate(cls,
                 height: float = 0.1,
                 radius: float = 0.05,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "BodyHollowPart":

        choice = random.choice(["conical", "spherical", "torus"])

        if choice == "conical":
            dims = HollowConeDimensions(
                inner_bottom_radius=radius * 0.9,
                inner_top_radius=radius * 0.9,
                outer_bottom_radius=radius,
                outer_top_radius=radius,
                height=height
            )
            shape = ShapeFactory.generate_conical_hollow(dims, aesthetics, structural)
        elif choice == "spherical":
            dims = HollowSphereDimensions(
                outer_radius=radius,
                inner_radius=radius * 0.9,
                start_latitude_deg=0.0,
                end_latitude_deg=180.0
            )
            shape = ShapeFactory.generate_spherical_hollow(dims, aesthetics, structural)
        else:  # torus
            dims = HollowTorusDimensions(
                major_radius=radius,
                minor_radius=radius * 0.2
            )
            shape = ShapeFactory.generate_torus_hollow(dims, aesthetics, structural)

        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"torso": self.shape.compile()}

# =========================================================================
# BODY INFRASTRUCTURE
# =========================================================================

@dataclass
class Body(CompiledSymbol):
    """
    body: LBRACE BODY COLON LBRACE
          TORSO COLON LBRACK body_hollow_part (COMMA body_hollow_part)* RBRACK COMMA
          BASE COLON base_shape
          RBRACE RBRACE
    """
    torsos: List[BodyHollowPart]
    joints: List[JointDefinition]
    base: BaseShape
    base_joint: JointDefinition

    @classmethod
    def generate(cls,
                 aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Body":

        # 1. Generate the Stack of Torsos
        num_segments = random.randint(1, 3)
        torsos = []
        joints = []

        current_z = 0.0
        base_radius = 0.05

        for i in range(num_segments):
            seg_height = random.uniform(0.05, 0.1)
            part = BodyHollowPart.generate(height=seg_height, radius=base_radius,
                                           aesthetics=aesthetics, structural=structural)

            # The first part is at origin, subsequent parts stack on top
            joint = JointDefinition.generate(joint_type="fixed", pos_z=current_z)

            torsos.append(part)
            joints.append(joint)
            current_z += seg_height

        # 2. Generate the Solid Base
        # Per grammar: base_shape : conical_closed | spherical_closed
        base = BaseShape.generate(aesthetics=aesthetics, structural=structural)

        # The base is usually attached to the bottom of the first torso segment
        base_joint = JointDefinition.generate(joint_type="fixed", pos_z=-0.01)

        return cls(torsos=torsos, joints=joints, base=base, base_joint=base_joint)

    def compile(self) -> Dict[str, Any]:
        # Compile all torso parts with their respective joints
        torso_list = []
        for part, joint in zip(self.torsos, self.joints):
            compiled_part = part.compile()["torso"]
            # Inject joint into the shape data
            compiled_part.update(joint.compile())
            torso_list.append(compiled_part)

        return {
            "body": {
                "torso": torso_list,
                "base": {
                    **self.base.compile()["base"],
                    **self.base_joint.compile()
                }
            }
        }

@dataclass
class HandleSpoon(CompiledSymbol):
    """Specifically for flat containers like spoons."""
    shape: FullShape

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "HandleSpoon":
        # Using the exact parameter names from terminals.py
        dims = ClosedConeDimensions.generate(
            outer_bottom_radius=0.005,
            outer_top_radius=0.005,
            height=0.15
        )
        shape = ShapeFactory.generate_conical_closed(
            dimensions=dims,
            aesthetics=aesthetics,
            structural=structural
        )
        return cls(shape=shape)

    def compile(self) -> Dict[str, Any]:
        return {"handle": self.shape.compile()}

# =========================================================================
# LOCAL TESTING FACTORY
# =========================================================================

class FunctionalFactory:
    @staticmethod
    def generate() -> CompiledSymbol:
        choices = [Support, Aperture, Closure, Handle, Feet, Spout, Body, HandleSpoon]
        return random.choice(choices).generate()



# =========================================================================
# TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 10
    samples = []
    for _ in range(nb_samples):
        symbol = FunctionalFactory.generate()
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