import os
import PIL.Image
from google import genai
import json
from google.genai import types


class PESGEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "models/gemini-2.5-flash-lite"

    def induce_grammar(self, image_prompt):
        """Returns a Python Dictionary directly."""
        try:
            img = image_prompt

            # This prompt now strictly defines the output format
            prompt = """
            Analyze the image and return a JSON object representing the 3D functional structure.
            Use these components ONLY: ConeGenerator, TorusSupportGenerator, ConeSupportGenerator.

            Example Format:
            {"scene_object": {"scene_container": {"bottle": {"deep_body": {"body": {"torso": [{"torso": {"spherical_hollow_shape": {"dimensions": {"outer_radius": 3.82, "inner_radius": 7.39, "start_latitude_deg": 0.35, "end_latitude_deg": 2.19, "segments": 49, "rings": 21}, "aesthetics": {"colors": ["BLACK"], "texture": "PATTERN_T"}, "structural": {"material": "STEEL", "fragility_rate": 7.83, "absolute_fragility": 7.91, "density": 6.64, "friction": 1.44, "restitution": 6.24, "transparency": 8.95}}}}], "base": {"spherical_closed_shape": {"dimensions": {"outer_radius": 7.19, "start_latitude_deg": 5.28, "end_latitude_deg": 2.13, "segments": 41, "rings": 70}, "aesthetics": {"colors": ["GREEN"], "texture": "SOLID_T"}, "structural": {"material": "PLASTIC", "fragility_rate": 9.23, "absolute_fragility": 8.14, "density": 8.53, "friction": 6.7, "restitution": 4.88, "transparency": 6.06}}}}}, "aperture": {"aperture_profile": {"POLYGON": {"num_segments": 37}}, "dimensions": {"radius": 5.47, "position_z": 2.38}}, "closure": {"lid": {"torso": {"spherical_closed_shape": {"dimensions": {"outer_radius": 0.59, "start_latitude_deg": 1.8, "end_latitude_deg": 1.88, "segments": 25, "rings": 5}, "aesthetics": {"colors": ["GRAY"], "texture": "PATTERN_T"}, "structural": {"material": "CERAMIC", "fragility_rate": 4.83, "absolute_fragility": 9.19, "density": 6.68, "friction": 8.62, "restitution": 0.68, "transparency": 2.11}}}, "base": {"spherical_closed_shape": {"dimensions": {"outer_radius": 2.19, "start_latitude_deg": 8.7, "end_latitude_deg": 1.8, "segments": 75, "rings": 48}, "aesthetics": {"colors": ["VIOLET"], "texture": "SOLID_T"}, "structural": {"material": "WOOD", "fragility_rate": 9.35, "absolute_fragility": 2.6, "density": 2.98, "friction": 8.16, "restitution": 1.35, "transparency": 9.68}}}}}, "spout": {"conical_hollow_shape": {"dimensions": {"outer_bottom_radius": 3.0, "outer_top_radius": 4.79, "height": 8.83, "inner_bottom_radius": 7.28, "inner_top_radius": 4.53, "segments": 71, "rings": 30}, "aesthetics": {"colors": ["GREEN"], "texture": "SOLID_T"}, "structural": {"material": "WOOD", "fragility_rate": 6.47, "absolute_fragility": 3.7, "density": 2.02, "friction": 8.37, "restitution": 1.48, "transparency": 2.34}}}}}}}
           
            """

            # We use config to enforce JSON response
            answer="{}"
            """
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            answer = response.text.strip()
            """

            answer=json.loads(answer)
            #answer= {"scene_object": {"scene_container": {"bottle": {"deep_body": {"body": {"torso": [{"torso": {"spherical_hollow_shape": {"dimensions": {"outer_radius": 3.82, "inner_radius": 7.39, "start_latitude_deg": 0.35, "end_latitude_deg": 2.19, "segments": 49, "rings": 21}, "aesthetics": {"colors": ["BLACK"], "texture": "PATTERN_T"}, "structural": {"material": "STEEL", "fragility_rate": 7.83, "absolute_fragility": 7.91, "density": 6.64, "friction": 1.44, "restitution": 6.24, "transparency": 8.95}}}}], "base": {"spherical_closed_shape": {"dimensions": {"outer_radius": 7.19, "start_latitude_deg": 5.28, "end_latitude_deg": 2.13, "segments": 41, "rings": 70}, "aesthetics": {"colors": ["GREEN"], "texture": "SOLID_T"}, "structural": {"material": "PLASTIC", "fragility_rate": 9.23, "absolute_fragility": 8.14, "density": 8.53, "friction": 6.7, "restitution": 4.88, "transparency": 6.06}}}}}, "aperture": {"aperture_profile": {"POLYGON": {"num_segments": 37}}, "dimensions": {"radius": 5.47, "position_z": 2.38}}, "closure": {"lid": {"torso": {"spherical_closed_shape": {"dimensions": {"outer_radius": 0.59, "start_latitude_deg": 1.8, "end_latitude_deg": 1.88, "segments": 25, "rings": 5}, "aesthetics": {"colors": ["GRAY"], "texture": "PATTERN_T"}, "structural": {"material": "CERAMIC", "fragility_rate": 4.83, "absolute_fragility": 9.19, "density": 6.68, "friction": 8.62, "restitution": 0.68, "transparency": 2.11}}}, "base": {"spherical_closed_shape": {"dimensions": {"outer_radius": 2.19, "start_latitude_deg": 8.7, "end_latitude_deg": 1.8, "segments": 75, "rings": 48}, "aesthetics": {"colors": ["VIOLET"], "texture": "SOLID_T"}, "structural": {"material": "WOOD", "fragility_rate": 9.35, "absolute_fragility": 2.6, "density": 2.98, "friction": 8.16, "restitution": 1.35, "transparency": 9.68}}}}}, "spout": {"conical_hollow_shape": {"dimensions": {"outer_bottom_radius": 3.0, "outer_top_radius": 4.79, "height": 8.83, "inner_bottom_radius": 7.28, "inner_top_radius": 4.53, "segments": 71, "rings": 30}, "aesthetics": {"colors": ["GREEN"], "texture": "SOLID_T"}, "structural": {"material": "WOOD", "fragility_rate": 6.47, "absolute_fragility": 3.7, "density": 2.02, "friction": 8.37, "restitution": 1.48, "transparency": 2.34}}}}}}}
            # The SDK automatically parses JSON strings into Python dicts
            answer = json.dumps(answer, indent=1)
            return  answer

        except Exception as e:
            print(f"Induction Error: {e}")
            return None