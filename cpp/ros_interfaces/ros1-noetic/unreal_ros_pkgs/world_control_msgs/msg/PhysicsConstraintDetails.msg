# All fields directly represent values of the PhysicsConstrained.
# And can be looked up here: https://docs.unrealengine.com/en-US/Engine/Physics/Constraints/ConstraintsReference
# Models affected by the constrained
string id_first_model
string id_second_model
# Constrained Behavior
bool disable_collision
bool enable_projection
float32 projection_linear_tolerance
float32 projection_angular_tolerance
bool parent_dominates
world_control_msgs/LinearLimits linear_limits
world_control_msgs/AngularLimits angular_limits
