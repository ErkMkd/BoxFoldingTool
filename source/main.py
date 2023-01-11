# ImGui basics

import harfang as hg
import data_converter as dc
from Backdrops import *
from Draw2D import *
from DebugShape import *
import OBJ_Exporter as OBJ_Exp
from Draw3D import *
import json
import os
import tools2D as t2D
import sys, traceback

# ================================================================
# Main

# Démarrer en fullscreen


# Commande assimp:
# bin\Release\assimp.exe export "in\wavefront\BOULON_M8x15.obj" "out\obj_to_fbx\BOULON_M8x15.fbx" -f fbx

# ================================================================
"""
Version 1.4:
 -Added alpha blending in lines colors - Grid is transparent.

Version 1.4.1:
 -Harfang update
 -Display fixed in DebugShape mode

Version 1.5.0:
 -Added holes
 -Backdrops display alpha intensity setting
 -Save layout (cursor pos, zoom, maps intensity, grid settings) parameters in project files

Version 1.5.1:
 -Added transform box to shapes and holes polygons.
 -Fatal error handler

Version 1.5.2:
 -Multiple vertices selection for moving

Version 1.5.3:
 - Adjustment of the thickness of the splits of a shape

"""


class Main:
    version = "1.5.3"

    flag_error_handler = True

    flag_fatal_error = False
    flag_crashed_saved = False
    fatal_error_stack = None

    flag_running = True
    flag_debug_mode = False
    project_path = ""
    assets_compiled = os.getenv('ALLUSERSPROFILE') + "\\BoxFoldingTool\\assets_compiled"

    error = ""
    flag_deactivate_main_menu = False
    flag_fullscreen = False
    resolution = hg.Vec2(1920, 1080)
    screen_center = hg.Vec2(1920 / 2, 1080 / 2)
    panel_size = hg.Vec2(410, 140)
    state = None
    mouse = None
    keyboard = None
    flag_hovering_gui = False
    flag_popup_opened = False
    flag_splash_screen = True

    splash_logo = None

    current_state_id = 1

    backdrop_state_id = 1
    draw2d_state_id = 2
    draw3d_state_id = 3
    debug_shape_state_id = 4

    project_file_name = ""

    EXPORT_NORMALS_SMOOTH = 1
    EXPORT_NORMALS_FLAT = 2
    current_export_normals_mode = EXPORT_NORMALS_SMOOTH

    load_versions = {}

    @classmethod
    def init(cls):
        cls.state = cls.state_Draw2D
        cls.current_state_id = cls.draw2d_state_id

        cls.mouse = hg.Mouse()
        cls.keyboard = hg.Keyboard()
        cls.screen_center = hg.Vec2((cls.panel_size.x + (1920 - cls.panel_size.x) / 2) / 1920 * cls.resolution.x, cls.resolution.y / 2)
        Draw2D.init(cls.resolution, cls.draw2d_state_id)
        t2D.Edit2DBox.init(Draw2D.vtx_decl, Draw2D.shapes_program)
        Draw3D.init(Draw2D.vtx_decl, Draw2D.shapes_program)
        Backdrops.init(Draw2D.vtx_decl, Draw2D.shapes_program, Draw2D.view2D, Draw2D.texts)
        DebugShape.init(Draw2D.vtx_decl, Draw2D.shapes_program, Draw2D.texts, cls.resolution)

        Draw2D.flag_debug = cls.flag_debug_mode
        Draw3D.flag_debug = cls.flag_debug_mode
        Backdrops.flag_debug = cls.flag_debug_mode

        cls.load_versions = {
            "1.1": cls.load_version1_4,
            "1.2": cls.load_version1_4,
            "1.3": cls.load_version1_4,
            "1.4": cls.load_version1_4,
            "1.4.1": cls.load_version1_4,
            "1.5.0": cls.load_version1_5,
            "1.5.1": cls.load_version1_5,
            "1.5.2": cls.load_version1_5,
            "1.5.3": cls.load_version1_5
        }

    @classmethod
    def get_monitor_mode(cls, width, height):
        monitors = hg.GetMonitors()
        for i in range(monitors.size()):
            monitor = monitors.at(i)
            f, monitorModes = hg.GetMonitorModes(monitor)
            if f:
                for j in range(monitorModes.size()):
                    mode = monitorModes.at(j)
                    if mode.rect.ex == width and mode.rect.ey == height:
                        print("get_monitor_mode() : Width " + str(mode.rect.ex) + " Height " + str(mode.rect.ey))
                        return monitor, j
        return None, 0

    @classmethod
    def get_resolutions(cls):
        resolutions = []
        monitors = hg.GetMonitors()
        for i in range(monitors.size()):
            monitor = monitors.at(i)
            f, monitorModes = hg.GetMonitorModes(monitor)
            if f:
                for j in range(monitorModes.size()):
                    mode = monitorModes.at(j)
                    resolutions.append(hg.Vec2(mode.rect.ex, mode.rect.ey))
        resolutions.sort(key=lambda p: p.x, reverse=True)
        return resolutions

    @classmethod
    def set_resolution(cls, request_resolutions: list = None):

        if request_resolutions is None:
            request_resolutions = cls.get_resolutions()

        if Main.flag_fullscreen:
            for res in request_resolutions:
                monitor, mode_id = cls.get_monitor_mode(res.x, res.y)
                if monitor is not None:
                    Main.resolution = res
                    return hg.NewFullscreenWindow(monitor, mode_id)
            return None
        else:
            for res in request_resolutions:
                win = hg.NewWindow(int(res.x), int(res.y), 0, hg.WV_Hidden)
                f, wx, wy = hg.GetWindowClientSize(win)
                if wx == res.x and wy == res.y:
                    Main.resolution = res
                    hg.DestroyWindow(win)
                    return hg.NewWindow(int(res.x), int(res.y))
                else:
                    hg.DestroyWindow(win)
            return None

    @classmethod
    def update_hovering_ImGui(cls):
        if cls.flag_popup_opened or cls.flag_splash_screen:
            cls.flag_hovering_gui = True
        else:
            if hg.ImGuiWantCaptureMouse() and hg.ReadMouse().Button(hg.MB_0):
                Main.flag_hovering_gui = True
            if Main.flag_hovering_gui and not hg.ReadMouse().Button(hg.MB_0):
                Main.flag_hovering_gui = False

    @classmethod
    def save_project(cls, project_file_name=""):
        if project_file_name == "":
            f, export_path, export_name, project_file_name = cls.input_save_file_name("Save project", "json")
        else:
            f = True
        if f:
            print("Save project : " + project_file_name)
            cls.project_file_name = project_file_name
            project_script = {"shapes": [], "backdrops": Backdrops.get_state(), "layout": Draw2D.view2D.get_state(), "version": cls.version}
            for shape in Draw2D.shapes:
                project_script["shapes"].append(Draw2D.get_shape_state(shape))

            if cls.flag_fatal_error:
                # project_script["fatal_error_message"] = cls.fatal_error_message
                project_script["fatal_error_stack"] = cls.fatal_error_stack
            json_script = json.dumps(project_script, indent=4)

            file = open(project_file_name, "w")
            file.write(json_script)
            file.close()

    @classmethod
    def load_project(cls):
        f, cls.project_file_name = hg.OpenFileDialog("Select a project", "*.json", "")
        if f:
            print("Load project : " + cls.project_file_name)
            project_path = cls.project_file_name.replace(cls.project_file_name.split("/")[-1], "")
            file = open(cls.project_file_name, "r")
            json_script = file.read()
            file.close()
            if json_script != "":
                p_mem = cls.project_file_name
                cls.clear_all()
                cls.project_file_name = p_mem
                project_script = json.loads(json_script)
                if "version" in project_script:
                    vload = project_script["version"]
                    if vload in cls.load_versions:
                        cls.load_versions[vload](project_path, project_script)
                    else:
                        print("UNKNOWN FILE VERSION !")
                else:
                    cls.load_version1_4(project_path, project_script)
        Main.current_state_id = Main.draw2d_state_id
        Main.state = cls.state_Draw2D
        cls.clear_views()
        if len(Draw2D.shapes) > 0:
            Draw2D.set_current_shape(0)
        else:
            Draw2D.current_shape = -1

    @classmethod
    def load_version1_4(cls, project_path, project_script):
        if "backdrops" in project_script:
            Backdrops.set_state(project_script["backdrops"], project_path)
        Draw2D.shapes = []
        for shape_script in project_script["shapes"]:
            shape = Draw2D.new_2d_shape()
            shape["closed"] = shape_script["closed"]
            shape["thickness"] = shape_script["thickness"]
            shape["color"] = dc.list_to_color(shape_script["color"])
            for v in shape_script["vertices"]:
                shape["vertices"].append(dc.list_to_vec2(v))
            for fold_script in shape_script["folds"]:
                fold = Draw2D.new_2d_fold()
                fold["vertices"] = [dc.list_to_vec2(fold_script["vertices"][0]), dc.list_to_vec2(fold_script["vertices"][1])]
                fold["fold_angle"] = fold_script["fold_angle"]
                fold["round_radius"] = fold_script["round_radius"]
                fold["round_segments_count"] = fold_script["round_segments_count"]
                shape["folds"].append(fold)
            if "splits" in shape_script:
                for split_script in shape_script["splits"]:
                    split = Draw2D.new_2d_split()
                    split["vertices"] = [dc.list_to_vec2(split_script["vertices"][0]), dc.list_to_vec2(split_script["vertices"][1])]
                    shape["splits"].append(split)
            Draw2D.add_shape(shape)

    @classmethod
    def load_version1_5(cls, project_path, project_script):
        if "backdrops" in project_script:
            Backdrops.set_state(project_script["backdrops"], project_path)
        if "layout" in project_script:
            Draw2D.view2D.set_state(project_script["layout"])
        Draw2D.shapes = []
        for shape_script in project_script["shapes"]:
            shape = Draw2D.new_2d_shape()
            Draw2D.set_shape_state(shape, shape_script)
            Draw2D.add_shape(shape)

    @classmethod
    def input_save_file_name(cls, title, extension):
        f, export_file_name = hg.SaveFileDialog(title, "*." + extension, "")
        if f:
            export_name = export_file_name.split("/")[-1]
            export_path = export_file_name.replace(export_name, "")
            ext = export_file_name.split(".")[-1].lower()
            if ext != extension.lower():
                export_file_name += "." + extension
            else:
                export_name = export_name.replace("." + export_name.split(".")[-1], "")
            print("Export path: " + export_path + " - Export name: " + export_name + " - Export filename: " + export_file_name)
            return True, export_path, export_name, export_file_name
        return False, "", "", ""

    @classmethod
    def write_OBJ(cls, shape, export_path, export_name):
        if cls.current_export_normals_mode == cls.EXPORT_NORMALS_FLAT:
            OBJ_script, OBJ_mtl = OBJ_Exp.convert_flat_to_obj(export_name, shape["name"], shape["materials"])
        # default mode:
        # if Main.current_export_normals_mode == Main.EXPORT_NORMALS_SMOOTH:
        else:
            OBJ_script, OBJ_mtl = OBJ_Exp.convert_to_obj(export_name, shape["name"], shape["vertices_export"], shape["smooth_normales"], shape["materials"])

        file = open(export_path + export_name + ".obj", "w")
        file.write(OBJ_script)
        file.close()

        file = open(export_path + export_name + ".mtl", "w")
        file.write(OBJ_mtl)
        file.close()

    @classmethod
    def export_current_shape_OBJ(cls):
        shape = Draw2D.get_current_shape()
        if shape is not None and shape["closed"]:
            f, export_path, export_name, export_file_name = cls.input_save_file_name("Export OBJ", "obj")
            if f:
                Draw3D.generate_3D_export(shape)
                cls.write_OBJ(shape, export_path, export_name)
                if cls.current_state_id == cls.draw3d_state_id:
                    Draw3D.generate_3d(shape, True)

    @classmethod
    def export_current_shape_from_OBJ(cls, export_format):
        # bin\Release\assimp.exe export "in\wavefront\BOULON_M8x15.obj" "out\obj_to_fbx\BOULON_M8x15.fbx" - f fbx
        shape = Draw2D.get_current_shape()
        if shape is not None and shape["closed"]:
            f, export_path, export_name, export_file_name = cls.input_save_file_name("Export " + export_format.upper(), export_format)
            if f:
                Draw3D.generate_3D_export(shape)
                # Export to OBJ:
                cls.write_OBJ(shape, export_path, export_name)
                dc.run_command("bin\\assimp\\assimp.exe export \"" + export_path + export_name + ".obj\"" + " \"" + export_path + export_name + "." + export_format + "\" - f " + export_format)
                os.remove(export_path + export_name + ".obj")
                os.remove(export_path + export_name + ".mtl")
                if cls.current_state_id == cls.draw3d_state_id:
                    Draw3D.generate_3d(shape, True)

    @classmethod
    def clear_all(cls):
        Draw3D.remove_all()
        Draw2D.remove_all()
        Backdrops.remove_all()
        DebugShape.clear_all()
        cls.project_file_name = ""

    @classmethod
    def imgui_centered_text_pos(cls, txt, wsize):
        s = hg.ImGuiCalcTextSize(txt)
        cp = hg.ImGuiGetCursorPos()
        cp.x += wsize.x / 2 - s.x / 2
        hg.ImGuiSetCursorPos(cp)

    @classmethod
    def imgui_centered_text(cls, txt, wsize):
        cls.imgui_centered_text_pos(txt, wsize)
        hg.ImGuiText(txt)

    @classmethod
    def imgui_centered_button(cls, txt, wsize):
        cls.imgui_centered_text_pos(txt, wsize)
        return hg.ImGuiButton(txt)

    @classmethod
    def splash_screen(cls):
        wn = "Box Folding Tool "
        if cls.splash_logo is None:
            cls.splash_logo = hg.LoadTextureFromAssets("textures/logo_splash_screen.png", 0)[0]
        if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing):
            size = hg.Vec2(700, 600)
            hg.ImGuiSetWindowPos(wn, hg.Vec2(cls.resolution / 2 - size / 2), hg.ImGuiCond_Always)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(size.x, size.y), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

            hg.ImGuiImage(cls.splash_logo, hg.Vec2(700, 700 / (800 / 500)))

            cls.imgui_centered_text("Box Folding Tool - V " + Main.version, size)
            cls.imgui_centered_text("VirtualPackshot - 2020 / 2021", size)

            cls.imgui_centered_text("Code: Eric Kernin", size)

            # if cls.imgui_centered_button("Close splash",size):
            #	cls.flag_splash_screen = False
            #	hg.DestroyTexture(cls.splash_logo)

            hg.ImGuiEnd()

        if cls.mouse.Pressed(hg.MB_0):
            cls.flag_splash_screen = False
            hg.DestroyTexture(cls.splash_logo)
            cls.splash_logo = None

    @classmethod
    def export_gui(cls, title):
        wn = "Export"
        cls.flag_popup_opened = True
        hg.ImGuiSetWindowPos(wn, hg.Vec2(100, 100), hg.ImGuiCond_Once)
        hg.ImGuiSetWindowSize(wn, hg.Vec2(300, 150), hg.ImGuiCond_Always)

        hg.ImGuiText(title)
        dc.panel_part_separator("NORMALS")

        f, d = hg.ImGuiRadioButton("Smooth", int(Main.current_export_normals_mode), int(Main.EXPORT_NORMALS_SMOOTH))
        if f: Main.current_export_normals_mode = Main.EXPORT_NORMALS_SMOOTH
        f, d = hg.ImGuiRadioButton("Flat", int(Main.current_export_normals_mode), int(Main.EXPORT_NORMALS_FLAT))
        if f: Main.current_export_normals_mode = Main.EXPORT_NORMALS_FLAT

        dc.panel_part_separator("EXPORT")

        if hg.ImGuiButton("OK"):
            hg.ImGuiCloseCurrentPopup()
            cls.flag_popup_opened = False
            return True
        hg.ImGuiSameLine()
        if hg.ImGuiButton("CANCEL"):
            hg.ImGuiCloseCurrentPopup()
            cls.flag_popup_opened = False
            return False
        return False

    @classmethod
    def gui(cls):
        project_lbl = "Project file: " + (cls.project_file_name if cls.project_file_name != "" else "- Undefined -")

        cls.flag_popup_opened = False
        # ----------- Top menu ------------------
        flag_exit_popup = False
        flag_clear_all_popup = False
        flag_export_OBJ_popup = False
        flag_export_FBX_popup = False
        flag_export_GLTF_popup = False
        if hg.ImGuiBeginMainMenuBar():
            if hg.ImGuiBeginMenu("Project"):
                if not cls.flag_deactivate_main_menu:
                    Main.flag_hovering_gui = True  # True when menu opened
                    if hg.ImGuiMenuItem("Load project"):
                        cls.load_project()
                    if hg.ImGuiMenuItem("Save project"):
                        cls.save_project(cls.project_file_name)
                    if hg.ImGuiMenuItem("Save project as"):
                        cls.save_project()
                    if hg.ImGuiMenuItem("Clear all"):
                        flag_clear_all_popup = True
                    hg.ImGuiSpacing()
                    hg.ImGuiSpacing()
                    hg.ImGuiSpacing()
                    hg.ImGuiSpacing()
                    hg.ImGuiSeparator()
                    hg.ImGuiSpacing()
                    if hg.ImGuiMenuItem("Exit"):
                        flag_exit_popup = True
                hg.ImGuiEndMenu()

            if hg.ImGuiBeginMenu("Export"):
                if hg.ImGuiMenuItem("Export to OBJ"):
                    flag_export_OBJ_popup = True
                if hg.ImGuiMenuItem("Export to GLTF"):
                    flag_export_GLTF_popup = True
                if hg.ImGuiMenuItem("Export to FBX"):
                    flag_export_FBX_popup = True
                hg.ImGuiEndMenu()

            if hg.ImGuiBeginMenu("Help"):
                if hg.ImGuiMenuItem("About..."):
                    cls.flag_splash_screen = True
                if hg.ImGuiMenuItem("Debug mode", "", cls.flag_debug_mode):
                    cls.flag_debug_mode = not cls.flag_debug_mode
                    Draw2D.flag_debug = cls.flag_debug_mode
                    Draw3D.flag_debug = cls.flag_debug_mode
                    Backdrops.flag_debug = cls.flag_debug_mode
                    if not cls.flag_debug_mode:
                        if cls.current_state_id == cls.debug_shape_state_id:
                            cls.current_state_id = cls.draw2d_state_id
                            cls.state = cls.state_Draw2D
                            cls.clear_views()
                hg.ImGuiEndMenu()

            if hg.ImGuiBeginMenu(project_lbl, False):
                pass
                hg.ImGuiEndMenu()

            hg.ImGuiEndMainMenuBar()

        if flag_exit_popup:
            hg.ImGuiOpenPopup("Confirm exit")
        if flag_clear_all_popup:
            hg.ImGuiOpenPopup("Confirm clear")
        if flag_export_OBJ_popup:
            hg.ImGuiOpenPopup("Export OBJ")
        if flag_export_FBX_popup:
            hg.ImGuiOpenPopup("Export FBX")
        if flag_export_GLTF_popup:
            hg.ImGuiOpenPopup("Export GLTF")

        wn = "Confirm exit"
        if hg.ImGuiBeginPopup(wn):
            cls.flag_popup_opened = True
            hg.ImGuiSetWindowPos(wn, hg.Vec2(100, 100), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(300, 150), hg.ImGuiCond_Always)
            hg.ImGuiText("Are you sure you want to exit ?")
            if hg.ImGuiButton("YES"):
                cls.flag_running = False
            hg.ImGuiSameLine()

            if hg.ImGuiButton("NO"):
                hg.ImGuiCloseCurrentPopup()

            hg.ImGuiEndPopup()

        wn = "Confirm clear"
        if hg.ImGuiBeginPopup(wn):
            cls.flag_popup_opened = True
            hg.ImGuiSetWindowPos(wn, hg.Vec2(100, 100), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(300, 150), hg.ImGuiCond_Always)
            hg.ImGuiText("Are you sure you want to clear all ?")
            if hg.ImGuiButton("YES"):
                cls.clear_all()
                hg.ImGuiCloseCurrentPopup()
                cls.flag_popup_opened = False
            hg.ImGuiSameLine()
            if hg.ImGuiButton("NO"):
                hg.ImGuiCloseCurrentPopup()
                cls.flag_popup_opened = False

        if hg.ImGuiBeginPopup("Export OBJ"):
            if cls.export_gui("Export OBJ"):
                cls.export_current_shape_OBJ()
            hg.ImGuiEndPopup()
        if hg.ImGuiBeginPopup("Export FBX"):
            if cls.export_gui("Export FBX"):
                cls.export_current_shape_from_OBJ("fbx")
            hg.ImGuiEndPopup()
        if hg.ImGuiBeginPopup("Export GLTF"):
            if cls.export_gui("Export GLTF"):
                cls.export_current_shape_from_OBJ("gltf")
            hg.ImGuiEndPopup()

        # -------------- Main panel --------------
        wn = "Panels"
        if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
            hg.ImGuiSetWindowPos(wn, hg.Vec2(0, 20), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(cls.panel_size.x, cls.panel_size.y), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

            f1, d = hg.ImGuiRadioButton("Backdrops", int(Main.current_state_id), int(Main.backdrop_state_id))
            if f1 and not cls.flag_deactivate_main_menu:
                Main.current_state_id = Main.backdrop_state_id
                Main.state = cls.state_Backdrops
                cls.clear_views()
            f2, d = hg.ImGuiRadioButton("Draw2D", int(Main.current_state_id), int(Main.draw2d_state_id))
            if f2 and not cls.flag_deactivate_main_menu:
                Main.current_state_id = Main.draw2d_state_id
                Main.state = cls.state_Draw2D
                cls.clear_views()
            f3, d = hg.ImGuiRadioButton("Draw3D", int(Main.current_state_id), int(Main.draw3d_state_id))
            if f3 and not cls.flag_deactivate_main_menu:
                cls.setup_3dState()
                Main.current_state_id = Main.draw3d_state_id
                Main.state = cls.state_Draw3D
                cls.clear_views()
            if cls.flag_debug_mode:
                f4, d = hg.ImGuiRadioButton("Debug shape", int(Main.current_state_id), int(Main.debug_shape_state_id))
                if f4 and not cls.flag_deactivate_main_menu:
                    cls.setup_debugShapeState()
                    Main.current_state_id = Main.debug_shape_state_id
                    Main.state = cls.state_DebugShape
                    cls.clear_views()
            else:
                f4 = False

            if f1 or f2 or f3 or f4:
                Backdrops.deselect_all()
            hg.ImGuiEnd()

    @classmethod
    def setup_3dState(cls):
        if 0 <= Draw2D.current_shape < len(Draw2D.shapes):
            shape = Draw2D.get_current_shape()
            if shape["closed"]:
                Draw2D.generates_shape(shape, Draw3D.flag_generate_holes)
                Draw3D.generate_3d(shape)
            if "model" in shape:
                Draw3D.set_current_shape(shape)
            else:
                Draw3D.set_current_shape(None)
        else:
            print("ERROR in Main.setup_3dState")
            Draw3D.set_current_shape(None)

    @classmethod
    def clear_views(cls):
        for i in range(100):
            hg.SetViewClear(i, hg.CF_Color | hg.CF_Depth, 0x00000000, 1.0, 0)
            hg.SetViewRect(i, 0, 0, int(cls.resolution.x), int(cls.resolution.y))
            hg.Touch(i)

    @classmethod
    def state_Draw2D(cls, vid, dts):
        # Draw2D.texts = []
        cls.gui()
        Draw2D.gui(cls.resolution, cls.panel_size)
        if not Main.flag_hovering_gui:
            Draw2D.ui(cls.mouse, cls.keyboard, cls.resolution)
        uiid = Draw2D.get_current_ui_state_id()
        if uiid == Draw2D.UI_STATE_DRAWING:
            cls.flag_deactivate_main_menu = True
        else:
            cls.flag_deactivate_main_menu = False

        Draw2D.update_display(vid, cls.resolution, cls.current_state_id, Draw2D.flag_show_backdrops, dts)

    @classmethod
    def setup_debugShapeState(cls):
        if 0 <= Draw2D.current_shape < len(Draw2D.shapes):
            shape = Draw2D.get_current_shape()
            if shape["closed"]:
                Draw2D.generates_shape(shape, True)
        else:
            print("ERROR in Main.setup_3dState")
            Draw3D.set_current_shape(None)

    @classmethod
    def state_DebugShape(cls, vid, dts):
        # DebugShape.texts = []
        cls.gui()
        DebugShape.gui(cls.resolution, cls.panel_size)
        if not Main.flag_hovering_gui:
            DebugShape.ui(cls.mouse, cls.keyboard, cls.resolution)

        DebugShape.update_display(vid, cls.resolution)

    @classmethod
    def state_Backdrops(cls, vid, dts):
        # Draw2D.texts = []

        cls.gui()
        Backdrops.gui(cls.resolution, cls.panel_size)

        if not Main.flag_hovering_gui:
            Backdrops.ui(cls.mouse, cls.keyboard, cls.resolution)

        Backdrops.flag_enable_uv_widgets = True
        # Backdrops.update_display(vid,cls.resolution)
        Draw2D.update_display(vid, cls.resolution, cls.current_state_id, True, dts)

    @classmethod
    def state_Draw3D(cls, vid, dt):
        cls.gui()
        Draw3D.gui(cls.resolution, cls.panel_size)
        if not Main.flag_hovering_gui:
            Draw3D.ui(cls.mouse, cls.keyboard, cls.resolution)
        Draw3D.update_display(vid, cls.resolution)

    @classmethod
    def fatal_error_handler(cls, vid):
        if not cls.flag_crashed_saved:
            project_crashed = cls.project_file_name + ".crashed.json"
            cls.save_project(project_crashed)
            cls.flag_crashed_saved = True
        wn = "FATAL ERROR"
        wsize = hg.Vec2(600, 200)
        wpos = (cls.resolution - wsize) / 2
        if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
            hg.ImGuiSetWindowPos(wn, wpos, hg.ImGuiCond_Always)
            hg.ImGuiSetWindowSize(wn, wsize, hg.ImGuiCond_Always)
            hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)
            cls.imgui_centered_text("FATAL ERROR - Your project has been saved as 'XXX.crashed.json'.", wsize)
            cls.imgui_centered_text("You can send it to the dev.", wsize)
            cpos = hg.ImGuiGetCursorPos()
            cpos.y += 20
            hg.ImGuiSetCursorPos(cpos)
            if cls.imgui_centered_button("EXIT", wsize):
                cls.flag_running = False
            hg.ImGuiEnd()


# ================================================================
# Main entry
# ================================================================

# --------------------------------------------
# Assets compilation
# --------------------------------------------

print("Box folding tool - V " + Main.version)
print("Compiling assets in " + Main.assets_compiled + " , please wait...")
dc.run_command("bin\\assetc\\assetc.exe assets " + Main.assets_compiled)

print("PROJECT PATH: " + os.path.abspath(os.getcwd()))
print("APPDATA PATH:" + os.getenv('APPDATA'))


# ---------------------------------------------
# Main inits
# ---------------------------------------------


# ==============================================
# Resolution update
# ==============================================

def update_resolution(win, resolution):
    f, wx, wy = hg.GetWindowClientSize(win)
    if wx != int(resolution.x) or wy != int(resolution.y):
        resolution.x = float(wx)
        resolution.y = float(wy)
        hg.RenderReset(wx, wy, hg.RF_VSync | hg.RF_MSAA4X)


# ==============================================
hg.InputInit()
hg.WindowSystemInit()

win = Main.set_resolution()

if win is not None:

    # hg.AddAssetsFolder("assets_compiled")
    hg.AddAssetsFolder(Main.assets_compiled)

    hg.RenderInit(win)
    hg.RenderReset(int(Main.resolution.x), int(Main.resolution.y), hg.RF_VSync | hg.RF_MSAA4X)

    imgui_prg = hg.LoadProgramFromAssets('core/shader/imgui')
    imgui_img_prg = hg.LoadProgramFromAssets('core/shader/imgui_image')
    hg.ImGuiInit(10, imgui_prg, imgui_img_prg)

    Main.init()

    hg.ResetClock()

    # -------------------------------------------------------
    # Main loop
    # -------------------------------------------------------

    while Main.flag_running:
        update_resolution(win, Main.resolution)

        Main.keyboard.Update()
        Main.mouse.Update()

        # w = Main.mouse.Wheel()
        # print("Mouse wheel:" + str(w))

        dt = hg.TickClock()
        dts = hg.time_to_sec_f(dt)

        hg.ImGuiBeginFrame(int(Main.resolution.x), int(Main.resolution.y), dt, Main.mouse.GetState(), Main.keyboard.GetState())

        Main.update_hovering_ImGui()

        Draw2D.debug = False
        if Main.keyboard.Pressed(hg.K_Space):
            Draw2D.debug = True

        # ------ Splash screen:
        if Main.flag_splash_screen:
            Main.splash_screen()
        # ------ View:
        vid = 0
        if not Main.flag_fatal_error:
            if Main.flag_error_handler:
                try:
                    Main.state(vid, dts)
                except:
                    Main.flag_fatal_error = True
                    etype, value, tb = sys.exc_info()
                    Main.fatal_error_stack = traceback.format_exception(etype, value, tb)
            else:
                Main.state(vid, dts)
        else:
            Main.fatal_error_handler(vid)

        # ------ImGui

        # hg.SetViewClear(255, hg.ClearColor | hg.ClearDepth, 0x1f1f1fff, 1.0, 0)
        # hg.SetViewRect(255, 0, 0, res_x,res_y)

        # ------- Eof
        hg.ImGuiEndFrame(255)
        hg.Frame()
        hg.UpdateWindow(win)

    hg.DestroyWindow(win)
