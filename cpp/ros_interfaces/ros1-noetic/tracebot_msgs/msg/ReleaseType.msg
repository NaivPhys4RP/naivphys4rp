uint8 CUSTOM=0
uint8 POSITION=1
uint8 FORCE=2
uint8 release_type_id 	        # label of selected opening strategy (ReleaseType.CUSTOM, ReleaseType.POSITION, ReleaseType.FORCE etc.)
float64[] custom_grasp_release	# customized opening strategy (target reference to reach) (read only if release_type_id=ReleaseType.CUSTOM)