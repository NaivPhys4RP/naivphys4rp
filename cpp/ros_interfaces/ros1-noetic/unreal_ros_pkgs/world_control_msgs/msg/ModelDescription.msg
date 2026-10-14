#  the name of the model (mesh)
string name

# Pose the model is supposed to have
# pose in right handed, ros coord system
geometry_msgs/Pose pose

string id

# Everything below this is OPTIONAL

# UTags that the should be set to Model
world_control_msgs/Tag[] tags

# path in the project directory (ProjectContentDir() + path) where to start searching for the model
# if not found in the given path, a recursive search will be done in ProjectContentDir()
# (If multiple search results will be return, first one will be used)
string path

# name of the model in the editor
string actor_label

# Physics proterties of the Model
world_control_msgs/PhysicsProperties physics_properties

# By default the default materials of the mesh are used
string[] material_names
string[] material_paths
