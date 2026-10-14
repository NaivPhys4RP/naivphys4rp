#!/usr/bin/env python3
import time
import lark
from threading import Thread
import PIL
import cv2
import json
import math
import itertools
import sys
import gi
import actionlib
import numpy as np
import roslib
from difflib import SequenceMatcher

import tf2_ros

roslib.load_manifest('rosprolog')
roslib.load_manifest('naivphys4rp_msgs')
roslib.load_manifest('sensor_msgs')
roslib.load_manifest('unreal_vision_bridge')
roslib.load_manifest('nav_msgs')
roslib.load_manifest('mujoco_msgs')
roslib.load_manifest('tf2_msgs')
roslib.load_manifest('tf2_ros')
roslib.load_manifest('tf2_geometry_msgs')
import rospy
from naivphys4rp_msgs.msg import *
from threading import Lock
from mujoco_msgs.srv import *
from mujoco_msgs.msg import *
from sensor_msgs.msg import *
from tf2_msgs import *
from tf2_ros import *
from unreal_vision_bridge.msg import *
from nav_msgs.msg import *
from pyquaternion import *
from tf2_geometry_msgs import *
import cv_bridge
from cv_bridge import CvBridge

# A class that trans
# late symbols into sensation

class MotorManager():

    def __init__(self):
        self.motor_model="PR2"
        self.motor_joint_topic="/joint_states"
        self.motor_frame_topic="/tf"
        self.motor_joint_tree={}
        self.motor_frame_tree={}
        self.selected_motor_joints=[]
        self.selected_motor_frames=[]
        self.motor_joint_reader=None
        self.motor_frame_reader=None
        self.can_load_motor_joint = False
        self.can_load_motor_frame = False
        self.actual_frame_values=None
        self.actual_joint_values=None
        #A transform for mapping from secondary worlds to the primary world
        self.from_sw_to_pw_transform=TransformStamped()
        self.from_sw_to_pw_transform.transform.translation.x=1.3
        self.from_sw_to_pw_transform.transform.translation.y = 3.4
        self.from_sw_to_pw_transform.transform.translation.z = 0.0
        self.from_sw_to_pw_transform.transform.rotation.x = 0.0
        self.from_sw_to_pw_transform.transform.rotation.y = 0.0
        self.from_sw_to_pw_transform.transform.rotation.z = 1.0*np.sin(-np.pi/10)
        self.from_sw_to_pw_transform.transform.rotation.w = np.cos(-np.pi/10)


class CameraManager():
    def __init__(self):
        self.color_cam_info_topic="/kinect_head/rgb/camera_info"
        self.color_cam_data_topic="/kinect_head/rgb/image_color/compressed"
        self.depth_cam_info_topic="/kinect_head/rgb/camera_info"
        self.depth_cam_data_topic="/kinect_head/depth_registered/image_raw/compressedDepth"
        self.color_cam_hint="compressed"
        self.depth_cam_hint="compressedDepth"
        self.cam_height=480
        self.cam_width=640
        self.cam_model="kinect"
        self.source_frame="/head_mount_kinect_rgb_optical_frame"
        self.destination_frame="/map"



class Imagination():

    def __init__(self, nb_cameras):
        #create all subscribers and publishers

        # set the robot view: Third or First
        self.robot_view=0
        self.app_gui=None
        self.single_view=1
        self.real_image=False
        self.sensor_modality=0
        self.real_motion = False
        self.camera_manager=CameraManager()
        self.motor_manager = MotorManager()
        self.multi_view_spacing=10
        self.Nb_Cameras=nb_cameras
        print ("Creating controllers ...")
        self.cbackf = []
        self.obackf=[]
        self.dbackf=[]
        self.callf=[]
        self.robot_base_joint_name="base_footprint"
        self.index=0
        self.brightness=0.0
        self.contrast=1.0
        self.robot_base_publisher=[]
        self.robot_joint_publisher=[]
        for i in range(self.Nb_Cameras):
            #base motor
            self.robot_base_publisher.append(rospy.Publisher('/set_base_footprint_'+str(i), Odometry, queue_size=10))
            #self.robot_base_subscriber=rospy.Subscriber('/get_base_footprint', Odometry, self.callback)

            #joint motor
            self.robot_joint_publisher.append(rospy.Publisher('/set_joint_states_'+str(i), JointState, queue_size=10))
            #self.robot_joint_subscriber = rospy.Subscriber('/get_joint_states', JointState, self.callback)

        #sensor
        #self.robot_joint_subscriber = rospy.Subscriber('/unreal_vision/camera_info', CameraInfo, self.callback)
        #self.robot_joint_subscriber = rospy.Subscriber('/unreal_vision/image_color', Image, self.callback)
        #self.robot_joint_subscriber = rospy.Subscriber('/unreal_vision/image_depth', Image, self.callback)
        #self.robot_joint_subscriber = rospy.Subscriber('/unreal_vision/image_object', Image, self.callback)
        #self.robot_joint_subscriber = rospy.Subscriber('/unreal_vision/object_color_map', ObjectColorMap, self.callback)

        #object
        self.object_state_publisher = rospy.Publisher('/set_object_states', ObjectState, queue_size=10)
        #self.object_state_subscriber = rospy.Subscriber('/get_object_states', ObjectState, self.callback)

        print("Wating for controller servers ...")
        #rospy.wait_for_service('/unreal/spawn_objects')
        self.object_assertion = rospy.ServiceProxy('/unreal/spawn_objects', SpawnObject)
        #cannot wait for this service (not yet implemented)
        #self.object_deletion = rospy.ServiceProxy('/unreal/destroy_objects', mujoco_msgs/DestroyObject)
        self.initialize_config_variables()
        self.initialize_robot_pose()
        self.initialize_robot_arms()
        self.initialize_robot_head()
        self.initialize_robot_grippers()
        self.initialize_robot_camera()


        print("Creation of controllers successfully terminated ...")

    def camera_resize(self, images, meanSize1, meanSize2):
        #meanSize 1 and 2 are respectively width and height
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
        except:
            rospy.logwarn('Failed to normalize/resize dataset')
        return normImages

    def addieren(self, b):
        return (lambda x: x+b)

    def set_gui(self,gui):
        self.app_gui=gui

    def initialize_real_robot_motor(self):
        self.motor_manager.motor_joint_reader = rospy.Subscriber(self.motor_manager.motor_joint_topic, JointState, self.real_motor_joint_read)
        self.motor_manager.motor_frame_reader = rospy.Subscriber(self.motor_manager.motor_frame_topic, TFMessage, self.real_motor_frame_read)


    def real_motor_joint_read(self, jointState):
        self.motor_manager.actual_joint_values=jointState
        if not self.motor_manager.can_load_motor_joint:
            #populate joint
            for joint in jointState.name:
                self.motor_manager.motor_joint_tree[joint]=joint
            #print('JointState: ',self.motor_manager.motor_joint_tree)
            self.motor_manager.can_load_motor_joint=True
            self.app_gui.actualize_config_motor_joint()
    def real_motor_frame_read(self, tfMessage):
        self.motor_manager.actual_frame_values=tfMessage
        if not self.motor_manager.can_load_motor_frame:
            #populate joint
            for transform in tfMessage.transforms:
                self.motor_manager.motor_frame_tree[transform.child_frame_id]=transform.header.frame_id
            #print('Time Frame: ',self.motor_manager.motor_frame_tree)
            self.motor_manager.can_load_motor_frame=True
            self.app_gui.actualize_config_motor_frame()
    def initialize_real_robot_camera(self):
        self.iheight = rospy.get_param('real_input_height', 480)
        self.iwidth = rospy.get_param('real_input_width', 640)
        self.height = rospy.get_param('real_output_height', 1000)
        self.width = rospy.get_param('real_output_width', 1000)
        self.real_color_hint = rospy.get_param('real_color_hint', self.camera_manager.color_cam_hint)

        # First View
        self.real_topic_color = []
        self.real_color_image = []
        for i in range(1):
            self.real_topic_color.append(rospy.get_param('real_topic_color_name', self.camera_manager.color_cam_data_topic))
            self.real_color_image.append(np.zeros((self.iheight, self.iwidth, 3), dtype="uint8"))
        self.color_hints = {"": Image, "Compressed": CompressedImage, "raw": Image, "Raw": Image,
                            "compressed": CompressedImage}
        if rospy.get_param('videomode', 'local') == 'local':
            self.cvMode = 'bgr8'
        else:
            self.cvMode = 'rgb8'
        self.bridge = CvBridge()

        self.merged_real_color_image = np.zeros((self.iheight, self.iwidth, 3), dtype="uint8")

        self.real_color_image_subscriber = []

        for i in range(1):
            self.real_color_image_subscriber.append(rospy.Subscriber(self.real_topic_color[i], self.color_hints[self.real_color_hint], callback=self.read_real_color_image))


        print("*************************** List of Subscribers ******************", len(self.color_image_subscriber))
        print(self.color_image_subscriber)
        print(self.cbackf)
    def initialize_robot_camera(self):
        self.iheight = rospy.get_param('input_height', 480)
        self.iwidth = rospy.get_param('input_width', 640)
        self.height = rospy.get_param('output_height', 1000)
        self.width = rospy.get_param('output_width', 1000)
        self.color_hint = rospy.get_param('color_hint', "raw")

        # First View
        self.topic_color=[]
        self.topic_object=[]
        self.topic_depth=[]
        self.object_map=[]
        self.color_lock=[]
        self.object_lock = []
        self.depth_lock = []
        self.color_image = []
        self.object_image = []
        self.depth_image = []
        for i in range(self.Nb_Cameras):
            self.topic_color.append(rospy.get_param('topic_color_name', "/unreal_vision"+str(i)+"/image_color"))
            self.topic_object.append(rospy.get_param('topic_object_name', "/unreal_vision"+str(i)+"/image_object"))
            self.topic_depth.append(rospy.get_param('topic_depth_name', "/unreal_vision"+str(i)+"/image_depth"))
            self.object_map.append(rospy.get_param('topic_object_map_name', "/unreal_vision"+str(i)+"/object_color_map"))
            self.color_lock.append(Lock())
            self.depth_lock.append(Lock())
            self.object_lock.append(Lock())
            self.color_image.append(np.zeros((self.iheight, self.iwidth, 3), dtype="uint8"))
            self.object_image.append(np.zeros((self.iheight, self.iwidth, 3), dtype="uint8"))
            self.depth_image.append(np.zeros((self.iheight, self.iwidth, 3), dtype="uint8"))

        self.model = None
        self.color_hints = {"": Image, "Compressed": CompressedImage, "raw": Image, "Raw": Image,
                            "compressed": CompressedImage}
        if rospy.get_param('videomode', 'local') == 'local':
            self.cvMode = 'bgr8'
        else:
            self.cvMode = 'rgb8'
        self.bridge = CvBridge()

        self.merged_color_image = np.zeros((self.iheight, self.iwidth, 3), dtype="uint8")
        self.merged_object_image = np.zeros((self.iheight, self.iwidth, 3), dtype="uint8")
        self.merged_depth_image = np.zeros((self.iheight, self.iwidth, 3), dtype="uint8")

        self.color_image_subscriber = []
        self.object_image_subscriber = []
        self.depth_image_subscriber = []

        for i in range(self.Nb_Cameras):
            self.cbackf.append(self.modified_read_color_image(i))
            self.obackf.append(self.modified_read_object_image(i))
            self.dbackf.append(self.modified_read_depth_image(i))
            self.color_image_subscriber.append( rospy.Subscriber(self.topic_color[i], self.color_hints[self.color_hint],callback= self.cbackf[i]))
            self.object_image_subscriber.append(rospy.Subscriber(self.topic_object[i], self.color_hints[self.color_hint],
                                                             callback= self.obackf[i]))
            self.depth_image_subscriber.append( rospy.Subscriber(self.topic_depth[i], self.color_hints[self.color_hint],
                                                                 callback= self.dbackf[i]))

        print("*************************** List of Subscribers ******************", len(self.color_image_subscriber))
        print(self.color_image_subscriber)
        print(self.cbackf)

    def modified_read_color_image(self,index):
        return (lambda image: self.read_color_image(index, image))

    def modified_read_object_image(self,index):
        return (lambda image: self.read_object_image(index, image))

    def modified_read_depth_image(self,index):
        return (lambda image: self.read_depth_image(index, image))


    def read_color_image(self,index, image):
        image = self.bridge.imgmsg_to_cv2(image, self.cvMode)
       # self.color_lock[index].acquire(blocking=True)
        print("********************* Execution of callback image color *************:", index)
        self.color_image[index][:,:,:] = (self.camera_resize([image], self.iwidth, self.iheight)[0]).copy()
       # self.color_lock[index].release()

    def read_real_color_image(self, image):
        np_arr = np.fromstring(image.data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        print("Helloklklkltttt")
        self.real_color_image[0][:, :, :] = (self.camera_resize([image], self.iwidth, self.iheight)[0]).copy()

    # self.color_lock[index].release()

    def read_object_image(self,index,image):
        image = self.bridge.imgmsg_to_cv2(image, self.cvMode)
        #self.object_lock[index].acquire(blocking=True)
        self.object_image[index][:,:,:] = (self.camera_resize([image], self.iwidth, self.iheight)[0]).copy()
        #self.object_lock[index].release()

    def read_depth_image(self,index,image):
        image = self.bridge.imgmsg_to_cv2(image, '32FC1')
        image=np.ceil((np.array(image)/np.max(image))*255)
        image=np.uint8(image)
        image=cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        print(image.shape)
        #self.depth_lock[index].acquire(blocking=True)
        self.depth_image[index][:,:,:] = (self.camera_resize([image], self.iwidth, self.iheight)[0]).copy()
        #self.depth_lock[index].release()
        """
        self.mutex = mutex.mutex()
        self.mutex.testandset()
        self.mutex.unlock()
        """


        """
        self.mutex = mutex.mutex()
        self.mutex.testandset()
        self.mutex.unlock()
        """

    def initialize_config_variables(self):
        self.step=0.01
        self.steps=0.3
        self.sleep_time=1/120.

    def callback(self, msgs):
        pass

    def initialize_robot_pose(self):
        self.robot_pose = Odometry()
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        self.robot_pose.pose.pose.position.x = 1.14
        self.robot_pose.pose.pose.position.y = 2.61
        self.robot_pose.pose.pose.position.z = 0.0

        self.robot_pose.pose.pose.orientation.x=0
        self.robot_pose.pose.pose.orientation.y = 0
        self.robot_pose.pose.pose.orientation.z = 0
        self.robot_pose.pose.pose.orientation.w = 1
        # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
        # self.robot_pose.twist.twist.angular=0
        # self.robot_pose.twist.twist.linear = 0
        # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
        self.robot_base_upper_bounds = [17.87, 4.44,0.0,0.0,0.0,1.0,+np.Inf]
        self.robot_base_lower_bounds = [0.8,0.5,0.0,0.0,0.0,1.0,-np.Inf]

    def initialize_robot_head(self):
        self.head_tilt = JointState()
        self.head_tilt.name = ['head_tilt_joint']
        self.head_tilt.position = [0]
        self.head_pan=JointState()
        self.head_pan.name=['head_pan_joint']
        self.head_pan.position = [0]
        self.head_upper_bounds = [np.pi / 2, np.pi / 2]
        self.head_lower_bounds = [-np.pi / 2, -np.pi / 2]

    def initialize_robot_grippers(self):

        self.grippers = JointState()
        self.grippers.name = ['l_gripper_l_finger_joint','l_gripper_r_finger_joint','r_gripper_l_finger_joint','r_gripper_r_finger_joint']
        self.grippers.position = [0,0,0,0]
        self.grippers_upper_bounds=[np.pi , np.pi, np.pi, np.pi]
        self.grippers_lower_bounds = [-np.pi, -np.pi, -np.pi, -np.pi]

    def initialize_robot_arms(self):
        self.parkedArms=JointState()
        self.parkedArms.name=['r_shoulder_pan_joint','l_shoulder_pan_joint', 'r_elbow_flex_joint', 'l_elbow_flex_joint',
                              'r_wrist_roll_joint','r_shoulder_lift_joint','r_upper_arm_roll_joint','r_wrist_flex_joint']

        self.arms_upper_bounds = [np.pi , np.pi, np.pi, np.pi,np.pi , np.pi, np.pi, np.pi]
        self.arms_lower_bounds = [-np.pi, -np.pi, -np.pi, -np.pi,-np.pi, -np.pi, -np.pi, -np.pi]

    def park_robot_arms(self, topic=0, parallel=True,progressive=True):
        self.parkedArms.position = [-np.pi/2.0,np.pi/2.0,-np.pi/2.0,-np.pi/2.0,0,0,0,0]
        for i in range(len(self.parkedArms.position)):
            if self.parkedArms.position[i]> self.arms_upper_bounds[i]:
                self.parkedArms.position[i]=self.arms_upper_bounds[i]
                continue
            if self.parkedArms.position[i]< self.arms_lower_bounds[i]:
                self.parkedArms.position[i]=self.arms_lower_bounds[i]
                continue
        list_index=[]
        if parallel:
            list_index=range(self.Nb_Cameras//2)
        else:
            list_index=[topic]

        if not self.real_motion:
            for s in list_index:
                self.robot_joint_publisher[s].publish(self.parkedArms)
        else:
            self.act_from_real_robot()

    def r_wrist_roll_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index=4
        sig=np.sign(-steps)
        steps=np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step*sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step*sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step*sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()

    def r_shoulder_lift_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 5
        sig = np.sign(-steps)
        steps = np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step * sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step * sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step * sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
    def r_upper_arm_roll_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 6
        sig = np.sign(-steps)
        steps = np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step * sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step * sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step * sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
    def r_shoulder_pan_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 0
        sig = np.sign(-steps)
        steps = np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step * sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step * sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step * sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
    def r_elbow_flex_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 2
        sig = np.sign(steps)
        steps = np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step * sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step * sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step * sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)

                else:
                    self.act_from_real_robot()
    def r_wrist_flex_joint(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 7
        sig = np.sign(-steps)
        steps = np.abs(steps)
        if progressive:
            while (steps > 0):
                steps -= step
                if self.parkedArms.position[index] + step * sig < self.arms_lower_bounds[index]:
                    self.parkedArms.position[index] = self.arms_lower_bounds[index]
                else:
                    if self.parkedArms.position[index] + step * sig > self.arms_upper_bounds[index]:
                        self.parkedArms.position[index] = self.arms_upper_bounds[index]
                    else:
                        self.parkedArms.position[index] += step * sig
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras // 2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.parkedArms)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
    def turn_robot_head_up(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        if progressive:
            while (steps > 0):
                steps -= step
                if self.head_tilt.position[0]- step<self.head_lower_bounds[0]:
                    self.head_tilt.position[0]=self.head_lower_bounds[0]
                else:
                    if self.head_tilt.position[0] - step > self.head_upper_bounds[0]:
                        self.head_tilt.position[0] = self.head_upper_bounds[0]
                    else:
                        self.head_tilt.position[0]-= step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.head_tilt)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.head_tilt.position[0] - steps < self.head_lower_bounds[0]:
                self.head_tilt.position[0] = self.head_lower_bounds[0]
            else:
                if self.head_tilt.position[0] - steps > self.head_upper_bounds[0]:
                    self.head_tilt.position[0] = self.head_upper_bounds[0]
                else:
                    self.head_tilt.position[0] -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.head_tilt)
            else:
                self.act_from_real_robot()

    def turn_robot_head_down(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        if progressive:
            while (steps > 0):
                steps -= step
                if self.head_tilt.position[0] + step < self.head_lower_bounds[0]:
                    self.head_tilt.position[0] = self.head_lower_bounds[0]
                else:
                    if self.head_tilt.position[0] + step > self.head_upper_bounds[0]:
                        self.head_tilt.position[0] = self.head_upper_bounds[0]
                    else:
                        self.head_tilt.position[0] += step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.head_tilt)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.head_tilt.position[0] + steps < self.head_lower_bounds[0]:
                self.head_tilt.position[0] = self.head_lower_bounds[0]
            else:
                if self.head_tilt.position[0] + steps > self.head_upper_bounds[0]:
                    self.head_tilt.position[0] = self.head_upper_bounds[0]
                else:
                    self.head_tilt.position[0] += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.head_tilt)
            else:
                self.act_from_real_robot()


    def turn_robot_head_right(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        if progressive:
            while (steps > 0):
                steps -= step
                if self.head_pan.position[0] - step < self.head_lower_bounds[1]:
                    self.head_pan.position[0] = self.head_lower_bounds[1]
                else:
                    if self.head_pan.position[0] - step > self.head_upper_bounds[1]:
                        self.head_pan.position[0] = self.head_upper_bounds[1]
                    else:
                        self.head_pan.position[0] -= step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.head_pan)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.head_pan.position[0] - steps < self.head_lower_bounds[1]:
                self.head_pan.position[0] = self.head_lower_bounds[1]
            else:
                if self.head_pan.position[0] - steps > self.head_upper_bounds[1]:
                    self.head_pan.position[0] = self.head_upper_bounds[1]
                else:
                    self.head_pan.position[0] -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.head_pan)
            else:
                self.act_from_real_robot()

    def turn_robot_head_left(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        if progressive:
            while (steps > 0):
                steps -= step
                if self.head_pan.position[0] + step < self.head_lower_bounds[1]:
                    self.head_pan.position[0] = self.head_lower_bounds[1]
                else:
                    if self.head_pan.position[0] + step > self.head_upper_bounds[1]:
                        self.head_pan.position[0] = self.head_upper_bounds[1]
                    else:
                        self.head_pan.position[0] += step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.head_pan)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.head_pan.position[0] + steps < self.head_lower_bounds[1]:
                self.head_pan.position[0] = self.head_lower_bounds[1]
            else:
                if self.head_pan.position[0] + steps > self.head_upper_bounds[1]:
                    self.head_pan.position[0] = self.head_upper_bounds[1]
                else:
                    self.head_pan.position[0] += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.head_pan)
            else:
                self.act_from_real_robot()


    def act_from_real_robot(self,steps=0.3, step=0.01, topic=0, parallel=True, progressive=True):
        self.turn_from_real_robot_joint()
        #time.sleep(self.sleep_time)
        self.move_from_real_robot_base()
        #time.sleep(self.sleep_time)

    # Move the robot base from real signals
    def move_from_real_robot_base(self, steps=0.3, step=0.01, topic=0, parallel=True, progressive=True):
        if True:#self.robot_base_joint_name in self.motor_manager.selected_motor_frames:
            print('GET THE TRANSFORMS ..............', self.motor_manager.actual_frame_values.transforms)
            for transform in self.motor_manager.actual_frame_values.transforms:
                print('-------------------- FOUND -------------------', transform.child_frame_id,
                      self.robot_base_joint_name)
                if transform.child_frame_id==self.robot_base_joint_name:

                    if parallel:
                        list_index = range(self.Nb_Cameras // 2)
                    else:
                        list_index = [topic]
                    for s in list_index:
                        robot_pose=PoseStamped()
                        robot_pose.header=transform.header
                        robot_pose.pose.position=transform.transform.translation
                        robot_pose.pose.orientation=transform.transform.rotation
                        transformed_robot_pose=do_transform_pose(robot_pose, self.motor_manager.from_sw_to_pw_transform)
                        robot_odom = Odometry()
                        robot_odom.pose.pose=transformed_robot_pose.pose
                        self.robot_base_publisher[s].publish(robot_odom)
                        print('-------------------- FOUND -------------------', transform.child_frame_id, self.robot_base_joint_name)


    # Move the robot joints from real signal
    def turn_from_real_robot_joint(self, steps=0.3, step=0.01, topic=0, parallel=True, progressive=True):
        robot_joint_state=JointState()
        robot_joint_state.header=self.motor_manager.actual_joint_values.header
        robot_joint_state.name=self.motor_manager.selected_motor_joints
        indices=[self.motor_manager.actual_joint_values.name.index(e) for e in self.motor_manager.selected_motor_joints]
        velocity=[self.motor_manager.actual_joint_values.velocity[i] for i in indices]
        effort = [self.motor_manager.actual_joint_values.effort[i] for i in indices]
        position = [self.motor_manager.actual_joint_values.position[i] for i in indices]
        robot_joint_state.position=position
        robot_joint_state.velocity=velocity
        robot_joint_state.effort=effort
        if parallel:
            list_index = range(self.Nb_Cameras // 2)
        else:
            list_index = [topic]
        for s in list_index:
            self.robot_joint_publisher[s].publish(robot_joint_state)
        #time.sleep(self.sleep_time)

    def move_robot_forward(self, steps=0.3, step=0.01, topic=0, parallel=True, progressive=True):
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        if progressive:
            while(steps>0):
                steps-=step
                if self.robot_pose.pose.pose.position.x+step>self.robot_base_upper_bounds[0]:
                    self.robot_pose.pose.pose.position.x=self.robot_base_upper_bounds[0]
                else:
                    if self.robot_pose.pose.pose.position.x + step < self.robot_base_lower_bounds[0]:
                        self.robot_pose.pose.pose.position.x = self.robot_base_lower_bounds[0]
                    else:
                        self.robot_pose.pose.pose.position.x +=step
                #self.robot_pose.pose.pose.position.y = -2.6
                #self.robot_pose.pose.pose.position.z = 0.1
                # self.robot_pose.pose.pose.orientation.x=0
                # self.robot_pose.pose.pose.orientation.y = 0
                # self.robot_pose.pose.pose.orientation.z = 0
                # self.robot_pose.pose.pose.orientation.w = 1
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.robot_pose.pose.pose.position.x + steps > self.robot_base_upper_bounds[0]:
                self.robot_pose.pose.pose.position.x = self.robot_base_upper_bounds[0]
            else:
                if self.robot_pose.pose.pose.position.x + steps < self.robot_base_lower_bounds[0]:
                    self.robot_pose.pose.pose.position.x = self.robot_base_lower_bounds[0]
                else:
                    self.robot_pose.pose.pose.position.x += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def move_robot_backward(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        if progressive:
            while (steps > 0):
                steps -= step
                if self.robot_pose.pose.pose.position.x - step > self.robot_base_upper_bounds[0]:
                    self.robot_pose.pose.pose.position.x = self.robot_base_upper_bounds[0]
                else:
                    if self.robot_pose.pose.pose.position.x - step < self.robot_base_lower_bounds[0]:
                        self.robot_pose.pose.pose.position.x = self.robot_base_lower_bounds[0]
                    else:
                        self.robot_pose.pose.pose.position.x -= step
                # self.robot_pose.pose.pose.position.y = -2.6
                # self.robot_pose.pose.pose.position.z = 0.1
                # self.robot_pose.pose.pose.orientation.x=0
                # self.robot_pose.pose.pose.orientation.y = 0
                # self.robot_pose.pose.pose.orientation.z = 0
                # self.robot_pose.pose.pose.orientation.w = 1
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.robot_pose.pose.pose.position.x - steps > self.robot_base_upper_bounds[0]:
                self.robot_pose.pose.pose.position.x = self.robot_base_upper_bounds[0]
            else:
                if self.robot_pose.pose.pose.position.x - steps < self.robot_base_lower_bounds[0]:
                    self.robot_pose.pose.pose.position.x = self.robot_base_lower_bounds[0]
                else:
                    self.robot_pose.pose.pose.position.x -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def turn_robot_right(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        q=Quaternion(self.robot_pose.pose.pose.orientation.w,self.robot_pose.pose.pose.orientation.x, self.robot_pose.pose.pose.orientation.y,self.robot_pose.pose.pose.orientation.z)
        angle=q.angle
        axis=q.axis
        axis=np.array([0,0,1])
        if progressive:
            while (steps > 0):
                if angle-step>self.robot_base_upper_bounds[6]:
                    angle=self.robot_base_upper_bounds[6]
                else:
                    if angle - step < self.robot_base_lower_bounds[6]:
                        angle = self.robot_base_lower_bounds[6]
                    else:
                        angle-=step
                steps-=step
                p=Quaternion(axis=axis, angle=angle)
                print (axis, angle)
                # self.robot_pose.pose.pose.position.y = -2.6
                # self.robot_pose.pose.pose.position.z = 0.1
                self.robot_pose.pose.pose.orientation.x = p.x
                self.robot_pose.pose.pose.orientation.y = p.y
                self.robot_pose.pose.pose.orientation.z = p.z
                self.robot_pose.pose.pose.orientation.w = p.w
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if angle - steps > self.robot_base_upper_bounds[6]:
                angle = self.robot_base_upper_bounds[6]
            else:
                if angle - steps < self.robot_base_lower_bounds[6]:
                    angle = self.robot_base_lower_bounds[6]
                else:
                    angle -= steps
            p = Quaternion(axis=axis, angle=angle)
            self.robot_pose.pose.pose.orientation.x = p.x
            self.robot_pose.pose.pose.orientation.y = p.y
            self.robot_pose.pose.pose.orientation.z = p.z
            self.robot_pose.pose.pose.orientation.w = p.w
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def turn_robot_left(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        q = Quaternion(self.robot_pose.pose.pose.orientation.w, self.robot_pose.pose.pose.orientation.x,
                       self.robot_pose.pose.pose.orientation.y, self.robot_pose.pose.pose.orientation.z)
        angle = q.angle
        axis = q.axis
        axis = np.array([0, 0, 1])
        if progressive:
            while (steps > 0):
                if angle + step > self.robot_base_upper_bounds[6]:
                    angle = self.robot_base_upper_bounds[6]
                else:
                    if angle + step < self.robot_base_lower_bounds[6]:
                        angle = self.robot_base_lower_bounds[6]
                    else:
                        angle += step
                steps -= step
                p = Quaternion(axis=axis, angle=angle)
                print(axis, angle)
                # self.robot_pose.pose.pose.position.y = -2.6
                # self.robot_pose.pose.pose.position.z = 0.1
                self.robot_pose.pose.pose.orientation.x = p.x
                self.robot_pose.pose.pose.orientation.y = p.y
                self.robot_pose.pose.pose.orientation.z = p.z
                self.robot_pose.pose.pose.orientation.w = p.w
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if angle + steps > self.robot_base_upper_bounds[6]:
                angle = self.robot_base_upper_bounds[6]
            else:
                if angle + steps < self.robot_base_lower_bounds[6]:
                    angle = self.robot_base_lower_bounds[6]
                else:
                    angle += steps
            p = Quaternion(axis=axis, angle=angle)
            self.robot_pose.pose.pose.orientation.x = p.x
            self.robot_pose.pose.pose.orientation.y = p.y
            self.robot_pose.pose.pose.orientation.z = p.z
            self.robot_pose.pose.pose.orientation.w = p.w
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def move_robot_left(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        if progressive:
            while (steps > 0):
                steps -= step
                if self.robot_pose.pose.pose.position.y + step > self.robot_base_upper_bounds[1]:
                    self.robot_pose.pose.pose.position.y = self.robot_base_upper_bounds[1]
                else:
                    if self.robot_pose.pose.pose.position.y + step < self.robot_base_lower_bounds[1]:
                        self.robot_pose.pose.pose.position.y = self.robot_base_lower_bounds[1]
                    else:
                        self.robot_pose.pose.pose.position.y += step
                # self.robot_pose.pose.pose.position.y = -2.6
                # self.robot_pose.pose.pose.position.z = 0.1
                # self.robot_pose.pose.pose.orientation.x=0
                # self.robot_pose.pose.pose.orientation.y = 0
                # self.robot_pose.pose.pose.orientation.z = 0
                # self.robot_pose.pose.pose.orientation.w = 1
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.robot_pose.pose.pose.position.y + steps > self.robot_base_upper_bounds[1]:
                self.robot_pose.pose.pose.position.y = self.robot_base_upper_bounds[1]
            else:
                if self.robot_pose.pose.pose.position.y + steps < self.robot_base_lower_bounds[1]:
                    self.robot_pose.pose.pose.position.y = self.robot_base_lower_bounds[1]
                else:
                    self.robot_pose.pose.pose.position.y += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def move_robot_right(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        # self.robot_pose.header.seq=0
        # self.robot_pose.header.stamp=0
        # self.robot_pose.header.frame_id=self.robot_base_joint_name
        # self.robot_pose.child_frame_id=self.robot_base_joint_name
        if progressive:
            while (steps > 0):
                steps -= step
                if self.robot_pose.pose.pose.position.y - step > self.robot_base_upper_bounds[1]:
                    self.robot_pose.pose.pose.position.y = self.robot_base_upper_bounds[1]
                else:
                    if self.robot_pose.pose.pose.position.y - step < self.robot_base_lower_bounds[1]:
                        self.robot_pose.pose.pose.position.y = self.robot_base_lower_bounds[1]
                    else:
                        self.robot_pose.pose.pose.position.y -= step
                # self.robot_pose.pose.pose.position.y = -2.6
                # self.robot_pose.pose.pose.position.z = 0.1
                # self.robot_pose.pose.pose.orientation.x=0
                # self.robot_pose.pose.pose.orientation.y = 0
                # self.robot_pose.pose.pose.orientation.z = 0
                # self.robot_pose.pose.pose.orientation.w = 1
                # self.robot_pose.pose.covariance=np.identity(36, dtype='float64')
                # self.robot_pose.twist.twist.angular=0
                # self.robot_pose.twist.twist.linear = 0
                # self.robot_pose.twist.covariance=np.identity(36, dtype='float64')
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_base_publisher[s].publish(self.robot_pose)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.robot_pose.pose.pose.position.y - steps > self.robot_base_upper_bounds[1]:
                self.robot_pose.pose.pose.position.y = self.robot_base_upper_bounds[1]
            else:
                if self.robot_pose.pose.pose.position.y - steps < self.robot_base_lower_bounds[1]:
                    self.robot_pose.pose.pose.position.y = self.robot_base_lower_bounds[1]
                else:
                    self.robot_pose.pose.pose.position.y -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_base_publisher[s].publish(self.robot_pose)
            else:
                self.act_from_real_robot()

    def close_robot_right_gripper(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index=2
        if progressive:
            while (steps > 0):
                steps -= step
                if self.grippers.position[index]-step<self.grippers_lower_bounds[index]:
                    self.grippers.position[index] = self.grippers_lower_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
                else:
                    if self.grippers.position[index] - step > self.grippers_upper_bounds[index]:
                        self.grippers.position[index] = self.grippers_upper_bounds[index]
                        self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                    else:
                        self.grippers.position[index] -= step
                        self.grippers.position[index+1] -= step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.grippers)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.grippers.position[index] - steps < self.grippers_lower_bounds[index]:
                self.grippers.position[index] = self.grippers_lower_bounds[index]
                self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
            else:
                if self.grippers.position[index] - steps > self.grippers_upper_bounds[index]:
                    self.grippers.position[index] = self.grippers_upper_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                else:
                    self.grippers.position[index] -= steps
                    self.grippers.position[index + 1] -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.grippers)
            else:
                self.act_from_real_robot()

    def close_robot_left_gripper(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 0
        if progressive:
            while (steps > 0):
                steps -= step
                if self.grippers.position[index] - step < self.grippers_lower_bounds[index]:
                    self.grippers.position[index] = self.grippers_lower_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
                else:
                    if self.grippers.position[index] - step > self.grippers_upper_bounds[index]:
                        self.grippers.position[index] = self.grippers_upper_bounds[index]
                        self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                    else:
                        self.grippers.position[index] -= step
                        self.grippers.position[index + 1] -= step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.grippers)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.grippers.position[index] - steps < self.grippers_lower_bounds[index]:
                self.grippers.position[index] = self.grippers_lower_bounds[index]
                self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
            else:
                if self.grippers.position[index] - steps > self.grippers_upper_bounds[index]:
                    self.grippers.position[index] = self.grippers_upper_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                else:
                    self.grippers.position[index] -= steps
                    self.grippers.position[index + 1] -= steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.grippers)
            else:
                self.act_from_real_robot()

    def open_robot_left_gripper(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 0
        if progressive:
            while (steps > 0):
                steps -= step
                if self.grippers.position[index] + step < self.grippers_lower_bounds[index]:
                    self.grippers.position[index] = self.grippers_lower_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
                else:
                    if self.grippers.position[index] + step > self.grippers_upper_bounds[index]:
                        self.grippers.position[index] = self.grippers_upper_bounds[index]
                        self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                    else:
                        self.grippers.position[index] += step
                        self.grippers.position[index + 1] += step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.grippers)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.grippers.position[index] + steps < self.grippers_lower_bounds[index]:
                self.grippers.position[index] = self.grippers_lower_bounds[index]
                self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
            else:
                if self.grippers.position[index] + steps > self.grippers_upper_bounds[index]:
                    self.grippers.position[index] = self.grippers_upper_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                else:
                    self.grippers.position[index] += steps
                    self.grippers.position[index + 1] += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.grippers)
            else:
                self.act_from_real_robot()

    def open_robot_right_gripper(self, steps=0.3, step=0.01, topic=0, parallel=True,progressive=True):
        index = 2
        if progressive:
            while (steps > 0):
                steps -= step
                if self.grippers.position[index] + step < self.grippers_lower_bounds[index]:
                    self.grippers.position[index] = self.grippers_lower_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
                else:
                    if self.grippers.position[index] + step > self.grippers_upper_bounds[index]:
                        self.grippers.position[index] = self.grippers_upper_bounds[index]
                        self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                    else:
                        self.grippers.position[index] += step
                        self.grippers.position[index + 1] += step
                list_index = []
                if parallel:
                    list_index = range(self.Nb_Cameras//2)
                else:
                    list_index = [topic]
                if not self.real_motion:
                    for s in list_index:
                        self.robot_joint_publisher[s].publish(self.grippers)
                    time.sleep(self.sleep_time)
                else:
                    self.act_from_real_robot()
        else:
            if self.grippers.position[index] + steps < self.grippers_lower_bounds[index]:
                self.grippers.position[index] = self.grippers_lower_bounds[index]
                self.grippers.position[index + 1] = self.grippers_lower_bounds[index]
            else:
                if self.grippers.position[index] + steps > self.grippers_upper_bounds[index]:
                    self.grippers.position[index] = self.grippers_upper_bounds[index]
                    self.grippers.position[index + 1] = self.grippers_upper_bounds[index]
                else:
                    self.grippers.position[index] += steps
                    self.grippers.position[index + 1] += steps
            list_index = []
            if parallel:
                list_index = range(self.Nb_Cameras//2)
            else:
                list_index = [topic]
            if not self.real_motion:
                for s in list_index:
                    self.robot_joint_publisher[s].publish(self.grippers)
            else:
                self.act_from_real_robot()

    def observe(self):
        if self.robot_view==1:
            print("-------------- THE SUMS -----------------------", np.sum(self.color_image[0]), np.sum(self.object_image[0]), np.sum(self.depth_image[0]))
            return [self.color_image[0], self.object_image[0], self.depth_image[0]]
        else:
            print("-------------- THE SUMS -----------------------", np.sum(self.color_image[1]),
                  np.sum(self.object_image[1]), np.sum(self.depth_image[1]))
            return [self.color_image[1], self.object_image[1], self.depth_image[1]]

    def getSquareNumber(self, n):
        return int(np.ceil(np.sqrt(n)))

    def merged_observe(self):
        if self.real_image:
            self.merged_real_color_image = np.array(self.real_color_image[0], dtype="float")
            self.merged_real_color_image = np.clip(self.contrast * self.merged_real_color_image + self.brightness, 0.0, 255.0)
            self.merged_real_color_image = np.array(self.merged_real_color_image, dtype="uint8")
            return [self.merged_real_color_image, None, None]
        else:
            if self.single_view:
                color_image = np.zeros((self.iheight, self.iwidth, 3), dtype="float")
                depth_image = np.zeros((self.iheight, self.iwidth, 3), dtype="float")
                object_image = np.zeros((self.iheight, self.iwidth, 3), dtype="float")
                if self.robot_view == 1:
                    i=1
                else:
                    i=0
                while(i<self.Nb_Cameras):
                    color_image=color_image+np.array(self.color_image[i], dtype="float")
                    depth_image = depth_image + np.array(self.depth_image[i], dtype="float")
                    object_image = object_image + np.array(self.object_image[i], dtype="float")
                    i+=2

                if self.sensor_modality==1:
                    color_image=object_image.copy()
                else:
                    if self.sensor_modality==2:
                        color_image=depth_image.copy()
                self.merged_color_image = np.array(color_image * 2 / self.Nb_Cameras, dtype="float")

                self.merged_color_image = np.clip(self.contrast * self.merged_color_image + self.brightness, 0.0, 255.0)

                self.merged_color_image = np.array(self.merged_color_image, dtype="uint8")
                self.merged_object_image = np.array(object_image * 2 / self.Nb_Cameras, dtype="uint8")
                self.merged_depth_image = np.array(depth_image * 2 / self.Nb_Cameras, dtype="uint8")
                #return [self.merged_color_image, self.merged_object_image, self.merged_depth_image]
            else:
                N=self.getSquareNumber(self.Nb_Cameras//2)
                if self.robot_view == 1:
                    i = 1
                else:
                    i = 0
                self.merged_color_image=np.ones((N*(self.iheight+self.multi_view_spacing),N*(self.iwidth+self.multi_view_spacing),3),dtype="uint8")*255
                for row in range(N):
                    for col in range(N):
                        row1=row*(self.iheight+self.multi_view_spacing)
                        row2=(row+1)*(self.iheight+self.multi_view_spacing)-self.multi_view_spacing
                        col1 = col * (self.iwidth + self.multi_view_spacing)
                        col2 = (col + 1) * (self.iwidth + self.multi_view_spacing) - self.multi_view_spacing
                        if ((row*N+col)*2+i)>=self.Nb_Cameras:
                            break
                        else:
                            if self.sensor_modality==0:
                                self.merged_color_image[row1:row2,col1:col2,:]=np.array(np.clip(self.contrast * np.array(self.color_image[(row*N+col)*2+i],dtype="float")+ self.brightness, 0.0, 255.0),dtype="uint8")
                            else:
                                if self.sensor_modality==1:
                                    self.merged_color_image[row1:row2, col1:col2, :] = np.array(np.clip(
                                        self.contrast * np.array(self.object_image[(row * N + col) * 2 + i],
                                                                 dtype="float") + self.brightness, 0.0, 255.0),
                                                                                                dtype="uint8")
                                else:
                                    self.merged_color_image[row1:row2, col1:col2, :] = np.array(np.clip(
                                        self.contrast * np.array(self.depth_image[(row * N + col) * 2 + i],
                                                                 dtype="float") + self.brightness, 0.0, 255.0),
                                                                                                dtype="uint8")

            return [self.merged_color_image, None, None]
