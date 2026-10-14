# Check: https://docs.unrealengine.com/en-US/Engine/Physics/Constraints/ConstraintsReference
# under "Linear Limits" for refrence.
# the motions are represented by the folowing Enum.
# 0: LCM_Free
# 1: LCM_Limited
# 2: LCM_Locked
uint8 x_motion
uint8 y_motion
uint8 z_motion
float32 limit

# if this is set to false the Advanced options will be set to their unreal default values.
bool use_advanced
# Advanced
bool soft_constraint # default false
float32 stiffness # default 0
float32 damping # default 0
