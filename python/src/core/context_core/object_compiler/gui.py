import sys
import os
import PIL.Image
from language_model import *
from PIL import Image, ImageOps
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QFrame, QTextEdit, QMessageBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    import numpy as np
    from pxr import Usd, UsdGeom, Gf, UsdPhysics, UsdShade

    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

from compiler import *


class NaivPhysGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("naivphys4rp - PESG Visual Interface")
        self.resize(1400, 850)
        self.temp_image_path = "gui_temp_crop.jpg"
        self.engine = PESGEngine()
        self.compiler = ObjectCompiler()
        self.usd_info = {}
        self.hierarchy = {}  # Map: parent_prim_path -> list of child_prim_paths

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        quad_layout = QHBoxLayout()

        # Q1: Image Loader
        q1_frame = QFrame()
        q1_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        vbox1 = QVBoxLayout(q1_frame)
        vbox1.addWidget(QLabel("<b>1. IMAGE INPUT</b>"))
        self.img_label = QLabel("Select Image")
        self.img_label.setFixedSize(300, 300)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background-color: #1a1a1a; border: 2px dashed #555;")
        vbox1.addWidget(self.img_label)
        btn_load = QPushButton("Select Image File")
        btn_load.clicked.connect(self.handle_upload)
        vbox1.addWidget(btn_load)

        # Q2: Console
        q2_frame = QFrame()
        q2_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        vbox2 = QVBoxLayout(q2_frame)
        vbox2.addWidget(QLabel("<b>2. VLM CONSOLE</b>"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: 'Monospace';")
        vbox2.addWidget(self.console)

        # Q3: 3D Rendering
        q3_frame = QFrame()
        q3_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        vbox3 = QVBoxLayout(q3_frame)
        vbox3.addWidget(QLabel("<b>3. 3D USD PREVIEW</b>"))
        if PYVISTA_AVAILABLE:
            self.plotter = QtInteractor(q3_frame)
            vbox3.addWidget(self.plotter.interactor)
            self.plotter.set_background("black")
        else:
            vbox3.addWidget(QLabel("PyVista not detected."))

        quad_layout.addWidget(q1_frame)
        quad_layout.addWidget(q2_frame)
        quad_layout.addWidget(q3_frame)
        main_layout.addLayout(quad_layout)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("RUN INFERENCE")
        self.run_btn.setFixedHeight(50)
        self.run_btn.setStyleSheet("background-color: #1b5e20; color: white;")
        self.run_btn.clicked.connect(self.run_inference)
        reset_btn = QPushButton("RESET")
        reset_btn.setFixedHeight(50)
        reset_btn.clicked.connect(self.reset_all)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(reset_btn)
        main_layout.addLayout(btn_layout)

    def handle_upload(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.jpg *.png *.jpeg)")
        if path:
            try:
                img = Image.open(path)
                cropped = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
                cropped.save(self.temp_image_path)
                qimg = QImage(self.temp_image_path)
                pixmap = QPixmap.fromImage(qimg).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio)
                self.img_label.setPixmap(pixmap)
                self.console.append(f"<b>[SYSTEM]</b> Image prepped.")
            except Exception as e:
                QMessageBox.critical(self, "Upload Error", f"{e}")

    def run_inference(self):
        if not os.path.exists(self.temp_image_path):
            QMessageBox.warning(self, "Warning", "Upload an image first!")
            return
        self.console.append("\n<b>[PROCESSING]</b> Starting...")
        QApplication.processEvents()
        try:
            img = PIL.Image.open(self.temp_image_path)
            params = self.engine.induce_grammar(img)
            self.console.append(f"\n<b>[VLM]:</b>\n{params}")
            paths, json_code = self.compiler.compile_object_from_json_v2(params)
            obj_path, usd_code = paths[0], paths[1]
            self.console.append(f"\n\n<font color='white'><b>[OBJECT SEMANTICS AND STRUCTURE]:</b> {json_code}</font>")
            self.console.append(f"\n\n<font color='green'><b>[USDA OBJECT COMPILATION]:</b> {usd_code}</font>")

            if PYVISTA_AVAILABLE:
                self.load_usd_model(obj_path)
        except Exception as e:
            self.console.append(f"\n<font color='red'><b>[ERROR]:</b> {e}</font>")

    def load_usd_model(self, usd_path):
        try:
            stage = Usd.Stage.Open(usd_path)
            self.plotter.clear()
            self.usd_info = {}
            self.hierarchy = {}
            time = Usd.TimeCode.Default()
            base_dir = os.path.dirname(usd_path)

            # --- PART 1: MESH & TEXTURE LOADING ---
            for prim in stage.Traverse():
                if not prim.IsA(UsdGeom.Mesh): continue

                mesh_geom = UsdGeom.Mesh(prim)
                xformable = UsdGeom.Xformable(prim)

                gf_mat = xformable.ComputeLocalToWorldTransform(time)
                matrix = np.array(gf_mat).reshape(4, 4).T
                pts = np.array(mesh_geom.GetPointsAttr().Get())
                f_counts = np.array(mesh_geom.GetFaceVertexCountsAttr().Get())
                f_indices = np.array(mesh_geom.GetFaceVertexIndicesAttr().Get())

                p_api = UsdGeom.PrimvarsAPI(prim)
                uv_p = p_api.GetPrimvar("st") or p_api.GetPrimvar("uv")
                uv_data = uv_p.ComputeFlattened() if uv_p and uv_p.HasValue() else None

                tex_image = None
                mat_bind = UsdShade.MaterialBindingAPI(prim)
                bound_mat = mat_bind.ComputeBoundMaterial()[0]
                if bound_mat:
                    sources = bound_mat.ComputeSurfaceSource()
                    if sources:
                        shader = sources[0]
                        diff_in = shader.GetInput("diffuseColor")
                        if diff_in and diff_in.HasConnectedSource():
                            tex_node = UsdShade.Shader(diff_in.GetConnectedSource()[0])
                            file_in = tex_node.GetInput("file")
                            if file_in:
                                raw_path = str(file_in.Get()).strip("@")
                                full_path = os.path.join(base_dir, raw_path)
                                if os.path.exists(full_path):
                                    tex_image = Image.open(full_path).convert('RGB')

                pv_f = []
                idx_ptr = 0
                for count_np in f_counts:
                    count = int(count_np)
                    pv_f.append(count)
                    pv_f.extend(f_indices[idx_ptr:idx_ptr + count])
                    idx_ptr += count
                mesh = pv.PolyData(pts, pv_f)

                n_cells = mesh.n_cells
                semantic_rgb = np.zeros((n_cells, 3), dtype=np.float32)

                if tex_image and uv_data is not None:
                    px_array = tex_image.load()
                    w, h = tex_image.size
                    uv_ptr = 0
                    for i in range(n_cells):
                        count = int(f_counts[i])
                        face_uvs = uv_data[uv_ptr: uv_ptr + count]
                        avg_uv = np.mean(face_uvs, axis=0)
                        px = int(avg_uv[0] * (w - 1))
                        py = int((1.0 - avg_uv[1]) * (h - 1))
                        px, py = max(0, min(w - 1, px)), max(0, min(h - 1, py))
                        r, g, b = px_array[px, py]
                        semantic_rgb[i] = [r / 255.0, g / 255.0, b / 255.0]
                        uv_ptr += count
                else:
                    semantic_rgb[:] = [0.7, 0.7, 0.7]

                mesh.cell_data["Semantic_Colors"] = semantic_rgb
                mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)

                actor = self.plotter.add_mesh(
                    mesh, scalars="Semantic_Colors", rgb=True, preference="cell",
                    lighting=True, smooth_shading=True, ambient=0.7, diffuse=0.3
                )

                prim_path = str(prim.GetPath())
                self.usd_info[prim_path] = {
                    "actor": actor,
                    "base_matrix": matrix,
                    "path": prim_path
                }
                actor.user_matrix = matrix

            # --- PART 2: HIERARCHY MAPPING & JOINT SLIDER GENERATION ---
            current_y = 0.9
            for prim in stage.Traverse():
                is_rev = prim.IsA(UsdPhysics.RevoluteJoint)
                is_pris = prim.IsA(UsdPhysics.PrismaticJoint)
                is_fixed = prim.IsA(UsdPhysics.FixedJoint)

                if not (is_rev or is_pris or is_fixed): continue

                joint = UsdPhysics.Joint(prim)
                p_targets = joint.GetBody0Rel().GetTargets()
                c_targets = joint.GetBody1Rel().GetTargets()

                if p_targets and c_targets:
                    p_path, c_path = str(p_targets[0]), str(c_targets[0])
                    if p_path not in self.hierarchy:
                        self.hierarchy[p_path] = []
                    self.hierarchy[p_path].append(c_path)

                if is_fixed: continue

                child_path = str(c_targets[0])
                local_pos = prim.GetAttribute("physics:localPos0").Get() or Gf.Vec3f(0)
                pivot = np.array(local_pos, dtype=np.float64)

                axis_t = prim.GetAttribute("physics:axis").Get() or "Z"
                ax_vec = {"X": Gf.Vec3d(1, 0, 0), "Y": Gf.Vec3d(0, 1, 0), "Z": Gf.Vec3d(0, 0, 1)}.get(axis_t)

                low = prim.GetAttribute("physics:lowerLimit").Get() or (-180 if is_rev else -0.5)
                high = prim.GetAttribute("physics:upperLimit").Get() or (180 if is_rev else 0.5)

                # Passing child_path directly as the root of movement
                self.plotter.add_slider_widget(
                    callback=lambda val, cp=child_path, v=ax_vec, r=is_rev, p=pivot: self.update_joint(val, cp, v, r,
                                                                                                       p),
                    rng=[low, high], value=0, title=prim.GetName(),
                    pointa=(0.05, current_y), pointb=(0.25, current_y),
                    style='modern', interaction_event='always', fmt="%.2f"
                )
                current_y -= 0.12

            self.plotter.view_isometric()
            self.plotter.render()

        except Exception as e:
            self.console.append(f"<font color='red'><b>[USD ERROR]:</b> {e}</font>")

    def _get_all_descendants(self, path, collected_paths):
        """Recursively find all children paths in the hierarchy."""
        collected_paths.add(path)
        if path in self.hierarchy:
            for child in self.hierarchy[path]:
                self._get_all_descendants(child, collected_paths)

    def update_joint(self, val, root_path, vec, is_revolute, pivot):
        threshold = 2.0 if is_revolute else 0.001
        if abs(val) < threshold:
            val = 0.0

        if is_revolute:
            p_vec = Gf.Vec3d(float(pivot[0]), float(pivot[1]), float(pivot[2]))
            rot_mat = Gf.Matrix4d().SetRotate(Gf.Rotation(vec, float(val)))
            joint_mat_gf = Gf.Matrix4d().SetTranslate(-p_vec) * rot_mat * Gf.Matrix4d().SetTranslate(p_vec)
        else:
            joint_mat_gf = Gf.Matrix4d().SetTranslate(vec * float(val))

        movement_np = np.array(joint_mat_gf).reshape(4, 4).T

        # 1. Identify all logically linked descendant paths
        logical_paths = set()
        self._get_all_descendants(root_path, logical_paths)

        # 2. Match against actual geometry in usd_info using prefix matching
        for info_path, info in self.usd_info.items():
            should_move = False
            # Check if info_path is one of the logical paths OR a child of one
            for l_path in logical_paths:
                if info_path == l_path or info_path.startswith(l_path + "/"):
                    should_move = True
                    break

            if should_move:
                info["actor"].user_matrix = movement_np @ info["base_matrix"]

        self.plotter.render()

    def reset_all(self):
        self.console.clear()
        self.img_label.clear()
        self.img_label.setText("Select Image")

        if PYVISTA_AVAILABLE:
            # 1. Explicitly remove all slider widgets first
            self.plotter.clear_slider_widgets()

            # 2. Clear actors and reset the renderer
            self.plotter.clear()

            # 3. Re-establish background
            self.plotter.set_background("black")

            # 4. Force the interactor to reset its internal camera/interaction state
            self.plotter.reset_camera()

        self.usd_info = {}
        self.hierarchy = {}

        # Cleanup temp file if exists
        if os.path.exists(self.temp_image_path):
            try:
                os.remove(self.temp_image_path)
            except:
                pass

        self.console.append("<b>[SYSTEM]</b> Reset complete.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NaivPhysGUI()
    window.show()
    sys.exit(app.exec())