# ================================================================
#  Backdrops
# ================================================================

import harfang as hg
from math import exp
import data_converter as dc
import tools2D as t2D
import os


class Backdrops:
    flag_debug = False

    error = ""

    view2D = None
    texts = None

    default_texture_filename = "textures/default.jpg"
    default_texture = None
    bitmap_filename = "textures/default.jpg"
    build_map_filename = ""
    inside_texture_filename = ""
    bitmap = None
    bitmap_texture = None
    build_map_texture = None
    inside_picture = None
    inside_texture = None
    build_map = None
    bitmap_sprite = None
    build_map_sprite = None

    flag_bitmap_selected = False
    flag_build_map_selected = False

    spr_program = None
    spr_decl = None
    spr_model = None
    spr_render_state = None
    spr_uniform = None
    spr_texture = None

    vtx_decl = None
    line_program = None

    current_edit_box = None

    @classmethod
    def init(cls, vtx_decl_2d, program_2d, view2D, text_overlay: t2D.TextOverlay):

        cls.view2D = view2D
        cls.texts = text_overlay
        cls.vtx_decl = vtx_decl_2d
        cls.line_program = program_2d

        cls.spr_program = hg.LoadProgramFromAssets("shaders/sprite.vsb", "shaders/sprite.fsb")

        cls.spr_decl = hg.VertexLayout()
        cls.spr_decl.Begin()
        cls.spr_decl.Add(hg.A_Position, 3, hg.AT_Float)
        cls.spr_decl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
        cls.spr_decl.End()

        cls.spr_uniform = hg.UniformSetValueList()
        cls.spr_texture = hg.UniformSetTextureList()

        cls.spr_model = hg.CreatePlaneModel(cls.spr_decl, 1, 1, 1, 1)

        cls.spr_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

        cls.maps_names = ["Texture", "Coupes", "Texture + Coupes"]
        cls.current_map = 0

        cls.default_texture = hg.LoadTextureFromAssets(cls.default_texture_filename, 0)[0]

    @classmethod
    def remove_all(cls):
        if cls.bitmap_texture is not None:
            hg.DestroyTexture(cls.bitmap_texture)
            cls.bitmap_texture = None
            cls.bitmap_sprite = None
            cls.bitmap = None
        if cls.build_map_texture is not None:
            hg.DestroyTexture(cls.build_map_texture)
            cls.build_map_texture = None
            cls.build_map_sprite = None
            cls.build_map = None
        if cls.inside_texture is not None:
            hg.DestroyTexture(cls.inside_texture)
            cls.inside_texture = None

    @classmethod
    def get_state(cls):
        state = {}
        if cls.bitmap_sprite is not None:
            state.update({"bitmap": cls.bitmap_filename,  # (os.path.relpath(cls.bitmap_filename)).replace("\\","/")
                          "bitmap_position": dc.vec2_to_list(cls.bitmap_sprite["position"]),
                          "bitmap_scale": cls.bitmap_sprite["scale"]
                          })
        if cls.build_map_sprite is not None:
            state.update({"build_map": cls.build_map_filename,  # (os.path.relpath(cls.build_map_filename)).replace("\\","/")
                          "build_map_position": dc.vec2_to_list(cls.build_map_sprite["position"]),
                          "build_map_scale": cls.build_map_sprite["scale"]
                          })
        if cls.inside_texture is not None:
            state.update({"inside_map": cls.inside_texture_filename})
        else:
            state.update({"inside_map": cls.default_texture_filename})
        return state

    @classmethod
    def set_state(cls, bd_script, project_path):
        cls.remove_all()
        if "bitmap" in bd_script:
            cls.bitmap_filename = bd_script["bitmap"]
            if not cls.load_bitmap(cls.bitmap_filename):
                if cls.load_bitmap(project_path + cls.bitmap_filename.split("/")[-1]):
                    cls.bitmap_filename = project_path + cls.bitmap_filename.split("/")[-1]
                else:
                    print("Copy texture file to same project path: " + project_path)
            if cls.bitmap_sprite is not None:
                cls.bitmap_sprite["scale"] = bd_script["bitmap_scale"]
                cls.bitmap_sprite["position"] = dc.list_to_vec2(bd_script["bitmap_position"])
                cls.update_sprite_edit_box(cls.bitmap_sprite)
        if "build_map" in bd_script:
            cls.build_map_filename = bd_script["build_map"]
            if not cls.load_build_map(cls.build_map_filename):
                if cls.load_build_map(project_path + cls.build_map_filename.split("/")[-1]):
                    cls.build_map_filename = project_path + cls.build_map_filename.split("/")[-1]
                else:
                    print("Copy texture file to same project path: " + project_path)
            if cls.build_map_sprite is not None:
                cls.build_map_sprite["scale"] = bd_script["build_map_scale"]
                cls.build_map_sprite["position"] = dc.list_to_vec2(bd_script["build_map_position"])
                cls.update_sprite_edit_box(cls.build_map_sprite)

        if "inside_map" in bd_script:
            cls.inside_texture_filename = bd_script["inside_map"]
            if not cls.load_inside_map(cls.inside_texture_filename):
                if cls.load_inside_map(project_path + cls.inside_texture_filename.split("/")[-1]):
                    cls.inside_texture_filename = project_path + cls.inside_texture_filename.split("/")[-1]
                else:
                    print("Copy inside texture file to same project path: " + project_path)

    @classmethod
    def create_uv_widget(cls, name, npos):
        return {"name": name, "normalized_pos": npos, "pos": hg.Vec2(0, 0), "screen_pos": hg.Vec2(0, 0)}

    @classmethod
    def update_sprite_edit_box(cls, sprite):
        eb = sprite["edit_box"]
        eb.set_scale(sprite["scale"])
        eb.set_position(sprite["position"])

    @classmethod
    def remove_bitmap(cls):
        if cls.bitmap_texture is not None:
            hg.DestroyTexture(cls.bitmap_texture)
        cls.bitmap_texture = None
        cls.bitmap_sprite = None
        cls.bitmap = None

    @classmethod
    def load_bitmap(cls, bitmap_filename):
        if bitmap_filename != "":
            cls.remove_bitmap()
            cls.bitmap = hg.Picture()
            if not hg.LoadPicture(cls.bitmap, bitmap_filename):
                cls.error = "ERROR - Unable to load bitmap texture : " + cls.bitmap_filename
                cls.bitmap = None
                return False
            else:
                print("bitmap size: " + str(cls.bitmap.GetWidth()) + " * " + str(cls.bitmap.GetHeight()))
                cls.bitmap_texture = hg.CreateTextureFromPicture(cls.bitmap, "bitmap", 0)
                cls.bitmap_sprite = {"position": hg.Vec2(0, 0), "scale": 50, "width": cls.bitmap.GetWidth(), "height": cls.bitmap.GetHeight(), "texture": hg.MakeUniformSetTexture("s_tex", cls.bitmap_texture, 0), "edit_box": None}
                cls.bitmap_sprite["edit_box"] = t2D.Edit2DBox(t2D.Edit2DBox.FLAG_SCALE|t2D.Edit2DBox.FLAG_MOVE, cls.bitmap_sprite["position"], hg.Vec2(cls.bitmap_sprite["width"] / cls.bitmap_sprite["height"], 1), hg.Vec2(cls.bitmap_sprite["scale"], cls.bitmap_sprite["scale"]))
                return True
        return False

    @classmethod
    def remove_inside_map(cls):
        if cls.inside_texture is not None:
            hg.DestroyTexture(cls.inside_texture)
        cls.inside_texture = None
        cls.inside_picture = None

    @classmethod
    def load_inside_map(cls, inside_map_filename):
        if inside_map_filename != "":
            cls.remove_inside_map()
            cls.inside_picture = hg.Picture()
            if not hg.LoadPicture(cls.inside_picture, inside_map_filename):
                cls.error = "ERROR - Unable to load inside texture : " + inside_map_filename
                return False
            else:
                print("inside texture size: " + str(cls.inside_picture.GetWidth()) + " * " + str(cls.inside_picture.GetHeight()))
                cls.inside_texture = hg.CreateTextureFromPicture(cls.inside_picture, "inside_texture", 0)
                return True
        return False

    @classmethod
    def remove_build_map(cls):
        if cls.build_map_texture is not None:
            hg.DestroyTexture(cls.build_map_texture)
        cls.build_map_texture = None
        cls.build_map_sprite = None
        cls.build_map = None

    @classmethod
    def load_build_map(cls, build_map_filename):
        if build_map_filename != "":
            cls.remove_build_map()
            cls.build_map = hg.Picture()
            if not hg.LoadPicture(cls.build_map, build_map_filename):
                cls.error = "ERROR - Unable to load build map texture : " + cls.build_map_filename
                cls.build_map = None
                return False
            else:
                print("build_map size: " + str(cls.build_map.GetWidth()) + " * " + str(cls.build_map.GetHeight()))
                cls.build_map_texture = hg.CreateTextureFromPicture(cls.build_map, "build_map", 0)
                cls.build_map_sprite = {"position": hg.Vec2(0, 0), "scale": 50, "width": cls.build_map.GetWidth(), "height": cls.build_map.GetHeight(), "texture": hg.MakeUniformSetTexture("s_tex", cls.build_map_texture, 0), "edit_box": None}
                cls.build_map_sprite["edit_box"] = t2D.Edit2DBox(t2D.Edit2DBox.FLAG_SCALE|t2D.Edit2DBox.FLAG_MOVE, cls.build_map_sprite["position"], hg.Vec2(cls.build_map_sprite["width"] / cls.build_map_sprite["height"], 1),
                                                                 hg.Vec2(cls.build_map_sprite["scale"], cls.build_map_sprite["scale"]))
                return True
        return False

    @classmethod
    def display_maps(cls, vid):
        if cls.bitmap_sprite is not None: cls.display_sprite(vid, cls.bitmap_sprite["position"], cls.bitmap_sprite["scale"], cls.bitmap_sprite["width"], cls.bitmap_sprite["height"], cls.bitmap_sprite["texture"], cls.view2D.backdrops_intensity)
        if cls.build_map_sprite is not None: cls.display_sprite(vid, cls.build_map_sprite["position"], cls.build_map_sprite["scale"], cls.build_map_sprite["width"], cls.build_map_sprite["height"], cls.build_map_sprite["texture"], cls.view2D.backdrops_intensity)

    @classmethod
    def display_edit_boxes(cls, vid, view: t2D.View2D, resolution: hg.Vec2):

        if cls.current_edit_box is not None:
            cls.current_edit_box["Edit2DBox"].display(vid, view, resolution)

    @classmethod
    def display_sprite(cls, v_id, position, scale, width, height, uniform_target_tex: hg.UniformSetTexture, alpha=1):

        # set the uniforms
        cls.spr_uniform.clear()
        cls.spr_texture.clear()
        cls.spr_texture.push_back(uniform_target_tex)
        cls.spr_uniform.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, alpha)))

        mat = hg.TransformationMat4(hg.Vec3(position.x, position.y, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1))

        ratio = width / height
        hg.SetScale(mat, hg.Vec3(scale * ratio, 1, scale))

        hg.DrawModel(v_id, cls.spr_model, cls.spr_program, cls.spr_uniform, cls.spr_texture, mat, cls.spr_render_state)

    @classmethod
    def get_edit_box(cls):
        f = False
        if cls.flag_build_map_selected and cls.flag_bitmap_selected:
            eb = t2D.Edit2DBox.addBoxes(t2D.Edit2DBox.FLAG_SCALE|t2D.Edit2DBox.FLAG_MOVE, [cls.bitmap_sprite["edit_box"], cls.build_map_sprite["edit_box"]])
            return {"Edit2DBox": eb,
                    "sprites": [cls.bitmap_sprite, cls.build_map_sprite],
                    "start_scales": [cls.bitmap_sprite["scale"], cls.build_map_sprite["scale"]],
                    "start_pos": [cls.bitmap_sprite["position"] - eb.position, cls.build_map_sprite["position"] - eb.position]}
        elif cls.flag_bitmap_selected:
            spr = cls.bitmap_sprite
            f = True
        elif cls.flag_build_map_selected:
            spr = cls.build_map_sprite
            f = True

        if f:
            return {"Edit2DBox": spr["edit_box"], "sprites": [spr]}

        return None

    @classmethod
    def select_map(cls, mouse: hg.Mouse, keyboard: hg.Keyboard, resolution: hg.Vec2):

        if cls.current_edit_box is not None:
            if cls.current_edit_box["Edit2DBox"].get_ui_state() != t2D.Edit2DBox.UI_STATE_IDLE:
                return

        if mouse.Pressed(hg.MB_0):
            ms = hg.Vec2(mouse.X(), mouse.Y())
            mp = cls.view2D.get_point_plane(ms, resolution)
            if cls.bitmap_sprite is not None:
                if cls.bitmap_sprite["edit_box"].contains(mp):
                    if keyboard.Down(hg.K_LCtrl):
                        cls.flag_bitmap_selected = not cls.flag_bitmap_selected
                    else:
                        cls.flag_bitmap_selected = True
                        cls.flag_build_map_selected = False
                else:
                    if not keyboard.Down(hg.K_LCtrl):
                        cls.flag_bitmap_selected = False
            if cls.build_map_sprite is not None:
                if cls.build_map_sprite["edit_box"].contains(mp):
                    if keyboard.Down(hg.K_LCtrl):
                        cls.flag_build_map_selected = not cls.flag_build_map_selected
                    else:
                        cls.flag_bitmap_selected = False
                        cls.flag_build_map_selected = True
                else:
                    if not keyboard.Down(hg.K_LCtrl):
                        cls.flag_build_map_selected = False
            cls.current_edit_box = cls.get_edit_box()

    @classmethod
    def edit_map(cls, mouse: hg.Mouse, keyboard: hg.Keyboard, resolution):

        if cls.current_edit_box is not None:
            eb = cls.current_edit_box["Edit2DBox"]
            if eb.ui(mouse, keyboard, cls.view2D, resolution):
                if len(cls.current_edit_box["sprites"]) > 1:
                    for sidx in range(len(cls.current_edit_box["sprites"])):
                        sprite = cls.current_edit_box["sprites"][sidx]
                        str_scale = cls.current_edit_box["start_scales"][sidx]
                        str_pos = cls.current_edit_box["start_pos"][sidx]
                        sprite["scale"] = eb.scale.x * str_scale
                        sprite["position"] = eb.position + str_pos * eb.scale.x
                        sprite["edit_box"].position.x, sprite["edit_box"].position.y = sprite["position"].x, sprite["position"].y
                        sprite["edit_box"].set_scale(sprite["scale"])
                else:
                    sprite = cls.current_edit_box["sprites"][0]
                    sprite["position"].x = eb.position.x
                    sprite["position"].y = eb.position.y
                    sprite["scale"] = eb.scale.x

            if eb.message != "":
                cls.texts.push({"text": eb.message, "pos": hg.Vec2(mouse.X() + 10, mouse.Y() - 35) / resolution, "font": cls.texts.font_small, "color": hg.Color(0, 1, 1, 1)})

        """
        if mouse.Down(hg.MB_0):
            maps = cls.get_editBox()
            mdx = mouse.DtX()
            mdy = mouse.DtY()
            md = hg.Vec2(mdx / resolution.y, mdy / resolution.y) * cls.view2D.view_scale
            for map in maps:
                if map is not None:
                    map["position"].x += md.x
                    map["position"].y += md.y
        """

    @classmethod
    def deselect_all(cls):
        cls.flag_build_map_selected = False
        cls.flag_bitmap_selected = False
        cls.current_edit_box = None

    @classmethod
    def gui(cls, resolution, main_panel_size):
        wn = "Backdrops"
        if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
            hg.ImGuiSetWindowPos(wn, hg.Vec2(0, 20 + main_panel_size.y), hg.ImGuiCond_Always)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(main_panel_size.x, resolution.y - 20 - main_panel_size.y), hg.ImGuiCond_Always)
            hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

            dc.panel_part_separator("OUTSIDE", 10)

            if hg.ImGuiButton("Load outside texture"):
                cls.bitmap_filename = hg.OpenFileDialog("Select outside texture", "*.png;*.PNG;*.*", "")[1]
                cls.load_bitmap(cls.bitmap_filename)
            if cls.bitmap is not None:
                hg.ImGuiSameLine()
                if hg.ImGuiButton("Remove outside texture"):
                    cls.remove_bitmap()

            if hg.ImGuiButton("Load build map"):
                cls.build_map_filename = hg.OpenFileDialog("Select build map", "*.png;*.PNG;*.*", "")[1]
                cls.load_build_map(cls.build_map_filename)
            if cls.build_map is not None:
                hg.ImGuiSameLine()
                if hg.ImGuiButton("Remove build map"):
                    cls.remove_build_map()

            hg.ImGuiText("Maps:")

            hg.ImGuiText("Backdrops intensity")
            f, d = hg.ImGuiSliderFloat(" ##bi", cls.view2D.backdrops_intensity, 0, 1)
            if f:
                cls.view2D.backdrops_intensity = d

            f1, f2 = False, False
            if cls.bitmap_sprite is not None:
                f1, cls.flag_bitmap_selected = hg.ImGuiCheckbox("Texture", cls.flag_bitmap_selected)
                hg.ImGuiSameLine()


            if cls.build_map_sprite is not None:
                f2, cls.flag_build_map_selected = hg.ImGuiCheckbox("Build map", cls.flag_build_map_selected)

            if f1 or f2:
                cls.current_edit_box = cls.get_edit_box()

            dc.panel_part_separator("INSIDE", 10)

            if hg.ImGuiButton("Load inside texture"):
                cls.inside_texture_filename = hg.OpenFileDialog("Select inside texture", "*.png;*.PNG;*.jpg;*.JPG;*.*", "")[1]
                cls.load_inside_map(cls.inside_texture_filename)
            if cls.inside_texture is not None:
                hg.ImGuiSameLine()
                if hg.ImGuiButton("Remove inside texture"):
                    cls.remove_inside_map()
                else:
                    hg.ImGuiImage(cls.inside_texture, hg.Vec2(main_panel_size.x - 50, main_panel_size.x - 50), hg.Vec2(0, 0), hg.Vec2(1, 1), hg.Color.White, hg.Color.White)
            hg.ImGuiEnd()

    @classmethod
    def ui(cls, mouse, keyboard, resolution):
        cls.texts.clear()
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        cls.edit_map(mouse, keyboard, resolution)
        cls.select_map(mouse, keyboard, resolution)

    @classmethod
    def update_display(cls, vid, resolution):
        # Affichage de test, Backdrops utilise Draw2D.update_display()
        hg.SetViewClear(vid, hg.ClearColor | hg.ClearDepth, hg.ColorToABGR32(hg.Color.Black), 1.0, 0)
        hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
        vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, -1)), 10, 0.1, 100, hg.Vec2(resolution.x / resolution.y, 1))
        hg.SetViewTransform(vid, vs.view, vs.proj)
        hg.Touch(vid)

        vid += 1
        hg.SetViewClear(vid, 0, 0, 1.0, 0)
        hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
        # vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(cls.cursor_position.x, cls.cursor_position.y, -1)), cls.view_scale, 0.1, 100, hg.Vec2(Main.resolution.x / Main.resolution.y, 1))
        hg.SetViewTransform(vid, vs.view, vs.proj)
        hg.Touch(vid)
