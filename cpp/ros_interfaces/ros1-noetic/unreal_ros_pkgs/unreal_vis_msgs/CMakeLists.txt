cmake_minimum_required(VERSION 2.8.3)
project(unreal_vis_msgs)

find_package(
	catkin REQUIRED COMPONENTS
	std_msgs
  geometry_msgs
	message_generation
)


## Generate messages in the 'msg' folder
#add_message_files(
#   FILES
#)

## Generate services in the 'srv' folder
add_service_files(
  FILES
  DisplayBasicMarker.srv
	DisplayTrajectory.srv
	RemoveMarker.srv
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
