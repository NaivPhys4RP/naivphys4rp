#!/usr/bin/env python3
import rospy
import tf2_ros
import roslib
import sys
import os
import re
import functools
import time
import random
import rospkg
import glob
import actionlib
roslib.load_manifest('rosprolog')
roslib.load_manifest('tracebot_msgs')
from tracebot_msgs.msg import *
rospack = rospkg.RosPack()
TRACEBOT_KNOWROB_PATH=rospack.get_path('tracebot-knowrob')
from datetime import datetime
try:
    from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
    from rosprolog_client import PrologException, Prolog 
    print('Loading rosprolog ...') 
import json
from functional_verification.ModalityParser import *
from functional_verification.VerifierParser import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,SCRIPT_DIR )


class NeemInterface:
    def __init__(self):
        self.neem_experience_folder='experience'
        self.nonverbal_explanation_modality='Visual-Based'
        self.nonverbal_explanation_source='Robot@Tracebot.SceneRobotCamera@435D'
        self.nonverbal_explanation_source1='Robot@Tracebot.HeadRobotCamera@435D'
        self.nonverbal_perception_explanation_source='Robot@Tracebot.HeadRobotCamera@435D'
        #self.nonverbal_explanation_topic='compressed_color_image'
        self.nonverbal_explanation_topic='raw_color_image'
        self.nonverbal_perception_explanation_topic='raw_locate_result'
        self.explanation_placeholder='Not yet resolved'
        self.nonverbal_explanation_folder='resources/audit_trail_evidences'
        self.explanation_connectors=['Also,', 'Additionally', 'Furthermore', 'Moreover']
        self.perception_action_prefix=['recogniz', 'sens', 'locat', 'pos']
        """
        self.tactile_specific_tasks=['http://www.ease-crc.org/ont/SOMA.owl#Grasping', 
                                       'http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#Inserting', 
                                       'http://www.ease-crc.org/ont/SOMA.owl#Pushing',
                                       'http://www.ease-crc.org/ont/SOMA.owl#Closing',
                                       'http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceablePickingUp']
        """
        self.tactile_specific_tasks=[{'name':'http://www.ease-crc.org/ont/SOMA.owl#Pushing', 'participants':{}}]
        rospy.logwarn("NeemInterface: Wait for prolog service.")
        self.status_bool={'http://www.ease-crc.org/ont/SOMA.owl#ExecutionState_Succeeded':1,'http://www.ease-crc.org/ont/SOMA.owl#ExecutionState_Failed':0}
        self.bool_status={1:'http://www.ease-crc.org/ont/SOMA.owl#ExecutionState_Succeeded',0:'http://www.ease-crc.org/ont/SOMA.owl#ExecutionState_Failed'}
        self.executive_modules={'http://www.ease-crc.org/ont/SOMA.owl#Manipulating':{'Designator':'Manipulation', 'SubClass':[]}, 'http://www.ease-crc.org/ont/SOMA.owl#Perceiving':{'Designator':'Perception', 'SubClass':[]}, 'http://www.ease-crc.org/ont/SOMA.owl#MentalTask':{'Designator':'Reasoning', 'SubClass':[]}, 'http://www.ease-crc.org/ont/SOMA.owl#Planning':{'Designator':'Planning', 'SubClass':[]},'http://www.ease-crc.org/ont/SOMA.owl#Actuating':{'Designator':'Manipulation', 'SubClass':[]}, 'http://www.ease-crc.org/ont/SOMA.owl#ModifyingPhysicalObject':{'Designator':'Manipulation', 'SubClass':[]}, 'http://www.ease-crc.org/ont/SOMA.owl#AssumingPose':{'Designator':'Manipulation', 'SubClass':[]}}
        try:
            self.prolog = Prolog(timeout=10, wait_for_services=True)
            rospy.logwarn("NeemInterface: Connected to Prolog service.")
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        self.neem_path=os.path.expanduser(rospy.get_param('neem_path',''))
        if not os.path.exists(self.neem_path):
               try:
                    os.makedirs(self.neem_path+'/'+self.neem_experience_folder)
               except Exception as e:
                    print('Failure when creating path for Neem Experiences: '+str(e))
                    a=1/0
        else:
             if not os.path.exists(self.neem_path+'/'+self.neem_experience_folder):
                 try:
                     os.makedirs(self.neem_path+'/'+self.neem_experience_folder)
                 except Exception as e:
                     print('Failure when creating path for Neem Experiences: '+str(e))
                     a=1/0
        #parsing info source modalities
        print("parsing info source modalities ...")
        self.modalityParser=ModalityParser(path_name=str(TRACEBOT_KNOWROB_PATH)+'/descriptions/domains/modalities.yaml')
        print("parsing completed!")
        
        #parsing verifiers
        print("parsing list of verifiers ...")
        self.verifierParser=VerifierParser(path_name=str(TRACEBOT_KNOWROB_PATH)+'/descriptions/verifiers')
        print("parsing completed!")
        #self.load_neem_interface()
        
        self.class_id_client = actionlib.SimpleActionClient('tracebot_knowrob_class_id', KBGetClassIdAction)
        print("Client ontology class id is started !")
        print("Waiting for action server class id...")
        self.class_id_client.wait_for_server()
        print("Action server client ids loaded")
        
        self.new_individual_client = actionlib.SimpleActionClient('tracebot_knowrob_individual', KBNewIndividualAction)
        print("Client ontology new individual is started !")
        print("Waiting for action server new individual...")
        self.new_individual_client.wait_for_server()
        print("Action server new individual loaded")

########################################################################################################################################################################## 
    def load_neem_interface(self):

        try:
            query = self.prolog.query("register_ros_package(neem-interface).")
            solution = next(query.solutions())
            print(solution)
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            
            
########################################################################################################################################################################## 
    def verify_action(self, action_server='', action_id=''):
        try:
              self.verifier_client = actionlib.SimpleActionClient(action_server, KBVerifierAction)
              print("Client verifier is started !")
              print("Waiting for verifier server ...")
              if not self.verifier_client.wait_for_server(timeout = rospy.Duration(3)):
                 return None
              print("Verifier server and client loaded")
              goal = KBVerifierGoal()
              goal.action_id = action_id
              self.verifier_client.send_goal(goal)
              self.verifier_client.wait_for_result()
              results = self.verifier_client.get_result()
              return results
        except Exception as e: 
              rospy.logwarn("NeemInterface: %s" % str(e))
              return None
          
########################################################################################################################################################################## 
    def start_episode(self, ActionType):   

        #start and episode
        EnvOwl = "package://tracebot-knowrob/ontology/TraceBot-Ontology.owl"
        EnvOwlIndiName = ""
        EnvUrdf = "package://tracebot-knowrob/urdf/tracebot.urdf"
        EnvUrdfPrefix = ""
        AgentOwl = "package://tracebot-knowrob/ontology/TraceBot-Ontology.owl"
        AgentOwlIndiName = "http://www.semanticweb.org/smile/ontologies/2022/2/TraceBot#Robot@TraceBot"
        AgentUrdf = "package://tracebot-knowrob/urdf/tracebot.urdf"        
        Episode=""
        RootAction=""
        return self.start_episode_with_param(Episode, RootAction, ActionType, EnvOwl, EnvOwlIndiName, EnvUrdf, EnvUrdfPrefix, AgentOwl, AgentOwlIndiName, AgentUrdf)

########################################################################################################################################################################## 
    def start_episode_with_param(self, Episode, Action, ActionType, EnvOwl, EnvOwlIndiName, EnvUrdf, EnvUrdfPrefix, AgentOwl, AgentOwlIndiName, AgentUrdf):
        """
        Called at the start of a neem recording. Example parameter:

        EnvOwl = "'package://iai_semantic_maps/owl/kitchen.owl'"
        EnvOwlIndiName = "'http://knowrob.org/kb/IAI-kitchen.owl#iai_kitchen_room_link'"
        EnvUrdf = "'package://iai_kitchen/urdf_obj/kitchen.urdf'"
        EnvUrdfPrefix = "'iai_kitchen/'"
        AgentOwl = "'package://knowrob/owl/robots/PR2.owl'"
        AgentOwlIndiName = "'http://knowrob.org/kb/PR2.owl#PR2_0'"
        AgentUrdf = "'package://knowrob/urdf/pr2.urdf'"
        """

        try:
            
            #start neem narrative
            query = self.prolog.query("mem_episode_start(Episode, Action  , '" + ActionType + "', '" + EnvOwl + "', '" + EnvOwlIndiName + "', '" + EnvUrdf + "', '" + EnvUrdfPrefix + "', '" + AgentOwl + "', '" + AgentOwlIndiName + "', '" + AgentUrdf + "').")
           
            for solution in query.solutions():
                pass
            query.finish()
            #start neem experience
            if True:
               self.modalityParser.neem_experience_start(destination_folder=self.neem_path,root_name=solution['Action'].split("#").pop()+'.bag')
            return (solution['Episode'], solution['Action'])
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            #close neem_experience in case of exception
            if True:
               self.modalityParser.neem_experience_stop(destination_folder=self.neem_path, basefolder=self.neem_experience_folder)
            return None
########################################################################################################################################################################## 

    def stop_episode_V1(self, NeemPath):
        """
        Called at the end of a neem recording, NeemPath points to the place to store the neem
        """
        NeemPath=self.neem_path
        try:
            #stop neem experience
            time.sleep(3.0) # this sleep is necessary for the neem experience recorder to collect evidences from low-frequency data sources (e.g., sensor) 
            self.modalityParser.neem_experience_stop(destination_folder=self.neem_path, basefolder=self.neem_experience_folder)
            #stop neem narrative    
            query = self.prolog.query("mem_episode_stop('" + NeemPath + "').")
            query.finish()
            print('Starting automated planning and execution of action verification tasks ...')
            Episode=self.get_current_episode()
        except Exception as e:
            rospy.logwarn("Error while stopping episode recording: %s" % str(e))
##########################################################################################################################################################################

    def getClassId(self, class_key):
        goal = KBGetClassIdGoal()
        goal.exact = False
        goal.classname = class_key
        self.class_id_client.send_goal(goal)
        self.class_id_client.wait_for_result()
        results = self.class_id_client.get_result()
        return results.list_ids
         
##########################################################################################################################################################################
    def getNewInstance(self, class_id):
        goal = KBNewIndividualGoal()
        goal.class_name = class_id
        self.new_individual_client.send_goal(goal)
        self.new_individual_client.wait_for_result()
        results = self.new_individual_client.get_result()
        return results.object_id
##########################################################################################################################################################################

    def begin_skill(self, ParentAction, skill_type):
        """
        Called at the start of an action in order to add the skill to the neem. skill_type is unique to each skill and must match the ontology
        e.g. "'http://www.ease-crc.org/ont/SOMA.owl#Transporting'"

        returns id created by knworob
        """
        try:
            skill_id=""
            skill_id=self.add_subaction_with_task(ParentAction, skill_id, skill_type)
            self.begin_event(skill_id)
            if False:
                   self.modalityParser.neem_experience_start(destination_folder=self.neem_path, root_name=skill_id.split("#").pop()+'.bag')
            participants=self.get_participant_with_role(skill_id)
            
            tactile_specific_tasks=[task['name'] for task in self.tactile_specific_tasks]
            print('%%%%%%%SEARCHING 1 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            if skill_type in tactile_specific_tasks:
                 print('%%%%%%%SEARCHING 2 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')            
                 list_index=self.modalityParser.find_all_index(skill_type, tactile_specific_tasks)
                 print(list_index)
                 for i in list_index:
                     print('%%%%%%%SEARCHING 3 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                     print(self.tactile_specific_tasks[i]['participants'], participants)
                     if self.modalityParser.are_dict_matching(self.tactile_specific_tasks[i]['participants'], participants):
                             
                             print('%%%%%%%SEARCHING 4 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                             self.modalityParser.tactile_specific_actions.append(skill_id)
                             print('%%%%%%%SEARCHING 5 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                             self.modalityParser.tactile_experience_start() #collecting tactile data separately
                             print('\n\n\n\n\n\n\n\n %%%%%%%%%%%%%%%%%%%%%%%%%%% CEA TACTILE RECORDING: ', skill_type,skill_id, ' %%%%%%%%%%%%%%%%% \n\n\n\n\n\n')
                             break
            print(skill_type, skill_id, ParentAction)
            return skill_id
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            return ""
########################################################################################################################################################################## 
  
    def end_skill(self, skill_id):
        """
        Called at the end of an action in order to register the time the skill finished and whether or not it was successful
        """
        try:
            self.end_event(skill_id)
            time.sleep(1.0)
            #update object pose for perception-related action
            participants=self.get_participant_with_role(skill_id)
            is_perception=False
            designator,task=self.get_current_event_designator(skill_id)
            for action_key in self.perception_action_prefix:
                if action_key.lower() in task.split('#').pop().lower():
                   is_perception=True
                   break
            if is_perception:
               for role in participants.keys():
                   if 'Patient'.lower() in role.lower() or 'Stimulus'.lower() in role.lower():
                       print('\n\n\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UPDATING OBJECT POSE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ /n/n/n')
                       self.belief_perceived_at(participants[role][0])
                       break
            if skill_id in self.modalityParser.tactile_specific_actions:
                  self.modalityParser.tactile_experience_stop() #stopping tactile sensor data recording
            if False:
                self.modalityParser.neem_experience_stop(destination_folder=self.neem_path, basefolder=self.neem_experience_folder, root_name=skill_id.split("#").pop()+'.bag')
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
########################################################################################################################################################################## 


    def belief_perceived_at(self, Object, alternative_frame=None):
        
        tf_topics=self.modalityParser.get_dt_transform_topics( value_key='dynamic')[0]
        topic=tf_topics['name']
        local_frame=Object
        if alternative_frame is not None:
            parent_frame=alternative_frame
        else:
            parent_frame=tf_topics['world_frame']
        max_iter=20
        sleep_time=60.0
        tfBuffer = tf2_ros.Buffer()
        listener = tf2_ros.TransformListener(tfBuffer)
        # rospy.init_node('locate_object')
        Found=True
        trans= Nonerans is not Non
        rate = rospy.Rate(sleep_time)
        while (trans is None) and max_iter>0:
              max_iter=max_iter-1
              try:
                 trans = tfBuffer.lookup_transform(local_frame, parent_frame, rospy.Time(0))
              except Exception as e:
                 print(str(e)) 
              rate.sleep()
        if trans is not None:
             tx=trans.transform.translation.x
             ty=trans.transform.translation.y
             tz=trans.transform.translation.z
             rx=trans.transform.rotation.x
             ry=trans.transform.rotation.y
             rz=trans.transform.rotation.z
             rw=trans.transform.rotation.w
             Pose=[tx,ty,tz,rx,ry,rz,rw]   
             """ 
             print("\n\n\n\n\n\n\n\ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ DETECTED OBJECT POSE: ",Pose, Object, local_frame  " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n\n\n\n\n\n\n\n" )
             """
        else:
             Pose=[0.2, 0.794, 1.174,  0, 0, 1, 0 ] 
             Found= False
             """
             print("\n\n\n\n\n\n\n\ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  OBJECT POSE FAILED: ",Pose, Object, local_frame  " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n\n\n\n\n\n\n\n" )
             """
        print('Removing previous object pose')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Object+ "','http://www.semanticweb.org/smile/ontologies/2022/2/TraceBot#has_pose', Pose)).")
            query.finish()
        except Exception as e:
            print('Error while retracting previous object pose: '+str(e))
        try:
           print('Setting actual object pose')
           self.prolog.query("kb_project(triple('"+Object+ "','http://www.semanticweb.org/smile/ontologies/2022/2/TraceBot#has_pose', '"+json.dumps(Pose)+"')).")
           Found= True
        except Exception as e:
            print('Error while resetting object pose: '+str(e))
            Found=False
        return Found
         


########################################################################################################################################################################## 
    def get_perceived_belief(self, ObjectType):
        """
        Called when an object is perceived
        ObjectType = 'http://www.ease-crc.org/ont/SOMA.owl#Bowl',
        Mesh = 'package://kitchen_object_meshes/bowl.dae',
        Rotation = [-1.0,0.0,0.0,1.0],
        Object 'http://www.ease-crc.org/ont/SOMA.owl#SM_Bowl_2'
        """

        try:
            query = self.prolog.query("kb_call(triple('"+ObjectType+ "','http://www.semanticweb.org/smile/ontologies/2022/2/TraceBot#has_pose', Pose)).")
            solution = next(query.solutions())
            query.finish()
            return json.loads(solution['Pose'])
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            return None
########################################################################################################################################################################## 
    def add_participant_with_role(self, Action, ObjectId, RoleId):
        """
        Called to add agents/targets to a skill. E.g. Changing the state of a drawer
        Action = 'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Action_OCUKMQHD'
        ObjectId = 'drawer_sinkblock_middle_open',
        RoleId = 'http://www.ease-crc.org/ont/SOMA.owl#AlteredObject_VBGSYTFS'
        """
        try:
            query = self.prolog.query("kb_project(triple('" + Action + "', '" +"http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasParticipant"+ "', '" + RoleId + "')).")
            query.finish()
            query = self.prolog.query("kb_project(triple('" + ObjectId + "', '" +"http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasRole"+ "', '" + RoleId + "')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 
    def get_participant_with_role(self, Action):
        participant_with_role={}  
        try:
            query = self.prolog.query("kb_call([triple('" + Action + "', 'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasParticipant', Role),triple(Object, 'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasRole', Role)]).")
            
            for solution in query.solutions():
                if solution['Role'] in list(participant_with_role.keys()):
                    participant_with_role[solution['Role']].append(solution['Object'])
                else:
                    participant_with_role[solution['Role']]=[solution['Object']]
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return participant_with_role
########################################################################################################################################################################## 
    def get_participant_with_role(self, Action):
        participant_with_role={}  
        try:
            query = self.prolog.query("kb_call([triple('" + Action + "', 'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasParticipant', Role),triple(Object, 'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasRole', Role)]).")
            
            for solution in query.solutions():
                if solution['Role'].split('_')[0] in list(participant_with_role.keys()):
                    participant_with_role[solution['Role'].split('_')[0]].append(solution['Object'])
                else:
                    participant_with_role[solution['Role'].split('_')[0]]=[solution['Object']]
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return participant_with_role
##########################################################################################################################################################################


    def get_gripper_id(self, Action):
        participant_with_role={} 
        gripper_id=3 
        found_right=False
        found_left=False
        target_role=None
        try:
            participant_with_role=self.get_participant_with_role(Action)
            for role in participant_with_role.keys():
                  if 'Actor' in role or 'Agent' in role:
                        target_role=role
                        break
            if target_role is not None:
                for participant in participant_with_role[target_role]:
                          if 'right' in participant.lower():
                               found_right=True
                          else:
                             if 'left' in participant.lower():
                               found_left=True
                          if found_right and found_left:
                             break
                if found_right and found_left:
                   gripper_id=2
                else:
                   if found_right:
                      gripper_id=0
                   else: 
                      if found_left:
                         gripper_id=1
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return gripper_id
########################################################################################################################################################################## 
    def serialize_participant_with_role(self, list_participant_with_role):
        participant_with_role=''
        try:
            for role in list(list_participant_with_role.keys()):
                for participant in list_participant_with_role[role]:
                    participant_with_role=participant_with_role+role.split('#').pop()+': \n'
                    participant_with_role=participant_with_role+participant.split('#').pop()+';        \n'
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return participant_with_role
########################################################################################################################################################################## 
    def add_grasping_parameter(self, Action,GraspingOrientationType):

        try:
            query = self.prolog.query("add_grasping_parameter('" + Action + "', '" + GraspingOrientationType + "').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
########################################################################################################################################################################## 

    def add_comment(self, Entity,Comment):

        try:
            query = self.prolog.query("add_comment('" + Entity + "','" + Comment + "').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
########################################################################################################################################################################## 
    def set_event_explanation(self, Action,Explanation):

        try:
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_explanation','"+ Explanation+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
########################################################################################################################################################################## 
    def set_event_feasibility_explanation(self, Action,Explanation):
        try:
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_explanation','"+ Explanation+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
########################################################################################################################################################################## 
    def remove_experience(self, action_id):
        #remove local experience related to a task execution in order to free memory
        destination_folder=self.neem_path
        basefolder=self.neem_experience_folder
        root_name=action_id.split("#").pop()+'.bag'
        if os.path.exists(destination_folder+'/'+basefolder+'/'+root_name):
           os.remove(destination_folder+'/'+basefolder+'/'+root_name)
########################################################################################################################################################################## 
    def get_event_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification explanation: %s" % str(e))
        return Explanation
########################################################################################################################################################################## 
    def get_event_feasibility_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action feasibility verification explanation: %s" % str(e))
        return Explanation
########################################################################################################################################################################## 
    def reset_event_verification_mode(self, Action,mode):
        print('Removing previous mode')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_verification_postponed', Mode)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification mode: '+str(e))
        try:
            mode=('true'==(str(mode).lower()))
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_verification_postponed',"+ str(mode)+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_feasibility_verification_mode(self, Action,mode):
        print('Removing previous feasibility mode')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_feasibility_verification_postponed', Mode)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility verification mode: '+str(e))
        try:
            mode=('true'==(str(mode).lower()))
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_feasibility_verification_postponed',"+ str(mode)+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def get_event_feasibility_verification_mode(self, Action):
        Mode=False
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_feasibility_verification_postponed', Mode)).")
            solution = next(query.solutions())
            Mode=('true'==(str(solution['Mode']).lower()))
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action feasibility verification mode: %s" % str(e))
        return Mode
########################################################################################################################################################################## 
    def get_event_verification_mode(self, Action):
        Mode=False
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_verification_postponed', Mode)).")
            solution = next(query.solutions())
            Mode=('true'==(str(solution['Mode']).lower()))
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification mode: %s" % str(e))
        return Mode
##########################################################################################################################################################################  
    def reset_event_verification_state(self, Action,state):
        print('Removing previous state')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_been_verified', State)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification state: '+str(e))
        try:
            state=('true'==(str(state).lower()))
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_been_verified',"+ (str(state).lower())+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_feasibility_verification_status(self, Action,status):
        print('Removing previous feasibility status')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_action_feasible', Status)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility verification status: '+str(e))
        try:
            status=('true'==(str(status).lower()))
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_action_feasible',"+ (str(status).lower())+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_feasibility_verification_state(self, Action,state):
        print('Removing previous state')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_been_verified', State)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility verification state: '+str(e))
        try:
            state=('true'==(str(state).lower()))
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_been_verified',"+ (str(state).lower())+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def get_event_verification_state(self, Action):
        State=False
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_been_verified', State)).")
            solution = next(query.solutions())
            State=('true'==(str(solution['State']).lower()))
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification state: %s" % str(e))
        return State
########################################################################################################################################################################## 
    def get_event_feasibility_verification_state(self, Action):
        State=False
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_been_verified', State)).")
            solution = next(query.solutions())
            State=('true'==(str(solution['State']).lower()))
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action feasibility verification state: %s" % str(e))
        return State
##########################################################################################################################################################################
    def get_event_feasibility_verification_status(self, Action):
        Status=False
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#is_action_feasible', Status)).")
            solution = next(query.solutions())
            Status=('true'==(str(solution['Status']).lower()))
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action feasibility verification status: %s" % str(e))
        return Status
##########################################################################################################################################################################  
 
    def reset_event_nonverbal_verification_explanation(self, Action,explanation):
        print('Removing previous explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_verification_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification explanation: '+str(e))
        try:
            explanation=str(explanation) 
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_verification_explanation','"+ str(explanation)+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_nonverbal_feasibility_verification_explanation(self, Action,explanation):
        print('Removing previous feasibility explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_feasibility_verification_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility verification explanation: '+str(e))
        try:
            explanation=str(explanation) 
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_feasibility_verification_explanation','"+ str(explanation)+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_recovery_verification_explanation(self, Action,explanation):
        print('Removing previous recovery explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_recovery_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action recovery verification explanation: '+str(e))
        try:
            explanation=str(explanation) 
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_recovery_explanation','"+ str(explanation)+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def reset_event_recovery_feasibility_verification_explanation(self, Action,explanation):
        print('Removing previous recovery feasibility explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_recovery_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility recovery verification explanation: '+str(e))
        try:
            explanation=str(explanation) 
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_recovery_explanation','"+ str(explanation)+"')).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################
    def get_event_nonverbal_verification_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_verification_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification nonverbal explanation: %s" % str(e))
        return Explanation
########################################################################################################################################################################## 
    def get_event_nonverbal_feasibility_verification_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_nonverbal_feasibility_verification_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification nonverbal feasibility explanation: %s" % str(e))
        return Explanation
##########################################################################################################################################################################
    def get_event_recovery_verification_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_recovery_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action verification recovery explanation: %s" % str(e))
        return Explanation
########################################################################################################################################################################## 
    def get_event_recovery_feasibility_verification_explanation(self, Action):
        Explanation=''
        try:
            query = self.prolog.query("kb_call(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_recovery_explanation', Explanation)).")
            solution = next(query.solutions())
            Explanation=solution['Explanation']
            query.finish()
        except Exception as e:
            rospy.logwarn("Error occured while retrieving action feasibility verification recovery explanation: %s" % str(e))
        return Explanation
    
##########################################################################################################################################################################
     
########################################################################################################################################################################## 
    def event_success_verification(self, action_id, runtime_verification, delete_local_experience=False):
        try:
             explanation=""
             confidence=1.0
             success=True
             nonverbal_explanation=''
             recovery_explanation=""
             is_verified=self.get_event_verification_state(action_id)
             if not runtime_verification: #action verification is being postponed
                     print(action_id, 'action verification is being postponed')       
                     success=(random.random()>=-0.01)
                     conf=random.random()
                     if conf<0.5:
                        confidence=conf/50.+0.98
                     else:
                        confidence=conf/50.+0.98
                     explanation=""
             else:   #runtime action verification
                     print(action_id, 'runtime action verification')
                     if is_verified: #action has been already verified
                        #retrieve results from NEEMs
                        print(action_id, 'action has been already verified')
                        confidence=self.getActionVerificationConfidence(action_id)
                        explanation=self.get_event_explanation(action_id)
                        success=self.get_direct_current_event_status(action_id)
                        nonverbal_explanation=self.get_event_nonverbal_verification_explanation(action_id)
                        recovery_explanation=self.get_event_recovery_verification_explanation(action_id)
                     else: #action has not been verified yet and should be verified now
                        print(action_id, 'action has not been verified yet and should be verified now')
                        print('Retrieving action tree ...')
                        RootAction=action_id
                        ListSubAction=self.get_current_event_sub_event(RootAction)
                        #Directly verify the root                       
                        RootActionDesignator, RootActionTask=self.get_current_event_designator(RootAction)
                        [f_feasibility, f_confidence, f_explanation, f_nonverbal_explanation, f_recovery_explanation]=self.event_feasibility_verification(RootAction, runtime_verification, delete_local_experience=delete_local_experience)
                        #get list of potential verifiers
                        participants={}
                        participants=self.get_participant_with_role(action_id)
                        participant_roots=self.modalityParser.get_participant_roots(participants)
                        list_verifiers=self.verifierParser.filter_verifiers(action=RootActionTask.split('#').pop().split('_')[0], mode='Success', participants=participant_roots)
                        l_status=[]
                        l_confidence=[]
                        l_explanation=[]
                        l_nonverbal_explanation=[]
                        l_recovery_explanation=[]
                        #random decision if no verifiers: failure distribution learnt from experience
                        success=(random.random()>=-0.01)
                        conf=random.random()
                        if conf<0.5:
                            confidence=conf/50.+0.98
                        else:
                            confidence=conf/50.+0.98
                        should_be_randomized=True
                        if list_verifiers==[]: #no verifier found
                               if ListSubAction==[]: #no subaction found
                                  explanation=""
                               else: #subactions found
                                  explanation=''
                        else:
                               for verifier in list_verifiers:
                                   result=self.verify_action(action_server=verifier['verifier']['name'], action_id=RootAction)
                                   
                                   if result is not None:
                                      print('\n\n\n\n $$$$$$$$$$$$$$$ NON VERBAL EXPLANATION $$$$$$$',(result.nonverbal_explanation,'$$$$$$$$$$$$$$$$$$$$$$ \n\n\n'))
                                      l_status.append(result.decision)
                                      l_confidence.append(result.confidence)
                                      l_explanation.append(result.explanation)
                                      l_nonverbal_explanation.append(result.nonverbal_explanation)
                                      l_recovery_explanation.append(result.recovery_explanation)
                               print('Consolidate the results ...')
                               if l_status!=[]: #there are some results from verifiers
                                   explanation=''
                                   confidence=0.0
                                   success=True
                                   nonverbal_explanation=''
                                   recovery_explanation=''
                                   for i in range(len(l_status)):
                                         success=success and l_status[i]
                                         confidence=confidence+l_confidence[i]
                                         if self.explanation_placeholder.lower() not in explanation and self.explanation_placeholder.lower() not in l_explanation[i].lower():
                                                 if explanation!='' and l_explanation[i]!='':
                                                       explanation=explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+l_explanation[i]
                                                 else:
                                                       if l_explanation[i]!='':
                                                            explanation=l_explanation[i]
                                         else:
                                              explanation=l_explanation[i]
                                         if self.explanation_placeholder.lower() not in recovery_explanation and self.explanation_placeholder.lower() not in l_recovery_explanation[i].lower():
                                                   if recovery_explanation!='' and l_recovery_explanation[i]!='':
                                                        recovery_explanation=recovery_explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+l_recovery_explanation[i]
                                                   else:
                                                       if l_recovery_explanation[i]!='':
                                                             recovery_explanation=l_recovery_explanation[i] 
                                         if l_nonverbal_explanation[i]!='':
                                               if nonverbal_explanation!='':
                                                     nonverbal_explanation=nonverbal_explanation+'+'+l_nonverbal_explanation[i] #concatenate only if non empty string
                                               else:
                                                     nonverbal_explanation=l_nonverbal_explanation[i]
                                   confidence=confidence/len(l_status)
                               #consider the subactions
                        conf=1.0
                        list_verification_results={}
                        
                        """
                        for action in ListSubAction
                              success=success and i_success
                              conf=conf*i_confidence
                              [i_success, i_confidence, i_explanation, i_nonverbal_explanation, i_recovery_explanation]=self.event_success_verification(action, runtime_verification,delete_local_experience=delete_local_experience)
                        """      
                              
                        for action in ListSubAction:
                              [i_success, i_confidence, i_explanation, i_nonverbal_explanation, i_recovery_explanation]=self.event_success_verification(action, runtime_verification,delete_local_experience=delete_local_experience)
                              list_verification_results[action]={}
                              list_verification_results[action]['result']=[i_success, i_confidence, i_explanation, i_nonverbal_explanation, i_recovery_explanation]
                              list_verification_results[action]['context']=[]
                              list_verification_results[action]['task']=''
                              S_RootActionDesignator, S_RootActionTask=self.get_current_event_designator(action)
                              list_verification_results[action]['task']=S_RootActionTask
                              list_verification_results[action]['context'].append(S_RootActionTask.split('_')[0])
                              participants=self.get_participant_with_role(action)
                              list_verification_results[action]['context']=list_verification_results[action]['context']+list(participants.keys())
                              for actors in list(participants.values()):
                                  list_verification_results[action]['context']=list_verification_results[action]['context']+list(actors)
                              list_verification_results[action]['context']=set(list_verification_results[action]['context'])
                         
                        for r in range(len( ListSubAction)):
                              action=ListSubAction[r]
                              if not list_verification_results[action]['result'][0] and 'Grasping'.lower() in list_verification_results[action]['task'].lower():
                                 found_recovery=False
                                 for s in range(len( ListSubAction)):
                                     action2=ListSubAction[s]
                                     if s!=r and list_verification_results[action]['context']==list_verification_results[action2]['context'] and list_verification_results[action2]['result'][0]:
                                         found_recovery=True
                                         break
                                 if not found_recovery:
                                    success=False
                              else:
                                   if not list_verification_results[action]['result'][0]:
                                      success=False 
                              conf=conf*list_verification_results[action]['result'][1]
                              
                              
                        confidence=(confidence + conf+f_confidence)/3.0 #indirect and direct verification and feasibility verification
                        success=success and f_feasibility #success verification and feasibility verification
                        if success:
                            if ListSubAction!=[]:
                                 if explanation!='' and self.explanation_placeholder.lower() not in explanation.lower():
                                      explanation='All constitutive subactions were successful'+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+explanation
                                 else:
                                      explanation='All constitutive subactions were successful'
                        else:
                            if ListSubAction!=[] and self.explanation_placeholder.lower() not in explanation.lower():
                                 if explanation!='' :
                                      explanation='At least one constitutive subaction has failed'+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+explanation
                                 else:
                                       explanation='At least one constitutive subaction has failed'
                        if self.explanation_placeholder.lower() not in f_explanation.lower():
                             if explanation!='' and f_explanation!='':
                                  explanation=explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+f_explanation
                             else:
                                  if f_explanation!='':
                                      explanation=f_explanation
                                      
                        if self.explanation_placeholder.lower() not in f_recovery_explanation.lower():
                             if recovery_explanation!='' and f_recovery_explanation!='':
                                  recovery_explanation=recovery_explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+f_recovery_explanation
                             else:
                                  if f_recovery_explanation!='':
                                      recovery_explanation=f_recovery_explanation
                        #recovery_explanation=recovery_explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+f_recovery_explanation {TODO: }
                        if f_nonverbal_explanation!='':
                           if nonverbal_explanation!='':
                                nonverbal_explanation=nonverbal_explanation+'+'+f_nonverbal_explanation #concatenate only if non empty string
                           else:
                                nonverbal_explanation=f_nonverbal_explanation 
             if runtime_verification and not is_verified: 
                   if explanation=='':
                        explanation=self.explanation_placeholder	#put default explanation message
                   if recovery_explanation=='':
                        recovery_explanation=self.explanation_placeholder	#put default explanation message
                   self.ResetActionVerificationExplanation(RootAction, explanation) #resetting the explanation
                   explanation1=self.get_event_explanation(RootAction) #to be removed or commented
                   
                   self.ResetActionVerificationStatus(RootAction, success) #resetting the decision
                   success1=self.get_direct_current_event_status(RootAction) #to be removed or commented
                   	
                   self.ResetActionVerificationConfidence(RootAction, confidence)	#resetting the confidence
                   confidence1=self.getActionVerificationConfidence(RootAction) #to be removed or commented
                   
                   ############################################ scaling down non verbal explanation ############################################
                   try:
                         n_expl=json.loads(nonverbal_explanation)
                         data_modality=n_expl['modality']#getting type of the content. It could be acoustic or odometric or purely tactile
                         data_type=n_expl['value_type'] #setting type of the content. it could be a path to the data already saved
                         data_format=n_expl['format'] #setting type of the content. it could be float for acoustic for instance
                         data_shape=n_expl['shape']#setting shape of the content for restitution
                         data_list=n_expl['data'] #setting the content of the image
                         
                         #print('\n\n\n\n\n\n\n',data_list,'\n\n\n\n\n\n\n')
                         
                         if data_modality=='Visual-Based':  #only considers visual content now
                            if data_type=='data': #only considers raw data
                               if data_shape[0]*data_shape[1]>10000: #image size exceeds max string length
                                  scale=float(10000)/float(data_shape[0]*data_shape[1])
                                  data_shape0=int(data_shape[0]*scale)
                                  data_shape1=int(data_shape[1]*scale)
                                  explanation_image=np.array(data_list, dtype=data_format) #reshape the array within appropriate format
                                  explanation_image=explanation_image.reshape(data_shape)
                                  explanation_image=cv2.resize(explanation_image.copy(), (data_shape1, data_shape0), interpolation=cv2.INTER_AREA)
                                  n_expl['shape']=explanation_image.shape #setting shape of the content for restitution
                                  explanation_image=explanation_image.flatten() #flatten the  multidimensional array
                                  explanation_image=list(explanation_image) #turn array into list
                                  dtype=int
                                  if 'float' in str(data_type):
                                      dtype=float
                                  else:
                                      if 'str' in str(data_type):
                                         dtype=str
                                  final_explanation_image=[dtype(explanation_image[i]) for i in range(len(explanation_image)) ] # turning list elements serializable
                                  n_expl['data']=final_explanation_image
                                  nonverbal_explanation=json.dumps(n_expl) #serializing the non verbal explanation 
                         print('Rescaling non verbal explanation completed successfully!!!')
                   except Exception as e:
                          print('Rescaling non verbal explanation before storage in the knowledge base did not complete properly: '+str(e)) 
                   
                   ############################################################################################################################
                   
                   self.reset_event_nonverbal_verification_explanation(RootAction, nonverbal_explanation)   #resetting the nonverbal explanation
                   
                   nonverbal_explanation1=self.get_event_nonverbal_verification_explanation(RootAction) #to be removed or commented
                   print('\n\n\n\n $$$$$$$$$$$$$$$ NON VERBAL EXPLANATION 2 $$$$$$$',len(nonverbal_explanation),'$$$$$$$$$$$$$$$$$$$$$$ \n\n\n')
                   print('\n\n\n\n $$$$$$$$$$$$$$$ NON VERBAL EXPLANATION 3 $$$$$$$',len(nonverbal_explanation1),'$$$$$$$$$$$$$$$$$$$$$$ \n\n\n')
                   
                  
                   self.reset_event_recovery_verification_explanation(RootAction, recovery_explanation)   #resetting the recovery explanation
                   recovery_explanation1=self.get_event_recovery_verification_explanation(RootAction) #to be removed or commented
                   
                   self.reset_event_verification_state(RootAction,runtime_verification)  
                   runtime_verification1=self.get_event_verification_state(RootAction) #to be removed or commented
                      
        except Exception as e:
            rospy.logwarn("Error occured while verifying an action: %s" % str(e))
        #remove the local neem experience related to this action
        try:
                 if delete_local_experience:
                      self.remove_experience(action_id,)
        except Exception as e:
                 rospy.logwarn('Error occured while deleting local experience file')
        return [success, confidence, explanation, nonverbal_explanation, recovery_explanation]      
########################################################################################################################################################################## 
    def event_feasibility_verification(self, action_id, runtime_verification, delete_local_experience=False):
        try:
             explanation=""
             confidence=1.0
             feasibility=True
             nonverbal_explanation=''
             recovery_explanation=""
             is_verified=self.get_event_feasibility_verification_state(action_id)
             if not runtime_verification: #action verification is being postponed
                     print(action_id, 'action verification is being postponed')       
                     feasibility=(random.random()>=-0.01)
                     conf=random.random()
                     if conf<0.5:
                        confidence=conf/50.+0.98
                     else:
                        confidence=conf/50.+0.98
                     explanation=""
             else:   #runtime action verification
                     print(action_id, 'runtime action verification')
                     if is_verified: #action has been already verified
                        #retrieve results from NEEMs
                        print(action_id, 'action has been already verified')
                        confidence=self.getActionFeasibilityVerificationConfidence(action_id)
                        explanation=self.get_event_feasibility_explanation(action_id)
                        feasibility=self.get_event_feasibility_verification_status(action_id)
                        nonverbal_explanation=self.get_event_nonverbal_feasibility_verification_explanation(action_id)
                        recovery_explanation=self.get_event_recovery_feasibility_verification_explanation(action_id) 
                     else: #action has not been verified yet and should be verified now
                        print(action_id, 'action has not been verified yet and should be verified now')
                        print('Retrieving action tree ...')
                        RootAction=action_id
                        ListSubAction=self.get_current_event_sub_event(RootAction)
                        #Directly verify the root                       
                        RootActionDesignator, RootActionTask=self.get_current_event_designator(RootAction)
                        #get list of potential verifiers
                        participants={}
                        participants=self.get_participant_with_role(action_id)
                        participant_roots=self.modalityParser.get_participant_roots(participants)
                        list_verifiers=self.verifierParser.filter_verifiers(action=RootActionTask.split('#').pop().split('_')[0], mode='Feasibility', participants = participant_roots)
                        l_status=[]
                        l_confidence=[]
                        l_explanation=[]
                        l_nonverbal_explanation=[]
                        l_recovery_explanation=[]
                        #random decision if no verifiers: failure distribution learnt from experience
                        feasibility=(random.random()>=-0.01)
                        conf=random.random()
                        if conf<0.5:
                            confidence=conf/50.+0.98
                        else:
                            confidence=conf/50.+0.98
                        should_be_randomized=True
                        if list_verifiers==[]: #no verifier found
                               if ListSubAction==[]: #no subaction found
                                  explanation=""
                               else: #subactions found
                                  explanation=''
                        else:
                               for verifier in list_verifiers:
                                   result=self.verify_action(action_server=verifier['verifier']['name'], action_id=RootAction)
                                   if result is not None:
                                      print('\n\n\n\n $$$$$$$$$$$$$$$ NON VERBAL EXPLANATION $$$$$$$',(result.nonverbal_explanation,'$$$$$$$$$$$$$$$$$$$$$$ \n\n\n'))
                                      l_status.append(result.decision)
                                      l_confidence.append(result.confidence)
                                      l_explanation.append(result.explanation)
                                      l_nonverbal_explanation.append(result.nonverbal_explanation)
                                      l_recovery_explanation.append(result.recovery_explanation)
                               print('Consolidate the results ...')
                               if l_status!=[]: #there are some results from verifiers
                                   explanation=''
                                   confidence=0.0
                                   feasibility=True
                                   nonverbal_explanation=''
                                   recovery_explanation=''
                                   for i in range(len(l_status)):
                                         feasibility=feasibility and l_status[i]
                                         confidence=confidence+l_confidence[i]
                                         if self.explanation_placeholder.lower() not in explanation and self.explanation_placeholder.lower() not in l_explanation[i].lower():
                                                 if explanation!='' and l_explanation[i]!='':
                                                       explanation=explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+l_explanation[i]
                                                 else:
                                                       if l_explanation[i]!='':
                                                            explanation=l_explanation[i]
                                         else:
                                              explanation=l_explanation[i]
                                         if self.explanation_placeholder.lower() not in recovery_explanation and self.explanation_placeholder.lower() not in l_recovery_explanation[i].lower():
                                                   if recovery_explanation!='' and l_recovery_explanation[i]!='':
                                                        recovery_explanation=recovery_explanation+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+l_recovery_explanation[i]
                                                   else:
                                                       if l_recovery_explanation[i]!='':
                                                             recovery_explanation=l_recovery_explanation[i]
                                         if l_nonverbal_explanation[i]!='':
                                               if nonverbal_explanation!='':
                                                     nonverbal_explanation=nonverbal_explanation+'+'+l_nonverbal_explanation[i] #concatenate only if non empty string
                                               else:
                                                     nonverbal_explanation=l_nonverbal_explanation[i]
                                   confidence=confidence/len(l_status)
                               #consider the subactions
                        conf=1.0
                        for action in ListSubAction:
                              [i_feasibility, i_confidence, i_explanation, i_nonverbal_explanation, i_recovery_explanation]=self.event_feasibility_verification(action, runtime_verification, delete_local_experience=delete_local_experience)
                              feasibility=feasibility and i_feasibility
                              conf=conf*i_confidence
                        confidence=(confidence + conf)/2.0 #indirect and direct verification
                        if feasibility:
                            if ListSubAction!=[]:
                                 if explanation!='' and  self.explanation_placeholder.lower() not in explanation.lower():
                                      explanation='All constitutive subactions were feasible'+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+explanation
                                 else:
                                      explanation='All constitutive subactions were feasible'
                        else:
                            if ListSubAction!=[]:
                                 if explanation!='' and self.explanation_placeholder.lower() not in explanation.lower():
                                      explanation='At least one constitutive subaction is not feasible (i.e., failed)'+'. '+self.explanation_connectors[int(random.random()*(len(self.explanation_connectors)-1))]+", "+explanation
                                 else:
                                       explanation='At least one constitutive subaction is not feasible (i.e., failed)'
             if runtime_verification and not is_verified: 
                   if explanation=='':
                        if feasibility:
                             explanation="This action is feasible"	#put default explanation message
                        else:
                             explanation="This action is not feasible"
                   if recovery_explanation=='':
                        recovery_explanation=self.explanation_placeholder	#put default explanation message
                   self.ResetActionFeasibilityVerificationExplanation(RootAction, explanation) #resetting the explanation
                   explanation1=self.get_event_feasibility_explanation(RootAction) #to be removed or commented
                   
                   self.reset_event_feasibility_verification_status(RootAction, feasibility) #resetting the decision
                   feasibility1=self.get_event_feasibility_verification_status(RootAction) #to be removed or commented
                   	
                   self.ResetActionFeasibilityVerificationConfidence(RootAction, confidence)	#resetting the confidence
                   confidence1=self.getActionFeasibilityVerificationConfidence(RootAction) #to be removed or commented
                   
                   self.reset_event_nonverbal_feasibility_verification_explanation(RootAction, nonverbal_explanation)   #resetting the nonverbal explanation
                   nonverbal_explanation1=self.get_event_nonverbal_feasibility_verification_explanation(RootAction) #to be removed or commented
                   
                   self.reset_event_recovery_feasibility_verification_explanation(RootAction, recovery_explanation)   #resetting the recovery explanation
                   recovery_explanation1=self.get_event_recovery_feasibility_verification_explanation(RootAction) #to be removed or commented
                   
                   self.reset_event_feasibility_verification_state(RootAction,runtime_verification)  
                   runtime_verification1=self.get_event_feasibility_verification_state(RootAction) #to be removed or commented
                      
        except Exception as e:
            rospy.logwarn("Error occured while verifying an action: %s" % str(e))
        #remove the local neem experience related to this action
        try:
                 if delete_local_experience:
                       self.remove_experience(action_id,)
        except Exception as e:
                 rospy.logwarn('Error occured while deleting local experience file')
        return [feasibility, confidence, explanation, nonverbal_explanation, recovery_explanation]      
					
########################################################################################################################################################################## 
					
    def begin_event(self, Event):

        try:
            query = self.prolog.query("mem_event_begin('"+Event+"').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 
    def end_event(self, Event):

        try:
            query = self.prolog.query("mem_event_end('" + Event + "').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 

    def set_event_failed(self, Action):

        try:
            query = self.prolog.query("mem_event_set_failed('" + Action + "').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 

    def set_event_succeeded(self, Action):

        try:
            query = self.prolog.query("mem_event_set_succeeded('" + Action + "').")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 

    def add_subaction_with_task(self, ParentAction,SubAction,TaskType):

        try:
            query = self.prolog.query("add_subaction_with_task('"+ ParentAction + "', SubAction ,'" + TaskType + "').")
            solution = next(query.solutions())
            query.finish()
            return solution['SubAction']
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))

########################################################################################################################################################################## 

    def add_diagnosis_event(self, Situation, Diagnosis):

        try:
            query = self.prolog.query("mem_event_add_diagnosis('" + Situation + "','" + Diagnosis + "').")
            solution = next(query.solutions())
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################             
    
    def get_current_episode(self):
        try:
            Episode="http://www.ease-crc.org/ont/SOMA.owl#Episode"
            query = self.prolog.query("instance_of(Episode,'"+Episode+ "').")
            solution = next(query.solutions())
            query.finish()
            return solution['Episode']
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
##########################################################################################################################################################################             
            
    def get_current_object_comment(self,Object):
        try:
            query = self.prolog.query("triple('"+Object+ "','http://www.w3.org/2000/01/rdf-schema#comment', Comment).")
            solution = next(query.solutions())
            query.finish()
            return solution['Comment']
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            return 'NOTHING TO COMMENT'
            
##########################################################################################################################################################################    
    def get_current_episode_root_action(self, Episode):
        
        try:
            query = self.prolog.query("triple('"+Episode+ "','http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#isSettingFor', RootAction).")
            solution = next(query.solutions())
            query.finish()
            return solution['RootAction']
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))  
            
 ##########################################################################################################################################################################            
    def get_current_event_duration(self,Event):
        try:
            query = self.prolog.query("kb_call([triple('"+Event+ "','http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasTimeInterval', TimeInterval), triple(TimeInterval,'http://www.ease-crc.org/ont/SOMA.owl#hasIntervalBegin', BT), triple(TimeInterval,'http://www.ease-crc.org/ont/SOMA.owl#hasIntervalEnd', ET)]).")
            solution = next(query.solutions())
            query.finish()
            dt_object_begin = datetime.fromtimestamp(float(solution['BT']))
            dt_object_end =  datetime.fromtimestamp(float(solution['ET']))
            return (dt_object_begin.isoformat(), dt_object_end.isoformat())
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            return [None, None]
##########################################################################################################################################################################             
    def get_current_event_sub_event(self, Event):
        result=[]
        try:
            query = self.prolog.query("triple('"+Event+ "','http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasConstituent', SubEvent).")
            for solution in query.solutions():
                result.append(solution['SubEvent'])
            query.finish()
            return result
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))  
            return [] 
            
    def get_current_event_super_event(self, Event):
        result=None
        try:
            query = self.prolog.query("triple(SuperEvent,'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasConstituent', '"+Event+ "').")
            for solution in query.solutions():
                result=solution['SuperEvent']
                break
            query.finish()
            return result
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))  
            return None
##########################################################################################################################################################################             
            
    def get_current_event_designator(self, Event):
        
        try:
            query = self.prolog.query("kb_call([ triple('"+Event+ "','http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#executesTask', Task),instance_of(Task, Designator)]).")
            solution = next(query.solutions())
            query.finish()
            return (solution['Designator'], solution['Task'])
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            
    def get_current_event_agent(self, Task):
        
        try:
            query = self.prolog.query("kb_call([ triple('"+Task+ "','http://www.ease-crc.org/ont/SOMA.owl#isPerformedBy', Agent)]).")
            solution = next(query.solutions())
            query.finish()
            return  solution['Agent']
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
            
    
    def get_all_instances(self, Class):
        result=[]
        try:
            query = self.prolog.query("kb_call([ instance_of(Instance, '"+Class+ "')]).")
            for solution in query.solutions():
                result.append(solution['Instance'])
            query.finish()
            return  result
        except Exception as e:
            rospy.logwarn("TraceBot-KowRob Server: %s" % str(e))

##########################################################################################################################################################################     
            
    def get_current_event_status(self, Event):
        
        if Event==[]:
            return 1
        else:
               try:
                     RootAction=Event.pop()
                     ListSubAction=self.get_current_event_sub_event(RootAction)
                     query = self.prolog.query("kb_call([ triple('"+RootAction+ "','http://www.ease-crc.org/ont/SOMA.owl#hasExecutionState', Status)]).")
                     solution = next(query.solutions())
                     query.finish()
                     if ListSubAction!=[]:
                        return (self.get_current_event_status(Event+ListSubAction))
                     else:
                        return self.status_bool[solution['Status']] and self.get_current_event_status(Event)
               except Exception as e:
                     #rospy.logwarn("NeemInterface: %s" % str(e))
                     if ListSubAction==[]:
                        return 0
                     else:
                       return self.get_current_event_status(Event+ListSubAction)   
########################################################################################################################################################################## 
            
    def get_direct_current_event_status(self, Event):
        Status=0
        try:
                     RootAction=Event
                     query = self.prolog.query("kb_call([ triple('"+RootAction+ "','http://www.ease-crc.org/ont/SOMA.owl#hasExecutionState', Status)]).")
                     solution = next(query.solutions())
                     query.finish()
                     Status= self.status_bool[solution['Status']] 
        except Exception as e:
                     rospy.logwarn("NeemInterface: %s" % str(e))
        return Status 
##########################################################################################################################################################################                         

    def get_current_event_participants(self, Event):
        
               try:
                     RootAction=Event.pop()
                     ListSubAction=self.get_current_event_sub_event(RootAction)
                     query = self.prolog.query("kb_call([ subclass_of('"+RootAction+ "','http://www.ease-crc.org/ont/SOMA.owl#hasExecutionState', Status)]).")
                     solution = next(query.solutions())
                     query.finish()
                     if ListSubAction!=[]:
                        return (self.get_current_event_status(Event+ListSubAction))
                     else:
                        return self.status_bool[solution['Status']] and self.get_current_event_status(Event)
               except Exception as e:
                     #rospy.logwarn("NeemInterface: %s" % str(e))
                     if ListSubAction==[]:
                        return 0
                     else:
                       return self.get_current_event_status(Event+ListSubAction)   
########################################################################################################################################################################## 


########################################################################################################################################################################## 
              
    def get_all_subclass(self, Event):
              i=0
              while(i<len(Event)):         
                   result=[]
                   try:
                        Task=Event[i]
                        q = self.prolog.query("kb_call(subclass_of(A, '"+Task+"')).")
                        for solution in q.solutions():
                            result.append(solution['A'])
                        q.finish()
                   except Exception as e: 
                        pass       
                   Event=Event+result
                   i+=1
              return Event                
                              

########################################################################################################################################################################## 
    def get_final_event_executives(self, Event, audit_trail):
        if audit_trail[Event]['List_SubActions']==[]:
           pass
        else:
           for SubAction in audit_trail[Event]['List_SubActions']:
               self.get_final_event_executives(SubAction, audit_trail)
               audit_trail[Event]['Participants']+=audit_trail[SubAction]['Participants']
           #remove duplicates
           audit_trail[Event]['Participants']=list(set(audit_trail[Event]['Participants']))
           
##########################################################################################################################################################################             
    def get_current_event_confidence(self, Event, audit_trail):
        
        if Event==[]:
            return 1.0
        else:
               try:
                     RootAction=Event.pop()
                     ListSubAction=self.get_current_event_sub_event(RootAction)
                     if ListSubAction!=[]:
                        return (self.get_current_event_confidence(Event+ListSubAction, audit_trail))
                     else:
                        return audit_trail[RootAction]['Confidence']*self.get_current_event_confidence(Event, audit_trail)
               except Exception as e:
                     rospy.logwarn("NeemInterface: %s" % str(e))
                     if ListSubAction==[]:
                        return 0.0
                     else:
                       return self.get_current_event_confidence(Event+ListSubAction, audit_trail)

##########################################################################################################################################################################             
    def get_direct_current_event_confidence(self, Event):
        Confidence=0.0
        try:
                     RootAction=Event
                     query = self.prolog.query("kb_call([ triple('"+RootAction+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_confidence', Confidence)]).")
                     solution = next(query.solutions())
                     query.finish()
                     Confidence= float(solution['Confidence']) 
        except Exception as e:
                     rospy.logwarn("NeemInterface: %s" % str(e))
        return Confidence 
##########################################################################################################################################################################    

    def Release(self, participants=["Canister","Robot"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#Releasing')
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#Releasing')
        return True	

##########################################################################################################################################################################    

    def Retract(self, participants=["Robot"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#Retracting')
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#Retracting')
        return True	


##########################################################################################################################################################################    

    def RotatedInsert(self, participants=["Canister","DrainTray"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#Orienting')
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#Orienting')
        return True	

##########################################################################################################################################################################    

    def TiltedInsert(self, participants=["Canister","DrainTray"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#Pushing')
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#Pushing')
        return True	

##########################################################################################################################################################################    

    def ComputeInsertPose(self, participants=["Canister","DrainTray"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#PlanningInsertion')
        insert_pose=[[0.0,0.0,1.0,0.0,0.0,1.0,0.0],[0.7,0.7,0.7],2]
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#PlanningInsertion')
        return insert_pose 	

##########################################################################################################################################################################    

    def ComputeGraspPose(self, participants=["Canister"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#PlanningGrasp')
        grasp_pose=[[0.0,0.0,1.0,0.0,0.0,1.0,0.0],[0.7,0.7,0.7],2]
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#PlanningGrasp')
        return grasp_pose 	
                
##########################################################################################################################################################################    

    def VerifyPose(self, participants=["Canister"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#VerifyingPose')
        canister_pose=[0.0,0.0,1.0,0.0,0.0,1.0,0.0]
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#VerifyingPose')
        return canister_pose 	
                
##########################################################################################################################################################################                


    def MoveArmHome(self,participants=["JointVelocity"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#ParkingArms')
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#ParkingArms')
        return True

##########################################################################################################################################################################

    def Locate(self,participants=["Canister"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableLocating')
        canister_pose, canister_id=[[0.0,0.0,1.0,0.0,0.0,0.0,0.0], 'Canister_ID568']
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#VerifyingPose"
        SubAction = self.begin_skill(ParentAction,ActionType)
        canister_pose=self.VerifyPose(participants=[canister_pose, canister_id],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableLocating')
        return canister_pose, canister_id

##########################################################################################################################################################################        

    def Grab(self, participants=["Canister","JointVelocity"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.ease-crc.org/ont/SOMA.owl#Holding')
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Holding"
        
        
        list_canister_ids=self.getClassId('Canister')
        print('Canister IDs:', list_canister_ids )
        canister_id=self.getNewInstance(list_canister_ids[0])
        print('Canister ID:', canister_id )
        list_canister_role=self.getClassId('PatientRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
      
        
        list_gripper_ids=self.getClassId('RightRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids )
        gripper_id=self.getNewInstance(list_gripper_ids[0])
        print('Gripper ID:', gripper_id )
        list_gripper_role=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role )
        gripper_role_id=self.getNewInstance(list_gripper_role[0])
        print('Gripper Role ID:', gripper_role_id )
        
         
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        #adding participant and role
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.add_participant_with_role( SubAction, gripper_id, gripper_role_id)
        
        grasp_pose=self.ComputeGraspPose(participants=["Canister"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.ease-crc.org/ont/SOMA.owl#Holding')
        return True

##########################################################################################################################################################################

    def Insert(self, participants=["DrainTray", "DrainTray"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableInserting')
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#PlanningInsertion"
        SubAction = self.begin_skill(ParentAction,ActionType)
        insert_pose=self.ComputeInsertPose(participants=["Canister","DrainTray"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        #ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Grasping"
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Pushing"
        
        
        list_canister_ids=self.getClassId('Needle')
        print('Canister IDs:', list_canister_ids )
        canister_id=self.getNewInstance(list_canister_ids[0])
        print('Canister ID:', canister_id )
        list_canister_role=self.getClassId('PatientRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
        
        list_insertee_ids=self.getClassId('RinseBottleA')
        print('Insertee IDs:', list_insertee_ids )
        insertee_id=self.getNewInstance(list_insertee_ids[0])
        print('Insertee ID:', insertee_id )
        list_insertee_role=self.getClassId('DestinationRole')
        print('Insertee role:', list_insertee_role )
        insertee_role_id=self.getNewInstance(list_insertee_role[0])
        print('Insertee Role ID:', insertee_role_id )
        
      
        
        list_gripper_ids=self.getClassId('LeftRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids )
        gripper_id=self.getNewInstance(list_gripper_ids[0])
        print('Gripper ID:', gripper_id )
        list_gripper_role=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role )
        gripper_role_id=self.getNewInstance(list_gripper_role[0])
        print('Gripper Role ID:', gripper_role_id )
        
         
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        #adding participant and role
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.add_participant_with_role( SubAction, gripper_id, gripper_role_id)
        self.add_participant_with_role( SubAction, insertee_id, insertee_role_id)

        """
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#Inserting"
        SubAction = self.begin_skill(ParentAction,ActionType)
        """
        
        self.TiltedInsert( participants=["DrainTray", "DrainTray"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Orienting"
        SubAction = self.begin_skill(ParentAction,ActionType)
        self.RotatedInsert( participants=["DrainTray", "DrainTray"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Releasing"
        SubAction = self.begin_skill(ParentAction,ActionType)
        self.Release(participants=["DrainTray"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Retracting"
        SubAction = self.begin_skill(ParentAction,ActionType)
        self.Retract(participants=["Robot"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableInserting')
        return True             
                
##########################################################################################################################################################################


    def FitInsertableIntoInsertee(self,participants=["Canister","DrainTray"],sp=2,ParentAction=None):
        print((' '*sp)+'Starting http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#FittingInsertableIntoInsertee')
        
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#ParkingArms"
        
        
        list_sensor_ids=self.getClassId('SceneRobotCamera@435D')
        print('Sensor IDs:', list_sensor_ids )
        sensor_id=self.getNewInstance(list_sensor_ids[0])
        print('Sensor ID:', sensor_id )
        list_sensor_role=self.getClassId('SensorRole')
        print('Sensor role:', list_sensor_role )
        sensor_role_id=self.getNewInstance(list_sensor_role[0])
        print('Sensor Role ID:', sensor_role_id )
      
        
        list_gripper_ids=self.getClassId('RightRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids )
        gripper_id=self.getNewInstance(list_gripper_ids[0])
        print('Gripper ID:', gripper_id )
        list_gripper_role=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role )
        gripper_role_id=self.getNewInstance(list_gripper_role[0])
        print('Gripper Role ID:', gripper_role_id )
        
        
        list_gripper_ids1=self.getClassId('LeftRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids1 )
        gripper_id1=self.getNewInstance(list_gripper_ids1[0])
        print('Gripper ID:', gripper_id1 )
        list_gripper_role1=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role1 )
        gripper_role_id1=self.getNewInstance(list_gripper_role1[0])
        print('Gripper Role ID:', gripper_role_id1 )
        
         
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        #adding participant and role
        self.add_participant_with_role( SubAction, gripper_id, gripper_role_id)
        self.add_participant_with_role( SubAction, gripper_id1, gripper_role_id1)
        self.add_participant_with_role( SubAction, sensor_id, sensor_role_id)
        
        self.MoveArmHome(participants=["JointVelocity"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableLocating"
        
        
        list_canister_ids=self.getClassId('Canister')
        print('Canister IDs:', list_canister_ids )
        canister_id=self.getNewInstance(list_canister_ids[0])
        print('Canister ID:', canister_id )
        list_canister_role=self.getClassId('StimulusRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
        
        list_sensor_ids=self.getClassId('HeadRobotCamera@435D')
        print('Sensor IDs:', list_sensor_ids )
        sensor_id=self.getNewInstance(list_sensor_ids[0])
        print('Sensor ID:', sensor_id )
        list_sensor_role=self.getClassId('SensorRole')
        print('Sensor role:', list_sensor_role )
        sensor_role_id=self.getNewInstance(list_sensor_role[0])
        print('Sensor Role ID:', sensor_role_id )
     
         
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        #adding participant and role
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.add_participant_with_role( SubAction, sensor_id, sensor_role_id) 
        canister_pose, X=self.Locate(participants=["Canister"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        ActionType = "http://www.ease-crc.org/ont/SOMA.owl#Grasping"
        #ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceablePickingUp"
        
        """
        list_canister_ids=self.getClassId('Needle')
        print('Canister IDs:', list_canister_ids )
        canister_id=self.getNewInstance(list_canister_ids[0])
        print('Canister ID:', canister_id )
        """
        
        list_canister_role=self.getClassId('PatientRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
      
        
        list_gripper_ids=self.getClassId('RightRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids )
        gripper_id=self.getNewInstance(list_gripper_ids[0])
        print('Gripper ID:', gripper_id )
        list_gripper_role=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role )
        gripper_role_id=self.getNewInstance(list_gripper_role[0])
        print('Gripper Role ID:', gripper_role_id )
        
         
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        #adding participant and role
       
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.add_participant_with_role( SubAction, gripper_id, gripper_role_id) 
        
        
        #add rotation to canister
        #self.belief_perceived_at(canister_id)
        #print('------------------ROTATION INSERTION: ', [0.,0.,0.,0.,0.,0.,1.])
        #print('------------------RETRIEVED ROTATION: ', self.get_perceived_belief(canister_id))
        
        self.Grab(participants=[canister_id,"JointVelocity"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableLocating"
        SubAction = self.begin_skill(ParentAction,ActionType)
        drain_tray_pose,drain_tray_id= self.Locate(participants=["DrainTray"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        
        ################################ FIRST TRIAL #######################################################
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableInserting"
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        
        #adding participant and role
        
        list_canister_role=self.getClassId('PatientRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.Insert(participants=["Canister", "DrainTray", "JointVelocity"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        ######################################################################################################
        
        ################################ SECOND TRIAL #######################################################
        
        ActionType = "http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#TraceableInserting"
        SubAction = self.begin_skill(ParentAction,ActionType)
        
        
        #adding participant and role
        
        list_canister_role=self.getClassId('StimulusRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
        self.add_participant_with_role( SubAction, canister_id, canister_role_id)
        self.Insert(participants=["Canister", "DrainTray", "JointVelocity"],sp=sp+5, ParentAction=SubAction)
        self.end_skill(SubAction)
        result,confidence=self.VerifyAction(SubAction, True)
        ######################################################################################################
        
        
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#FittingInsertableIntoInsertee')
        return True

                
##########################################################################################################################################################################


    def skill_process_emulator(self,title="Execute An Episode", path_name='.', sp=2):

        #start and episode
        RootActionType="http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#FittingInsertableIntoInsertee"
        Episode, RootAction=self.start_episode(RootActionType)
        Comment=title
        self.setEpisodeTitle(Episode,Comment)


        #self.belief_perceived_at("http://www.ease-crc.org/ont/SOMA.owl#Bowl","package://kitchen_object_meshes/bowl.dae","[-1.0,0.0,0.0,1.0]","http://www.ease-crc.org/ont/SOMA.owl#SM_Bowl_2")

        
        list_canister_ids=self.getClassId('Canister')
        print('Canister IDs:', list_canister_ids )
        canister_id=self.getNewInstance(list_canister_ids[0])
        print('Canister ID:', canister_id )
        list_canister_role=self.getClassId('PatientRole')
        print('Canister role:', list_canister_role )
        canister_role_id=self.getNewInstance(list_canister_role[0])
        print('Canister Role ID:', canister_role_id )
        
        list_tray_ids=self.getClassId('DrainTray')
        print('Tray IDs:', list_tray_ids )
        tray_id=self.getNewInstance(list_tray_ids[0])
        print('Tray ID:', tray_id )
        list_tray_role=self.getClassId('DestinationRole')
        print('Tray role:', list_tray_role )
        tray_role_id=self.getNewInstance(list_tray_role[0])
        print('Tray Role ID:', tray_role_id )
        
        list_gripper_ids=self.getClassId('RightRobotGripper@CEA')
        print('Gripper IDs:', list_gripper_ids )
        gripper_id=self.getNewInstance(list_gripper_ids[0])
        print('Gripper ID:', gripper_id )
        list_gripper_role=self.getClassId('ActorRole')
        print('Gripper role:', list_gripper_role )
        gripper_role_id=self.getNewInstance(list_gripper_role[0])
        print('Gripper Role ID:', gripper_role_id )
        
        #adding participant and role
        self.add_participant_with_role( RootAction, canister_id, canister_role_id)
        self.add_participant_with_role( RootAction, tray_id, tray_role_id)
        self.add_participant_with_role( RootAction, gripper_id, gripper_role_id)   

        print((' '*sp)+'Starting Episode Emulator')
        self.FitInsertableIntoInsertee(participants=["Canister","DrainTray"],sp=sp+5, ParentAction=RootAction)
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending Episode Emulator')
        #stop the episode to dump the neem from knowrob to disk
        self.stop_episode(path_name) 
        return True

##########################################################################################################################################################################

    def VerifyAction(self,Action, runtime_verification):
        return self.event_success_verification(Action , runtime_verification,delete_local_experience=True)[:2]
 
##########################################################################################################################################################################

    def getActionVerificationConfidence(self,Action):
        print('Getting Action Verification Confidence')
        return self.get_direct_current_event_confidence(Action)
         
##########################################################################################################################################################################

    def getActionFeasibilityVerificationConfidence(self,Action):
        print('Getting Action Fesibility Verification Confidence')
        Confidence=0.0
        try:
                     RootAction=Action
                     query = self.prolog.query("kb_call([ triple('"+RootAction+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_confidence', Confidence)]).")
                     solution = next(query.solutions())
                     query.finish()
                     Confidence= float(solution['Confidence']) 
        except Exception as e:
                     rospy.logwarn("NeemInterface: %s" % str(e))
        return Confidence 
         
##########################################################################################################################################################################

    def ResetActionVerificationConfidence(self,Action, Confidence):
        print('Removing previous confidence')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_confidence', Comment)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification confidence: '+str(e))
        try:
           print('Setting Action Verification Confidence')
           self.setActionVerificationConfidence(Action,Confidence)
           return True
        except Exception as e:
            print('Error while resetting action verification decision: '+str(e))
         
##########################################################################################################################################################################
    def ResetActionFeasibilityVerificationConfidence(self,Action, Confidence):
        print('Removing previous confidence')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_confidence', Comment)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibility verification confidence: '+str(e))
        try:
           print('Setting Action Feasibility Verification Confidence')
           self.setActionFeasibilityVerificationConfidence(Action,Confidence)
           return True
        except Exception as e:
            print('Error while resetting action feasibility verification decision: '+str(e))
         
##########################################################################################################################################################################

    def ResetActionVerificationExplanation(self,Action, Explanation):
        print('Removing previous explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification explanation: '+str(e))
        try:
           print('Setting Action Verification Explanation')
           self.set_event_explanation(Action,Explanation)
           return True
        except Exception as e:
            print('Error while resetting action verification explanation: '+str(e))
         
##########################################################################################################################################################################

    def ResetActionFeasibilityVerificationExplanation(self,Action, Explanation):
        print('Removing previous feasibility explanation')
        try:
            query = self.prolog.query("kb_unproject(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_explanation', Explanation)).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action feasibillity verification explanation: '+str(e))
        try:
           print('Setting Action Feasibility Verification Explanation')
           self.set_event_feasibility_explanation(Action,Explanation)
           return True
        except Exception as e:
            print('Error while resetting action feasibility verification explanation: '+str(e))
         
##########################################################################################################################################################################


    def ResetActionVerificationStatus(self,Action, Status):
        print('Removing previous status')
        try:
            query = self.prolog.query("kb_unproject([ triple('"+Action+ "','http://www.ease-crc.org/ont/SOMA.owl#hasExecutionState', Status)]).")
            query.finish()
        except Exception as e:
            print('Error while retracting pre-estimation of action verification decision: '+str(e))
        try:
            print('Setting Action Verification decision')
            if(Status):
                self.set_event_succeeded(Action)
            else:
                self.set_event_failed(Action)
            return True
        except Exception as e:
            print('Error while resetting an action verification decision: '+str(e))
            return False
         
##########################################################################################################################################################################
    def getEpisodeTitle(self,Episode):
        print('Getting Episode Title')
        return self.get_current_object_comment(Episode)
        

##########################################################################################################################################################################

    def setActionVerificationConfidence(self,Action, Confidence):
        try:
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_verification_confidence',"+ str(Confidence)+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return True

         
##########################################################################################################################################################################

    def setActionFeasibilityVerificationConfidence(self,Action, Confidence):
        try:
            query = self.prolog.query("kb_project(triple('"+Action+ "','http://www.semanticweb.org/smile/ontologies/2022/3/TraceBot#has_feasibility_verification_confidence',"+ str(Confidence)+")).")
            query.finish()
        except Exception as e:
            rospy.logwarn("NeemInterface: %s" % str(e))
        return True

         
##########################################################################################################################################################################
    def setEpisodeTitle(self,Episode, Title):
        print('Setting Episode Title')
        self.add_comment(Episode,Title)
        return True

         
##########################################################################################################################################################################

    def executeNeemRecording(self,title="Execute An Episode", path_name='.', sp=0):
        print((' '*sp)+'Starting recording NEEMs')
        self.skill_process_emulator(title=title, path_name=path_name, sp=sp+5)
        time.sleep(random.random()*3)
        print((' '*sp)+'Ending recording NEEMs')
        return True
##########################################################################################################################################################################
    def GetDataSource(self, action_id, modality='', topic='', source='', value=''):
        data_source=self.modalityParser.filter_topic(modality_key=modality, topic_key=topic, source_key=source, value_key=value)
        if data_source==[]:
            return {'type':'topic', 'value':''}
        else:
           if data_source[0]['name'].__class__==dict:
              return {'type':'path', 'value':'package://'+str(data_source[0]['name']['package'])+'/'+str(data_source[0]['name']['pathname'])}
           else:
              return {'type':'topic', 'value':str(data_source[0]['name'])} #we assume that the value is a topic 
               
##########################################################################################################################################################################
    def GetSensor(self, action_id, msg_type, nb_msgs):
        """
        input: (action_id, msg_type, nb_msgs)
        output: [{modality, value, source, data{timestamp, msg}}]
        description: takes an action of id action_id and returns nb_msgs of type msg_type that constitute the robot experience during the given action. Furthermore
        add semantic information about the given experience such as source (gripper), the type (visual), the value (color image), and the timestamp for each data sample.
         
        """ 
        output=[]
        #get the action execution time
        BT,ET=self.get_current_event_duration(action_id)
        if BT is None or ET is None:
              print('Given action could not be found!!!')
              return output
        else:
             BT=datetime.fromisoformat(BT)
             ET=datetime.fromisoformat(ET) 
             print('Searching the target bag file ...')
             target_experience_file=self.modalityParser.get_current_neem_experience(destination_folder=self.neem_path+'/'+self.neem_experience_folder, root_name=action_id.split("#").pop()+'.bag')
             print('ACTION NEEM EXPERIENCE: ', target_experience_file)
             folder_base=os.path.dirname(target_experience_file)
             base_name=os.path.basename(target_experience_file)      
             print('Searching for corresponding topics ...')
             typed_topics=self.modalityParser.neem_experience_get_typed_topics(source_folder=folder_base, input_bag_name=base_name)
             target_topic=None
             for topic_dict in typed_topics:
                 if topic_dict['type']==msg_type:
                     target_topic=topic_dict['topic']
                     output_sample={'modality':'', 'value':'', 'source':'', 'data':[]}
                     msgs=self.modalityParser.neem_experience_get_msgs(source_folder=folder_base, input_bag_name=base_name, topic=target_topic, nbs=nb_msgs, begin_time=ET)
                     output_sample['data']=msgs.copy()
                     print('searching for semantics ....')
                     for topic_desc in self.modalityParser.actual_topic:
                         if topic_desc['name']==target_topic:
                              output_sample['modality']=topic_desc['modality']
                              output_sample['source']=topic_desc['source']
                              output_sample['value']=topic_desc['value']
                              break
                     output.append(output_sample.copy())
             return output

########################################################################################################################################################################## 

    def stop_episode(self, NeemPath):
        """
        Called at the end of a neem recording, NeemPath points to the place to store the neem
        """
        NeemPath=self.neem_path
        try:
            
            #stop neem narrative    
            query = self.prolog.query("mem_episode_stop('" + NeemPath + "').")
            query.finish()
            
            #get root action of the episode
            Episode=self.get_current_episode()
            RootAction=self.get_current_episode_root_action(Episode)
            #stop neem experience
            time.sleep(2.0) # this sleep is necessary for the neem experience recorder to collect evidences from low-frequency data sources (e.g., sensor)
            if True:
               self.modalityParser.neem_experience_stop(destination_folder=self.neem_path, basefolder=self.neem_experience_folder,root_name=RootAction.split("#").pop()+'.bag')
            
            print('Starting offline automated planning and execution of action verification tasks ...')
            self.event_success_verification(RootAction, True) #forcing offline verification when the robot finishes
        except Exception as e:
            rospy.logwarn("Error while stopping episode recording: %s" % str(e))
            
#############################################################################################################################################################
    def compare_action_timeslot(self, action1, action2):
        if self.NONVERBAL_EXPLANATIONS[action1]['ET']<self.NONVERBAL_EXPLANATIONS[action2]['ET']:
           return 1
        else:
            if self.NONVERBAL_EXPLANATIONS[action1]['ET']>self.NONVERBAL_EXPLANATIONS[action2]['ET']:
               return -1
            else:
               return 0 

############################################################################################################################################################################


    def generateAuditTrail(self,sp=0, path_name="audit_trail.pdf"):
       
        # prepare directory of evidence
        print('Preparing directory of evidence storage ...')
        if not os.path.exists(self.neem_path+'/'+self.nonverbal_explanation_folder):
               try:
                    os.makedirs(self.neem_path+'/'+self.nonverbal_explanation_folder)
               except Exception as e:
                    print('Failure when creating path for Neem Experiences: '+str(e))
                    a=1/0
        else:
             # remove all existing file
             existing_files=glob.glob(self.neem_path+'/'+self.nonverbal_explanation_folder+'/*.*')
             for img_file in existing_files:
                 try:
                     os.remove(img_file)
                 except Exception as e:
                     print('Failure to remove a daemon image: '+str(e))
        print('Evidence storage prepared successfully ...')
       
        print('Searching the target info source topic ...')
        target_topic=None #third person camera
        for topic in self.modalityParser.actual_topic:
              if topic['source']==self.nonverbal_explanation_source and self.nonverbal_explanation_topic in topic['value'].lower() and self.nonverbal_explanation_modality.lower() in topic['modality'].lower():
                  target_topic=topic.copy()
                  break
        print('$$$$$$$$$$$$$$$$$$$$$ TARGET TOPIC - THIRD VIEW $$$$$$$$$$$$$$$$$$$$$$$$$', target_topic )
        
        
        target_topic1=None #first person camera
        for topic in self.modalityParser.actual_topic:
              if topic['source']==self.nonverbal_explanation_source1 and self.nonverbal_explanation_topic in topic['value'].lower() and self.nonverbal_explanation_modality.lower() in topic['modality'].lower():
                  target_topic1=topic.copy()
                  break
        print('$$$$$$$$$$$$$$$$$$$$$ TARGET TOPIC - FIRST VIEW $$$$$$$$$$$$$$$$$$$$$$$$$', target_topic1 )
        
        
                  
        target_perception_topic=None
        for topic in self.modalityParser.actual_topic:
              if topic['source']==self.nonverbal_perception_explanation_source and self.nonverbal_perception_explanation_topic in topic['value'].lower() and self.nonverbal_explanation_modality.lower() in topic['modality'].lower():
                  target_perception_topic=topic.copy()
                  break
        print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& TARGET PERCEPTION TOPIC &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', target_perception_topic )
        
       
        audit_trail={}
        audit_trail['Header_Length']=8
        print('\n\n-----------------------------------------------------------------')
        Episode=self.get_current_episode()
        audit_trail['Episode']=str(Episode)
        print('Episode: ',Episode)
        
        Comment=self.getEpisodeTitle(Episode)
        audit_trail['Episode_Title']=str(Comment)
        print('Episode Title: ', Comment)
        
        RootAction=self.get_current_episode_root_action(Episode)
        audit_trail['Root_Action_ID']=str(RootAction)
        print('Episode Root Action ID: ', RootAction)
        
        print('Searching the target bag file ...')
        target_experience_file=self.modalityParser.get_current_neem_experience(destination_folder=self.neem_path+'/'+self.neem_experience_folder, root_name=RootAction.split("#").pop()+'.bag')
        
        
        print('AUDIT NEEM EXPERIENCE: ', target_experience_file)
        
        RootActionDesignator, RootActionTask=self.get_current_event_designator(RootAction)
        audit_trail['Root_Task_Id']= str(RootActionTask)
        print('Episode Task Id: ', RootActionTask)
        
        audit_trail['Root_Task_Designator']=str(RootActionDesignator)
        print('Episode Task Designator: ', RootActionDesignator)
        
        BT, ET=self.get_current_event_duration(RootAction)
        audit_trail['Episode_Duration']=[BT, ET]
        print('Episode Duration: ', BT, ' - ', ET)
        
        Status=self.get_current_event_status([RootAction])
        audit_trail['Episode_Status']=self.bool_status[Status]
        
        print('-----------------------------------------------------------------\n\n')
        ListAction=[RootAction]
        ListAllAction=[]
    
        while ListAction!=[]:
            RootAction=ListAction.pop()
            
            ListAllAction.append(RootAction)
            audit_trail[str(RootAction)]={}
            
            ListSubAction=self.get_current_event_sub_event(RootAction)
            audit_trail[str(RootAction)]['List_SubActions']=ListSubAction
            
            ListAction=ListSubAction+ListAction
            print('Action ID: ', RootAction)
            SuperAction=self.get_current_event_super_event(RootAction)
            if SuperAction is None:
                  SuperAction=RootAction
            audit_trail[str(RootAction)]['SuperAction']=SuperAction
            print('Parent Action ID: ', SuperAction)
            
            RootActionDesignator, RootActionTask=self.get_current_event_designator(RootAction)
            audit_trail[str(RootAction)]['Task_ID']=RootActionTask
            audit_trail[str(RootAction)]['Task_Designator']=RootActionDesignator
            print('Task Id: ', RootActionTask)
            print('Task Designator: ', RootActionDesignator)
            
            Agent=self.get_current_event_agent(RootAction)
            audit_trail[str(RootAction)]['Agent_ID']=Agent
            print('Agent ID: ', Agent)
            
            BT, ET=self.get_current_event_duration(RootAction)
            audit_trail[str(RootAction)]['Action_Duration']=[BT,ET]
            print('Action Duration: ', BT, ' - ', ET)
            
            Status=self.get_direct_current_event_status(RootAction)
            audit_trail[str(RootAction)]['Status']=self.bool_status[Status]
            audit_trail[str(RootAction)]['Verbal_Explanation']=self.get_event_explanation(RootAction)
            audit_trail[str(RootAction)]['Recovery_Explanation']=self.get_event_recovery_verification_explanation(RootAction)
            audit_trail[str(RootAction)]['Confidence']=self.getActionVerificationConfidence(RootAction)
        
        #compute confidence levels
        for RootAction in ListAllAction:
            audit_trail[RootAction]['Confidence']=float("{:.2f}".format(self.getActionVerificationConfidence(RootAction)*100))
        
        #infer executive modules
        for module in self.executive_modules.keys():
            self.executive_modules[module]['SubClass']=self.get_all_subclass([module])
        for RootAction in ListAllAction:
            audit_trail[RootAction]['Participants']=[]
            audit_trail[RootAction]['Participant']=self.serialize_participant_with_role(self.get_participant_with_role(RootAction))
            for module in self.executive_modules.keys():
                if audit_trail[RootAction]['Task_Designator'] in self.executive_modules[module]['SubClass']:    
                       audit_trail[RootAction]['Participants'].append(self.executive_modules[module]['Designator'])
        
        self.get_final_event_executives( audit_trail['Root_Action_ID'], audit_trail)  
        audit_trail['Episode_Confidence']=audit_trail[audit_trail["Root_Action_ID"]]['Confidence']  
        audit_trail['Episode_Status']=audit_trail[audit_trail["Root_Action_ID"]]['Status'] 
        print('Episode Status: ', audit_trail['Episode_Status']) 
        print('Episode Confidence: ', audit_trail['Episode_Confidence']) 
        
        
        
        #get a dictionary for both 
        self.NONVERBAL_EXPLANATIONS={}
        for SubAction in ListAllAction:
            self.NONVERBAL_EXPLANATIONS[SubAction]={}
            self.NONVERBAL_EXPLANATIONS[SubAction]['ET']=datetime.fromisoformat(audit_trail[SubAction]['Action_Duration'][1]) # get the end time
            self.NONVERBAL_EXPLANATIONS[SubAction]['message']={}
            self.NONVERBAL_EXPLANATIONS[SubAction]['message'][0]=[]
            self.NONVERBAL_EXPLANATIONS[SubAction]['message'][1]=[]
            self.NONVERBAL_EXPLANATIONS[SubAction]['message'][2]=[]
        SortedListAllAction=ListAllAction.copy()
        SortedListAllAction.sort(key=functools.cmp_to_key(self.compare_action_timeslot)) # sorting list of action 
        SortedListAllAction.reverse()
        
        ########## Compute non-verbal explanations #############################################
        if True:
            if (target_topic is None and target_topic1 is None) or target_experience_file is None or target_perception_topic is None:
                 image_data=np.zeros([self.modalityParser.height,self.modalityParser.width,3], dtype='uint8')
            else:
                 folder_base=os.path.dirname(target_experience_file)
                 base_name=os.path.basename(target_experience_file)
                 print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%',folder_base, base_name, target_experience_file, target_topic['name'], target_perception_topic['name'])
                 try:
                 
                        # perceptionless nonverbal explanation. Results stored in self.NONVERBAL_EXPLANATIONS
                        self.modalityParser.neem_experience_get_msgs_sv(source_folder=folder_base, input_bag_name=base_name, topic=target_topic['name'],
                                                                        nonverbal_explanation_dict=self.NONVERBAL_EXPLANATIONS, list_keys=SortedListAllAction, flags=0)
                        
                        # perception-based nonverbal explanation. Results stored in self.NONVERBAL_EXPLANATIONS
                        self.modalityParser.neem_experience_get_msgs_sv(source_folder=folder_base, input_bag_name=base_name,
                         topic=target_perception_topic['name'], nonverbal_explanation_dict=self.NONVERBAL_EXPLANATIONS, list_keys=SortedListAllAction, flags=1) 
                        
                        # perceptionless nonverbal explanation (Third-person). Results stored in self.NONVERBAL_EXPLANATIONS
                        self.modalityParser.neem_experience_get_msgs_sv(source_folder=folder_base, input_bag_name=base_name, topic=target_topic1['name'],
                         nonverbal_explanation_dict=self.NONVERBAL_EXPLANATIONS, list_keys=SortedListAllAction, flags=2) 
                       
                        for SubAction in ListAllAction:
                             RootActionTask=audit_trail[SubAction]['Task_ID']
                             is_perception=False
                             for action_key in self.perception_action_prefix:
                                  if action_key.lower() in RootActionTask.split('#').pop().lower():
                                         is_perception=True
                                         break
                             try:
                                  if not is_perception:
                                       print("################################ ", "THIS ACTION IS NOT A PERCEPTION ##########################")	
                                  
                                       image_data=self.modalityParser.read_raw_color_image( self.NONVERBAL_EXPLANATIONS[SubAction]['message'][0][0],
                                             iwidth=self.modalityParser.width, iheight=self.modalityParser.height, cvMode='bgr8') 
                                  else:
                                       print("################################ ", "THIS ACTION IS A PERCEPTION ##########################")
                                       image_data=self.modalityParser.read_perception_result(self.NONVERBAL_EXPLANATIONS[SubAction]['message'][1][0],
                                                                  iwidth=self.modalityParser.width,iheight=self.modalityParser.height, cvMode='bgr8')
                             except Exception as e:
                                       print('Failed to read sensor data from neem experience: '+str(e))                 
                                       image_data=np.zeros([self.modalityParser.height,self.modalityParser.width,3], dtype='uint8')
                             try:
                        
                                       print("################################ ", "THIS ACTION FROM FIRST PERSON ##########################")
                                       image_data1=self.modalityParser.read_raw_color_image( self.NONVERBAL_EXPLANATIONS[SubAction]['message'][2][0], 
                                                                     iwidth=self.modalityParser.width,iheight=self.modalityParser.height, cvMode='bgr8')
                             except Exception as e:
                                       print('Failed to read sensor data from neem experience: '+str(e))                 
                                       image_data1=np.zeros([self.modalityParser.height,self.modalityParser.width,3], dtype='uint8') 
                             image_data=np.concatenate([image_data,image_data1], axis=0)    
            
                             #reading other non verbal explanation
                             l_non_verbal_explanation=self.get_event_nonverbal_verification_explanation(SubAction).split('+')
                             l_non_verbal_image=[]
                             for n_expl in l_non_verbal_explanation:
                                 if n_expl!='':
                                       try:
                                            n_expl=json.loads(n_expl)
                                            data_modality=n_expl['modality']#getting type of the content. It could be acoustic or odometric or purely tactile
                                            data_type=n_expl['value_type'] #setting type of the content. it could be a path to the data already saved
                                            data_format=n_expl['format'] #setting type of the content. it could be float for acoustic for instance
                                            data_shape=n_expl['shape']#setting shape of the content for restitution
                                            data_list=n_expl['data'] #setting the content of the image
                                            if data_modality!='Visual-Based':
                                               continue  #only considers visual content now
                                            if data_type=='path':
                                               explanation_image=cv2.imread(data_list)
                                               l_non_verbal_image.append(explanation_image.copy())
                                            else:
                                               if data_type!='data':
                                                  continue #unknown data type
                                               explanation_image=np.array(data_list, dtype=data_format) #reshape the array within appropriate format
                                               explanation_image=explanation_image.reshape(data_shape)
                                               l_non_verbal_image.append(explanation_image.copy())
                                       except Exception as e:
                                            print('Error accessing the non verbal explanation data: '+str(e))
                             try:  
                                 nonverbal_explanation=self.neem_path+'/'+self.nonverbal_explanation_folder+'/'+SubAction.split('#').pop()+'.png'
                                 data_shape=image_data.shape
                                 data_format=image_data.dtype
                                 l_non_verbal_image=[image_data]+l_non_verbal_image
                                 fl_non_verbal_image=[]
                                 ind=-1
                                 for img in l_non_verbal_image:
                                     ind=ind+1            
                                     if img.sum()>0.0:
                                        if ind>0:
                                           img=cv2.resize(img.copy(), (data_shape[1], int(data_shape[0]/2)), interpolation=cv2.INTER_AREA)
                                        else:
                                           img=cv2.resize(img.copy(), (data_shape[1], data_shape[0]), interpolation=cv2.INTER_AREA)
                                        if len(img.shape)==2:
                                           img=np.stack([img.copy(), img.copy(), img.copy()], axis=2)
                                        else:
                                           if len(img.shape)==3 and img.shape[2]==1:
                                              img=np.concatenate([img.copy(), img.copy(), img.copy()], axis=2)
                                           else:
                                              if len(img.shape)!=3 or img.shape[2]!=3:
                                                 continue #illegally formatted image is ignored
                                        fl_non_verbal_image.append(img.copy()) # adding image in the list
                                        fl_non_verbal_image.append(np.ones([10, data_shape[1], 3], dtype=data_format)*255) # adding white separator
                                 if fl_non_verbal_image!=[]:
                                    image_data=np.concatenate(fl_non_verbal_image, axis=0) #concatenate all the explanation
                             except Exception as e:
                                 print('Error accessing the non verbal explanation data: '+str(e))
                             cv2.imwrite(nonverbal_explanation, image_data) #save the explanation
                             self.reset_event_nonverbal_verification_explanation(SubAction, nonverbal_explanation) #setting proper nonverbal explanation
                             audit_trail[str(SubAction)]['Non_Verbal_Explanation']=self.get_event_nonverbal_verification_explanation(SubAction)
                 except Exception as e:
                        print('Error encountered when preparing nonverbal explanation: '+str(e))
        #########################################################################################
        
        
        
        return audit_trail



############################################################################################################################################################################


#if __name__ == '__main__':
#    rospy.init_node('NeemInterface')
    ##################### Audit Trail Emulator ##########################
    #ni = NeemInterface()
    #path_name='/home/franklin/Desktop/Audit_Trail.pdf'
    #scenario_name='inserting canister into drain tray'
    #ni.excuteNeemRecording(title=scenario_name)
    #audit_trail=ni.generateAuditTrail(path_name=path_name) 
    #print(audit_trail)
    
