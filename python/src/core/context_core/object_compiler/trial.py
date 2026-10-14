from common import *

def extract_parameters(shape_json):
    """
    Extracts 'aesthetics' and 'structural' dictionaries from a given shape JSON.

    Example input:
    {
        "spherical_hollow_shape": {
            "dimensions": {...},
            "aesthetics": {"colors": ["BROWN"], "texture": "GRADIENT_T"},
            "structural": {
                "material": "GLASS", "fragility_rate": 9.22, "absolute_fragility": 8.98,
                "density": 0.91, "friction": 6.62, "restitution": 3.8, "transparency": 4.94
            }
        }
    }

    Returns:
        aesthetics_params, structural_params
    """

    # Extract the first shape key dynamically
    shape_key = next(iter(shape_json))
    shape_data = shape_json[shape_key]

    # Extract aesthetics and structural data
    aesthetics = shape_data.get("aesthetics", {})
    structural = shape_data.get("structural", {})

    # Build the aesthetics_params dict
    aesthetics_params = {
        "colors": aesthetics.get("colors", []),
        "texture_type": TEXTURE_TYPE.get(aesthetics.get("texture"), aesthetics.get("texture")),
        "texture_data": {}
    }

    # Build the structural_params dict
    structural_params = {
        "material": MATERIAL_TYPE.get(structural.get("material"), structural.get("material")),
        "fragility_rate": structural.get("fragility_rate", 0.0),
        "density": structural.get("density", 0.0),
        "friction": structural.get("friction", 0.0),
        "restitution": structural.get("restitution", 0.0),
        "absolute_fragility": structural.get("absolute_fragility", 0.0),
        "transparency": structural.get("transparency", 1.0)
    }

    return aesthetics_params, structural_params


# --- Example usage ---
example_json = {
    "spherical_hollow_shape": {
        "dimensions": {
            "outer_radius": 7.18, "inner_radius": 3.07,
            "start_latitude_deg": 4.35, "end_latitude_deg": 8.19,
            "segments": 74, "rings": 82
        },
        "aesthetics": {"colors": ["BROWN"], "texture": "GRADIENT_T"},
        "structural": {
            "material": "GLASS", "fragility_rate": 9.22, "absolute_fragility": 8.98,
            "density": 0.91, "friction": 6.62, "restitution": 3.8, "transparency": 4.94
        }
    }
}

aesthetics_params, structural_params = extract_parameters(example_json)
print("Aesthetics:", aesthetics_params)
print("Structural:", structural_params)
