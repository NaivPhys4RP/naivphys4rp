import random
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

# Import the terminals (ApertureDimensions, HollowConeDimensions, TransformDefinition, etc.)
from terminals import *


# =========================================================================
# 1. DESIGN PROPERTY DEFINITIONS (Tier 3: Full Randomization)
# =========================================================================

@dataclass
class ContainerAestheticDesign(CompiledSymbol):
    colors: List[str] = field(default_factory=lambda: ["WHITE"])
    texture: str = "SOLID_T"

    @classmethod
    def generate(cls, colors: Optional[List[str]] = None,
                 texture: Optional[str] = None) -> "ContainerAestheticDesign":
        if colors is None:
            palette = ["RED", "BLUE", "GREEN", "YELLOW", "WHITE", "GRAY", "ORANGE", "PURPLE"]
            colors = random.sample(palette, k=random.randint(1, 3))

        if texture is None:
            #texture = random.choice(["PATTERN_T", "PICTURE_T", "SOLID_T", "GRADIENT_T", "METALLIC_T"])
            texture = random.choice(["PATTERN_T", "SOLID_T", "GRADIENT_T"])
        return cls(colors=colors, texture=texture)

    def compile(self) -> Dict[str, Any]:
        return {
            "aesthetics": {
                "colors": self.colors,
                "texture": self.texture
            }
        }


@dataclass
class ContainerStructuralDesign(CompiledSymbol):
    material: str = "PLASTIC"
    fragility_rate: float = 0.1
    absolute_fragility: float = 0.0
    density: float = 1000.0
    friction: float = 0.5
    restitution: float = 0.3
    transparency: float = 1.0

    @classmethod
    def generate(cls,
                 material: Optional[str] = None,
                 fragility_rate: Optional[float] = None,
                 absolute_fragility: Optional[float] = None,
                 density: Optional[float] = None,
                 friction: Optional[float] = None,
                 restitution: Optional[float] = None,
                 transparency: Optional[float] = None) -> "ContainerStructuralDesign":

        m = material if material is not None else random.choice(
            ["PLASTIC", "WOOD", "GLASS", "STEEL", "CERAMIC"])

        if transparency is None:
            if m == "GLASS":
                transparency = random.uniform(0.1, 0.4)
            elif m == "PLASTIC":
                transparency = random.choice([1.0, 1.0, 0.5])
            else:
                transparency = 1.0

        return cls(
            material=m,
            fragility_rate=fragility_rate if fragility_rate is not None else random.uniform(0.01, 0.8),
            absolute_fragility=absolute_fragility if absolute_fragility is not None else random.uniform(0.0, 0.15),
            density=density if density is not None else random.uniform(400.0, 8000.0),
            friction=friction if friction is not None else random.uniform(0.2, 0.95),
            restitution=restitution if restitution is not None else random.uniform(0.1, 0.7),
            transparency=transparency
        )

    def compile(self) -> Dict[str, Any]:
        return {
            "structural": asdict(self)
        }


# =========================================================================
# 2. CORE SHAPES (Orchestrators)
# =========================================================================

@dataclass
class FullShape(CompiledSymbol):
    shape_key: str
    dimensions: CompiledSymbol
    aesthetics: ContainerAestheticDesign
    structural: ContainerStructuralDesign
    transform: TransformDefinition  # <--- Added extrinsic spatial pillar

    def compile(self) -> Dict[str, Any]:
        """Recursive traversal: Compiles terminals, design properties, and extrinsic transform."""
        return {
            self.shape_key: {
                **self.dimensions.compile(),
                **self.aesthetics.compile(),
                **self.structural.compile(),
                "transform": self.transform.compile() # <--- Compiled as extrinsic metadata
            }
        }


# =========================================================================
# 3. SHAPE FACTORIES (The "Start" Rule Implementation)
# =========================================================================

class ShapeFactory:
    @staticmethod
    def generate_conical_hollow(dimensions: Optional[HollowConeDimensions] = None,
                                aesthetics: Optional[ContainerAestheticDesign] = None,
                                structural: Optional[ContainerStructuralDesign] = None,
                                transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="conical_hollow_shape",
            dimensions=dimensions if dimensions is not None else HollowConeDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate_spherical_hollow(dimensions: Optional[HollowSphereDimensions] = None,
                                  aesthetics: Optional[ContainerAestheticDesign] = None,
                                  structural: Optional[ContainerStructuralDesign] = None,
                                  transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="spherical_hollow_shape",
            dimensions=dimensions if dimensions is not None else HollowSphereDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate_torus_hollow(dimensions: Optional[HollowTorusDimensions] = None,
                              aesthetics: Optional[ContainerAestheticDesign] = None,
                              structural: Optional[ContainerStructuralDesign] = None,
                              transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="torus_hollow_shape",
            dimensions=dimensions if dimensions is not None else HollowTorusDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate_conical_closed(dimensions: Optional[ClosedConeDimensions] = None,
                                aesthetics: Optional[ContainerAestheticDesign] = None,
                                structural: Optional[ContainerStructuralDesign] = None,
                                transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="conical_closed_shape",
            dimensions=dimensions if dimensions is not None else ClosedConeDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate_spherical_closed(dimensions: Optional[ClosedSphereDimensions] = None,
                                  aesthetics: Optional[ContainerAestheticDesign] = None,
                                  structural: Optional[ContainerStructuralDesign] = None,
                                  transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="spherical_closed_shape",
            dimensions=dimensions if dimensions is not None else ClosedSphereDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate_torus_closed(dimensions: Optional[ClosedTorusDimensions] = None,
                              aesthetics: Optional[ContainerAestheticDesign] = None,
                              structural: Optional[ContainerStructuralDesign] = None,
                              transform: Optional[TransformDefinition] = None) -> FullShape:
        return FullShape(
            shape_key="torus_closed_shape",
            dimensions=dimensions if dimensions is not None else ClosedTorusDimensions.generate(),
            aesthetics=aesthetics if aesthetics is not None else ContainerAestheticDesign.generate(),
            structural=structural if structural is not None else ContainerStructuralDesign.generate(),
            transform=transform if transform is not None else TransformDefinition.generate()
        )

    @staticmethod
    def generate() -> FullShape:
        generators = [
            ShapeFactory.generate_conical_hollow,
            ShapeFactory.generate_spherical_hollow,
            ShapeFactory.generate_torus_hollow,
            ShapeFactory.generate_conical_closed,
            ShapeFactory.generate_spherical_closed,
            ShapeFactory.generate_torus_closed
        ]
        return random.choice(generators)()


# =========================================================================
# 4. TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    nb_samples = 6
    samples = []
    for _ in range(nb_samples):
        symbol = ShapeFactory.generate()
        if symbol:
            print(f"\nGenerated: {symbol.shape_key}")
            sample = symbol.compile()
            sample_str = json.dumps(sample, indent=4)
            samples.append(sample_str)
            print(sample_str)

    for s in samples:
        try:
            parsed = json.loads(s)
            print(f" ✅ Valid JSON")
        except json.JSONDecodeError as e:
            print(f" ❌ Invalid JSON ({e})")