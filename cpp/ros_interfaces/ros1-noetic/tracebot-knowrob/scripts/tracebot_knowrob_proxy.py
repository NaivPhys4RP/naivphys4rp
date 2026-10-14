#!/usr/bin/env python3

import sys
import random
import time
import os
import actionlib
import roslib
import rospkg
rospack = rospkg.RosPack()
TRACEBOT_KNOWROB_PATH=rospack.get_path('tracebot-knowrob')
print("parsing info source modalities ...")
roslib.load_manifest('rosprolog')
roslib.load_manifest('tracebot_msgs')
import rospy
try:
    from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
    from rosprolog_client import PrologException, Prolog 
    print('Loading rosprolog ...')
from tracebot_msgs.msg import *
from neem_interface.neem_interface import *
import numpy as np
from tracebot_audit_trail_generator import *
import json
from functional_verification.ModalityParser import *
from functional_verification.ObjectParser import *
from functional_verification.ActionParser import *
from functional_verification.VerifierParser import *


class TraceBotKnowrobServer:
	def __init__(self):
	 
         global TRACEBOT_KNOWROB_PATH
	 #starting prolog and action server
         self.prolog = Prolog()
         
         self.namespace="http://www.semanticweb.org/smile/ontologies/2022/2/TraceBot#" #default ontology's namespace /verify_feasibility_canister_grasp
         self.throttle_processes=[]
         
         self.canister_inserting_success_verifier_server = actionlib.SimpleActionServer('KBCanisterInsertionSuccess', KBVerifierAction, self.KBCanisterInsertionSuccess, False)
         self.canister_inserting_success_verifier_server.start()
         print("Server canister inserting success verifier is started !")
         
         self.canister_grasping_feasibility_verifier_server = actionlib.SimpleActionServer('KBCanisterGraspingFeasibilityCheck', KBVerifierAction, self.KBCanisterGraspingFeasibilityCheck, False)
         self.canister_grasping_feasibility_verifier_server.start()
         print("Server canister grasping feasibility verifier is started !")
         
         self.get_participant_with_role_server = actionlib.SimpleActionServer('KBGetActionParticipantRole', KBGetActionParticipantRoleAction, self.KBGetActionParticipantRole, False)
         self.get_participant_with_role_server.start()
         print("Server for getting action participant is started !")
         
         self.grasping_verifier_server = actionlib.SimpleActionServer('KBGrabSuccessCheck', KBVerifierAction, self.KBGrabSuccessCheck, False)
         self.grasping_verifier_server.start()
         print("Server grasping verifier is started !")
         
         self.action_gripper_id_server = actionlib.SimpleActionServer('tracebot_knowrob_gripper_id', KBGetGripperIdAction, self.get_gripper_id, False)
         self.action_gripper_id_server.start()
         print("Server for getting gripper id is started !")
         
         self.inserting_verifier_server = actionlib.SimpleActionServer('KBInsertSuccessCheck', KBVerifierAction, self.KBInsertSuccessCheck , False)
         self.inserting_verifier_server.start()
         print("Server inserting verifier is started !")
         
         self.locating_small_verifier_server = actionlib.SimpleActionServer('SmallObjectLocateCheck', KBVerifierAction, self.SmallObjectLocateCheck, False)
         self.locating_small_verifier_server.start()
         print("Server locating small objects verifier is started !")
         
         self.locating_transparent_verifier_server = actionlib.SimpleActionServer('TransparentObjectLocateCheck', KBVerifierAction, self.TransparentObjectLocateCheck , False)
         self.locating_transparent_verifier_server.start()
         print("Server locating transparent verifier is started !")
         
         
         self.onto_load_server = actionlib.SimpleActionServer('tracebot_knowrob_load', KBLoadOntologyAction, self.executeLoadOntology, False)
         self.onto_load_server.start()
         print("Server ontology loader is started !")
         
         self.fake_process_server = actionlib.SimpleActionServer('tracebot_knowrob_fake_process', KBFakeTBProcessAction, self.executeFakeTBProcess, False)
         self.fake_process_server.start()
         print("Server Fake Process Executive is started !")
         
         self.list_individual_server = actionlib.SimpleActionServer('tracebot_knowrob_list_individual', KBListIndividualAction, self.executeListIndividual, False)
         self.list_individual_server.start()
         print("Server for extracting the individual list is started !")
         
         self.audit_trail_server = actionlib.SimpleActionServer('tracebot_knowrob_audit_trail', KBAuditTrailAction, self.executeAuditTrail, False)
         self.audit_trail_server.start()
         print("Server for generating the audit trail is started !")
         
         self.subclass_server = actionlib.SimpleActionServer('tracebot_knowrob_subclass', KBSubClassAction, self.executeSubClass, False)
         self.subclass_server.start()
         print("Server subclass is started !")
         
         self.new_individual_server = actionlib.SimpleActionServer('tracebot_knowrob_individual', KBNewIndividualAction, self.executeNewIndividual, False)
         self.new_individual_server.start()
         print("Server for creating instances is started !")
         
         
         self.new_cindividual_server = actionlib.SimpleActionServer('tracebot_knowrob_cindividual', KBNewComplexIndividualAction, self.executeNewComplexIndividual, False)
         self.new_cindividual_server.start()
         print("Server for creating complex instances is started !")
         
         self.object_property_server = actionlib.SimpleActionServer('tracebot_knowrob_object_property', KBObjectPropertyAction, self.executeObjectProperty, False)
         self.object_property_server.start()
         print("Server for extracting object image is started !")
         
         self.data_property_server = actionlib.SimpleActionServer('tracebot_knowrob_data_property', KBDataPropertyAction, self.executeDataProperty, False)
         self.data_property_server.start()
         print("Server for extracting data image is started !")
         
         self.list_property_server = actionlib.SimpleActionServer('tracebot_knowrob_list_property', KBListPropertyAction, self.executeListProperty, False)
         self.list_property_server.start()
         print("Server for extracting the property list is started !")
         
         self.list_class_server = actionlib.SimpleActionServer('tracebot_knowrob_list_class', KBListClassAction, self.executeListClass, False)
         self.list_class_server.start()
         print("Server for extracting the class list is started !")
         
         
         self.query_knowledge_server = actionlib.SimpleActionServer('tracebot_knowrob_query_knowledge', KBQueryKnowledgeAction, self.executeQueryKnowledge, False)
         self.query_knowledge_server.start()
         print("Server for extracting the class list is started !")
         
         self.common_pose_server = actionlib.SimpleActionServer('tracebot_knowrob_common_pose', KBCommonPoseAction, self.executeCommonPose, False)
         self.common_pose_server.start()
         print("Server for extracting common object poses is started !")
         
         self.get_class_id_server = actionlib.SimpleActionServer('tracebot_knowrob_class_id', KBGetClassIdAction, self.executeGetClassId, False)
         self.get_class_id_server.start()
         print("Server for extracting class ids is started !")
         
         self.reset_server = actionlib.SimpleActionServer('tracebot_knowrob_reset', KBResetAction, self.executeReset, False)
         self.reset_server.start()
         print("Server for resetting the KB is started !")
         
         self.action_feasibility_server = actionlib.SimpleActionServer('tracebot_knowrob_action_feasibility', KBActionFeasibilityVerificationAction, self.executeActionFeasibility, False)
         self.action_feasibility_server.start()
         print("Server for verifying the feasibility of actions is started !")
         
         self.action_success_server = actionlib.SimpleActionServer('tracebot_knowrob_action_success', KBActionSuccessVerificationAction, self.executeActionSuccess, False)
         self.action_success_server.start()
         print("Server for verifying the success of actions is started !")
         
         self.onto_load_default_server = actionlib.SimpleActionServer('tracebot_knowrob_load_default', KBLoadDefaultOntologyAction, self.executeLoadDefaultOntology, False)
         self.onto_load_default_server.start()
         print("Server default ontologies loader is started !")
         
         with_kb_reset=rospy.get_param('with_kb_reset',True)
         self.with_clean_up_neem_experience=rospy.get_param('with_clean_up_neem_experience',True)
         
         
         #reinitializing KB
         try:
                if with_kb_reset:
                       q = self.prolog.query("mng_drop('roslog', 'triples')")
                       q.finish()    
                       print("KB reinitialized successfully!!!")           
         except Exception as e:
                print("Reinitializing KB failed: ", str(e))
	#Loading default KB
         try:
                packageName = "tracebot-knowrob"
                relativePath= "ontology/TraceBot-Ontology.owl"
                print("Loading ontology from:", packageName, relativePath)
                q=self.prolog.query("load_owl('package://"+str(packageName)+"/"+str(relativePath)+"').")
                q.finish()    
                print("TraceBot ontology loaded successfully")     
         except Exception as e:
                print("Loading default ontology KB failed: ", str(e))
         
         #print("parsing list of modalities ...")
         self.modalityParser=ModalityParser(path_name=str(TRACEBOT_KNOWROB_PATH)+'/descriptions/domains/modalities.yaml')
         #print("parsing completed!")
         #throttle ros topic
         
         
         
         for topic in self.modalityParser.actual_topic:
             if 'throttle_frequency' in list(topic.keys()) and '_throttle' in topic['name']:
                 command='rosrun topic_tools throttle messages '+topic['name'][:len(topic['name'])-len('_throttle')]+' '+str(topic['throttle_frequency'])      
                 self.throttle_processes.append(subprocess.Popen(command.split(), shell=False))
        
         print("parsing list of actions ...")
         self.actionParser=ActionParser(path_name=str(TRACEBOT_KNOWROB_PATH)+'/descriptions/domains/actions.yaml')
         print("parsing completed!")
         
         
         #Caching ontology classes for speeding up percept grounding
         print("Caching ontology classes to speed up percept grounding")
         self.cached_ontology_classes={}
         try:
             q = self.prolog.query("kb_call(is_class(A)).")
             for solution in q.solutions():
                 key=solution['A'].split("#").pop()
                 self.cached_ontology_classes[key.lower()]=solution['A']
             print("Caching ontology classes terminated successfully!!!")
             q.finish()
         except Exception as e:
                print("Caching ontology classes failed!")
         print('\n\n\n ***************** KNOWROB-TRACEBOT IS READY **************** \n\n\n')
         
##########################################################################################################################################################################             
	def cleanup(self):
            # killing throttle processes
            for proc in self.throttle_processes:
                try:    	                                                         
                     proc.send_signal(subprocess.signal.SIGKILL)
                     proc.communicate()
                     print('Killing throttling subprocess '+''+' ...')
                except Exception as e:
                     print('Terminating topic throttling failing ... ' +str(e))
            # killing neem recording processes
            for proc in psutil.process_iter():
                if ("record" in proc.name()) or  ("rosbag" in proc.name() and "record" in proc.cmdline()):
                    try:    	                                                         
                        proc.send_signal(subprocess.signal.SIGKILL)
                        proc.communicate()
                        print('Killing neem recording subprocess: '+proc.name()+' ...')
                    except Exception as e:
                        print('Terminating neem recording processes failing...')
            #cleaning unfinished bag files due to interruption
            if not self.with_clean_up_neem_experience:
               return
            ni=NeemInterface()
            list_bag_files=glob.glob(ni.neem_path+'/*Action_*.bag*')
            for file in list_bag_files:
                try:
                    os.remove(file)
                    print('Successfully deleted bag file: '+str(file))
                except Exception as e:
                    print('Failed to delete bag file. May be the file has been deleted meanwhile: '+str(e)) 

 
 
	def generate_nonverbalexplanation_graspability(self, confidence):
	   
            image = np.ones([100,100,3], dtype='uint8')*255
  
            # Window name in which image is displayed
            window_name = 'Image'
 
            # represents the top left corner of rectangle
            start_point1 = (40, 25)
            start_point2 = (60, 25)
            # represents the bottom right corner of rectangle
            end_point1 = (60, 75)
            end_point2 = (40, 75)
            # Black color in BGR
            color = (0, int(confidence*255), int((1-confidence)*255))
 
            # Line thickness of -1 px
            # Thickness of -1 will fill the entire shape
            thickness = -1
            
            points=[start_point1, start_point2, end_point1, end_point2,start_point1]
            c_x, c_y = np.mean(points, axis=0)
            
            #ANGLE
            ANGLE=np.arccos(confidence)
            
            corners= np.array(
            [
               [
                c_x + np.cos(ANGLE) * (px - c_x) - np.sin(ANGLE) * (py - c_x),
                c_y + np.sin(ANGLE) * (px - c_y) + np.cos(ANGLE) * (py - c_y)
               ]
               for px, py in points
            ]
            ).astype(int)
 
           
            image=cv2.drawContours(image, [corners], -1, color, thickness=cv2.FILLED)
            
            image=cv2.putText(image, "Distance", (5,15), cv2.FONT_HERSHEY_SIMPLEX , 0.4,(255,0,0), 1, cv2.LINE_AA)
            image = cv2.rectangle(image, start_point1, end_point1, (0,0,0), 3)
            
            return image
##########################################################################################################################################################################             
	def  KBCanisterInsertionSuccess(self, goal):
         global TRACEBOT_KNOWROB_PATH
         try:
             print("Processing goal ...")
             print("Verifying success of action: "+str(goal.action_id))
             result=KBVerifierResult()
             feedback=KBVerifierFeedback()
             result.decision=True
             result.confidence=0.7
             result.explanation="The target patient object is standing in the drain tray"
             result.recovery_explanation=''
             feedback.feedback=True
             ni = NeemInterface() #neem interface
             role_participant_lists={}
             role_participant_lists=ni.get_participant_with_role(goal.action_id)
             non_verbal_explanation={}
             
             if 'Patient' not in ([role.split('#').pop().split('_')[0] for role in list(role_participant_lists.keys())]):
                 result.decision=False
                 result.explanation='No target patient object could be found for this action'
                 result.confidence=1.0
                 result.recovery_explanation='Set the target patient object (to be inserted) before proceeding. Only in this manner can the action be successful and the verification proceed'
             else:
                 for role in list(role_participant_lists.keys()):
                   if 'Patient' in role.split('#').pop():
                        for participant in role_participant_lists[role]:
                            Object=participant
                            target_f=ni.modalityParser.get_expected_pose(object_key='canister', target_frame_key='map')[0]
                            target_frame=target_f['target_frame']
                            ni.belief_perceived_at(Object, alternative_frame=target_frame) 
                            object_rotation=ni.get_perceived_belief(Object)
                            support_position= np.array(target_f['expected_pose'][0:3], dtype='float')
                            support_normal=np.array(target_f['expected_pose'][3:6])
                            ni.belief_perceived_at(Object)
                            if object_rotation is None:
                               result.decision=False
                               result.confidence=1.0
                               result.explanation='Target patient object '+str(Object.split('#').pop())+' could be found, but 6D-pose could not be found'
                               result.recovery_explanation='The 6D-pose of the target patient object '+str(Object.split('#').pop())+'  has to be provided by the digital twin. Check that the digital twin is running properly.'
                            else:
                               object_position=object_rotation[0:3] #just take the position from the quaternion
                               object_rotation=object_rotation[3:6] #just take the axis from the quaternion
                               object_axis=np.array(object_rotation, dtype='float')
                               object_position=np.array(object_position, dtype='float')
                               
                               error1=np.abs(np.clip(np.dot(support_normal, object_axis)/(np.linalg.norm(support_normal)*np.linalg.norm(object_axis)), -1.0, 1.0))
                               error2=np.exp(-np.linalg.norm(support_position - object_position))
                               confidence=error1*error2
                               if confidence>0.8:
                                  result.decision=True
                                  result.explanation='Target patient object '+str(Object.split('#').pop())+' is standing in the drain tray and has therefore been inserted successfully. Pose Found='+str(object_rotation)
                                  result.confidence=confidence
                                  result.recovery_explanation=''
                               else:
                                  result.decision=False
                                  result.explanation='Target patient object '+str(Object.split('#').pop())+' is not standing properly in the drain tray'
                                  result.confidence=1-confidence
                                  result.recovery_explanation='Reperceive the canister  '+str(Object.split('#').pop())+' grasp it, take it back and insert it again into the tray'
         except Exception as e:
         	feedback.feedback=False
         	result.decision=False
         	result.confidence=1.0
         	result.recovery_explanation='To recover from this failure, please check the following message: (Action success verification failed: '+ str(e)+')'
         	
         	result.explanation='Verification process was interrupted for some reasons. Usual reason is the access of unavailable resources. The system is missing some resources necessary for the successful execution of this action.'
         	non_verbal_explanation=json.dumps('{}') #empty non verbal explanation
         	print("Action success verification failed: ", str(e))
         try:
                 ######### Setting non verbal explanation ########################################
             non_verbal_explanation={}
             confidence=result.confidence
             if not result.decision:
                confidence=1-confidence
             explanation_image=None
             try:
                    results=ni.GetSensor( goal.action_id, 'sensor_msgs/Image', 1)
                    for res in results:
                       if 'Robot@Tracebot.HeadRobotCamera@435D'.lower() in res['source'].lower() and 'Color'.lower() in res['value'].lower() and 'DT-Based'.lower() in res['modality'].lower():
                           print('modality:',res['modality'], 'source: ', res['source'], 'value: ', res['value'], 'length: ', len(res['data']))
                           explanation_image=res['data'][0]['message']
                           explanation_image=image =CvBridge().imgmsg_to_cv2(image, 'bgr8')
                           explanation_image=cv2.resize(explanation_image.copy(), (134, 100), interpolation=cv2.INTER_AREA)
             except Exception as e:
                    print('Error while extracting sensor data from DT: '+str(e))
             explanation_image1=self.generate_nonverbalexplanation_graspability(confidence) #imagine an image of size 100x100x3 of type uint8. you can load the image from disk with cv2.imread(file_path)
             if explanation_image is not None:
                explanation_image=np.concatenate([explanation_image[:,:,0:3],explanation_image1], axis=0)
             else:
                explanation_image=explanation_image1
             non_verbal_explanation['modality']='Visual-Based' #setting type of the content. It could be acoustic or odometric or purely tactile
             non_verbal_explanation['value_type']='data' #setting type of the content. it could be a path to the data already saved
             #non_verbal_explanation['value_type']='path' #setting type of the content. it could be a path to the data already saved
             non_verbal_explanation['format']=str(explanation_image.dtype) #setting type of the content. it could be float for acoustic for instance
             non_verbal_explanation['shape']=explanation_image.shape #setting shape of the content for restitution
             explanation_image=explanation_image.flatten() #flatten the  multidimensional array
             explanation_image=list(explanation_image) #turn array into list
             #"""=
             dtype=int
             if 'float' in str(non_verbal_explanation['format']):
                 dtype=float
             else:
                 if 'str' in str(non_verbal_explanation['format']):
                     dtype=str
             final_explanation_image=[dtype(explanation_image[i]) for i in range(len(explanation_image)) ] # turning list elements serializable
           
             non_verbal_explanation['data']=final_explanation_image
             non_verbal_explanation=json.dumps(non_verbal_explanation) #serializing the non verbal explanation 
         except Exception as e:
             print('Failure occured during insertion success check: '+str(e))
             non_verbal_explanation=json.dumps({}) #empty non verbal explanation
         result.nonverbal_explanation=non_verbal_explanation
        
        # Mock-up 
        # """
         result.decision=True
         result.confidence=0.7
         result.explanation="The target patient object is standing in the drain tray as expected"
         result.recovery_explanation='Nothing to recover here'
        # """
         print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ SUCCESSCHECKER ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
         
         print('DECISION: ',result.decision)
         print('CONFIDENCE: ',result.confidence)
         print('EXPLAINATION: ',result.explanation)
         print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ END SUCCESS CHECKER ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
         #result.decision=True
         self.canister_inserting_success_verifier_server.publish_feedback(feedback)
         self.canister_inserting_success_verifier_server.set_succeeded(result)
##########################################################################################################################################################################             

##########################################################################################################################################################################             
	def KBCanisterGraspingFeasibilityCheck(self, goal):
         global TRACEBOT_KNOWROB_PATH
         try:
             print("Processing goal ...")
             print("Verifying feasibility of action: "+str(goal.action_id))
             result=KBVerifierResult()
             feedback=KBVerifierFeedback()
             result.decision=True
             result.confidence=0.7
             result.explanation="The target patient object is lying on the support"
             result.recovery_explanation=''
             feedback.feedback=True
             ni = NeemInterface() #neem interface
             role_participant_lists={}
             role_participant_lists=ni.get_participant_with_role(goal.action_id)
             non_verbal_explanation={}
             
             if 'Patient' not in ([role.split('#').pop().split('_')[0] for role in list(role_participant_lists.keys())]):
                 result.decision=False
                 result.explanation='No target patient object could be found for this action'
                 result.confidence=1.0
                 result.recovery_explanation='Set the target patient object (to be grasped) before proceeding. Only in this manner can the feasibility verification proceed'
             else:
                 for role in list(role_participant_lists.keys()):
                   if 'Patient' in role.split('#').pop():
                        for participant in role_participant_lists[role]:
                            Object=participant
                            object_rotation=ni.get_perceived_belief(Object)
                            if object_rotation is None:
                               result.decision=False
                               result.confidence=1.0
                               result.explanation='Target patient object '+str(Object.split('#').pop())+' could be found, but 6D-pose could not be found'
                               result.recovery_explanation='The 6D-pose of the target patient object '+str(Object.split('#').pop())+'  (to be grasped) must be foremost estimated'
                            else:
                               object_rotation=object_rotation[3:6] #just take the axis from the quaternion
                               support_normal=np.array([0.,0.,1.])
                               object_axis=np.array(object_rotation, dtype='float')
                               error=np.abs(np.clip(np.dot(support_normal, object_axis)/(np.linalg.norm(support_normal)*np.linalg.norm(object_axis)), -1.0, 1.0))
                               confidence=error
                               if confidence>0.5:
                                  result.decision=True
                                  result.explanation='Target patient object '+str(Object.split('#').pop())+' is standing on the support and can be grasped'
                                  result.confidence=confidence
                                  result.recovery_explanation=''
                               else:
                                  result.decision=False
                                  result.explanation='Target patient object '+str(Object.split('#').pop())+' is lying on the support and cannot be grasped'
                                  result.confidence=1-confidence
                                  result.recovery_explanation='(Manually) place the target patient object  '+str(Object.split('#').pop())+' in standing position on the support. Then, perceive it again and grasp it' 
         except Exception as e:
         	feedback.feedback=False
         	result.decision=False
         	result.confidence=1.0
         	result.recovery_explanation='To recover from this failure, please check the following message: (Action feasibility verification failed: '+ str(e)+')'
         	result.explanation='Verification process was interrupted for some reasons. Usual reason is the access of unavailable resources. The system is missing some resources necessary for the feasibility of this action.'
         	non_verbal_explanation=json.dumps('{}') #empty non verbal explanation
         	print("Action feasibility verification failed: ", str(e))
         try:
                 ######### Setting non verbal explanation ########################################
             non_verbal_explanation={}
             confidence=result.confidence
             if not result.decision:
                confidence=1-confidence
             explanation_image=self.generate_nonverbalexplanation_graspability(confidence) #imagine an image of size 100x100x3 of type uint8. you can load the image from disk with cv2.imread(file_path)
             non_verbal_explanation['modality']='Visual-Based' #setting type of the content. It could be acoustic or odometric or purely tactile
             non_verbal_explanation['value_type']='data' #setting type of the content. it could be a path to the data already saved
             #non_verbal_explanation['value_type']='path' #setting type of the content. it could be a path to the data already saved
             non_verbal_explanation['format']=str(explanation_image.dtype) #setting type of the content. it could be float for acoustic for instance
             non_verbal_explanation['shape']=explanation_image.shape #setting shape of the content for restitution
             explanation_image=explanation_image.flatten() #flatten the  multidimensional array
             explanation_image=list(explanation_image) #turn array into list
             #"""=
             dtype=int
             if 'float' in str(non_verbal_explanation['format']):
                 dtype=float
             else:
                 if 'str' in str(non_verbal_explanation['format']):
                     dtype=str
             final_explanation_image=[dtype(explanation_image[i]) for i in range(len(explanation_image)) ] # turning list elements serializable
             #"""
             #non_verbal_explanation['value']=str(TRACEBOT_KNOWROB_PATH)+"/resources/GraspFeasibility.png" #setting the content of the image
             #non_verbal_explanation=json.dumps(non_verbal_explanation) #serializing the non verbal explanation
             non_verbal_explanation['data']=final_explanation_image
             non_verbal_explanation=json.dumps(non_verbal_explanation) #serializing the non verbal explanation 
         except Exception as e:
             print('Failure occured during grasp feasibility check: '+str(e))
             non_verbal_explanation=json.dumps({}) #empty non verbal explanation
         result.nonverbal_explanation=non_verbal_explanation
        # Mock-up 
        # """
         result.decision=True
         result.confidence=0.7
         result.explanation="The target patient object is standing on the support"
         result.recovery_explanation=''
        # """
         print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ FEASIBILITYCHECKER ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
         
         print('DECISION: ',result.decision)
         print('CONFIDENCE: ',result.confidence)
         print('EXPLAINATION: ',result.explanation)
         print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ END FEASIBILITYCHECKER ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
         #result.decision=True
         self.canister_grasping_feasibility_verifier_server.publish_feedback(feedback)
         self.canister_grasping_feasibility_verifier_server.set_succeeded(result)
##########################################################################################################################################################################             
	def KBGrabSuccessCheck(self, goal):
      
         print("Processing goal ...")
         print("Verifying success of action: "+str(goal.action_id))
         result=KBVerifierResult()
         feedback=KBVerifierFeedback()
         result.decision=True
         result.confidence=0.98+random.random()/50.0
         result.explanation="The location of the grasped object matches with the pose of the grasping gripper."
         feedback.feedback=True
         try:
            pass
         except Exception as e:
         	feedback.feedback=False
         	print("Action verification failed: ", str(e))
         self.grasping_verifier_server.publish_feedback(feedback)
         self.grasping_verifier_server.set_succeeded(result)
##########################################################################################################################################################################             
	def KBInsertSuccessCheck(self, goal):
      
         print("Processing goal ...")
         print("Verifying success of action: "+str(goal.action_id))
         result=KBVerifierResult()
         feedback=KBVerifierFeedback()
         result.decision=True
         result.confidence=0.98+random.random()/50.0
         result.explanation="The location of the inserted object matches with the pose of the destination insertee."
         feedback.feedback=True
         try:
            pass
         except Exception as e:
         	feedback.feedback=False
         	print("Action verification failed: ", str(e))
         self.inserting_verifier_server.publish_feedback(feedback)
         self.inserting_verifier_server.set_succeeded(result)
########################################################################################################################################################################## 
	def get_gripper_id(self, goal):
      
         print("Processing goal ...")
         print("target action id: "+str(goal.action_id))
         result=KBGetGripperIdResult()
         feedback=KBGetGripperIdFeedback()
         feedback.feedback=True
         try:
            ni = NeemInterface()
            result.gripper_id=ni.get_gripper_id(goal.action_id)
            print('gripper id found: ', result.gripper_id)
         except Exception as e:
         	feedback.feedback=False
         	print("Getting gripper id failed: ", str(e))
         self.action_gripper_id_server.publish_feedback(feedback)
         self.action_gripper_id_server.set_succeeded(result)
##########################################################################################################################################################################  
	def KBGetActionParticipantRole(self, goal):
      
         print("Processing goal ...")
         print("target action id: "+str(goal.action_id))
         result=KBGetActionParticipantRoleResult()
         feedback=KBGetActionParticipantRoleFeedback()
         feedback.feedback=True
         participants={}
         try:
            ni = NeemInterface()
            participants=ni.get_participant_with_role(goal.action_id)
            print('participants found: ', participants)
         except Exception as e:
         	feedback.feedback=False
         	print("Getting  action participants failed: ", str(e))
         result.participant_with_role=json.dumps(participants)
         self.get_participant_with_role_server.publish_feedback(feedback)
         self.get_participant_with_role_server.set_succeeded(result)
########################################################################################################################################################################## 
           
	def SmallObjectLocateCheck(self, goal):
      
         print("Processing goal ...")
         print("Verifying success of action: "+str(goal.action_id))
         result=KBVerifierResult()
         feedback=KBVerifierFeedback()
         result.decision=True
         result.confidence=0.98+random.random()/50.0
         result.explanation="The imagination of the detected objects at the given pose produce the same image as the bounded real image."
         feedback.feedback=True
         try:
            pass
         except Exception as e:
         	feedback.feedback=False
         	print("Action verification failed: ", str(e))
         self.locating_small_verifier_server.publish_feedback(feedback)
         self.locating_small_verifier_server.set_succeeded(result)

##########################################################################################################################################################################             
	def TransparentObjectLocateCheck(self, goal):
      
         print("Processing goal ...")
         print("Verifying success of action: "+str(goal.action_id))
         result=KBVerifierResult()
         feedback=KBVerifierFeedback()
         result.decision=True
         result.confidence=0.98+random.random()/50.0
         result.explanation="The imagination of the detected objects at the given pose produce the same image as the bounded real image."
         feedback.feedback=True
         try:
            pass
         except Exception as e:
         	feedback.feedback=False
         	print("Action verification failed: ", str(e))
         self.locating_transparent_verifier_server.publish_feedback(feedback)
         self.locating_transparent_verifier_server.set_succeeded(result)

##########################################################################################################################################################################    

         
	def executeFakeTBProcess(self, goal):
      
         print("Processing goal ...")
         scenarioName = goal.scenario_name
         result=KBFakeTBProcessResult()
         feedback=KBFakeTBProcessFeedback()
         result.status=False
         feedback.feedback=True
         try:
            if not os.path.exists(goal.path_name):
               try:
                    os.makedirs(goal.path_name)
               except Exception as e:
                    print('Failure when creating path: '+str(e))
                    a=1/0   
            path_name=goal.path_name
            if ("insert" in scenarioName.lower()) and ("canister" in scenarioName.lower()) and ("tray" in scenarioName.lower()):
               ##################### NEEMs Emulator ##########################	
               ni = NeemInterface()
               ni.executeNeemRecording(title=goal.scenario_name,path_name=path_name)
               ###############################################################
            else:
                result.status=False  
            print("Fake process executed !")             
         except Exception as e:
         	feedback.feedback=False
         	print("*********aa", str(e))
         self.fake_process_server.publish_feedback(feedback)
         self.fake_process_server.set_succeeded(result)
##########################################################################################################################################################################

	def executeAuditTrail(self, goal):
      
         print("Processing goal ...")
         path_name = goal.path_name
         result=KBAuditTrailResult()
         feedback=KBAuditTrailFeedback()
         result.status=False
         result.audit_trail=""
         feedback.feedback=True
         try:
            dirname=os.path.dirname(path_name)
            basename=os.path.basename(path_name)
            basename=basename.split('.')
            if os.path.exists(dirname) and len(basename)==2 and len(basename[0].rstrip().lstrip())>0 and basename.pop().lower()=='pdf':
               ##################### Audit Trail Emulator ##########################
               ni = NeemInterface()
               #complete audit trail generation with formatting
               audit_trail=ni.generateAuditTrail(path_name=path_name)
               formater=AuditTrailFormat(path_name, audit_trail)
               audit_trail=formater.buid_audit_trail()
               result.audit_trail=json.dumps(audit_trail)
               result.status=True
               print("Audit trail generation succeded !")
		###############################################################
            else:
                result.status=False  
                print("Audit trail generation failed: destination path is invalid !")             
         except Exception as e:
         	feedback.feedback=False
         	print("*********", str(e))
         self.audit_trail_server.publish_feedback(feedback)
         self.audit_trail_server.set_succeeded(result)
##########################################################################################################################################################################
         
	def executeListIndividual(self, goal):
      
         print("Processing goal ...")
         class_name = goal.class_name
         result=KBListIndividualResult()
         feedback=KBListIndividualFeedback()
         result.list_individuals=[]
         feedback.feedback=True
         try:
            query = self.prolog.query("kb_call([ instance_of(Instance, '"+class_name+ "')]).")
            for solution in query.solutions():
                result.list_individuals.append(solution['Instance'])
                print(solution['Instance'])
            query.finish()	              
         except Exception as e:
         	feedback.feedback=False
         	print("*********", str(e))
         self.list_individual_server.publish_feedback(feedback)
         self.list_individual_server.set_succeeded(result)


############################################################################################################################################################################
         
	def executeLoadOntology(self, goal):
      
         print("Processing goal ...")
         packageName = goal.package
         relativePath= goal.relative_path
         result=KBLoadOntologyResult()
         feedback=KBLoadOntologyFeedback()
         result.status=True
         feedback.feedback=True
         try:
            print("Loading ontology from:", packageName, relativePath)
            q=self.prolog.query("load_owl('package://"+str(packageName)+"/"+str(relativePath)+"').")
            #check if loading was successful
            solution=next(q.solutions())
            print("Loading ontology was successful")
            q.finish()	                
         except Exception as e:
         	result.status=False
         	feedback.feedback=False
         	print("*********", str(e))
         self.onto_load_server.publish_feedback(feedback)
         self.onto_load_server.set_succeeded(result)
##########################################################################################################################################################################
	def executeLoadDefaultOntology(self, goal):
      
      
         result=KBLoadDefaultOntologyResult()
         feedback=KBLoadDefaultOntologyFeedback()
         result.status=True
         feedback.feedback=True
         #Loading default KB
         try:
                packageName = "tracebot-knowrob"
                relativePath= "ontology/TraceBotOntology.owl"
                print("Loading ontology from:", packageName, relativePath)
                q=self.prolog.query("load_owl('package://"+str(packageName)+"/"+str(relativePath)+"').")
                q.finish()    
                print("Default ontology loaded successfully")  
                
                packageName = "tracebot-knowrob"
                relativePath= "ontology/SOMA-TraceBot.owl"
                print("Loading ontology from:", packageName, relativePath)
                q=self.prolog.query("load_owl('package://"+str(packageName)+"/"+str(relativePath)+"').")
                q.finish()    
                print("Default ontology loaded successfully")     
         except Exception as e:
                print("Loading default ontology KB failed: ", str(e))
                result.status=False
                feedback.feedback=False
                print("*********", str(e))
         self.onto_load_default_server.publish_feedback(feedback)
         self.onto_load_default_server.set_succeeded(result)


##########################################################################################################################################################################
         
	def executeQueryKnowledge(self, goal):
      
		print("Processing goal ...")

		result=KBQueryKnowledgeResult()
		feedback=KBQueryKnowledgeFeedback()
		result.results=[]
		feedback.feedback=True
		try:
			q = self.prolog.query(goal.query)
			for solution in q.solutions():
				result.results.append(str(solution))
				print(str(solution))
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.query_knowledge_server.publish_feedback(feedback)
		self.query_knowledge_server.set_succeeded(result)
##########################################################################################################################################################################
         
         
	def executeSubClass(self, goal):
		
		print("Processing goal ...")

		result=KBSubClassResult()
		feedback=KBSubClassFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
			if goal.is_sub:
				q = self.prolog.query("kb_call(subclass_of(A, '"+goal.class_name+"')).")
			else:
				q = self.prolog.query("kb_call(subclass_of('"+goal.class_name+"', A)).")
			for solution in q.solutions():
				result.classes.append(solution['A'])
				print(solution['A'])
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.subclass_server.publish_feedback(feedback)
		self.subclass_server.set_succeeded(result)
##########################################################################################################################################################################
	def executeActionFeasibility(self, goal):
		print("Processing goal ...")
		result=KBActionFeasibilityVerificationResult()
		feedback=KBActionFeasibilityVerificationFeedback()
		try:
			ni = NeemInterface()
			runtime_verification=goal.runtime
			action_id=goal.action_id
			delete_local_experience=goal.delete_local_experience
			[decision, confidence, explanation, nonverbal_explanation, recovery_explanation]=ni.event_feasibility_verification(action_id, runtime_verification,delete_local_experience=delete_local_experience)	
			result.feasibility=decision
			result.confidence=confidence
			result.decision_explanation=explanation
			result.nonverbal_explanation=nonverbal_explanation
			result.recovery_explanation=recovery_explanation	
		except Exception as e:
			feedback.feedback=False
		feedback.feedback=True
		self.action_feasibility_server.publish_feedback(feedback)
		self.action_feasibility_server.set_succeeded(result)		
##########################################################################################################################################################################
	def executeActionSuccess(self, goal):
		print("Processing goal ...")
		result=KBActionSuccessVerificationResult()
		feedback=KBActionSuccessVerificationFeedback()
		try:
			ni = NeemInterface()
			runtime_verification=goal.runtime
			action_id=goal.action_id
			delete_local_experience=goal.delete_local_experience
			[decision, confidence, explanation, nonverbal_explanation, recovery_explanation]=ni.event_success_verification(action_id, runtime_verification,delete_local_experience=delete_local_experience)	
			result.success=decision
			result.confidence=confidence
			result.decision_explanation=explanation
			result.nonverbal_explanation=nonverbal_explanation
			result.recovery_explanation=recovery_explanation	
		except Exception as e:
			feedback.feedback=False
		feedback.feedback=True
		self.action_success_server.publish_feedback(feedback)
		self.action_success_server.set_succeeded(result)
##########################################################################################################################################################################
	def executeGetClassId(self, goal):
		
		print("Processing goal ...")

		result=KBGetClassIdResult()
		feedback=KBGetClassIdFeedback()
		result.list_ids=[]
		feedback.feedback=True
		try:
			if goal.exact:
				result.list_ids.append(self.cached_ontology_classes[goal.classname.lower()])
				print(self.cached_ontology_classes[goal.classname.lower()])
			else:
				class_name=goal.classname.lower()
				for key in self.cached_ontology_classes.keys():
					if class_name in key:
						result.list_ids.append(self.cached_ontology_classes[key])	
						print(self.cached_ontology_classes[key])		
			#q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.get_class_id_server.publish_feedback(feedback)
		self.get_class_id_server.set_succeeded(result)
##########################################################################################################################################################################
	         
	def executeReset(self, goal):
		
		print("Processing goal ...")

		result=KBResetResult()
		feedback=KBResetFeedback()
		result.status=True
		feedback.feedback=True
		try:
			q = self.prolog.query("mng_drop('roslog', 'triples')")
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			result.status=False
			print("*********", str(e))
		self.reset_server.publish_feedback(feedback)
		self.reset_server.set_succeeded(result)

##########################################################################################################################################################################
	         
	def executeListClass(self, goal):
		
		print("Processing goal ...")

		result=KBListClassResult()
		feedback=KBListClassFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
			q = self.prolog.query("kb_call(is_class(A)).")
			for solution in q.solutions():
				if True:
					result.classes.append(solution['A'])
					print(solution['A'])
					self.list_class_server.publish_feedback(feedback)
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.list_class_server.publish_feedback(feedback)
		self.list_class_server.set_succeeded(result)
##########################################################################################################################################################################

 
	def executeListProperty(self, goal):
		
		print("Processing goal ...")

		result=KBListPropertyResult()
		feedback=KBListPropertyFeedback()
		result.properties=[]
		feedback.feedback=True
		try:
			q = self.prolog.query("kb_call(is_property(A)).")
			for solution in q.solutions():
				if True:
					result.properties.append(solution['A'])
					print(solution['A'])
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.list_property_server.publish_feedback(feedback)
		self.list_property_server.set_succeeded(result)
##########################################################################################################################################################################
	
	def parseAttribute(self, s):
		nature=""
		delimiter=""
		s=s.rstrip().lstrip().split(" ")
		if len(s)>1:
			nature=s[0]
			delimiter=s.pop()
		return (nature, delimiter)
##########################################################################################################################################################################
		
	def executeObjectProperty(self, goal):
		
		print("Processing goal ...")

		result=KBObjectPropertyResult()
		feedback=KBObjectPropertyFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
		
			if goal.quantifier == "only" or goal.quantifier == "some":
				q = self.prolog.query("kb_call((subclass_of('"+goal.class_name+"', C), has_description(C,"+ goal.quantifier+"('"+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+goal.class_name+"', "+ goal.quantifier+"('"+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
			else:
				(nature, delimiter)=self.parseAttribute(goal.quantifier)
				q = self.prolog.query("kb_call((subclass_of('"+goal.class_name+"', C), has_description(C,"+ nature+"('"+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+goal.class_name+"', "+ nature+"('"+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.object_property_server.publish_feedback(feedback)
		self.object_property_server.set_succeeded(result)
##########################################################################################################################################################################
				
	def executeDataProperty(self, goal):
		
		print("Processing goal ...")

		result=KBDataPropertyResult()
		feedback=KBDataPropertyFeedback()
		result.values=[]
		feedback.feedback=True
		try:
		
			if goal.quantifier == "only" or goal.quantifier == "some" or goal.quantifier == "value":
				q = self.prolog.query("kb_call((subclass_of('"+goal.class_name+"', C), has_description(C,"+ goal.quantifier+"('"+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+goal.class_name+"', "+ goal.quantifier+"('"+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
			else:
				(nature, delimiter)=self.parseAttribute(goal.quantifier)
				q = self.prolog.query("kb_call((subclass_of('"+goal.class_name+"', C), has_description(C,"+ nature+"('"+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+goal.class_name+"', "+ nature+"('"+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
			                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.data_property_server.publish_feedback(feedback)
		self.data_property_server.set_succeeded(result)
##########################################################################################################################################################################
		
	def executeNewIndividual(self, goal):
		
		print("Processing goal ...")

		result=KBNewIndividualResult()
		feedback=KBNewIndividualFeedback()
		result.object_id=""
		feedback.feedback=True
		try:
			
			q = self.prolog.query("kb_project([new_iri(A,'"+goal.class_name+"'), has_type(A,'"+goal.class_name+"')]).")
			for solution in q.solutions():
				result.object_id=solution['A']
				print(solution['A'])
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.new_individual_server.publish_feedback(feedback)
		self.new_individual_server.set_succeeded(result)
##########################################################################################################################################################################
	
	def computeChildInstanceIds(self, goal, parent_id):
		pair_ids=[]	
		part_relation=goal.class_name.split("#")[0]+"#"+"has_part"
		part_filter=["Pose"]
		
		try:
			if parent_id=="":
				#instantiating main object
				q = self.prolog.query("kb_project([new_iri(A,'"+goal.class_name+"'), has_type(A,'"+goal.class_name+"')]).")
				for solution in q.solutions():
					object_id=solution['A']
					print(solution['A'])
				q.finish()
				#adding pair_ids
				pair=KBNewComplexIndividualOutput()
				pair.parent_id=parent_id
				pair.object_id=object_id
				pair_ids.append(pair)
			else:
				object_id=parent_id                
			
			#Searching the direct parts of main object
			sub_parts=[]
			sub_full_parts=[]
			q = self.prolog.query("kb_call([subclass_of('"+goal.class_name+"', A), has_description(A, exactly('"+part_relation+"',1,B))]).")
			for solution in q.solutions():
				if solution['B'].split("#").pop() not in part_filter:
					sub_parts.append(solution['B'].split("#").pop())
					sub_full_parts.append(solution['B'])
					print(solution['B'])
			q.finish() 
			
			for i in range(len(sub_parts)):
				part_id=sub_parts[i]
				part_full_id=sub_full_parts[i]
				
				#Instantiating the direct parts of the main objects
				q = self.prolog.query("kb_project([has_type('"+object_id+"@"+part_id+"','"+part_full_id+"')]).")
				q.finish()
				
				#instantiating aggregation between parent and child instances
				q = self.prolog.query("kb_project([triple('"+object_id+"','"+part_relation+"','"+object_id+"@"+part_id+"')]).")
				q.finish()
				
				#adding pair_ids
				pair=KBNewComplexIndividualOutput()
				pair.parent_id=object_id
				pair.object_id=object_id+"@"+part_id
				pair_ids.append(pair)
				
				#setting the new goal
				new_goal=KBNewComplexIndividualGoal()
				new_goal.class_name=part_full_id
				parent_id=object_id+"@"+part_id
				pair_ids=pair_ids+self.computeChildInstanceIds(new_goal, parent_id)			 
			
			return pair_ids
		except Exception as e:
			print("*********", str(e))
			return pair_ids
			
		
	def executeNewComplexIndividual(self, goal):
		
		print("Processing goal ...")

		result=KBNewComplexIndividualResult()
		feedback=KBNewComplexIndividualFeedback()
		result.pair_ids=[]

		feedback.feedback=True
		
		try:
						 
			result.pair_ids=self.computeChildInstanceIds( goal, "")
			print(result.pair_ids)
		
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		
		self.new_cindividual_server.publish_feedback(feedback)
		self.new_cindividual_server.set_succeeded(result)
##########################################################################################################################################################################	
		
		
		
	def executeCommonPose(self, goal):
		
		print("Processing goal ...")

		result=KBCommonPoseResult()
		feedback=KBCommonPoseFeedback()
		feedback.feedback=True
		try:
			if goal.class_name=='Canister' and goal.pose_type=='Grasp':
			
				#accessing grasp pose
				
				q = self.prolog.query('kb_call([subclass_of(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#CanisterGraspInfo\", A),has_description(A, exactly(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_pose\",1,C)), has_description(C,value(\"http://www.ease-crc.org/ont/SOMA.owl#hasPositionData\",D))]).')
				for solution in q.solutions():
					pose0=solution['D'].split(" ")
					pose=[c for c in pose0 if c!=""]
					result.pose.position.x=float(pose[0])
					result.pose.position.y=float(pose[1])
					result.pose.position.z=float(pose[2])
					result.pose.orientation.x=float(pose[3])
					result.pose.orientation.y=float(pose[4])
					result.pose.orientation.z=float(pose[5])
					result.pose.orientation.w=float(pose[6])
					break
				q.finish()
				
				#accessing motion direction
				q = self.prolog.query('kb_call([subclass_of(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#CanisterGraspInfo\", A),has_description(A, exactly(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#hasMotionDirection\",1,C)), has_description(C,value(\"http://www.ease-crc.org/ont/SOMA.owl#hasPositionData\",D))]).')
				for solution in q.solutions():
					pose0=solution['D'].split(" ")
					pose=[c for c in pose0 if c!=""]
					result.offset.x=float(pose[0])
					result.offset.y=float(pose[1])
					result.offset.z=float(pose[2])
					break
				q.finish()
				
				#accessing grasp type
				q = self.prolog.query('kb_call([subclass_of(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#CanisterGraspInfo\", A),has_description(A, exactly(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#hasGraspType\",1,C)),has_description(C, intersection_of(D)), nth0(0,D,E1), nth0(1,D, E2), has_description(E1,value(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#hasCustomGraspTypeValue\",F)), has_description(E2,value(\"http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#hasGraspTypeValue\",G))]).')
				for solution in q.solutions():
					custom=solution['F'].split(" ")
					custom0=[c for c in custom if c!=""]
					custom1=np.array([float(c) for c in custom0],dtype='float64')
					result.grasp_type.grasp_type_id=int(solution['G'])
					result.grasp_type.custom_grasp=custom1.copy()
					print(result)
					break
				q.finish()
		
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.common_pose_server.publish_feedback(feedback)
		self.common_pose_server.set_succeeded(result)
##########################################################################################################################################################################
				


if __name__ == '__main__':
 
    rospy.init_node('tracebot_knowrob_node')
    server = TraceBotKnowrobServer()
    rospy.on_shutdown(server.cleanup)
    rospy.spin()
 
    
  
