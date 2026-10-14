cmake_minimum_required(VERSION 2.8.3)
project(world_control_msgs)

find_package(
	catkin REQUIRED COMPONENTS
	std_msgs
  geometry_msgs
	message_generation
)


## Generate messages in the 'msg' folder
add_message_files(
   FILES
   Tag.msg
	 AngularLimits.msg
	 LinearLimits.msg
	 PhysicsConstraintDetails.msg
	 PhysicsProperties.msg
	 ModelDescription.msg
	 ConstraintDescription.msg
	 RelationDescription.msg
	 object_dynamics.msg
)

## Generate services in the 'srv' folder
add_service_files(
  FILES
  SpawnModel.srv
	SetModelPose.srv
	DeleteModel.srv
	GetModelPose.srv
	AttachModelToParent.srv
	SpawnPhysicsConstraint.srv
	HighlightModel.srv
	SetMaterial.srv
	SetPhysicsProperties.srv
	SpawnSemanticMap.srv
)

generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
)

catkin_package(
  CATKIN_DEPENDS message_runtime
)

include_directories(
 include
 ${catkin_INCLUDE_DIRS}
)
