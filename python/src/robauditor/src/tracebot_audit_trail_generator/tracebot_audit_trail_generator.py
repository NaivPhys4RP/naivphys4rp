#!/usr/bin/env python3

import actionlib
import rospkg
import roslib
roslib.load_manifest('rosprolog')
roslib.load_manifest('tracebot_msgs')
import rospy
import time
from datetime import datetime, timedelta
try:
	from rosprolog.rosprolog_client import PrologException, Prolog
except Exception as e:
	from rosprolog_client import PrologException, Prolog 
	print('Loading rosprolog ...')
from tracebot_msgs.msg import *
import numpy as np
import os
import cv2
from pathlib import Path
from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import SingleColumnLayout
from decimal import Decimal
from borb.pdf import Image
from borb.pdf import FlexibleColumnWidthTable as Table
from borb.pdf import FixedColumnWidthTable as FTable
from borb.pdf import Paragraph
from borb.pdf import Alignment
from datetime import datetime
from borb.pdf import PDF
from borb.pdf.page.page_size import PageSize
import random
from borb.pdf import HexColor
from borb.pdf import TableCell
from borb.pdf import X11Color
import re
import functools


class AuditTrailFormat():

	def __init__(self, path_name, audit_trail_dict):
		self.path_name=path_name
		self.audit_trail_dict=audit_trail_dict
		#Adding font information to audit trail export format

		self.audit_trail_dict["Fcolor"]="FFFFFF"
		self.audit_trail_dict["Bcolor"]="203864"
		self.audit_trail_dict["Fcolor_Successful"]="00FF00"
		self.audit_trail_dict["Fcolor_Failed"]="FF0000"
		self.audit_trail_dict["Fcolor_Interrupted"]="FF7700"
		self.audit_trail_dict["Fcolor_Pending"]="666666"
		self.audit_trail_dict['C_Degradation_scale']="0.1"	
		self.audit_trail_dict['C_step']=100
		self.audit_trail_dict['Header_Length']=self.audit_trail_dict['Header_Length']+7


	#############################################################################################################################################################
	def compare_action_timeslot(self, action1, action2):
		if self.audit_trail_dict[action1]['Action_Duration'][0]<self.audit_trail_dict[action2]['Action_Duration'][0]:
			return 1
		else:
			if self.audit_trail_dict[action1]['Action_Duration'][0]>self.audit_trail_dict[action2]['Action_Duration'][0]:
				return -1
			else:
				return 0 
	#############################################################################################################################################################
	def action_name_from_url(self, url):
		bname=url.split('#').pop()
		iname=re.findall('[A-Z][^A-Z]*', bname)
		fname=""
		for i in range(len(iname)):
			fname+=iname[i]+" "
		return fname
	
	#############################################################################################################################################################
	def rgb_hexTodec(self, col):
		return [int(col[:2],16), int(col[2:4],16), int(col[4:6],16)]

	#############################################################################################################################################################
	def rgb_decTohex(self, col):
		return ('0'*(2-len(hex(col[0])[2:]))+hex(col[0])[2:]+'0'*(2-len(hex(col[1])[2:]))+hex(col[1])[2:]+'0'*(2-len(hex(col[2])[2:]))+hex(col[2])[2:]).upper()

	#############################################################################################################################################################
	#Filling audit trail header / summary
	def build_audit_trail_header(self):    
		header = Table(number_of_rows=4, number_of_columns=3)
		title=self.audit_trail_dict['Episode_Title'].title()
		status=self.audit_trail_dict['Episode_Status']
		if 'failed' in status.lower():
			status='Failed'
		else:
			if 'succeed' in status.lower():
				status='Successful'
			else:
				status='Interrupted'
		start_time, end_time=self.audit_trail_dict['Episode_Duration']
		start_time, end_time=(datetime.fromisoformat(start_time), datetime.fromisoformat(end_time))
		header.add(Paragraph("Episode",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))    
		header.add(Paragraph(":",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))  
		header.add(Paragraph(title, horizontal_alignment=Alignment.LEFT,font_size=Decimal(16))) 

		header.add(Paragraph("Duration",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))    
		header.add(Paragraph(":",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))    
		header.add(Paragraph("%02d.%02d.%02d, %02d:%02d:%02d - %02d.%02d.%02d, %02d:%02d:%02d" % (start_time.day, start_time.month, start_time.year,start_time.hour,start_time.minute,start_time.second,end_time.day, end_time.month, end_time.year,end_time.hour,end_time.minute,end_time.second),horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))

		header.add(Paragraph("Status",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16),font_color=HexColor("2F5597")))    
		header.add(Paragraph(":",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16))) 
		if status=='Failed':	
			header.add(Paragraph("--[Failed]-- / Successful / Interrupted / Pending",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16),font_color=HexColor(self.audit_trail_dict["Fcolor_Failed"])))
		else:
			if status=='Successful':	
				header.add(Paragraph("Failed / --[Successful]-- / Interrupted / Pending",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16),font_color=HexColor("395625")))
			else:
				header.add(Paragraph("Failed / Successful / --[Interrupted]-- / Pending",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16),font_color=HexColor(self.audit_trail_dict["Fcolor_Interrupted"])))
		
		header.add(Paragraph("Confidence",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))    
		header.add(Paragraph(":",font="Helvetica-Bold", horizontal_alignment=Alignment.LEFT,font_size=Decimal(16)))  
		header.add(Paragraph(str(self.audit_trail_dict[self.audit_trail_dict["Root_Action_ID"]]['Confidence'])+'%', font="Helvetica-Bold",horizontal_alignment=Alignment.LEFT,font_size=Decimal(16))) 

		header.set_padding_on_all_cells(Decimal(5), Decimal(5), Decimal(5), Decimal(5))    		
		header.no_borders()
		return header
	
	#############################################################################################################################################################
	    
	#Filling detailed content of audit trail
	
	def build_audit_trail_content(self):    
	   
	    	# create content table
		nb_rows=len(self.audit_trail_dict.keys())-self.audit_trail_dict['Header_Length']+1
		nb_cols=8
		content = FTable(number_of_rows=1, number_of_columns=9)
		#content.set_padding_on_all_cells(Decimal(3), Decimal(3), Decimal(3), Decimal(3))
		try:
			
			# First row
			content.add(TableCell(Paragraph("Action Designator",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Executive Module",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))	

			content.add(TableCell(Paragraph("Participants",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Execution Timeslot",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Status",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Confidence Level",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Verbal Explanation",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))

			content.add(TableCell(Paragraph("Non-verbal Explanation",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))
			
			content.add(TableCell(Paragraph("Recovery Explanation",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor("FFFFFF")),background_color=HexColor("000000")))
			
			self.page_layout.add(content)
			#Add empty paragraph for spacing  
			#self.page_layout.add(Paragraph(""))
			
		except Exception as e:
			print(str(e)+': Creating a new page for table')
			# Create page
			self.page =  Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])
			#Add page to document
			self.pdf.add_page(self.page)
			#Create Layout
			#Set number of columns
			self.page_layout = SingleColumnLayout(self.page)
			#Set margin size
			self.page_layout.vertical_margin = Decimal(0)
			self.page_layout.add(content)
			#Add empty paragraph for spacing  
			#self.page_layout.add(Paragraph(""))
																							
																								
		#Initialize second row																				
		ListAction=[self.audit_trail_dict["Root_Action_ID"]]
		#initialize first action
		self.audit_trail_dict[ListAction[0]]['Fcolor']="FFFFFF"
		self.audit_trail_dict[ListAction[0]]['Bcolor']="203864"
		self.audit_trail_dict[ListAction[0]]['Index']=""
		self.audit_trail_dict[ListAction[0]]['Child_Index']="-1"
		self.audit_trail_dict[ListAction[0]]['Cscale']="1.0"
		
		count=0
		while ListAction!=[]:
			content = FTable(number_of_rows=1, number_of_columns=9)
			content.set_padding_on_all_cells(Decimal(0), Decimal(0), Decimal(0), Decimal(0))
			try:
				count+=1
				#if count>=2:
				#	break
				RootAction=ListAction.pop()
				self.audit_trail_dict[RootAction]['List_SubActions'].sort(key=functools.cmp_to_key(self.compare_action_timeslot))
				ListAction+=self.audit_trail_dict[RootAction]['List_SubActions']
				ParentAction=self.audit_trail_dict[RootAction]['SuperAction']
				index=self.audit_trail_dict[ParentAction]['Child_Index']
				index=int(index)+1
				if int(index)<=0:
					self.audit_trail_dict[RootAction]['Index']=self.audit_trail_dict[ParentAction]['Index']
				else:
					self.audit_trail_dict[RootAction]['Index']=self.audit_trail_dict[ParentAction]['Index']+str(index)+str(".")
					
				self.audit_trail_dict[ParentAction]['Child_Index']=str(index)
				self.audit_trail_dict[RootAction]['Child_Index']=str(0)
				
				index=self.audit_trail_dict[RootAction]['Index']
				
				fcolor=self.audit_trail_dict[ParentAction]['Fcolor']
				bcolor=self.audit_trail_dict[ParentAction]['Bcolor']
				
				ifcolor=self.rgb_hexTodec(fcolor)
				ibcolor=self.rgb_hexTodec(bcolor)
				s=self.audit_trail_dict['C_step']*(count>1)
				ibcolor=[min(ibcolor[0]+s,255),min(ibcolor[1]+s,255),min(ibcolor[2]+s,255)]
				#print(ibcolor)
				
				ffcolor=list(np.array(np.round(np.array(ifcolor, dtype='float')*float(self.audit_trail_dict[ParentAction]['Cscale'])), dtype='int'))
				fbcolor=list(np.array(np.round(np.array(ibcolor, dtype='float')), dtype='int'))
				
				
				hfcolor=self.rgb_decTohex(ffcolor)
				hbcolor=self.rgb_decTohex(fbcolor)
				
				self.audit_trail_dict[RootAction]['Fcolor']=hfcolor
				self.audit_trail_dict[RootAction]['Bcolor']=hbcolor
				
				self.audit_trail_dict[RootAction]['Cscale']=float(self.audit_trail_dict[ParentAction]['Cscale'])*float(self.audit_trail_dict['C_Degradation_scale'])
				
				action_name=self.action_name_from_url(self.audit_trail_dict[RootAction]['Task_Designator'])
				print("ACTION NAME: ", action_name)
				
				# adding action designator
				content.add(TableCell(Paragraph(index+" "+action_name, horizontal_alignment=Alignment.LEFT,font_size=Decimal(8),font_color=HexColor(hfcolor)),   
					background_color=HexColor(hbcolor)))
				
				#adding the executive module
				participants=' ; '.join(self.audit_trail_dict[RootAction]['Participants']).rstrip().lstrip()
				if participants=='':
					content.add(TableCell(Paragraph("could not be infered", horizontal_alignment=Alignment.LEFT,font_size=Decimal(7),font="Helvetica-Oblique", 
					font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				else:
					content.add(TableCell(Paragraph(participants, horizontal_alignment=Alignment.LEFT,font_size=Decimal(7),font="Helvetica-Oblique", 
					font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
					
					
				#agent=self.action_name_from_url(self.audit_trail_dict[RootAction]['Agent_ID'])
				participants=self.audit_trail_dict[RootAction]['Participant'].replace('_', ' ')
				agent='could not be inferred'
				try:
					agent=self.audit_trail_dict[RootAction]['Agent_ID'].split('#').pop()
				except Exception as e:
					print('Warning: issue retrieving action participants - '+str(e))
				self.audit_trail_dict[RootAction]['Participants']=[agent]
				if participants=='':
					content.add(TableCell(Paragraph(agent, horizontal_alignment=Alignment.LEFT,font_size=Decimal(8),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				else:
					content.add(TableCell(Paragraph(participants, horizontal_alignment=Alignment.LEFT,font_size=Decimal(5),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				#adding duration
				start_time, end_time=self.audit_trail_dict[RootAction]['Action_Duration']
				start_time, end_time=(datetime.fromisoformat(start_time), datetime.fromisoformat(end_time))
				content.add(TableCell(Paragraph("%02d.%02d.%02d, %02d:%02d:%02d - %02d.%02d.%02d, %02d:%02d:%02d" % (start_time.day, start_time.month, 		
					start_time.year,start_time.hour,start_time.minute,start_time.second,end_time.day, end_time.month, 
					end_time.year,end_time.hour,end_time.minute,end_time.second),horizontal_alignment=Alignment.LEFT,font_size=Decimal(7), 		
					font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				
				#adding status
				status=self.audit_trail_dict[RootAction]['Status']
				if 'failed' in status.lower():
					sfcolor=self.audit_trail_dict['Fcolor_Failed']
					status='Failed'
				else:
					if 'succeed' in status.lower():
						sfcolor=self.audit_trail_dict['Fcolor_Successful']
						status='Successful'
					else:
						sfcolor=self.audit_trail_dict['Fcolor_Interrupted']
						status='Interrupted'
						
				content.add(TableCell(Paragraph(status, horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font="Helvetica-Bold",font_color=HexColor(sfcolor)), 
					background_color=HexColor(hbcolor)))
				
				#adding confidence
				confidence=str(self.audit_trail_dict[RootAction]['Confidence'])+"%"
				content.add(TableCell(Paragraph(confidence, horizontal_alignment=Alignment.CENTERED,font_size=Decimal(8),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				
				#adding status justification
				if self.audit_trail_dict[RootAction]['List_SubActions']==[]:
					if self.audit_trail_dict[RootAction]['Verbal_Explanation']=='':
						self.audit_trail_dict[RootAction]['Verbal_Explanation']='Yet to be resolved'
					content.add(TableCell(Paragraph(self.audit_trail_dict[RootAction]['Verbal_Explanation'], horizontal_alignment=Alignment.CENTERED,font="Helvetica-Oblique", 
						font_size=Decimal(6),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				else:
					if status=='Successful':
						self.audit_trail_dict[RootAction]['Verbal_Explanation']=""+self.audit_trail_dict[RootAction]['Verbal_Explanation']
						content.add(TableCell(Paragraph(self.audit_trail_dict[RootAction]['Verbal_Explanation'], 
							horizontal_alignment=Alignment.CENTERED,font="Helvetica-Oblique", font_size=Decimal(6),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
					else:
						if status=='Failed':
							self.audit_trail_dict[RootAction]['Verbal_Explanation']=""+self.audit_trail_dict[RootAction]['Verbal_Explanation']
							content.add(TableCell(Paragraph(self.audit_trail_dict[RootAction]['Verbal_Explanation'], 
							horizontal_alignment=Alignment.CENTERED,font="Helvetica-Oblique", font_size=Decimal(6),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
						else:
							self.audit_trail_dict[RootAction]['Verbal_Explanation']="The action has been interrupted"
							content.add(TableCell(Paragraph(self.audit_trail_dict[RootAction]['Verbal_Explanation'], 
							horizontal_alignment=Alignment.CENTERED,font="Helvetica-Oblique", font_size=Decimal(6),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				
				# adding non verbal explanation
				expected_height=480
				expected_width=640
				try:
					shape=cv2.imread(self.audit_trail_dict[RootAction]['Non_Verbal_Explanation']).shape
					expected_height=shape[0]
					expected_width=shape[1]
				except Exception as e:
					print('Failure while reading non verbal explanation: '+str(e))
				expected_height=50*expected_height/480
				expected_width=67*expected_width/640
				content.add(TableCell( Image(        
				image=Path(self.audit_trail_dict[RootAction]['Non_Verbal_Explanation']),        
				width=Decimal(expected_width),        
				height=Decimal(expected_height), 
				horizontal_alignment=Alignment.CENTERED   
				),background_color=HexColor(hbcolor)))
				# adding recovery explanation
				recovery_message=self.audit_trail_dict[RootAction]['Recovery_Explanation']
				if recovery_message=='Not yet resolved':
					if 'failed' in self.audit_trail_dict[RootAction]['Status'].lower():
						recovery_message='The agent should recover from this failure.'
					else:
						recovery_message='Nothing to recover'
				content.add(TableCell(Paragraph(recovery_message, horizontal_alignment=Alignment.CENTERED,font="Helvetica-Oblique", 
						font_size=Decimal(6),font_color=HexColor(hfcolor)),background_color=HexColor(hbcolor)))
				self.page_layout.add(content)
				#Add empty paragraph for spacing  
				#self.page_layout.add(Paragraph(" "))
			except Exception as e:
				print(str(e)+': Creating a new page for table')
				# Create page
				self.page =  Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])
				#Add page to document
				self.pdf.add_page(self.page)
				#Create Layout
				#Set number of columns
				self.page_layout = SingleColumnLayout(self.page)
				#Set margin size
				self.page_layout.vertical_margin = Decimal(0)
				self.page_layout.add(content)
				#Add empty paragraph for spacing  
				#self.page_layout.add(Paragraph(" "))
	    
		print('NB ROWS: ', count)
		 
		return True

	def buid_audit_trail(self):
		print("Generating audit trail ...")

		# Create document
		self.pdf = Document()

		# Create page
		self.page =  Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])

		#Add page to document
		self.pdf.add_page(self.page)

		#Create Layout
		#Set number of columns
		self.page_layout = SingleColumnLayout(self.page)
		#Set margin size
		self.page_layout.vertical_margin = Decimal(0)
		#Adding image to page
		self.page_layout.add(    
			Image(        
			image=Path(os.path.join(rospkg.RosPack().get_path('tracebot-knowrob'), 'resources', 'TraceBot.png')),        
			width=Decimal(170),        
			height=Decimal(60), 
			horizontal_alignment=Alignment.CENTERED   
			))

		#Add title
		self.page_layout.add(Paragraph("(End-User) Auto-Generated Audit Trail",font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED,font_color=HexColor("395625"),font_size=Decimal(24)))

		#Add empty paragraph for spacing  
		#self.page_layout.add(Paragraph(" "))

		#Add summary information to page 
		self.page_layout.add(self.build_audit_trail_header())

		#Add empty paragraph for spacing  
		#self.page_layout.add(Paragraph(" "))

		
		#Add detailed information to page
		self.build_audit_trail_content()
			

		#Writing the pdf document in hard file
		with open(self.path_name, "wb") as pdf_file_handle:
			PDF.dumps(pdf_file_handle, self.pdf)
		print("Audit trail successfully generated !!!")
		return self.audit_trail_dict


