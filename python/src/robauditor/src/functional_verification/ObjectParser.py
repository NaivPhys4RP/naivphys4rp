#!/usr/bin/env python3
import rospy
import sys
import os
import time
import random
import subprocess
from datetime import datetime, timedelta
from datetime import datetime, timedelta
try:
	from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
	from rosprolog_client import PrologException, Prolog 
	print('Loading rosprolog ...') 
import json
from std_msgs.msg import String
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,SCRIPT_DIR )
import yaml
import rosbag
from rosbag.bag import Bag


class Object():
	def __init__(self, name='', types='', source_tree={}):
		self.name=name
		self.ontology_id=''
		self.types=types
		self.source_tree=source_tree
	
	def __str__(self):
		return " Name: "+str(self.name)+"\n Ontology Id: "+ str(self.ontology_id)+"\n Types: "+ str(self.types)+"\n Source Tree: "+ str(self.source_tree)

class ObjectParser():

	def __init__(self, path_name='objects.yaml'):
		self.yaml_objects=[]
		self.set_objects=[]
		self.parent_splitter='.'
		self.types_splitter='@'
		self.actual_object=[]
		#starting prolog and action server
		self.prolog = Prolog()
		try:
			with open(path_name, 'r') as file:
				self.yaml_objects=yaml.safe_load(file)
			print(self.yaml_objects)
			print("Parsing of objects ended successfully!")
			# build different modalities
			for obj in self.yaml_objects:
				parents=obj.split(self.parent_splitter)
				s_tree={}
				p=None
				for i in  range(len(parents)):
					r=parents[i].split(self.types_splitter)
					if len(r)>1:
						r1=r[1]
					else:
						r1=''
					s_tree[r[0]]={'parent':p, 'types':r1}
					p=r[0]
				self.set_objects.append(Object(name=r[0], types=r1, source_tree=s_tree))
		except Exception as e:
			print("error occured while parsing objects: "+str(e))
		print('Auto test of modules starting ... \n\n\n\n\n')
		print(self.filter_objects())
		print("\n")
		print(str(self.filter_formatted_objects()[0]))
		print("\n")
		print('\n\n\n\n\n Auto test of modules completed!')
	
	def get_all_objects(self):
		return self.yaml_objects
	
	def filter_objects(self, object_key=''):
		result=[]
		for obj in self.yaml_objects:
			if object_key in obj:
				result.append(obj)
		return result
		
	def filter_formatted_objects(self, object_key='', type_key=''):
		result=[]
		for obj in self.set_objects:
			if object_key in obj.name and type_key in obj.types:
				result.append(obj)
		return result
		
		
		
		
		
		
