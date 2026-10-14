# =========================================================================
# flat_containers.py
# =========================================================================

from deep_containers import *

# =========================================================================
# 1. FLAT CONTAINER CLASSES
# =========================================================================

@dataclass
class Plate(CompiledSymbol):
    body: Body
    aperture: Aperture
    aperture_joint: JointDefinition
    feet: Optional[Feet] = None
    feet_joint: Optional[JointDefinition] = None

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Plate":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Generate shallow body
        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Plate: Shallow Z-offset for the aperture
        z_top = 0.02
        ap_dims = ApertureDimensions.generate(radius=0.15, position_z=z_top)
        aperture = Aperture.generate(dimensions=ap_dims, aesthetics=aesthetics, structural=structural)
        aperture_joint = JointDefinition.generate(joint_type="fixed", pos_z=z_top)

        feet, feet_joint = (None, None)
        if random.random() < 0.3:
            feet = Feet.generate(aesthetics=aesthetics, structural=structural)
            feet_joint = JointDefinition.generate(joint_type="fixed", pos_z=0.0)

        return cls(body, aperture, aperture_joint, feet, feet_joint)

    def compile(self) -> Dict[str, Any]:
        inner = {
            "shallow_body": self.body.compile()["body"],
            "full_aperture": {**self.aperture.compile()["aperture"], **self.aperture_joint.compile()}
        }
        if self.feet:
            inner["feet"] = {**self.feet.compile()["feet"], **self.feet_joint.compile()}
        return {"plate": inner}


@dataclass
class Spoon(CompiledSymbol):
    body: Body
    handle_spoon: HandleSpoon
    handle_joint: JointDefinition

    @classmethod
    def generate(cls, aesthetics: Optional[ContainerAestheticDesign] = None,
                 structural: Optional[ContainerStructuralDesign] = None) -> "Spoon":
        aesthetics = aesthetics or ContainerAestheticDesign.generate()
        structural = structural or ContainerStructuralDesign.generate()

        # Scoop part
        body = Body.generate(aesthetics=aesthetics, structural=structural)

        # Functional handle part
        handle_spoon = HandleSpoon.generate(aesthetics=aesthetics, structural=structural)

        # Joint to attach handle to the scoop edge
        handle_joint = JointDefinition.generate(
            joint_type="fixed",
            pos_x=0.04,
            pos_z=0.01
        )

        return cls(body, handle_spoon, handle_joint)

    def compile(self) -> Dict[str, Any]:
        return {
            "spoon": {
                "spoon_body": self.body.compile()["body"],
                "handle": {**self.handle_spoon.compile()["handle"], **self.handle_joint.compile()}
            }
        }


# =========================================================================
# 2. TOP LEVEL FACTORY
# =========================================================================

class FlatContainerFactory:
    @staticmethod
    def generate() -> Dict[str, Any]:
        # Tiered fallback design
        aesthetics = ContainerAestheticDesign.generate()
        structural = ContainerStructuralDesign.generate()

        choice = random.choice([Plate, Spoon])
        container_instance = choice.generate(aesthetics=aesthetics, structural=structural)

        return  container_instance

# =========================================================================
# TEST EXECUTION
# =========================================================================

if __name__ == "__main__":
    # Test multiple generations to verify randomization
    nb_samples = 2
    samples = []
    for _ in range(nb_samples):
        symbol = FlatContainerFactory.generate()
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