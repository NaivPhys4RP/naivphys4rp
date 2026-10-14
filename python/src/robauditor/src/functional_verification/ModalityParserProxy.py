#!/usr/bin/env python3
import rospy
import sys
import os
import glob
import time
import random
import subprocess
import numpy as np
import psutil
import actionlib
import roslib
import rospkg
rospack = rospkg.RosPack()
roslib.load_manifest('tracebot_msgs')
from tracebot_msgs.msg import *
from datetime import datetime, timedelta
from datetime import datetime, timedelta
try:
	from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
	from rosprolog_client import PrologException, Prolog 
	print('Loading rosprolog ...')
import json
from std_msgs.msg import String
from cv_bridge import CvBridge
from sensor_msgs.msg import *
import cv2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,SCRIPT_DIR )
import yaml
import rosbag
from rosbag.bag import Bag
class Modality():
	def __init__(self, key='', data=''):
		pass

class ModalityParser():

	def __init__(self, path_name='modalities.yaml'):
		self.set_modalities=[]
		self.yaml_modalities=''
		self.actual_topic=[]
		self.width=640
		self.height=480
		self.max_experience_terminate_time=20.0
		self.neem_experience_stop_command={}
		self.actual_ontology=[]
		self.neem_experience_recorder={}
		self.tactile_specific_actions=[]
		#starting prolog and action server
		self.prolog = Prolog()
		
		try:
			with open(path_name, 'r') as file:
				self.yaml_modalities=yaml.safe_load(file)
			print(self.yaml_modalities,'\n\n\n')
			print("Parsing of info source modalities ended successfully!")
			# build different modalities
			for modality in self.ybelief_perceived_at(aml_modalities.keys():
				self.set_modalities.append(Modality(data=self.yaml_modalities[modality],key=modality))
			self.actual_topic=self.filter_topic()
			print('*********** TOPIC LIST ******************: ', self.actual_topic,'\n\n\n')
			
					
		except Exception as e:
			print("error occured while parsing info source modalities: "+str(e))
			
		print('Searching the name of tactile data recorder ...')
		
		stop_action_name=[]
		start_action_name=[]
		for topic in self.actual_topic:
			if 'start_recording_action' in topic.keys():
				start_action_name.append(topic['start_recording_action']['name'])
			if 'stop_recording_action' in topic.keys():
				stop_action_name.append(topic['stop_recording_action']['name'])
		
		# remove duplication
		start_action_name=list(set(start_action_name))
		# remove duplication
		stop_action_name=list(set(stop_action_name))
		print('Start tactile recorders found: ', start_action_name)
		print('Stop tactile recorders found: ', stop_action_name)
				
		print("Loading client for starting tactile recording")	
		self.tactile_experience_start_client=[]
		for recorder in start_action_name:	
			self.tactile_experience_start_client.append(actionlib.SimpleActionClient(start_action_name,
					                            TTVStartBufferingAction))
		
		print("Loading client for stopping tactile recording")
		self.tactile_experience_stop_client=[]
		for recorder in stop_action_name:
			self.tactile_experience_stop_client.append(actionlib.SimpleActionClient(stop_action_name,
							                    TTVStopBufferingAction))
		print('\n\n\n\n AUTO TEST FOR DICO MATCH FUNCTION \n\n\n\n\n')
		a={'actor':[]}
		e={}
		print('\n\n Test: ', a,e, self.are_dict_matching(a,e))
		
		a={'actor':[]}
		e={'Actor_dghdjhd':['']}
		print('\n\n Test: ', a,e, self.are_dict_matching(a,e))
		
		a={}
		e={'Actor':['']}
		print('\n\n Test: ', a,e, self.are_dict_matching(a,e))
		
		
		"""
		print('Auto test of modules starting ... \n\n\n\n\n')
		print(self.filter_modalities(key='a'))
		print(self.filter_modalities())
		print(self.filter_topic())
		self.neem_experience_start()
		time.sleep(14.0)
		self.neem_experience_stop()
		print(self.neem_experience_get_info_V2(input_bag_name='2023-08-07-17-23-18.bag'))
		print("/n")
		print(self.neem_experience_get_typed_topics(input_bag_name='2023-08-07-17-23-18.bag'))
		print("\n")
		
		print(self.neem_experience_sgs( source_folder='/media/franklin/Data/bag', input_bag_name='ilias1.bag', topic='/camera/color/image_raw', nbs=2,begin_time=datetime(2022,5,25,10,17,13) ))
		print("\n")
		
		o=self.filter_ontology(ontology_key='soma')
		print(o)belief_perceived_at(
		print("\n")
		print(self.load_ontology(package=o[0]['package'], ontology_path=o[0]['pathname']))
		print("\n")
		"""
		print('\n\n\n\n\n Auto test of modules completed!')

		print('TPOSES: ', self.get_expected_pose( object_key='', target_frame_key=''))
		print('TOPICS: ', self.get_dt_transform_topics( value_key='dynamic'))



	
	def get_expected_pose(self, object_key='', target_frame_key=''):
		result=[]
		try:
			print('Retrieving object expected pose ...')
			mods=self.filter_modalities(key='DT-Based')
			mods=self.yaml_modalities[mods[0]]['topics']
			if mods!=[]:
				for mod in mods:
					if mod['source']=='Cell' and 'world_frame' in list(mod.keys()) and 'expected_pose_object_frame' in list(mod.keys()):
						for pose in mod['expected_pose_object_frame']:
							sub_res={'world_frame': mod['world_frame']}
							if object_key.lower() in pose['object'].lower() and target_frame_key.lower() in pose['target_frame'].lower():
								sub_res['object'] = pose['object']
								sub_res['target_frame'] = pose['target_frame']
								result.append(sub_res.copy())
		except Exception as e:
			print('Issues encountered when retrieving object expected pose: '+str(e))
		return result
	
	def get_dt_transform_topics(self, value_key=''):
		return self.filter_topic(modality_key='DT-Based', topic_key='', source_key='Cell', value_key=value_key)
		
	def getAllModalities(self):
		pass
	
	def findModality(self, list_musters):
		pass
	
	def filter_modalities(self, key=''):
		result=[]
		for modality in self.yaml_modalities.keys():
			if key.lower() in modality.lower():
				result.append(modality)
		return result
	
	def filter_topic(self, modality_key='', topic_key='', source_key='', value_key=''):
		actual_topic=[]belief_perceived_at(
		for modality in self.yaml_modalities.keys():
			if modality_key.lower() in modality.lower():
				if 'topics' in list(self.yaml_modalities[modality].keys()):
					for topic_data in self.yaml_modalities[modality]['topics']:
						if source_key.lower() in topic_data['source'].lower():
							for val_key in topic_data['value'].keys():	
								if (value_key.lower() in val_key.lower()) and (topic_key.lower() in str(topic_data['value'][val_key]).lower()):
									topic={}
									topic['source']=topic_data['source']
									topic['value']=val_key
									try:
										assert val_key in topic_data['throttle_value']	     
										topic['throttle_frequency']=float(topic_data['throttle_frequency'])
										topic['name']=topic_data['value'][val_key]+'_throttle'
									except Exception as e:
										topic['name']=topic_data['value'][val_key]
										print('Failed to throttle the topic. Frequency should be float: '+str(e))
								        
									topic['modality']=modality
									if 'start_recording_action' in topic_data.keys():
										topic['start_recording_action']=topic_data['start_recording_action']
									if 'stop_recording_action' in topic_data.keys():
										topic['stop_recording_action']=topic_data['stop_recording_action']
									if 'world_frame' in topic_data.keys():
										topic['world_frame']=topic_data['world_frame']
									actual_topic.append(topic.copy())
		return actual_topic
	
	
	
	
	def filter_ontology(self, modality_key='', package_key='', ontology_key=''):
		self.actual_ontology=[]
		for modality in self.yaml_modalities.keys():
			if modality_key.lower() in modality.lower():
				if 'ontologies' in list(self.yaml_modalities[modality].keys()):
					for ontology_data in self.yaml_modalities[modality]['ontologies']:	
						if (package_key.lower() in ontology_data['package'].lower()) and (ontology_key.lower() in ontology_data['pathname'].lower()):
							ontology={}
							ontology['package']=ontology_data['package']
							ontology['pathname']=ontology_data['pathname']
							self.actual_ontology.append(ontology.copy())
		return self.actual_ontology
		
	def get_current_neem_experience(self, destination_folder='.', root_name=None):
		lbf=list(sorted(glob.glob(destination_folder+'/*.bag*'), key=os.path.getmtime))
		list_bag_files=[]belief_perceived_at(
		if root_name is not None:
			for files in lbf:
				if root_name in files:
					list_bag_files.append(files)
		else:
			list_bag_files=lbf.copy()
			if list_bag_files!=[]:
				return list_bag_files.pop()
			else:
				return ''
		if list_bag_files!=[]:
			return list_bag_files.pop()
		else:
			return self.get_current_neem_experience(destination_folder=destination_folder, root_name=None) #return the most recent available experience


	def neem_experience_start(self, destination_folder='/home/franklin/neem_experience', root_name=None, extension='.bag'):
		
		print('Recording of neem experience starting ...')
		if root_name is not None:
			command='rosbag record -O '+root_name+' '
		else:
			command='rosbag record'
		for topic in self.actual_topic:
			if topic['name'].__class__==str:	
				command=command+' '+topic['name']
		self.neem_experience_stop_command[root_name]=command.split(' ')
		print('\n\n\n\n',command,'n\n\n\n')
		self.neem_experience_recorder[root_name] = subprocess.Popen(command.split(), shell=False, cwd=destination_folder)
		

	def neem_experience_stop(self, destination_folder='/home/franklin/neem_experience', root_name=None, basefolder='experience', extension=''):
		
		if len(self.neem_experience_recorder) > 0:
			for proc in psutil.process_iter():
				if "record" in proc.name() and set(self.neem_experience_stop_command[root_name][2:]).issubset(proc.cmdline()):
					try:    	                                                         
						proc.send_signal(subprocess.signal.SIGTERM)
						proc.communicate()
						print('Killing subprocess: '+proc.name()+' ...')
					except Exception as e:
						print('Terminating neem recording ...')
			try:
				self.neem_experience_recorder[root_name].send_signal(subprocess.signal.SIGTERM)
				self.neem_experience_recorder[root_name].communicate()
				print('Killing process: '+self.neem_experience_recorder[root_name].name()+' ...')
			except Exception as e:
				print('Terminating neem recording ...')
		self.neem_experience_recorder.pop(root_name, None)
		self.neem_experience_stop_command.pop(root_name, None)	
		#reindex the resulted bag file
		start_time=time.time()
		while True:
			lbf=list(sorted(glob.glob(destination_folder+'/*.bag'), key=os.path.getmtime))
			list_bag_files=[]
			if root_name is not None:
				for files in lbf:
					if root_name in files:
						list_bag_files.append(files)
			else:
				list_bag_files=lbf.copy()
			if list_bag_files==[]:
				time.sleep(1.0) #sleep and wait till the process terminate correctly
			else:
				break #exit the while when the process has terminated correctly
			end_time=time.time()
			if end_time-start_time>self.max_experience_terminate_time:
				break #break if the clean termination has been waited for a certain time preventing endless loop
		print(list_bag_files)
		if list_bag_files!=[]:
			file_path=list_bag_files.pop()
			base_name=os.path.basename(file_path)
			root_name=base_name.split('.')[0]
			try:
				command='rosbag reindex '+str(base_name)
				p=subprocess.Popen(command.split(), stdin=subprocess.PIPE, shell=False, cwd=destination_folder)
				p.wait() #wait the reindexing to complete
				#remove unfinished bag files
				if os.path.exists(destination_folder+'/'+root_name+'.bag.orig.active'):
					os.remove(destination_folder+'/'+root_name+'.bag.orig.active')
				#remove unfinished bag files
				if os.path.exists(destination_folder+'/'+root_name+'.bag.active'):
					os.remove(destination_folder+'/'+root_name+'.bag.active')
				#rename new index bag file
				file_path=destination_folder+'/'+root_name+'.orig.bag'
				if os.path.exists(file_path):
					os.rename(file_path, destination_folder+'/'+root_name+'.bag')
			except Exception as e:
				print('Reindexing bagfile failed or was not necessary: '+str(e))
			file_path=destination_folder+'/'+root_name+'.bag'
			if os.path.exists(file_path):		  
				os.rename(file_path, destination_folder+'/'+basefolder+'/'+root_name+'.bag')
		print('Recording of neem experience completed!')

	        
	        
	def neem_experience_stop_V2(self, destination_folder='/home/franklin/neem_experience', basefolder='experience', extension=''):
		if self.neem_experience_recorder is not None:
			for proc in psutil.process_iter():
				if "record" in proc.name() and set(self.neem_experience_stop_command[2:]).issubset(proc.cmdline()):
					proc.send_signal(subprocess.signal.SIGINT)
			self.neem_experience_recorder.send_signal(subprocess.signal.SIGINT)
		self.neem_experience_recorder=None
		#reindex the resulted bag file
		list_bag_files=list(sorted(glob.glob(destination_folder+'/*.bag*'), key=os.path.getmtime))
		print(list_bag_files)
		if list_bag_files!=[]:
			file_path=list_bag_files.pop()
			base_name=os.path.basename(file_path)
			root_name=base_name.split('.')[0]
			try:
				command='rosbag reindex '+str(base_name)
				p=subprocess.Popen(command.split(), stdin=subprocess.PIPE, shell=False, cwd=destination_folder)
				p.wait() #wait the reindexing to complete
				#remove backup
				if os.path.exists(destination_folder+'/'+root_name+'.bag.orig.active'):
					os.remove(destination_folder+'/'+root_name+'.bag.orig.active')
				#rename new index bag file
				
				if os.path.exists(destination_folder+'/'+root_name+'.bag.active'):
					os.rename(file_path, destination_folder+'/'+root_name+'.bag')
			except Exception as e:
				print('Reindexing bagfile not necessary: '+str(e))
			os.rename(destination_folder+'/'+root_name+'.bag', destination_folder+'/'+basefolder+'/'+root_name+'.bag')
		print('Recording of neem experience completed!')
		
	def neem_experience_start_V2(self, destination_folder='/home/franklin/neem_experience', extension='.bag'):
		print('Recording of neem experience starting ...')
		command='rosbag record'
		for topic in self.actual_topic:
			if topic['name'].__class__==str:	
				command=command+' '+topic['name']
		self.neem_experience_stop_command=command.split(' ')
		self.neem_experience_recorder = subprocess.Popen(command.split(), stdin=subprocess.PIPE, shell=False, cwd=destination_folder)
		
		
	def neem_experience_time_indexing(self, destination_folder='/home/franklin', input_bag_name='input.bag', output_bag_name='output.bag'):
		with rosbag.Bag('output.bag', 'w') as outbag:
			for topic, msg, t in rosbag.Bag('input.bag').read_messages():
		 		# This also replaces tf timestamps under the assumption 
		 		# that all transforms in the message share the same timestamp
				if topic == "/tf" and msg.transforms:
					outbag.write(topic, msg, msg.transforms[0].header.stamp)
				else:
					outbag.write(topic, msg, msg.header.stamp if msg._has_header else t)
				
	def neem_experience_add_metadata(self, episode_id='', destination_folder='/home/franklin', input_bag_name='input.bag'):
		with rosbag.Bag('input.bag', 'a') as bag:
			metadata_msg = String(data='my metadata')
			bag.write('/metadata', metadata_msg, rospy.Time(bag.get_end_time()))
	
	def neem_experience_get_info_V1(self, source_folder='/home/franklin/Documents/bagfiles', input_bag_name='input.bag'):
		self.neem_experience_info_dict = yaml.load(subprocess.Popen(['rosbag', 'info', '--yaml', input_bag_name], shell=False, stdout=subprocess.PIPE, cwd=source_folder).communicate()[0])
		return self.neem_experience_info_dict
		
	def neem_experience_get_info_V2(self, source_folder='/home/franklin/Documents/bagfiles', input_bag_name='input.bag'):
		infos={}
		try:
			self.neem_experience_info_dict = yaml.safe_load(Bag(source_folder+'/'+input_bag_name, 'r')._get_yaml_info())
			return self.neem_experience_info_dict
		except Exception as e:
			print('Fetching infos from ros bag failed: '+str(e))
		return infos
		
	def neem_experience_get_typed_topics(self, source_folder='/home/franklin/Documents/bagfiles', input_bag_name='input.bag'):
		info=self.neem_experience_get_info_V2(source_folder=source_folder,input_bag_name=input_bag_name)
		self.typed_topics={}
		if 'topics' in list(info.keys()):
			self.typed_topics=info['topics'].copy()
		return self.typed_topics
	
	
	
	def tactile_experience_start(self):
		print('Starting the recording of tactile data for the action ...')
		for i in range(len(self.tactile_experience_start_client)):
			result=None
			if not self.tactile_experience_start_client[i].wait_for_server(timeout = rospy.Duration(3)):
	 			return result
			goal = TTVStartBufferingGoal()
			goal.verification_type=3
			self.tactile_experience_start_client[i].send_goal(goal)
			self.tactile_experience_start_client[i].wait_for_result()
			self.tactile_experience_start_client[i].get_result()
        
	def tactile_experience_stop(self):
		print('Stoping the recording of tactile data for the action ...')
		result=None
		for i in range(len(self.tactile_experience_stop_client)):
			result=None
			if not self.tactile_experience_stop_client[i].wait_for_server(timeout = rospy.Duration(3)):
	 			return result
			goal = TTVStopBufferingGoal()
			self.tactile_experience_stop_client[i].send_goal(goal)
			self.tactile_experience_stop_client[i].wait_for_result()
			result=TTVStopBufferingResult()
			result=self.tactile_experience_stop_client[i].get_result()
			result.success=True
			result.duration=0.87
			print("Result from tactile verification: Decision - ",result.success," Confidence - ",result.duration)
		return result belief_perceived_at(
        
	def are_list_matching(self, actual, expected):
		actual_m=[a.lower() for a in actual]
		expected_m=[e.lower() for e in expected]
		nb=0
		for a in actual_m:
			for e in expected_m:
				if a in e:
					nb+=1
		
		return nb>=len(actual_m)
		
	def find_all_index(self, e, l):
		result=[]
		for i in range(len(l)):
			if e==l[i]:
				result.append(i)
		return result
		
	def get_matching_key(self, target_key, list_keys):
		for key in list_keys:
			if target_key.lower() in key.lower():
				return key
		return None
	
	def are_dict_matching(self, actual, expected):
		 a_keys=list(actual.keys())
		 e_keys=list(expected.keys())
		 if self.are_list_matching(list(a_keys),list(e_keys)):
		 	for a_key in a_keys:
		 		e_key=self.get_matching_key(a_key, e_keys)
		 		if not self.are_list_matching(actual[a_key], expected[e_key]):
		 			return False
		 	return True
		 else:
		 	return False
		 	
	def get_participant_roots(self, participants):
		participant_roots={}
		for role in participants.keys():
			new_role=role.split('#').pop().split('_')[0].split('Role')[0]
			participant_roots[new_role]=[]
			for obj in participants[role]:
				participant_roots[new_role].append(obj.split('#').pop().split('_')[0])
				participant_roots[new_role]=list(set(participant_roots[new_role]))
		return participant_roots
	 			
	# special version
	def neem_experience_get_msgs_sv(self, source_folder='/home/franklin/bagfiles', input_bag_name='input.bag', topic='/joint_states', cahe=nonverbal_explanation_dict, sorted_keys=list_keys, flags=0 ):
	        begin_time=datetime(2023,8,7,15,23,18)
	        nbs=1
	        pivot=0
	        N=len(list(list_keys))
		self.msgs=[]
		print('THE BAG FILES: ', source_folder+'/'+input_bag_name, 'TIME: ', begin_time )
		try:
			for top, msg, t in rosbag.Bag(source_folder+'/'+input_bag_name).read_messages(topics=[topic]):
				if pivot>=N:
					break #exit when no more action to look for
				if top==topic and self.rostime_to_datetime(t)>=nonverbal_explanation_dict[list_keys[pivot]]['ET']:
					nonverbal_explanation_dict[list_keys[pivot]]['message'][flags].append(msg)
					pivot=pivot+1
		except Exception as e:
			print('Fetching messages from ros bag failed: '+str(e))
			return False
		return True
	
		
	def neem_experience_get_msgs(self, source_folder='/home/franklin/bagfiles', input_bag_name='input.bag', topic='/joint_states', nbs=1, begin_time=datetime(2023,8,7,15,23,18) ):
		self.msgs=[]
		print('THE BAG FILES: ', source_folder+'/'+input_bag_name, 'TIME: ', begin_time )
		try:
			for top, msg, t in rosbag.Bag(source_folder+'/'+input_bag_name).read_messages():
				#print('found: ',self.rostime_to_datetime(t), ' expected: ', begin_time)
				if top!=topic or self.rostime_to_datetime(t)<begin_time:
					continue
				if nbs:
					dict_msg={}
					dict_msg['timestamp']=t
					dict_msg['message']=msg
					self.msgs.append(dict_msg.copy())
					nbs-=1
				else:
					break
		except Exception as e:
			print('Fetching messages from ros bag failed: '+str(e))
		return self.msgs
	
	def datetime_to_rostime(self,dt0):	
		rt0 = rospy.Time.from_sec(dt0.replace(tzinfo=datetime.timezone.utc).timestamp())
		return rt0
		
	def rostime_to_datetime(self,rt0):
		dt0 = datetime.fromtimestamp(rt0.to_sec())
		return dt0
		
	
	def load_ontology(self, package='', ontology_path=''):
		packageName = package
		relativePath= ontology_path
		result=True
		print("Loading ontology from:", packageName, relativePath)
		try:
			q=self.prolog.query("load_owl('package://"+str(packageName)+"/"+str(relativePath)+"').")
			#check if loading was successful
			solution=next(q.solutions())
			print("Loading ontology was successful")
			q.finish()	                
		except Exception as e:
			result=False
			print("*********", str(e))
		return result
	
	def read_compressed_color_image(self, image, save=False, base_name='image', extension='png', folder='.', index=0, iwidth=640, iheight=480, cvMode='bgr8'):
		np_arr = np.fromstring(image.data, np.uint8)
		#print(len(np_arr))
		image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
		image = (self.camera_resize([image], iwidth, iheight)[0]).copy()
		if save:
			try:
				cv2.imwrite(folder+'/'+base_name+str(index)+'.'+extension, image)
			except Exception as e:
				print('Failed to save image: '+str(e))
		return image
			
	def read_compressed_depth_image(self, image, save=False, base_name='image', extension='png', folder='.', index=0, iwidth=640, iheight=480, cvMode='bgr8'):
		depth_header_size = 12
		raw_data = image.data[depth_header_size:]
		image = cv2.imdecode(np.fromstring(raw_data, np.uint8), cv2.IMREAD_UNCHANGED)
		#print(image)
		image = (self.camera_resize([image], iwidth, iheight)[0]).copy()
		if save:
			try:
				cv2.imwrite(folder+'/'+base_name+str(index)+'.'+extension, image)
			except Exception as e:
				print('Failed to save image: '+str(e))
		return image


	def read_perception_result(self,result_msg,save=False, base_name='color_image', extension='png', folder='.', index=0, iwidth=640, iheight=480, cvMode='bgr8'):
		result_msg = result_msg.result
		image=result_msg.color_image
		bboxes=result_msg.bounding_boxes
		object_types=result_msg.object_types
		confidences=result_msg.confidences
		bridge = CvBridge()
		image = bridge.imgmsg_to_cv2(image, cvMode)
		#write onto the image
		for i in range(len(bboxes)):
			x1, y1, x2, y2 = [bboxes[i].x_offset,bboxes[i].y_offset,bboxes[i].x_offset+bboxes[i].width, bboxes[i].y_offset+bboxes[i].height]
			cv2.rectangle(image, (x1, y1), (x2, y2), (255,255,0), 5)
			font = cv2.FONT_HERSHEY_SIMPLEX
			# org
			org = (x1, y1)
			# fontScale
			fontScale = 0.6
			# Blue color in BGR
			color = (0,255,0)
			# Line thickness
			thickness = 1
			area=(x2-x1)*(y2-y1)
			image = cv2.putText(image,  str(str(object_types[i])+': '+str(confidences[i])) , org, font, fontScale, color, thickness, cv2.LINE_AA)
		image = (self.camera_resize([image], iwidth, iheight)[0]).copy()
		if save:
			try:
				cv2.imwrite(folder+'/'+base_name+str(index)+'.'+extension, image)
			except Exception as e:
				print('Failed to save image: '+str(e))
		return image


	def read_raw_color_image(self,image,save=False, base_name='color_image', extension='png', folder='.', index=0, iwidth=640, iheight=480, cvMode='bgr8'):
		bridge = CvBridge()
		image = bridge.imgmsg_to_cv2(image, cvMode)
		image = (self.camera_resize([image], iwidth, iheight)[0]).copy()
		if save:
			try:
				cv2.imwrite(folder+'/'+base_name+str(index)+'.'+extension, image)
			except Exception as e:
				print('Failed to save image: '+str(e))
		return image
		
	def read_raw_depth_image(self,image, save=False, base_name='image', extension='png', folder='.', index=0, iwidth=640, iheight=480, cvMode='32FC1'):
		bridge = CvBridge()
		image = bridge.imgmsg_to_cv2(image, cvMode)
		image=np.ceil((np.array(image)/np.max(image))*255)
		image=np.uint8(image)
		image=cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
		#print(image.shape)
		image = (self.camera_resize([image], iwidth, iheight)[0]).copy()
		if save:
			try:
				cv2.imwrite(folder+'/'+base_name+str(index)+'.'+extension, image)
			except Exception as e:
				print('Failed to save image: '+str(e))
		return image
		
	def camera_resize(self, images, meanSize1, meanSize2):
		normImages = []
		try:
			for i in range(len(images)):
				if (images[i].shape[0] * images[i].shape[1] < meanSize1 * meanSize2):
					normImages.append(np.array(cv2.resize(images[i].copy(), (meanSize1, meanSize2),
						                          interpolation=cv2.INTER_LINEAR), dtype='uint8'))  # enlarge
				else:
					normImages.append(np.array(cv2.resize(images[i].copy(), (meanSize1, meanSize2),
						                          interpolation=cv2.INTER_AREA), dtype='uint8'))  # shrink
				rospy.loginfo('Resizing of images successful')
		except Exception as e:
			rospy.logwarn('Failed to normalize/resize dataset: '+str(e))
		return normImages
