High-Level Geometric DSL Grammar Specification (EBNF)
--- Top-Level Structure ---
Defines the overall object and shared, inherited properties.

ObjectDefinition = "{",
""" NAME """, ":", "{",
""Type"", ":", ""CONTAINER" | "SUPPORT"", ",",
""MaterialType"", ":", "STRING", ",",
""WallThickness"", ":", "NUMBER", ",",
"[", ""BaseThickness"", ":", "NUMBER", ",", "]",
""Assembly"", ":", "[", ComponentDefinition+, "]",
"}",
"}"
--- Component Definition (The Building Blocks) ---
Defines a single geometric part and how it is instantiated and assembled.

ComponentDefinition = "{",
""Name"", ":", "NAME", ",",
""Generator"", ":", GeneratorType, ",",
"[", JointDefinition, ",", "]",
""Params"", ":", "{", ArgList, "}", ",",
"[", ExposedJointsDefinition, ",", "]",
"}"
--- Generator Types (Specific Primitives) ---

GeneratorType = ""CONE_CONTAINER"" | ""SPHERE_CONTAINER"" | ""CONE_SUPPORT"" | ""SPHERE_SUPPORT"" | ""HANDLE""
--- Parameters ---
ArgList: The list of parameters passed to the Generator.

ArgList = [Argument, {",", Argument}]
Argument = """ NAME """, ":", Value
Value = NAME | NUMBER | STRING
--- Joint/Assembly Logic (PROPAGATION & MERGING) ---
JointDefinition: Rules for attaching this component to a previously defined component.

JointDefinition = ""Joint"", ":", "{",
""Attach_To"", ":", "NAME", ",",
""Target_Dim_Prop"", ":", "NAME", ",",
""Local_Param_Key"", ":", "NAME", ",",
""Target_Face_Type"", ":", "NAME", ",",
""Local_Face_Type"", ":", "NAME",
"}"
--- Dimension Exposure ---
ExposedJointsDefinition: Defines which local parameters should be made available (exposed)
for subsequent components to use for dimension matching.

ExposedJointsDefinition = ""Exposed_Joints"", ":", "{",
[ExposedDimension, {",", ExposedDimension}],
"}"
ExposedDimension = """ NAME """, ":", """ NAME """
--- Terminal Symbol Definitions ---
These define the basic tokens used throughout the grammar.

NAME = LETTER, {LETTER | DIGIT | "_"}
NUMBER = [SIGN], (DIGIT+) | (DIGIT+, ".", DIGIT+)
STRING = "'", {CHARACTER}, "'" | """, {CHARACTER}, """
SIGN = "+" | "-"
LETTER = "a".."z" | "A".."Z"
DIGIT = "0".."9"
CHARACTER = any valid string character