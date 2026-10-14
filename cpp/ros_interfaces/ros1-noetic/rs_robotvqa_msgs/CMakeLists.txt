cmake_minimum_required(VERSION 2.8.3)
project(rs_robotvqa_msgs)

find_package(catkin REQUIRED COMPONENTS 
  geometry_msgs 
  shape_msgs
  sensor_msgs
  actionlib_msgs
  visualization_msgs
  message_generation)

add_message_files(
  FILES
  ObjectProperty.msg
  ObjectRelation.msg
  ObjectDescription.msg
  SceneGraph.msg
)

add_service_files(
  FILES
  GetSceneGraph.srv
)

#add_action_files(DIRECTORY action FILES RSQuery.action)

generate_messages(
  DEPENDENCIES
  geometry_msgs
  visualization_msgs
  actionlib_msgs
  shape_msgs
  sensor_msgs)

catkin_package(
  CATKIN_DEPENDS 
    geometry_msgs 
    shape_msgs 
    sensor_msgs
    message_runtime
)
