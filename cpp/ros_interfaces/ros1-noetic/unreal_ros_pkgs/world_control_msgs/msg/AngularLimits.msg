# Check: https://docs.unrealengine.com/en-US/Engine/Physics/Constraints/ConstraintsReference
# under "Angular Limits" for refrence.
# the motions are represented by the folowing Enum.
# 0: ACM_Free
# 1: ACM_Limited
# 2: ACM_Locked
uint8 swing_1_motion
uint8 swing_2_motion
uint8 twist_motion
float32 swing_1_limit_angle
float32 swing_2_limit_angle
float32 twist_limit_angle
geometry_msgs/Vector3 angular_roation_offset

# if this is set to false the Advanced options will be set to their unreal default values.
bool use_advanced
# Advanced
bool swing_soft_constraint # default true
float32 swing_stiffness # default 50
float32 swing_damping # default 0
bool twist_soft_constraint # default true
float32 twist_stiffness # default 50
float32 twist_damping # default 0
