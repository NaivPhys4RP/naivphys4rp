uint8 CUSTOM=0
uint8 CYLINDRICAL_1=1
uint8 CYLINDRICAL_2=2
uint8 SPHERICAL=3
uint8 SCISSOR_1=4
uint8 SCISSOR_2=5
uint8 SCISSOR_3=6
uint8 SCISSOR_4=7
uint8 HOLLOW_1=8
uint8 HOLLOW_2=9
uint8 HOLLOW_3=10
uint8 HOLLOW_4=11
uint8 CLOSE_CLAMP_TTVC=12   # grasp used for closing the clamp (TTVC = TacTile Verification Compatible)
uint8 INSERT_NEEDLE_TTVC=13 # grasp used for inserting the needle (TTVC = TacTile Verification Compatible)
uint8 grasp_type_id 	    # label of the selected discrete grasp (GraspType.CUSTOM, GraspType.CYLINDRICAL_1, GraspType.SPHERICAL, etc.)
float64[] custom_grasp	    # customized grasp : in the case of non existing grasp in the available list of preshaped grasp (read only if grasp_type_id=GraspType.CUSTOM)
