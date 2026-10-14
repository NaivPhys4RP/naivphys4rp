#!/usr/bin/env python3
import rospy
import sys
import os
import time
import random
import subprocess
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

class Action():
	def __init__(self, name='', vcd={}, roles=[], ontology_id=''):
		self.name=name
		self.verification_capability_distribution=vcd
		self.ontology_id=ontology_id
		self.roles=roles
	
	def __str__(self):
		return " Name: "+str(self.name)+"\n Ontology Id: "+ str(self.ontology_id)+"\n Roles: "+ str(self.roles)+"\n verification: "+ str(self.verification_capability_distribution)
	
	def set_ontology_id(self):
		pass

class ActionParser():

	def __init__(self, path_name='actions.yaml'):
		self.yaml_actions={}
		self.set_actions=[]
		self.actual_action=[]
		#starting prolog and action server
		self.prolog = Prolog()
		try:
			with open(path_name, 'r') as file:
				self.yaml_actions=yaml.safe_load(file)
			print(self.yaml_actions)
			print("Parsing of actions ended successfully!")
			# build different action objects
			for act in self.yaml_actions.keys():
				self.set_actions.append(Action(name=act, vcd=self.yaml_actions[act]['verification'], roles=self.yaml_actions[act]['roles']))
		except Exception as e:
			print("error occured while parsing action: "+str(e))
		print('Auto test of modules starting ... \n\n\n\n\n')
		print(self.filter_actions(action_key='Grasp', vcd_key={}, role_keys=[]))
		print("\n")
		print(self.filter_actions(action_key='', vcd_key={}, role_keys=['Sensor']))
		print("\n")
		print(self.filter_actions(action_key='', vcd_key={}, role_keys=['Destination', 'Source']))
		print('\n\n\n\n\n Auto test of modules completed!')
		
	def filter_actions(self, action_key='', vcd_key={}, role_keys=[]):
		list_actions=[]
		for key in self.yaml_actions.keys():
			if action_key.lower() in key.lower():
				valid=True
				for vcd_k in vcd_key.keys():
					if vcd_key[vcd_k]> self.yaml_actions[key]['verification'][vcd_k]:
						valid=False
						break
				if not valid:
					continue
				for role in role_keys:
					if role not in self.yaml_actions[key]['roles']:
						valid=False
						break
				if not valid:
					continue
				list_actions.append(str(Action(name=key, vcd=self.yaml_actions[key]['verification'], roles=self.yaml_actions[key]['roles'])))
		return list_actions
		
	
