#!/usr/bin/env python3
import time
import lark
import PyKDL
from threading import *
from datetime import datetime as dt
from random import shuffle
import PIL
import cv2
import json
import math
import random
import itertools
import sys
import gi
import actionlib
import roslib
from difflib import SequenceMatcher

import vedo
import os
import threading
import time
import queue

roslib.load_manifest('rosprolog')
roslib.load_manifest('naivphys4rp_msgs')
import rospy
from rosprolog_client import PrologException, Prolog
from naivphys4rp_msgs.msg import *

gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from pyvis.network import Network
import networkx as nx

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk, Pango, Gdk, GdkPixbuf

import cairo
import numpy as np
from graph_tool.all import *
import sys

sys.path.append("../imagination")
sys.path.append("../filtering")
from imagination import *
from filtering import *

# This would typically be its own file
MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <attribute name="label" translatable="yes">Change label</attribute>
      <item>
        <attribute name="action">win.change_label</attribute>
        <attribute name="target">String 1</attribute>
        <attribute name="label" translatable="yes">String 1</attribute>
      </item>
      <item>
        <attribute name="action">win.change_label</attribute>
        <attribute name="target">String 2</attribute>
        <attribute name="label" translatable="yes">String 2</attribute>
      </item>
      <item>
        <attribute name="action">win.change_label</attribute>
        <attribute name="target">String 3</attribute>
        <attribute name="label" translatable="yes">String 3</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="action">win.maximize</attribute>
        <attribute name="label" translatable="yes">Maximize</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""

THREAD_KILLABLE = False  # global variable
THREAD_RUN_BELIEF_KILLABLE=False
THREAD_RUN_FILTERING_KILLABLE=False
RUN_GRASPING=False

class StoppableThread(Thread):
    """ A Thread that can be stopped """

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()
        self.kill = False

    def stop(self):
        self.skill = True
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class ImaginationAreaFrame(Gtk.Frame):
    def __init__(self, css=None, border_width=0):
        super().__init__()
        self.set_border_width(border_width)
        self.set_size_request(100, 100)
        self.vexpand = True
        self.hexpand = True
        self.surface = None
        self.min_index = -1
        self.area = Gtk.DrawingArea()
        self.add(self.area)
        self.imagination = None

        self.init_surface(self.area)
        self.area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.area.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.area.connect('button-press-event', self.on_press)
        self.area.connect('button-release-event', self.on_press)
        self.area.connect('motion-notify-event', self.on_press)
        self.area.connect("draw", self.on_draw)
        self.area.connect('configure-event', self.on_configure)

    def imagine(self, images):
        self.imagination = images

    def forget(self):
        if self.imagination is not None:
            del self.imagination
            self.imagination = None

    def set_nearest_vertex(self, x, y, delta=30.0):
        pass

    def on_release(self):
        pass

    def on_press(self, widget, event):
        pass

    def init_surface(self, area):
        # Destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.area.get_allocated_width(),
                                          self.area.get_allocated_width())

    def redraw(self):
        self.init_surface(self.area)
        context = cairo.Context(self.surface)
        context.scale(self.surface.get_width(), self.surface.get_height())
        self.do_drawing(context)
        self.surface.flush()

    def on_configure(self, area, event, data=None):
        self.redraw()
        return False

    def on_draw(self, area, context):
        if self.surface is not None:
            context.set_source_surface(self.surface, 0.0, 0.0)
            context.paint()
        else:
            print('Invalid surface')
        return False

    def draw_image(self, ctx):
        if self.imagination is None:
            ctx.rectangle(0.0, 0, 1.0, 1.0)
            ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ctx.fill()
        else:
            img_arr=None
            if((self.imagination[1] is not None) and (self.imagination[2] is not None)):
                x_space = 5
                x_dim = self.imagination[0].shape[1] + x_space + self.imagination[1].shape[1] + x_space + \
                        self.imagination[2].shape[1]
                y_dim = max(self.imagination[0].shape[0], self.imagination[1].shape[0], self.imagination[2].shape[0])
                z_dim = max(self.imagination[0].shape[2], self.imagination[1].shape[2], self.imagination[2].shape[2], 4)
                img_arr = np.ones([y_dim, x_dim, z_dim], dtype="uint8") * 255
                for l in range(3):
                    img_arr[:self.imagination[0].shape[0], :self.imagination[0].shape[1], l] = self.imagination[0][:, :, l]
                    img_arr[:self.imagination[1].shape[0],
                    self.imagination[0].shape[1] + x_space:self.imagination[0].shape[1] + x_space +
                                                           self.imagination[1].shape[1], l] = self.imagination[1][:, :, l]
                    img_arr[:self.imagination[2].shape[0],
                    self.imagination[0].shape[1] + self.imagination[1].shape[1] + 2 * x_space:, l] = self.imagination[2][:,
                                                                                                     :, l]
            else:
                y_dim = self.imagination[0].shape[0]
                x_dim = self.imagination[0].shape[1]
                z_dim=4
                img_arr = np.ones([y_dim, x_dim, z_dim], dtype="uint8") * 255
                img_arr[:,:,:3]=self.imagination[0].copy()
            # im = PIL.Image.open(filename)
            img_arr = cv2.resize(img_arr, (0, 0), fx=self.area.get_allocated_width() * 1.0 / (1.0 * x_dim),
                                 fy=self.area.get_allocated_width() * 1.0 / (1.0 * x_dim))
            # im.putalpha(256)  # create alpha channel
            # arr = np.array(im)
            height, width, channels = img_arr.shape
            self.surface = cairo.ImageSurface.create_for_data(img_arr, cairo.FORMAT_ARGB32, width, height)
            # surface = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, width, height)
            print("IMAGE SHAPE", height, width, channels)
            # Create a new buffer

    def do_drawing(self, ctx):
        self.draw_image(ctx)


####################################################################################################################################################################################


class OntologyAreaFrame(Gtk.Frame):
    def __init__(self, css=None, border_width=0):
        super().__init__()
        self.set_border_width(border_width)
        self.set_size_request(100, 100)

        self.vexpand = True
        self.hexpand = True
        self.surface = None
        self.view = WebKit2.WebView()
        self.settings =  WebKit2.Settings(enable_fullscreen=True,
                                           enable_smooth_scrolling=True,
                                           enable_dns_prefetching=True,
                                           enable_webgl=True,
                                           enable_media_stream=True,
                                           enable_mediasource=True,
                                           enable_encrypted_media=True,
                                           enable_developer_extras=True)

        font_size = 14
        font_default = "VLGothic"
        font_serif = "VLGothic"
        font_sans_serif = "VLGothic"
        font_monospace = "VLGothic"

        self.settings.set_property("serif-font-family", font_serif)
        self.settings.set_property("sans-serif-font-family", font_sans_serif)
        self.settings.set_property("monospace-font-family", font_monospace)
        self.settings.set_property("default-font-family", font_default)
        self.settings.set_property("default-font-size", font_size)

        self.settings.set_hardware_acceleration_policy(False)
        self.settings.set_enable_javascript(True)
        self.view.set_settings(self.settings)

        self.swin = Gtk.ScrolledWindow()
        self.swin.add(self.view)
        self.swin.set_hexpand(True)
        self.swin.set_vexpand(True)
        self.swin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.add(self.swin)
        self.view.load_html("", "ontology.html")

    def set_nearest_vertex(self, x, y, delta=30.0):
        self.min_index = -1
        min_dist = +math.inf
        # print("Num vertices",self.g.num_vertices())
        for i in range(self.g.num_vertices()):
            x2 = self.pos[i][0] * self.area.get_allocated_width()
            y2 = self.pos[i][1] * self.area.get_allocated_width()
            print(x, y, x2, y2)
            d = np.sqrt(pow(x - x2, 2) + pow(y - y2, 2))
            if (d < min_dist) and (d <= delta):
                min_dist = d
                self.min_index = i

    def on_release(self):
        if self.min_index > -1:
            self.h[self.min_index] = False
            self.min_index = -1
            self.redraw()
            self.area.queue_draw()

    def on_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            print(event.x, event.y, event.type)
            self.set_nearest_vertex(event.x, event.y)
            if self.min_index > -1:
                self.h[self.min_index] = True
                self.mouseX = event.x
                self.mouseY = event.y
                self.redraw()
                self.area.queue_draw()
        else:
            if event.type == Gdk.EventType.BUTTON_RELEASE:
                self.on_release()
            else:
                if event.type == Gdk.EventType.MOTION_NOTIFY and self.min_index > -1:
                    deltaX = event.x - self.mouseX
                    deltaY = event.y - self.mouseY
                    self.mouseX = event.x
                    self.mouseY = event.y
                    self.pos[self.min_index][0] = min(
                        max(self.pos[self.min_index][0] + deltaX / self.area.get_allocated_width(), 0.), 1.0)
                    self.pos[self.min_index][1] = min(
                        max(self.pos[self.min_index][1] + deltaY / self.area.get_allocated_width(), 0.), 1.0)
                    self.redraw()
                    self.area.queue_draw()

                    print("SOME MOTION")

    def destroy_graph(self):
        if self.g is not None:
            self.g.clear()
            self.g = None

    def build_graph(self):

        self.g = Graph(directed=True)
        v1 = self.g.add_vertex()
        v12 = self.g.add_vertex()
        v2 = self.g.add_vertex()
        v3 = self.g.add_vertex()
        v31 = self.g.add_vertex()
        v4 = self.g.add_vertex()
        v34 = self.g.add_vertex()

        e012 = self.g.add_edge(v1, v12)
        e112 = self.g.add_edge(v12, v2)
        e031 = self.g.add_edge(v3, v31)
        e131 = self.g.add_edge(v31, v1)
        e034 = self.g.add_edge(v3, v34)
        e134 = self.g.add_edge(v34, v4)

        self.x = self.g.new_vertex_property("string")
        self.x[v1] = "Milk"
        self.x[v2] = "MilkBottle"
        self.x[v3] = "MilkPreparation"
        self.x[v4] = "Task"
        self.x[v12] = "is_in"
        self.x[v31] = "involves"
        self.x[v34] = "is_a"

        self.y = self.g.new_edge_property("string")
        self.y[e012] = ""
        self.y[e112] = ""
        self.y[e031] = ""
        self.y[e131] = ""
        self.y[e034] = ""
        self.y[e134] = ""

        self.m = self.g.new_edge_property("string")
        self.m[e012] = "none"
        self.m[e112] = "arrow"
        self.m[e031] = "none"
        self.m[e131] = "arrow"
        self.m[e034] = "none"
        self.m[e134] = "arrow"

        self.s = self.g.new_vertex_property("string")
        self.s[v2] = "circle"
        self.s[v1] = "circle"
        self.s[v3] = "circle"
        self.s[v4] = "circle"
        self.s[v12] = "square"
        self.s[v31] = "square"
        self.s[v34] = "square"

        self.c = self.g.new_vertex_property("vector<float>")
        self.c[v2] = np.array([1., 0., 0.0, 1.], dtype="float")
        self.c[v1] = np.array([0.7, 0., 0.0, 1.], dtype="float")
        self.c[v3] = np.array([0.5, 0., 0.0, 1.], dtype="float")
        self.c[v4] = np.array([0.3, 0., 0.0, 1.], dtype="float")
        self.c[v12] = (self.c[v1].get_array() + self.c[v2].get_array()) / 2.
        self.c[v31] = (self.c[v3].get_array() + self.c[v1].get_array()) / 2.
        self.c[v34] = (self.c[v4].get_array() + self.c[v3].get_array()) / 2.
        self.pos = self.g.new_vertex_property("vector<float>")
        self.pos[v1] = np.array([0.3, 0.3 * 0.4], dtype="float")
        self.pos[v2] = np.array([0.3, 0.9 * 0.4], dtype="float")
        self.pos[v3] = np.array([0.7, 0.3 * 0.4], dtype="float")
        self.pos[v4] = np.array([0.9, 0.9 * 0.4], dtype="float")
        self.pos[v31] = (self.pos[v1].get_array() + self.pos[v3].get_array()) / 2.
        self.pos[v12] = (self.pos[v1].get_array() + self.pos[v2].get_array()) / 2.
        self.pos[v34] = (self.pos[v4].get_array() + self.pos[v3].get_array()) / 2.

        self.h = self.g.new_vertex_property("bool")
        self.h[v1] = False
        self.h[v2] = False
        self.h[v3] = False
        self.h[v4] = False
        self.h[v12] = False
        self.h[v31] = False
        self.h[v34] = False

        self.mouseX = 0.0
        self.mouseY = 0.0

    def init_surface(self, area):
        # Destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None

        # Create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.area.get_allocated_width(),
                                          self.area.get_allocated_width())

    def redraw(self):
        print(self.g, self.c, self.x)
        self.init_surface(self.area)
        context = cairo.Context(self.surface)
        context.scale(self.surface.get_width(), self.surface.get_height())
        self.do_drawing(context)
        self.surface.flush()

    def on_configure(self, area, event, data=None):
        self.redraw()
        return False

    def on_draw(self, area, context):
        if self.surface is not None:
            context.set_source_surface(self.surface, 0.0, 0.0)
            context.paint()
        else:
            print('Invalid surface')
        return False

    def draw_graph(self, ctx):

        if self.g is None:
            ctx.rectangle(0, 0, 1, 1)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        else:
            graph_tool.draw.cairo_draw(self.g, self.pos, ctx, edge_dash_style=[.005, .005, 0], edge_end_marker=self.m,
                                       edge_font_family="bahnschrift", vertex_font_family="bahnschrift",
                                       vertex_font_size=12, edge_font_size=20, edge_marker_size=18,
                                       vertex_fill_color=[.7, .8, .9, 0.9], vertex_color=self.c, edge_text=self.y,
                                       vertex_text=self.x, vertex_shape=self.s, vertex_size=80, vertex_halo_size=1.2,
                                       vertex_halo=self.h, vertex_pen_width=3.0, edge_pen_width=1)

    def do_drawing(self, ctx):
        self.draw_graph(ctx)


class SearchDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Search", transient_for=parent, modal=True)
        self.add_buttons(
            Gtk.STOCK_FIND,
            Gtk.ResponseType.OK,
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
        )

        box = self.get_content_area()

        label = Gtk.Label(label="Insert text you want to search for:")
        box.add(label)

        self.entry = Gtk.Entry()
        box.add(self.entry)

        self.show_all()


class Transformers():
    def __init__(self, state_verb):
        self.state_verb = state_verb

    def context(self, trees):
        interpretation = []
        for statements in trees.children:
            if statements is not None:
                if statements.__class__ == lark.Tree:
                    if statements.data.value == 'statement':
                        interpretation = interpretation + self.statement(statements)
        return interpretation

    def statement(self, trees):
        subject = self.decompose(trees.children[0])
        subject_noun = subject['noun'][0]
        object = self.decompose(trees.children[2])
        subject_adjectiv = subject['adjectiv']
        subject_terminal = self.getTerminal(subject_noun)
        object_noun = object['noun'][0]
        object_adjectiv = object['adjectiv']
        object_terminal = self.getTerminal(object_noun)
        interpretation = [[subject_terminal, self.getTerminal(trees.children[1]), object_terminal]]
        interpretation = interpretation + self.subject(subject_adjectiv, subject_terminal) + self.object(
            object_adjectiv, object_terminal)
        return interpretation

    def subject(self, adjectives, noun):
        interpretation = []
        for adj in adjectives:
            interpretation.append([str(noun), self.state_verb, self.getTerminal(adj)])
        return interpretation

    def object(self, adjectives, noun):
        interpretation = []
        for adj in adjectives:
            interpretation.append([str(noun), self.state_verb, self.getTerminal(adj)])
        return interpretation

    def decompose(self, trees):
        result = {'noun': [], 'adjectiv': []}
        for res in trees.children:
            if (res is not None) and (res.__class__ == lark.Tree) and (res.data.value in ["noun", "adjectiv"]):
                result[res.data.value].append(res)
        return result

    def getTerminal(self, trees):
        terminal = ""
        if trees is None:
            pass
        else:
            if trees.__class__ == lark.Tree:
                for elt in trees.children:
                    r = self.getTerminal(elt)
                    if len(terminal) > 0 and len(r) > 0:
                        terminal = terminal + " " + r
                    else:
                        terminal = terminal + r
            else:
                r = str(trees)
                if len(terminal) > 0 and len(r) > 0:
                    terminal = terminal + " " + r
                else:
                    terminal = terminal + r
        return terminal


# The tab object for monitoring different aspects of the framework
class MovableFrame():
    def __init__(self, title, parent):
        self.title = title
        self.parent = parent
        self.header = Gtk.HBox()
        self.title = Gtk.Label(label=title)
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        close_button = Gtk.Button()
        close_button.set_image(image)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.connect("clicked", self.on_movable_frame_close)
        self.header.pack_start(self.title,expand=True, fill=True, padding=0)
        self.header.pack_end(close_button,expand=False, fill=False, padding=0)
        self.header.show_all()
    def on_movable_frame_close(self, button):
        self.parent.remove_page(self.parent.get_current_page())

# The tab object for monitoring different aspects of the framework
class SetMovableFrame(Gtk.Notebook):
    def add_movable_frame(self, title, widget):
        movable_frame = MovableFrame(title, self)
        self.append_page(widget, movable_frame.header)


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(1920, 1080)
        # the graph
        self.nt = None
        self.CONTEXT={}
        self.CONTEXT["Joint_Graph"]=[]
        self.CONTEXT["Creation_Date"]=dt.timestamp(dt.now())
        self.thread = None
        self.thread_robot = None
        self.thread_run_belief=None
        self.Nb_Cameras=2
        self.observation_frequency = 60.  # in Hz
        # Imagination framework

        # create action client for ontology
        self.path_name = "/ontology/naivphys4rp.owl"
        self.package = "belief_state"
        self.namespace = "http://www.semanticweb.org/franklin/ontologies/2022/7/naivphys4rp.owl#"  # default ontology's namespace
        self.concepts = []
        self.relations = []
        self.symbol_grounding_table = {}
        self.onto_load_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_load', KBLoadOntologyAction)
        print("Client ontology loading is started !")
        print("Waiting for action server ...")
        self.onto_load_client.wait_for_server()
        print("Loading ontology ...")
        self.grammarFile = 'grammar.json'
        self.grammar = json.dumps("{}")
        self.state_verb = "is"
        self.aggregation_relations={'SOFT':'includes', 'HARD':'has_part'}
        self.participant_global_relation="needs"
        self.CONTEXT['Participant_Global_Relation']=self.participant_global_relation
        self.action_object_relation = "performs"
        self.CONTEXT['Action_Object_Relation'] = self.action_object_relation
        self.grammar = """
        	context: (statement delimiter)*

        	statement: subject verb object

        	object: [determinant] (adjectiv)* noun

        	subject: [determinant] (adjectiv)* noun

        	determinant: DET

        	verb: iverb | dverb

        	iverb: dverb preposition

        	noun: NOUN

        	delimiter: FULLSTOP | COMMA | CONJUNCTION

        	dverb: DVERB

        	preposition: PREP

        	adjectiv: (COLOR|SIZE|SHAPE|MATERIAL|TIGHTNESS)
        	
        	CONJUNCTION: "and"

            FULLSTOP: "."

            COMMA: ","

            DVERB: "has" | "is" | "participates" | "makes" | "cooks" | "prepares" | "pours" | "moves" | "transports" | "picks"  ["up"] | "places" | "sees" | "observes" | "looks" | "perceives" | "inserts" | "inserted" | "tests" 

            PREP: "in" | "on" | "over" | "under" | "of" | "at" | "to" | "behind" | "left to" | "right to" | "near to" | "far from" | "near" | "in front of"

        	NOUN: "box" | "medium rinse fluid bottle" | "large rinse fluid bottle" | "small soy broth bottle" | "milk" | "machine" | "robot" | "bowl" | "spoon" | "bottle" | "table" | "fridge" | "mug" | "drawer" | "island" | "sink" | "muesli" | "cornflakes" | "kitchen" | "lab" | "laboratory" | "labor" | "dinningroom" | "dinning room" | "breakfast" | "pump" | "rinse fluid" | "sample fluid"| "fluid" | "fluid" | "drain tray" | "tray" | "canister"| "sterility test table"

        	DET: "a" | "an" | "the" | "another" | "this" | "that"

            COLOR: "red" | "orange" | "brown" | "yellow" | "green" | "blue" | "white" | "gray" | "black" | "violet" |"pink"

            SHAPE: "cubic" |"conical" | "cylindrical" | "filiform" | "flat" | "rectangular" | "circular" | "triangular"

            MATERIAL: "plastic" | "woody" | "glassy" | "steel" | "cartoonish" | "ceramic"

            TIGHTNESS: "solid" | "gaseous" | "liquid" | "powdered"

            SIZE: "large" | "big" | "medium" | "small" | "tiny"

        	%import common.ESCAPED_STRING

        	%import common.SIGNED_NUMBER

        	%import common.WS

        	%ignore WS
        """
        self.text=""
        self.containment_disposition={'Support':['is_on'], 'Container':['is_in']}
        self.quality_relation={'Material':{'relation':['has_material'], 'dtype':[str], 'units':[],'unknown_value':['Unknown_Material']}, 'Color':{'unknown_value':['Unknown_Color'],'relation':['has_color'], 'dtype':[str], 'units':[]},'Mass':{'unknown_value':['0.01-1'],'relation':['has_mass'], 'dtype':[float], 'units':['kg']}}
        self.CONTEXT['Quality_Relation']=self.quality_relation
        self.CONTEXT['Containment_Disposition']=self.containment_disposition
        self.spatial_direction={'is_behind':{'synonym':['is_behind'], 'opposite':['is_infront'], 'probability':0.2, 'canonicity':False},'is_infront':{'synonym':['is_infront'], 'opposite':['is_behind'], 'probability':0.2, 'canonicity':True},'is_right':{'synonym':['is_right'], 'opposite':['is_left'], 'probability':0.3, 'canonicity':False},'is_left':{'synonym':['is_left'], 'opposite':['is_right'], 'probability':0.3, 'canonicity':True}}
        self.spatial_proximity={'is_far':{'synonym':['is_far'], 'opposite':['is_near'], 'probability':0.4, 'canonicity':True, 'fuzzy_boundary':'0.0-0.5'}, 'is_near':{'synonym':['is_near'], 'opposite':['is_near'], 'probability':0.6, 'canonicity':True, 'fuzzy_boundary':'0.5-1.0'}}
        self.role_player_participant_probability=0.98
        self.role_player_participant_representativeness = 0.98
        self.containment_probability=0.4
        self.CONTEXT['Containment_Probability']=self.containment_probability
        self.CONTEXT['Role_Player_Participant_Probability']=self.role_player_participant_probability
        self.CONTEXT['Role_Player_Participant_Representativeness']=self.role_player_participant_representativeness
        self.CONTEXT['State_Verb']=self.state_verb
        self.CONTEXT['Grammar']=self.grammar
        self.unknown_value='UNKNOWN'
        self.CONTEXT['Unknown_Value']=self.unknown_value
        self.quality_probability=0.1
        self.CONTEXT['Quality_Probability']=self.quality_probability
        self.json_parser = lark.Lark(self.grammar, start="context", ambiguity='explicit')

        goal = KBLoadOntologyGoal()
        goal.package = self.package
        goal.namespace = self.namespace
        goal.relative_path = self.path_name
        self.onto_load_client.send_goal(goal)
        self.onto_load_client.wait_for_result()
        if (self.onto_load_client.get_result().status == True):
            print("Ontology loaded successfully!")
        else:
            print("Ontology failed to load!!!")

        self.list_part_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_part', KBClassConstituentAction)
        print("Client ontology parts is started !")
        print("Waiting for action server parts...")
        self.list_part_client.wait_for_server()
        print("Action server parts loaded")

        self.list_synonym_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_synonym', KBClassSynonymAction)
        print("Client ontology synonym is started !")
        print("Waiting for action server synonym...")
        self.list_synonym_client.wait_for_server()
        print("Action server synonym loaded")

        self.onto_class_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_subclass', KBSubClassAction)
        print("Client ontology subclass is started !")
        print("Waiting for action server subclass...")
        self.onto_class_client.wait_for_server()
        print("Action server subclass loaded")

        self.onto_property_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_subproperty', KBSubPropertyAction)
        print("Client ontology subproperty is started !")
        print("Waiting for action server subproperty...")
        self.onto_property_client.wait_for_server()
        print("Action server subproperty loaded")

        self.onto_list_property_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_list_property',
                                                                      KBListPropertyAction)
        print("Client list property is started !")
        print("Waiting for action server list property...")
        self.onto_list_property_client.wait_for_server()
        print("Action server list property loaded")

        self.onto_list_class_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_list_class', KBListClassAction)
        print("Client list class is started !")
        print("Waiting for action server list class...")
        self.onto_list_class_client.wait_for_server()
        print("Action server list class loaded")

        self.onto_property_io_client = actionlib.SimpleActionClient('naivphys4rp_knowrob_property_io',
                                                                    KBPropertyIOAction)
        print("Client property io is started !")
        print("Waiting for action server property io...")
        self.onto_property_io_client.wait_for_server()
        print("Action server property io loaded")

        self.list_participant_client = actionlib.SimpleActionClient('naivphys4rp_list_participant',
                                                                    KBListParticipantAction)
        print("Client list prticipant is started !")
        print("Waiting for action server list participant...")
        self.list_participant_client.wait_for_server()
        print("Action server list participant loaded")

        self.role_to_object_client = actionlib.SimpleActionClient('naivphys4rp_role_to_object',
                                                                  KBFromRoleToObjectAction)
        print("Client role to object is started !")
        print("Waiting for action server role to object...")
        self.role_to_object_client.wait_for_server()
        print("Action server role to object loaded")

        self.domain_relation_client = actionlib.SimpleActionClient('naivphys4rp_domain_relation',
                                                                   KBDomainRelationAction)
        print("Client domain relation is started !")
        print("Waiting for action server domain relation...")
        self.domain_relation_client.wait_for_server()
        print("Action server domain relation loaded")

        self.potential_action_object_client = actionlib.SimpleActionClient('naivphys4rp_potential_action_object',
                                                                           KBPotentialActionObjectAction)
        print("Client potential action object is started !")
        print("Waiting for action server potential action object...")
        self.potential_action_object_client.wait_for_server()
        print("Action server potential action object loaded")

        self.data_property = actionlib.SimpleActionClient('naivphys4rp_knowrob_data_property',KBDataPropertyAction)
        print("Client data property is started !")
        print("Waiting for action server data property...")
        self.data_property.wait_for_server()
        print("Action server data property loaded")

        """
                ################## List of Class ########################################
                goal = KBListClassGoal()
                self.onto_list_class_client.send_goal(goal)
                self.onto_list_class_client.wait_for_result()
                results = self.onto_list_class_client.get_result()
                self.generic_class_prefix="_:Description"
                if (len(results.classes) > 0):
                    print("Knowrob query executed successfully!")
                    for cls in results.classes:
                        if len(cls.split(self.generic_class_prefix))<2:
                            self.concepts.append(cls)
                    print(len(self.concepts),self.concepts)
                else:
                    print("Knowrob query failed!!")

                ####################### List of Property ##############################################
                goal = KBListPropertyGoal()
                self.onto_list_property_client.send_goal(goal)
                self.onto_list_property_client.wait_for_result()
                results = self.onto_list_property_client.get_result()
                if (len(results.properties) > 0):
                    print("Knowrob query executed successfully!")
                    self.concepts = results.properties.copy()
                    print(len(results.properties),results.properties)
                else:
                    print("Knowrob query failed!!")
                """
        """
        ################ List of classes ####################################
        goal = KBSubClassGoal()
        goal.is_sub = True
        goal.namespace = "http://www.w3.org/2002/07/owl#"
        goal.class_name = 'Thing'
        self.onto_class_client.send_goal(goal)
        self.onto_class_client.wait_for_result()
        results = self.onto_class_client.get_result()
        self.classes = {}
        self.generic_class_prefix = "_:Description"
        if (len(results.classes) > 0):
            print("Knowrob query executed successfully!")
            for cls in results.classes:
                if len(cls.split(self.generic_class_prefix)) < 2 and len(cls.split(self.namespace)) >= 2:
                    self.classes[cls.split(self.namespace).pop()] = cls
            print(len(self.classes), self.classes)
        else:
            print("Knowrob query failed!!")
        self.CONTEXT['List_Classes']=self.classes
        ######################### List of Subproperty ################################
        goal = KBSubPropertyGoal()
        goal.is_sub = True
        goal.namespace = "http://www.w3.org/2002/07/owl#"
        goal.property_name = 'topObjectProperty'
        self.onto_property_client.send_goal(goal)
        self.onto_property_client.wait_for_result()
        results = self.onto_property_client.get_result()
        self.object_properties = {}
        self.generic_class_prefix = "_:Description"
        if (len(results.propertyes) > 0):
            print("Knowrob query executed successfully!")
            for cls in results.propertyes:
                if len(cls.split(self.generic_class_prefix)) < 2 and len(cls.split(self.namespace)) >= 2:
                    self.object_properties[cls.split(self.namespace).pop()] = cls
            print(len(self.object_properties), self.object_properties)
        else:
            print("Knowrob query failed!!")
        self.object_properties[self.state_verb] = "rdfs:SubClassOf"
        self.CONTEXT['Object_Properties'] = self.object_properties

        ################## List of Action as Object Property ########################################
        goal = KBSubClassGoal()
        goal.class_name = 'Action'
        goal.is_sub = True
        goal.namespace = self.namespace
        self.actions = {}
        self.onto_class_client.send_goal(goal)
        self.onto_class_client.wait_for_result()
        results = self.onto_class_client.get_result()
        self.generic_class_prefix = "_:Description"
        if (len(results.classes) > 0):
            print("Knowrob query executed successfully!")
            for cls in results.classes:
                if len(cls.split(self.generic_class_prefix)) < 2:
                    self.actions[cls.split(self.namespace).pop()] = cls
                    self.object_properties[cls.split(self.namespace).pop()] = cls
            print(len(self.actions), self.actions)
        else:
            print("Knowrob query failed!!")
        self.CONTEXT['List_Actions'] = self.actions

        ######################### List of Subproperty ################################
        goal = KBSubPropertyGoal()
        goal.is_sub = True
        goal.namespace = "http://www.w3.org/2002/07/owl#"
        goal.property_name = 'topDataProperty'
        self.onto_property_client.send_goal(goal)
        self.onto_property_client.wait_for_result()
        results = self.onto_property_client.get_result()
        self.data_properties = {}
        self.generic_class_prefix = "_:Description"
        if (len(results.propertyes) > 0):
            print("Knowrob query executed successfully!")
            for cls in results.propertyes:
                if len(cls.split(self.generic_class_prefix)) < 2 and len(cls.split(self.namespace)) >= 2:
                    self.data_properties[cls.split(self.namespace).pop()] = cls
            print(len(self.data_properties), self.data_properties)
        else:
            print("Knowrob query failed!!")
        self.CONTEXT['Data_Properties'] = self.data_properties

        ######################### List of property range ################################
        self.property_io = {}
        for prop in self.data_properties:
            goal = KBPropertyIOGoal()
            goal.type_range = "extension"
            goal.namespace = self.namespace
            goal.property_name = prop.split(self.namespace).pop()
            self.onto_property_io_client.send_goal(goal)
            self.onto_property_io_client.wait_for_result()
            self.property_io[prop] = self.onto_property_io_client.get_result().erange
        self.CONTEXT['Data_Properties_Ranges'] = self.property_io

        ######################### List of disposition ################################
        goal = KBSubClassGoal()
        results = KBSubClassResult()
        goal.class_name = 'Role'
        goal.is_sub = True
        goal.namespace = self.namespace
        self.roles = {}
        self.onto_class_client.send_goal(goal)
        self.onto_class_client.wait_for_result()
        results = self.onto_class_client.get_result()
        self.generic_class_prefix = "_:Description"
        if (len(results.classes) > 0):
            print("Knowrob query executed successfully!")
            for cls in results.classes:
                if len(cls.split(self.generic_class_prefix)) < 2:
                    self.roles[cls.split(self.namespace).pop()] = {}
                    self.roles[cls.split(self.namespace).pop()]['url'] = cls
            print("***************************", self.roles)
        else:
            print("Knowrob query failed!!")
        self.CONTEXT['List_Roles'] = self.roles

        ######################### List of object per disposition ################################
        for disposition in self.roles.keys():
            goal = KBFromRoleToObjectGoal()
            results = KBFromRoleToObjectResult()
            goal.class_name = disposition
            goal.namespace = self.namespace
            self.roles[disposition]['object'] = []
            self.role_to_object_client.send_goal(goal)
            self.role_to_object_client.wait_for_result()
            results = self.role_to_object_client.get_result()
            results.classes = list(set(results.classes))
            for cls in results.classes:
                if len(cls.split(self.generic_class_prefix)) < 2:
                    self.roles[disposition]['object'].append(cls.split(self.namespace).pop())

        self.CONTEXT['List_Roles'] = self.roles

        ######################### List of relation to action domain ################################
        for disposition in self.roles.keys():
            goal = KBDomainRelationGoal()
            results = KBDomainRelationResult()
            goal.class_name = disposition
            goal.type = 'Action'
            goal.namespace = self.namespace
            self.roles[disposition]['action_relation'] = []
            self.domain_relation_client.send_goal(goal)
            self.domain_relation_client.wait_for_result()
            results = self.domain_relation_client.get_result()
            results.relations = list(set(results.relations))
            for cls in results.relations:
                if len(cls.split(self.generic_class_prefix)) < 2:
                    self.roles[disposition]['action_relation'].append(cls.split(self.namespace).pop())
        self.CONTEXT['List_Roles'] = self.roles

        ######################### List of relation to object domain ################################
        for disposition in self.roles.keys():
            goal = KBDomainRelationGoal()
            results = KBDomainRelationResult()
            goal.class_name = disposition
            goal.type = 'Object'
            goal.namespace = self.namespace
            self.roles[disposition]['object_relation'] = []
            self.domain_relation_client.send_goal(goal)
            self.domain_relation_client.wait_for_result()
            results = self.domain_relation_client.get_result()
            results.relations = list(set(results.relations))
            for cls in results.relations:
                if len(cls.split(self.generic_class_prefix)) < 2:
                    self.roles[disposition]['object_relation'].append(cls.split(self.namespace).pop())
        print("+++++++++++++++++++++++++++++++++++++++++++", self.roles)
        self.CONTEXT['List_Roles'] = self.roles

        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")
        
        ######################Object per Role#####################################################################
        self.action_object_role={}
        for role in self.roles.keys():
            print('1.1.********************************************************************', role)
            self.action_object_role[role]={}
            for object in self.roles[role]['object']:
                print('1.2.********************************************************************',  role, object)
                self.action_object_role[role][object] = {}

                #Action
                self.action_object_role[role][object]['action'] = []
                goal = KBPotentialActionObjectGoal()
                results = KBPotentialActionObjectResult()
                goal.class_name = object
                goal.relation = self.roles[role]['action_relation'][0]
                goal.namespace = self.namespace
                goal.type='Action'
                self.potential_action_object_client.send_goal(goal)
                self.potential_action_object_client.wait_for_result()
                results = self.potential_action_object_client.get_result()
                for cls in results.classes:
                    if len(cls.split(self.generic_class_prefix)) < 2:
                        print('1.3.********************************************************************', role, object,cls)
                        self.action_object_role[role][object]['action'].append(cls.split(self.namespace).pop())

                # Object
                self.action_object_role[role][object]['object'] = []
                if role not in self.containment_disposition.keys():
                    continue
                goal = KBPotentialActionObjectGoal()
                results = KBPotentialActionObjectResult()
                goal.class_name = object
                goal.relation = self.roles[role]['object_relation'][0]
                goal.namespace = self.namespace
                goal.type = 'Object'
                self.potential_action_object_client.send_goal(goal)
                self.potential_action_object_client.wait_for_result()
                results = self.potential_action_object_client.get_result()
                for cls in results.classes:
                    if len(cls.split(self.generic_class_prefix)) < 2:
                        print('1.3.********************************************************************', role,
                              object, cls)
                        self.action_object_role[role][object]['object'].append(cls.split(self.namespace).pop())



        self.CONTEXT['Action_Object_Role'] = self.action_object_role

        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")
        """
        ##########################################################################################################

        # This will be in the windows group and have the "win" prefix
        max_action = Gio.SimpleAction.new_stateful(
            "maximize", None, GLib.Variant.new_boolean(False)
        )
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)

        # Keep it in sync with the actual state
        self.connect(
            "notify::is-maximized",
            lambda obj, pspec: max_action.set_state(
                GLib.Variant.new_boolean(obj.props.is_maximized)
            ),
        )

        lbl_variant = GLib.Variant.new_string("String 1")
        lbl_action = Gio.SimpleAction.new_stateful(
            "change_label", lbl_variant.get_type(), lbl_variant
        )
        lbl_action.connect("change-state", self.on_change_label_state)
        self.add_action(lbl_action)

        self.label = Gtk.Label(label=lbl_variant.get_string(), margin=30)
        self.grid = Gtk.Grid()
        self.top_grid = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)
        self.context_editor_frame = Gtk.Frame()
        self.ontology_frame = OntologyAreaFrame()
        self.imagination_frame = ImaginationAreaFrame()
        self.ce_label = Gtk.Label(label="", margin=10)
        self.ce_label.set_markup("<b>Context Editor - Abstract Context Description Language (ACDL)</b>")
        self.context_editor_frame.set_label_widget(self.ce_label)
        # self.grid.attach(self.label, 1, 20, 2, 1)

        self.o_label = Gtk.Label(label="", margin=10)
        self.o_label.set_markup("<b>Ontology - Context formalization</b>")
        self.ontology_frame.set_label_widget(self.o_label)

        self.i_label = Gtk.Label(label="", margin=10)
        self.i_label.set_markup("<b>Imagination - Mind eye's view of context</b>")
        self.imagination_frame.set_label_widget(self.i_label)

        self.lsepartor_label = Gtk.Label(label="", margin=1)
        self.rsepartor_label = Gtk.Label(label="", margin=1)
        self.bsepartor_label = Gtk.Label(label="", margin=1)

        self.context_editor_frame.add(self.grid)

        # print("SIZE GRID", self.top_grid.get_size())
        self.top_grid.attach(self.lsepartor_label, 0, 0, 1, 1)
        self.top_grid.attach(self.rsepartor_label, 114, 0, 1, 1)
        self.top_grid.attach(self.bsepartor_label, 0, 49, 1, 1)
        self.top_grid.attach(self.context_editor_frame, 1, 0, 40, 49)
        self.top_grid.attach(self.ontology_frame, 41, 0, 72, 31)
        self.top_grid.attach(self.imagination_frame, 41, 31, 72, 18)
        self.create_textview()
        self.create_toolbar()
        self.create_buttons()
        self.imaginator = Imagination(nb_cameras=self.Nb_Cameras)
        self.belief_filtering=Filtering()



        #building the tabs
        self.setFrame=SetMovableFrame()

        ########################################## Adding input frame ##############################################
        self.movable_input_frame = Gtk.Frame()
        self.setFrame.add_movable_frame("Emulator Configuration", self.movable_input_frame)
        self.config_separator1 = Gtk.Label(label="", margin=1)
        self.config_separator2 = Gtk.Label(label="", margin=1)
        self.config_separator3 = Gtk.Label(label="", margin=1)
        self.config_separator4 = Gtk.Label(label="", margin=1)
        self.config_separator5 = Gtk.Label(label="", margin=1)

        #adding sensor configuration pane
        self.config_sensor_frame = Gtk.Frame()
        self.bc_label = Gtk.Label(label="", margin=10)
        self.bc_label.set_markup("<b>Sensor configurations</b>")
        self.config_sensor_frame.set_label_widget(self.bc_label)

        # adding motor configuration pane
        self.config_motor_frame = Gtk.Frame()
        self.bc_label = Gtk.Label(label="", margin=10)
        self.bc_label.set_markup("<b>Motor configurations</b>")
        self.config_motor_frame.set_label_widget(self.bc_label)

        # adding context configuration pane
        self.config_context_frame = Gtk.Frame()
        self.bc_label = Gtk.Label(label="", margin=10)
        self.bc_label.set_markup("<b>Belief configurations</b>")
        self.config_context_frame.set_label_widget(self.bc_label)

        # adding KB configuration pane
        self.config_ontology_frame = Gtk.Frame()
        self.bc_label = Gtk.Label(label="", margin=10)
        self.bc_label.set_markup("<b>Context configurations</b>")
        self.config_ontology_frame.set_label_widget(self.bc_label)

        self.config_top_grid = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.config_top_grid.attach(self.config_separator1, 0, 0, 1, 1)
        self.config_top_grid.attach(self.config_sensor_frame, 1, 0, 34, 10)
        #self.config_top_grid.attach(self.config_separator2, 35, 0, 1, 1)
        self.config_top_grid.attach(self.config_separator4, 35, 10, 1, 1)
        self.config_top_grid.attach(self.config_motor_frame, 36, 0, 33, 10)
        self.config_top_grid.attach(self.config_separator3, 69, 0, 1, 1)
        self.config_top_grid.attach(self.config_context_frame, 1, 11, 34, 41)
        self.config_top_grid.attach(self.config_ontology_frame, 36, 11, 33, 41)
        self.movable_input_frame.add(self.config_top_grid)

        ############################################################################################################################################################################################
        self.config_motor_grid = Gtk.Grid(column_homogeneous=True, column_spacing=3, row_spacing=30)

        ############################################

        self.config_motor_label9 = Gtk.Label(label="Robot Motor Model:", margin=1)
        self.config_motor_grid.attach(self.config_motor_label9, 0, 0, 5, 1)
        self.config_robot_motor_model = Gtk.ComboBoxText()
        self.list_model = ["PR2", "Turtle", "UR5/10", "HSR", "Pepper"]
        for i in range(len(self.list_model)):
            self.config_robot_motor_model.append_text(self.list_model[i])
        self.config_robot_motor_model.set_active(1)
        self.config_motor_grid.attach_next_to(self.config_robot_motor_model, self.config_motor_label9, Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator400 = Gtk.Label(label="", margin=1)
        self.config_motor_grid.attach_next_to(self.config_separator400, self.config_robot_motor_model, Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_motor_label = Gtk.Label(label="Time Frame Topic:", margin=1)

        self.config_motor_grid.attach(self.config_motor_label, 0, 1, 5, 1)
        self.config_motor_text_time_frame_topic = Gtk.Entry()
        self.config_motor_text_time_frame_topic.set_text("/tf")
        self.config_motor_grid.attach_next_to(self.config_motor_text_time_frame_topic, self.config_motor_label,
                                               Gtk.PositionType.RIGHT, 7, 1)

        ############################################

        self.config_motor_label500 = Gtk.Label(label="Joint State Topic:", margin=1)

        self.config_motor_grid.attach(self.config_motor_label500, 0, 2, 5, 1)
        self.config_motor_text_joint_state_topic = Gtk.Entry()
        self.config_motor_text_joint_state_topic.set_text("/joint_states")
        self.config_motor_grid.attach_next_to(self.config_motor_text_joint_state_topic, self.config_motor_label500,
                                              Gtk.PositionType.RIGHT, 7, 1)

        ############################################
        self.config_motor_label401 = Gtk.Label(label="Select Joints/Frame:", margin=1)
        self.config_motor_grid.attach(self.config_motor_label401, 0, 3, 5, 1)

        self.config_motor_time_joint_scrolledwindow = Gtk.ScrolledWindow()
        self.config_motor_time_joint_tree = Gtk.TreeView()
        self.config_motor_time_joint_frame = Gtk.Frame()
        self.config_motor_time_joint_tree_store = Gtk.TreeStore(bool, str)
        self.config_motor_time_joint_tree.set_model(self.config_motor_time_joint_tree_store)
        iter = self.config_motor_time_joint_tree_store.append(None, [True, "base_joint"])
        self.config_motor_time_joint_tree_store.append(None, [False, "base_r_joint"])
        self.config_motor_time_joint_tree_store.append(None, [True, "base_l_joint"])
        iter = self.config_motor_time_joint_tree_store.append(None, [True, "base_joint"])
        self.config_motor_time_joint_tree_store.append(None, [False, "base_r_joint"])
        self.config_motor_time_joint_tree_store.append(None, [True, "base_l_joint"])
        iter = self.config_motor_time_joint_tree_store.append(None, [True, "base_joint"])
        self.config_motor_time_joint_tree_store.append(None, [False, "base_r_joint"])
        self.config_motor_time_joint_tree_store.append(None, [True, "base_l_joint"])
        iter = self.config_motor_time_joint_tree_store.append(None, [True, "base_joint"])
        self.config_motor_time_joint_tree_store.append(None, [False, "base_r_joint"])
        self.config_motor_time_joint_tree_store.append(None, [True, "base_l_joint"])
        # create a column
        self.config_motor_time_joint_tree_column = Gtk.TreeViewColumn("Joint Selection", )
        self.config_motor_time_joint_tree.append_column(self.config_motor_time_joint_tree_column)
        # add a toggle render
        self.config_motor_time_joint_tree_toggle = Gtk.CellRendererToggle()
        self.config_motor_time_joint_tree_column.pack_start(self.config_motor_time_joint_tree_toggle, True)
        self.config_motor_time_joint_tree_column.add_attribute(self.config_motor_time_joint_tree_toggle, "active", 0)
        self.config_motor_time_joint_tree_column.set_clickable(True)
        self.config_motor_time_joint_tree_toggle.connect('toggled', self.on_toggle,
                                                         self.config_motor_time_joint_tree.get_model())
        # create a column
        self.config_motor_time_joint_tree_column2 = Gtk.TreeViewColumn("Joint Name", )
        self.config_motor_time_joint_tree.append_column(self.config_motor_time_joint_tree_column2)
        # and add a text renderer to a second column
        text_ren = Gtk.CellRendererText()
        self.config_motor_time_joint_tree_column2.pack_start(text_ren, True)
        self.config_motor_time_joint_tree_column2.add_attribute(text_ren, "text", 1)
        # self.config_motor_time_joint_tree.set_border_width(10)
        self.config_motor_time_joint_scrolledwindow.add(self.config_motor_time_joint_tree)
        self.config_motor_time_joint_frame.add(self.config_motor_time_joint_scrolledwindow)
        self.config_motor_grid.attach_next_to(self.config_motor_time_joint_frame, self.config_motor_label401,
                                              Gtk.PositionType.RIGHT, 7, 5)

        self.config_motor_time_frame_scrolledwindow = Gtk.ScrolledWindow()
        self.config_motor_time_frame_tree = Gtk.TreeView()
        self.config_motor_time_frame_frame = Gtk.Frame()
        self.config_motor_time_frame_tree_store = Gtk.TreeStore(bool, str)
        self.config_motor_time_frame_tree.set_model(self.config_motor_time_frame_tree_store)
        iter = self.config_motor_time_frame_tree_store.append(None, [True, "base_link"])
        self.config_motor_time_frame_tree_store.append(None, [False, "base_r_link"])
        self.config_motor_time_frame_tree_store.append(None, [True, "base_l_link"])
        # create a column
        self.config_motor_time_frame_tree_column = Gtk.TreeViewColumn("Frame Selection", )
        self.config_motor_time_frame_tree.append_column(self.config_motor_time_frame_tree_column)
        # add a toggle render
        self.config_motor_time_frame_tree_toggle = Gtk.CellRendererToggle()
        self.config_motor_time_frame_tree_column.pack_start(self.config_motor_time_frame_tree_toggle, True)
        self.config_motor_time_frame_tree_column.add_attribute(self.config_motor_time_frame_tree_toggle, "active", 0)
        self.config_motor_time_frame_tree_column.set_clickable(True)
        self.config_motor_time_frame_tree_toggle.connect('toggled', self.on_toggle,
                                                         self.config_motor_time_frame_tree.get_model())
        # create a column
        self.config_motor_time_frame_tree_column2 = Gtk.TreeViewColumn("Frame Name", )
        self.config_motor_time_frame_tree.append_column(self.config_motor_time_frame_tree_column2)
        # and add a text renderer to a second column
        text_ren = Gtk.CellRendererText()
        self.config_motor_time_frame_tree_column2.pack_start(text_ren, True)
        self.config_motor_time_frame_tree_column2.add_attribute(text_ren, "text", 1)
        # self.config_motor_time_frame_tree.set_border_width(10)
        self.config_motor_time_frame_scrolledwindow.add(self.config_motor_time_frame_tree)
        self.config_motor_time_frame_frame.add(self.config_motor_time_frame_scrolledwindow)
        self.config_motor_grid.attach_next_to(self.config_motor_time_frame_frame, self.config_motor_time_joint_frame,
                                              Gtk.PositionType.RIGHT, 7, 5)

        #############################################################################################

        self.config_motor_load = Gtk.Button(label="Load from File", margin=10)
        self.config_motor_load.connect("clicked", self.run_config_motor)
        self.config_motor_grid.attach(self.config_motor_load, 0, 8, 5, 1)

        self.config_motor_register = Gtk.Button(label="Register", margin=10)
        self.config_motor_register.connect("clicked", self.run_config_motor)
        self.config_motor_grid.attach_next_to(self.config_motor_register, self.config_motor_load,
                                              Gtk.PositionType.RIGHT, 5, 1)

        self.config_motor_save = Gtk.Button(label="Save to File", margin=10)
        self.config_motor_save.connect("clicked", self.run_config_motor)
        self.config_motor_grid.attach_next_to(self.config_motor_save, self.config_motor_register,
                                              Gtk.PositionType.RIGHT, 5, 1)

        self.config_motor_unregister = Gtk.Button(label="Unregister", margin=10)
        self.config_motor_unregister.connect("clicked", self.run_config_motor)
        self.config_motor_grid.attach_next_to(self.config_motor_unregister, self.config_motor_save,
                                              Gtk.PositionType.RIGHT, 5, 1)

        self.config_motor_load.set_sensitive(False)
        self.config_motor_save.set_sensitive(False)
        self.config_motor_unregister.set_sensitive(False)
        ############################################

        self.config_motor_grid.show_all()

        self.config_motor_frame.add(self.config_motor_grid)
        ############################################################################################################################################################################################

        self.config_sensor_grid = Gtk.Grid(column_homogeneous=True, column_spacing=3, row_spacing=30)

        self.config_sensor_label = Gtk.Label(label="Color Cam Info Topic:", margin=1)

        self.config_sensor_grid.attach(self.config_sensor_label, 0, 0, 5, 1)
        self.config_sensor_text_cam_info_topic = Gtk.Entry()
        self.config_sensor_text_cam_info_topic.set_text("/kinect_head/rgb/camera_info")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_cam_info_topic, self.config_sensor_label,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_sensor_label2 = Gtk.Label(label="Color Cam Data Topic:", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_label2, self.config_sensor_text_cam_info_topic,
                                               Gtk.PositionType.RIGHT, 5, 1)
        self.config_sensor_text_cam_data_topic = Gtk.Entry()
        self.config_sensor_text_cam_data_topic.set_text("/kinect_head/rgb/image_color/compressed")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_cam_data_topic, self.config_sensor_label2,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator10 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator10, self.config_sensor_text_cam_data_topic,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_sensor_label3 = Gtk.Label(label="Depth Cam Info Topic:", margin=1)

        self.config_sensor_grid.attach(self.config_sensor_label3, 0, 1, 5, 1)
        self.config_sensor_text_depth_info_topic = Gtk.Entry()
        self.config_sensor_text_depth_info_topic.set_text("/kinect_head/rgb/camera_info")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_depth_info_topic, self.config_sensor_label3,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_sensor_label4 = Gtk.Label(label="Depth Cam Data Topic:", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_label4, self.config_sensor_text_depth_info_topic,
                                               Gtk.PositionType.RIGHT, 5, 1)
        self.config_sensor_text_depth_data_topic = Gtk.Entry()
        self.config_sensor_text_depth_data_topic.set_text("/kinect_head/depth_registered/image_raw/compressedDepth")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_depth_data_topic, self.config_sensor_label4,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator11 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator11, self.config_sensor_text_depth_data_topic,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################
        self.config_sensor_label30 = Gtk.Label(label="Color Cam Hints:", margin=1)

        self.config_sensor_grid.attach(self.config_sensor_label30, 0, 2, 5, 1)
        self.config_sensor_text_color_hint = Gtk.Entry()
        self.config_sensor_text_color_hint.set_text("compressed")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_color_hint, self.config_sensor_label30,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_sensor_label40 = Gtk.Label(label="Depth Cam Hints:", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_label40, self.config_sensor_text_color_hint,
                                               Gtk.PositionType.RIGHT, 5, 1)
        self.config_sensor_text_depth_hint = Gtk.Entry()
        self.config_sensor_text_depth_hint.set_text("compressedDepth")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_depth_hint, self.config_sensor_label40,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator110 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator110, self.config_sensor_text_depth_hint,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_sensor_label5 = Gtk.Label(label="Source Frame:", margin=1)

        self.config_sensor_grid.attach(self.config_sensor_label5, 0, 3, 5, 1)
        self.config_sensor_text_source_frame = Gtk.Entry()
        self.config_sensor_text_source_frame.set_text("/head_mount_kinect_rgb_optical_frame")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_source_frame, self.config_sensor_label5,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_sensor_label6 = Gtk.Label(label="Destination Frame:", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_label6, self.config_sensor_text_source_frame,
                                               Gtk.PositionType.RIGHT, 5, 1)
        self.config_sensor_text_destination_frame = Gtk.Entry()
        self.config_sensor_text_destination_frame.set_text("/map")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_destination_frame, self.config_sensor_label6,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator12 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator12, self.config_sensor_text_destination_frame,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_sensor_label7 = Gtk.Label(label="Image Height:", margin=1)

        self.config_sensor_grid.attach(self.config_sensor_label7, 0, 4, 5, 1)
        self.config_sensor_text_image_height = Gtk.Entry()
        self.config_sensor_text_image_height.set_text("480")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_image_height, self.config_sensor_label7,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_sensor_label8 = Gtk.Label(label="Image Width:", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_label8, self.config_sensor_text_image_height,
                                               Gtk.PositionType.RIGHT, 5, 1)
        self.config_sensor_text_image_width = Gtk.Entry()
        self.config_sensor_text_image_width.set_text("640")
        self.config_sensor_grid.attach_next_to(self.config_sensor_text_image_width, self.config_sensor_label8,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator13 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator12, self.config_sensor_text_image_width,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_sensor_label9 = Gtk.Label(label="Camera Model:", margin=1)
        self.config_sensor_grid.attach(self.config_sensor_label9, 0, 5, 5, 1)
        self.config_sensor_camera_model = Gtk.ComboBoxText()
        self.list_model = ["Realsense", "Kinect", "Unreal Engine", "Bag File", "Unknown"]
        for i in range(len(self.list_model)):
            self.config_sensor_camera_model.append_text(self.list_model[i])
        self.config_sensor_camera_model.set_active(1)
        self.config_sensor_grid.attach_next_to(self.config_sensor_camera_model, self.config_sensor_label9,
                                               Gtk.PositionType.RIGHT, 7, 1)

        self.config_separator14 = Gtk.Label(label="", margin=1)
        self.config_sensor_grid.attach_next_to(self.config_separator14, self.config_sensor_camera_model,
                                               Gtk.PositionType.RIGHT, 1, 1)

        ############################################

        self.config_sensor_load = Gtk.Button(label="Load from File", margin=10)
        self.config_sensor_load.connect("clicked", self.run_config_sensor)
        self.config_sensor_grid.attach(self.config_sensor_load, 0, 6, 5, 1)

        self.config_sensor_register = Gtk.Button(label="Register", margin=10)
        self.config_sensor_register.connect("clicked", self.run_config_sensor)
        self.config_sensor_grid.attach_next_to(self.config_sensor_register, self.config_sensor_load,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_sensor_save = Gtk.Button(label="Save to File", margin=10)
        self.config_sensor_save.connect("clicked", self.run_config_sensor)
        self.config_sensor_grid.attach_next_to(self.config_sensor_save, self.config_sensor_register,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_sensor_unregister = Gtk.Button(label="Unregister", margin=10)
        self.config_sensor_unregister.connect("clicked", self.run_config_sensor)
        self.config_sensor_grid.attach_next_to(self.config_sensor_unregister, self.config_sensor_save,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_sensor_load.set_sensitive(False)
        self.config_sensor_save.set_sensitive(False)
        self.config_sensor_unregister.set_sensitive(False)

        ############################################
        self.config_sensor_grid.show_all()

        self.config_sensor_frame.add(self.config_sensor_grid)
        ############################################################################################################################################################################################
        ############################################################################################################################################################################################
        self.config_belief_grid = Gtk.Grid(column_homogeneous=True, column_spacing=3, row_spacing=30)

        ############################################

        self.config_belief_label0 = Gtk.Label(label="Physical World Model:", margin=1)
        self.config_belief_grid.attach(self.config_belief_label0, 0, 0, 5, 1)

        self.config_belief_physics = Gtk.Entry()
        self.config_belief_physics.set_text("/UParaSIM/Maps/Kitchen.umap")
        self.config_belief_grid.attach_next_to(self.config_belief_physics, self.config_belief_label0,
                                               Gtk.PositionType.RIGHT, 10, 1)

        ############################################
        self.config_belief_label1 = Gtk.Label(label="Number of Belief Particles:", margin=1)
        self.config_belief_grid.attach(self.config_belief_label1, 0, 1, 5, 1)

        self.config_belief_number_particles = Gtk.Entry()
        self.config_belief_number_particles.set_text("4")
        self.config_belief_grid.attach_next_to(self.config_belief_number_particles, self.config_belief_label1,
                                               Gtk.PositionType.RIGHT, 10, 1)

        ############################################

        self.config_belief_load = Gtk.Button(label="Load from File", margin=10)
        self.config_belief_load.connect("clicked", self.run_config_belief)
        self.config_belief_grid.attach(self.config_belief_load, 0, 2, 5, 1)

        self.config_belief_register = Gtk.Button(label="Register", margin=10)
        self.config_belief_register.connect("clicked", self.run_config_belief)
        self.config_belief_grid.attach_next_to(self.config_belief_register, self.config_belief_load,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_belief_save = Gtk.Button(label="Save to File", margin=10)
        self.config_belief_save.connect("clicked", self.run_config_belief)
        self.config_belief_grid.attach_next_to(self.config_belief_save, self.config_belief_register,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_belief_unregister = Gtk.Button(label="Unregister", margin=10)
        self.config_belief_unregister.connect("clicked", self.run_config_belief)
        self.config_belief_grid.attach_next_to(self.config_belief_unregister, self.config_belief_save,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_belief_load.set_sensitive(False)
        self.config_belief_save.set_sensitive(False)
        self.config_belief_unregister.set_sensitive(False)

        ############################################
        self.config_belief_grid.show_all()

        self.config_context_frame.add(self.config_belief_grid)
        ###########################################################################################################################################################################################

        ############################################################################################################################################################################################
        self.config_context_grid = Gtk.Grid(column_homogeneous=True, column_spacing=3, row_spacing=30)

        ############################################

        self.config_context_label0 = Gtk.Label(label="World Ontology:", margin=1)
        self.config_context_grid.attach(self.config_context_label0, 0, 0, 5, 1)

        self.config_context_ontology = Gtk.Entry()
        self.config_context_ontology.set_text("/naivphys4rp/belief_state/ontology/naivphys4rp.owl")
        self.config_context_grid.attach_next_to(self.config_context_ontology, self.config_context_label0,
                                               Gtk.PositionType.RIGHT, 10, 1)

        ############################################
        self.config_context_label1 = Gtk.Label(label="Language Model:", margin=1)
        self.config_context_grid.attach(self.config_context_label1, 0, 1, 5, 1)

        self.config_context_language = Gtk.Entry()
        self.config_context_language.set_text("/naivphys4rp/belief_state/ontology/naivphys4rp.lm")
        self.config_context_grid.attach_next_to(self.config_context_language, self.config_context_label1,
                                               Gtk.PositionType.RIGHT, 10, 1)

        ############################################
        self.config_context_label2 = Gtk.Label(label="Context Narrative Topic:", margin=1)
        self.config_context_grid.attach(self.config_context_label2, 0, 2, 5, 1)

        self.config_context_narrative_topic = Gtk.Entry()
        self.config_context_narrative_topic.set_text("/naivphys4rp/context_narrative")
        self.config_context_grid.attach_next_to(self.config_context_narrative_topic, self.config_context_label2,
                                                Gtk.PositionType.RIGHT, 10, 1)

        ############################################
        self.config_context_load = Gtk.Button(label="Load from File", margin=10)
        self.config_context_load.connect("clicked", self.run_config_context)
        self.config_context_grid.attach(self.config_context_load, 0, 3, 5, 1)

        self.config_context_register = Gtk.Button(label="Register", margin=10)
        self.config_context_register.connect("clicked", self.run_config_context)
        self.config_context_grid.attach_next_to(self.config_context_register, self.config_context_load,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_context_save = Gtk.Button(label="Save to File", margin=10)
        self.config_context_save.connect("clicked", self.run_config_context)
        self.config_context_grid.attach_next_to(self.config_context_save, self.config_context_register,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_context_unregister = Gtk.Button(label="Unregister", margin=10)
        self.config_context_unregister.connect("clicked", self.run_config_context)
        self.config_context_grid.attach_next_to(self.config_context_unregister, self.config_context_save,
                                               Gtk.PositionType.RIGHT, 5, 1)

        self.config_context_load.set_sensitive(False)
        self.config_context_save.set_sensitive(False)
        self.config_context_unregister.set_sensitive(False)

        ############################################
        self.config_context_grid.show_all()

        self.config_ontology_frame.add(self.config_context_grid)
        ###########################################################################################################################################################################################

        ##################################################################################################################

        ########################################## Adding imagination frame ##############################################
        self.movable_imagination_frame=Gtk.Frame()
        self.movable_imagination_frame.add(self.top_grid)
        self.setFrame.add_movable_frame("Belief State Imagination",self.movable_imagination_frame)

        ########################################## Adding augmentation frame ##############################################
        self.movable_augmentation_frame = Gtk.Frame()
        # self.movable_input_frame.add(self.top_grid)
        self.setFrame.add_movable_frame("Belief State Augmentation", self.movable_augmentation_frame)

        ######################################### Adding belief state frame ##############################################

        self.movable_belief_state_frame = Gtk.Frame()
        self.belief_top_grid = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.belief_control_frame = Gtk.Frame()
        self.bc_label = Gtk.Label(label="", margin=10)
        self.bc_label.set_markup("<b>Belief State - Controls</b>")
        self.belief_control_frame.set_label_widget(self.bc_label)
        self.belief_control_grid = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=50)

        self.belief_display_frame = ImaginationAreaFrame()
        self.bv_label = Gtk.Label(label="", margin=10)
        self.bv_label.set_markup("<b>Belief State - Visualization</b>")
        self.belief_display_frame.set_label_widget(self.bv_label)

        self.belief_control_button = Gtk.Button(label="Run Belief")
        self.belief_control_button.connect("clicked", self.run_belief)
        self.belief_control_grid.attach(self.belief_control_button, 0, 0, 1, 1)

        self.belief_check_cursor_viewpoint = Gtk.CheckButton(label="Thrid-Person View")
        self.belief_check_cursor_viewpoint.set_active(False)
        self.belief_check_cursor_viewpoint.connect("toggled", self.on_cursor_toggled)
        self.belief_control_grid.attach_next_to(self.belief_check_cursor_viewpoint, self.belief_control_button, Gtk.PositionType.RIGHT, 1, 1)

        self.belief_check_cursor_singleness = Gtk.CheckButton(label="Single View")
        self.belief_check_cursor_singleness.set_active(True)
        self.belief_check_cursor_singleness.connect("toggled", self.on_cursor_singleness_toggled)
        self.belief_control_grid.attach_next_to(self.belief_check_cursor_singleness, self.belief_check_cursor_viewpoint,
                                                Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_color0 = Gtk.RadioButton.new_with_label_from_widget(None, "Color RGB")
        self.belief_radio_mode_mask = Gtk.RadioButton.new_with_label_from_widget(self.belief_radio_mode_color0 , "Object Mask")
        self.belief_radio_mode_depth = Gtk.RadioButton.new_with_label_from_widget(self.belief_radio_mode_color0, "Scene Depth")
        self.belief_control_grid.attach(self.belief_radio_mode_color0, 0,4 , 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_mask, self.belief_radio_mode_color0,Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_depth, self.belief_radio_mode_mask,Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_color0.connect("toggled", self.change_sensor_modality)
        self.belief_radio_mode_mask.connect("toggled", self.change_sensor_modality)
        self.belief_radio_mode_depth.connect("toggled", self.change_sensor_modality)

        self.belief_radio_mode_category = Gtk.CheckButton(label="Category")
        self.belief_radio_mode_bounding_box = Gtk.CheckButton(label="Bounding Box")
        self.belief_radio_mode_pose =Gtk.CheckButton(label="6D Pose")
        self.belief_control_grid.attach(self.belief_radio_mode_category, 0, 8, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_bounding_box, self.belief_radio_mode_category,
                                                Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_pose, self.belief_radio_mode_bounding_box,
                                                Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_color = Gtk.CheckButton(label="Color")
        self.belief_radio_mode_shape = Gtk.CheckButton(label="Shape")
        self.belief_radio_mode_material = Gtk.CheckButton(label="Material")
        self.belief_control_grid.attach(self.belief_radio_mode_color, 0, 9, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_shape, self.belief_radio_mode_color,
                                                Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_material, self.belief_radio_mode_shape,
                                                Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_spatial_relation = Gtk.CheckButton(label="Spatial Relation")
        self.belief_radio_mode_mass = Gtk.CheckButton(label="Mass")
        self.belief_radio_mode_speed = Gtk.CheckButton(label="Speed")
        self.belief_control_grid.attach(self.belief_radio_mode_spatial_relation, 0, 10, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_mass, self.belief_radio_mode_spatial_relation,
                                                Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_speed, self.belief_radio_mode_mass,
                                                Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_real_image = Gtk.RadioButton.new_with_label_from_widget(None, "Real Image")
        self.belief_radio_mode_mental_image = Gtk.RadioButton.new_with_label_from_widget(self.belief_radio_mode_real_image,"Mental Image")

        self.belief_radio_mode_real_image.connect("toggled", self.change_belief_source)
        self.belief_radio_mode_mental_image.connect("toggled", self.change_belief_source)

        self.belief_control_grid.attach(self.belief_radio_mode_real_image, 0, 11, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_mental_image, self.belief_radio_mode_real_image,
                                                Gtk.PositionType.RIGHT, 1, 1)

        self.belief_radio_mode_real_motion = Gtk.RadioButton.new_with_label_from_widget(None, "Real Motion")
        self.belief_radio_mode_mental_motion = Gtk.RadioButton.new_with_label_from_widget(
            self.belief_radio_mode_real_motion, "Mental Motion")

        self.belief_radio_mode_real_motion.connect("toggled", self.change_motion_source)
        self.belief_radio_mode_mental_motion.connect("toggled", self.change_motion_source)

        self.belief_control_grid.attach(self.belief_radio_mode_real_motion, 0, 12, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_radio_mode_mental_motion, self.belief_radio_mode_real_motion,
                                                Gtk.PositionType.RIGHT, 1, 1)


        self.belief_brightness_label = Gtk.Label(label="Brightness: ")
        self.belief_brightness_label.set_justify(Gtk.Justification.LEFT)
        self.belief_contrast_label = Gtk.Label(label="Contrast: ")
        self.belief_contrast_label.set_justify(Gtk.Justification.LEFT)
        self.belief_brightness_adjustment = Gtk.Adjustment(value=0, lower=-100, upper=100, step_increment=1, page_increment=10, page_size=0)
        self.belief_contrast_adjustment = Gtk.Adjustment(value=10, lower=0, upper=30, step_increment=1, page_increment=5, page_size=0)
        self.belief_brightness_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.belief_brightness_adjustment)
        self.belief_contrast_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,adjustment=self.belief_contrast_adjustment)
        self.belief_contrast_scale.connect("value-changed", self.scale_changed)
        self.belief_brightness_scale.connect("value-changed", self.scale_changed)

        self.belief_control_grid.attach(self.belief_contrast_label, 0, 13, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_contrast_scale, self.belief_contrast_label,Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_brightness_label, self.belief_contrast_scale,Gtk.PositionType.RIGHT, 1, 1)
        self.belief_control_grid.attach_next_to(self.belief_brightness_scale, self.belief_brightness_label,Gtk.PositionType.RIGHT, 1, 1)


        self.belief_control_frame.add(self.belief_control_grid)

        self.belief_top_grid.attach(self.lsepartor_label, 0, 0, 1, 1)
        self.belief_top_grid.attach(self.rsepartor_label, 114, 0, 1, 1)
        self.belief_top_grid.attach(self.bsepartor_label, 0, 49, 1, 1)
        self.belief_top_grid.attach(self.belief_control_frame, 1, 0, 40, 95)
        self.belief_top_grid.attach(self.belief_display_frame, 41, 0, 72, 95)
        #self.top_grid.attach(self.imagination_frame, 41, 31, 72, 18)

        self.movable_belief_state_frame.add(self.belief_top_grid)
        self.setFrame.add_movable_frame("Belief State Anticipation (Prediction)", self.movable_belief_state_frame)
        ##################################################################################################################

        ########################################## Adding filtering frame ##############################################
        self.movable_filtering_frame = Gtk.Frame()
        self.setFrame.add_movable_frame("Belief State Filtering (Explanation)", self.movable_filtering_frame)

        self.config_separator01 = Gtk.Label(label="", margin=1)
        self.config_separator02 = Gtk.Label(label="", margin=1)
        self.config_separator03 = Gtk.Label(label="", margin=1)
        self.config_separator04 = Gtk.Label(label="", margin=1)
        self.config_separator05 = Gtk.Label(label="", margin=1)

        # Active/Passive Filtering - two images result/mask
        self.filtering_frame = ImaginationAreaFrame()
        self.filtering_label = Gtk.Label(label="", margin=10)
        self.filtering_label.set_markup("<b>Active / Passive Filtering</b>")
        self.filtering_frame.set_label_widget(self.filtering_label)

        # Status - Progess, state, output
        self.status_frame = Gtk.Frame()
        self.status_label = Gtk.Label(label="", margin=10)
        self.status_label.set_markup("<b>Status</b>")
        self.status_frame.set_label_widget(self.status_label)

        # Control Frame
        self.control_frame = Gtk.Frame()
        self.control_label = Gtk.Label(label="", margin=10)
        self.control_label.set_markup("<b>Control</b>")
        self.control_frame.set_label_widget(self.control_label)

        self.explanation_top_grid = Gtk.Grid(column_homogeneous=True, column_spacing=9, row_spacing=9)

        self.explanation_top_grid.attach(self.config_separator01, 0, 0, 1, 1)
        self.explanation_top_grid.attach(self.filtering_frame, 1, 0, 68, 60)
        self.explanation_top_grid.attach(self.config_separator02, 0, 61, 1, 1)
        self.explanation_top_grid.attach(self.status_frame, 1, 62, 68, 8)
        self.explanation_top_grid.attach(self.config_separator03, 0, 70, 1, 1)
        self.explanation_top_grid.attach(self.control_frame, 1, 71, 68,29)
        self.explanation_top_grid.attach(self.config_separator04, 69, 100, 1, 1)
        self.movable_filtering_frame.add(self.explanation_top_grid)


        #control frame
        ############################################
        self.control_grid = Gtk.Grid(column_homogeneous=True, column_spacing=400, row_spacing=20)


        self.control_run = Gtk.Button(label="Run", margin=1)
        self.control_run.connect("clicked", self.run_filtering)
        self.control_grid.attach(self.control_run, 0,0,1,1)

        self.control_reset = Gtk.Button(label="Reset", margin=1)
        self.control_reset.connect("clicked", self.run_filtering)
        self.control_grid.attach_next_to(self.control_reset, self.control_run,Gtk.PositionType.BOTTOM, 1, 1)

        self.active_button = Gtk.CheckButton(label="Active Filtering")
        self.active_button.set_active(True)
        self.active_button.connect("toggled", self.on_active_filtering_toggled)
        self.control_grid.attach_next_to(
            self.active_button, self.control_reset, Gtk.PositionType.BOTTOM, 1, 1
        )

        self.passive_button = Gtk.CheckButton(label="Passive Filtering")
        self.passive_button.set_active(False)
        self.passive_button.connect("toggled", self.on_active_filtering_toggled)
        self.control_grid.attach_next_to(
            self.passive_button, self.active_button, Gtk.PositionType.BOTTOM, 1, 1
        )

        self.control_feature_label = Gtk.Label(label="Select a feature:", margin=1)
        self.control_grid.attach_next_to(self.control_feature_label, self.control_run,
                                        Gtk.PositionType.RIGHT, 1, 1)

        self.control_feature_list = Gtk.ComboBoxText()
        self.feature_list = ["Contour", "Edge", "Bounding-Box", "Size", "Color", "Proximity", "Similarity", "Background", "Foreground", "Shape", "Material"]
        for i in range(len(self.feature_list)):
            self.control_feature_list.append_text(self.feature_list[i])
        self.control_feature_list.set_active(1)
        self.control_grid.attach_next_to(self.control_feature_list, self.control_feature_label,
                                              Gtk.PositionType.BOTTOM, 1, 1)

        self.control_add_filter = Gtk.Button(label="Add Filter", margin=1)
        self.control_add_filter.connect("clicked", self.add_filter)
        self.control_grid.attach_next_to(self.control_add_filter, self.active_button, Gtk.PositionType.RIGHT, 1, 1)

        self.control_parameterize_filter = Gtk.Button(label="Parameterize Filter", margin=1)
        self.control_parameterize_filter.connect("clicked", self.parameterize_filter)
        self.control_grid.attach_next_to(self.control_parameterize_filter, self.passive_button, Gtk.PositionType.RIGHT, 1, 1)

        self.control_list_feature_label = Gtk.Label(label="Select Minimal Transparent Features:", margin=1)
        self.control_grid.attach_next_to(self.control_list_feature_label, self.control_feature_label, Gtk.PositionType.RIGHT, 1, 1)

        self.control_feature_scrolledwindow = Gtk.ScrolledWindow()
        self.control_feature_tree = Gtk.TreeView()
        self.control_feature_frame = Gtk.Frame()
        self.control_feature_tree_store = Gtk.TreeStore(bool, str)

        self.selected_feature_list=["Contour", "Edge", "Bounding-Box", "Size", "Color", "Proximity", "Foreground", "Background"]

        self.control_feature_tree.set_model(self.control_feature_tree_store)
        for i in range(len(self.feature_list)):
            if self.feature_list[i] in self.selected_feature_list:
                self.control_feature_tree_store.append(None, [True, self.feature_list[i]])
            else:
                self.control_feature_tree_store.append(None, [False, self.feature_list[i]])
        # create a column
        self.control_feature_tree_column = Gtk.TreeViewColumn("Feature Selection", )
        self.control_feature_tree.append_column(self.control_feature_tree_column)
        # add a toggle render
        self.control_feature_tree_toggle = Gtk.CellRendererToggle()
        self.control_feature_tree_column.pack_start(self.control_feature_tree_toggle, True)
        self.control_feature_tree_column.add_attribute(self.control_feature_tree_toggle, "active", 0)
        self.control_feature_tree_column.set_clickable(True)
        self.control_feature_tree_toggle.connect('toggled', self.on_toggle,
                                                 self.control_feature_tree.get_model())
        # create a column
        self.control_feature_tree_column2 = Gtk.TreeViewColumn("Feature Name", )
        self.control_feature_tree.append_column(self.control_feature_tree_column2)
        # and add a text renderer to a second column
        text_ren2 = Gtk.CellRendererText()
        self.control_feature_tree_column2.pack_start(text_ren2, True)
        self.control_feature_tree_column2.add_attribute(text_ren2, "text", 1)
        # self.control_feature_tree.set_border_width(10)
        self.control_feature_scrolledwindow.add(self.control_feature_tree)
        self.control_feature_frame.add(self.control_feature_scrolledwindow)
        self.control_grid.attach_next_to(self.control_feature_frame, self.control_feature_list,
                                         Gtk.PositionType.RIGHT, 1, 3)

        self.control_grid.show_all()
        self.control_frame.add(self.control_grid)

        # status frame
        ############################################
        self.status_grid = Gtk.Grid(column_homogeneous=True, column_spacing=1, row_spacing=1)
        self.map_filtering_control_status_function = {}

        self.status_feature_label = Gtk.Label(label="Current Feature:", margin=1)
        self.status_grid.attach(self.status_feature_label, 0, 1, 25, 1)

        self.status_feature_value_label = Gtk.Label(label="", margin=1)
        self.status_feature_value_label.set_markup("<b>Not running!</b>")
        self.status_grid.attach_next_to(self.status_feature_value_label, self.status_feature_label,
                                        Gtk.PositionType.RIGHT, 25, 1)

        self.status_output_label = Gtk.Label(label="Current Output:", margin=1)
        self.status_grid.attach_next_to(self.status_output_label, self.status_feature_value_label,
                                        Gtk.PositionType.RIGHT, 25, 1)

        self.status_output_value_label = Gtk.Label(label="Not running!", margin=1)
        self.status_output_value_label.set_markup("<b>Not running!</b>")
        self.status_grid.attach_next_to(self.status_output_value_label, self.status_output_label,
                                        Gtk.PositionType.RIGHT, 25, 1)

        self.status_progress_label = Gtk.Label(label="Progress:", margin=1)
        self.status_grid.attach_next_to(self.status_progress_label, self.status_output_value_label,
                                        Gtk.PositionType.RIGHT, 25, 1)

        self.status_progress_value_label = Gtk.Label(label="0.0 %", margin=1)
        self.status_progress_value_label.set_markup("<b>0.0 %</b>")
        self.status_grid.attach_next_to(self.status_progress_value_label, self.status_progress_label,
                                        Gtk.PositionType.RIGHT, 25, 1)
        self.map_filtering_control_status_function['feature']=self.status_feature_value_label
        self.map_filtering_control_status_function['output']=self.status_output_value_label
        self.map_filtering_control_status_function['progress']=self.status_progress_value_label
        self.status_grid.show_all()

        self.status_frame.add(self.status_grid)

        ########################################## Adding VQA frame ##############################################
        self.movable_bqa_frame = Gtk.Frame()
        self.movable_bqa_frame_final = Gtk.Frame()
        # self.movable_input_frame.add(self.top_grid)

        self.plotter = None
        self.current_mesh = None
        self.plotter_thread = None
        self._plotter_ready_event = threading.Event()
        self._plotter_command_queue = queue.Queue()
        self._stop_plotter_thread = threading.Event()

        # --- Main Layout: Horizontal Box ---
        main_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.movable_bqa_frame_final.add(main_h_box)

        # --- NEW: Control Panel Frame ---
        self.movable_bqa_frame = Gtk.Frame(label="Controls")
        self.movable_bqa_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        self.movable_bqa_frame.set_size_request(200, -1)  # Set minimum width for the frame
        main_h_box.pack_start(self.movable_bqa_frame, False, False, 0)

        # --- Left Control Panel: Vertical Box (inside the frame) ---
        control_v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        control_v_box.set_border_width(10)  # Add some padding inside the frame
        self.movable_bqa_frame.add(control_v_box)  # Add the VBox to the frame

        # Load OBJ Button
        load_button = Gtk.Button(label="Load OBJ File")
        load_button.connect("clicked", self._on_load_obj_clicked)
        control_v_box.pack_start(load_button, False, False, 0)

        # Zoom Buttons (initially insensitive until plotter is ready)
        self.zoom_in_button = Gtk.Button(label="Zoom In")
        self.zoom_in_button.connect("clicked", self._on_zoom_in_clicked)
        self.zoom_in_button.set_sensitive(False)
        control_v_box.pack_start(self.zoom_in_button, False, False, 0)

        self.zoom_out_button = Gtk.Button(label="Zoom Out")
        self.zoom_out_button.connect("clicked", self._on_zoom_out_clicked)
        self.zoom_out_button.set_sensitive(False)
        control_v_box.pack_start(self.zoom_out_button, False, False, 0)

        # Separator for rotation controls
        control_v_box.pack_start(Gtk.Separator(), False, False, 5)

        # Rotation Buttons (initially insensitive until plotter is ready)
        self.rotate_x_button = Gtk.Button(label="Rotate X+")
        self.rotate_x_button.connect("clicked", lambda w: self._on_rotate_clicked("x", 15))
        self.rotate_x_button.set_sensitive(False)
        control_v_box.pack_start(self.rotate_x_button, False, False, 0)

        self.rotate_y_button = Gtk.Button(label="Rotate Y+")
        self.rotate_y_button.connect("clicked", lambda w: self._on_rotate_clicked("y", 15))
        self.rotate_y_button.set_sensitive(False)
        control_v_box.pack_start(self.rotate_y_button, False, False, 0)

        self.rotate_z_button = Gtk.Button(label="Rotate Z+")
        self.rotate_z_button.connect("clicked", lambda w: self._on_rotate_clicked("z", 15))
        self.rotate_z_button.set_sensitive(False)
        control_v_box.pack_start(self.rotate_z_button, False, False, 0)

        # Spacer to push controls to top
        control_v_box.pack_start(Gtk.Label(), True, True, 0)

        # --- Right 3D Viewer Placeholder ---
        placeholder_frame = Gtk.Frame(label="3D Viewer (Opens on File Load)")
        placeholder_frame.set_hexpand(True)
        placeholder_frame.set_vexpand(True)
        main_h_box.pack_start(placeholder_frame, True, True, 0)

        self.setFrame.add_movable_frame("Belief Question Answering (BQA)", self.movable_bqa_frame_final)

        ########################################## Adding Learning frame ##############################################
        self.movable_learning_frame = Gtk.Frame()
        # self.movable_input_frame.add(self.top_grid)
        self.setFrame.add_movable_frame("Self-supervised Learning", self.movable_learning_frame)

        #adding tab collector to main window
        self.add(self.setFrame)
        self.grid.show_all()
        self.top_grid.show_all()
        self.belief_top_grid.show_all()
        self.belief_control_grid.show_all()
        self.config_top_grid.show_all()
        self.explanation_top_grid.show_all()
        self.show_all()
        self.imaginator = Imagination(nb_cameras= self.Nb_Cameras)
        self.belief_radio_mode_real_image.set_active(self.imaginator.real_image)
        self.belief_radio_mode_real_motion.set_active(self.imaginator.real_motion)



    def add_filter(self, widget):
        pass
    def parameterize_filter(self, widget):
        pass
    def on_active_filtering_toggled(self, widget):
        pass
    
    def on_toggle(self,cell, path, model, *ignore):
        if path is not None:
            it = model.get_iter(path)
            model[it][0] = not model[it][0]
            if model[it][0]:
                if cell==self.config_motor_time_frame_tree_toggle:
                    self.imaginator.motor_manager.selected_motor_frames.append(model[it][1])
                else:
                    self.imaginator.motor_manager.selected_motor_joints.append(model[it][1])
            else:
                if cell==self.config_motor_time_frame_tree_toggle:
                    self.imaginator.motor_manager.selected_motor_frames.remove(model[it][1])
                else:
                    self.imaginator.motor_manager.selected_motor_joints.remove(model[it][1])
            print('Selected joints: ',self.imaginator.motor_manager.selected_motor_joints)
            print('Selected frames: ',self.imaginator.motor_manager.selected_motor_frames)


    def run_filtering(self, widget):
        global THREAD_RUN_FILTERING_KILLABLE
        if widget==self.control_run:
            THREAD_RUN_FILTERING_KILLABLE = False
            self.thread_run_filtering = Thread(target=self.run_filtering_spin, args=[])
            self.thread_run_filtering.daemon = True
            self.thread_run_filtering.start()
        else:
            THREAD_RUN_FILTERING_KILLABLE = True

    def scale_changed(self,widget):
        if widget==self.belief_contrast_scale:
            self.imaginator.contrast=self.belief_contrast_scale.get_value()/10.0
        else:
            self.imaginator.brightness=self.belief_brightness_scale.get_value()

    def getBaseName(self, lists):
        return [r.split(self.namespace).pop() for r in lists]
    def change_belief_source(self, widget):
        self.imaginator.real_image=self.belief_radio_mode_real_image.get_active()

    def change_motion_source(self, widget):
        self.imaginator.real_motion=self.belief_radio_mode_real_motion.get_active()
    def change_sensor_modality(self,widget):
        if self.belief_radio_mode_color0.get_active():
            self.imaginator.sensor_modality=0
        else:
            if self.belief_radio_mode_mask.get_active():
                self.imaginator.sensor_modality = 1
            else:
                self.imaginator.sensor_modality = 2

    def closest(self, s, l):
        l = list(l)
        s = s.lower().replace('_', '').replace(' ', '')
        res = l[0]
        dist = +np.Inf
        for r in l:
            re = r.lower().replace('_', '').replace(' ', '')
            d = self.distance(s, re)
            if d < dist:
                dist = d
                res = r
        return res


    def run_config_motor(self,widget):
        if widget==self.config_motor_register:
            self.imaginator.motor_manager.motor_model = self.config_robot_motor_model.get_active_text()
            self.imaginator.motor_manager.motor_joint_topic = self.config_motor_text_joint_state_topic.get_text()
            self.imaginator.motor_manager.motor_frame_topic = self.config_motor_text_time_frame_topic.get_text()
            self.imaginator.set_gui(self)
            self.imaginator.initialize_real_robot_motor()
            self.config_motor_unregister.set_sensitive(True)
            self.config_motor_register.set_sensitive(False)
        else:
            if widget==self.config_motor_unregister:
                self.config_motor_unregister.set_sensitive(False)
                self.config_motor_register.set_sensitive(True)

    def run_config_context(self, widget):
        if widget==self.config_context_register:
            self.config_context_unregister.set_sensitive(True)
            self.config_context_register.set_sensitive(False)

        else:
            if widget == self.config_context_unregister:
                self.config_context_unregister.set_sensitive(False)
                self.config_context_register.set_sensitive(True)

    def actualize_config_motor_frame(self):
        self.config_motor_time_frame_tree_store.clear()
        frames=list(set(list(self.imaginator.motor_manager.motor_frame_tree.keys())+list(self.imaginator.motor_manager.motor_frame_tree.values())))
        for frame in frames:
            self.config_motor_time_frame_tree_store.append(None, [True, frame])
            self.imaginator.motor_manager.selected_motor_frames.append(frame)

    def actualize_config_motor_joint(self):
        self.config_motor_time_joint_tree_store.clear()
        for joint in self.imaginator.motor_manager.motor_joint_tree.keys():
            self.config_motor_time_joint_tree_store.append(None, [True, joint])
            self.imaginator.motor_manager.selected_motor_joints.append(joint)
    def distance(self, str1, str2):
        m = SequenceMatcher(None, str1, str2).find_longest_match(0, len(str1), 0, len(str2))
        return len(str1) + len(str2) - 2 * m.size

    def parse_context(self, text):
        try:
            h=5
            parsing = self.json_parser.parse(text.lower())
            return (True, parsing, Transformers(self.state_verb).context(parsing))
        except Exception as e:
            print(e)
            return (False, str(e), [])
        """
        #reading grammar file
        with open(self.grammarFile, 'r') as infile:
            self.grammar = json.load(infile)
        infile.close()

        #writing grammar file
        with open(self.grammarFile, 'w') as infile:
            json.load(infile,self.grammar)
        infile.close()
        """

    def run_config_belief(self, widget):
        if widget == self.config_belief_register:
            self.config_belief_unregister.set_sensitive(True)
            self.config_belief_register.set_sensitive(False)

        else:
            if widget == self.config_belief_unregister:
                self.config_belief_unregister.set_sensitive(False)
                self.config_belief_register.set_sensitive(True)


    def run_config_sensor(self, widget):
        if widget == self.config_sensor_register:
            self.imaginator.camera_manager.color_cam_info_topic=self.config_sensor_text_cam_info_topic.get_text()
            self.imaginator.camera_manager.depth_cam_info_topic=self.config_sensor_text_depth_info_topic.get_text()
            self.imaginator.camera_manager.color_cam_data_topic=self.config_sensor_text_cam_data_topic.get_text()
            self.imaginator.camera_manager.depth_cam_data_topic=self.config_sensor_text_depth_data_topic.get_text()
            self.imaginator.camera_manager.color_cam_hint=self.config_sensor_text_color_hint.get_text()
            self.imaginator.camera_manager.depth_cam_hint=self.config_sensor_text_depth_hint.get_text()
            self.imaginator.camera_manager.cam_height=int(self.config_sensor_text_image_height.get_text())
            self.imaginator.camera_manager.cam_width=int(self.config_sensor_text_image_width.get_text())
            self.imaginator.camera_manager.cam_model=self.config_sensor_camera_model.get_active_text()
            self.imaginator.camera_manager.source_frame=self.config_sensor_text_source_frame.get_text()
            self.imaginator.camera_manager.destination_frame=self.config_sensor_text_destination_frame.get_text()
            self.imaginator.initialize_real_robot_camera()
            self.config_sensor_unregister.set_sensitive(True)
            self.config_sensor_register.set_sensitive(False)
        else:
            if widget == self.config_sensor_unregister:
                self.imaginator.camera_manager= CameraManager()
                self.config_sensor_text_cam_info_topic.set_text(self.imaginator.camera_manager.color_cam_info_topic)
                self.config_sensor_text_depth_info_topic.set_text(self.imaginator.camera_manager.depth_cam_info_topic)
                self.config_sensor_text_cam_data_topic.set_text(self.imaginator.camera_manager.color_cam_data_topic)
                self.config_sensor_text_depth_data_topic.set_text(self.imaginator.camera_manager.depth_cam_data_topic)
                self.config_sensor_text_color_hint.set_text(self.imaginator.camera_manager.color_cam_hint)
                self.config_sensor_text_depth_hint.set_text(self.imaginator.camera_manager.depth_cam_hint)
                self.config_sensor_text_image_height.set_text(str(self.imaginator.camera_manager.cam_height))
                self.config_sensor_text_image_width.set_text(str(self.imaginator.camera_manager.cam_width))
                self.config_sensor_camera_model.set_active(1)
                self.config_sensor_text_source_frame.set_text(self.imaginator.camera_manager.source_frame)
                self.config_sensor_text_destination_frame.set_text(self.imaginator.camera_manager.destination_frame)
                self.config_sensor_unregister.set_sensitive(False)
                self.config_sensor_register.set_sensitive(True)

    def create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.grid.attach(toolbar, 0, 0, 3, 1)

        button_bold = Gtk.ToolButton()
        button_bold.set_icon_name("format-text-bold-symbolic")
        toolbar.insert(button_bold, 0)

        button_italic = Gtk.ToolButton()
        button_italic.set_icon_name("format-text-italic-symbolic")
        toolbar.insert(button_italic, 1)

        button_underline = Gtk.ToolButton()
        button_underline.set_icon_name("format-text-underline-symbolic")
        toolbar.insert(button_underline, 2)

        button_bold.connect("clicked", self.on_button_clicked, self.tag_bold)
        button_italic.connect("clicked", self.on_button_clicked, self.tag_italic)
        button_underline.connect("clicked", self.on_button_clicked, self.tag_underline)

        toolbar.insert(Gtk.SeparatorToolItem(), 3)

        radio_justifyleft = Gtk.RadioToolButton()
        radio_justifyleft.set_icon_name("format-justify-left-symbolic")
        toolbar.insert(radio_justifyleft, 4)

        radio_justifycenter = Gtk.RadioToolButton.new_from_widget(radio_justifyleft)
        radio_justifycenter.set_icon_name("format-justify-center-symbolic")
        toolbar.insert(radio_justifycenter, 5)

        radio_justifyright = Gtk.RadioToolButton.new_from_widget(radio_justifyleft)
        radio_justifyright.set_icon_name("format-justify-right-symbolic")
        toolbar.insert(radio_justifyright, 6)

        radio_justifyfill = Gtk.RadioToolButton.new_from_widget(radio_justifyleft)
        radio_justifyfill.set_icon_name("format-justify-fill-symbolic")
        toolbar.insert(radio_justifyfill, 7)

        radio_justifyleft.connect(
            "toggled", self.on_justify_toggled, Gtk.Justification.LEFT
        )
        radio_justifycenter.connect(
            "toggled", self.on_justify_toggled, Gtk.Justification.CENTER
        )
        radio_justifyright.connect(
            "toggled", self.on_justify_toggled, Gtk.Justification.RIGHT
        )
        radio_justifyfill.connect(
            "toggled", self.on_justify_toggled, Gtk.Justification.FILL
        )

        toolbar.insert(Gtk.SeparatorToolItem(), 8)

        button_clear = Gtk.ToolButton()
        button_clear.set_icon_name("edit-clear-symbolic")
        button_clear.connect("clicked", self.on_clear_clicked)
        toolbar.insert(button_clear, 9)

        toolbar.insert(Gtk.SeparatorToolItem(), 10)

        button_search = Gtk.ToolButton()
        button_search.set_icon_name("system-search-symbolic")
        button_search.connect("clicked", self.on_search_clicked)
        toolbar.insert(button_search, 11)

    def create_textview(self):
        scrolledwindow = Gtk.ScrolledWindow()
        # scrolledwindow.set_min_content_height(50)
        # scrolledwindow.set_min_content_width(50)
        # scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 1, 4, 5)

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.context_template = json.loads(
            '{"who": {"type": "robot", "name":"PR2"}, "where": {"type": "location", "name": "kitchen"}, "what": {"type":"action", "name":"preparing", "object":"Breakfast"}, "why":{}, "how":{}, "when":{}}')

        self.textbuffer.set_text(
            json.dumps(self.context_template, indent=28, sort_keys=True)
        )
        scrolledwindow.add(self.textview)

        self.tag_bold = self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag(
            "underline", underline=Pango.Underline.SINGLE
        )
        self.tag_found = self.textbuffer.create_tag("found", background="yellow")

    def create_buttons(self):

        self.proceed_button = Gtk.Button(label="Run")
        self.proceed_button.connect("clicked", self.do_clicked)
        self.grid.attach(self.proceed_button, 0, 10, 1, 1)

        self.reset_button = Gtk.Button(label="Reset")
        self.reset_button.connect("clicked", self.do_clicked)
        self.grid.attach(self.reset_button, 0, 11, 1, 1)

        check_editable = Gtk.CheckButton(label="Editable")
        check_editable.set_active(True)
        check_editable.connect("toggled", self.on_editable_toggled)
        self.grid.attach(check_editable, 1, 10, 1, 1)

        check_cursor = Gtk.CheckButton(label="Thrid View")
        check_cursor.set_active(False)
        check_cursor.connect("toggled", self.on_cursor_toggled)
        self.grid.attach_next_to(
            check_cursor, check_editable, Gtk.PositionType.RIGHT, 1, 1
        )

        self.dynamic_button = Gtk.CheckButton(label="Dynamic")
        self.dynamic_button.set_active(True)
        self.dynamic_button.connect("toggled", self.on_dynamic_toggled)
        self.grid.attach_next_to(
            self.dynamic_button, check_cursor, Gtk.PositionType.RIGHT, 1, 1
        )

        self.autocorrect_button = Gtk.CheckButton(label="Auto-Correct")
        self.autocorrect_button.set_active(False)
        self.autocorrect_button.connect("toggled", self.on_autocorrect_toggled)
        self.grid.attach_next_to(
            self.autocorrect_button, self.dynamic_button, Gtk.PositionType.RIGHT, 1, 1
        )

        self.spinner = Gtk.Spinner()
        """
        self.imageFrame = Gtk.Frame()
        self.imageFrame.set_shadow_type(Gtk.ShadowType.IN)
        self.filename = "../../../resources/search.gif"
        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        self.transparent = self.pixbuf.add_alpha(True, 0xff, 0xff, 0xff)
        self.image = Gtk.Image.new_from_pixbuf(self.pixbuf)
        self.imageFrame.add(self.image)
        """
        self.grid.attach(self.spinner, 3, 0, 1, 1)
        # self.spinner.start()

        radio_wrapnone = Gtk.RadioButton.new_with_label_from_widget(None, "No Wrapping")
        self.grid.attach(radio_wrapnone, 1, 11, 1, 1)

        radio_wrapchar = Gtk.RadioButton.new_with_label_from_widget(
            radio_wrapnone, "Character Wrapping"
        )
        self.grid.attach_next_to(
            radio_wrapchar, radio_wrapnone, Gtk.PositionType.RIGHT, 1, 1
        )

        radio_wrapword = Gtk.RadioButton.new_with_label_from_widget(
            radio_wrapnone, "Word Wrapping"
        )
        self.grid.attach_next_to(
            radio_wrapword, radio_wrapchar, Gtk.PositionType.RIGHT, 1, 1
        )
        self.next_button = Gtk.Button(label="Next Graph")
        self.next_button.connect("clicked", self.do_clicked)
        self.next_button.set_sensitive(False)
        self.grid.attach_next_to(self.next_button,radio_wrapword, Gtk.PositionType.RIGHT, 1, 1)

        radio_wrapnone.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.NONE)
        radio_wrapchar.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.CHAR)
        radio_wrapword.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.WORD)
    def run_belief_spin(self):
        #global THREAD_RUN_BELIEF_KILLABLE
        #while not THREAD_RUN_BELIEF_KILLABLE:
        GLib.idle_add(self.update_belief)
        time.sleep(1. / self.observation_frequency)
        #self.thread_run_belief.join()


    def run_filtering_spin(self):
        GLib.idle_add(self.update_filtering)
        time.sleep(1. / self.observation_frequency)

    def update_belief(self):
        if not THREAD_RUN_BELIEF_KILLABLE:
            self.belief_display_frame.imagine(self.imaginator.merged_observe())
            self.belief_display_frame.redraw()
            self.belief_display_frame.area.queue_draw()
        else:
            self.belief_display_frame.forget()
            self.belief_display_frame.redraw()
            self.belief_display_frame.area.queue_draw()
        return (not THREAD_RUN_BELIEF_KILLABLE)

    def update_filtering(self):
        if not THREAD_RUN_FILTERING_KILLABLE:
            res=self.belief_filtering.run_pipeline()
            images=res[0]
            print(len(images),'rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr')
            status=res[1]
            for key in status.keys():
                self.map_filtering_control_status_function[key].set_markup("<b> "+status[key]+" </b>")
            self.filtering_frame.imagine(images)
            self.filtering_frame.redraw()
            self.filtering_frame.area.queue_draw()
        else:
            self.filtering_frame.forget()
            self.filtering_frame.redraw()
            self.filtering_frame.area.queue_draw()
        return (not THREAD_RUN_FILTERING_KILLABLE)


    def move_robot(self):
        global THREAD_KILLABLE
        wait_time=1/120.
        while not THREAD_KILLABLE:
            #self.imaginator.move_robot_right(steps=0.1)
            #self.imaginator.move_robot_left(steps=0.1)
            if RUN_GRASPING:
                if not self.imaginator.real_motion:
                    print('-----------------------------------------------------------------------------------------------------')
                    self.imaginator.move_robot_right(steps=0.1)
                    self.imaginator.move_robot_left(steps=0.1)
                    self.imaginator.move_robot_forward(steps=0.4)
                    self.imaginator.turn_robot_head_down(steps=0.6)
                    time.sleep(wait_time*200.)
                    self.imaginator.turn_robot_head_left(steps=0.3)
                    time.sleep(wait_time * 200.)
                    self.imaginator.turn_robot_left(steps=0.3)
                    time.sleep(wait_time * 200.)
                    self.imaginator.turn_robot_right(steps=0.3)
                    time.sleep(wait_time * 200.)
                    self.imaginator.turn_robot_head_up(steps=0.6)
                    self.imaginator.move_robot_backward(steps=0.4)
                    self.imaginator.turn_robot_head_right(steps=0.3)
                    time.sleep(wait_time)
                    """
                    self.imaginator.park_robot_arms()
                    time.sleep(wait_time)

                    self.imaginator.move_robot_forward(steps=10./200.)
                    time.sleep(wait_time)

                    self.imaginator.turn_robot_head_down(steps=np.pi/4.)
                    time.sleep(wait_time)

                    self.imaginator.turn_robot_left(steps=np.pi/18.)
                    time.sleep(wait_time)

                    self.imaginator.move_robot_forward(steps=10./200.)
                    time.sleep(wait_time)

                    self.imaginator.r_wrist_roll_joint(steps=np.pi/2.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=50.*np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_lift_joint(steps=20.*np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.r_upper_arm_roll_joint(steps=np.pi/2)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-np.pi/3.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=np.pi/18.)
                    time.sleep(wait_time)

                    self.imaginator.r_upper_arm_roll_joint(steps=np.pi/18.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_lift_joint(steps=-np.pi/6)
                    time.sleep(wait_time)
                    
                    #self.imaginator.r_elbow_flex_joint(steps=np.pi/90.)
                    #self.imaginator.r_shoulder_pan_joint(steps=np.pi/90.)
                    #time.sleep(wait_time)
    
                    #self.imaginator.r_elbow_flex_joint(steps=np.pi/90.)
                    #time.sleep(wait_time)
                    
                    self.imaginator.r_wrist_flex_joint(steps=-0.5*np.pi/45.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=4. * np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=np.pi/36.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.r_elbow_flex_joint(steps=3*np.pi / 180.)
                    time.sleep(wait_time)

                    self.imaginator.close_robot_right_gripper(steps=38*np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_lift_joint(steps=7*np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_pan_joint(steps=-13*np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.r_shoulder_lift_joint(steps=-np.pi/90.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=np.pi/180.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=np.pi*2./180.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=np.pi*4./180.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=np.pi * 10. / 180.)
                    time.sleep(wait_time)

                    self.imaginator.open_robot_right_gripper(steps=np.pi * 20. / 180.)
                    time.sleep(wait_time)

                    self.imaginator.initialize_robot_pose()
                    self.imaginator.initialize_robot_arms()
                    self.imaginator.initialize_robot_head()
                    self.imaginator.initialize_robot_grippers()
                    """
                else:
                    self.imaginator.act_from_real_robot()
                    time.sleep(wait_time)
            else:
                time.sleep(wait_time)



    def build_graph(self):
        # parse input context
        global THREAD_KILLABLE
        """
        self.CONTEXT['Joint_Graph'].append({})
        ACTUAL_INDEX=len(self.CONTEXT['Joint_Graph'])-1
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Creation_Date']=dt.timestamp(dt.now())
        self.imaginator.initialize_robot_pose()
        self.imaginator.park_robot_arms()
        data=0
        res = self.parse_context(self.text)
        text=self.text
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative']=text
        if res[0]:
            title0 = "\n 0. Input Context Description as Informal Narrative \n\n\n"
            result0 = text
            title1 = "\n\n\n 1. Syntactical Parsing of Context Description \n\n\n"
            result1 = res[1].pretty()
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']={ 'Tree': res[1]}
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Status']= True
            data = [title0, result0, title1, result1]
            GLib.idle_add(self.update_textview, data)
        else:
            title0 = "\n 0. Input Context Description as Informal Narrative \n\n\n"
            result0 = text
            title1 = "\n\n\n 1. Syntactical Parsing of Context Description \n\n\n"
            result1 = "\n\n\n Error(s) found: \n\n" + str(res[1])
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing'] = {'Tree': res[1]}
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Status']= False
            data = [title0, result0, title1, result1]
            GLib.idle_add(self.update_textview, data)
            self.spinner.stop()
            return
        if res[2] == []:
            self.textbuffer.set_text(str(res[1]))
            self.spinner.stop()
            return
        graph = res[2]
        graph.sort()
        graph = list(graph for graph, _ in itertools.groupby(graph))
        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")
        # symbol grounding

        self.symbol_grounding_table = {}
        prefix=0

        for n in range(len(graph)):
            rel0 = ''
            rel1 = ''
            rel2 = ''
            rel = graph[n].copy()
            if rel[0] not in self.symbol_grounding_table.keys():
                nearest=self.closest(rel[0], self.classes.keys())
                rel0=nearest.lower()
                self.symbol_grounding_table[nearest.lower()+ "_" + str(prefix + 0)] = self.classes[nearest]

            if rel[1] != self.state_verb:
                nearest_first_part=self.closest(rel[2], self.classes.keys())
                rel2=nearest_first_part.lower()
                self.symbol_grounding_table[nearest_first_part.lower()+ "_" + str(prefix + 2)] = self.classes[nearest_first_part]
                res = self.closest(rel[1], self.object_properties.keys())
                rel1=res.lower()
                self.symbol_grounding_table[res.lower()+ "_" + str(prefix + 1)] = self.object_properties[res]
            else:
                key = None
                rel2 = rel[2][:1].upper() + rel[2][1:]
                print("++++++++++++++++++++++++++++ ", rel2)
                for k in self.data_properties.keys():
                    if rel2 in self.property_io[k]:
                        key = k
                        break
                if key is None:
                    nearest=self.closest(rel[2], self.classes.keys())
                    rel2=nearest.lower()
                    self.symbol_grounding_table[nearest.lower()+ "_" + str(prefix + 2)] = self.classes[nearest]
                    nearest=self.closest(rel[1], self.object_properties.keys())
                    rel1=nearest.lower()
                    self.symbol_grounding_table[nearest.lower()+ "_" + str(prefix + 1)] = self.object_properties[nearest]
                else:
                    rel1=rel[1]
                    self.symbol_grounding_table[rel[1]+ "_" + str(prefix + 1)] = self.data_properties[key]
                    rel2=rel[2]
                    self.symbol_grounding_table[rel[2]+ "_" + str(prefix + 2)] = "owl:oneOf(rdfs:range(" + str(
                        self.data_properties[key]) + "))"

            rel = graph[n].copy()
            rel = [rel0 + "_" + str(prefix), rel1 + "_" + str(prefix + 1), rel2 + "_" + str(prefix + 2)]
            graph[n] = rel.copy()
            prefix += 3

        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table']=self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets']  = graph
        # Build String
        title2 = "\n 2. Grounding of Narrative Symbols in the Ontology \n\n\n"
        result2 = ""
        for elt in self.symbol_grounding_table.keys():
            result2 = result2 + elt + " ----> " + self.symbol_grounding_table[elt] + "\n\n"
        data = [title0, result0, title1, result1, title2, result2]
        GLib.idle_add(self.update_textview, data)
        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")

        title3 = "\n 3. Inferring action's participant roles and multiplicities \n\n\n"
        result3 = ""
        ################## Action's participant roles ########################################
        self.action_participants = {}
        for elt in self.symbol_grounding_table.keys():
            if self.symbol_grounding_table[elt] in list(self.actions.values()):
                self.action_participants[elt] = {}
                self.action_participants[elt]['type']='List_Actions'
            else:
                if self.symbol_grounding_table[elt] in list(self.object_properties.values()):
                    self.action_participants[elt] = {}
                    self.action_participants[elt]['type'] = 'Object_Properties'
                else:
                    if self.symbol_grounding_table[elt] in list(self.data_properties.values()):
                        self.action_participants[elt] = {}
                        self.action_participants[elt]['type'] = 'Data_Properties'
                    else:
                        continue

            goal = KBListParticipantGoal()
            results = KBListParticipantResult()
            class_name= self.symbol_grounding_table[elt].split(self.namespace).pop()
            if self.action_participants[elt]['type'] != 'List_Actions':
                class_name=class_name.replace('_', ' ').title().replace(' ', '_')
            goal.class_name=class_name
            goal.namespace = self.namespace
            self.list_participant_client.send_goal(goal)
            self.list_participant_client.wait_for_result()
            results = self.list_participant_client.get_result()
            self.action_participants[elt]['role'] = []
            self.action_participants[elt]['multiplicity'] = []
            self.action_participants[elt]['participant'] = {}
            result3 = result3 + "\n" + elt + " -------------------------------\n\n"
            for i in range(len(results.classes)):
                if (results.classes[i].split(self.namespace).pop() not in self.action_participants[elt]['role']) and (len(results.classes[i].split(self.generic_class_prefix)) < 2):
                    self.action_participants[elt]['role'].append(results.classes[i].split(self.namespace).pop())
                    self.action_participants[elt]['multiplicity'].append(results.multiplicity[i])
                    result3 = result3 + results.multiplicity[i] + " --> " + results.classes[i] + "\n\n"



        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Action_Participants']=self.action_participants
        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")

        data = [title0, result0, title1, result1, title2, result2, title3, result3]
        GLib.idle_add(self.update_textview, data)

        title4 = "\n 4. Inferring potential role players in an action \n\n\n"
        result4 = ""
        ################## Action's participant roles ########################################
        self.action_radical_map={}
        for elt in self.action_participants.keys():
            result4 = result4 + "\n * " + elt + " ---------------------------------- \n\n"
            print('4.1.********************************************************************',elt)

            elt_radical=elt.split('_')
            elt_radical.pop()
            elt_radical='_'.join(elt_radical)

            if elt_radical in self.action_radical_map.keys():
                self.action_participants[elt]=self.action_participants[self.action_radical_map[elt_radical]].copy()
                continue
            else:
                self.action_radical_map[elt_radical]=elt
            for role in self.action_participants[elt]['role']:
                print('4.2.********************************************************************', elt,role)
                self.action_participants[elt]['participant'][role] = []
                result4 = result4 + "   +" + self.action_participants[elt]['multiplicity'][
                    self.action_participants[elt]['role'].index(role)] + " " + role + "\n\n"
                if role not in self.roles.keys():
                    continue
                for object in self.roles[role]['object']:
                    print('4.3.********************************************************************', elt, role, object)
                    class_name = self.symbol_grounding_table[elt].split(self.namespace).pop().title()
                    if class_name in self.action_object_role[role][object]['action']:
                        self.action_participants[elt]['participant'][role].append(object)
                        result4 = result4 + "       -" + self.classes[object] + "\n\n"

        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Action_Participants'] = self.action_participants
        print("------------------------------------------------------------------------------------------------")
        print(self.CONTEXT)
        print("-------------------------------------------------------------------------------------------------")

        data=[title0 , result0 , title1 , result1 , title2 , result2 , title3 , result3 , title4 , result4]
        GLib.idle_add(self.update_textview, data)

        ########################################## Building initial Graph #############################################################

        self.final_graph=[]
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets_To_Graph']={}

        for rel in graph:

            rel0=self.symbol_grounding_table[rel[0]].split(self.namespace).pop().lower()+'_'+rel[0].split('_').pop()
            rel0=rel0.title()
            rel1 = self.symbol_grounding_table[rel[1]].split(self.namespace).pop().lower() + '_' + rel[1].split('_').pop()
            if(self.symbol_grounding_table[rel[1]] in list(self.data_properties.values())):
                rel2 = rel[2].title()
            else:
                rel2 = self.symbol_grounding_table[rel[2]].split(self.namespace).pop().lower() + '_' + rel[2].split('_').pop()
                rel2=rel2.title()

            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets_To_Graph'][rel0]=rel[0]
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets_To_Graph'][rel1]=rel[1]
            self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets_To_Graph'][rel2]=rel[2]

            self.final_graph.append([rel0,rel1,rel2])

        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree']=self.final_graph
        print(self.CONTEXT)

        ########################################## ID resolution #############################################################

        title5 = "\n 5. ID resolution of similar concepts \n\n\n"
        result5 = ""
        self.dict_id={}
        for i in range(len(self.final_graph)):

            rel0,rel1,rel2=self.final_graph[i]

            key=rel0.split('_')
            key.pop()
            key='_'.join(key)
            if key not in self.dict_id.keys():
                self.dict_id[key] = rel0
            else:
                result5 = result5 + "\n * " + rel0 + " == " + self.dict_id[key] + "\n\n"
            self.final_graph[i][0]=self.dict_id[key]


            key = rel2.split('_')
            key.pop()
            key = '_'.join(key)
            if key not in self.dict_id.keys():
                self.dict_id[key] = rel2
            else:
                result5 = result5 + "\n * " + rel2 + " == " + self.dict_id[key] + "\n\n"
            self.final_graph[i][2] = self.dict_id[key]


        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution']=self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5]
        GLib.idle_add(self.update_textview, data)
        print(self.CONTEXT)

        ########################################## Resolving conceptual relations #############################################################

        self.class_equivalence = {"Breakfast": ["Milk", "Muesli"], "Robot": ["Machine"], "Cup": ["Mug"],
                                  "CookTable": ["Island"]}

        title6 = "\n 6. Refining definitions of concepts \n\n\n"
        result6 = ""

        goal = KBClassConstituentGoal()

        self.new_dict_id=self.dict_id.copy()
        for key in self.dict_id.keys():
            if self.symbol_grounding_table[self.new_dict_id[key].lower()] in list(self.classes.values()):
                goal.class_name = self.symbol_grounding_table[self.new_dict_id[key].lower()].split(self.namespace).pop()
                self.list_part_client.send_goal(goal)
                self.list_part_client.wait_for_result()
                results = self.list_part_client.get_result()
                if self.symbol_grounding_table[self.new_dict_id[key].lower()].split(self.namespace).pop() in self.roles['Ingredient']['object'] or key in self.action_participants.keys():
                    ENTITY_STATE='SOFT'
                else:
                    ENTITY_STATE='HARD'
                for part in results.classes:
                    if len(part.split(self.generic_class_prefix)) < 2 and len(part.split(self.namespace)) >= 2:

                        n=len(self.symbol_grounding_table.keys())
                        self.symbol_grounding_table[(part.split(self.namespace).pop()+'_'+str(n)).lower()]=part
                        n+=1
                        self.symbol_grounding_table[(self.aggregation_relations[ENTITY_STATE] + '_' + str(n)).lower()] = self.namespace+(self.aggregation_relations[ENTITY_STATE].title())
                        #if self.aggregation_relations[ENTITY_STATE] not in self.new_dict_id.keys():
                        #   self.new_dict_id[self.aggregation_relations[ENTITY_STATE]]=self.aggregation_relations[ENTITY_STATE] + '_' + str(n)

                        if part.split(self.namespace).pop() not in self.new_dict_id.keys():
                            self.new_dict_id[part.split(self.namespace).pop()] = part.split(self.namespace).pop()+'_'+str(n)

                        elt=[self.new_dict_id[key], (self.aggregation_relations[ENTITY_STATE] + '_' + str(n)).lower(), self.new_dict_id[part.split(self.namespace).pop()]]
                        self.final_graph.append(elt.copy())
                        result6 = result6 + "\n * " + elt[0] + "  " +elt[1]+" "+elt[2]+" \n\n"
                self.dict_id = self.new_dict_id.copy()

        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table']=self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree']=self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution']=self.dict_id

        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5,result5, title6,result6]
        GLib.idle_add(self.update_textview, data)
        print(self.CONTEXT)

        #Splitting implicit events into explicit ones

        title7 = "\n 7. Splitting implicit events into explicit ones \n\n\n"
        result7 = ""

        self.new_final_graph = []
        self.new_dict_id = self.dict_id.copy()
        self.processed_relations=[]
        for action in self.action_participants.keys():
            print("********************************************** 1 ****************************************")
            if self.action_participants[action]['type']=='List_Actions':
                print("********************************************** 1 ****************************************")
                self.participant_tracker={}
                for i  in range(len(self.final_graph)):
                    print("********************************************** 1 ****************************************")
                    rel=self.final_graph[i]
                    print(action, rel[1])
                    print(self.symbol_grounding_table[action].split(self.namespace).pop().lower()+'_'+action.split('_').pop(),rel[1])
                    if rel[1]==(self.symbol_grounding_table[action].split(self.namespace).pop().lower()+'_'+action.split('_').pop()):
                        print("********************************************** 2 ****************************************")
                        #splitting the relation into two relations
                        subject_participant=rel[0]
                        object_participant=rel[2]
                        #identify roles
                        role_found1=0
                        role_found2=0
                        concept1 = self.symbol_grounding_table[subject_participant.lower()].split(self.namespace).pop()
                        concept2 = self.symbol_grounding_table[object_participant.lower()].split(self.namespace).pop()
                        for role in self.action_participants[action]['role']:
                            if concept1 in self.action_participants[action]['participant'][role]:
                                print("********************************************** 3 ****************************************")
                                rel0=rel[0]
                                n=len(self.symbol_grounding_table.keys())
                                rel1=self.CONTEXT['List_Roles'][role]['action_relation'][0]+'_'+str(n)
                                self.symbol_grounding_table[rel1]=self.namespace+self.CONTEXT['List_Roles'][role]['action_relation'][0]
                                rel2=self.symbol_grounding_table[action].split(self.namespace).pop()+'_'+action.split('_').pop()
                                if rel2 not in list(self.new_dict_id.values()):
                                    self.new_dict_id[self.symbol_grounding_table[action].split(self.namespace).pop()]=rel2
                                self.new_final_graph.append([rel0,rel1,rel2])
                                result7 = result7 + "\n * " + rel0 + "  " + rel1+ "  " + rel2 + " \n\n"
                                role_found1+=1
                                if role in self.participant_tracker.keys():
                                    self.participant_tracker[role].append([rel0,[rel0,rel1,rel2]])
                                else:
                                    self.participant_tracker[role]=[[rel0, [rel0, rel1, rel2]]]

                        if role_found1<1:
                            result7 = result7 + "\n * Semantic Error(s): \n\n"
                            result7 = result7 + "\n * "+subject_participant+" cannot play a role in "+action+"!!! \n\n"
                            data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                    title5, result5,
                                    title6, result6, title7, result7]
                            GLib.idle_add(self.update_textview, data)
                            self.update_ontology_frame([],[])
                            return

                        for role in self.action_participants[action]['role']:
                            print("********************************************** 4 ****************************************")
                            if concept2 in self.action_participants[action]['participant'][role]:
                                rel0 = rel[2]
                                n = len(self.symbol_grounding_table.keys())
                                rel1 = self.CONTEXT['List_Roles'][role]['action_relation'][0] + '_' + str(n)
                                self.symbol_grounding_table[rel1] = self.namespace + self.CONTEXT['List_Roles'][role]['action_relation'][0]
                                rel2 = self.symbol_grounding_table[action].split(self.namespace).pop() + '_' + action.split('_').pop()
                                if rel2 not in list(self.new_dict_id.values()):
                                    self.new_dict_id[self.symbol_grounding_table[action].split(self.namespace).pop()] = rel2
                                self.new_final_graph.append([rel0, rel1, rel2])
                                result7 = result7 + "\n * " + rel0 + "  " + rel1 + "  " + rel2 + " \n\n"
                                role_found2 += 1
                                if role in self.participant_tracker.keys():
                                    self.participant_tracker[role].append([rel0,[rel0,rel1,rel2]])
                                else:
                                    self.participant_tracker[role]=[[rel0, [rel0, rel1, rel2]]]
                        if role_found2 < 1:
                            result7 = result7 + "\n * Semantic Error(s): \n\n"
                            result7 = result7 + "\n * " + object_participant + " cannot play a role in " + action + "!!! \n\n"
                            data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                    title5, result5,
                                    title6, result6, title7, result7]
                            GLib.idle_add(self.update_textview, data)
                            self.update_ontology_frame([],[])
                            return
                        self.processed_relations.append(rel.copy())
                    else:
                        pass

                for role in self.participant_tracker.keys():
                    #remove useless relations
                    index=self.action_participants[action]['role'].index(role)
                    multiplicity= self.action_participants[action]['multiplicity'][index]
                    if multiplicity == 'some':
                        multiplicity=len(self.action_participants[action]['participant'][role])
                    else:
                        multiplicity=int(multiplicity)
                    if len(self.participant_tracker[role])>multiplicity:
                        nb_removals=len(self.participant_tracker[role])-multiplicity
                        for couple in self.participant_tracker[role]:
                            for cont_role in self.participant_tracker.keys():
                                if cont_role==role:
                                    continue
                                cindex = self.action_participants[action]['role'].index(cont_role)
                                cmultiplicity = self.action_participants[action]['multiplicity'][cindex]
                                if cmultiplicity == 'some':
                                    cmultiplicity = len(self.action_participants[action]['participant'][role])
                                else:
                                    cmultiplicity = int(cmultiplicity)
                                for part in self.participant_tracker[cont_role]:
                                    #remove the second condition to strenghten the process
                                    if part[0]==couple[0] and len(self.participant_tracker[cont_role])-1<cmultiplicity:
                                        #remove that useless relation from tracker and final graph
                                        self.participant_tracker[role].remove(couple)
                                        self.new_final_graph.remove(couple[1])
                                        nb_removals -= 1
                                        break
                                if nb_removals <= 0:
                                    break
                            if nb_removals <= 0:
                                break
        for rel in self.final_graph:
            if rel not in self.processed_relations:
                self.new_final_graph.append(rel)
        self.final_graph=self.new_final_graph.copy()
        self.dict_id=self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id

        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5,
                title6, result6, title7, result7]
        GLib.idle_add(self.update_textview, data)

        ########################################## Completing actions' participants #############################################################

        title8 = "\n 8. Completing actions's participants \n\n\n"
        result8 = ""

        self.new_final_graph=self.final_graph.copy()
        self.new_dict_id=self.dict_id.copy()
        self.list_object_subject=[]
        self.radical_list_object_subject = []
        #collecting all objects and subjects
        for rel in self.final_graph:

            rel0 = rel[0].split('_')
            rel0.pop()
            rel0 = '_'.join(rel0)
            if rel[0] not in self.list_object_subject:
                self.list_object_subject.append(rel[0])
                self.radical_list_object_subject.append(rel0)

            rel2 = rel[2].split('_')
            rel2.pop()
            rel2 = '_'.join(rel2)
            if rel[2] not in self.list_object_subject:
                self.list_object_subject.append(rel[2])
                self.radical_list_object_subject.append(rel2)

        for action in self.action_participants.keys():
            print('8.1---------------------------------------------------------', action)
            if self.action_participants[action]['type']!='List_Actions':
                continue
            action_root=self.symbol_grounding_table[action].split(self.namespace).pop()
            final_action_root=action_root+'_'+(action.split('_').pop())
            for i in range(len(self.action_participants[action]['role'])):
                print('8.2---------------------------------------------------------', action,self.action_participants[action]['role'][i])
                role=self.action_participants[action]['role'][i]
                multiplicity = self.action_participants[action]['multiplicity'][i]
                participants=self.action_participants[action]['participant'][role].copy()
                found_participant=[]
                found_potential_participant=[]
                print('8.2.1.------------------------------------', multiplicity, action_root, final_action_root)
                for rel in self.new_final_graph:
                    print('8.3---------------------------------------------------------', action,role,rel)
                    print('8.3.1.------------------------------------',final_action_root, rel[2])

                    rel0 = rel[0].split('_')
                    rel0.pop()
                    rel0 = '_'.join(rel0)
                    if rel0 in participants:
                        if final_action_root==rel[2]:
                            if rel0 not in found_participant:
                                found_participant.append(rel0)
                        else:
                            if rel0 not in found_potential_participant:
                                found_potential_participant.append(rel0)

                    rel2 = rel[2].split('_')
                    rel2.pop()
                    rel2 = '_'.join(rel2)
                    if rel2 in participants:
                        if rel2 not in found_participant and rel2 not in found_potential_participant:
                            found_potential_participant.append(rel2)

                    print('8.3.2.------------------------------------', final_action_root, rel[2])
                au_multiplicity=multiplicity
                if multiplicity == 'some':
                    multiplicity=len(self.action_participants[action]['participant'][role])
                else:
                    multiplicity=int(multiplicity)
                print('8.2.2.------------------------------------', multiplicity, role, final_action_root, rel[2])
                sample_probability=self.role_player_participant_probability
                sample_representativeness=self.role_player_participant_representativeness
                count=1
                steps=0.1
                actual_multiplicity=multiplicity
                if len(found_participant) >= actual_multiplicity:
                    continue #noting to say
                else:
                    if actual_multiplicity-len(found_participant)>len(found_potential_participant):
                        take_these_participants=found_potential_participant.copy()
                    else:
                        shuffle(found_potential_participant) #randomize and only take the necessary
                        take_these_participants=found_potential_participant[:actual_multiplicity-len(found_participant)]
                    #set the potential participants as participants
                    for participant in take_these_participants:
                        n = len(self.symbol_grounding_table.keys())
                        new_action = self.CONTEXT['List_Roles'][role]['action_relation'][0] + '_' + str(n)
                        self.symbol_grounding_table[new_action] = self.namespace + self.CONTEXT['List_Roles'][role]['action_relation'][0]
                        final_participant = self.new_dict_id[participant]
                        self.symbol_grounding_table[final_participant] = self.namespace + participant
                        self.new_final_graph.append([final_participant, new_action, final_action_root])
                        result8 = result8 + "\n * " + final_participant + "  " + new_action + " " + final_action_root + " \n\n"
                        print('8.6.2.------------------------------------')
                    #add these to found participants
                    found_participant+=take_these_participants.copy()

                    if len(found_participant) < actual_multiplicity:
                        not_found=True
                        while not_found:
                            print('8.4---------------------------------------------------------', action,role,rel,actual_multiplicity)
                            for participant in participants:
                                print('8.5---------------------------------------------------------', action,role,rel,actual_multiplicity, participant)
                                if (participant not in found_participant) or (len(found_participant)>=len(participants)):
                                    if random.random()<=sample_probability:
                                        # adding a new relation
                                        print('8.5.1.------------------------------------', actual_multiplicity, participant)
                                        n = len(self.symbol_grounding_table.keys())
                                        new_action = self.CONTEXT['List_Roles'][role]['action_relation'][0] + '_' + str(n)
                                        self.symbol_grounding_table[new_action] = self.namespace + self.CONTEXT['List_Roles'][role]['action_relation'][0]
                                        if participant not in self.new_dict_id.keys():
                                            n = len(self.symbol_grounding_table.keys())
                                            final_participant=participant+'_'+str(n)
                                            self.new_dict_id[participant] = final_participant
                                        else:
                                            final_participant = self.new_dict_id[participant]
                                        self.symbol_grounding_table[final_participant] = self.namespace + participant
                                        self.new_final_graph.append([final_participant, new_action, final_action_root])
                                        result8 = result8 + "\n * " + final_participant + "  "+new_action+" " + final_action_root + " \n\n"
                                        actual_multiplicity += 1
                                        found_participant.append(participant)
                                        print('8.5.2.------------------------------------', actual_multiplicity, participant)

                                if actual_multiplicity >= multiplicity:
                                    not_found = False
                                    break
                            sample_probability+=steps
                            if actual_multiplicity>len(participants)*sample_representativeness and au_multiplicity=='some':
                                break



        self.final_graph = self.new_final_graph.copy()
        self.dict_id=self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5, title6, result6, title7, result7, title8, result8]
        GLib.idle_add(self.update_textview, data)

        ################################################# Closing co-reference resolution ####################################################################

        title9 = "\n 9. Closing co-reference resolution \n\n\n"
        result9 = ""

        target_objects={}
        list_synonym={}
        self.new_final_graph=self.final_graph.copy()
        self.new_dict_id=self.dict_id.copy()
        goal=KBClassSynonymGoal()


        for rel in self.final_graph:
            first_participant=rel[0]
            first_participant=first_participant.split('_')
            first_participant.pop()
            first_participant='_'.join(first_participant)

            second_participant=rel[2]
            second_participant=second_participant.split('_')
            second_participant.pop()
            second_participant='_'.join(second_participant)

            if first_participant in self.classes.keys():
                if first_participant in target_objects.keys():
                    target_objects[first_participant].append(rel.copy())
                else:
                    target_objects[first_participant]=[]

            if second_participant in self.classes.keys():
                if second_participant in target_objects.keys():
                    target_objects[second_participant].append(rel.copy())
                else:
                    target_objects[second_participant]=[rel.copy()]

        for participant in target_objects.keys():
            goal.class_name=participant
            self.list_synonym_client.send_goal(goal)
            self.list_synonym_client.wait_for_result()
            results = self.list_synonym_client.get_result()
            for cls in results.classes:
                if len(cls.split(self.generic_class_prefix)) < 2 and len(cls.split(self.namespace)) >= 2:
                    synonym=cls.split(self.namespace).pop()
                    if synonym in target_objects.keys():
                        intersection=[x for x in target_objects[participant] if x in target_objects[synonym]]
                        if intersection!=[]:
                            pass
                        else:
                            if participant in list_synonym.keys():
                                list_synonym[participant].append(synonym)
                            else:
                                list_synonym[participant]=[synonym]
                    else:
                        pass
                else:
                    pass

        for participant in list_synonym.keys():
            #self.new_dict_id.pop(participant, None)
            for i in range(len(self.new_final_graph)):
                if self.new_final_graph[i][0]==self.dict_id[participant]:
                    self.new_final_graph[i][0]=self.dict_id[list_synonym[participant][0]]
                    result9 = result9 + "\n * " + self.dict_id[participant] + "  " + self.state_verb + " " + self.dict_id[list_synonym[participant][0]] + " \n\n"
                if self.new_final_graph[i][2]==self.dict_id[participant]:
                    self.new_final_graph[i][2]=self.dict_id[list_synonym[participant][0]]
                    result9 = result9 + "\n * " + self.dict_id[participant] + "  " + self.state_verb + " " + self.dict_id[list_synonym[participant][0]] + " \n\n"
        self.final_graph = self.new_final_graph.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5,
                title6, result6, title7, result7, title8, result8, title9, result9]
        GLib.idle_add(self.update_textview, data)

        ################################################# Closing co-reference resolution ####################################################################

        title10 = "\n 10. Resolving containment relationships among objects \n\n\n"
        result10 = ""

        self.new_final_graph=self.final_graph.copy()
        self.new_dict_id=self.dict_id.copy()

        self.list_object_subject = []
        self.radical_list_object_subject = []
        self.containment={}
        self.containment_relation=[]
        self.containment_relation_support=[]
        self.containment_relation_container=[]
        for role in self.containment_disposition.keys():
            self.containment_relation+=self.containment_disposition[role].copy()
            self.containment_relation+=self.roles[role]['object_relation']
        # collecting all objects and subjects
        for rel in self.final_graph:

            rel0 = rel[0].split('_')
            rel0.pop()
            rel0 = '_'.join(rel0)
            if rel0 in self.classes.keys() and rel[0] not in self.list_object_subject:
                self.list_object_subject.append(rel[0])
                self.radical_list_object_subject.append(rel0)

            rel2 = rel[2].split('_')
            rel2.pop()
            rel2 = '_'.join(rel2)
            if rel2 in self.classes.keys() and rel[2] not in self.list_object_subject:
                self.list_object_subject.append(rel[2])
                self.radical_list_object_subject.append(rel2)

            rel1 = rel[1].split('_')
            rel1.pop()
            rel1 = '_'.join(rel1)

            if rel1 in self.containment_relation:
                if rel0 in self.containment.keys():
                    self.containment[rel0].append(rel2)
                else:
                    self.containment[rel0]=[rel2]
        self.new_containment=self.containment.copy()
        for obj in self.containment.keys():
            for cont_obj in self.containment[obj]:
                disposition=list(self.containment_disposition.keys())[0]
                disposition_found=False
                for disp in self.containment_disposition.keys():
                    if cont_obj in self.roles[disp]['object']:
                        disposition=disp
                        disposition_found=True
                        break
                if not disposition_found:
                    result10 = result10 + "\n * " + obj + "  cannot be contained or supported by " + cont_obj + " \n\n"
                    data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                            title5, result5,
                            title6, result6, title7, result7, title8, result8, title9, result9, title10, result10]
                    GLib.idle_add(self.update_textview, data)
                    self.update_ontology_frame([], [])
                    return

                if obj in self.action_object_role[disposition][cont_obj]['object']:
                    continue
                pos_conts=[]
                pos_conts_exist=[]
                for pos_cont in self.action_object_role[disposition][cont_obj]['object']:
                    pos_disposition = list(self.containment_disposition.keys())[0]
                    pos_disposition_found=False
                    for pos_disp in self.containment_disposition.keys():
                        if pos_cont in self.roles[pos_disp]['object']:
                            pos_disposition = pos_disp
                            pos_disposition_found=True
                            break
                    if not pos_disposition_found:
                        continue
                    if obj in self.action_object_role[pos_disposition][pos_cont]['object']:
                        if pos_cont in self.radical_list_object_subject:
                            if pos_cont not in self.new_containment.keys() or (pos_cont  in  self.new_containment.keys() and cont_obj not in self.new_containment[pos_cont]):
                                pos_conts_exist.append(pos_cont)
                            else:
                                continue
                        else:
                            pos_conts.append(pos_cont)
                if pos_conts_exist!=[]:
                    new_container=pos_conts_exist[int(np.round(random.random()*(len(pos_conts_exist)-1)))]
                else:
                    if pos_conts!=[]:
                        new_container=pos_conts[int(np.round(random.random()*(len(pos_conts)-1)))]
                    else:
                        result10 = result10 + "\n * " + obj + "  cannot be contained or supported by " + cont_obj + " \n\n"
                        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                title5, result5,
                                title6, result6, title7, result7, title8, result8, title9, result9, title10, result10]
                        GLib.idle_add(self.update_textview, data)
                        self.update_ontology_frame([], [])
                        return

                new_disposition = list(self.containment_disposition.keys())[0]
                new_disposition_found=False
                for new_disp in self.containment_disposition.keys():
                    if new_container in self.roles[new_disp]['object']:
                        new_disposition = new_disp
                        new_disposition_found=True
                        break
                found_one_party=0
                if new_container in self.radical_list_object_subject:
                    if new_container in self.new_containment[obj]:
                        if new_container in self.new_containment.keys() and cont_obj in self.new_containment[new_container]:
                            continue
                        found_one_party=1
                    else:
                        if new_container in self.new_containment.keys() and cont_obj in self.new_containment[new_container]:
                            found_one_party=2
                    cont_index=self.radical_list_object_subject.index(new_container)
                    new_container_final=self.list_object_subject[cont_index]

                else:
                    n=len(self.symbol_grounding_table.keys())
                    new_container_final=new_container+'_'+str(n)
                    self.symbol_grounding_table[new_container_final]=self.namespace+new_container
                    self.new_dict_id[new_container]=new_container_final
                    self.radical_list_object_subject.append(new_container)
                    self.list_object_subject.append(new_container_final)
                #remove meaningless relation
                self.new_containment[obj].remove(cont_obj)
                self.new_containment[obj].append(new_container)
                if new_container in self.new_containment.keys():
                    self.new_containment[new_container].append(cont_obj)
                else:
                    self.new_containment[new_container]=[cont_obj]
                n=len(self.symbol_grounding_table.keys())
                first_new_relation=self.containment_disposition[new_disposition][0]+"_"+str(n)
                self.symbol_grounding_table[first_new_relation]=self.namespace+self.containment_disposition[new_disposition][0]

                n =  len(self.symbol_grounding_table.keys())
                second_new_relation = self.containment_disposition[disposition][0] + "_" + str(n)
                self.symbol_grounding_table[second_new_relation] = self.namespace + self.containment_disposition[disposition][0]
                if found_one_party==0 or found_one_party==2:
                    self.new_final_graph.append([self.new_dict_id[obj], first_new_relation, new_container_final])
                    result10 = result10 + "\n * " + self.new_dict_id[obj] + "  " + first_new_relation + " " + new_container_final + " \n\n"
                if found_one_party == 0 or found_one_party == 1:
                    self.new_final_graph.append([new_container_final, second_new_relation, self.new_dict_id[cont_obj]])
                    result10 = result10 + "\n * " + new_container_final + "  " + second_new_relation + " " + self.new_dict_id[cont_obj] + " \n\n"
                #remove meaningless relation
                target_rel=[]
                found=False
                for rel in self.new_final_graph:
                    rel1 = rel[1].split('_')
                    rel1.pop()
                    rel1 = '_'.join(rel1)
                    if rel[0]==self.new_dict_id[obj] and rel[2]==self.new_dict_id[cont_obj] and rel1 in self.containment_relation:
                        found=True
                        target_rel=rel.copy()
                        break
                if found:
                    self.new_final_graph.remove(target_rel)

        self.containment={}
        for cont in self.new_containment.keys():
            if self.new_containment[cont]!=[]:
                self.containment[cont]=self.new_containment[cont].copy()

        multiplicator=int(np.ceil((1-self.containment_probability)/self.containment_probability))

        self.new_list_object_subject=self.list_object_subject.copy()
        self.new_radical_list_object_subject=self.radical_list_object_subject.copy()
        stability_reached=False
        while not stability_reached:
            for i in range(len(self.list_object_subject)):
                participant=self.list_object_subject[i]
                radical_participant=self.radical_list_object_subject[i]
                if (radical_participant not in self.classes.keys()) or (radical_participant in self.containment.keys()):
                    continue
                self.possible_container=[]

                #get all possible containers for that objects
                for role in self.containment_disposition.keys():
                    for object in self.roles[role]['object']:
                        if radical_participant in self.action_object_role[role][object]['object']:
                            self.possible_container.append(object)

                #check that there is no such container already in the lists

                container_to_be_selected=[]
                for j in range(len(self.list_object_subject)):
                    participant_j = self.list_object_subject[j]
                    radical_participant_j = self.radical_list_object_subject[j]
                    if radical_participant_j in self.possible_container:
                        container_to_be_selected.append(radical_participant_j)

                #consider the possible containers if no container is present
                if container_to_be_selected==[]:
                    container_to_be_selected=self.possible_container.copy()

                print(participant, container_to_be_selected)
                container_index=int(np.ceil(random.random()*len(container_to_be_selected)))
                container_index-=int(container_index>=len(container_to_be_selected))
                print('*************',container_index, len(container_to_be_selected),'***********************')
                #randomly select a container if multiple possible
                if container_index<0:
                    continue
                new_container=container_to_be_selected[container_index]
                new_disposition=list(self.containment_disposition.keys())[0]
                for role in self.containment_disposition.keys():
                    if new_container in self.roles[role]['object']:
                        new_disposition=role
                        break
                #register new container if not yet in the graph
                if new_container not in self.radical_list_object_subject:
                    n = len(self.symbol_grounding_table.keys())
                    new_participant=new_container+'_'+str(n)
                    self.symbol_grounding_table[new_participant] = self.namespace + new_participant
                    if new_container not in self.new_dict_id.keys():
                        self.new_dict_id[new_container]=new_participant
                    self.new_radical_list_object_subject.append(new_container)
                    self.new_list_object_subject.append(new_participant)
                #register new containment relation instance
                n=len(self.symbol_grounding_table.keys())
                new_relation=self.containment_disposition[new_disposition][0]+"_"+str(n)
                self.symbol_grounding_table[new_relation]=self.namespace+new_relation
                self.new_final_graph.append([participant, new_relation, self.new_dict_id[new_container]])
                result10 = result10 + "\n * " + participant + "  " + new_relation + " " + self.new_dict_id[new_container] + " \n\n"
                if radical_participant in self.containment.keys():
                    self.containment[radical_participant].append(new_container)
                else:
                    self.containment[radical_participant]=[new_container]


            #check that no object has more than one container or support
            print(self.containment)
            for obj in self.containment.keys():
                if len(list(set(self.containment[obj])))>1:
                    result10 = result10 + "\n * " + obj + "  cannot have more than one support or container!!! \n\n"
                    data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                            title5, result5,
                            title6, result6, title7, result7, title8, result8, title9, result9, title10, result10]
                    GLib.idle_add(self.update_textview, data)
                    self.update_ontology_frame([], [])
                    return

            if len(self.list_object_subject)==len(self.new_list_object_subject):
                stability_reached=True
            self.list_object_subject=self.new_list_object_subject.copy()
            self.radical_list_object_subject=self.new_radical_list_object_subject.copy()

        #update the graph and the concept dictionary
        self.final_graph = self.new_final_graph.copy()
        self.dict_id=self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Containment']=self.containment.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5,
                title6, result6, title7, result7, title8, result8, title9, result9, title10, result10]
        GLib.idle_add(self.update_textview, data)

        
        ################################################# Closing co-reference resolution ####################################################################

        title11 = "\n 11. Resolving directional relationships among objects \n\n\n"
        result11 = ""

        self.new_final_graph = self.final_graph.copy()
        self.new_dict_id = self.dict_id.copy()

        #initializes variables
        self.list_object_subject = []
        self.radical_list_object_subject = []
        self.containment_reverse = {}
        self.direction={}
        self.direction_relation=[]
        self.canonical_direction_relation=[]
        self.containment_relation = []
        self.containment_relation_support = []
        self.containment_relation_container = []

        #collect set of containment relations
        for role in self.containment_disposition.keys():
            self.containment_relation += self.containment_disposition[role].copy()
            self.containment_relation += self.roles[role]['object_relation']

        #collect set of directional relations
        for values in self.spatial_direction.keys():
            self.direction_relation+=self.spatial_direction[values]['synonym'].copy()
            if self.spatial_direction[values]['canonicity']:
                self.canonical_direction_relation+=self.spatial_direction[values]['synonym'].copy()

        # collecting all objects and subjects
        for rel in self.final_graph:

            rel0 = rel[0].split('_')
            rel0.pop()
            rel0 = '_'.join(rel0)
            if rel0 in self.classes.keys() and rel[0] not in self.list_object_subject:
                self.list_object_subject.append(rel[0])
                self.radical_list_object_subject.append(rel0)

            rel2 = rel[2].split('_')
            rel2.pop()
            rel2 = '_'.join(rel2)
            if rel2 in self.classes.keys() and rel[2] not in self.list_object_subject:
                self.list_object_subject.append(rel[2])
                self.radical_list_object_subject.append(rel2)

            rel1 = rel[1].split('_')
            rel1.pop()
            rel1 = '_'.join(rel1)

            if rel1 in self.containment_relation:
                if rel0 in self.containment_reverse.keys():
                    self.containment_reverse[rel0].append(rel2)
                else:
                    self.containment_reverse[rel0] = [rel2]

            if rel1 in self.direction_relation:
                if rel1 in self.canonical_direction_relation:
                    if rel0 in self.direction.keys():
                        self.direction[rel0].append([rel2,rel1, rel[1]])
                    else:
                        self.direction[rel0]=[[rel2, rel1, rel[1]]]
                else:
                    n=rel[1].split('_').pop()
                    new_direct=self.spatial_direction[rel1]['opposite'][0]+'_'+str(n)
                    self.symbol_grounding_table[new_direct]=self.namespace+self.spatial_direction[rel1]['opposite'][0]
                    self.new_final_graph.remove(rel)
                    self.new_final_graph.append([rel[2], new_direct, rel[0]])
                    if rel2 in self.direction.keys():
                        self.direction[rel2].append([rel0,self.spatial_direction[rel1]['opposite'][0], new_direct])
                    else:
                        self.direction[rel2]=[[rel0,self.spatial_direction[rel1]['opposite'][0], new_direct]]
        #resolve ambiguous directional relations
        self.new_direction=self.direction.copy()
        for obj in self.direction.keys():
            for cont_set in self.direction[obj]:
                cont_obj=cont_set[0]
                if obj not in self.containment.keys() or  cont_obj not in self.containment.keys():
                    result11 = result11 + "\n * " + obj + "  "+cont_set[1]+" " + cont_obj + ": does not make sense!!! \n\n"
                    data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                            title5, result5,
                            title6, result6, title7, result7, title8, result8, title9, result9, title10, result10, title11, result11]
                    GLib.idle_add(self.update_textview, data)
                    self.update_ontology_frame([], [])
                    return

                inter_holder = list(set(self.containment[obj]) & set(self.containment[cont_obj]))
                if inter_holder!=[]:
                    continue
                else:
                    list_container_obj=self.compute_containment_property(obj,self.containment)
                    list_container_cont_obj=self.compute_containment_property(cont_obj, self.containment)
                    common_container=self.compute_common_container(list_container_obj,list_container_cont_obj)
                    if common_container==[-1,-1]:
                        #they either are not in the same room or one is contained by the other
                        result11 = result11 + "\n * " + obj + "  " + cont_set[1] + " " + cont_set[0] + " not in the same room or one contains the other: does not make sense!!! \n\n"
                        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                title5, result5,
                                title6, result6, title7, result7, title8, result8, title9, result9, title10,
                                result10, title11, result11]
                        GLib.idle_add(self.update_textview, data)
                        self.update_ontology_frame([], [])
                        return
                    #select new targets
                    first_obj=([obj]+list_container_obj)[common_container[0]]
                    first_cont_obj = ([cont_obj] + list_container_cont_obj)[common_container[1]]
                    if  first_obj in self.new_direction.keys():
                        #add a meaningful directional relation
                        found=False
                        for dir_set in self.new_direction[first_obj]:
                            if first_cont_obj == dir_set[0] and cont_set[1]==dir_set[1]:
                                found=True
                                break
                        if not found:
                            self.new_direction[first_obj].append([first_cont_obj, cont_set[1], cont_set[2]])
                            #adding new relation
                            self.new_final_graph.append([self.new_dict_id[first_obj], cont_set[2], self.new_dict_id[first_cont_obj]])
                            result11 = result11 + "\n * " + self.new_dict_id[first_obj] + "  " + cont_set[2] + " " + self.new_dict_id[first_cont_obj] + " \n\n"
                        else:
                            #the new directional already exists
                            continue
                    else:
                        self.new_direction[first_obj]=[[first_cont_obj, cont_set[1], cont_set[2]]]
                        # adding new relation
                        self.new_final_graph.append([self.new_dict_id[first_obj], cont_set[2], self.new_dict_id[first_cont_obj]])
                        result11 = result11 + "\n * " + self.new_dict_id[first_obj] + "  " + cont_set[2] + " " + self.new_dict_id[first_cont_obj] + " \n\n"
                    #remove meaningless
                    self.new_direction[obj].remove(cont_set)
                    self.new_final_graph.remove([self.new_dict_id[obj], cont_set[2], self.new_dict_id[cont_set[0]]])
        self.direction={}
        for cont_set in self.new_direction.keys():
            if self.new_direction[cont_set]!=[]:
                self.direction[cont_set]=self.new_direction[cont_set].copy()
        self.new_direction=self.direction.copy()
        for i in range(len(self.list_object_subject)-1):
            for j in range(i+1, len(self.list_object_subject)):
                participant_i=self.list_object_subject[i]
                participant_j = self.list_object_subject[j]
                r_participant_i = self.radical_list_object_subject[i]
                r_participant_j = self.radical_list_object_subject[j]
                if r_participant_i not in self.containment_reverse.keys() or r_participant_j not in self.containment_reverse.keys():
                    continue
                inter_holder=list(set(self.containment_reverse[r_participant_i])&set(self.containment_reverse[r_participant_j]))
                if inter_holder==[]:
                    #cannot decide positioning if no common holder
                    continue
                else:
                    not_found = []
                    found = []
                    if r_participant_i in self.new_direction.keys():
                        for com_set in self.new_direction[r_participant_i]:
                            if com_set[0]== r_participant_j:
                                #a relation already exists
                                found.append(com_set[1])

                    if r_participant_j in self.new_direction.keys():
                        for com_set in self.new_direction[r_participant_j]:
                            if com_set[0] == r_participant_i:
                                # a relation already exists
                                found.append(com_set[1])

                    for relation in self.canonical_direction_relation:
                        if relation not in found:
                            not_found.append(relation)
                    if not_found==[]:
                        #relation already
                        continue

                    objects=[i,j]
                    for relation in not_found:
                        f_index=int(np.round(random.random()))
                        new_relation=relation
                        n=len(self.symbol_grounding_table.keys())
                        new_relation_final=new_relation+'_'+str(n)
                        self.symbol_grounding_table[new_relation]=self.namespace+new_relation_final
                        s_index=1-f_index
                        if self.radical_list_object_subject[objects[f_index]] in self.new_direction.keys():
                            self.new_direction[self.radical_list_object_subject[objects[f_index]]].append([self.radical_list_object_subject[objects[s_index]],new_relation, new_relation_final])
                        else:
                            self.new_direction[self.radical_list_object_subject[objects[f_index]]]=[[self.radical_list_object_subject[objects[s_index]], new_relation, new_relation_final]]
                        self.new_final_graph.append([self.list_object_subject[objects[f_index]], new_relation_final, self.list_object_subject[objects[s_index]]])
                        result11 = result11 + "\n * " + self.list_object_subject[objects[f_index]] + "  " + new_relation_final + " " + self.list_object_subject[objects[s_index]] + " \n\n"

        #check that there is no contradictory relation
        for obj in self.new_direction.keys():
            for cont_set in self.new_direction[obj]:
                if cont_set[0] in self.new_direction.keys():
                    for cont_set2 in self.new_direction[cont_set[0]]:
                        if cont_set2[0]==obj and cont_set2[1]==cont_set[1]:
                            result11 = result11 + "\n * " + obj + "  " + cont_set[1] + " " + cont_set[0] + " and vice versa: does not make sense!!! \n\n"
                            data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                    title5, result5,
                                    title6, result6, title7, result7, title8, result8, title9, result9, title10,
                                    result10, title11, result11]
                            GLib.idle_add(self.update_textview, data)
                            self.update_ontology_frame([], [])
                            return
        self.direction=self.new_direction.copy()
        # update the graph and the concept dictionary
        self.final_graph = self.new_final_graph.copy()
        self.dict_id = self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Direction'] = self.direction.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5,
                result5,
                title6, result6, title7, result7, title8, result8, title9, result9, title10, result10, title11, result11]
        GLib.idle_add(self.update_textview, data)

        ################################################# Proximity resolution ####################################################################

        title12 = "\n 12. Resolving proximity among objects \n\n\n"
        result12 = ""

        self.new_final_graph = self.final_graph.copy()
        self.new_dict_id = self.dict_id.copy()

        self.list_object_subject = []
        self.radical_list_object_subject = []
        self.proximity = {}
        self.proximity_relation = []

        for prox in self.spatial_proximity.keys():
            self.proximity_relation += self.spatial_proximity[prox]['synonym'].copy()

        # collecting all objects and subjects
        for rel in self.final_graph:

            rel0 = rel[0].split('_')
            rel0.pop()
            rel0 = '_'.join(rel0)
            if rel0 in self.classes.keys() and rel[0] not in self.list_object_subject:
                self.list_object_subject.append(rel[0])
                self.radical_list_object_subject.append(rel0)

            rel2 = rel[2].split('_')
            rel2.pop()
            rel2 = '_'.join(rel2)
            if rel2 in self.classes.keys() and rel[2] not in self.list_object_subject:
                self.list_object_subject.append(rel[2])
                self.radical_list_object_subject.append(rel2)

            rel1 = rel[1].split('_')
            rel1.pop()
            rel1 = '_'.join(rel1)

            if rel1 in self.proximity_relation:
                if rel0 not in self.containment.keys() or rel2 not in self.containment.keys():
                    #cannot exists a proximity relation
                    result12 = result12 + "\n * There cannot be a proximity relation between " + rel[0] + " and " + rel[2] + ": does not make sense!!! \n\n"
                    data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                            title5, result5,
                            title6, result6, title7, result7, title8, result8, title9, result9, title10, result10,
                            title11, result11,title12, result12]
                    GLib.idle_add(self.update_textview, data)
                    self.update_ontology_frame([], [])
                    return
                else:
                    inter_holder=list(set(self.containment[rel0])&set(self.containment[rel2]))
                    if inter_holder!=[]:
                        if rel0 in self.proximity.keys():
                            if rel2 in self.proximity[rel0]:
                                #no need to further process
                                self.new_final_graph.remove(rel)
                                continue
                            else:
                                if rel2 in self.proximity.keys():
                                    if rel0 in self.proximity[rel2]:
                                        #no need to further process
                                        self.new_final_graph.remove(rel)
                                        continue
                                #resolve fuzziness in proximity
                                fuzziness=int(np.round(random.random()*100))
                                new_relation=rel1+'_'+rel[1].split('_').pop()+':'+str(fuzziness)+'%'
                                self.symbol_grounding_table[new_relation]=self.namespace+rel1
                                self.new_final_graph.remove(rel)
                                self.new_final_graph.append([rel[0], new_relation,rel[2]])
                                self.proximity[rel0].append(rel2)
                                result12 = result12 + "\n * " + rel[0] + " " +new_relation+ " " + rel[2] + " \n\n"
                        else:
                            if rel2 in self.proximity.keys() and rel0 in self.proximity[rel2]:
                                #nothing
                                self.new_final_graph.remove(rel)
                                continue
                            else:
                                # resolve fuzziness in proximity
                                fuzziness = int(np.round(random.random() * 100))
                                new_relation = rel1 + '_' + rel[1].split('_').pop() + ':' + str(fuzziness) + '%'
                                self.symbol_grounding_table[new_relation] = self.namespace + rel1
                                self.new_final_graph.remove(rel)
                                self.new_final_graph.append([rel[0], new_relation, rel[2]])
                                self.proximity[rel0]=[rel2]
                                result12 = result12 + "\n * " + rel[0] + " " + new_relation + " " + rel[2] + " \n\n"
                    else:
                        obj = rel0
                        cont_obj = rel2
                        list_container_obj = self.compute_containment_property(obj, self.containment)
                        list_container_cont_obj = self.compute_containment_property(cont_obj, self.containment)
                        common_container = self.compute_common_container(list_container_obj, list_container_cont_obj)
                        if common_container == [-1, -1]:
                            # they either are not in the same room or one is contained by the other
                            result12 = result12 + "\n * " + obj + "  " + rel[1] + " " + cont_obj + " not in the same room or one contains the other: does not make sense!!! \n\n"
                            data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4,
                                    title5, result5,
                                    title6, result6, title7, result7, title8, result8, title9, result9, title10,
                                    result10, title11, result11, title12, result12]
                            GLib.idle_add(self.update_textview, data)
                            self.update_ontology_frame([], [])
                            return
                        # select new targets
                        first_obj = ([obj] + list_container_obj)[common_container[0]]
                        first_cont_obj = ([cont_obj] + list_container_cont_obj)[common_container[1]]

                        if first_obj in self.proximity.keys():
                            if first_cont_obj in self.proximity[first_obj]:
                                #no need to further process
                                self.new_final_graph.remove(rel)
                                continue
                            else:
                                if first_cont_obj in self.proximity.keys():
                                    if first_obj in self.proximity[first_cont_obj]:
                                        #no need to further process
                                        self.new_final_graph.remove(rel)
                                        continue
                                #resolve fuzziness in proximity
                                fuzziness=int(np.round(random.random()*100))
                                new_relation=rel1+'_'+rel[1].split('_').pop()+':'+str(fuzziness)+'%'
                                self.symbol_grounding_table[new_relation]=self.namespace+rel1
                                self.new_final_graph.remove(rel)
                                self.new_final_graph.append([self.new_dict_id[first_obj], new_relation,self.new_dict_id[first_cont_obj]])
                                self.proximity[first_obj].append(first_cont_obj)
                                result12 = result12 + "\n * " + self.new_dict_id[first_obj] + " " +new_relation+ " " + self.new_dict_id[first_cont_obj] + " \n\n"
                        else:
                            if first_cont_obj in self.proximity.keys() and first_obj in self.proximity[first_cont_obj]:
                                #nothing
                                self.new_final_graph.remove(rel)
                                continue
                            else:
                                # resolve fuzziness in proximity
                                fuzziness = int(np.round(random.random() * 100))
                                new_relation = rel1 + '_' + rel[1].split('_').pop() + ':' + str(fuzziness) + '%'
                                self.symbol_grounding_table[new_relation] = self.namespace + rel1
                                self.new_final_graph.remove(rel)
                                self.new_final_graph.append([self.new_dict_id[first_obj], new_relation, self.new_dict_id[first_cont_obj]])
                                self.proximity[first_obj]=[first_cont_obj]
                                result12 = result12 + "\n * " + self.new_dict_id[first_obj] + " " + new_relation + " " + self.new_dict_id[first_cont_obj] + " \n\n"


        for obj in self.direction.keys():
            for cont_set in self.direction[obj]:
                cont_obj=cont_set[0]
                if obj in self.proximity.keys():
                    if cont_obj in self.proximity[obj]:
                        # no need to further process
                        continue
                    else:
                        if cont_obj in self.proximity.keys():
                            if obj in self.proximity[cont_obj]:
                                # no need to further process
                                continue
                        # resolve fuzziness in proximity
                        fuzziness = int(np.round(random.random() * 100))
                        rel_prop=random.random()-pow(0.1,10)
                        start_prop=0
                        found_relation=None
                        for relation in self.proximity_relation:
                            if rel_prop>=start_prop and rel_prop<start_prop+self.spatial_proximity[relation]['probability']:
                                found_relation=relation
                                break
                            start_prop += self.spatial_proximity[relation]['probability']
                        if found_relation not in self.proximity_relation:
                            continue
                        n=len(self.symbol_grounding_table.keys())
                        new_relation = found_relation + '_' + str(n) + ':' + str(fuzziness) + '%'
                        self.symbol_grounding_table[new_relation] = self.namespace + found_relation
                        self.new_final_graph.append([self.new_dict_id[obj], new_relation, self.new_dict_id[cont_obj]])
                        self.proximity[obj].append(cont_obj)
                        result12 = result12 + "\n * " + self.new_dict_id[obj] + " " + new_relation + " " + self.new_dict_id[cont_obj] + " \n\n"
                else:
                    if cont_obj in self.proximity.keys() and obj in self.proximity[cont_obj]:
                        # nothing
                        continue
                    else:
                        # resolve fuzziness in proximity
                        fuzziness = int(np.round(random.random() * 100))
                        rel_prop = random.random() - pow(0.1, 10)
                        start_prop = 0
                        found_relation = None
                        for relation in self.proximity_relation:
                            if rel_prop >= start_prop and rel_prop < start_prop + self.spatial_proximity[relation]['probability']:
                                found_relation = relation
                                break
                            start_prop+=self.spatial_proximity[relation]['probability']
                        if found_relation not in self.proximity_relation:
                            continue
                        n = len(self.symbol_grounding_table.keys())
                        new_relation = found_relation + '_' + str(n) + ':' + str(fuzziness) + '%'
                        self.symbol_grounding_table[new_relation] = self.namespace + found_relation
                        self.new_final_graph.append([self.new_dict_id[obj], new_relation, self.new_dict_id[cont_obj]])
                        self.proximity[obj]=[cont_obj]
                        result12 = result12 + "\n * " + self.new_dict_id[obj] + " " + new_relation + " " + self.new_dict_id[cont_obj] + " \n\n"
        # update the graph and the concept dictionary
        self.final_graph = self.new_final_graph.copy()
        self.dict_id = self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Proximity'] = self.proximity.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5,
                result5,
                title6, result6, title7, result7, title8, result8, title9, result9, title10, result10, title11, result11, title12, result12]
        GLib.idle_add(self.update_textview, data)

        ################################################# Resolving physical parameters of objects  ####################################################################

        title13 = "\n 13. Resolving physical parameters of objects \n\n\n"
        result13 = ""
        # collecting all objects and subjects
        goal=KBDataPropertyGoal()
        self.new_final_graph=self.final_graph.copy()
        self.new_dict_id=self.dict_id.copy()
        for quality in self.quality_relation.keys():
            print('----------------------------------------------',quality)
            self.list_object_subject_found=[]

            self.list_object_subject_not_found = []
            self.radical_list_object_subject_not_found = []

            for rel in self.final_graph:

                rel1 = rel[1].split('_')
                rel1.pop()
                rel1 = '_'.join(rel1)

                if rel1 not in self.quality_relation[quality]['relation']:
                    continue
                else:
                    if rel[0] not in self.list_object_subject_found:
                        self.list_object_subject_found.append(rel[0])

                    if rel[2] not in self.list_object_subject_found:
                        self.list_object_subject_found.append(rel[2])

            for rel in self.final_graph:
                rel0 = rel[0].split('_')
                rel0.pop()
                rel0 = '_'.join(rel0)
                if rel0 in self.classes.keys() and rel[0] not in self.list_object_subject_not_found and rel[0] not in self.list_object_subject_found:
                    self.list_object_subject_not_found.append(rel[0])
                    self.radical_list_object_subject_not_found.append(rel0)

                rel2 = rel[2].split('_')
                rel2.pop()
                rel2 = '_'.join(rel2)
                if rel2 in self.classes.keys() and rel[2] not in self.list_object_subject_not_found and rel[2] not in self.list_object_subject_found:
                    self.list_object_subject_not_found.append(rel[2])
                    self.radical_list_object_subject_not_found.append(rel2)

            for i in range(len(self.list_object_subject_not_found)):
                participant=self.list_object_subject_not_found[i]
                radical_participant=self.radical_list_object_subject_not_found[i]
                print('----------------------------------------------', quality, radical_participant)
                goal.class_name=radical_participant
                goal.property_name=self.quality_relation[quality]['relation'][0]
                goal.quantifier='value'

                self.data_property.send_goal(goal)
                self.data_property.wait_for_result()
                results = self.data_property.get_result()
                values=results.values.copy()

                if values==[]:
                    try:
                        random_index=int(np.round(random.random()*(len(self.property_io[self.quality_relation[quality]['relation'][0]])-1)))
                        values.append(self.property_io[self.quality_relation[quality]['relation'][0]][random_index])
                        for val in self.property_io[self.quality_relation[quality]['relation'][0]]:
                            if val not in values and random.random()<self.quality_probability:
                                values.append(val)
                    except Exception as e:
                        values.append(self.quality_relation[quality]['unknown_value'][0])
                        print(str(e))

                if self.quality_relation[quality]['dtype'][0] != str:
                    minimum_set=[]
                    maximum_set=[]
                    for val in values:
                        val=val.split('-')
                        minimum_set.append(self.quality_relation[quality]['dtype'][0] (val[0]))
                        maximum_set.append(self.quality_relation[quality]['dtype'][0] (val[len(val)-1]))
                    val_min=min(minimum_set)
                    val_max=max(maximum_set)
                    if self.quality_relation[quality]['dtype'][0] == int:
                        final_value=self.quality_relation[quality]['dtype'][0](np.round(random.random()*(val_max-val_min)+val_min))
                    else:
                        final_value = self.quality_relation[quality]['dtype'][0](random.random() * (val_max - val_min) + val_min)
                    values=[final_value]
                for val in values:
                    print('----------------------------------------------', quality, radical_participant, val)
                    n=(len(self.symbol_grounding_table.keys()))
                    if self.quality_relation[quality]['units']==[]:
                        new_quality=str(val)+'_'+str(n)
                    else:
                        new_quality = str(val) + '_' + str(n)+self.quality_relation[quality]['units'][0]
                    self.symbol_grounding_table[new_quality]="owl:oneOf(rdfs:range(" + str(self.data_properties[self.quality_relation[quality]['relation'][0]]) + "))"
                    n = (len(self.symbol_grounding_table.keys()))
                    new_relation=self.quality_relation[quality]['relation'][0]+'_'+str(n)
                    self.symbol_grounding_table[new_relation]=self.namespace+new_relation
                    self.new_final_graph.append([participant, new_relation, new_quality])
                    result13 = result13 + "\n * " + participant + "  " + new_relation + " " + new_quality + " \n\n"

        # update the graph and the concept dictionary
        self.final_graph = self.new_final_graph.copy()
        self.dict_id = self.new_dict_id.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Containment'] = self.containment.copy()
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Symbol_Grounding_Table'] = self.symbol_grounding_table
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'] = self.final_graph
        self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['ID_Resolution'] = self.dict_id
        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5,
                title6, result6, title7, result7, title8, result8, title9, result9, title10, result10, title11, result11, title12, result12, title13, result13]
        GLib.idle_add(self.update_textview, data)

        
        ########################################## Resolving spatial relations among objects #############################################################
        self.spatial_relations={"CookTable": ["support", ["Bottle", "Bowl", "Mug", "Box"]], "Bowl": ["contains", ["Spoon"]], "Bottle": ["contains",["Milk"]], "Box": ["contains",["Muesli"]], "Robot":["is infront of",["CookTable"]]}

        title6 = "\n 6. Resolving spatial relationships among objects \n\n\n"
        result6 = ""
        for cls in self.spatial_relations.keys():
            result6 += self.classes[cls] + "\n" + self.spatial_relations[cls][0]+ " "
            for elt in self.spatial_relations[cls][1]:
                result6 += self.classes[elt] + ":"
            result6 += "\n\n"

        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5, title6, result6]
        GLib.idle_add(self.update_textview, data)
        ########################################## Resolving properties of objects #############################################################
        self.object_properties={"CookTable": ["Brown", "Large"], "Bowl": ["Red", "Small"], "Mug": ["Red", "Small"],"Spoon": ["Gray", "Small"], "Box": ["Green", "Medium"], "Milk": ["White", "Liquid"], "Muesli": ["Brown", "Powder"]}

        title7 = "\n 7. Resolving conceptual relationships among objects and properties \n\n\n"
        result7 = ""
        for cls in self.object_properties.keys():
            result7 += self.classes[cls] + "\n has_color "+self.object_properties[cls][0]
            result7 += "\n\n"

        data = [title0, result0, title1, result1, title2, result2, title3, result3, title4, result4, title5, result5,title6, result6,title7, result7]
        GLib.idle_add(self.update_textview, data)
        ########################################## Generating scene graph #############################################################
        
        
        graph = [["Robot", "test", "SampleFluid"], ["Robot", "need", "RinseFluid"],
                 ["SampleFluid", "is_in", "SampleBottle"], ["RinseFluid", "is in", "RinseBottle"], ["RinseBottle", "is_left", "Pump"],
                 ["SampleBottle", "is_right", "Pump"],
                 ["Pump", "is_on", "SterilityTestTable"], ["RinseBottle", "is_on", "SterilityTestTable"], ["SampleBottle", "is_on", "SterilityTestTable"],
                 ["Canister_1", "is_in", "DrainTray"], ["DrainTray", "is_part_of", "Pump"], ["Canister_2", "is_front", "Pump"],
                 ["Canister_2", "is_on", "SterilityTestTable"], ["Robot", "look", "SterilityTestTable"], ["SampleFluid", "is", "Orange"]]
        
        graph=[['Bowl_0', 'has_color_1', 'Red_2'], ['Bowl_0', 'is_on_4', 'Table_5'], ['Milk_6', 'is_in_7', 'Bowl_0'], ['Robot_9', 'look_10', 'Bowl_0'], ['Robot_9', 'prepare_13', 'Breakfast_14'], ['Table_5', 'has_color_16', 'Brown_17'], ['Table_5', 'has_material_19', 'Woody_20'], ['Breakfast_14', 'includes_22', 'Milk_6'], ['Breakfast_14', 'includes_24', 'Muesli_24']]
        
        initial_graph=self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Narrative_Parsing']['Triplets'].copy()
        input_text = [item.replace(' ','_') for sublist in initial_graph for item in sublist]
        # Final graph
        print(self.CONTEXT['Joint_Graph'][ACTUAL_INDEX]['Tree'])
        graph=self.final_graph.copy()
        #graph=[['Robot_0', 'can_be_agent_7', 'Make_1']]
        self.update_ontology_frame(graph,input_text)
        """
        self.thread_robot = Thread(target=self.move_robot, args=[])
        self.thread_robot.daemon=True
        self.thread_robot.start()
        while not THREAD_KILLABLE:
            GLib.idle_add(self.update_imagination_frame)
            time.sleep(1. / self.observation_frequency)
        self.thread_robot.join()


    def read_text(self):
        startIter, endIter = self.textbuffer.get_bounds()
        self.text = self.textbuffer.get_text(startIter, endIter, False)
        return False
    def update_textview(self, text):
        t=""
        for i in range(len(text)):
           t+=text[i]
        self.textbuffer.set_text(t)

        pivot=0
        for i in range(len(text)//2):
            start_iter = self.textbuffer.get_start_iter()
            end_iter = self.textbuffer.get_start_iter()
            start_iter.forward_chars(pivot)
            pivot+=len(text[2*i])
            end_iter.forward_chars(pivot)
            self.textbuffer.apply_tag(self.textbuffer.get_tag_table().lookup('bold'), start_iter, end_iter)
            pivot+=len(text[2*i+1])

        return False
    def compute_containment_property(self, target_obj, containment_dict):
        if target_obj not in containment_dict.keys():
            return []
        else:
            containment_depth=[]
            while True:
                containment_depth.append(containment_dict[target_obj][0])
                target_obj=containment_dict[target_obj][0]
                if target_obj not in containment_dict.keys():
                    break
            return containment_depth

    def compute_common_container(self, list_container1, list_container2):
        result=[-1,-1]
        for i in range(len(list_container1)):
            for j in range(len(list_container2)):
                if list_container1[i]==list_container2[j]:
                    return [i,j]
        return result




    def update_ontology_frame(self, graph,initial_graph):
        red_color = "#FF7377"
        blue_color = "#87CEFB"
        self.nx_graph = nx.MultiDiGraph()
        seen_nodes=[]
        for k  in range(len(graph)):
            rel=graph[k].copy()
            if rel[0] not in seen_nodes:
                if rel[0].lower() in initial_graph:
                    self.nx_graph.add_node(rel[0], color=blue_color)
                else:
                    self.nx_graph.add_node(rel[0], color=red_color)

                if rel[2] not in seen_nodes:
                    if rel[2].lower() in initial_graph:
                        self.nx_graph.add_node(rel[2], color=blue_color)
                    else:
                        self.nx_graph.add_node(rel[2], color=red_color)
            if rel[1].lower() in initial_graph:
                self.nx_graph.add_edge(rel[0], rel[2], color=blue_color, label=rel[1])
            else:
                self.nx_graph.add_edge(rel[0], rel[2], color=red_color, label=rel[1])
            time.sleep(0.1)
            self.nt = Network('100%', '100%', directed=True)
            self.nt.from_nx(self.nx_graph)
            self.nt.set_options("""
                                                            const options = {
                                                              "physics": {
                                                                "enabled": true,
                                                                "barnesHut": {
                                                                  "gravitationalConstant": -4200,
                                                                  "centralGravity": 0.95,
                                                                  "springLength": 130,
                                                                  "springConstant": 0.015,
                                                                  "damping": 0.01,
                                                                  "overlap":1.0
                                                                },
                                                                "maxVelocity": 5,
                                                                "minVelocity": 0.0001
                                                              }
                                                            }
                                                            """)
            if self.nt is not None:
                if k <len(graph)-1:
                    self.nt.options['physics']['enabled'] = False
                else:
                    self.nt.options['physics']['enabled'] = True
            graphText = self.nt.generate_html()
            self.ontology_frame.view.load_html(graphText, "ontology.html")
            print(graphText)
        self.spinner.stop()
        self.next_button.set_sensitive(True)
        return False

    def update_imagination_frame(self):
        self.imagination_frame.imagine(self.imaginator.observe())
        self.imagination_frame.redraw()
        self.imagination_frame.area.queue_draw()
        return False
    def do_clicked(self, widget):
        global THREAD_KILLABLE
        if (widget == self.proceed_button):
            self.spinner.start()
            THREAD_KILLABLE = False
            self.read_text()
            self.thread = Thread(target=self.build_graph, args=[])
            self.thread.daemon=True
            self.thread.start()
            # thread=Thread(target=self.spin,args=['stop'])
            # thread.start()
            # thread.join()

        else:
            if (widget == self.reset_button):
                self.next_button.set_sensitive(False)
                self.textbuffer.set_text(json.dumps(self.context_template, indent=28, sort_keys=True))
                self.nt = None
                self.ontology_frame.view.load_html("", "ontology.html")
                self.imagination_frame.forget()
                self.imagination_frame.redraw()
                self.imagination_frame.area.queue_draw()
                self.dynamic_button.set_active(True)
                self.spinner.stop()
                if (self.thread is not None):
                    THREAD_KILLABLE = True
            else:
                if widget==self.next_button:
                    pass
    def on_button_clicked(self, widget, tag):
        bounds = self.textbuffer.get_selection_bounds()
        if len(bounds) != 0:
            start, end = bounds
            self.textbuffer.apply_tag(tag, start, end)

    def run_belief(self, widget):
        global THREAD_RUN_BELIEF_KILLABLE
        global RUN_GRASPING
        if (widget.get_label()=="Run Belief"):
            widget.set_label("Reset Belief")
            THREAD_RUN_BELIEF_KILLABLE=False
            RUN_GRASPING=True
            self.thread_run_belief = Thread(target=self.run_belief_spin, args=[])
            self.thread_run_belief.daemon=True
            self.thread_run_belief.start()
        else:
            THREAD_RUN_BELIEF_KILLABLE=True
            widget.set_label("Run Belief")


    def on_clear_clicked(self, widget):
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_all_tags(start, end)

    def on_editable_toggled(self, widget):
        self.textview.set_editable(widget.get_active())

    def on_cursor_toggled(self, widget):
        if widget.get_active():
            self.imaginator.robot_view = 1
        else:
            self.imaginator.robot_view = 0
    def on_cursor_singleness_toggled(self, widget):
        if widget.get_active():
            self.imaginator.single_view = 1
        else:
            self.imaginator.single_view = 0
    def on_dynamic_toggled(self, widget):
        if self.nt is not None:
            self.nt.options['physics']['enabled'] = widget.get_active()
            graphText = self.nt.generate_html()
            self.ontology_frame.view.load_html(graphText, "ontology.html")
    def on_autocorrect_toggled(self, widget):
        self.auto_correct=widget.get_active()
    def on_wrap_toggled(self, widget, mode):
        self.textview.set_wrap_mode(mode)

    def on_justify_toggled(self, widget, justification):
        self.textview.set_justification(justification)

    def on_search_clicked(self, widget):
        dialog = SearchDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            cursor_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(cursor_mark)
            if start.get_offset() == self.textbuffer.get_char_count():
                start = self.textbuffer.get_start_iter()

            self.search_and_mark(dialog.entry.get_text(), start)

        dialog.destroy()

    def search_and_mark(self, text, start):
        end = self.textbuffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
            self.search_and_mark(text, match_end)

    def on_change_label_state(self, action, value):
        action.set_state(value)
        self.label.set_text(value.get_string())

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()
    ########################## Callback for vQA Frame ######################################################
    def _start_vedo_plotter_thread(self):
        """Initializes and runs the Vedo plotter in a dedicated background thread."""

        def run_plotter():
            print("Vedo plotter thread started.")
            self.plotter = vedo.Plotter(size=(800, 600), bg='lightgrey', title="Vedo 3D Viewer", interactive=False)
            self.plotter.show()  # This initially opens the window

            self._plotter_ready_event.set()
            GLib.idle_add(self._enable_controls)

            while not self._stop_plotter_thread.is_set():
                while True:
                    try:
                        command = self._plotter_command_queue.get_nowait()
                        print(f"Plotter thread: Processing command {command[0]}")
                        if command[0] == 'load_mesh':
                            filepath = command[1]
                            self._load_and_display_obj_internal_on_plotter_thread(filepath)
                        elif command[0] == 'zoom':
                            factor = command[1]
                            self._zoom_internal_on_plotter_thread(factor)
                        elif command[0] == 'rotate':
                            axis, angle = command[1], command[2]
                            self._rotate_internal_on_plotter_thread(axis, angle)
                        elif command[0] == 'close_app':
                            print("Plotter thread received close command during main loop.")
                            self._stop_plotter_thread.set()
                            break
                    except queue.Empty:
                        break
                    except Exception as e:
                        print(f"Error processing command in Vedo thread loop: {e}")

                if self.plotter.interactor:
                    self.plotter.interactor.ProcessEvents()
                    self.plotter.interactor.Render()

                time.sleep(0.01)

            print("Plotter thread stopping. Closing Vedo plotter...")
            if self.plotter:
                self.plotter.close()
            print("Vedo plotter thread finished.")

        self.plotter_thread = threading.Thread(target=run_plotter)
        self.plotter_thread.daemon = True
        self.plotter_thread.start()

        if not self._plotter_ready_event.wait(timeout=10):
            print("Warning: Vedo plotter did not become ready in time.")
            return False
        return True

    def _enable_controls(self):
        self.zoom_in_button.set_sensitive(True)
        self.zoom_out_button.set_sensitive(True)
        self.rotate_x_button.set_sensitive(True)
        self.rotate_y_button.set_sensitive(True)
        self.rotate_z_button.set_sensitive(True)
        return False

    def _on_destroy(self, widget):
        print("GTK window destroyed. Signalling Vedo plotter thread to stop...")
        self._stop_plotter_thread.set()
        if self.plotter_thread and self.plotter_thread.is_alive():
            self.plotter_thread.join(timeout=3)
            if self.plotter_thread.is_alive():
                print("Warning: Vedo plotter thread did not terminate cleanly.")
        Gtk.main_quit()

    def _on_load_obj_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Load OBJ File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_obj = Gtk.FileFilter()
        filter_obj.set_name("OBJ files")
        filter_obj.add_pattern("*.obj")
        dialog.add_filter(filter_obj)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            if filepath:
                print(f"Selected OBJ file: {filepath}")
                if self.plotter is None:
                    print("Vedo plotter not running. Starting it now and queuing file load.")
                    GLib.idle_add(self._start_vedo_and_queue_load, filepath)
                else:
                    print("Vedo plotter already running. Queuing file load.")
                    self._plotter_command_queue.put(('load_mesh', filepath))
            else:
                print("No file selected.")
        elif response == Gtk.ResponseType.CANCEL:
            print("File selection cancelled.")

        dialog.destroy()

    def _start_vedo_and_queue_load(self, filepath):
        if self._start_vedo_plotter_thread():
            self._plotter_command_queue.put(('load_mesh', filepath))
        else:
            print("Failed to start Vedo plotter. Cannot load file.")
        return False

    def _load_and_display_obj_internal_on_plotter_thread(self, filepath):
        if not self.plotter:
            print("Error: Plotter not available during internal load (Vedo thread).")
            return

        try:
            if self.current_mesh:
                print("Removing previous mesh (Vedo thread)...")
                self.plotter.remove(self.current_mesh)
                self.current_mesh = None

            print(f"Loading mesh from {filepath} (Vedo thread)...")
            self.current_mesh = vedo.load(filepath)

            if self.current_mesh:
                print(f"Mesh loaded successfully (Vedo thread): {self.current_mesh}")
                self.plotter.add(self.current_mesh)
                self.plotter.reset_camera()
                print(f"Successfully displayed {filepath} in Vedo (Vedo thread).")
            else:
                print(f"Failed to load mesh from {filepath}: Vedo returned no mesh object (Vedo thread).")

        except Exception as e:
            print(f"ERROR loading or displaying OBJ with Vedo (Vedo thread): {e}")
            self.current_mesh = None

    def _zoom_internal_on_plotter_thread(self, factor):
        if self.plotter and self.plotter.camera:
            print(f"Zooming by {factor} (Vedo thread)...")
            self.plotter.zoom(factor)

    def _rotate_internal_on_plotter_thread(self, axis: str, angle: float):
        if not self.current_mesh:
            print("No mesh loaded to rotate (Vedo thread).")
            return
        if not self.plotter:
            print("Plotter not available for rotation (Vedo thread).")
            return

        print(f"Rotating mesh {axis.upper()} by {angle} degrees (Vedo thread).")
        try:
            if axis == "x":
                self.current_mesh.rotate_x(angle)
            elif axis == "y":
                self.current_mesh.rotate_y(angle)
            elif axis == "z":
                self.current_mesh.rotate_z(angle)
        except Exception as e:
            print(f"Error rotating mesh (Vedo thread): {e}")

    def _on_zoom_in_clicked(self, button):
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('zoom', 1.2))

    def _on_zoom_out_clicked(self, button):
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('zoom', 0.8))

    def _on_rotate_clicked(self, axis: str, angle: float):
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('rotate', axis, angle))



class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.example.myapp",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.window = None

        self.add_main_option(
            "test",
            ord("t"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Command line test",
            None,
        )

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = AppWindow(application=self, title="NaivPhys4RP - Naive Physics For Robot Perception")
        self.window.set_default_size(1920, 1080)
        self.window.present()


    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "test" in options:
            # This is printed on the main instance
            print("Test argument recieved: %s" % options["test"])

        self.activate()
        return 0

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.set_license(license="Distributed under Berkeley Software Distribution 4 (BSD-4)")
        about_dialog.set_authors(authors=["Franklin Kenghagho Kenfack"])
        about_dialog.set_version(version="V 0.1")
        about_dialog.set_copyright(copyright="Copyrights 2023 reserved to Institute for Artificial Intelligence")
        about_dialog.set_comments(comments="NaivPhys4RP is a White-box Causal Generative Model of Robot Perception based on Cognitive Emulation that attempts to capture aspects of human commonsense that enables scene understanding in dynamic and human-centered worlds.")
        about_dialog.set_program_name(name="NaivPhys4RP --- Naive Physics for Robot Perception")
        about_dialog.set_logo_icon_name(icon_name="../../resources/logo.png")
        about_dialog.present()

    def on_quit(self, action, param):
        self.quit()


if __name__ == '__main__':
    rospy.init_node('naivphys4rp_imagination_node')
    app = Application()
    app.run(sys.argv)
# graph_draw(g,edge_color="blue",vertex_fill_color=c,vertex_color=c, vertex_text=x, edge_text=y, edge_pen_width=3, vertex_font_size=19, edge_font_size=19, vertex_aspect=1. ,adjust_aspect=True, fit_view_ink=True, fit_view=True)
