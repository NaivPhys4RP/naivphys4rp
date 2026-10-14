#!/usr/bin/env python3
import rospy
import sys
import os
import time
import random
import glob
import yaml
from datetime import datetime
from datetime import datetime, timedelta
try:
	from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
	from rosprolog_client import PrologException, Prolog 
	print('Loading rosprolog ...') 
import json
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,SCRIPT_DIR )

class Verifier():
	def __init__(self, name='', mode='', description='', domains=[] ):
		self.name=name
		self.mode=mode
		self.description=description
		self.domains=domains


class VerifierParser():
	def __init__(self, path_name='verifiers'):
		self.yaml_verifiers=[]
		self.set_verifiers=[]
		self.actual_verifier=[]
		#starting prolog and action server
		self.prolog = Prolog()
		list_verifiers=glob.glob(path_name+'/*.yaml')	
	
		for filename in list_verifiers:
			try:	
				verifier_yaml=''   
				with open(filename, 'r') as file:
					verifier_yaml=yaml.safe_load(file)
					self.yaml_verifiers.append(verifier_yaml.copy())
				print(self.yaml_verifiers)
				# build different verifier objects
				self.set_verifiers.append(Verifier(name=verifier_yaml['verifier']['name'], mode=verifier_yaml['verifier']['mode'], description=verifier_yaml['verifier']['description'], domains=verifier_yaml['domains']))
				print("Parsing of verifiers ended successfully!")
			except Exception as e:
				print("error occured while parsing action: "+str(e))
		print('Auto test of modules starting ... \n\n\n\n\n')
		#print(self.filter_verifiers(action='Grasping', mode='Success'))
		#print(self.filter_verifiers(action='Grasping', mode='Feasibility'))
		#print('\n\n\n Testing \n\n\n')
		
		#print('\n\n\n\n\n Auto test of modules completed!')
	
	
	def are_list_matching(self, actual, expected, relaxed=False):
		try:
			actual_m=[a.lower() for a in actual]
			expected_m=[e.lower() for e in expected]
			if actual_m==[] and expected_m!=[] and (not relaxed):
				return False
			nb=0
			for a in actual_m:
				for e in expected_m:
					if len(a)==0 and len(e)!=0 and (not relaxed):
						continue
					if a in e:
						nb+=1
			
			return nb>=len(actual_m)
		except Exception as e:
			print('Error1: '+str(e), actual, expected)
			return False
		
	def find_all_index(self, e, l):
		try:
			result=[]
			for i in range(len(l)):
				if e==l[i]:
					result.append(i)
			return result
		except Exception as e:
			print('Error2: '+str(e))
			return []
		
	def get_matching_key(self, target_key, list_keys):
		try:
			for key in list_keys:
				if target_key.lower() in key.lower():
					return key
			return None
		except Exception as e:
			print('Error3: '+str(e))
			return None
	
	def are_dict_matching(self, actual, expected, relaxed=False):
		print('INPUTS: ', actual, expected)
		try:
			a_keys=list(actual.keys())
			e_keys=list(expected.keys())
			if self.are_list_matching(list(a_keys),list(e_keys), relaxed=relaxed):
				for a_key in a_keys:
					e_key=self.get_matching_key(a_key, e_keys)
					if not self.are_list_matching(actual[a_key], expected[e_key], relaxed=relaxed):
						return False
				return True
			else:
				return False
		except Exception as e:
			print('Error4: '+str(e))
			return False
	
		
	#filter the verifiers that meet certain constrainsts.	
	def filter_verifiers(self, name='', description='', mode='', action='', participants={}, modalities=[], relaxed=False):
		results=[]
		for yaml_verifier in self.yaml_verifiers:
			if name.lower() in yaml_verifier['verifier']['name'].lower():
				if description.lower() in yaml_verifier['verifier']['description'].lower(): 
					if mode.lower() in yaml_verifier['verifier']['mode'].lower():
						for domain in yaml_verifier['domains']:
							for task in domain.keys():
								try:
									print('VERIFIER BEING SCANNED: ', yaml_verifier['verifier']['name'])
									if action.lower() in task.lower() and self.are_dict_matching(participants,domain[task]['objects'], relaxed=relaxed):
										results.append(yaml_verifier.copy())
										break
								except Exception as e:
									print('Warning when filtering verifiers: '+str(e))
		print('Verifiers found :', name, [r['verifier']['name']  for r in results])
		print('Participants found: ','Task:',action, participants, 'Participants expected: ',[r['domains']  for r in results])
		return results
