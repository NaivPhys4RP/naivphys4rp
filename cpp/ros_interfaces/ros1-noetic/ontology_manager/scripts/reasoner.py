#!/usr/bin/env python3

import actionlib
import roslib
roslib.load_manifest('rosprolog')
roslib.load_manifest('naivphys4rp_msgs')
import rospy
from rosprolog_client import PrologException, Prolog
from naivphys4rp_msgs.msg import *

class NaivPhys4RPKnowrobServer:
	def __init__(self):
	 #starting prolog and action server
         self.prolog = Prolog()
         
         self.namespace="http://www.semanticweb.org/franklin/ontologies/2022/7/naivphys4rp.owl#" #default ontology's namespace
         
         self.onto_load_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_load', LoadOntologyAction, self.executeLoadOntology, False)
         self.onto_load_server.start()
         print("Server ontology loader is started !")
         
         self.subclass_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_subclass', SubClassAction, self.executeSubClass, False)
         self.subclass_server.start()
         print("Server subclass is started !")
         
         self.new_individual_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_individual', NewIndividualAction, self.executeNewIndividual, False)
         self.new_individual_server.start()
         print("Server for creating instances is started !")
         
         self.object_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_object_property', ObjectPropertyAction, self.executeObjectProperty, False)
         self.object_property_server.start()
         print("Server for extracting object image is started !")
         
         self.data_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_data_property', DataPropertyAction, self.executeDataProperty, False)
         self.data_property_server.start()
         print("Server for extracting data image is started !")
         
         self.list_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_list_property', ListPropertyAction, self.executeListProperty, False)
         self.list_property_server.start()
         print("Server for extracting the property list is started !")
         
         self.list_class_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_list_class', ListClassAction, self.executeListClass, False)
         self.list_class_server.start()
         print("Server for extracting the class list is started !")
         
         self.query_knowledge_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_query_knowledge', QueryKnowledgeAction, self.executeQueryKnowledge, False)
         self.query_knowledge_server.start()
         print("Server for extracting the class list is started !")
         
         self.common_pose_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_common_pose', CommonPoseAction, self.executeCommonPose, False)
         self.common_pose_server.start()
         print("Server for extracting common object poses is started !")
##########################################################################################################################################################################
         
	def executeLoadOntology(self, goal):
      
         print("Processing goal ...")
         packageName = goal.package
         relativePath= goal.relative_path
         self.namespace=goal.namespace
         result=LoadOntologyResult()
         feedback=LoadOntologyFeedback()
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
         
	def executeQueryKnowledge(self, goal):
      
		print("Processing goal ...")

		result=QueryKnowledgeResult()
		feedback=QueryKnowledgeFeedback()
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

		result=SubClassResult()
		feedback=SubClassFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
			if goal.is_sub:
				q = self.prolog.query("kb_call(subclass_of(A, '"+self.namespace+goal.class_name+"')).")
			else:
				q = self.prolog.query("kb_call(subclass_of('"+self.namespace+goal.class_name+"', A)).")
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
	
	         
	def executeListClass(self, goal):
		
		print("Processing goal ...")

		result=ListClassResult()
		feedback=ListClassFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
			q = self.prolog.query("kb_call(is_class(A)).")
			for solution in q.solutions():
				if solution['A'].split("#")[0]+"#"==self.namespace:
					result.classes.append(solution['A'])
					print(solution['A'])
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.list_class_server.publish_feedback(feedback)
		self.list_class_server.set_succeeded(result)
##########################################################################################################################################################################

 
	def executeListProperty(self, goal):
		
		print("Processing goal ...")

		result=ListPropertyResult()
		feedback=ListPropertyFeedback()
		result.properties=[]
		feedback.feedback=True
		try:
			q = self.prolog.query("kb_call(is_property(A)).")
			for solution in q.solutions():
				if solution['A'].split("#")[0]+"#"==self.namespace:
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

		result=ObjectPropertyResult()
		feedback=ObjectPropertyFeedback()
		result.classes=[]
		feedback.feedback=True
		try:
		
			if goal.quantifier == "only" or goal.quantifier == "some":
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+goal.class_name+"', C), has_description(C,"+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+goal.class_name+"', "+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
			else:
				(nature, delimiter)=self.parseAttribute(goal.quantifier)
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+goal.class_name+"', C), has_description(C,"+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+goal.class_name+"', "+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
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

		result=DataPropertyResult()
		feedback=DataPropertyFeedback()
		result.values=[]
		feedback.feedback=True
		try:
		
			if goal.quantifier == "only" or goal.quantifier == "some" or goal.quantifier == "value":
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+goal.class_name+"', C), has_description(C,"+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+goal.class_name+"', "+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
			else:
				(nature, delimiter)=self.parseAttribute(goal.quantifier)
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+goal.class_name+"', C), has_description(C,"+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+goal.class_name+"', "+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
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

		result=NewIndividualResult()
		feedback=NewIndividualFeedback()
		result.object_id=""
		feedback.feedback=True
		try:
			
			q = self.prolog.query("kb_project([new_iri(A,'"+self.namespace+goal.class_name+"'), has_type(A,'"+self.namespace+goal.class_name+"')]).")
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
		
	def executeCommonPose(self, goal):
		
		print("Processing goal ...")

		result=CommonPoseResult()
		feedback=CommonPoseFeedback()
		feedback.feedback=True
		try:
			targetPoseClass=goal.class_name+goal.pose_type.capitalize()+"Pose"
			q = self.prolog.query("kb_call((has_equivalent_class('"+self.namespace+targetPoseClass+"' , A),has_description(A,intersection_of(B)), nth0(0,B,C),  nth0(1,B,D), has_description(C, exactly(O,1,ROT)), has_description(D, exactly(P,1,TRANS)), has_description(ROT, intersection_of(ROTS)), nth0(1,ROTS,ROTX), nth0(2,ROTS, ROTY), nth0(3,ROTS, ROTZ),nth0(0,ROTS, ROTW), has_description(TRANS, intersection_of(TRANSS)), nth0(0,TRANSS,TRANSX), nth0(1,TRANSS, TRANSY), nth0(2,TRANSS, TRANSZ), has_description(ROTX, value(Rx, RX)), has_description(ROTY, value(Ry, RY)), has_description(ROTZ, value(Rz, RZ)), has_description(ROTW, value(Rw, RW)), has_description(TRANSX, value(Tx, TX)), has_description(TRANSY, value(Ty, TY)), has_description(TRANSZ, value(Tz, TZ)))).")
			for solution in q.solutions():
				result.pose.position.x=solution['TX']
				result.pose.position.y=solution['TY']
				result.pose.position.z=solution['TZ']
				result.pose.orientation.x=solution['RX']
				result.pose.orientation.y=solution['RY']
				result.pose.orientation.z=solution['RZ']
				result.pose.orientation.w=solution['RW']
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
 
    rospy.init_node('naivphys4rp_knowrob_node')
    server = NaivPhys4RPKnowrobServer()
    rospy.spin()
  
  
    
    
 
    
  
