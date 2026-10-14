cmake_minimum_required(VERSION 2.8.3)
project(belief_state)

## Find catkin and any catkin packages
find_package(catkin REQUIRED COMPONENTS naivphys4rp_msgs)



## Declare ROS messages and services
## add_message_files(FILES Num.msg)
## add_service_files(FILES AddTwoInts.srv)

## Generate added messages and services
## generate_messages(DEPENDENCIES std_msgs)

################################################################################
## catkin specific configuration                                              ##
################################################################################

# libraries to export


catkin_package(
  INCLUDE_DIRS ${catkin_INCLUDE_DIRS}
  CATKIN_DEPENDS naivphys4rp_msgs
  DEPENDS 
)

include_directories(${catkin_INCLUDE_DIRS} )

################################################################################
## Set include directories                                                    ##
################################################################################



## Build talker and listener
## include_directories(include ${catkin_INCLUDE_DIRS})

## add_executable(talker src/talker.cpp)
## target_link_libraries(talker ${catkin_LIBRARIES})
## add_dependencies(talker beginner_tutorials_generate_messages_cpp)

## add_executable(listener src/listener.cpp)
## target_link_libraries(listener ${catkin_LIBRARIES})
## add_dependencies(listener beginner_tutorials_generate_messages_cpp)
