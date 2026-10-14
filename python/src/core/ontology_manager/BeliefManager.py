#!/usr/bin/python3

#setting python paths
import sys
import os
import shlex, subprocess
import socketserver
import signal

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
         s=self.prolog.query
         self.currentBeliefState=None
         self.namespace="http://www.semanticweb.org/franklin/ontologies/2022/7/naivphys4rp.owl#" #default ontology's namespace
         
         #KBListParticipant.action KBFromRoleToObject.action KBDomainRelation.action KBPotentialActionObject.action
         
         self.list_participant_server = actionlib.SimpleActionServer('naivphys4rp_list_participant', KBListParticipantAction, self.executeListParticipant, False)
         self.list_participant_server.start()
         print("Server list participant is started !")
         
         
         
         self.list_synonym_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_synonym', KBClassSynonymAction, self.executeClassSynonym, False)
         self.list_synonym_server.start()
         print("Server list synonyms is started !")
         
         
         self.list_part_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_part', KBClassConstituentAction, self.executeClassPart, False)
         self.list_part_server.start()
         print("Server list parts is started !")
         
         
         """
         self.object_relation_server = actionlib.SimpleActionServer('naivphys4rp_object_relation', KBObjectRelationAction, self.executeObjectRelation, False)
         self.object_relation_server.start()
         print("Server object relation is started !")
         """
         
         self.role_to_object_server = actionlib.SimpleActionServer('naivphys4rp_role_to_object', KBFromRoleToObjectAction, self.executeFromRoleToObject, False)
         self.role_to_object_server.start()
         print("Server role to object is started !")
         
         self.domain_relation_server = actionlib.SimpleActionServer('naivphys4rp_domain_relation', KBDomainRelationAction, self.executeDomainRelation, False)
         self.domain_relation_server.start()
         print("Server domain relation is started !")
         
         self.potential_action_object_server = actionlib.SimpleActionServer('naivphys4rp_potential_action_object', KBPotentialActionObjectAction, self.executePotentialActionObject, False)
         self.potential_action_object_server.start()
         print("Server potential action object is started !")
         
         self.onto_load_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_load', KBLoadOntologyAction, self.executeLoadOntology, False)
         self.onto_load_server.start()
         print("Server ontology loader is started !")
         
         
         
         self.subclass_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_subclass', KBSubClassAction, self.executeSubClass, False)
         self.subclass_server.start()
         print("Server subclass is started !")
         
         self.subproperty_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_subproperty', KBSubPropertyAction, self.executeSubProperty, False)
         self.subproperty_server.start()
         print("Server subproperty is started !")
         
         self.property_io_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_property_io', KBPropertyIOAction, self.executePropertyIO, False)
         self.property_io_server.start()
         print("Server property io is started !")
         
         self.new_individual_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_individual', KBNewIndividualAction, self.executeNewIndividual, False)
         self.new_individual_server.start()
         print("Server for creating instances is started !")
         
         self.object_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_object_property', KBObjectPropertyAction, self.executeObjectProperty, False)
         self.object_property_server.start()
         print("Server for extracting object image is started !")
         
         self.data_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_data_property', KBDataPropertyAction, self.executeDataProperty, False)
         self.data_property_server.start()
         print("Server for extracting data image is started !")
         
         self.list_property_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_list_property', KBListPropertyAction, self.executeListProperty, False)
         self.list_property_server.start()
         print("Server for extracting the property list is started !")
         
         
         
         self.list_class_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_list_class', KBListClassAction, self.executeListClass, False)
         self.list_class_server.start()
         print("Server for extracting the class list is started !")
         
         self.query_knowledge_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_query_knowledge', KBQueryKnowledgeAction, self.executeQueryKnowledge, False)
         self.query_knowledge_server.start()
         print("Server for generic knowrob query is started !")
         
         self.common_pose_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_common_pose', KBCommonPoseAction, self.executeCommonPose, False)
         self.common_pose_server.start()
         print("Server for extracting common object poses is started !")

         self.belief_manager_server = actionlib.SimpleActionServer('naivphys4rp_knowrob_belief_manager', KBLoadBeliefStateAction, self.executeLoadBeliefState, False)
         self.belief_manager_server.start()
         print("Server for launching belief state is started !")
##########################################################################################################################################################################
         
	def executeLoadOntology(self, goal):
      
	 print("Processing goal ...")
	 packageName = goal.package
	 relativePath= goal.relative_path
	 if len(goal.namespace)<1:
	      goal.namespace=self.namespace
	 else:	
	      self.namespace=goal.namespace
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
         
	def executeClassSynonym(self, goal):
      
		print("Processing goal ...")
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		else:	
			self.namespace=goal.namespace
		result=KBClassSynonymResult()
		feedback=KBClassSynonymFeedback()
		feedback.feedback=True
		listclasses=[goal.class_name]
		result.classes=[]
		i=0
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#subclasses
			try:
				q = self.prolog.query("kb_call([subclass_of(A,'"+goal.namespace+class_name+"')]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#union of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',union_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			i=i+1
		self.list_synonym_server.publish_feedback(feedback)
		self.list_synonym_server.set_succeeded(result)


##########################################################################################################################################################################
         
	def executeClassPart(self, goal):
      
		print("Processing goal ...")
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		else:	
			self.namespace=goal.namespace
		result=KBClassConstituentResult()
		feedback=KBClassConstituentFeedback()
		feedback.feedback=True
		listclasses=[goal.class_name]
		result.classes=[]
		i=0
		part_relation=goal.namespace+"has_part"
		include_relation=goal.namespace+"includes"
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#has_part relation
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"', B), has_description(B, exactly('"+part_relation+"',1,A))]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
				
			
			#include relation
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"', B), has_description(B, exactly('"+include_relation+"',1,A))]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							result.classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#union of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',union_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			i=i+1
		self.list_part_server.publish_feedback(feedback)
		self.list_part_server.set_succeeded(result)


##########################################################################################################################################################################


	"""
	def executeObjectRelation(self, goal):
		print("Processing goal ...")

		result=KBObjectRelationResult()
		feedback=KBObjectRelationFeedback()
		result.relations=[]
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		############################################################################### Such for all related classes ##############################################
		listclasses=[goal.class_name]
		i=0
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			if len(result.classes)>0:
				feedback.feedback=True
			else:
				feedback.feedback=False
		self.role_to_object_server.publish_feedback(feedback)
		self.role_to_object_server.set_succeeded(result)  
		""" 

##########################################################################################################################################################################



	def executeFromRoleToObject(self, goal):
		print("Processing goal ...")

		result=KBFromRoleToObjectResult()
		feedback=KBFromRoleToObjectFeedback()
		result.classes=[]
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		############################################################################### Such for all related classes ##############################################
		listclasses=[goal.class_name]
		print('----------------------------Role To Object----------------', goal.class_name)
		i=0
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#union of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',union_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			i=i+1
				
		################################################################## Iterate Reasoning over all related classes #######################################
		for i in range(len(listclasses)):
			goal.class_name=listclasses[i]
			#simple indirect query 
			try:
				q = self.prolog.query("kb_call([subclass_of(A, '"+self.namespace+"Object'),subclass_of(A,B), has_description(B, some('"+self.namespace+"has_disposition', '"+self.namespace+goal.class_name+"'))]).")
				for solution in q.solutions():
					result.classes.append(solution['A'])
					print(solution['A'])
				q.finish() 
			except Exception as e:
				feedback.feedback=False
				print("*********", str(e))
			try:
				q = self.prolog.query("kb_call([subclass_of(A, '"+self.namespace+"Object'),subclass_of(A,B), has_description(B, some('"+self.namespace+"has_disposition', '"+self.namespace+goal.class_name+"')), has_equivalent_class(A,C)]).")
				for solution in q.solutions():
					result.classes.append(solution['C'])
					print(solution['C'])
				q.finish() 
			except Exception as e:
				feedback.feedback=False
				print("*********", str(e))
			if len(result.classes)>0:
				feedback.feedback=True
			else:
				feedback.feedback=False
		
		############################ Such for all subclasses #################################################
		i=0
		list_classes=result.classes.copy()
		while(i<len(list_classes)):
			class_name=list_classes[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of(A,'"+class_name+"')]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'] not in list_classes:
							list_classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			i+=1
		
		result.classes=list_classes.copy()
		print('----------------------------Role To Object 2----------------', result.classes)
		self.role_to_object_server.publish_feedback(feedback)
		self.role_to_object_server.set_succeeded(result)   

##########################################################################################################################################################################
	def executeDomainRelation(self, goal):
		print("Processing goal ...")

		result=KBDomainRelationResult()
		feedback=KBDomainRelationFeedback()
		result.relations=[]
		if goal.type=='':
			goal='Object'
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		
		if goal.type=='Object':
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A,value('"+goal.namespace+"has_object_domain',B))]).")
				for solution in q.solutions():
					result.relations.append(solution['B'])
					print(solution['B'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
		else:
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A,value('"+goal.namespace+"has_action_domain',B))]).")
				for solution in q.solutions():
					result.relations.append(solution['B'])
					print(solution['B'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
		if len(result.relations)>0:
			feedback.feedback=True
		else:
			feedback.feedback=False
		self.domain_relation_server.publish_feedback(feedback)
		self.domain_relation_server.set_succeeded(result)

##########################################################################################################################################################################
	def executePotentialActionObject(self, goal):
		print("Processing goal ...")

		result=KBListParticipantResult()
		feedback=KBListParticipantFeedback()
		result.classes=[]
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		############################################################################### Such for all related classes ##############################################
		listclasses=[goal.class_name]
		i=0
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							#print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							#print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							#print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#union of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',union_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							#print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			i=i+1
				
		################################################################## Iterate Reasoning over all related classes #######################################
		if goal.type=='Action':
			for i in range(len(listclasses)):
				goal.class_name=listclasses[i]
				
				try:
					q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A, some('"+goal.namespace+goal.relation+"', C)), has_description(C,union_of(D)), member(E,D)]).")
					for solution in q.solutions():
						result.classes.append(str(solution['E']))
						print(solution['E'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				try:
					q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A, some('"+goal.namespace+goal.relation+"', C))]).")
					for solution in q.solutions():
						result.classes.append(str(solution['C']))
						print(solution['C'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
		else:
			for i in range(len(listclasses)):
				goal.class_name=listclasses[i]
				
				try:
					q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A, some('"+goal.namespace+goal.relation+"', C)), has_description(C,union_of(D)), member(E,D)]).")
					for solution in q.solutions():
						result.classes.append(str(solution['E']))
						print(solution['E'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				try:
					q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',B), has_description(B, some('"+goal.namespace+goal.relation+"', C)),has_description(C,some('"+goal.namespace+"has_disposition',F)),subclass_of(G,'"+goal.namespace+"Object'), subclass_of(G,H), has_description(H, some('"+goal.namespace+"has_disposition', F))]).")
					for solution in q.solutions():
						result.classes.append(str(solution['G']))
						print(solution['G'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				try:
					q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+goal.class_name+"',A), has_description(A, some('"+goal.namespace+goal.relation+"', C))]).")
					for solution in q.solutions():
						result.classes.append(str(solution['C']))
						print(solution['C'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				try:
				
					q = self.prolog.query("kb_call([ subclass_of('"+goal.namespace+goal.class_name+"',B), has_description(B, some('"+goal.namespace+goal.relation+"', C)), has_description(C,union_of(D)), member(E,D), has_description(E,some('"+goal.namespace+"has_disposition',F)),subclass_of(G, '"+goal.namespace+"Object'), subclass_of(G,H), has_description(H, some('"+goal.namespace+"has_disposition', F))]).")
					for solution in q.solutions():
						result.classes.append(str(solution['G']))
						print(solution['G'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
			
			
		if len(result.classes)>0:
			feedback.feedback=True
		else:
			feedback.feedback=False
		
		i=0
		list_classes=result.classes.copy()
		while(i<len(list_classes)):
			class_name=list_classes[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of(A,'"+class_name+"')]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'] not in list_classes:
							list_classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
				
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'] not in list_classes:
							list_classes.append(solution['A'])
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
				
			i+=1
		
		result.classes=list_classes.copy()
		
		self.potential_action_object_server.publish_feedback(feedback)
		self.potential_action_object_server.set_succeeded(result)
##########################################################################################################################################################################

	def executeListParticipant(self, goal):
		
		print("Processing goal ...")

		result=KBListParticipantResult()
		feedback=KBListParticipantFeedback()
		result.classes=[]
		result.multiplicity=[]
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		############################################################################### Such for all related classes ##############################################
		listclasses=[goal.class_name]
		i=0
		while(i<len(listclasses)):
			class_name=listclasses[i]
			
			#superclasses
			try:
				q = self.prolog.query("kb_call([subclass_of('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			
			except Exception as e:
				print("*********", str(e))
			
			#equivalentclasses
			try:
				q = self.prolog.query("kb_call([has_equivalent_class('"+goal.namespace+class_name+"',A)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#intersection of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',intersection_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			
			#union of classes
			try:
				q = self.prolog.query("kb_call([has_description('"+goal.namespace+class_name+"',union_of(B)), member(A,B)]).")
				for solution in q.solutions():
					if len(solution['A'].split(goal.namespace))>1:
						if solution['A'].split(goal.namespace).pop() not in listclasses:
							listclasses.append(solution['A'].split(goal.namespace).pop())
							print(solution['A'])
				q.finish() 
			except Exception as e:
				print("*********", str(e))
			i=i+1
				
		################################################################## Iterate Reasoning over all related classes #######################################
		for i in range(len(listclasses)):
			goal.class_name=listclasses[i]
			try:	
				#simple indirect query
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, exactly('"+self.namespace+"has_participant',M, C)), has_description(C,some('"+self.namespace+"has_disposition',E))]).")
					for solution in q.solutions():
						result.classes.append(solution['E'])
						result.multiplicity.append(str(solution['M']))
						print(solution['E'],solution['M'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False   
				
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, exactly('"+self.namespace+"has_participant',M, C)), has_description(C,some('"+self.namespace+"has_disposition',E)),has_description(E,union_of(F))]).")
					for solution in q.solutions():
						res=""
						for r in solution['F']:
							res=res+str(r)+";"
						result.classes.append(res)
						result.multiplicity.append(str(solution['M']))
						print(res,solution['M'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, some('"+self.namespace+"has_participant', C)), has_description(C,some('"+self.namespace+"has_disposition',E)),has_description(E,union_of(F))]).")
					for solution in q.solutions():
						res=""
						for r in solution['F']:
							res=res+str(r)+";"
						result.classes.append(res)
						result.multiplicity.append(str("some"))
						print(res,str("some"))
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
				
				#complex indirect query
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, some('"+self.namespace+"has_participant', C)), has_description(C,some('"+self.namespace+"has_disposition',E))]).")
					for solution in q.solutions():
						result.classes.append(solution['E'])
						result.multiplicity.append(str("some"))
						print(solution['E'],str("some"))
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				#simple direct query
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, some('"+self.namespace+"has_participant', C))]).")
					for solution in q.solutions():
						result.classes.append(solution['C'])
						result.multiplicity.append(str("some"))
						print(solution['C'],str("some"))
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, some('"+self.namespace+"has_participant', C)),has_description(C,union_of(F))]).")
					for solution in q.solutions():
						res=""
						for r in solution['F']:
							res=res+str(r)+";"
						result.classes.append(res)
						result.multiplicity.append(str("some"))
						print(res,str("some"))
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
				
				#complex direct query
				try:
					q = self.prolog.query("kb_call([subclass_of('"+self.namespace+goal.class_name+"',B), has_description(B, exxactly('"+self.namespace+"has_participant',M, C)),has_description(C,union_of(F))]).")
					for solution in q.solutions():
						res=""
						for r in solution['F']:
							res=res+str(r)+";"
						result.classes.append(res)
						result.multiplicity.append(str(solution['M']))
						print(res,solution['M'])
					q.finish() 
					feedback.feedback=True  
				except Exception as e:
					feedback.feedback=False
					
				if len(result.classes)>0:
					feedback.feedback=True
				else:
					feedback.feedback=False
			except Exception as e:
				feedback.feedback=False
				print("*********", str(e))
		self.list_participant_server.publish_feedback(feedback)
		self.list_participant_server.set_succeeded(result)
##########################################################################################################################################################################
         
	def executeLoadBeliefState(self, goal):

		print("Processing goal ...")
		project_path = goal.project_path
		ue_path = goal.ue_path
		binary_path= goal.binary_path
		map_relative_path= goal.map_relative_path
		is_from_binary=goal.is_from_binary
		result=KBLoadOntologyResult()
		feedback=KBLoadOntologyFeedback()
		result.status=True
		feedback.feedback=True
		try:
			if (not is_from_binary):
				print("Loading belief state from game project")
				command=str(ue_path)+" "+str(project_path)+" "+str(map_relative_path)+"  -game  -messaging -SessionName=Playing in Standalone Game -windowed"
				final_command=""
				print("COMMAND: "+str(command))
				final_command=shlex.split(command)
				print("FINAL COMMAND: "+str(final_command))
			if self.currentBeliefState is not None:
				raise Exception("A belief state is still running!") 
			else:                     
				self.currentBeliefState=subprocess.Popen(final_command)
				print("Loading belief state was successful!")	                
		except Exception as e:
			result.status=False
			feedback.feedback=False
			print("Loading belief state failed !!!", str(e))
		self.belief_manager_server.publish_feedback(feedback)
		self.belief_manager_server.set_succeeded(result)


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
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		try:
			if goal.is_sub:
				q = self.prolog.query("kb_call(subclass_of(A, '"+goal.namespace+goal.class_name+"')).")
			else:
				q = self.prolog.query("kb_call(subclass_of('"+goal.namespace+goal.class_name+"', A)).")
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
         
         
	def executeSubProperty(self, goal):
		
		print("Processing goal ...")

		result=KBSubPropertyResult()
		feedback=KBSubPropertyFeedback()
		result.propertyes=[]
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		try:
			if goal.is_sub:
				q = self.prolog.query("kb_call(subproperty_of(A, '"+goal.namespace+goal.property_name+"')).")
			else:
				q = self.prolog.query("kb_call(subproperty_of('"+goal.namespace+goal.property_name+"', A)).")
			for solution in q.solutions():
				result.propertyes.append(solution['A'])
				print(solution['A'])
			q.finish()                
		except Exception as e:
			feedback.feedback=False
			print("*********", str(e))
		self.subproperty_server.publish_feedback(feedback)
		self.subproperty_server.set_succeeded(result)
##########################################################################################################################################################################
	
         
	def executePropertyIO(self, goal):
		
		print("Processing goal ...")

		result=KBPropertyIOResult()
		feedback=KBPropertyIOFeedback()
		result.erange=[]
		result.irange=""
		result.edomain=[]
		result.idomain=""
		feedback.feedback=True
		if len(goal.namespace)<1:
			goal.namespace=self.namespace
		if goal.type_range == "extension":
			try:
				q = self.prolog.query("kb_call([triple('"+goal.namespace+goal.property_name+"', rdfs:'range', RANGE),triple(RANGE,'http://www.w3.org/2002/07/owl#oneOf',LIST)]).")
				for solution in q.solutions():
					LIST=solution['LIST']
				q.finish()
				while True:
					if LIST.split("#").pop()=="nil":
						break
					else:
						q = self.prolog.query("kb_call([triple('"+str(LIST)+"',rdf:first,FIRST),triple('"+str(LIST)+"',rdf:rest,LIST)]).")
						for solution in q.solutions():
							FIRST=solution['FIRST']
							LIST=solution['LIST']
							result.erange.append(str(FIRST))
						q.finish()               
			except Exception as e:
				feedback.feedback=False
				print("*********", str(e))
		self.property_io_server.publish_feedback(feedback)
		self.property_io_server.set_succeeded(result)
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

		result=KBListPropertyResult()
		feedback=KBListPropertyFeedback()
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

		result=KBObjectPropertyResult()
		feedback=KBObjectPropertyFeedback()
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
	def executeDataProperty1(self, goal):
		
		print("Processing goal ...")

		result=KBDataPropertyResult()
		feedback=KBDataPropertyFeedback()
		result.values=[]
		feedback.feedback=True
		try:
		
			if goal.quantifier == "only" or goal.quantifier == "some" or goal.quantifier == "value":
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+class_name+"', C), has_description(C,"+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+class_name+"', "+ goal.quantifier+"('"+self.namespace+goal.property_name+"',A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
			else:
				(nature, delimiter)=self.parseAttribute(goal.quantifier)
				q = self.prolog.query("kb_call((subclass_of('"+self.namespace+class_name+"', C), has_description(C,"+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
				for solution in q.solutions():
					result.values.append(solution['A'])
					print(solution['A'])
				q.finish()
				
				q = self.prolog.query("kb_call((has_description('"+self.namespace+class_name+"', "+ nature+"('"+self.namespace+goal.property_name+"',"+ delimiter+",A)))).")
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
				
	def executeDataProperty(self, goal):
		
		print("Processing goal ...")

		result=KBDataPropertyResult()
		feedback=KBDataPropertyFeedback()
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

		result=KBNewIndividualResult()
		feedback=KBNewIndividualFeedback()
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

		result=KBCommonPoseResult()
		feedback=KBCommonPoseFeedback()
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
  
  
    
    
 
    
  
