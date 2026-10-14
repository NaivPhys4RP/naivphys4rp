from shape_generator import *
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import numpy as np
from perlin_noise import PerlinNoise
from PIL import Image
import vedo
import os
import threading
import time
import queue
import random
import numpy as np
import trimesh
import cv2

# Try to get the GDK X11 library for XID
try:
    gi.require_version('GdkX11', '3.0')
    from gi.repository import GdkX11

    _HAS_GDKX11 = True
except ValueError:
    _HAS_GDKX11 = False
    print("Warning: GdkX11 not available.")


class ObjViewerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="OBJ Viewer (Enhanced Controls)")
        self.set_default_size(1000, 700)
        self.connect("destroy", self._on_destroy)

        self.plotter = None
        self.current_mesh = None
        self.plotter_thread = None
        self._plotter_ready_event = threading.Event()
        self._plotter_command_queue = queue.Queue()
        self._stop_plotter_thread = threading.Event()
        self._continuous_generation_thread = None

        self.IS_SHAPE_GENERATING = False
        try:
            initial_vedo_color = vedo.colors.red
            if isinstance(initial_vedo_color, (tuple, list)) and len(initial_vedo_color) == 3:
                self.current_color = tuple(int(c) for c in initial_vedo_color)
            elif isinstance(initial_vedo_color, str):
                cleaned_str = ''.join(filter(str.isdigit, initial_vedo_color))
                if len(cleaned_str) >= 3 and cleaned_str.isdigit():
                    r = int(cleaned_str[:3]) if len(cleaned_str) >= 3 else 0
                    g = int(cleaned_str[3:6]) if len(cleaned_str) >= 6 else 0
                    b = int(cleaned_str[6:9]) if len(cleaned_str) >= 9 else 0
                    self.current_color = (r, g, b)
                else:
                    raise ValueError(f"Could not parse initial vedo color string: {initial_vedo_color}")
            else:
                self.current_color = (255, 0, 0)
                print(
                    f"Warning: Unexpected type for vedo.colors.red: {type(initial_vedo_color)}. Defaulting to (255,0,0).")
        except Exception as e:
            print(f"Error initializing self.current_color from vedo.colors.red: {e}. Defaulting to (255,0,0).")
            self.current_color = (255, 0, 0)

        self.current_opacity = 1.0
        self.current_shininess = 30.0
        self.current_specular = 0.5

        try:
            initial_edge_color_val = (0, 0, 0)
            if isinstance(initial_edge_color_val, (tuple, list)) and len(initial_edge_color_val) == 3:
                self.current_edge_color = tuple(int(c) for c in initial_edge_color_val)
            else:
                self.current_edge_color = (0, 0, 0)
                print(f"Warning: Unexpected type for initial edge color. Defaulting to (0,0,0).")
        except Exception as e:
            print(f"Error initializing self.current_edge_color: {e}. Defaulting to (0,0,0).")
            self.current_edge_color = (0, 0, 0)

        self.current_edge_width = 0.0
        self.current_texture_path = None

        main_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(main_h_box)

        control_frame = Gtk.Frame(label="File & Camera Controls")
        control_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        control_frame.set_size_request(250, -1)
        main_h_box.pack_start(control_frame, True, True, 0)

        control_v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        control_v_box.set_border_width(10)
        control_frame.add(control_v_box)

        load_button = Gtk.Button(label="Load OBJ File")
        load_button.connect("clicked", self._on_load_obj_clicked)
        control_v_box.pack_start(load_button, False, False, 0)

        self.zoom_in_button = Gtk.Button(label="Zoom In")
        self.zoom_in_button.connect("clicked", self._on_zoom_in_clicked)
        self.zoom_in_button.set_sensitive(False)
        control_v_box.pack_start(self.zoom_in_button, False, False, 0)

        self.zoom_out_button = Gtk.Button(label="Zoom Out")
        self.zoom_out_button.connect("clicked", self._on_zoom_out_clicked)
        self.zoom_out_button.set_sensitive(False)
        control_v_box.pack_start(self.zoom_out_button, False, False, 0)

        control_v_box.pack_start(Gtk.Separator(), False, False, 5)

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

        control_v_box.pack_start(Gtk.Label(), True, True, 0)

        right_column_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_h_box.pack_start(right_column_vbox, True, True, 0)

        shape_gen_frame = Gtk.Frame(label="Generate 3D Shape")
        shape_gen_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        right_column_vbox.pack_start(shape_gen_frame, True, True, 0)

        shape_gen_v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        shape_gen_v_box.set_border_width(10)
        shape_gen_frame.add(shape_gen_v_box)

        shape_name_label = Gtk.Label(label="Select Shape:")
        shape_name_label.set_halign(Gtk.Align.START)
        shape_gen_v_box.pack_start(shape_name_label, False, False, 0)

        self.shape_name_dropdown = Gtk.ComboBoxText()
        self.shape_name_dropdown.append_text("Sphere")
        self.shape_name_dropdown.append_text("Cube")
        self.shape_name_dropdown.append_text("Cylinder")
        self.shape_name_dropdown.append_text("Cone")
        self.shape_name_dropdown.append_text("Torus")
        self.shape_name_dropdown.append_text("Prism")
        self.shape_name_dropdown.append_text("Pyramid")
        self.shape_name_dropdown.set_active(0)
        self.shape_name_dropdown.connect("changed", self._on_shape_name_changed)
        shape_gen_v_box.pack_start(self.shape_name_dropdown, False, False, 0)

        self.param_stack = Gtk.Stack()
        self.param_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.param_stack.set_transition_duration(300)
        shape_gen_v_box.pack_start(self.param_stack, False, False, 0)

        sphere_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sphere_params_box.set_border_width(5)
        sphere_label = Gtk.Label(label="Radius:")
        sphere_label.set_halign(Gtk.Align.START)
        self.sphere_radius_entry = Gtk.Entry()
        self.sphere_radius_entry.set_text("1.0")
        self.sphere_radius_entry.set_placeholder_text("e.g., 1.0")
        sphere_params_box.pack_start(sphere_label, False, False, 0)
        sphere_params_box.pack_start(self.sphere_radius_entry, False, False, 0)
        self.param_stack.add_named(sphere_params_box, "Sphere")

        cube_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cube_params_box.set_border_width(5)
        cube_x_label = Gtk.Label(label="Length X:")
        cube_x_label.set_halign(Gtk.Align.START)
        self.cube_x_entry = Gtk.Entry()
        self.cube_x_entry.set_text("1.0")
        self.cube_x_entry.set_placeholder_text("e.g., 1.0")
        cube_y_label = Gtk.Label(label="Length Y:")
        cube_y_label.set_halign(Gtk.Align.START)
        self.cube_y_entry = Gtk.Entry()
        self.cube_y_entry.set_text("1.0")
        self.cube_y_entry.set_placeholder_text("e.g., 1.0")
        cube_z_label = Gtk.Label(label="Length Z:")
        cube_z_label.set_halign(Gtk.Align.START)
        self.cube_z_entry = Gtk.Entry()
        self.cube_z_entry.set_text("1.0")
        self.cube_z_entry.set_placeholder_text("e.g., 1.0")
        cube_params_box.pack_start(cube_x_label, False, False, 0)
        cube_params_box.pack_start(self.cube_x_entry, False, False, 0)
        cube_params_box.pack_start(cube_y_label, False, False, 0)
        cube_params_box.pack_start(self.cube_y_entry, False, False, 0)
        cube_params_box.pack_start(cube_z_label, False, False, 0)
        cube_params_box.pack_start(self.cube_z_entry, False, False, 0)
        self.param_stack.add_named(cube_params_box, "Cube")

        cyl_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cyl_params_box.set_border_width(5)
        cyl_radius_label = Gtk.Label(label="Radius:")
        cyl_radius_label.set_halign(Gtk.Align.START)
        self.cyl_radius_entry = Gtk.Entry()
        self.cyl_radius_entry.set_text("0.5")
        self.cyl_radius_entry.set_placeholder_text("e.g., 0.5")
        cyl_height_label = Gtk.Label(label="Height:")
        cyl_height_label.set_halign(Gtk.Align.START)
        self.cyl_height_entry = Gtk.Entry()
        self.cyl_height_entry.set_text("2.0")
        self.cyl_height_entry.set_placeholder_text("e.g., 2.0")
        cyl_params_box.pack_start(cyl_radius_label, False, False, 0)
        cyl_params_box.pack_start(self.cyl_radius_entry, False, False, 0)
        cyl_params_box.pack_start(cyl_height_label, False, False, 0)
        cyl_params_box.pack_start(self.cyl_height_entry, False, False, 0)
        self.param_stack.add_named(cyl_params_box, "Cylinder")

        cone_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cone_params_box.set_border_width(5)
        cone_radius_label = Gtk.Label(label="Radius:")
        cone_radius_label.set_halign(Gtk.Align.START)
        self.cone_radius_entry = Gtk.Entry()
        self.cone_radius_entry.set_text("0.5")
        self.cone_radius_entry.set_placeholder_text("e.g., 0.5")
        cone_height_label = Gtk.Label(label="Height:")
        cone_height_label.set_halign(Gtk.Align.START)
        self.cone_height_entry = Gtk.Entry()
        self.cone_height_entry.set_text("2.0")
        self.cone_height_entry.set_placeholder_text("e.g., 2.0")
        cone_params_box.pack_start(cone_radius_label, False, False, 0)
        cone_params_box.pack_start(self.cone_radius_entry, False, False, 0)
        cone_params_box.pack_start(cone_height_label, False, False, 0)
        cone_params_box.pack_start(self.cone_height_entry, False, False, 0)
        self.param_stack.add_named(cone_params_box, "Cone")

        torus_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        torus_params_box.set_border_width(5)
        torus_major_radius_label = Gtk.Label(label="Major Radius:")
        torus_major_radius_label.set_halign(Gtk.Align.START)
        self.torus_major_radius_entry = Gtk.Entry()
        self.torus_major_radius_entry.set_text("1.0")
        self.torus_major_radius_entry.set_placeholder_text("e.g., 1.0")
        torus_minor_radius_label = Gtk.Label(label="Minor Radius:")
        torus_minor_radius_label.set_halign(Gtk.Align.START)
        self.torus_minor_radius_entry = Gtk.Entry()
        self.torus_minor_radius_entry.set_text("0.2")
        self.torus_minor_radius_entry.set_placeholder_text("e.g., 0.2")
        torus_params_box.pack_start(torus_major_radius_label, False, False, 0)
        torus_params_box.pack_start(self.torus_major_radius_entry, False, False, 0)
        torus_params_box.pack_start(torus_minor_radius_label, False, False, 0)
        torus_params_box.pack_start(self.torus_minor_radius_entry, False, False, 0)
        self.param_stack.add_named(torus_params_box, "Torus")

        prism_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        prism_params_box.set_border_width(5)
        prism_sides_label = Gtk.Label(label="Number of Sides:")
        prism_sides_label.set_halign(Gtk.Align.START)
        self.prism_sides_entry = Gtk.Entry()
        self.prism_sides_entry.set_text("6")
        self.prism_sides_entry.set_placeholder_text("e.g., 6")
        prism_radius_label = Gtk.Label(label="Radius (base):")
        prism_radius_label.set_halign(Gtk.Align.START)
        self.prism_radius_entry = Gtk.Entry()
        self.prism_radius_entry.set_text("1.0")
        self.prism_radius_entry.set_placeholder_text("e.g., 1.0")
        prism_height_label = Gtk.Label(label="Height:")
        prism_height_label.set_halign(Gtk.Align.START)
        self.prism_height_entry = Gtk.Entry()
        self.prism_height_entry.set_text("2.0")
        self.prism_height_entry.set_placeholder_text("e.g., 2.0")
        prism_params_box.pack_start(prism_sides_label, False, False, 0)
        prism_params_box.pack_start(self.prism_sides_entry, False, False, 0)
        prism_params_box.pack_start(prism_radius_label, False, False, 0)
        prism_params_box.pack_start(self.prism_radius_entry, False, False, 0)
        prism_params_box.pack_start(prism_height_label, False, False, 0)
        prism_params_box.pack_start(self.prism_height_entry, False, False, 0)
        self.param_stack.add_named(prism_params_box, "Prism")

        pyramid_params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        pyramid_params_box.set_border_width(5)
        pyramid_base_sides_label = Gtk.Label(label="Base Sides:")
        pyramid_base_sides_label.set_halign(Gtk.Align.START)
        self.pyramid_base_sides_entry = Gtk.Entry()
        self.pyramid_base_sides_entry.set_text("4")
        self.pyramid_base_sides_entry.set_placeholder_text("e.g., 4")
        pyramid_radius_label = Gtk.Label(label="Base Radius:")
        pyramid_radius_label.set_halign(Gtk.Align.START)
        self.pyramid_radius_entry = Gtk.Entry()
        self.pyramid_radius_entry.set_text("1.0")
        self.pyramid_radius_entry.set_placeholder_text("e.g., 1.0")
        pyramid_height_label = Gtk.Label(label="Height:")
        pyramid_height_label.set_halign(Gtk.Align.START)
        self.pyramid_height_entry = Gtk.Entry()
        self.pyramid_height_entry.set_text("2.0")
        self.pyramid_height_entry.set_placeholder_text("e.g., 2.0")
        pyramid_params_box.pack_start(pyramid_base_sides_label, False, False, 0)
        pyramid_params_box.pack_start(self.pyramid_base_sides_entry, False, False, 0)
        pyramid_params_box.pack_start(pyramid_radius_label, False, False, 0)
        pyramid_params_box.pack_start(self.pyramid_radius_entry, False, False, 0)
        pyramid_params_box.pack_start(pyramid_height_label, False, False, 0)
        pyramid_params_box.pack_start(self.pyramid_height_entry, False, False, 0)
        self.param_stack.add_named(pyramid_params_box, "Pyramid")

        self.param_stack.set_visible_child_name("Sphere")

        self.generate_button = Gtk.Button(label="Generate & Display")
        self.generate_button.connect("clicked", self._on_generate_shape_clicked)
        shape_gen_v_box.pack_start(self.generate_button, False, False, 0)

        shape_gen_v_box.pack_start(Gtk.Label(), True, True, 0)

        self.stop_generate_button = Gtk.Button(label="Stop Generation")
        self.stop_generate_button.connect("clicked", self._on_stop_generate_shape_clicked)
        self.stop_generate_button.set_sensitive(False)
        shape_gen_v_box.pack_start(self.stop_generate_button, False, False, 0)

        shape_gen_v_box.pack_start(Gtk.Label(), True, True, 0)

        material_texture_frame = Gtk.Frame(label="Material & Texture")
        material_texture_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        right_column_vbox.pack_start(material_texture_frame, False, False, 0)

        material_texture_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        material_texture_vbox.set_border_width(10)
        material_texture_frame.add(material_texture_vbox)

        color_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        color_h_box.pack_start(Gtk.Label(label="Color:"), False, False, 0)
        self.color_button = Gtk.ColorButton()
        self.color_button.set_rgba(Gdk.RGBA(int(self.current_color[0]) / 255, int(self.current_color[1]) / 255,
                                            int(self.current_color[2]) / 255, 1.0))
        self.color_button.connect("color-set", self._on_color_set)
        color_h_box.pack_start(self.color_button, False, False, 0)
        color_h_box.pack_start(Gtk.Label(), True, True, 0)
        material_texture_vbox.pack_start(color_h_box, False, False, 0)

        opacity_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        opacity_h_box.pack_start(Gtk.Label(label="Opacity:"), False, False, 0)
        self.opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.01)
        self.opacity_scale.set_value(self.current_opacity)
        self.opacity_scale.set_digits(2)
        self.opacity_scale.set_hexpand(True)
        self.opacity_scale.connect("value-changed", self._on_opacity_changed)
        opacity_h_box.pack_start(self.opacity_scale, True, True, 0)
        material_texture_vbox.pack_start(opacity_h_box, False, False, 0)

        shininess_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        shininess_h_box.pack_start(Gtk.Label(label="Shininess:"), False, False, 0)
        self.shininess_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 128.0, 1.0)
        self.shininess_scale.set_value(self.current_shininess)
        self.shininess_scale.set_digits(0)
        self.shininess_scale.set_hexpand(True)
        self.shininess_scale.connect("value-changed", self._on_shininess_changed)
        shininess_h_box.pack_start(self.shininess_scale, True, True, 0)
        material_texture_vbox.pack_start(shininess_h_box, False, False, 0)

        specular_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        specular_h_box.pack_start(Gtk.Label(label="Specular:"), False, False, 0)
        self.specular_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.01)
        self.specular_scale.set_value(self.current_specular)
        self.specular_scale.set_digits(2)
        self.specular_scale.set_hexpand(True)
        self.specular_scale.connect("value-changed", self._on_specular_changed)
        specular_h_box.pack_start(self.specular_scale, True, True, 0)
        material_texture_vbox.pack_start(specular_h_box, False, False, 0)

        edge_color_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        edge_color_h_box.pack_start(Gtk.Label(label="Edge Color:"), False, False, 0)
        self.edge_color_button = Gtk.ColorButton()
        self.edge_color_button.set_rgba(
            Gdk.RGBA(int(self.current_edge_color[0]) / 255, int(self.current_edge_color[1]) / 255,
                     int(self.current_edge_color[2]) / 255, 1.0))
        self.edge_color_button.connect("color-set", self._on_edge_color_set)
        edge_color_h_box.pack_start(self.edge_color_button, False, False, 0)
        edge_color_h_box.pack_start(Gtk.Label(), True, True, 0)
        material_texture_vbox.pack_start(edge_color_h_box, False, False, 0)

        edge_width_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        edge_width_h_box.pack_start(Gtk.Label(label="Edge Width:"), False, False, 0)
        self.edge_width_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 5.0, 0.1)
        self.edge_width_scale.set_value(self.current_edge_width)
        self.edge_width_scale.set_digits(1)
        self.edge_width_scale.set_hexpand(True)
        self.edge_width_scale.connect("value-changed", self._on_edge_width_changed)
        edge_width_h_box.pack_start(self.edge_width_scale, True, True, 0) # Corrected line
        material_texture_vbox.pack_start(edge_width_h_box, False, False, 0)

        material_texture_vbox.pack_start(Gtk.Separator(), False, False, 5)

        texture_h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        texture_h_box.pack_start(Gtk.Label(label="Texture:"), False, False, 0)
        self.texture_label = Gtk.Label(label="None")
        self.texture_label.set_hexpand(True)
        self.texture_label.set_halign(Gtk.Align.START)
        texture_h_box.pack_start(self.texture_label, True, True, 0)
        self.load_texture_button = Gtk.Button(label="Load Texture")
        self.load_texture_button.connect("clicked", self._on_load_texture_clicked)
        texture_h_box.pack_start(self.load_texture_button, False, False, 0)
        self.clear_texture_button = Gtk.Button(label="Clear")
        self.clear_texture_button.connect("clicked", self._on_clear_texture_clicked)
        texture_h_box.pack_start(self.clear_texture_button, False, False, 0)
        material_texture_vbox.pack_start(texture_h_box, False, False, 0)

        apply_material_button = Gtk.Button(label="Apply Material/Texture")
        apply_material_button.connect("clicked", self._on_apply_material_clicked)
        material_texture_vbox.pack_start(apply_material_button, False, False, 0)

        material_texture_vbox.pack_start(Gtk.Label(), True, True, 0)

    def _start_vedo_plotter_thread(self):
        def run_plotter():
            print("Vedo plotter thread started.")
            self.plotter = vedo.Plotter(size=(800, 600), bg='lightgrey', title="Vedo 3D Viewer", interactive=False)

            # Add a bright directional light from the top-right
            intensity=0.5
            main_light = vedo.Light(pos=(10, 0, 0), c='white', intensity=intensity)
            #self.plotter.add(main_light)

            main_light2 = vedo.Light(pos=(-10, 0, 0), c='white', intensity=intensity)
            #self.plotter.add(main_light)

            main_light3 = vedo.Light(pos=(0, 10, 0), c='white', intensity=intensity)
            self.plotter.add(main_light3)

            main_light4 = vedo.Light(pos=(0, -10, 0), c='white', intensity=intensity)
            self.plotter.add(main_light4)

            main_light5 = vedo.Light(pos=(0, 0, 10), c='white', intensity=intensity)
            self.plotter.add(main_light5)

            main_light6 = vedo.Light(pos=(0, 0, -10), c='white', intensity=intensity)
            self.plotter.add(main_light6)

            self.plotter.show()
            self._plotter_ready_event.set()
            GLib.idle_add(self._enable_controls)

            while not self._stop_plotter_thread.is_set():
                try:
                    command = self._plotter_command_queue.get(timeout=0.05)
                    print(f"Plotter thread: Processing command {command[0]}")
                    if command[0] == 'load_mesh':
                        filepath = command[1]
                        self._load_and_display_obj_internal_on_plotter_thread(filepath)
                    elif command[0] == 'generate_shape':
                        shape_name, params = command[1], command[2]
                        self._generate_and_display_shape_on_plotter_thread(shape_name, params)
                    elif command[0] == 'apply_material':
                        color, opacity, shininess, specular, edge_color, edge_width, texture_path = command[1:]
                        self._apply_material_internal_on_plotter_thread(color, opacity, shininess, specular,
                                                                        edge_color, edge_width, texture_path)
                    elif command[0] == 'zoom':
                        factor = command[1]
                        self._zoom_internal_on_plotter_thread(factor)
                    elif command[0] == 'rotate':
                        axis, angle = command[1], command[2]
                        self._rotate_internal_on_plotter_thread(axis, angle)
                    elif command[0] == 'activate_window':
                        self._activate_vedo_window_internal_on_plotter_thread()
                    elif command[0] == 'close_app':
                        print("Plotter thread received close command during main loop.")
                        self._stop_plotter_thread.set()
                        break
                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"Error processing command in Vedo thread loop: {e}")

                if self.plotter and self.plotter.interactor:
                    self.plotter.interactor.ProcessEvents()

            print("Plotter thread stopping. Closing Vedo plotter...")
            if self.plotter:
                self.plotter.close()
            print("Vedo plotter thread finished.")

        self.plotter_thread = threading.Thread(target=run_plotter)
        self.plotter_thread.daemon = True
        self.plotter_thread.start()

        return False

    def _enable_controls(self):
        self.zoom_in_button.set_sensitive(True)
        self.zoom_out_button.set_sensitive(True)
        self.rotate_x_button.set_sensitive(True)
        self.rotate_y_button.set_sensitive(True)
        self.rotate_z_button.set_sensitive(True)
        return False

    def _on_destroy(self, widget):
        print("GTK window destroyed. Signalling Vedo plotter thread to stop...")
        self._plotter_command_queue.put(('close_app',))
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

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            if filepath:
                print(f"Selected OBJ file: {filepath}")
                if self.plotter is None or not self._plotter_ready_event.is_set():
                    print("Vedo plotter not running or not ready. Starting it now.")
                    GLib.idle_add(self._start_vedo_plotter_thread)

                self._plotter_command_queue.put(('load_mesh', filepath))
                self._plotter_command_queue.put(('activate_window',))
            else:
                print("No file selected.")
        elif response == Gtk.ResponseType.CANCEL:
            print("File selection cancelled.")

        dialog.destroy()

    def _on_shape_name_changed(self, combo_box):
        selected_shape_name = combo_box.get_active_text()
        self.param_stack.set_visible_child_name(selected_shape_name)

    def _on_stop_generate_shape_clicked(self, button):
        print("Stopping continuous generation...")
        self.IS_SHAPE_GENERATING = False
        self.stop_generate_button.set_sensitive(False)

    def _on_generate_shape_clicked(self, button):
        self.IS_SHAPE_GENERATING = True
        self.generate_button.set_sensitive(False)
        self.stop_generate_button.set_sensitive(True)

        shape_name = self.shape_name_dropdown.get_active_text()
        params = []

        try:
            if shape_name == "Sphere":
                radius_str = self.sphere_radius_entry.get_text()
                params.append(float(radius_str))
            elif shape_name == "Cube":
                x_str = self.cube_x_entry.get_text()
                y_str = self.cube_y_entry.get_text()
                z_str = self.cube_z_entry.get_text()
                params.extend([float(x_str), float(y_str), float(z_str)])
            elif shape_name == "Cylinder":
                radius_str = self.cyl_radius_entry.get_text()
                height_str = self.cyl_height_entry.get_text()
                params.extend([float(radius_str), float(height_str)])
            elif shape_name == "Cone":
                radius_str = self.cone_radius_entry.get_text()
                height_str = self.cone_height_entry.get_text()
                params.extend([float(radius_str), float(height_str)])
            elif shape_name == "Torus":
                major_r_str = self.torus_major_radius_entry.get_text()
                minor_r_str = self.torus_minor_radius_entry.get_text()
                params.extend([float(major_r_str), float(minor_r_str)])
            elif shape_name == "Prism":
                sides_str = self.prism_sides_entry.get_text()
                radius_str = self.prism_radius_entry.get_text()
                height_str = self.prism_height_entry.get_text()
                params.extend([int(sides_str), float(radius_str), float(height_str)])
            elif shape_name == "Pyramid":
                base_sides_str = self.pyramid_base_sides_entry.get_text()
                base_radius_str = self.pyramid_radius_entry.get_text()
                height_str = self.pyramid_height_entry.get_text()
                params.extend([int(base_sides_str), float(base_radius_str), float(height_str)])
            else:
                print(f"Error: Unknown shape selected: {shape_name}")
                self.generate_button.set_sensitive(True)
                self.stop_generate_button.set_sensitive(False)
                self.IS_SHAPE_GENERATING = False
                return

        except ValueError:
            print("Error: Invalid dimension input. Please ensure all fields contain valid numbers.")
            self.generate_button.set_sensitive(True)
            self.stop_generate_button.set_sensitive(False)
            self.IS_SHAPE_GENERATING = False
            return

        print(f"Starting continuous generation of {shape_name} with parameters: {params}")

        if self.plotter is None or not self._plotter_ready_event.is_set():
            print("Vedo plotter not running or not ready. Starting it now.")
            GLib.idle_add(self._start_vedo_plotter_thread)

        GLib.idle_add(self._start_continuous_shape_generation_thread, shape_name, params)

    def _start_continuous_shape_generation_thread(self, shape_name, params):
        self._continuous_generation_thread = threading.Thread(
            target=self._run_continuous_shape_generation,
            args=(shape_name, params)
        )
        self._continuous_generation_thread.daemon = True
        self._continuous_generation_thread.start()
        return False

    def _run_continuous_shape_generation(self, shape_name, params):
        """
        This function runs in a separate thread.
        It continuously generates and displays shapes as long as IS_SHAPE_GENERATING is True.
        It waits for the Vedo plotter to be ready before sending commands.

        Parameters:
            shape_name (str): The name of the shape to generate (e.g., "Sphere", "Cube").
            params (list): A list of parameters required for the specific shape generation.
        """
        print("Continuous generation thread: Waiting for plotter to be ready...")
        # Block this thread until the Vedo plotter has initialized and set the event.
        self._plotter_ready_event.wait()
        print("Continuous generation thread: Plotter is ready, starting generation loop.")

        while self.IS_SHAPE_GENERATING:
            print(f"Continuous generation: Queuing {shape_name} with {params}")
            # Queue the command to generate and display the shape on the Vedo plotter thread
            #self._plotter_command_queue.put(('generate_shape', shape_name, params))
            shape_index=random.randrange(0,5,1)
            outer_radius = 1.0
            inner_radius = random.randrange(1, 10) * 0.1
            start_latitude_deg = random.randrange(-90, -10, 10)
            end_latitude_deg = random.randrange(10, 90, 10)
            segments = random.randrange(10, 60, 5)
            rings = random.randrange(6, 30, 4)
            generator = SphereGenerator(outer_radius=outer_radius,
                                        inner_radius=inner_radius,
                                        start_latitude_deg=start_latitude_deg,
                                        end_latitude_deg=end_latitude_deg,
                                        segments=segments,
                                        rings=rings
                                        )
            if shape_index==1:
                     outer_bottom_radius = 1.0
                     outer_top_radius = 1.0#random.randrange(1, 101) * 0.01
                     height = 1.0#random.randrange(1, 51) * 0.1
                     inner_bottom_radius = random.randrange(1, 100) * 0.01
                     inner_top_radius = random.randrange(0, int(outer_top_radius*100)) * 0.01
                     maxd=np.max(np.array([outer_radius, outer_bottom_radius, height, inner_bottom_radius, inner_top_radius]))

                     segments = random.randrange(10,60,5)
                     generator = ConeGenerator(outer_bottom_radius=1.5*outer_bottom_radius/maxd,
                                               outer_top_radius=outer_top_radius/maxd,
                                               height=0.2*height/maxd,
                                               inner_bottom_radius=inner_bottom_radius/maxd,
                                               inner_top_radius=inner_top_radius/maxd,
                                               segments=segments
                     )
            if shape_index == 2:
                major_radius = 1.0
                minor_radius = 0.3#random.randrange(2, 5) * 0.1
                inner_radius = random.randrange(1, int(minor_radius*10)) * 0.1
                arc_degrees = random.randrange(90, 91, 20)
                major_segments = random.randrange(10, 90, 10)
                minor_segments = random.randrange(10, 90, 10)
                maxd = np.max(np.array([major_radius, minor_radius, inner_radius]))
                generator = TorusGenerator( major_radius=major_radius/maxd,
                                            minor_radius=minor_radius/maxd,
                                            inner_radius=inner_radius/maxd,
                                            arc_degrees=arc_degrees,
                                            major_segments=major_segments,
                                            minor_segments=minor_segments
                                            )

            if shape_index == 3:

                outer_base_side_length = 1.
                outer_top_side_length = random.randrange(2, 11) * 0.1
                height = random.randrange(1, 51) * 0.1
                inner_base_side_length = random.randrange(1, 10) * 0.1
                inner_top_side_length = random.randrange(0, int(outer_top_side_length*10)) * 0.1
                maxd = np.max( np.array([outer_base_side_length, outer_top_side_length, height, inner_base_side_length, inner_top_side_length]))
                generator = PyramidGenerator(outer_base_side_length=outer_base_side_length/maxd,
                                             outer_top_side_length=outer_top_side_length/maxd,
                                             height=height/maxd,
                                             inner_base_side_length=inner_base_side_length/maxd,
                                             inner_top_side_length=inner_top_side_length/maxd
                                            )

            if shape_index == 4:

                depth = random.randrange(1, 51) * 0.1
                base_wall_thickness = random.randrange(1, 21) * 0.1
                apex_wall_thickness = random.randrange(1, 21) * 0.1
                bottom_wall_thickness = random.randrange(1, 21) * 0.1

                outer_base_side = random.randrange(int(bottom_wall_thickness+1)*2*10, 61) * 0.1
                outer_height = random.randrange(int(apex_wall_thickness+bottom_wall_thickness+1)*10, 61) * 0.1

                maxd = np.max( np.array([depth, base_wall_thickness, apex_wall_thickness, bottom_wall_thickness, outer_base_side, outer_height]))

                generator = PrismGenerator(outer_base_side=outer_base_side/maxd,
                                           outer_height=outer_height/maxd,
                                           base_wall_thickness=base_wall_thickness/maxd,
                                           apex_wall_thickness=apex_wall_thickness/maxd,
                                           bottom_wall_thickness=bottom_wall_thickness/maxd,
                                           depth=depth/maxd
                                            )

            generator.generate_files()
            self._load_and_display_obj_internal_on_plotter_thread(generator.output_obj_filepath)
            # Also queue a command to activate/bring the Vedo window to front
            self._plotter_command_queue.put(('activate_window',))

            for i in range(20):
                self._on_rotate_clicked("x", 15)
                time.sleep(0.1)
            for i in range(20):
                self._on_rotate_clicked("y", 15)
                time.sleep(0.1)
            for i in range(20):
                self._on_rotate_clicked("z", 15)
                time.sleep(0.1)
            # Introduce a delay to control the generation speed and prevent overwhelming the plotter
            time.sleep(1.0)  # Generate a new shape every 1 second

        print("Continuous generation loop finished.")
        # Safely re-enable the 'Generate' button and disable 'Stop' button on the GTK main thread
        GLib.idle_add(self.generate_button.set_sensitive, True)
        GLib.idle_add(self.stop_generate_button.set_sensitive, False)

    def _load_and_display_obj_internal_on_plotter_thread(self, filepath):
        if not self.plotter:
            print("Error: Plotter not available during internal load (Vedo thread).")
            return
        try:
            # Clear all actors from the plotter first for a clean display
            if self.plotter.actors:
                print("Clearing all existing actors from the plotter (Vedo thread)...")
                self.plotter.clear()
                self.plotter.interactor.GetRenderWindow().Render()
                self.current_mesh = None

            print(f"Loading mesh from {filepath} (Vedo thread)...")
            loaded_mesh = vedo.load(filepath)

            if loaded_mesh:
                if not isinstance(loaded_mesh, vedo.Mesh):
                    self.current_mesh = vedo.Mesh(loaded_mesh)
                else:
                    self.current_mesh = loaded_mesh

                print(f"DEBUG: self.current_mesh IS NOW SET to {self.current_mesh.name} after loading.")
                self.current_mesh.name = os.path.basename(filepath)
                self.current_mesh.clean()
                self.plotter.add(self.current_mesh)
                self._apply_material_internal_on_plotter_thread(
                    self.current_color, self.current_opacity,
                    self.current_shininess, self.current_specular,
                    self.current_edge_color, self.current_edge_width,
                    self.current_texture_path
                )
                print('TEXTURE:', self.current_color, self.current_opacity,
                    self.current_shininess, self.current_specular,
                    self.current_edge_color, self.current_edge_width,
                    self.current_texture_path)
                self.plotter.reset_camera()
                self.plotter.interactor.GetRenderWindow().Render()
                self._activate_vedo_window_internal_on_plotter_thread()
                print(f"Successfully displayed {filepath} in Vedo (Vedo thread).")
            else:
                print(f"Failed to load mesh from {filepath}: Vedo returned no mesh object (Vedo thread).")
                print("DEBUG: self.current_mesh IS STILL NONE after attempted load.")
        except Exception as e:
            print(f"ERROR loading or displaying OBJ with Vedo (Vedo thread): {e}")
            if False:
                self.current_mesh = None

    def _generate_and_display_shape_on_plotter_thread(self, shape_name, params):
        if not self.plotter:
            print("Error: Plotter not available during internal shape generation (Vedo thread).")
            return
        try:
            if self.plotter.actors:
                print("Clearing all existing actors from the plotter (Vedo thread)...")
                self.plotter.clear()
                self.plotter.interactor.GetRenderWindow().Render()
                self.current_mesh = None

            new_primitive = None
            if shape_name == "Sphere":
                radius = params[0] if params else 1.0
                new_primitive = vedo.Sphere(r=radius, res=32)
                new_primitive.name = f"Sphere_r{radius}"
            elif shape_name == "Cube":
                sx = params[0] if len(params) > 0 else 1.0
                sy = params[1] if len(params) > 1 else sx
                sz = params[2] if len(params) > 2 else sx
                new_primitive = vedo.Cube([sx, sy, sz])
                new_primitive.name = f"Cube_s{sx}x{sy}x{sz}"
            elif shape_name == "Cylinder":
                radius = params[0] if len(params) > 0 else 0.5
                height = params[1] if len(params) > 1 else 2.0
                new_primitive = vedo.Cylinder(r=radius, height=height, res=32)
                new_primitive.name = f"Cylinder_r{radius}h{height}"
            elif shape_name == "Cone":
                radius = params[0] if len(params) > 0 else 0.5
                height = params[1] if len(params) > 1 else 2.0
                new_primitive = vedo.Cone(r=radius, height=height, res=32)
                new_primitive.name = f"Cone_r{radius}h{height}"
            elif shape_name == "Torus":
                major_radius = params[0] if len(params) > 0 else 1.0
                minor_radius = params[1] if len(params) > 1 else 0.2
                new_primitive = vedo.Torus(r=minor_radius, R=major_radius, res=32)
                new_primitive.name = f"Torus_R{major_radius}r{minor_radius}"
            elif shape_name == "Prism":
                sides = params[0] if len(params) > 0 else 6
                radius = params[1] if len(params) > 1 else 1.0
                height = params[2] if len(params) > 2 else 2.0
                points = vedo.shapes.Disc(pos=(0, 0, 0), r=radius, res=sides).points()
                base_polygon = points[:, :2]
                new_primitive = vedo.shapes.Extrusion(base_polygon, z_min=0, z_max=height)
                new_primitive.name = f"Prism_s{sides}r{radius}h{height}"
            elif shape_name == "Pyramid":
                base_sides = params[0] if len(params) > 0 else 4
                base_radius = params[1] if len(params) > 1 else 1.0
                height = params[2] if len(params) > 2 else 2.0
                new_primitive = vedo.Pyramid(pos=(0, 0, 0), r=base_radius, height=height, n=base_sides)
                new_primitive.name = f"Pyramid_s{base_sides}r{base_radius}h{height}"
            else:
                print(f"Unsupported shape name: {shape_name} (Vedo thread).")
                return

            if new_primitive:
                if not isinstance(new_primitive, vedo.Mesh):
                    self.current_mesh = vedo.Mesh(new_primitive)
                else:
                    self.current_mesh = new_primitive

                print(f"DEBUG: self.current_mesh IS NOW SET to {self.current_mesh.name} after generation.")
                self.current_mesh.clean()
                print(f"Generated {shape_name} successfully (Vedo thread): {self.current_mesh}")
                self.plotter.add(self.current_mesh)
                self._apply_material_internal_on_plotter_thread(
                    self.current_color, self.current_opacity,
                    self.current_shininess, self.current_specular,
                    self.current_edge_color, self.current_edge_width,
                    self.current_texture_path
                )
                self.plotter.reset_camera()
                self.plotter.interactor.GetRenderWindow().Render()
                self._activate_vedo_window_internal_on_plotter_thread()
                print(f"Successfully displayed {shape_name} in Vedo (Vedo thread).")
            else:
                print(f"Failed to generate {shape_name}: No mesh object created (Vedo thread).")
                print("DEBUG: self.current_mesh IS STILL NONE after attempted generation.")

        except Exception as e:
            print(f"ERROR generating or displaying shape with Vedo (Vedo thread): {e}")
            if False:
               self.current_mesh = None

    def _zoom_internal_on_plotter_thread(self, factor):
        if self.plotter and self.plotter.camera:
            print(f"Zooming by {factor} (Vedo thread)...")
            self.plotter.zoom(factor)
            self.plotter.interactor.GetRenderWindow().Render()

    def _rotate_internal_on_plotter_thread(self, axis: str, angle: float):
        print(f"DEBUG: _rotate_internal_on_plotter_thread received command. current_mesh is: {self.current_mesh}")
        print(f"DEBUG: Mesh object ID in rotate: {id(self.current_mesh)}")

        if not self.current_mesh:
            print("No mesh loaded to rotate (Vedo thread).")
            return
        if not self.plotter:
            print("Plotter not available for rotation (Vedo thread).")
            return

        print(
            f"Vedo thread: Executing rotate {axis} by {angle} on mesh {self.current_mesh.name if self.current_mesh else 'None'}")
        try:
            print(f"DEBUG: Mesh pos before rotation: {self.current_mesh.pos()}")

            if axis == "x":
                self.current_mesh.rotate_x(angle)
            elif axis == "y":
                self.current_mesh.rotate_y(angle)
            elif axis == "z":
                self.current_mesh.rotate_z(angle)

            print(f"DEBUG: Mesh pos after rotation: {self.current_mesh.pos()}")

            self.plotter.interactor.GetRenderWindow().Render()
            print(f"Vedo thread: Mesh rotated. Calling render.")
        except Exception as e:
            print(f"Error rotating mesh (Vedo thread): {e}")

    def _activate_vedo_window_internal_on_plotter_thread(self):
        if self.plotter and self.plotter.interactor and self.plotter.interactor.GetRenderWindow():
            try:
                vtk_render_window = self.plotter.interactor.GetRenderWindow()
                vtk_render_window.Frame()
                vtk_render_window.Render()
                print("Vedo window activation attempt successful.")
            except Exception as e:
                print(f"Error attempting to activate Vedo window: {e}")

    def _on_zoom_in_clicked(self, button):
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('zoom', 1.2))

    def _on_zoom_out_clicked(self, button):
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('zoom', 0.8))

    def _on_rotate_clicked(self, axis: str, angle: float):
        print(f"GTK: Rotate command for {axis} by {angle} queued.")
        if self.plotter and self._plotter_ready_event.is_set():
            self._plotter_command_queue.put(('rotate', axis, angle))

    def _on_color_set(self, color_button):
        rgba = color_button.get_rgba()
        self.current_color = (int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255))
        print(f"Color set to: {self.current_color}")

    def _on_opacity_changed(self, scale):
        self.current_opacity = scale.get_value()
        print(f"Opacity set to: {self.current_opacity:.2f}")

    def _on_shininess_changed(self, scale):
        self.current_shininess = scale.get_value()
        print(f"Shininess set to: {self.current_shininess:.0f}")

    def _on_specular_changed(self, scale):
        self.current_specular = scale.get_value()
        print(f"Specular set to: {self.current_specular:.2f}")

    def _on_edge_color_set(self, color_button):
        rgba = color_button.get_rgba()
        self.current_edge_color = (int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255))
        print(f"Edge Color set to: {self.current_edge_color}")

    def _on_edge_width_changed(self, scale):
        self.current_edge_width = scale.get_value()
        print(f"Edge Width set to: {self.current_edge_width:.1f}")

    def _on_load_texture_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Load Texture Image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_pattern("*.png")
        filter_images.add_pattern("*.jpg")
        filter_images.add_pattern("*.jpeg")
        filter_images.add_pattern("*.bmp")
        filter_images.add_pattern("*.tiff")
        dialog.add_filter(filter_images)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            if filepath:
                self.current_texture_path = filepath
                self.texture_label.set_text(os.path.basename(filepath))
                print(f"Texture selected: {filepath}")
            else:
                self.current_texture_path = None
                self.texture_label.set_text("None")
                print("No texture selected.")
        elif response == Gtk.ResponseType.CANCEL:
            print("Texture selection cancelled.")

        dialog.destroy()

    def _on_clear_texture_clicked(self, button):
        self.current_texture_path = None
        self.texture_label.set_text("None")
        print("Texture cleared.")

    def _on_apply_material_clicked(self, button):
        if self.plotter is None or self.current_mesh is None:
            print("No mesh displayed or plotter not active to apply material.")
            return

        print("Applying material properties...")
        self._plotter_command_queue.put(('apply_material',
                                         self.current_color,
                                         self.current_opacity,
                                         self.current_shininess,
                                         self.current_specular,
                                         self.current_edge_color,
                                         self.current_edge_width,
                                         self.current_texture_path))
        self._plotter_command_queue.put(('activate_window',))

    def _apply_material_internal_on_plotter_thread(self, color, opacity, shininess, specular, edge_color, edge_width,
                                                   texture_path):
        if self.current_mesh:
            texture_path = '/home/franklin/Desktop/rospace2/src/naivphys4rp/inverse_simulation/scripts/contextualization/question_answering/brick.jpg'
            print(f"Applying material to mesh {self.current_mesh.name} on Vedo thread.")
            """
            texture = vedo.Texture(texture_path)
            self.current_mesh.texture(texture)
            self.current_mesh.color('white').metallic(0.1).roughness(0.5)
            """

            self.current_mesh.color('green').alpha(1.0)
            """"
            texture=np.zeros((100,100,3), dtype='uint8')
            for i in range(5):
                for j in range(5):
                    texture[20*i:((i+1)*20-1), 20*j:((j+1)*20-1)]=np.random.randint(240, 256, size=(1))
            try:
                os.remove('texture.jpg')
            except Exception as e:
                print('Error: '+str(e))
            cv2.imwrite('texture.jpg', texture)
            """
            #self.generate_texture()
            self.current_mesh.texture('texture.jpg')
            print('Function name:', self.current_mesh.lighting)
            self.current_mesh.specularColor('white').specular(1.0).specularPower(125)
            self.current_mesh.metallic(0.1).roughness(1.0)
            self.current_mesh.shading('phong')

            #self.current_mesh.lighting(style='shiny',
            #                           diffuse=[1.0, 1.0, 1.0],  # Red diffuse color
            #                           ambient=[1.0, 1.0, 1.0],  # Red diffuse color
            #                           specular=[0.5, 0.5, 0.5], # White specular highlight
            #                          specular_power=100.0      # High shininess
            #                          )
            #self.current_mesh.specular(specular)
            #self.current_mesh.shininess(shininess)

            edge_width=0
            if edge_width > 0:
                self.current_mesh.lw(edge_width).lc(edge_color)
            else:
                self.current_mesh.lw(0)

            if texture_path and os.path.exists(texture_path):
                try:
                    self.current_mesh.texture(texture_path)
                    print(f"Texture '{texture_path}' applied.")
                except Exception as e:
                    print(f"Error applying texture {texture_path}: {e}")
                    self.current_mesh.texture(None)
            else:
                self.current_mesh.texture(None)
                print("No valid texture path, clearing texture.")

            self.plotter.interactor.GetRenderWindow().Render()
            print("Material applied on Vedo thread.")
        else:
            print("No current mesh to apply material to on Vedo thread.")


    def generate_texture(self):

        # --- Configuration for the texture ---

        # Image dimensions
        width = 512
        height = 512

        # Perlin noise parameters
        octaves = 2
        # Use different seeds for each color channel for a more interesting result
        seeds = [123, 456, 789]

        # --- Generate the Perlin noise values for each color channel ---

        # Create PerlinNoise objects for Red, Green, and Blue channels
        noise_r = PerlinNoise(octaves=octaves, seed=seeds[0])
        noise_g = PerlinNoise(octaves=octaves, seed=seeds[1])
        noise_b = PerlinNoise(octaves=octaves, seed=seeds[2])

        # Generate 2D arrays of noise values for each channel
        noise_grid_r = [[noise_r([i / width, j / height]) for j in range(width)] for i in range(height)]
        noise_grid_g = [[noise_g([i / width, j / height]) for j in range(width)] for i in range(height)]
        noise_grid_b = [[noise_b([i / width, j / height]) for j in range(width)] for i in range(height)]

        # --- Normalize and combine into a color image ---

        # Convert lists to NumPy arrays
        array_r = np.array(noise_grid_r)
        array_g = np.array(noise_grid_g)
        array_b = np.array(noise_grid_b)

        # Normalize each color channel to the range [0, 1]
        normalized_r = (array_r - array_r.min()) / (array_r.max() - array_r.min())
        normalized_g = (array_g - array_g.min()) / (array_g.max() - array_g.min())
        normalized_b = (array_b - array_b.min()) / (array_b.max() - array_b.min())

        # Scale each channel to the range [0, 255] and convert to integers
        red_channel = (normalized_r * 255 ).astype(np.uint8)
        green_channel = (normalized_g * random.randrange(0, 50)).astype(np.uint8)
        blue_channel = (normalized_b * random.randrange(0, 50)).astype(np.uint8)

        # Stack the channels to form a single 3D array (height, width, 3)
        rgb_data = np.stack([red_channel, green_channel, blue_channel], axis=-1)

        # Create a Pillow Image object from the NumPy array
        texture_image = Image.fromarray(rgb_data, mode='RGB')

        # --- Save the image ---

        # Save the image as a JPG file
        texture_image.save('texture.jpg')

        print("Successfully generated 'texture.jpg'")

    def merge_obj_files(filename1, filename2, id1, id2, filename3):
        """
        Merges two .obj files by aligning a specified face from each.

        Args:
            filename1 (str): Path to the first .obj file.
            filename2 (str): Path to the second .obj file.
            id1 (int): The 0-indexed ID of the face in filename1 to merge.
            id2 (int): The 0-indexed ID of the face in filename2 to merge.
            filename3 (str): Path to save the merged .obj file.
        """
        try:
            # Load the two meshes
            mesh1 = trimesh.load(filename1)
            mesh2 = trimesh.load(filename2)
            print(f"Loaded {filename1} with {len(mesh1.faces)} faces.")
            print(f"Loaded {filename2} with {len(mesh2.faces)} faces.")
        except Exception as e:
            print(f"Error loading files: {e}")
            return

        # Validate face IDs
        if not (0 <= id1 < len(mesh1.faces) and 0 <= id2 < len(mesh2.faces)):
            print("Error: Face IDs are out of range.")
            return

        # --- CORRECTED: Get face properties in a more compatible way ---

        # Get the faces (polygons) and their normal vectors
        face1 = mesh1.faces[id1]
        face2 = mesh2.faces[id2]
        normal1 = mesh1.face_normals[id1]
        normal2 = mesh2.face_normals[id2]

        # Calculate the centroids by averaging the vertices of the face
        centroid1 = np.mean(mesh1.vertices[face1], axis=0)
        centroid2 = np.mean(mesh2.vertices[face2], axis=0)

        # --- Step 1: Calculate the rotation ---

        # The normal of the face in the second mesh needs to be aligned with
        # the normal of the face in the first mesh. We also flip the normal
        # of the second face so it points inward.
        align_vector = -normal1
        rotation_matrix = trimesh.geometry.align_vectors(normal2, align_vector)

        # Apply the rotation to the second mesh
        mesh2.apply_transform(rotation_matrix)

        # --- Step 2: Calculate the translation ---

        # After rotation, the centroid of face2 has moved. We need to
        # re-calculate it to find the translation needed to align it with face1.
        new_centroid2 = trimesh.transform_points(centroid2.reshape(1, 3), rotation_matrix)[0]
        translation_vector = centroid1 - new_centroid2

        # Apply the translation to the second mesh
        mesh2.apply_transform(trimesh.transformations.translation_matrix(translation_vector))

        # --- Step 3: Merge the two meshes ---

        # Combine the vertices and faces of both meshes.
        merged_mesh = trimesh.util.concatenate([mesh1, mesh2])
        print(f"Merged mesh created with {len(merged_mesh.faces)} faces.")

        # --- Step 4: Save the new mesh ---

        # Save the final merged mesh to a new .obj file.
        merged_mesh.export(filename3)
        print(f"Successfully saved merged mesh to {filename3}")


        #merge_obj_files('textured_thick_conical_stalk.obj', 'textured_hollow_torus_arc.obj', 5, 3300,'merged_output.obj')


# --- Main Application Entry Point ---
if __name__ == '__main__':
    win = ObjViewerApp()
    win.show_all()
    Gtk.main()