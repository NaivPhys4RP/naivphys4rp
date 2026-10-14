import random
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


# =========================================================================
# 1. BASE COMPILER INTERFACE
# =========================================================================

@dataclass
class CompiledSymbol:
    def compile(self) -> Dict[str, Any]:
        """Default compiler for Dimension symbols."""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return {"dimensions": data}


# =========================================================================
# 2. DIMENSION SYMBOLS (Full Mirror + Proper Randomization)
# =========================================================================

@dataclass
class ApertureDimensions(CompiledSymbol):
    radius: Optional[float] = None
    position_z: Optional[float] = None

    @classmethod
    def generate(cls, radius: Optional[float] = None, position_z: Optional[float] = None) -> "ApertureDimensions":
        return cls(
            radius=radius if radius is not None else random.uniform(0.01, 0.05),
            position_z=position_z if position_z is not None else random.uniform(0.1, 0.3)
        )


@dataclass
class HollowSphereDimensions(CompiledSymbol):
    outer_radius: Optional[float] = None
    inner_radius: Optional[float] = None
    start_latitude_deg: Optional[float] = None
    end_latitude_deg: Optional[float] = None
    segments: Optional[int] = None
    rings: Optional[int] = None

    @classmethod
    def generate(cls, outer_radius: Optional[float] = None, inner_radius: Optional[float] = None,
                 start_latitude_deg: Optional[float] = None, end_latitude_deg: Optional[float] = None,
                 segments: Optional[int] = None, rings: Optional[int] = None) -> "HollowSphereDimensions":
        r_out = outer_radius if outer_radius is not None else random.uniform(0.05, 0.15)
        r_in = inner_radius if inner_radius is not None else r_out * 0.9
        return cls(
            outer_radius=r_out,
            inner_radius=r_in,
            start_latitude_deg=start_latitude_deg if start_latitude_deg is not None else 0.0,
            end_latitude_deg=end_latitude_deg if end_latitude_deg is not None else 180.0,
            segments=segments if segments is not None else random.randint(16, 64),
            rings=rings if rings is not None else random.randint(8, 32)
        )


@dataclass
class ClosedSphereDimensions(CompiledSymbol):
    outer_radius: Optional[float] = None
    start_latitude_deg: Optional[float] = None
    end_latitude_deg: Optional[float] = None
    segments: Optional[int] = None
    rings: Optional[int] = None

    @classmethod
    def generate(cls, outer_radius: Optional[float] = None, start_latitude_deg: Optional[float] = None,
                 end_latitude_deg: Optional[float] = None, segments: Optional[int] = None,
                 rings: Optional[int] = None) -> "ClosedSphereDimensions":
        return cls(
            outer_radius=outer_radius if outer_radius is not None else random.uniform(0.05, 0.15),
            start_latitude_deg=start_latitude_deg if start_latitude_deg is not None else 0.0,
            end_latitude_deg=end_latitude_deg if end_latitude_deg is not None else 180.0,
            segments=segments if segments is not None else random.randint(16, 64),
            rings=rings if rings is not None else random.randint(8, 32)
        )


@dataclass
class HollowConeDimensions(CompiledSymbol):
    outer_bottom_radius: Optional[float] = None
    outer_top_radius: Optional[float] = None
    height: Optional[float] = None
    inner_bottom_radius: Optional[float] = None
    inner_top_radius: Optional[float] = None
    segments: Optional[int] = None
    rings: Optional[int] = None

    @classmethod
    def generate(cls, outer_bottom_radius: Optional[float] = None, outer_top_radius: Optional[float] = None,
                 height: Optional[float] = None, inner_bottom_radius: Optional[float] = None,
                 inner_top_radius: Optional[float] = None, segments: Optional[int] = None,
                 rings: Optional[int] = None) -> "HollowConeDimensions":
        h = height if height is not None else random.uniform(0.1, 0.4)
        rb = outer_bottom_radius if outer_bottom_radius is not None else random.uniform(0.03, 0.08)
        rt = outer_top_radius if outer_top_radius is not None else rb
        return cls(
            outer_bottom_radius=rb,
            outer_top_radius=rt,
            height=h,
            inner_bottom_radius=inner_bottom_radius if inner_bottom_radius is not None else rb - 0.005,
            inner_top_radius=inner_top_radius if inner_top_radius is not None else rt - 0.005,
            segments=segments if segments is not None else random.randint(16, 48),
            rings=rings if rings is not None else random.randint(2, 12)
        )


@dataclass
class ClosedConeDimensions(CompiledSymbol):
    outer_bottom_radius: Optional[float] = None
    outer_top_radius: Optional[float] = None
    height: Optional[float] = None
    segments: Optional[int] = None
    rings: Optional[int] = None

    @classmethod
    def generate(cls, outer_bottom_radius: Optional[float] = None, outer_top_radius: Optional[float] = None,
                 height: Optional[float] = None, segments: Optional[int] = None,
                 rings: Optional[int] = None) -> "ClosedConeDimensions":
        rb = outer_bottom_radius if outer_bottom_radius is not None else random.uniform(0.03, 0.08)
        return cls(
            outer_bottom_radius=rb,
            outer_top_radius=outer_top_radius if outer_top_radius is not None else rb,
            height=height if height is not None else random.uniform(0.1, 0.4),
            segments=segments if segments is not None else random.randint(16, 48),
            rings=rings if rings is not None else random.randint(2, 12)
        )


@dataclass
class HollowTorusDimensions(CompiledSymbol):
    major_radius: Optional[float] = None
    minor_radius: Optional[float] = None
    inner_radius: Optional[float] = None
    arc_degrees: Optional[float] = None
    major_segments: Optional[int] = None
    minor_segments: Optional[int] = None

    @classmethod
    def generate(cls, major_radius: Optional[float] = None, minor_radius: Optional[float] = None,
                 inner_radius: Optional[float] = None, arc_degrees: Optional[float] = None,
                 major_segments: Optional[int] = None, minor_segments: Optional[int] = None) -> "HollowTorusDimensions":
        mj_r = major_radius if major_radius is not None else random.uniform(0.08, 0.15)
        mi_r = minor_radius if minor_radius is not None else random.uniform(0.02, 0.04)
        return cls(
            major_radius=mj_r,
            minor_radius=mi_r,
            inner_radius=inner_radius if inner_radius is not None else mi_r * 0.7,
            arc_degrees=arc_degrees if arc_degrees is not None else 360.0,
            major_segments=major_segments if major_segments is not None else random.randint(24, 64),
            minor_segments=minor_segments if minor_segments is not None else random.randint(12, 32)
        )


@dataclass
class ClosedTorusDimensions(CompiledSymbol):
    major_radius: Optional[float] = None
    minor_radius: Optional[float] = None
    arc_degrees: Optional[float] = None
    major_segments: Optional[int] = None
    minor_segments: Optional[int] = None

    @classmethod
    def generate(cls, major_radius: Optional[float] = None, minor_radius: Optional[float] = None,
                 arc_degrees: Optional[float] = None, major_segments: Optional[int] = None,
                 minor_segments: Optional[int] = None) -> "ClosedTorusDimensions":
        return cls(
            major_radius=major_radius if major_radius is not None else random.uniform(0.08, 0.15),
            minor_radius=minor_radius if minor_radius is not None else random.uniform(0.02, 0.04),
            arc_degrees=arc_degrees if arc_degrees is not None else 360.0,
            major_segments=major_segments if major_segments is not None else random.randint(24, 64),
            minor_segments=minor_segments if minor_segments is not None else random.randint(12, 32)
        )


# =========================================================================
# 3. TRANSFORM & JOINT SYMBOLS
# =========================================================================

@dataclass
class BaseTransform(CompiledSymbol):
    """The base spatial definition (Position and Rotation)."""
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def compile(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OffsetTransform(BaseTransform):
    """Used for joint offsets. Inherits Pos/Rot only."""
    pass


@dataclass
class TransformDefinition(BaseTransform):
    """Link Transform adding Scale for extrinsic geometry manipulation."""
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

    @classmethod
    def generate(cls, pos_x: Optional[float] = None, pos_y: Optional[float] = None, pos_z: Optional[float] = None,
                 roll: Optional[float] = None, pitch: Optional[float] = None, yaw: Optional[float] = None,
                 scale_x: Optional[float] = None, scale_y: Optional[float] = None, scale_z: Optional[float] = None) -> "TransformDefinition":
        return cls(
            pos_x=pos_x if pos_x is not None else 0.0,
            pos_y=pos_y if pos_y is not None else 0.0,
            pos_z=pos_z if pos_z is not None else 0.0,
            roll=roll if roll is not None else 0.0,
            pitch=pitch if pitch is not None else 0.0,
            yaw=yaw if yaw is not None else 0.0,
            scale_x=scale_x if scale_x is not None else 1.0,
            scale_y=scale_y if scale_y is not None else 1.0,
            scale_z=scale_z if scale_z is not None else 1.0
        )


@dataclass
class JointLimits(CompiledSymbol):
    lower: float = 0.0
    upper: float = 0.0

    @classmethod
    def generate(cls, lower: Optional[float] = None, upper: Optional[float] = None) -> "JointLimits":
        return cls(
            lower=lower if lower is not None else random.uniform(-3.14, -0.5),
            upper=upper if upper is not None else random.uniform(0.5, 3.14)
        )

    def compile(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JointDefinition(CompiledSymbol):
    source_face: str = "outside"
    target_face: str = "outside"
    joint_type: str = "fixed"
    alignment_algorithm: str = "PYMESH_NORMAL_CENTROID_LOGIC"
    offset: OffsetTransform = field(default_factory=OffsetTransform)
    limits: Optional[JointLimits] = None
    max_force: float = 0.0
    friction: float = 0.5
    velocity_limit: float = 0.0
    break_torque: float = 0.0
    break_force: float = 0.0

    @classmethod
    def generate(cls, source_face: Optional[str] = None, target_face: Optional[str] = None,
                 joint_type: Optional[str] = None, alignment_algorithm: Optional[str] = None,
                 pos_x: Optional[float] = None, pos_y: Optional[float] = None, pos_z: Optional[float] = None,
                 roll: Optional[float] = None, pitch: Optional[float] = None, yaw: Optional[float] = None,
                 limits: Optional[JointLimits] = None,
                 max_force: Optional[float] = None, friction: Optional[float] = None,
                 velocity_limit: Optional[float] = None, break_torque: Optional[float] = None,
                 break_force: Optional[float] = None, probability: float = 1.0) -> Optional["JointDefinition"]:
        if pos_z is None and random.random() > probability:
            return None

        j_type = joint_type if joint_type is not None else random.choice(["fixed", "revolute", "prismatic"])
        #j_type = random.choice(["fixed", "revolute", "prismatic"])
        return cls(
            source_face=source_face if source_face is not None else "outside",
            target_face=target_face if target_face is not None else "outside",
            joint_type=j_type,
            alignment_algorithm=alignment_algorithm if alignment_algorithm is not None else "PYMESH_NORMAL_CENTROID_LOGIC",
            offset=OffsetTransform(
                pos_x=pos_x if pos_x is not None else random.uniform(-0.02, 0.02),
                pos_y=pos_y if pos_y is not None else random.uniform(-0.02, 0.02),
                pos_z=pos_z if pos_z is not None else random.uniform(0.05, 0.25),
                roll=roll if roll is not None else random.uniform(0, 3.14),
                pitch=pitch if pitch is not None else 0.0,
                yaw=yaw if yaw is not None else 0.0
            ),
            limits=limits if limits is not None else (JointLimits.generate() if j_type != "fixed" else None),
            max_force=max_force if max_force is not None else random.uniform(100.0, 500.0),
            friction=friction if friction is not None else random.uniform(0.1, 1.0),
            velocity_limit=velocity_limit if velocity_limit is not None else random.uniform(1.0, 5.0),
            break_torque=break_torque if break_torque is not None else random.uniform(50.0, 200.0),
            break_force=break_force if break_force is not None else random.uniform(500.0, 2000.0)
        )

    def compile(self) -> Dict[str, Any]:
        return {
            "joint": {
                "alignment": {
                    "source_face": self.source_face,
                    "target_face": self.target_face,
                    "alignment_algorithm": self.alignment_algorithm,
                    "offset_transform": self.offset.compile()
                },
                "kinematic": {
                    "type": self.joint_type,
                    "limits": self.limits.compile() if self.limits else None
                },
                "dynamic": {
                    "max_force": self.max_force,
                    "friction": self.friction,
                    "velocity_limit": self.velocity_limit,
                    "break_torque": self.break_torque,
                    "break_force": self.break_force
                }
            }
        }


# =========================================================================
# 4. THE START SYMBOL
# =========================================================================

class TerminalFactory:
    @staticmethod
    def generate() -> CompiledSymbol:
        choices = [
            ApertureDimensions, HollowSphereDimensions, ClosedSphereDimensions,
            HollowConeDimensions, ClosedConeDimensions, HollowTorusDimensions,
            ClosedTorusDimensions, JointDefinition, TransformDefinition
        ]
        return random.choice(choices).generate()


if __name__ == "__main__":
    nb_samples=6
    samples=[]
    for _ in range(nb_samples):
        symbol = TerminalFactory.generate()
        if symbol:
            print(f"\nGenerated: {type(symbol).__name__}")
            sample=symbol.compile()
            sample=json.dumps(sample, indent=4)
            samples.append(sample)
            print(sample)

    for s in samples:
        try:
            parsed = json.loads(s)
            print(f" ✅ Valid JSON")
        except json.JSONDecodeError as e:
            print(f" ❌ Invalid JSON ({e})")