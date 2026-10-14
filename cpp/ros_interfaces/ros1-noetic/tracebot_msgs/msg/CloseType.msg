uint8 CUSTOM=0
uint8 POSITION=1
uint8 FORCE=2
uint8 CLOSE_CLAMP_TTVC=3        # grasp used for closing the clamp (TTVC = TacTile Verification Compatible)
uint8 INSERT_NEEDLE_TTVC=4      # grasp used for inserting the needle (TTVC = TacTile Verification Compatible)
uint8 close_type_id 	        # label of selected closing strategy (CloseType.CUSTOM, CloseType.POSITION, CloseType.FORCE etc.)
float64[] custom_grasp_close	# customized closing strategy (target reference to reach) (read only if close_type_id=CloseType.CUSTOM)
