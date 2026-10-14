project(rs_naivphs4r_io)

rs_add_library(rs_naivphs4r_BeliefLoader src/BeliefLoader.cpp)
target_link_libraries(rs_naivphs4r_BeliefLoade rs_core)

#if(X_FOUND)
# rs_add_library(rs_CaffeAnnotator src/CaffeAnnotator.cpp)
# target_link_libraries(rs_CaffeAnnotator rs_core rs_caffeProxy)
#endif()

rs_add_executable(BeliefLoader src/BeliefLoader.cpp)
target_link_libraries(BeliefLoader rs_naivphs4r_io ${catkin_LIBRARIES})
