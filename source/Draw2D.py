# ================================================================
#  2D Drawing
# ================================================================

import harfang as hg
import Polygons as pol
from Backdrops import *
from math import pi, cos, sin, acos, tan, floor
import data_converter as dc
import tools2D as t2D


class Draw2D:

    main_state_id = 0
    flag_debug = False
    flag_render_holes = False

    # Keys:
    key_multiple_vertices_selection = hg.K_LShift

    # UI States:
    UI_STATE_DRAW_IDLE = 0
    UI_STATE_WAIT_DRAW_IDLE = 2
    UI_STATE_SELECT = 3
    UI_STATE_DIRECT_SELECT = 4
    UI_STATE_DRAWING = 5

    UI_STATE_MOVING_VERTEX = 6
    UI_STATE_MOVING_FOLD = 7
    UI_STATE_MOVING_SPLIT = 8
    UI_STATE_MOVING_HOLE = 9
    UI_STATE_MOVING_SHAPE = 10

    UI_STATE_WAIT_ADD_VERTEX_SHAPE = 11
    UI_STATE_ADD_VERTEX_SHAPE = 12
    UI_STATE_WAIT_REMOVE_VERTEX_SHAPE = 13
    UI_STATE_REMOVE_VERTEX_SHAPE = 14

    UI_STATE_TRANSFORM_POLYGON = 15

    # Tools:
    DRAW_SHAPE_TOOL_SELECT = 0
    DRAW_SHAPE_TOOL_DIRECT_SELECT = 1
    DRAW_SHAPE_TOOL_DRAW = 2
    DRAW_SHAPE_TOOL_ADD_VERTEX = 3
    DRAW_SHAPE_TOOL_REMOVE_VERTEX = 4

    lines2D = []

    view2D = None
    texts = None

    main_panel_size = None

    vtx_decl = None
    shapes_program = None
    lines_render_state = None

    move_vector = None
    move_vector_snap = None
    flag_modified_move_vector = False  # True when move_vector is modified (in that case, proceed to undo_record to record old position)

    line_type = 0
    line_types = ["Shape", "Fold", "Split", "Hole"]
    LINE_TYPE_SHAPE = 0
    LINE_TYPE_FOLD = 1
    LINE_TYPE_SPLIT = 2
    LINE_TYPE_HOLE = 3

    shapes = []
    undo_shapes = []
    undo_index = 0

    current_shape = -1
    shape_hover = -1
    current_fold = -1
    fold_hover = -1
    current_split = -1
    split_hover = -1
    current_hole = -1
    hole_hover = -1

    current_vertex = []
    current_join_vertex = None
    point_hover = None
    hover_point_size = 15
    edge_hover_distance = 3
    mouse_pos_prec = None

    ui_state = None
    ui_states = None
    state_mem = -1

    flag_tool_shortcut_mode = False
    ctrl_mem_tool = DRAW_SHAPE_TOOL_SELECT  # DRAW_SHAPE_TOOL_SELECT or DRAW_SHAPE_TOOL_DIRECT_SELECT
    draw_shape_tool_id = DRAW_SHAPE_TOOL_DRAW
    draw_shape_tools = None

    # Colors:
    twinkle_t = 0
    twinkle_speed = 0.25

    face_holey_color = hg.Color(1, 1, 0, 1)
    alert_color = hg.Color(1, 0.2, 0.2, 1)
    advert_color = hg.Color(1, 0.5, 0., 1)
    background_color = hg.Color(0.3, 0.3, 0.3, 1)
    shape_line_color = hg.Color(0.3, 0.6, 0.66, 1)
    selected_shape_line_color = hg.Color(0.4, 0.9, 1, 1)
    hover_shape_line_color = hg.Color(0.8, 1, 1, 1)

    fold_line_color = hg.Color(0.4, 0.4, 0.2, 1)
    fold_hover_color = hg.Color(0.8, 1, 0.8, 1)
    selected_fold_color = hg.Color(1, 1, 0.5, 1)
    selected_shape_fold_line_color = hg.Color(0.7, 0.7, 0.5, 1)
    selected_fold_intersection_color = hg.Color(0.5, 1, 0.2, 1)
    fold_intersection_color = hg.Color(0.6, 0.6, 0.25, 1)
    selected_fold_segments_color = hg.Color(1, 0.8, 0.5, 1)
    fold_segments_color = hg.Color(0.6, 0.5, 0.35, 1)

    split_line_color = hg.Color(0.5, 0.1, 0.1, 1)
    split_hover_color = hg.Color(1, 0.8, 0.8, 1)
    selected_split_color = hg.Color(1, 0.5, 0.5, 1)
    selected_shape_split_line_color = hg.Color(1, 0.25, 0.25, 1)
    split_intersection_color = hg.Color(0.8, 0, 0, 1)

    hole_line_color = hg.Color(0.1, 0.5, 0.1, 1)
    hole_hover_color = hg.Color(0.8, 1, 0.8, 1)
    selected_hole_color = hg.Color(0.6, 1, 0.6, 1)
    selected_shape_hole_line_color = hg.Color(0.1, 0.8, 0.1, 1)

    shape_triangles_color = hg.Color(0.4, 0.4, 0.4, 1)
    point_hover_color = hg.Color(1, 1, 1, 0.75)
    point_hover_color_twinkle = hg.Color(1, 1, 1, 0.75)
    current_vertex_color = hg.Color(1, 1, 1, 1)
    grid_color = hg.Color(0.5, 0.5, 0.6, 1)
    grid_origin_color = hg.Color(1, 1, 1, 1)
    grid_subdivisions_color = hg.Color(0.4, 0.4, 0.5, 1)

    join_area_color = hg.Color(0.8, 0.8, 1, 1)

    edit_boxes_color = hg.Color(1, 0.8, 1, 1.0)

    # Gadgets settings
    points_size = 10  # in pixels
    split_points_size = 5
    split_thickness = 5e-3
    join_size = 10  # in pixels
    join_distance = 0  # Computed on frame

    current_vertex_size = 12

    triangles = None
    flag_show_holey_faces = False
    flag_global_folds_settings = True
    flag_show_triangles = False
    flag_show_main_vertices_idx = False
    flag_show_folded_vertices_idx = False
    flag_show_backdrops = True
    flag_display_mouse_position = True
    flag_snap_to_grid = True
    flag_snap_to_vertex = True

    flag_show_subdivision_grid = True
    flag_new_vertex = False

    shape_thickness = 0.05
    round_segments_count = 1
    round_radius = 0.05
    folds_angle = 1e-4

    round_max_angle = 89

    repeat_points_dict = {}
    flag_display_holey_vertices_idx = True

    # Copy/Paste
    copy_shape = None
    copy_fold = None
    copy_split = None
    copy_hole = None

    # Transform tool

    flag_display_transform_box = True
    transform_box_states = [UI_STATE_WAIT_ADD_VERTEX_SHAPE, UI_STATE_WAIT_REMOVE_VERTEX_SHAPE, UI_STATE_DRAW_IDLE, UI_STATE_SELECT] # UI states in which edit boxes are accessible
    transform_box_display_states = [UI_STATE_WAIT_ADD_VERTEX_SHAPE, UI_STATE_WAIT_REMOVE_VERTEX_SHAPE, UI_STATE_DRAW_IDLE, UI_STATE_SELECT, UI_STATE_TRANSFORM_POLYGON] # UI states in which edit boxes are displayed
    transform_polygon_backup = None

    # Check folds:
    folds_joined_vertices_distance_min = 5e-2

    @classmethod
    def init(cls, resolution, main_state_id):

        cls.main_state_id = main_state_id

        cls.view2D = t2D.View2D()

        cls.vtx_decl = hg.VertexLayout()
        cls.vtx_decl.Begin()
        cls.vtx_decl.Add(hg.A_Position, 3, hg.AT_Float)
        cls.vtx_decl.Add(hg.A_Color0, 3, hg.AT_Float)
        cls.vtx_decl.End()

        cls.shapes_program = hg.LoadProgramFromAssets("shaders/pos_rgb")
        cls.lines_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Less, hg.FC_Disabled)

        # Buttons images:

        cls.draw_shape_tools = [
            {"id": Draw2D.DRAW_SHAPE_TOOL_SELECT, "name": "Select", "selected": hg.LoadTextureFromAssets("icons/selection_selected.png", 0)[0], "idle": hg.LoadTextureFromAssets("icons/selection.png", 0)[0], "state": Draw2D.UI_STATE_SELECT, "enabled": True},
            {"id": Draw2D.DRAW_SHAPE_TOOL_DIRECT_SELECT, "name": "Direct select", "selected": hg.LoadTextureFromAssets("icons/direct_selection_selected.png", 0)[0], "idle": hg.LoadTextureFromAssets("icons/direct_selection.png", 0)[0], "state": Draw2D.UI_STATE_DIRECT_SELECT,
             "enabled": True},
            {"id": Draw2D.DRAW_SHAPE_TOOL_DRAW, "name": "Draw", "selected": hg.LoadTextureFromAssets("icons/draw_polygon_selected.png", 0)[0], "idle": hg.LoadTextureFromAssets("icons/draw_polygon.png", 0)[0], "state": Draw2D.UI_STATE_DRAW_IDLE, "enabled": True},
            {"id": Draw2D.DRAW_SHAPE_TOOL_ADD_VERTEX, "name": "Add vertex", "selected": hg.LoadTextureFromAssets("icons/add_vertex_selected.png", 0)[0], "idle": hg.LoadTextureFromAssets("icons/add_vertex.png", 0)[0], "state": Draw2D.UI_STATE_ADD_VERTEX_SHAPE, "enabled": True},
            {"id": Draw2D.DRAW_SHAPE_TOOL_REMOVE_VERTEX, "name": "Remove vertex", "selected": hg.LoadTextureFromAssets("icons/remove_vertex_selected.png", 0)[0], "idle": hg.LoadTextureFromAssets("icons/remove_vertex.png", 0)[0], "state": Draw2D.UI_STATE_REMOVE_VERTEX_SHAPE,
             "enabled": True}
        ]

        # Texts:
        cls.texts = t2D.TextOverlay(resolution)

        cls.ui_states = [
            {"id": cls.UI_STATE_DRAW_IDLE, "function": Draw2D.ui_draw_idle},
            {"id": cls.UI_STATE_WAIT_DRAW_IDLE, "function": Draw2D.ui_wait_draw_idle},
            {"id": cls.UI_STATE_SELECT, "function": Draw2D.ui_select},
            {"id": cls.UI_STATE_DIRECT_SELECT, "function": Draw2D.ui_direct_select},
            {"id": cls.UI_STATE_DRAWING, "function": Draw2D.ui_drawing},
            {"id": cls.UI_STATE_MOVING_VERTEX, "function": Draw2D.ui_move_vertex},
            {"id": cls.UI_STATE_MOVING_FOLD, "function": Draw2D.ui_move_fold},
            {"id": cls.UI_STATE_MOVING_SPLIT, "function": Draw2D.ui_move_split},
            {"id": cls.UI_STATE_MOVING_HOLE, "function": Draw2D.ui_move_hole},
            {"id": cls.UI_STATE_MOVING_SHAPE, "function": Draw2D.ui_move_shape},

            {"id": cls.UI_STATE_WAIT_ADD_VERTEX_SHAPE, "function": Draw2D.ui_wait_add_vertex_shape},
            {"id": cls.UI_STATE_ADD_VERTEX_SHAPE, "function": Draw2D.ui_add_shape_vertex},
            {"id": cls.UI_STATE_WAIT_REMOVE_VERTEX_SHAPE, "function": Draw2D.ui_wait_remove_vertex_shape},
            {"id": cls.UI_STATE_REMOVE_VERTEX_SHAPE, "function": Draw2D.ui_remove_shape_vertex},
            {"id": cls.UI_STATE_TRANSFORM_POLYGON, "function": Draw2D.ui_transform_polygon}
        ]
        cls.ui_state = cls.ui_states[cls.UI_STATE_DRAW_IDLE]

    # ================= Undo / Redo

    @classmethod
    def undo_record(cls):
        if cls.undo_index > 0: cls.undo_shapes = cls.undo_shapes[0:-cls.undo_index]
        cls.undo_index = 0
        c_shapes = []
        cls.undo_shapes.append({"shapes": c_shapes, "current_shape": cls.current_shape, "current_fold": cls.current_fold, "current_split": cls.current_split, "current_hole": cls.current_hole})
        for shape in cls.shapes:
            new_shape = cls.new_2d_shape()
            new_shape["name"] = shape["name"]
            new_shape["color"] = shape["color"]
            new_shape["thickness"] = shape["thickness"]
            for v in shape["vertices"]:
                new_shape["vertices"].append(hg.Vec2(v))

            #if cls.point_hover is not None and cls.point_hover["shape"] is not None and cls.point_hover["shape"] == shape:
            #    cls.point_hover["shape"] = new_shape
            #    if cls.point_hover["fold"] is None and cls.point_hover["split"] is None and cls.point_hover["hole"] is None: cls.point_hover["vertex"] = new_shape["vertices"][cls.point_hover["idx"]]
            new_shape["closed"] = shape["closed"]

            for fold in shape["folds"]:
                new_fold = cls.new_2d_fold()
                new_fold["fold_angle"] = fold["fold_angle"]
                new_fold["round_radius"] = fold["round_radius"]
                new_fold["round_segments_count"] = fold["round_segments_count"]
                for v in fold["vertices"]:
                    new_fold["vertices"].append(hg.Vec2(v))
                #if cls.point_hover is not None and cls.point_hover["fold"] is not None and cls.point_hover["fold"] == fold:
                #    cls.point_hover["fold"] = new_fold
                #    cls.point_hover["vertex"] = new_fold["vertices"][cls.point_hover["idx"]]
                new_shape["folds"].append(new_fold)
            for split in shape["splits"]:
                new_split = cls.new_2d_split()
                for v in split["vertices"]:
                    new_split["vertices"].append(hg.Vec2(v))
                #if cls.point_hover is not None and cls.point_hover["split"] is not None and cls.point_hover["split"] == split:
                #    cls.point_hover["split"] = new_split
                #    cls.point_hover["vertex"] = new_split["vertices"][cls.point_hover["idx"]]
                new_shape["splits"].append(new_split)
            for hole in shape["holes"]:
                new_hole = cls.new_2d_hole()
                for v in hole["vertices"]:
                    new_hole["vertices"].append(hg.Vec2(v))
                #if cls.point_hover is not None and cls.point_hover["hole"] is not None and cls.point_hover["hole"] == hole:
                #    cls.point_hover["hole"] = new_hole
                #    cls.point_hover["vertex"] = new_hole["vertices"][cls.point_hover["idx"]]
                new_hole["closed"] = hole["closed"]
                new_hole["edit_box"].set_state(hole["edit_box"].get_state())
                new_shape["holes"].append(new_hole)
            new_shape["edit_box"].set_state(shape["edit_box"].get_state())
            cls.generates_shape(new_shape, cls.flag_render_holes)
            c_shapes.append(new_shape)
        #cls.shapes = c_shapes

    @classmethod
    def undo(cls):

        if len(cls.undo_shapes) > 0 and cls.undo_index < len(cls.undo_shapes):
            cls.undo_index += 1
            u_shapes = cls.undo_shapes[-cls.undo_index]["shapes"]
            cs = cls.undo_shapes[-cls.undo_index]["current_shape"]
            cf = cls.undo_shapes[-cls.undo_index]["current_fold"]
            csp = cls.undo_shapes[-cls.undo_index]["current_split"]
            csh = cls.undo_shapes[-cls.undo_index]["current_hole"]

            cls.undo_shapes[-cls.undo_index]["shapes"] = cls.shapes
            cls.undo_shapes[-cls.undo_index]["current_shape"] = cls.current_shape
            cls.undo_shapes[-cls.undo_index]["current_fold"] = cls.current_fold
            cls.undo_shapes[-cls.undo_index]["current_split"] = cls.current_split
            cls.undo_shapes[-cls.undo_index]["current_hole"] = cls.current_hole

            cls.shapes = u_shapes

            cls.current_shape = cs if cs < len(cls.shapes) else -1
            if cls.current_shape >= 0:
                shape = cls.shapes[cls.current_shape]
                cls.current_hole = csh if csh < len(shape["holes"]) else -1
                cls.current_split = csp if csp < len(shape["splits"]) else -1
                cls.current_fold = cf if cf < len(shape["folds"]) else -1
            else:
                cls.current_hole = -1
                cls.current_split = -1
                cls.current_fold = -1

            cls.current_vertex = []

    @classmethod
    def redo(cls):
        if len(cls.undo_shapes) > 0 and 0 < cls.undo_index <= len(cls.undo_shapes):
            u_shapes = cls.undo_shapes[-cls.undo_index]["shapes"]
            cs = cls.undo_shapes[-cls.undo_index]["current_shape"]
            cf = cls.undo_shapes[-cls.undo_index]["current_fold"]
            csp = cls.undo_shapes[-cls.undo_index]["current_split"]
            csh = cls.undo_shapes[-cls.undo_index]["current_hole"]

            cls.undo_shapes[-cls.undo_index]["shapes"] = cls.shapes
            cls.undo_shapes[-cls.undo_index]["current_shape"] = cls.current_shape
            cls.undo_shapes[-cls.undo_index]["current_fold"] = cls.current_fold
            cls.undo_shapes[-cls.undo_index]["current_split"] = cls.current_split
            cls.undo_shapes[-cls.undo_index]["current_hole"] = cls.current_hole

            cls.current_hole = csh
            cls.current_split = csp
            cls.current_fold = cf
            cls.current_shape = cs
            cls.shapes = u_shapes

            cls.undo_index -= 1

            cls.current_vertex = []
            """
            if cls.current_shape>-1:
                if cls.current_shape>=len(cls.shapes): cls.current_shape=len(cls.shapes)-1
                if cls.current_shape>-1 and cls.current_fold>-1:
                    shape = cls.shapes[cls.current_shape]
                    if cls.current_fold>=len(shape["folds"]): cls.current_fold=len(shape["folds"])-1
            """

    # ================== Objects creation

    @classmethod
    def new_2d_object(cls, p: hg.Vec2 = None):
        if p is None:
            vlist = []
        else:
            vlist = [p, p]
        return {"vertices": vlist, "closed": False}

    @classmethod
    def new_2d_polygon(cls, p:hg.Vec2 = None):
        new_pol = cls.new_2d_object(p)
        new_pol["edit_box"] = t2D.Edit2DBox(t2D.Edit2DBox.FLAG_SCALEXY | t2D.Edit2DBox.FLAG_ROTATE, hg.Vec2(0, 0), hg.Vec2(0,0), hg.Vec2(1, 1))
        new_pol["edit_box"].set_colors(cls.edit_boxes_color, cls.edit_boxes_color)
        return new_pol

    @classmethod
    def new_2d_shape(cls, p: hg.Vec2 = None):
        newo = cls.new_2d_polygon(p)
        newo["name"] = "Shape"
        newo["folds"] = []  # Lignes de pliage
        newo["splits"] = []  # Lignes de coupe
        newo["holes"] = []  # trous
        newo["color"] = hg.Color(1, 1, 1, 1)
        newo["thickness"] = cls.shape_thickness
        newo["split_thickness"] = cls.split_thickness
        return newo

    @classmethod
    def new_2d_fold(cls, p: hg.Vec2 = None):
        newo = cls.new_2d_object(p)
        newo["intersections"] = []
        newo["fold_angle"] = 0 / 180 * pi
        newo["valide"] = False  # True lorsque la ligne de rainage génère un pliage cohérent.
        newo["round_radius"] = cls.round_radius
        newo["round_segments_count"] = cls.round_segments_count
        newo["segments_intersections"] = []
        return newo

    @classmethod
    def new_2d_split(cls, p: hg.Vec2 = None):
        newo = cls.new_2d_object(p)
        newo["intersections"] = []
        newo["inside_idx"] = 1  # Vertex idx inside shape
        newo["valide"] = False  # True lorsque la ligne de split génère une coupe cohérente.
        return newo

    @classmethod
    def new_2d_hole(cls, p: hg.Vec2 = None):
        newo = cls.new_2d_polygon(p)
        newo["valide"] = False  # True lorsque le trou est une forme fermée à l'intérieur de la shape
        return newo

    @classmethod
    # Called when project loading
    def add_shape(cls, shape):
        cls.shapes.append(shape)
        cls.current_shape = len(cls.shapes) - 1
        if shape["closed"]:
            pol.make_polygon_cw(shape["vertices"])
            for hole in shape["holes"]:
                if hole["closed"]:
                    pol.make_polygon_cw(hole["vertices"])
            cls.generates_shape(shape, cls.flag_render_holes)
            #cls.update_polygon_edit_box(shape)
        cls.current_vertex = []
        cls.point_hover = None

    @classmethod
    def remove_all(cls):
        cls.shapes = []
        cls.clear_selection()
        cls.current_shape = -1
        cls.current_fold = -1
        cls.current_split = -1
        cls.current_hole = -1
        cls.current_vertex = []
        cls.undo_shapes = []
        cls.undo_index = 0
        cls.view2D.reset()

    # ================== Scripting project

    @classmethod
    def get_shape_state(cls, shape):
        state = {"vertices": [],
                 "folds": [],
                 "splits": [],
                 "holes": [],
                 "closed": shape["closed"],
                 "thickness": shape["thickness"],
                 "split_thickness": shape["split_thickness"],
                 "color": dc.color_to_list(shape["color"]),
                 "edit_box": shape["edit_box"].get_state()}
        for v in shape["vertices"]:
            state["vertices"].append(dc.vec2_to_list(v))
        for fold in shape["folds"]:
            state["folds"].append(cls.get_fold_state(fold))
        for split in shape["splits"]:
            state["splits"].append(cls.get_split_state(split))
        for hole in shape["holes"]:
            state["holes"].append(cls.get_hole_state(hole))
        return state

    @classmethod
    def set_shape_state(cls, shape, state):
        shape["closed"] = state["closed"]
        shape["thickness"] = state["thickness"]
        if "split_thickness" in state:
            shape["split_thickness"] = state["split_thickness"]
        shape["color"] = dc.list_to_color(state["color"])
        for v in state["vertices"]:
            shape["vertices"].append(dc.list_to_vec2(v))
        for fold_script in state["folds"]:
            fold = Draw2D.new_2d_fold()
            cls.set_fold_state(fold, fold_script)
            shape["folds"].append(fold)
        if "splits" in state:
            for split_script in state["splits"]:
                split = Draw2D.new_2d_split()
                cls.set_split_state(split, split_script)
                shape["splits"].append(split)
        if "holes" in state:
            for hole_script in state["holes"]:
                hole = Draw2D.new_2d_hole()
                cls.set_hole_state(hole, hole_script)
                shape["holes"].append(hole)
        if "edit_box" in state:
            shape["edit_box"].set_state(state["edit_box"])
        else:
            cls.reset_polygon_edit_box(shape)

    @classmethod
    def get_fold_state(cls, fold):
        state = {"vertices": [dc.vec2_to_list(fold["vertices"][0]), dc.vec2_to_list(fold["vertices"][1])],
                 "fold_angle": fold["fold_angle"],
                 "round_radius": fold["round_radius"],
                 "round_segments_count": fold["round_segments_count"]}
        return state

    @classmethod
    def set_fold_state(cls, fold, state):
        fold["vertices"] = [dc.list_to_vec2(state["vertices"][0]), dc.list_to_vec2(state["vertices"][1])]
        fold["fold_angle"] = state["fold_angle"]
        fold["round_radius"] = state["round_radius"]
        fold["round_segments_count"] = state["round_segments_count"]

    @classmethod
    def get_split_state(cls, split):
        state = {"vertices": [dc.vec2_to_list(split["vertices"][0]), dc.vec2_to_list(split["vertices"][1])]}
        return state

    @classmethod
    def set_split_state(cls,split, state):
        split["vertices"] = [dc.list_to_vec2(state["vertices"][0]), dc.list_to_vec2(state["vertices"][1])]

    @classmethod
    def get_hole_state(cls, hole):
        state = {"closed": hole["closed"], "vertices": [], "edit_box": hole["edit_box"].get_state()}
        for v in hole["vertices"]:
            state["vertices"].append(dc.vec2_to_list(v))
        return state

    @classmethod
    def set_hole_state(cls, hole, state):
        for v in state["vertices"]:
            hole["vertices"].append(dc.list_to_vec2(v))
        hole["closed"] = state["closed"]
        if "edit_box" in state:
            hole["edit_box"].set_state(state["edit_box"])
        else:
            cls.reset_polygon_edit_box(hole)

    # ============== Get/Set Informations

    @classmethod
    def get_tool_from_id(cls, tool_id):
        for tool in cls.draw_shape_tools:
            if tool["id"] == tool_id:
                return tool
        return None

    @classmethod
    def set_current_shape(cls, idx):
        if idx < 0:
            cls.current_shape = -1
        elif len(cls.shapes) > idx:
            cls.current_shape = idx
            shape = cls.get_current_shape()
            cls.generates_shape(shape, cls.flag_render_holes)
        else:
            cls.current_shape = -1

    @classmethod
    def get_current_shape(cls):
        if -1 < cls.current_shape < len(cls.shapes):
            return cls.shapes[cls.current_shape]
        else:
            return None

    @classmethod
    def get_current_fold(cls):
        shape = cls.get_current_shape()
        if shape is not None:
            if -1 < cls.current_fold < len(shape["folds"]):
                return shape["folds"][cls.current_fold]
        return None

    @classmethod
    def get_current_split(cls):
        shape = cls.get_current_shape()
        if shape is not None:
            if -1 < cls.current_split < len(shape["splits"]):
                return shape["splits"][cls.current_split]
        return None

    @classmethod
    def get_current_hole(cls):
        shape = cls.get_current_shape()
        if shape is not None:
            if -1 < cls.current_hole < len(shape["holes"]):
                return shape["holes"][cls.current_hole]
        return None

    @classmethod
    def get_current_polygon(cls):
        if cls.current_fold > -1 or cls.current_split > -1:
            return None
        elif cls.current_hole > -1:
            return cls.get_current_hole()
        elif cls.current_shape > -1:
            return cls.get_current_shape()
        return None

    # ========== Display informations ===================

    @classmethod
    def display_mouse_message(cls, mouse, resolution, message):
        ms = hg.Vec2(mouse.X(), mouse.Y())
        cls.texts.push({"text": message, "pos": hg.Vec2(ms.x + 10, ms.y - 30) / resolution, "font": cls.texts.font_small})

    @classmethod
    def display_shape_infos(cls, shape, resolution):
        c = hg.Color(0.9, 0.8, 0.6, 1)
        x = cls.main_panel_size.x + 10
        y = 45
        cls.texts.push({"text": shape["name"], "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        y += 24
        cls.texts.push({"text": "Vertices: " + str(len(shape["vertices"])), "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        y += 24
        cls.texts.push({"text": "Folds: " + str(len(shape["folds"])), "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        y += 24
        cls.texts.push({"text": "Splits: " + str(len(shape["splits"])), "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        y += 24
        cls.texts.push({"text": "Holes: " + str(len(shape["holes"])), "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        y += 24
        if not shape["closed"]:
            cls.texts.push({"text": "Unclosed", "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        else:
            cls.texts.push({"text": "Area: %.2f" % cls.get_shape_area(shape), "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": c, "font": cls.texts.font_small})
        if "geometry_error" in shape and len(shape["geometry_error"]) > 0:
            error_labels = {}
            for error in shape["geometry_error"]:
                if not error[0] in error_labels:
                    error_labels[error[0]] = 1
                else:
                    error_labels[error[0]] += 1

            for error_label, num in error_labels.items():
                y += 24
                cls.texts.push({"text": error_label + ": %d" % num, "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": cls.alert_color, "font": cls.texts.font_small})

        if "folds_check_log" in shape:
            if "vertices_distances" in shape["folds_check_log"] and len(shape["folds_check_log"]["vertices_distances"]) > 0:
                y += 24
                error_label = "Check if folds vertices could be joined: %d" % len(shape["folds_check_log"]["vertices_distances"])
                cls.texts.push({"text": error_label, "pos": (hg.Vec2(x, resolution.y - y)) / resolution, "color": cls.advert_color, "font": cls.texts.font_small})

    @classmethod
    def get_shape_area(cls, shape):
        area = 0
        if "faces" in shape:
            for face in shape["faces"]:
                if "triangles" in face and face["triangles"] is not None:
                    for triangle in face["triangles"]:
                        area += pol.compute_triangle_area(shape["folded_vertices"], triangle)
        return area

    # ============= Display gfx ========================

    @classmethod
    def display_folds(cls, vid, resolution):
        for shape_idx in range(len(cls.shapes)):
            shape = cls.shapes[shape_idx]
            folds = shape["folds"]
            if len(folds) > 0:
                for fold_idx in range(len(folds)):
                    fold = folds[fold_idx]
                    if shape_idx == cls.current_shape:
                        if fold_idx == cls.current_fold:
                            color = cls.selected_fold_color
                        else:
                            color = cls.selected_shape_fold_line_color
                    else:
                        color = cls.fold_line_color
                    cls.draw_fold(vid, fold, color, resolution, fold_idx)

    @classmethod
    def draw_fold(cls, vid, fold, color, resolution, idx=-1):
        if "splitted_vertices" in fold:
            v_key = "splitted_vertices"
        else:
            v_key = "vertices"

        cp = dc.pack_color_RGba(color)

        nl = 2
        vtx = hg.Vertices(cls.vtx_decl, nl)
        vtx.Clear()
        v1 = fold[v_key][0]
        v2 = fold[v_key][1]
        vtx.Begin(0).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
        vtx.Begin(1).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()

        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

        middle_p = hg.Vec2(0, 0)
        for p in fold[v_key]:
            middle_p = middle_p + p
            cls.draw_point(vid, p, resolution, color, cls.points_size)
        # Display fold indice
        if cls.flag_show_triangles and idx >= 0:
            middle_p = middle_p / len(fold[v_key])
            cls.texts.push({"text": str(idx), "pos": (cls.view2D.get_point_screen(middle_p, resolution) + hg.Vec2(5, 5)) / resolution, "color": color, "font": cls.texts.font_small})

    @classmethod
    def display_splits(cls, vid, resolution):
        for shape_idx in range(len(cls.shapes)):
            shape = cls.shapes[shape_idx]
            splits = shape["splits"]
            if len(splits) > 0:
                for split_idx in range(len(splits)):
                    split = splits[split_idx]
                    if shape_idx == cls.current_shape:
                        if split_idx == cls.current_split:
                            color = cls.selected_split_color
                        else:
                            color = cls.selected_shape_split_line_color
                    else:
                        color = cls.split_line_color
                    cls.draw_split(vid, split, color, resolution, split_idx)

    @classmethod
    def draw_split(cls, vid, split, color, resolution, idx=-1):
        cp = dc.pack_color_RGba(color)
        vtx = hg.Vertices(cls.vtx_decl, 2)
        vtx.Clear()
        v1 = split["vertices"][0]
        v2 = split["vertices"][1]
        vtx.Begin(0).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
        vtx.Begin(1).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

        middle_p = hg.Vec2(0, 0)
        for p in split["vertices"]:
            middle_p = middle_p + p
            cls.draw_point_circle(vid, p, cls.split_points_size, resolution, color)
        # Display split indice
        if cls.flag_show_triangles and idx >= 0:
            middle_p = middle_p / len(split["vertices"])
            cls.texts.push({"text": str(idx), "pos": (cls.view2D.get_point_screen(middle_p, resolution) + hg.Vec2(5, 5)) / resolution, "color": color, "font": cls.texts.font_small})

    @classmethod
    def display_holes(cls, vid, resolution):
        for shape_idx in range(len(cls.shapes)):
            shape = cls.shapes[shape_idx]
            holes = shape["holes"]
            if len(holes) > 0:
                for hole_idx in range(len(holes)):
                    hole = holes[hole_idx]
                    if shape_idx == cls.current_shape:
                        if hole_idx == cls.current_hole:
                            color = cls.selected_hole_color
                        else:
                            color = cls.selected_shape_hole_line_color
                    else:
                        color = cls.hole_line_color
                    cls.draw_hole(vid, hole, color, resolution, hole_idx)

    @classmethod
    def draw_hole(cls, vid, hole, color, resolution, idx=-1):
        if "edit_error" in hole and hole["edit_error"] is not None:
            color_e = cls.alert_color
            cls.draw_point_circle(vid, hole["edit_error"], 5, resolution, cls.alert_color)
        else:
            color_e = color
        cls.draw_polygon(vid, hole["vertices"], color, color_e, hole["closed"])

        middle_p = hg.Vec2(0, 0)

        # draw points:
        v = hole["vertices"]
        p_color = color
        if cls.flag_show_main_vertices_idx:
            for p_idx in range(len(v)):
                p = v[p_idx]
                middle_p += p
                if p_idx == len(v) - 1:
                    if "edit_error" in hole and hole["edit_error"] is not None:
                        p_color = cls.alert_color
                cls.draw_point(vid, p, resolution, p_color, cls.points_size)
                cls.texts.push({"text": str(p_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10)) / resolution, "color": p_color, "font": cls.texts.font_small})

            """
            elif cls.flag_show_folded_vertices_idx and len(shape["folded_vertices"]) > 0:
                for p_idx in range(len(shape["folded_vertices"])):
                    p = shape["folded_vertices"][p_idx]
                    cls.draw_point_circle(vid, p, cls.points_size / 2, resolution, color)
                    cls.texts.push({"text": str(p_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10)) / resolution, "color": color, "font": cls.texts.font_small})
            """

        else:
            for p_idx in range(len(v)):
                p = v[p_idx]
                middle_p += p
                if p_idx == len(v) - 1:
                    if "edit_error" in hole and hole["edit_error"] is not None:
                        p_color = cls.alert_color
                cls.draw_point(vid, p, resolution, p_color, cls.points_size)

        # Display hole indice
        if cls.flag_show_triangles and idx >= 0:
            middle_p = middle_p / len(hole["vertices"])
            cls.texts.push({"text": str(idx), "pos": (cls.view2D.get_point_screen(middle_p, resolution) + hg.Vec2(5, 5)) / resolution, "color": color, "font": cls.texts.font_small})

        if "geometry_error" in hole and len(hole["geometry_error"]) > 0:
            for error in hole["geometry_error"]:
                cls.draw_crossed_point(vid, error[1], resolution, cls.alert_color, cls.points_size * 2)

    @classmethod
    def display_point_hover(cls, vid, resolution):
        if cls.point_hover["circle"]:
            cls.draw_point_circle(vid, cls.point_hover["vertex"], cls.hover_point_size / 2, resolution, cls.point_hover_color)
        else:
            cls.draw_point(vid, cls.point_hover["vertex"], resolution, cls.point_hover_color, cls.hover_point_size)

    @classmethod
    def display_current_vertex(cls, vid, resolution):
        for vtx in cls.current_vertex:
            if vtx["circle"]:
                cls.draw_point_circle(vid, vtx["vertex"], cls.current_vertex_size / 2, resolution, cls.current_vertex_color)
            else:
                cls.draw_point(vid, vtx["vertex"], resolution, cls.current_vertex_color, cls.current_vertex_size)

    @classmethod
    def display_current_join_vertex(cls, vid):
        cls.draw_circle(vid, cls.current_join_vertex, cls.join_distance, cls.join_area_color)

    @classmethod
    def display_fold_hover(cls, vid, resolution):
        cls.draw_fold(vid, cls.shapes[cls.current_shape]["folds"][cls.fold_hover], cls.fold_hover_color, resolution)

    @classmethod
    def display_split_hover(cls, vid, resolution):
        cls.draw_split(vid, cls.shapes[cls.current_shape]["splits"][cls.split_hover], cls.split_hover_color, resolution)

    @classmethod
    def display_hole_hover(cls, vid, resolution):
        cls.draw_hole(vid, cls.shapes[cls.current_shape]["holes"][cls.hole_hover], cls.hole_hover_color, resolution)

    @classmethod
    def display_shapes(cls, vid, resolution):
        for shape_idx in range(len(cls.shapes)):
            shape = cls.shapes[shape_idx]
            if shape_idx == cls.shape_hover:
                color = cls.hover_shape_line_color
            elif shape_idx == cls.current_shape:
                color = cls.selected_shape_line_color
            else:
                color = cls.shape_line_color

            cls.draw_shape(vid, shape, resolution, color)

            # display folds:
            if shape_idx == cls.current_shape:
                folds_color = cls.selected_fold_intersection_color
                segments_color = cls.selected_fold_segments_color
            else:
                folds_color = cls.fold_intersection_color
                segments_color = cls.fold_segments_color

            if shape["closed"]:
                cls.display_cut_edges(vid, shape, resolution, folds_color, segments_color)
                if cls.flag_show_triangles:
                    cls.display_triangulate_shape(vid, shape, cls.shape_triangles_color)

    @classmethod
    def draw_shape(cls, vid, shape, resolution, color):

        if "splitted_vertices" in shape and len(shape["splitted_vertices"]) > 0:
            v = shape["splitted_vertices"]
        else:
            v = shape["vertices"]
        if "edit_error" in shape and shape["edit_error"] is not None:
            color_e = cls.alert_color
            cls.draw_point_circle(vid, shape["edit_error"], 5, resolution, cls.alert_color)
        else:
            color_e = color

        if cls.draw_polygon(vid, v, color, color_e, shape["closed"]):
            # draw points
            p_color = color
            if cls.flag_show_main_vertices_idx:
                for p_idx in range(len(v)):
                    p = v[p_idx]
                    if p_idx == len(v) - 1:
                        if "edit_error" in shape and shape["edit_error"] is not None:
                            p_color = cls.alert_color
                    cls.draw_point(vid, p, resolution, p_color, cls.points_size)
                    cls.texts.push({"text": str(p_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10)) / resolution, "color": p_color, "font": cls.texts.font_small})

            elif cls.flag_show_folded_vertices_idx and len(shape["folded_vertices"]) > 0:
                for p_idx in range(len(shape["folded_vertices"])):
                    p = shape["folded_vertices"][p_idx]
                    cls.draw_point_circle(vid, p, cls.points_size / 2, resolution, color)
                    cls.texts.push({"text": str(p_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10)) / resolution, "color": color, "font": cls.texts.font_small})
            else:
                for p_idx in range(len(v)):
                    p = v[p_idx]
                    if p_idx == len(v) - 1:
                        if "edit_error" in shape and shape["edit_error"] is not None:
                            p_color = cls.alert_color
                    cls.draw_point(vid, p, resolution, p_color, cls.points_size)

            if "geometry_error" in shape and len(shape["geometry_error"]) > 0:
                for error in shape["geometry_error"]:
                    cls.draw_crossed_point(vid, error[1], resolution, cls.alert_color, cls.points_size * 2)

            # draw folds intersections points:
            if len(shape["folds"]) > 0:
                for fold_idx in range(len(shape["folds"])):
                    fold = shape["folds"][fold_idx]
                    for inter_idx in range(min(len(fold["intersections"]), 2)):
                        p = fold["intersections"][inter_idx]["vertex"]
                        if cls.flag_show_triangles: cls.texts.push({"text": str(inter_idx), "pos": (cls.view2D.get_point_screen(p, resolution)) / resolution, "color": cls.fold_intersection_color, "font": cls.texts.font_small})
                        cls.draw_point(vid, p, resolution, cls.fold_intersection_color, cls.points_size)

            # draw splits intersections points:
            if len(shape["splits"]) > 0:
                for split_idx in range(len(shape["splits"])):
                    split = shape["splits"][split_idx]
                    for inter_idx in range(len(split["intersections"])):
                        p = split["intersections"][inter_idx]["vertex"]
                        if cls.flag_show_triangles: cls.texts.push({"text": str(inter_idx), "pos": (cls.view2D.get_point_screen(p, resolution)) / resolution, "color": cls.split_intersection_color, "font": cls.texts.font_small})
                        cls.draw_point_circle(vid, p, cls.split_points_size, resolution, cls.split_intersection_color)

            # Draw folds check alerts:
            if "folds_check_log" in shape:
                for vd in shape["folds_check_log"]["vertices_distances"]:
                    f0 = shape["folds"][vd["folds"][0]]
                    f1 = shape["folds"][vd["folds"][1]]
                    v0 = f0["vertices"][vd["fold0_vidx"]]
                    v1 = f1["vertices"][vd["fold1_vidx"]]
                    cls.draw_point_circle(vid, (v0 + v1) / 2, max(15, cls.folds_joined_vertices_distance_min / 2 * resolution.y / cls.view2D.view_scale), resolution, cls.advert_color)

    @classmethod
    def display_cut_edges(cls, vid, shape, resolution, folds_color, segments_color):

        if "folded_vertices" in shape:

            fcp = dc.pack_color_RGba(folds_color)
            scp = dc.pack_color_RGba(segments_color)
            n = 0
            for fold in shape["folds"]:
                if len(fold["intersections"]) >= 2:
                    if fold["segments_intersections"] is None:
                        n += 2
                    else:
                        n += 2 * len(fold["segments_intersections"])

            vtx = hg.Vertices(cls.vtx_decl, n)
            vtx.Clear()

            i = 0
            flag_draw = False

            v = shape["folded_vertices"]

            for fold in shape["folds"]:
                if len(fold["intersections"]) >= 2:
                    if fold["segments_intersections"] is None:
                        va = v[fold["intersections"][0]["idx"]]
                        vb = v[fold["intersections"][1]["idx"]]
                        vtx.Begin(i).SetPos(hg.Vec3(va.x, va.y, 0)).SetColor0(fcp).End()
                        vtx.Begin(i + 1).SetPos(hg.Vec3(vb.x, vb.y, 0)).SetColor0(fcp).End()
                        i += 2
                    else:
                        ns = len(fold["segments_intersections"])
                        for si in range(ns):
                            segment = fold["segments_intersections"][si]
                            if si == ns // 2:
                                color = folds_color
                                cp = fcp
                            else:
                                color = segments_color
                                cp = scp
                            sa = v[segment[0]["idx"]]
                            sb = v[segment[1]["idx"]]
                            if cls.flag_show_triangles:
                                cls.texts.push({"text": str(segment[0]["edge_idx"]), "pos": (cls.view2D.get_point_screen(sa, resolution)) / resolution, "color": color, "font": cls.texts.font_small})
                                cls.texts.push({"text": str(segment[1]["edge_idx"]), "pos": (cls.view2D.get_point_screen(sb, resolution)) / resolution, "color": color, "font": cls.texts.font_small})
                            vtx.Begin(i).SetPos(hg.Vec3(sa.x, sa.y, 0)).SetColor0(cp).End()
                            vtx.Begin(i + 1).SetPos(hg.Vec3(sb.x, sb.y, 0)).SetColor0(cp).End()
                            i += 2

                    flag_draw = True
            if flag_draw: hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    @classmethod
    def draw_polygon(cls, vid, v, color_s, color_e, closed):
        color_sp = dc.pack_color_RGba(color_s)
        color_ep = dc.pack_color_RGba(color_e)
        if closed:
            cn = 1
        else:
            cn = 0
        line_count = len(v) - 1 + cn
        if line_count > 0:
            vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
            vtx.Clear()

            va = v[0]
            n = len(v)
            color_1 = color_sp
            for vi in range(1, line_count + 1):
                if not closed and vi == line_count:
                    color_1 = color_ep
                vb = v[vi % n]
                vtx.Begin((vi - 1) * 2).SetPos(hg.Vec3(va.x, va.y, 0)).SetColor0(color_sp).End()
                vtx.Begin((vi - 1) * 2 + 1).SetPos(hg.Vec3(vb.x, vb.y, 0)).SetColor0(color_1).End()
                va = vb
            hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)
            return True
        return False

    @classmethod
    def display_triangulate_shape(cls, vid, shape, color):
        if "faces" in shape and len(shape["faces"]) > 0:
            for face_idx in range(len(shape["faces"])):
                face = shape["faces"][face_idx]
                if cls.flag_show_holey_faces:
                    cls.display_triangulate_holey_face(vid, face, shape["holey_vertices"], color)
                else:
                    cls.display_triangulate_face(vid, face, shape["folded_vertices"], color)

    @classmethod
    def display_triangulate_holey_face(cls, vid, face, vertices, color):
        cp = dc.pack_color_RGba(color)
        if "holey_triangles" in face and face["holey_triangles"] is not None:
            line_count = 0
            for triangles in face["holey_triangles"]:
                line_count += len(triangles) * 3
            if line_count > 0:
                # draw shape:
                vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
                vtx.Clear()
                vi = 0
                for triangles in face["holey_triangles"]:
                    for t in triangles:
                        v0 = vertices[t[0]]
                        v1 = vertices[t[1]]
                        v2 = vertices[t[2]]
                        vtx.Begin(vi).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 1).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 2).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 3).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 4).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 5).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
                        vi += 6

                hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    @classmethod
    def display_triangulate_face(cls, vid, face, vertices, color):
        cp = dc.pack_color_RGba(color)
        if "triangles" in face and face["triangles"] is not None:
            line_count = len(face["triangles"]) * 3
            if line_count > 0:
                # draw shape:
                vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
                vtx.Clear()
                vi = 0
                for t in face["triangles"]:
                    v0 = vertices[t[0]]
                    v1 = vertices[t[1]]
                    v2 = vertices[t[2]]
                    vtx.Begin(vi).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
                    vtx.Begin(vi + 1).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
                    vtx.Begin(vi + 2).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
                    vtx.Begin(vi + 3).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
                    vtx.Begin(vi + 4).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
                    vtx.Begin(vi + 5).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
                    vi += 6

                hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    @classmethod
    def display_holey_shape(cls, vid, shape, color, resolution):
        if "holey_vertices" in shape:
            cls.repeat_points_dict = {}
            if shape is not None:
                if "faces" in shape and len(shape["faces"]) > 0:
                    for face_idx in range(len(shape["faces"])):
                        face = shape["faces"][face_idx]
                        cls.display_holey_face(vid, shape, face, color, resolution)
            if cls.flag_display_holey_vertices_idx and shape["holey_vertices"] is not None:
                cp = dc.pack_color_RGba(color)
                for v_idx in range(len(shape["holey_vertices"])):
                    p = shape["holey_vertices"][v_idx]
                    cls.draw_point(vid, p, resolution, cp, cls.points_size)
                    cls.texts.push({"text": str(v_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10)) / resolution, "color": cp, "font": cls.texts.font_small})

    @classmethod
    def get_point_offset(cls, p_idx):
        if not p_idx in cls.repeat_points_dict:
            cls.repeat_points_dict[p_idx] = 0
        else:
            cls.repeat_points_dict[p_idx] += 1
        return cls.repeat_points_dict[p_idx]

    @classmethod
    def display_holey_face(cls, vid, shape, face, color, resolution):
        cp = dc.pack_color_RGba(color)
        if face["holey_idx"] is not None:
            v = shape["holey_vertices"]
            line_count = 0
            for part in face["holey_idx"]:
                line_count += len(part)

            if line_count > 0:
                # draw polygon:
                vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
                vtx.Clear()
                vi = 0
                for part in face["holey_idx"]:
                    n = len(part)
                    for idx in range(n):
                        v0 = v[part[idx]]
                        v1 = v[part[(idx + 1) % n]]
                        vtx.Begin(vi).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
                        vtx.Begin(vi + 1).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
                        vi += 2
                hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

            if not cls.flag_display_holey_vertices_idx:

                for part in face["holey_idx"]:
                    n = len(part)
                    for p_idx in range(n):
                        idx = part[p_idx]
                        p = v[idx]
                        of7 = cls.get_point_offset(idx)
                        cls.draw_point(vid, p, resolution, cp, cls.points_size)
                        cls.texts.push({"text": str(p_idx), "pos": (cls.view2D.get_point_screen(p, resolution) + hg.Vec2(10, 10 - of7 * 12)) / resolution, "color": cp, "font": cls.texts.font_small})

    @classmethod
    def display_transform_box(cls, vid, resolution):
        polygon = cls.get_current_polygon()
        if polygon is not None:
            eb = polygon["edit_box"]
            eb.display(vid, cls.view2D, resolution)

    # ====================== UI drawings =========================

    @classmethod
    def line2D(cls, resolution: hg.Vec2, sx, sy, ex, ey, c: hg.Color):

        view_center = hg.Vec2(0.5, 0.5)

        v1 = (hg.Vec2(sx, sy) - (view_center * resolution)) * (cls.view2D.view_scale / resolution.y) + cls.view2D.cursor_position
        v2 = (hg.Vec2(ex, ey) - (view_center * resolution)) * (cls.view2D.view_scale / resolution.y) + cls.view2D.cursor_position
        cls.lines2D.append({"vs": v1, "ve": v2, "c": c})

    @classmethod
    def flush_lines2D(cls, vid):
        vtx = hg.Vertices(cls.vtx_decl, len(cls.lines2D) * 2)
        vtx.Clear()
        i = 0
        for line in cls.lines2D:
            va = line["vs"]
            vb = line["ve"]
            c = dc.pack_color_RGba(line["c"])
            vtx.Begin(i).SetPos(hg.Vec3(va.x, va.y, 0)).SetColor0(c).End()
            vtx.Begin(i + 1).SetPos(hg.Vec3(vb.x, vb.y, 0)).SetColor0(c).End()
            i += 2
        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)
        cls.lines2D = []

    @classmethod
    def draw_grid(cls, resolution):
        if cls.view2D.grid_size > 1e-5:
            cls.display_ortho_grid(resolution, cls.view2D.grid_size, cls.grid_color, True)
            if cls.flag_show_subdivision_grid and cls.view2D.grid_subdivisions > 1:
                cls.display_ortho_grid(resolution, cls.view2D.grid_size / cls.view2D.grid_subdivisions, cls.grid_subdivisions_color, False)

    @classmethod
    def display_ortho_grid(cls, resolution: hg.Vec2, grid_size, grid_color: hg.Color, display_origin=False):

        pixel_size = cls.view2D.view_scale / resolution.y
        view_zoom = 1 / pixel_size

        view_center = hg.Vec2(0.5, 0.5)

        if display_origin:
            # c = cls.grid_origin_color * cls.view2D.grid_intensity + cls.background_color * (1 - cls.view2D.grid_intensity)
            c = hg.Color(cls.grid_origin_color)
            c.a = cls.view2D.grid_intensity
            sx = view_center.x * resolution.x - cls.view2D.cursor_position.x / pixel_size
            sy = view_center.y * resolution.y - cls.view2D.cursor_position.y / pixel_size
            if 0 < sx < resolution.x: cls.line2D(resolution, sx, 0, sx, resolution.y, c)
            if 0 < sy < resolution.y: cls.line2D(resolution, 0, sy, resolution.x, sy, c)

        rmin = 5
        rmax = 10
        s = view_zoom * grid_size
        if s > rmin:
            # grid_color = grid_color * cls.view2D.grid_intensity + cls.background_color * (1 - cls.view2D.grid_intensity)
            grid_color = hg.Color(grid_color)
            grid_color.a = cls.view2D.grid_intensity

            f = min(1, (s - rmin) / (rmax - rmin))
            # cl = grid_color * f + cls.background_color * (1 - f)
            cl = hg.Color(grid_color)
            cl.a *= f
            sx = view_center.x * resolution.x + (-cls.view2D.cursor_position.x / pixel_size)
            sy = view_center.y * resolution.y + (-cls.view2D.cursor_position.y / pixel_size)
            step = grid_size * view_zoom
            sxl, sxr = sx, sx + step
            syh, syl = sy, sy + step

            while sxl > 0:
                cls.line2D(resolution, sxl, 0, sxl, resolution.y, cl)
                sxl -= step

            while sxr < resolution.x:
                cls.line2D(resolution, sxr, 0, sxr, resolution.y, cl)
                sxr += step

            while syh > 0:
                cls.line2D(resolution, 0, syh, resolution.x, syh, cl)
                syh -= step

            while syl < resolution.y:
                cls.line2D(resolution, 0, syl, resolution.x, syl, cl)
                syl += step

    @classmethod
    def get_point_plane(cls, ps: hg.Vec2, resolution: hg.Vec2, snap_to_grid=True, snap_to_vertex=False):

        msp = (ps - resolution / 2) / resolution.y * cls.view2D.view_scale + cls.view2D.cursor_position

        v_snap = False
        cls.current_join_vertex = None
        if snap_to_vertex:
            shape = cls.get_current_shape()
            if shape is not None:
                v = []
                for split in shape["splits"]:
                    if split["valide"]:
                        v = v + [split["vertices"][split["inside_idx"]], split["intersections"][0]["vertex"]]
                v = v + shape["vertices"]
                for p in v:
                    if hg.Len(p - msp) < cls.join_distance:
                        msp = hg.Vec2(p.x, p.y)
                        cls.current_join_vertex = p
                        v_snap = True
                        break

        if snap_to_grid and not v_snap:
            if cls.flag_show_subdivision_grid:
                q = cls.view2D.grid_size / cls.view2D.grid_subdivisions
            else:
                q = cls.view2D.grid_size
            if msp.x < 0:
                o = -0.5
            else:
                o = 0.5
            msp.x = (int(msp.x / q + o)) * q
            if msp.y < 0:
                o = -0.5
            else:
                o = 0.5
            msp.y = (int(msp.y / q + o)) * q

        return msp

    @classmethod
    def draw_point(cls, vid, p, resolution, color, psize):
        size = cls.view2D.view_scale / resolution.y * psize
        cls.draw_square(vid, p, size, color)

    @classmethod
    def draw_crossed_point(cls, vid, p, resolution, color, psize):
        size = cls.view2D.view_scale / resolution.y * psize
        cls.draw_crossed_square(vid, p, size, color)

    @classmethod
    def draw_square(cls, vid, p, s_size, color):
        vtx = hg.Vertices(cls.vtx_decl, 8)
        vtx.Clear()
        size = s_size / 2
        p1 = hg.Vec3(p.x - size, p.y - size, 0)
        p2 = hg.Vec3(p.x - size, p.y + size, 0)
        p3 = hg.Vec3(p.x + size, p.y + size, 0)
        p4 = hg.Vec3(p.x + size, p.y - size, 0)
        cp = dc.pack_color_RGba(color)
        vtx.Begin(0).SetPos(p1).SetColor0(cp).End()
        vtx.Begin(1).SetPos(p2).SetColor0(cp).End()

        vtx.Begin(2).SetPos(p2).SetColor0(cp).End()
        vtx.Begin(3).SetPos(p3).SetColor0(cp).End()

        vtx.Begin(4).SetPos(p3).SetColor0(cp).End()
        vtx.Begin(5).SetPos(p4).SetColor0(cp).End()

        vtx.Begin(6).SetPos(p4).SetColor0(cp).End()
        vtx.Begin(7).SetPos(p1).SetColor0(cp).End()

        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    @classmethod
    def draw_crossed_square(cls, vid, p, s_size, color):
        vtx = hg.Vertices(cls.vtx_decl, 12)
        vtx.Clear()
        size = s_size / 2
        p1 = hg.Vec3(p.x - size, p.y - size, 0)
        p2 = hg.Vec3(p.x - size, p.y + size, 0)
        p3 = hg.Vec3(p.x + size, p.y + size, 0)
        p4 = hg.Vec3(p.x + size, p.y - size, 0)

        cp = dc.pack_color_RGba(color)

        vtx.Begin(0).SetPos(p1).SetColor0(cp).End()
        vtx.Begin(1).SetPos(p2).SetColor0(cp).End()

        vtx.Begin(2).SetPos(p2).SetColor0(cp).End()
        vtx.Begin(3).SetPos(p3).SetColor0(cp).End()

        vtx.Begin(4).SetPos(p3).SetColor0(cp).End()
        vtx.Begin(5).SetPos(p4).SetColor0(cp).End()

        vtx.Begin(6).SetPos(p4).SetColor0(cp).End()
        vtx.Begin(7).SetPos(p1).SetColor0(cp).End()

        vtx.Begin(8).SetPos(p1).SetColor0(cp).End()
        vtx.Begin(9).SetPos(p3).SetColor0(cp).End()

        vtx.Begin(10).SetPos(p2).SetColor0(cp).End()
        vtx.Begin(11).SetPos(p4).SetColor0(cp).End()

        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    @classmethod
    def draw_point_circle(cls, vid, c, r, resolution, color):
        ray = cls.view2D.view_scale / resolution.y * r
        cls.draw_circle(vid, c, ray, color)

    @classmethod
    def draw_circle(cls, vid, c, r, color):
        cp = dc.pack_color_RGba(color)
        numSegments = 32
        stp = 2 * pi / numSegments
        p0 = hg.Vec3(c.x + r, c.y, 0)
        p1 = hg.Vec3(0, 0, 0)
        vtx = hg.Vertices(cls.vtx_decl, numSegments * 2 + 2)
        vtx.Clear()

        for i in range(numSegments + 1):
            p1.x = r * cos(i * stp) + c.x
            p1.y = r * sin(i * stp) + c.y
            vtx.Begin(2 * i).SetPos(p0).SetColor0(cp).End()
            vtx.Begin(2 * i + 1).SetPos(p1).SetColor0(cp).End()
            p0.x, p0.y = p1.x, p1.y

        hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

    # ============================================= Model render functions ============================

    @classmethod
    # Basic polygon checks
    # polygon must contains "vertices" and "closed" fields
    def check_polygon(cls, polygon):
        polygon["geometry_error"] = []
        # Vertex - vertices distance:
        v = polygon["vertices"]
        n = len(v)
        for v_idx0 in range(n):
            v0 = v[v_idx0]
            for v_idx1 in range(v_idx0, n):
                if v_idx0 != v_idx1:
                    v1 = v[v_idx1]
                    d = hg.Len(v0 - v1)
                    if d <= 1e-5:
                        polygon["geometry_error"].append(["vertex_overlay", v[v_idx0]])

        # Edge crossing:
        if polygon["closed"]:
            sc = 0
        else:
            sc = 1
        for v_idx0 in range(n - sc):
            vA = v[v_idx0]
            vB = v[(v_idx0 + 1) % n]
            for v_idx1 in range(v_idx0, n - sc):
                if v_idx0 == 0 and v_idx1 == n - 1:
                    continue
                if v_idx1 > v_idx0 + 1:
                    vC = v[v_idx1]
                    vD = v[(v_idx1 + 1) % n]
                    pi, t1, t2 = pol.vectors2D_intersection(vA, vB, vC, vD)
                    if pi is not None:
                        polygon["geometry_error"].append(["edge_crossing", pi])

    @classmethod
    # Try to find
    def check_folds(cls, shape):
        folds_check = {"vertices_distances":[]}
        size = shape["edit_box"].size * shape["edit_box"].scale
        smax = max(size.x, size.y)
        cls.folds_joined_vertices_distance_min = smax / 500
        dist_min = cls.folds_joined_vertices_distance_min
        # Get shape-vertex-joined folds:

        joined_folds = []
        for fold_idx0 in range(len(shape["folds"])):
            fold0 = shape["folds"][fold_idx0]
            if len(fold0["intersections"]) >= 2:
                if fold0["intersections"][0]["join_idx"] == 0 or fold0["intersections"][1]["join_idx"] == 0:
                    joined = {"fold_idx": fold_idx0, "v0": False, "v1": False, "distances": []}
                    if fold0["intersections"][0]["join_idx"] == 0:
                        if fold0["intersections"][0]["t"] == 0:
                            joined["v0"] = True
                        else:
                            joined["v1"] = True
                    if fold0["intersections"][1]["join_idx"] == 0:
                        if fold0["intersections"][1]["t"] == 0:
                            joined["v0"] = True
                        else:
                            joined["v1"] = True
                    joined_folds.append(joined)

        n = len(joined_folds)

        for jf_idx0 in range(n-1):
            jf0 = joined_folds[jf_idx0]
            fidx0 = jf0["fold_idx"]
            f0 = shape["folds"][fidx0]
            f0v0 = f0["vertices"][0]
            f0v1 = f0["vertices"][1]
            for jf_idx1 in range(jf_idx0+1, n):
                jf1 = joined_folds[jf_idx1]
                fidx1 = jf1["fold_idx"]
                f1 = shape["folds"][fidx1]
                f1v0 = f1["vertices"][0]
                f1v1 = f1["vertices"][1]
                vdist = [
                            hg.Len(f0v0 - f1v0) if jf0["v0"] and jf1["v0"] else None,
                            hg.Len(f0v0 - f1v1) if jf0["v0"] and jf1["v1"] else None,
                            hg.Len(f0v1 - f1v0) if jf0["v1"] and jf1["v0"] else None,
                            hg.Len(f0v1 - f1v1) if jf0["v1"] and jf1["v1"] else None
                        ]
                jf0["distances"].append({"fold_idx": fidx1, "vertices_dist": vdist})

                e = 1e-6
                if vdist[0] is not None and e < vdist[0] < dist_min:
                    folds_check["vertices_distances"].append({"folds": [fidx0, fidx1], "fold0_vidx": 0, "fold1_vidx": 0})
                if vdist[1] is not None and e < vdist[1] < dist_min:
                    folds_check["vertices_distances"].append({"folds": [fidx0, fidx1], "fold0_vidx": 0, "fold1_vidx": 1})
                if vdist[2] is not None and e < vdist[2] < dist_min:
                    folds_check["vertices_distances"].append({"folds": [fidx0, fidx1], "fold0_vidx": 1, "fold1_vidx": 0})
                if vdist[3] is not None and e < vdist[3] < dist_min:
                    folds_check["vertices_distances"].append({"folds": [fidx0, fidx1], "fold0_vidx": 1, "fold1_vidx": 1})

        return folds_check

    @classmethod
    def clear_shape_rendering_datas(cls, shape):
        def clear_keys(obj, ks):
            delete_keys = []
            for k in obj.keys():
                if k not in ks:
                    delete_keys.append(k)
            for k in delete_keys:
                del (obj[k])

        clear_keys(shape, list(cls.new_2d_shape().keys()))
        for fold in shape["folds"]:
            clear_keys(fold, list(cls.new_2d_fold().keys()))
            fold["intersections"] = []
        for split in shape["splits"]:
            clear_keys(split, list(cls.new_2d_split().keys()))
            split["intersections"] = []
        for hole in shape["holes"]:
            clear_keys(hole, list(cls.new_2d_hole().keys()))

    @classmethod
    def generates_shape(cls, shape, flag_holes):
        cls.clear_shape_rendering_datas(shape)
        cls.check_polygon(shape)
        if shape["closed"]:
            cls.split_shape(shape)
            cls.generate_folds_intersections(shape)
            shape["folds_check_log"] = cls.check_folds(shape)
            if "geometry_error" in shape and len(shape["geometry_error"]) > 0:
                shape["folded_vertices"] = []
                shape["faces"] = []
            else:
                cls.make_rounded_segments(shape)
                cls.make_shape_indexes(shape)
                cls.generate_faces(shape)
                if flag_holes:
                    cls.generate_holes(shape)
                cls.triangulate_faces(shape)

    @classmethod
    def triangulate_faces(cls, shape):
        if "faces" in shape:
            for face_idx in range(len(shape["faces"])): #Face_idx used to facilitate debugging
                face = shape["faces"][face_idx]
                face["triangles"] = pol.triangulate_polygon_idx(shape["folded_vertices"], face["idx"])
                if "holey_idx" in face:
                    face["holey_triangles"] = []
                    for part in face["holey_idx"]:
                        triangles = pol.triangulate_polygon_idx(shape["holey_vertices"], part)
                        if triangles is not None:
                            face["holey_triangles"].append(triangles)
                        else:
                            face["holey_triangles"] = "Unable to triangulate holey face"

    @classmethod
    def create_new_face(cls):
        return {"idx": [], "triangles": [], "normal": hg.Vec3(0, 0, 0)} # , "holey": [], "holey_idx": [], "holey_triangles": []

    @classmethod
    def make_shape_indexes(cls, shape):

        shape["folded_vertices"] = []
        face = cls.create_new_face()

        # insert folds intersection in shape's vertices
        sv = shape["splitted_vertices"] if "splitted_vertices" in shape else shape["vertices"]

        n = len(sv)
        vf_idx = 0
        inters_vf_idx_plus_1_check = []
        for v_idx in range(n):
            v0 = sv[v_idx]
            v1 = sv[(v_idx + 1) % n]
            shape["folded_vertices"].append(v0)
            face["idx"].append(vf_idx)

            # List des intersections sur l'arête:
            edge_inters = []

            def compute_t(interTab, tid):  # tid: fold ou segment d'arrondi
                for inter_idx in range(2):
                    inter = interTab[inter_idx]
                    if inter["edge_idx"] == v_idx:
                        edge_inters.append(inter)
                        inter["t"] = hg.Len(inter["vertex"] - v0)
                        inter["type"] = tid

            for fold in shape["folds"]:
                if len(fold["intersections"]) >= 2:
                    if fold["segments_intersections"] is None:
                        compute_t(fold["intersections"], "fold")
                    else:
                        for segment in fold["segments_intersections"]:
                            compute_t(segment, "segment")

            # Tri des intersections:
            if len(edge_inters) > 1: edge_inters.sort(key=lambda p: p["t"])

            for inter in edge_inters:
                # Join: voire la fonction "generate_folds_intersections":
                if inter["join_idx"] == 0:
                    inter["idx"] = vf_idx
                elif inter["join_idx"] == 1:
                    inter["idx"] = vf_idx + 1  # /!\ bouclage
                    inters_vf_idx_plus_1_check.append(inter)  # Report de vérification du bouclage
                else:
                    vf_idx += 1
                    shape["folded_vertices"].append(inter["vertex"])
                    face["idx"].append(vf_idx)
                    inter["idx"] = vf_idx
            vf_idx += 1

        # vérifie les dépassements des intersection collées au sommet supérieur (v1):
        for inter in inters_vf_idx_plus_1_check:
            inter["idx"] = inter["idx"] % vf_idx

        # Répercute les indexes des segments centraux sur le main fold:
        for fold in shape["folds"]:
            if len(fold["intersections"]) >= 2 and fold["segments_intersections"] is not None:
                fold["intersections"][0]["idx"] = fold["segments_intersections"][len(fold["segments_intersections"]) // 2][0]["idx"]
                fold["intersections"][1]["idx"] = fold["segments_intersections"][len(fold["segments_intersections"]) // 2][1]["idx"]

        shape["faces"] = [face]

    @classmethod
    def generate_faces(cls, shape):
        if "folds" in shape and len(shape["folds"]) > 0:
            for fold in shape["folds"]:
                fold["valide"] = False
                if len(fold["intersections"]) >= 2:
                    cls.cut_shape(shape, fold)

    @classmethod
    def generate_holes(cls, shape):
        v = shape["folded_vertices"]
        for face in shape["faces"]:
            face["holey"] = None
            face_holeys = [[]]
            for vidx in face["idx"]:
                face_holeys[0].append(v[vidx])
            for hole in shape["holes"]:
                if hole["closed"]:
                    new_holey = []
                    for holey_idx, face_holey in enumerate(face_holeys):
                        f, holey_polygons = pol.subtract_polygon(face_holey, hole["vertices"])
                        if holey_polygons is not None:
                            new_holey = new_holey + holey_polygons
                    if len(new_holey) > 0:
                        face_holeys = new_holey
            face["holey"] = face_holeys
        cls.clean_holey_vertices(shape)

    @classmethod
    def get_vertex_parent_edge(cls, vertex, edges, vertices):
        for i, edge in edges.items():
            if i > -1:
                dist = pol.point_edge_distance(vertex, vertices[edge[0]], vertices[edge[1]])
                if dist < 1e-5:
                    return i
        return -1

    @classmethod
    def clean_holey_vertices(cls, shape, flag_edges_parenting=True):
        if flag_edges_parenting:
            # Internal edges listing:
            edges = {}
            internal_edges = {-1: -1}
            for face in shape["faces"]:
                n = len(face["idx"])
                for idx in range(n):
                    v0 = face["idx"][idx]
                    v1 = face["idx"][(idx + 1) % n]
                    if v1 < v0 :
                        v0, v1 = v1, v0
                    hash = int( v0 * 100000 + v1)
                    if not hash in edges:
                        edges[hash] = [v0, v1]
                    else:
                        if not hash in internal_edges:
                            internal_edges[hash] = [v0, v1]


            #Assign holey vertices to originals edges:
            faces_edges_links = []
            for face in shape["faces"]:
                holeys_edges_links = []
                for holey in face["holey"]:
                    holey_edges_links = []
                    for v_idx in range(len(holey)):
                        v = holey[v_idx]
                        holey_edges_links.append(cls.get_vertex_parent_edge(v, internal_edges, shape["folded_vertices"]))
                    holeys_edges_links.append(holey_edges_links)
                faces_edges_links.append(holeys_edges_links)

        shape["holey_vertices"] = []
        if flag_edges_parenting: holey_vertices_edges_links = []
        for face_idx in range(len(shape["faces"])):
            face = shape["faces"][face_idx]
            if flag_edges_parenting: holeys_edges_links = faces_edges_links[face_idx]
            face["holey_idx"] = []
            for h_idx in range(len(face["holey"])):
                holey = face["holey"][h_idx]
                if flag_edges_parenting: holey_edges_links = holeys_edges_links[h_idx]
                holey_idx = []
                for v_idx in range(len(holey)):
                    v = holey[v_idx]
                    if flag_edges_parenting: edge_hash = holey_edges_links[v_idx]
                    flag_merge = False
                    for idx, v0 in enumerate(shape["holey_vertices"]):
                        if hg.Len(v0 - v) < 1e-4:
                            if (not flag_edges_parenting) or holey_vertices_edges_links[idx] == edge_hash:
                                if not (len(holey_idx) > 0 and holey_idx[-1] == idx):
                                    holey_idx.append(idx)
                                flag_merge = True
                                break
                    if not flag_merge:
                        holey_idx.append(len(shape["holey_vertices"]))
                        shape["holey_vertices"].append(v)
                        if flag_edges_parenting: holey_vertices_edges_links.append(edge_hash)
                face["holey_idx"].append(holey_idx)

    @classmethod
    def cut_shape(cls, shape, fold):
        faces = shape["faces"]

        def make_face(face, inter_idx, idx2):
            new_face = cls.create_new_face()
            n = len(face["idx"])
            idx = -1
            while idx != inter_idx:
                idx = face["idx"][idx2]
                new_face["idx"].append(idx)
                idx2 = (idx2 + 1) % n
            return new_face

        def make_faces(inter0, inter1):
            for face_idx in range(len(faces)):
                face = faces[face_idx]
                idx2_i0 = -1
                idx2_i1 = -1
                for idx2 in range(len(face["idx"])):
                    idx = face["idx"][idx2]
                    if idx == inter0["idx"]:
                        idx2_i0 = idx2
                    if idx == inter1["idx"]:
                        idx2_i1 = idx2
                    if idx2_i0 >= 0 and idx2_i1 >= 0:
                        face0 = make_face(face, inter1["idx"], idx2_i0)
                        face1 = make_face(face, inter0["idx"], idx2_i1)
                        faces.pop(face_idx)
                        faces.insert(face_idx, face1)
                        faces.insert(face_idx, face0)
                        return True
            return False

        # Détermine la face contenant le fold:
        if fold["segments_intersections"] is None:
            fi0 = fold["intersections"][0]
            fi1 = fold["intersections"][1]
            if make_faces(fi0, fi1) == False:
                shape["geometry_error"].append(["Crossed fold", (fi0["vertex"] + fi1["vertex"]) / 2])
                return
        else:
            segments_valides = True
            for segment in fold["segments_intersections"]:
                if make_faces(segment[0], segment[1]) == False:
                    shape["geometry_error"].append(["Crossed segments", (segment[0]["vertex"] + segment[1]["vertex"]) / 2])
                    segments_valides = False
            if not segments_valides: return

        fold["valide"] = True

    @classmethod
    def generates_splits_intersections(cls, shape):
        if "geometry_error" in shape and len(shape["geometry_error"]) > 0:
            for split in shape["splits"]:
                split["intersections"] = []
        else:
            for split_idx in range(len(shape["splits"])):
                split = shape["splits"][split_idx]
                if cls.get_current_ui_state_id() == cls.UI_STATE_DRAWING and split_idx == cls.current_split:
                    join_dist = cls.join_distance
                else:
                    join_dist = 1e-6
                split["intersections"] = []
                split["inside_idx"] = 1
                vf = split["vertices"]
                if hg.Len(vf[1] - vf[0]) < 1e-5:
                    split["valide"] = False
                else:
                    v = shape["vertices"]
                    v0 = v[0]
                    n = len(v)
                    if shape["closed"]:
                        cl = 1
                    else:
                        cl = 0
                    for v_idx in range(1, n + cl):
                        v1 = v[v_idx % n]
                        # Test vertices du split joints au vertex 0:
                        d0 = hg.Len(vf[0] - v0)
                        d1 = hg.Len(vf[1] - v0)
                        d2 = hg.Len(vf[0] - v1)
                        d3 = hg.Len(vf[1] - v1)
                        if d0 < join_dist or d1 < join_dist:
                            if d0 < join_dist and d1 < join_dist:
                                if d0 < d1:
                                    t = 0
                                else:
                                    t = 1
                            elif d0 < join_dist:
                                t = 0
                            elif d1 < join_dist:
                                t = 1
                                split["inside_idx"] = 0
                            split["intersections"].append({"vertex": hg.Vec2(v0.x, v0.y), "edge_t": 0, "t": t, "edge_idx": v_idx - 1, "idx": -1, "join_idx": 0})  # edge_t = pos on edge
                        elif d0 > join_dist and d1 > join_dist and d2 > join_dist and d3 > join_dist:
                            # Points d'intersection du split:
                            p, t1, t2 = pol.vectors2D_intersection(vf[0], vf[1], v0, v1)

                            if p is not None:
                                split["intersections"].append({"vertex": p, "edge_t": t2, "t": t1, "edge_idx": v_idx - 1, "idx": -1, "join_idx": -1})  # edge_t = pos on edge
                        v0 = v1
                    ni = len(split["intersections"])
                    if ni == 1:
                        if split["intersections"][0]["join_idx"] == 0:
                            if split["intersections"][0]["t"] == 0 and not pol.polygon_contains(v, vf[1].x, vf[1].y):
                                split["valide"] = False
                                continue
                            elif split["intersections"][0]["t"] == 1 and not pol.polygon_contains(v, vf[0].x, vf[0].y):
                                split["valide"] = False
                                continue
                        elif split["intersections"][0]["join_idx"] < 0 and pol.polygon_contains(v, vf[0].x, vf[0].y):
                            split["inside_idx"] = 0
                        split["valide"] = True
                    elif ni != 1:
                        if ni > 1:
                            shape["geometry_error"].append(["Split cuts shape", (split["vertices"][0] + split["vertices"][1]) / 2])
                        split["valide"] = False

    @classmethod
    def split_shape(cls, shape):
        if "splits" in shape:
            cls.generates_splits_intersections(shape)

            # Check crossing splits:
            for s0_idx in range(len(shape["splits"]) - 1):
                split0 = shape["splits"][s0_idx]
                if split0["valide"]:
                    for s1_idx in range(s0_idx + 1, len(shape["splits"])):
                        split1 = shape["splits"][s1_idx]
                        if split1["valide"]:
                            p, t1, t2 = pol.vectors2D_intersection(split0["vertices"][0], split0["vertices"][1], split1["vertices"][0], split1["vertices"][1])
                            if p is not None:
                                if pol.polygon_contains(shape["vertices"], p.x, p.y):
                                    split0["valide"] = False
                                    shape["geometry_error"].append(["Crossing splits", p])

            # Sort splits along edges:
            edges_links = []
            for e_idx in range(len(shape["vertices"])):
                edges_links.append([])
                for split in shape["splits"]:
                    if split["valide"]:
                        inter = split["intersections"][0]
                        if inter["edge_idx"] == e_idx:
                            edges_links[e_idx].append(split)
                if len(edges_links[e_idx]) > 0:
                    edges_links[e_idx].sort(key=lambda p: p["intersections"][0]["edge_t"])

            # Generate splited vertices
            v = shape["vertices"]
            n = len(v)
            sv = []
            shape["splitted_vertices"] = sv
            for e_idx in range(len(shape["vertices"])):
                if len(edges_links[e_idx]) > 0:
                    for s_idx, split in enumerate(edges_links[e_idx]):
                        iidx = split["inside_idx"]
                        vs = hg.Normalize(split["vertices"][iidx] - split["vertices"][1 - iidx])
                        nf = hg.Vec2(-vs.y, vs.x)
                        p0 = hg.Vec2(split["intersections"][0]["vertex"])
                        p1 = hg.Vec2(split["vertices"][iidx])

                        uv0 = hg.Normalize(v[(e_idx + 1) % n] - v[e_idx])
                        dot0 = hg.Dot(uv0, nf)

                        uv1 = hg.Normalize(v[e_idx] - v[(e_idx - 1) % n])
                        dot1 = hg.Dot(uv1, nf)

                        split["splitted_vertices_idx"] = len(sv)  # Start split quad indices

                        if split["intersections"][0]["join_idx"] == 0 and dot0 < dot1:

                            sv.append(p0 - uv1 * (shape["split_thickness"] / dot1))
                            sv.append(p1 - nf * shape["split_thickness"])
                            sv.append(p1)
                            sv.append(p0)
                        else:
                            if s_idx == 0:
                                sv.append(hg.Vec2(v[e_idx]))
                            if split["intersections"][0]["join_idx"] < 0:
                                if s_idx == 0:
                                    split["splitted_vertices_idx"] += 1
                                sv.append(p0)
                            sv.append(p1)
                            sv.append(p1 + nf * shape["split_thickness"])
                            sv.append(p0 + uv0 * (shape["split_thickness"] / dot0))

                else:
                    sv.append(hg.Vec2(v[e_idx]))

            # Generate splitted folds:
            sv = shape["splitted_vertices"]
            for fold in shape["folds"]:
                fold["splitted_vertices"] = [hg.Vec2(fold["vertices"][0]), hg.Vec2(fold["vertices"][1])]
            for split in shape["splits"]:
                if split["valide"]:
                    iidx = split["inside_idx"]
                    vs0 = split["intersections"][0]["vertex"]
                    vs1 = split["vertices"][iidx]
                    vs = hg.Normalize(vs1 - vs0)
                    ns = hg.Vec2(-vs.y, vs.x)
                    for fold in shape["folds"]:
                        vf0 = fold["vertices"][0]
                        vf1 = fold["vertices"][1]

                        # Join edge intersection splitted vertices to fold vertices
                        if hg.Len(vf0 - vs0) < 1e-6:
                            dot = hg.Dot(ns, vf1 - vf0)
                            if dot >= 0:
                                v = sv[split["splitted_vertices_idx"] + 3]
                            elif dot < 0:
                                v = sv[split["splitted_vertices_idx"] + 0]
                            fold["splitted_vertices"][0].x = v.x
                            fold["splitted_vertices"][0].y = v.y

                        elif hg.Len(vf1 - vs0) < 1e-6:
                            dot = hg.Dot(ns, vf0 - vf1)
                            if dot >= 0:
                                v = sv[split["splitted_vertices_idx"] + 3]
                            elif dot < 0:
                                v = sv[split["splitted_vertices_idx"] + 0]
                            fold["splitted_vertices"][1].x = v.x
                            fold["splitted_vertices"][1].y = v.y

                        # Join inside splitted vertices to fold vertices
                        elif hg.Len(vf0 - vs1) < 1e-6:
                            dot = hg.Dot(ns, vf1 - vf0)
                            if dot >= 0:
                                v = sv[split["splitted_vertices_idx"] + 2]
                            elif dot < 0:
                                v = sv[split["splitted_vertices_idx"] + 1]
                            fold["splitted_vertices"][0].x = v.x
                            fold["splitted_vertices"][0].y = v.y


                        elif hg.Len(vf1 - vs1) < 1e-6:
                            dot = hg.Dot(ns, vf0 - vf1)
                            if dot >= 0:
                                v = sv[split["splitted_vertices_idx"] + 2]
                            elif dot < 0:
                                v = sv[split["splitted_vertices_idx"] + 1]
                            fold["splitted_vertices"][1].x = v.x
                            fold["splitted_vertices"][1].y = v.y

    @classmethod
    def generate_folds_intersections(cls, shape):
        if "folds" in shape:
            if "geometry_error" in shape and len(shape["geometry_error"]) > 0:
                for fold in shape["folds"]:
                    fold["intersections"] = []
                    fold["segments_intersections"] = None
            else:
                v = shape["splitted_vertices"] if "splitted_vertices" in shape else shape["vertices"]
                for fold_idx in range(len(shape["folds"])):
                    fold = shape["folds"][fold_idx]
                    if cls.get_current_ui_state_id() == cls.UI_STATE_DRAWING and fold_idx == cls.current_fold:
                        join_dist = cls.join_distance
                    else:
                        join_dist = 1e-6
                    fold["intersections"] = []
                    vf = fold["splitted_vertices"] if "splitted_vertices" in fold else fold["vertices"]
                    v0 = v[0]
                    n = len(v)
                    if shape["closed"]:
                        cl = 1
                    else:
                        cl = 0
                    for v_idx in range(1, n + cl):
                        v1 = v[v_idx % n]
                        # Test vertices du fold joints au vertex 0:
                        d0 = hg.Len(vf[0] - v0)
                        d1 = hg.Len(vf[1] - v0)
                        d2 = hg.Len(vf[0] - v1)
                        d3 = hg.Len(vf[1] - v1)
                        if d0 < join_dist or d1 < join_dist:
                            if d0 < join_dist and d1 < join_dist:
                                if d0 < d1:
                                    t = 0
                                else:
                                    t = 1
                            elif d0 < join_dist:
                                t = 0
                            elif d1 < join_dist:
                                t = 1
                            fold["intersections"].append({"vertex": hg.Vec2(v0.x, v0.y), "t": t, "edge_idx": v_idx - 1, "idx": -1, "join_idx": 0})
                        elif d0 > join_dist and d1 > join_dist and d2 > join_dist and d3 > join_dist:
                            # Points d'intersection du fold:
                            p, t1, t2 = pol.vectors2D_intersection(vf[0], vf[1], v0, v1)

                            if p is not None:
                                fold["intersections"].append({"vertex": p, "t": t1, "edge_idx": v_idx - 1, "idx": -1, "join_idx": -1})
                        v0 = v1
                    if len(fold["intersections"]) > 1:
                        fold["intersections"].sort(key=lambda p: p["t"])
                        # tri intersection dans l'ordre croissant des arêtes:
                        if fold["intersections"][0]["edge_idx"] > fold["intersections"][1]["edge_idx"]:
                            fold["intersections"][0], fold["intersections"][1] = fold["intersections"][1], fold["intersections"][0]

    @classmethod
    def get_translated_segment_vertex(cls, vertices, dist, p0, i0, p1, i1, reverse=False):
        """
        :param shape: polygon
        :param dist: distance normale au segment
        :param p0: point 0 du segment
        :param i0: edge id du point 0
        :param p1: point 1 du segment
        :param i1: edge id du point 1
        :param reverse: Sens de translation dans le polygon, à partir du point 0 (le point 0 est toujours situé sur un edge antérieur au point 1)
        :return: tuple: [ {error id, t(p0), t(i0)} , {error id, t(p1), t(i1)} ]
        """
        n = len(vertices)
        i0_start = i0
        i1_start = i1
        vf = p1 - p0
        nf = hg.Normalize(hg.Vec2(-vf.y, vf.x))
        if reverse: nf = nf * -1

        # p0:
        def t_p0(p, d, i):
            d0 = d
            if d < 1e-6:
                return {"error": 0, "vertex": p, "edge_idx": i, "distance": 0}
            pt = {"error": -1, "vertex": None, "edge_idx": 0, "distance": 0}  # error_id, p, edge_idx, dist (dist < dist_start en cas d'angle aigue ou de sortie de polygone)
            while True:
                if reverse:
                    pe1 = vertices[i]
                else:
                    pe1 = vertices[(i + 1) % n]
                v0 = pe1 - p
                if hg.Len(v0) > 1e-6:
                    a = acos(max(-1, min(1, hg.Dot(hg.Normalize(v0), nf)))) / pi * 180
                    t = hg.Dot(v0, nf) / d
                    if t < 0 or a > cls.round_max_angle:  # Acute angle
                        if reverse:
                            i = (i + 1) % n
                        else:
                            i = (i - 1) % n
                        pt = {"error": 1, "vertex": p, "edge_idx": i, "distance": d0 - d}
                        return pt
                    if t < 1:
                        if reverse:
                            i = (i - 1) % n
                        else:
                            i = (i + 1) % n
                        if i == i0_start:  # Normalement cas impossible.
                            if reverse:
                                i0 = (i + 1) % n
                            else:
                                i0 = (i - 1) % n
                            pt["error"] = 2
                            return pt
                        p = pe1
                        d -= d * t
                    else:
                        pt = {"error": 0, "vertex": p + v0 / t, "edge_idx": i, "distance": d0}
                        return pt
                # fold vertex confondu avec shape vertex, on passe au suivant:
                # seulement possible en reverse.
                else:
                    i = (i - 1) % n

        # p1:
        def t_p1(p, d, i):
            d0 = d
            if d < 1e-6:
                return {"error": 0, "vertex": p, "edge_idx": i, "distance": 0}
            pt = {"error": -1, "vertex": None, "edge_idx": 0, "distance": 0}
            while True:
                if not reverse:
                    pe1 = vertices[i]
                else:
                    pe1 = vertices[(i + 1) % n]
                v0 = pe1 - p
                if hg.Len(v0) > 1e-6:
                    a = acos(max(-1, min(1, hg.Dot(hg.Normalize(v0), nf)))) / pi * 180
                    t = hg.Dot(v0, nf) / d
                    if t < 0 or a > cls.round_max_angle:  # Acute angle
                        if not reverse:
                            i = (i + 1) % n
                        else:
                            i = (i - 1) % n
                        pt = {"error": 1, "vertex": p, "edge_idx": i, "distance": d0 - d}
                        return pt
                    if t < 1:
                        if not reverse:
                            i = (i - 1) % n
                        else:
                            i = (i + 1) % n
                        if i == i1_start:  # Normalement cas impossible.
                            if not reverse:
                                i = (i + 1) % n
                            else:
                                i = (i - 1) % n
                            pt["error"] = 2
                            return pt
                        p = pe1
                        d -= d * t
                    else:
                        pt = {"error": 0, "vertex": p + v0 / t, "edge_idx": i, "distance": d0}
                        return pt

                # fold vertex confondu avec shape vertex, on passe au suivant:
                # Seulement possible en non reverse
                else:
                    i = (i - 1) % n

        pt0 = t_p0(p0, dist, i0)
        pt1 = t_p1(p1, dist, i1)
        # Analyse:
        if pt0["error"] == 2 or pt1["error"] == 2:
            return None, None
        if pt0["error"] == 0 and pt1["error"] == 0:
            return pt0, pt1
        elif pt0["error"] == 1 or pt1["error"] == 1:
            if pt0["distance"] < pt1["distance"]:
                pt1 = t_p1(p1, pt0["distance"], i1)
            else:
                pt0 = t_p0(p0, pt1["distance"], i0)

        return pt0, pt1

    @classmethod
    def make_rounded_segments(cls, shape):
        ep = 1e-6
        sep = 1e-5

        def fold_error():
            # Plus de 2 fold sur un même vertex:
            shape["geometry_error"].append(["More than 2 folds on same vertex", po])
            fold["intersections"] = []  # désactivation du fold
            fold["segments_intersections"] = None

        def get_segment_vertex(vertices, _dist, p0, i1, step, _nf, _n):
            """
            :param dist: distance normale au point p0
            :param p0: point 0 du segment
            :param i1: indice p1 du segment
            :param step: sens de parcours des indices dans le polygone
            :param nf: direction de la distance
            :param n: nombre d'indices du polygone
            :return: position du point, indice de l'arête contenant le point
            """
            i_start = i1

            while True:
                p1 = vertices[i1]
                v = p1 - p0
                t = hg.Dot(v, _nf) / _dist
                if t < 1:
                    i1 = (i1 + step) % _n
                    if i1 == i_start:
                        return None, None
                    p0 = p1
                    _dist -= _dist * t
                else:
                    p = p0 + hg.Normalize(v) * hg.Len(v) / t
                    return p, i1

        sv = shape["splitted_vertices"] if "splitted_vertices" in shape else shape["vertices"]
        n = len(sv)

        for fold_idx in range(len(shape["folds"])):
            fold_valid = True
            fold = shape["folds"][fold_idx]
            fold["segments_intersections"] = None
            if len(fold["intersections"]) >= 2 and fold["round_segments_count"] > 0:
                fold["round_segments_rendered"] = fold["round_segments_count"]
                dist_max = fold["round_radius"] * abs(fold["fold_angle"] / 2)
                while fold["round_segments_rendered"] > 0 and dist_max / fold["round_segments_rendered"] < 5e-3: # Avoid too small distance between folds segments
                    fold["round_segments_rendered"] -= 1

                if fold["round_segments_rendered"] > 0:

                    # Sauvegarde fold originel
                    fi0 = fold["intersections"][0]
                    fi1 = fold["intersections"][1]
                    po = (fi0["vertex"] + fi1["vertex"]) / 2
                    fold["intersections_corrected"] = [{"edge_idx": fi0["edge_idx"], "vertex": hg.Vec2(fi0["vertex"].x, fi0["vertex"].y), "join_idx": fi0["join_idx"]},
                                                       {"edge_idx": fi1["edge_idx"], "vertex": hg.Vec2(fi1["vertex"].x, fi1["vertex"].y), "join_idx": fi1["join_idx"]}]

                    # ------------ Etape 1: 2 folds à sommet commun:
                    flag_2_folds_found_0 = False
                    flag_2_folds_found_1 = False
                    for fold2_idx in range(len(shape["folds"])):
                        fold2 = shape["folds"][fold2_idx]
                        if fold2_idx != fold_idx and len(fold2["intersections"]) >= 2:
                            f2i0 = fold2["intersections"][0]
                            f2i1 = fold2["intersections"][1]
                            vf = hg.Normalize(fi1["vertex"] - fi0["vertex"])
                            nf = hg.Vec2(-vf.y, vf.x)
                            vf2 = hg.Normalize(f2i1["vertex"] - f2i0["vertex"])
                            d_00 = hg.Len(fi0["vertex"] - f2i0["vertex"])
                            d_01 = hg.Len(fi0["vertex"] - f2i1["vertex"])
                            d_10 = hg.Len(fi1["vertex"] - f2i0["vertex"])
                            d_11 = hg.Len(fi1["vertex"] - f2i1["vertex"])

                            # Folds confondus:
                            if d_00 < ep and d_11 < ep or d_01 < ep and d_10 < ep:
                                fold2["intersections"] = []  # Désactivation du fold.

                            # Folds partagent 1 vertex
                            else:

                                def get_step0(fi, _vf2, _nf):  # Calcul le sens de déplacement >> à partir du point de contact << des deux folds
                                    # join au shape vertex
                                    if fi["join_idx"] >= 0:
                                        v0 = sv[(fi["edge_idx"] + fi["join_idx"] + 1) % n] - fi["vertex"]
                                        if hg.Dot(_nf, v0) < 0 or hg.Dot(_nf, _vf2) > 0:
                                            return -1
                                        else:
                                            return 1

                                    # sur le edge
                                    else:
                                        if hg.Dot(_nf, _vf2) > 0:
                                            return -1
                                        else:
                                            return 1

                                if d_00 < ep:
                                    if flag_2_folds_found_0:
                                        fold_error()
                                        fold_valid = False
                                        break
                                    flag_2_folds_found_0 = True
                                    step0 = get_step0(fi0, vf2, nf)

                                elif d_01 < ep:
                                    if flag_2_folds_found_0:
                                        fold_error()
                                        fold_valid = False
                                        break
                                    flag_2_folds_found_0 = True
                                    vf2 *= -1
                                    step0 = get_step0(fi0, vf2, nf)

                                elif d_10 < ep:
                                    if flag_2_folds_found_1:
                                        fold_error()
                                        fold_valid = False
                                        break
                                    flag_2_folds_found_1 = True
                                    step0 = -get_step0(fi1, vf2, nf * -1)
                                elif d_11 < ep:
                                    if flag_2_folds_found_1:
                                        fold_error()
                                        fold_valid = False
                                        break
                                    flag_2_folds_found_1 = True
                                    vf2 *= -1
                                    step0 = -get_step0(fi1, vf2, nf * -1)
                                else:
                                    continue  # Pas de vertex partagé

                                # Fold 0
                                p0 = fi0["vertex"]

                                if step0 == -1:
                                    nf = nf * -1
                                    if fi0["join_idx"] != 0:
                                        i1 = fi0["edge_idx"]
                                    else:
                                        i1 = (fi0["edge_idx"] - 1) % n
                                else:
                                    if fi0["join_idx"] != 1:
                                        i1 = (fi0["edge_idx"] + 1) % n
                                    else:
                                        i1 = (fi0["edge_idx"] + 2) % n

                                s0, edge_idx0 = get_segment_vertex(sv, dist_max + ep * 4, p0, i1, step0, nf, n)
                                if s0 == None:
                                    shape["geometry_error"].append(["Fold out of shape", po])
                                    fold_valid = False
                                    break
                                if step0 == 1: edge_idx0 = (edge_idx0 - 1) % n

                                p0 = fi1["vertex"]

                                if -step0 == -1:
                                    if fi1["join_idx"] != 0:
                                        i1 = fi1["edge_idx"]
                                    else:
                                        i1 = (fi1["edge_idx"] - 1) % n
                                else:
                                    if fi1["join_idx"] != 1:
                                        i1 = (fi1["edge_idx"] + 1) % n
                                    else:
                                        i1 = (fi1["edge_idx"] + 2) % n

                                s1, edge_idx1 = get_segment_vertex(sv, dist_max + ep * 4, p0, i1, -step0, nf, n)
                                if s1 == None:
                                    shape["geometry_error"].append(["Fold out of shape", po])
                                    fold_valid = False
                                    break

                                if -step0 == 1: edge_idx1 = (edge_idx1 - 1) % n

                                fold["intersections_corrected"] = [{"edge_idx": edge_idx0, "vertex": s0, "join_idx": -1},
                                                                   {"edge_idx": edge_idx1, "vertex": s1, "join_idx": -1}]

                    # Le fold 2 sera modifié lors d'une autre itération, par rapport à la configuration initiale du fold 1.

                    if fold_valid:

                        # ------------- Clamp & recenter fold :

                        fi0 = fold["intersections_corrected"][0]
                        fi1 = fold["intersections_corrected"][1]

                        #
                        tp0, tp1 = cls.get_translated_segment_vertex(sv, dist_max, fi0["vertex"], fi0["edge_idx"], fi1["vertex"], fi1["edge_idx"])
                        tp2, tp3 = cls.get_translated_segment_vertex(sv, dist_max, fi0["vertex"], fi0["edge_idx"], fi1["vertex"], fi1["edge_idx"], True)
                        clamped_dist = tp0["distance"] + tp2["distance"]
                        if clamped_dist < dist_max * 2:
                            if tp0["distance"] < tp2["distance"]:
                                if tp2["distance"] > dist_max - sep:
                                    tp2t, tp3t = cls.get_translated_segment_vertex(sv, dist_max * 2, tp0["vertex"], tp0["edge_idx"], tp1["vertex"], tp1["edge_idx"], True)
                                    dist_max = tp2t["distance"] / 2
                                else:
                                    dist_max = clamped_dist / 2
                                tfi0, tfi1 = cls.get_translated_segment_vertex(sv, dist_max, tp0["vertex"], tp0["edge_idx"], tp1["vertex"], tp1["edge_idx"], True)
                            else:
                                if tp0["distance"] > dist_max - sep:
                                    tp0t, tp1t = cls.get_translated_segment_vertex(sv, dist_max * 2, tp2["vertex"], tp2["edge_idx"], tp3["vertex"], tp3["edge_idx"])
                                    dist_max = tp0t["distance"] / 2
                                else:
                                    dist_max = clamped_dist / 2
                                tfi0, tfi1 = cls.get_translated_segment_vertex(sv, dist_max, tp2["vertex"], tp2["edge_idx"], tp3["vertex"], tp3["edge_idx"])

                            fi0["edge_idx"], fi0["vertex"], fi0["join_idx"] = tfi0["edge_idx"], tfi0["vertex"], -1
                            fi1["edge_idx"], fi1["vertex"], fi1["join_idx"] = tfi1["edge_idx"], tfi1["vertex"], -1

                        # ------------- Calcul segments :

                        fold["segments_intersections"] = [None] * (fold["round_segments_rendered"] * 2 + 1)
                        vf = fold["intersections_corrected"][1]["vertex"] - fold["intersections_corrected"][0]["vertex"]
                        nf = hg.Normalize(hg.Vec2(-vf.y, vf.x))
                        flag_error = False
                        num_s = fold["round_segments_rendered"]
                        # La ligne de rainage est insérée dans les segments d'arrondis
                        fold["segments_intersections"][num_s] = [{"edge_idx": fi0["edge_idx"], "vertex": hg.Vec2(fi0["vertex"]), "join_idx": fi0["join_idx"]},
                                                                 {"edge_idx": fi1["edge_idx"], "vertex": hg.Vec2(fi1["vertex"]), "join_idx": fi1["join_idx"]}]

                        for i in range(num_s):

                            dist = (dist_max - sep) - (dist_max - sep) / fold["round_segments_rendered"] * i

                            p0 = fold["intersections_corrected"][0]["vertex"]
                            i1 = (fold["intersections_corrected"][0]["edge_idx"] + 1) % n
                            s0, edge_idx0 = get_segment_vertex(sv, dist, p0, i1, 1, nf, n)
                            if s0 == None:
                                flag_error = True
                                break

                            p0 = fold["intersections_corrected"][1]["vertex"]
                            i1 = fold["intersections_corrected"][1]["edge_idx"]
                            s1, edge_idx1 = get_segment_vertex(sv, dist, p0, i1, -1, nf, n)
                            if s1 == None:
                                flag_error = True
                                break

                            fold["segments_intersections"][i] = [{"edge_idx": (edge_idx0 - 1) % n, "vertex": s0, "join_idx": -1}, {"edge_idx": edge_idx1, "vertex": s1, "join_idx": -1}]

                            p0 = fold["intersections_corrected"][0]["vertex"]
                            i1 = fold["intersections_corrected"][0]["edge_idx"]
                            s0, edge_idx0 = get_segment_vertex(sv, dist, p0, i1, -1, nf * -1, n)
                            if s0 == None:
                                flag_error = True
                                break

                            p0 = fold["intersections_corrected"][1]["vertex"]
                            i1 = (fold["intersections_corrected"][1]["edge_idx"] + 1) % n
                            s1, edge_idx1 = get_segment_vertex(sv, dist, p0, i1, 1, nf * -1, n)
                            if s1 == None:
                                flag_error = True
                                break

                            fold["segments_intersections"][num_s * 2 - i] = [{"edge_idx": edge_idx0, "vertex": s0, "join_idx": -1}, {"edge_idx": (edge_idx1 - 1) % n, "vertex": s1, "join_idx": -1}]

                        if flag_error:
                            fold["segments_intersections"] = None

    @classmethod
    def update_folds_segments(cls, shape, flag_render_holes):
        for fold in shape["folds"]:
            fold["fold_angle"] = cls.folds_angle
            fold["round_radius"] = cls.round_radius
            fold["round_segments_count"] = cls.round_segments_count
            fold["segments_intersections"] = []
        cls.generates_shape(shape, flag_render_holes)

    # ================================== GUI =============================================

    @classmethod
    def gui(cls, resolution, main_panel_size):
        tp = cls.line_types[cls.line_type]
        cls.main_panel_size = main_panel_size
        wn = "Draw 2D"
        if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
            hg.ImGuiSetWindowPos(wn, hg.Vec2(0, 20 + main_panel_size.y), hg.ImGuiCond_Always)
            hg.ImGuiSetWindowSize(wn, hg.Vec2(main_panel_size.x, resolution.y - 20 - main_panel_size.y), hg.ImGuiCond_Always)
            hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

            dc.panel_part_separator("VIEW INFOS")

            hg.ImGuiText("Scale: %.2f" % cls.view2D.view_scale)

            if cls.get_current_ui_state_id() != cls.UI_STATE_DRAWING:

                dc.panel_part_separator("OBJECTS")

                shape = cls.get_current_shape()

                f, d = hg.ImGuiRadioButton("Shape", int(cls.line_type), int(Draw2D.LINE_TYPE_SHAPE))
                if f:
                    cls.set_line_type(Draw2D.LINE_TYPE_SHAPE)
                    cls.current_vertex = []
                    cls.point_hover = None
                hg.ImGuiSameLine()

                f, d = hg.ImGuiRadioButton("Fold", int(cls.line_type), int(Draw2D.LINE_TYPE_FOLD))
                if f:
                    cls.set_line_type(Draw2D.LINE_TYPE_FOLD)
                    cls.current_vertex = []
                    cls.point_hover = None
                hg.ImGuiSameLine()

                f, d = hg.ImGuiRadioButton("Split", int(cls.line_type), int(Draw2D.LINE_TYPE_SPLIT))
                if f:
                    cls.set_line_type(Draw2D.LINE_TYPE_SPLIT)
                    cls.current_vertex = []
                    cls.point_hover = None
                hg.ImGuiSameLine()

                f, d = hg.ImGuiRadioButton("Hole", int(cls.line_type), int(Draw2D.LINE_TYPE_HOLE))
                if f:
                    cls.set_line_type(Draw2D.LINE_TYPE_HOLE)
                    cls.current_vertex = []
                    cls.point_hover = None

                dc.panel_part_separator("TOOLS")

                for btn_tool_idx in range(len(cls.draw_shape_tools)):
                    btn_tool = cls.draw_shape_tools[btn_tool_idx]
                    if cls.draw_shape_tool_id == btn_tool["id"]:
                        f = hg.ImGuiImageButton(btn_tool["selected"], hg.Vec2(32, 32))
                    else:
                        if hg.ImGuiImageButton(btn_tool["idle"], hg.Vec2(32, 32)):
                            if cls.draw_shape_tool_id == Draw2D.DRAW_SHAPE_TOOL_SELECT:
                                cls.ctrl_mem_tool = Draw2D.DRAW_SHAPE_TOOL_SELECT
                            elif cls.draw_shape_tool_id == Draw2D.DRAW_SHAPE_TOOL_DIRECT_SELECT:
                                cls.ctrl_mem_tool = Draw2D.DRAW_SHAPE_TOOL_DIRECT_SELECT
                            cls.draw_shape_tool_id = btn_tool["id"]
                            cls.set_ui_state(btn_tool["state"])
                            cls.point_hover = None
                            cls.current_vertex = []
                            if cls.draw_shape_tool_id == Draw2D.DRAW_SHAPE_TOOL_SELECT:
                                cls.ctrl_mem_tool = Draw2D.DRAW_SHAPE_TOOL_DIRECT_SELECT
                            elif cls.draw_shape_tool_id == Draw2D.DRAW_SHAPE_TOOL_DIRECT_SELECT:
                                cls.ctrl_mem_tool = Draw2D.DRAW_SHAPE_TOOL_SELECT
                    if btn_tool_idx < len(cls.draw_shape_tools) - 1: hg.ImGuiSameLine()


                f, cls.flag_display_transform_box = hg.ImGuiCheckbox("Show transform box", cls.flag_display_transform_box)
                if tp == "Shape" or tp == "Hole":
                    if hg.ImGuiButton("Reset transform box"):
                        polygon = cls.get_current_polygon()
                        if polygon is not None:
                            cls.reset_polygon_edit_box(polygon)

                dc.panel_part_separator("DISPLAY SETTINGS")

                if cls.flag_debug:
                    f, cls.flag_render_holes = hg.ImGuiCheckbox("Render holes", cls.flag_render_holes)
                    f, cls.flag_show_triangles = hg.ImGuiCheckbox("Show triangles", cls.flag_show_triangles)

                f, cls.flag_show_main_vertices_idx = hg.ImGuiCheckbox("Show main vertices indices", cls.flag_show_main_vertices_idx)
                if f:
                    if cls.flag_show_main_vertices_idx: cls.flag_show_folded_vertices_idx = False

                if cls.flag_debug:
                    f, cls.flag_show_folded_vertices_idx = hg.ImGuiCheckbox("Show folded vertices indices", cls.flag_show_folded_vertices_idx)
                    if f:
                        if cls.flag_show_folded_vertices_idx: cls.flag_show_main_vertices_idx = False
                    f, cls.flag_show_holey_faces = hg.ImGuiCheckbox("Show holey faces", cls.flag_show_holey_faces)

                    if cls.flag_show_holey_faces:
                        f, cls.flag_display_holey_vertices_idx = hg.ImGuiCheckbox("Show holey vertices idx", cls.flag_display_holey_vertices_idx)

                hg.ImGuiText("Backdrops intensity")
                f, d = hg.ImGuiSliderFloat(" ##bdi", cls.view2D.backdrops_intensity, 0, 1)
                if f:
                    if d < 1e-6:
                        cls.flag_show_backdrops = False
                    else:
                        cls.flag_show_backdrops = True
                    cls.view2D.backdrops_intensity = d

                f, cls.flag_display_mouse_position = hg.ImGuiCheckbox("Display mouse position", cls.flag_display_mouse_position)

                dc.panel_part_separator("VERTEX")

                if len(cls.current_vertex) == 1:
                    vtx = cls.current_vertex[0]
                    f, d = hg.ImGuiInputVec2("Vertex position", vtx["vertex"], 2)
                    if f:
                        vtx["vertex"].x, vtx["vertex"].y = d.x, d.y

                if tp == "Fold":
                    f, cls.flag_snap_to_vertex = hg.ImGuiCheckbox("Snap to vertex", cls.flag_snap_to_vertex)
                    f, d = hg.ImGuiDragFloat("Join size", int(cls.join_size), 1)
                    if f:
                        cls.join_size = max(1, d)
                        if shape is not None:
                            if shape["closed"]: cls.generates_shape(shape, cls.flag_render_holes)

                dc.panel_part_separator("GRID")

                f, cls.flag_snap_to_grid = hg.ImGuiCheckbox("Snap to grid", cls.flag_snap_to_grid)
                hg.ImGuiSameLine()
                f, cls.flag_show_subdivision_grid = hg.ImGuiCheckbox("Show grid subdivisions", cls.flag_show_subdivision_grid)

                f, d = hg.ImGuiSliderFloat("Grid intensity", cls.view2D.grid_intensity, 0, 1)
                if f:
                    cls.view2D.grid_intensity = d
                f, d = hg.ImGuiInputFloat("Grid size (cm)", cls.view2D.grid_size, 0.01, 0.1, 2)
                if f:
                    cls.view2D.grid_size = max(0.01, d)
                f, d = hg.ImGuiInputInt("Grid subdivisions", cls.view2D.grid_subdivisions)
                if f:
                    cls.view2D.grid_subdivisions = max(1, d)

                if shape is not None:

                    dc.panel_part_separator("SHAPE SETTINGS")

                    f, d = hg.ImGuiDragFloat("Thickness", shape["thickness"], 0.001)
                    if f:
                        shape["thickness"] = max(0.001, d)
                    f, d = hg.ImGuiSliderFloat("Splits thickness", shape["split_thickness"], 1e-3, 5e-2, "%.5f")
                    if f:
                       shape["split_thickness"] = d
                       cls.generates_shape(shape, cls.flag_render_holes)

                    dc.panel_part_separator("FOLD SETTINGS")

                    f, cls.flag_global_folds_settings = hg.ImGuiCheckbox("Set all folds", cls.flag_global_folds_settings)

                    if cls.flag_global_folds_settings:
                        f, d = hg.ImGuiDragFloat("round radius", Draw2D.round_radius, 0.001, 0.001, 1000)
                        if f:
                            cls.round_radius = d
                            cls.update_folds_segments(shape, cls.flag_render_holes)

                        f, d = hg.ImGuiInputInt("round segments", cls.round_segments_count)
                        if f:
                            cls.round_segments_count = max(0, d)
                            cls.update_folds_segments(shape, cls.flag_render_holes)

                        f, d = hg.ImGuiDragFloat("Fold angle", cls.folds_angle / pi * 180, 0.1, -180, 180)
                        if f:
                            cls.folds_angle = d / 180 * pi
                            cls.update_folds_segments(shape, cls.flag_render_holes)

                        f, d = hg.ImGuiDragFloat("Max round angle", cls.round_max_angle, 0.01, 30, 89.99)
                        if f:
                            cls.round_max_angle = d
                            cls.update_folds_segments(shape, cls.flag_render_holes)

                    elif cls.current_fold >= 0:
                        fold = shape["folds"][cls.current_fold]
                        f, d = hg.ImGuiDragFloat("round radius", fold["round_radius"], 0.001, 0.001, 1000)
                        if f:
                            fold["round_radius"] = d
                            cls.generates_shape(shape, cls.flag_render_holes)

                        f, d = hg.ImGuiInputInt("round segments", fold["round_segments_count"])
                        if f:
                            fold["round_segments_count"] = max(0, d)
                            cls.generates_shape(shape, cls.flag_render_holes)

                        f, d = hg.ImGuiDragFloat("Fold angle", fold["fold_angle"] / pi * 180, 0.1, -180, 180)
                        if f:
                            fold["fold_angle"] = d / 180 * pi
                            cls.generates_shape(shape, cls.flag_render_holes)

            else:
                hg.ImGuiSpacing()
                hg.ImGuiSpacing()
                hg.ImGuiTextColored(hg.Color(0.9, 0.6, 0.5), "Drawing: " + tp)
                hg.ImGuiSpacing()
                hg.ImGuiSpacing()
                c = hg.Color(0.9, 0.9, 0.7, 1)
                if tp == "Shape":
                    hg.ImGuiTextColored(c, "Press ENTER or clic on last vertex to exit drawing mode.")
                    hg.ImGuiTextColored(c, "Clic on first vertex to close the shape.")
                    hg.ImGuiTextColored(c, "Press Left SHIFT to constrain orthogonal tracing.")
                    hg.ImGuiTextColored(c, "Press SUPPR to remove last vertex.")
                elif tp == "Fold":
                    hg.ImGuiTextColored(c, "Press ENTER or clic on first vertex to cancel Fold.")
                elif tp == "Split":
                    hg.ImGuiTextColored(c, "Press ENTER or clic on first vertex to cancel Split.")
                elif tp == "Hole":
                    hg.ImGuiTextColored(c, "Press ENTER or clic on first vertex to cancel Hole.")

            hg.ImGuiEnd()

    # ================================== Object type =============================================

    @classmethod
    def set_line_type(cls, line_type):
        cls.line_type = line_type
        if line_type == Draw2D.LINE_TYPE_SHAPE:
            cls.current_fold = -1
            cls.current_split = -1
            cls.current_hole = -1
        elif line_type == Draw2D.LINE_TYPE_FOLD:
            cls.current_split = -1
            cls.current_hole = -1
        elif line_type == Draw2D.LINE_TYPE_SPLIT:
            cls.current_fold = -1
            cls.current_hole = -1
        elif line_type == Draw2D.LINE_TYPE_HOLE:
            cls.current_fold = -1
            cls.current_split = -1

    # ================================================== Select tool : Selection functions ================================

    @classmethod
    def mouse_shape_selection(cls, mouse, resolution):
        ms = hg.Vec2(mouse.X(), mouse.Y())
        m = cls.get_point_plane(ms, resolution, False, False)
        cls.shape_hover, edge_idx, dist = cls.point_edge_proxymity(m, cls.shapes, resolution)
        if mouse.Down(hg.MB_0):
            if cls.shape_hover == cls.current_shape:
                return True
            cls.undo_record()
            cls.clear_selection()
            if cls.shape_hover < 0:
                cls.current_shape = -1
                return False
            else:
                cls.current_shape = cls.shape_hover
                return True
        return False

    @classmethod
    def mouse_fold_selection(cls, mouse, resolution):
        if 0 <= cls.current_shape < len(cls.shapes):
            shape = cls.shapes[cls.current_shape]
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            near_folds = []
            for fold_idx in range(len(shape["folds"])):
                fold = shape["folds"][fold_idx]
                d = pol.point_edge_distance(m, fold["vertices"][0], fold["vertices"][1])
                if d < cls.edge_hover_distance / resolution.y * cls.view2D.view_scale:
                    near_folds.append({"dist": d, "fold_idx": fold_idx})
            if len(near_folds) > 0:
                near_folds.sort(key=lambda p: p["dist"])
                cls.fold_hover = near_folds[0]["fold_idx"]
            else:
                cls.fold_hover = -1
            if mouse.Down(hg.MB_0):
                if cls.fold_hover < 0:
                    cls.current_fold = -1
                    return False
                elif cls.current_fold == cls.fold_hover:
                    return True
                else:
                    cls.current_vertex = []
                    cls.undo_record()
                    cls.current_fold = cls.fold_hover
                    return True
        return False

    @classmethod
    def mouse_split_selection(cls, mouse, resolution):
        if 0 <= cls.current_shape < len(cls.shapes):
            shape = cls.shapes[cls.current_shape]
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            near_splits = []
            for split_idx in range(len(shape["splits"])):
                split = shape["splits"][split_idx]
                d = pol.point_edge_distance(m, split["vertices"][0], split["vertices"][1])
                if d < cls.edge_hover_distance / resolution.y * cls.view2D.view_scale:
                    near_splits.append({"dist": d, "split_idx": split_idx})
            if len(near_splits) > 0:
                near_splits.sort(key=lambda p: p["dist"])
                cls.split_hover = near_splits[0]["split_idx"]
            else:
                cls.split_hover = -1
            if mouse.Down(hg.MB_0):
                if cls.split_hover < 0:
                    cls.current_split = -1
                    return False
                elif cls.current_split == cls.split_hover:
                    return True
                else:
                    cls.current_vertex = []
                    cls.undo_record()
                    cls.current_split = cls.split_hover
                    return True
        return False

    @classmethod
    def mouse_hole_selection(cls, mouse, resolution):
        if 0 <= cls.current_shape < len(cls.shapes):
            shape = cls.shapes[cls.current_shape]
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            cls.hole_hover, edge_idx, dist = cls.point_edge_proxymity(m, shape["holes"], resolution)
            if mouse.Down(hg.MB_0):
                if cls.hole_hover < 0:
                    cls.current_hole = -1
                    return False
                elif cls.current_hole == cls.hole_hover:
                    return True
                else:
                    cls.current_vertex = []
                    cls.undo_record()
                    cls.current_hole = cls.hole_hover
                    return True
        return False

    # ================================================== Select tool : Move functions ================================

    @classmethod
    def move_shape(cls, shape, m):
        for v in shape["vertices"]:
            v.x = v.x + m.x
            v.y = v.y + m.y
        for fold in shape["folds"]:
            cls.move_fold(fold, m)
        for split in shape["splits"]:
            cls.move_split(split, m)
        for hole in shape["holes"]:
            cls.move_hole(hole, m)

    @classmethod
    def move_fold(cls, fold, m):
        fold["vertices"][0] = fold["vertices"][0] + m
        fold["vertices"][1] = fold["vertices"][1] + m

    @classmethod
    def move_split(cls, split, m):
        split["vertices"][0] = split["vertices"][0] + m
        split["vertices"][1] = split["vertices"][1] + m

    @classmethod
    def move_hole(cls, hole, m):
        for i in range(len(hole["vertices"])):
            hole["vertices"][i] = hole["vertices"][i] + m

    @classmethod
    def reset_move_vector(cls):
        cls.move_vector = hg.Vec2(0, 0)
        cls.move_vector_snap = hg.Vec2(0, 0)
        cls.flag_modified_move_vector = False

    @classmethod  # /!\ cls.move_vector doit être mis à 0 au départ du déplacement
    def get_delta_plane(cls, ds: hg.Vec2, resolution: hg.Vec2, snap_to_grid=True):
        m = ds / resolution.y * cls.view2D.view_scale
        if snap_to_grid:
            move_vector_prec = hg.Vec2(cls.move_vector.x, cls.move_vector.y)
            cls.move_vector += m
            q = cls.view2D.grid_size / cls.view2D.grid_subdivisions
            move_vector_prec.x = int(move_vector_prec.x / q) * q
            move_vector_prec.y = int(move_vector_prec.y / q) * q
            m.x = int(cls.move_vector.x / q) * q - move_vector_prec.x
            m.y = int(cls.move_vector.y / q) * q - move_vector_prec.y
        if not cls.flag_modified_move_vector and hg.Len(m) > 1e-6:
            cls.flag_modified_move_vector = True
            cls.undo_record()
        cls.move_vector_snap += m
        return m

    @classmethod
    def mouse_move_shape(cls, mouse, resolution):
        if cls.current_shape >= 0 and mouse.Down(hg.MB_0):
            ms = hg.Vec2(mouse.DtX(), mouse.DtY())
            m = cls.get_delta_plane(ms, resolution, cls.flag_snap_to_grid)
            shape = cls.get_current_shape()
            cls.move_shape(shape, m)
            cls.generates_shape(shape, cls.flag_render_holes)
        else:
            shape = cls.get_current_shape()
            if shape is not None:
                cls.update_polygon_edit_box(shape)
            cls.set_ui_state(Draw2D.UI_STATE_SELECT)

    @classmethod
    def mouse_move_fold(cls, mouse, resolution):
        if cls.current_fold >= 0 and mouse.Down(hg.MB_0):
            ms = hg.Vec2(mouse.DtX(), mouse.DtY())
            m = cls.get_delta_plane(ms, resolution, cls.flag_snap_to_grid)
            shape = cls.shapes[cls.current_shape]
            fold = shape["folds"][cls.current_fold]
            cls.move_fold(fold, m)
            cls.generates_shape(shape, cls.flag_render_holes)
        else:
            cls.set_ui_state(Draw2D.UI_STATE_SELECT)

    @classmethod
    def mouse_move_split(cls, mouse, resolution):
        if cls.current_split >= 0 and mouse.Down(hg.MB_0):
            ms = hg.Vec2(mouse.DtX(), mouse.DtY())
            m = cls.get_delta_plane(ms, resolution, cls.flag_snap_to_grid)
            shape = cls.shapes[cls.current_shape]
            split = shape["splits"][cls.current_split]
            cls.move_split(split, m)
            cls.generates_shape(shape, cls.flag_render_holes)
        else:
            cls.set_ui_state(Draw2D.UI_STATE_SELECT)

    @classmethod
    def mouse_move_hole(cls, mouse, resolution):
        if cls.current_hole >= 0 and mouse.Down(hg.MB_0):
            ms = hg.Vec2(mouse.DtX(), mouse.DtY())
            m = cls.get_delta_plane(ms, resolution, cls.flag_snap_to_grid)
            shape = cls.shapes[cls.current_shape]
            hole = shape["holes"][cls.current_hole]
            cls.move_hole(hole, m)
            cls.generates_shape(shape, cls.flag_render_holes)
        else:
            hole = cls.get_current_hole()
            if hole is not None:
                cls.update_polygon_edit_box(cls.get_current_hole())
            cls.set_ui_state(Draw2D.UI_STATE_SELECT)

    # ================================================== Direct edit function ================================

    @classmethod
    def vertex_hit(cls, p, ms, shape, fold, split, hole, vi, resolution):
        ps = cls.view2D.get_point_screen(p, resolution)
        d = hg.Len(ms - ps)
        if d <= cls.points_size / 2:
            select_point = {"shape": shape, "fold": fold, "split": split, "hole": hole, "idx": vi, "vertex": p, "circle": False}
            if split is not None:
                select_point["circle"] = True
            cls.point_hover = select_point
            return True
        return False

    @classmethod
    def mouse_vertex_selection(cls, mouse, keyboard, resolution):
        cls.point_hover = None
        if mouse.Pressed(hg.MB_0):
            if not keyboard.Down(cls.key_multiple_vertices_selection):
                cls.current_vertex = []
        ms = hg.Vec2(mouse.X(), mouse.Y())
        if 0 <= cls.current_shape < len(cls.shapes):
            shape = cls.shapes[cls.current_shape]
            sel_funcs = [cls.select_shape_vtx, cls.select_fold_vtx, cls.select_split_vtx, cls.select_hole_vtx]
            f_id = 0
            if cls.line_type == Draw2D.LINE_TYPE_SHAPE:
                f_id = 0
            elif cls.line_type == Draw2D.LINE_TYPE_FOLD:
                f_id = 1
            elif cls.line_type == Draw2D.LINE_TYPE_SPLIT:
                f_id = 2
            elif cls.line_type == Draw2D.LINE_TYPE_HOLE:
                f_id = 3
            n = len(sel_funcs)
            for i in range(n):
                if sel_funcs[(f_id + i) % n](mouse, resolution, shape, ms):
                    cls.mouse_pos_prec = None
                    cls.undo_record()
                    return True
            # Move vertices if multiple selection:
            if mouse.Down(hg.MB_0) and keyboard.Down(cls.key_multiple_vertices_selection):
                if len(cls.current_vertex) > 0:
                    cls.set_ui_state(cls.UI_STATE_MOVING_VERTEX)
                    cls.mouse_pos_prec = None
                    cls.undo_record()
                    return True
        return False

    @classmethod
    def add_vertex_to_selection(cls, select_point):
        sp_s = False
        if select_point["fold"] is None and select_point["split"] is None and select_point["hole"] is None:
            sp_s = True
        for vtx_i in range(len(cls.current_vertex)):
            vtx = cls.current_vertex[vtx_i]
            shape = vtx["shape"]
            fold = vtx["fold"]
            split = vtx["split"]
            hole = vtx["hole"]
            vtx_s = False
            if fold is None and split is None and hole is None:
                vtx_s = True

            if shape is not None and select_point["shape"] == shape:
                if not (sp_s and vtx_s):
                    if fold is not None:
                        if select_point["fold"] == fold and select_point["idx"] == vtx["idx"]:
                            cls.current_vertex.pop(vtx_i)
                            return
                    elif split is not None:
                        if select_point["split"] == split and select_point["idx"] == vtx["idx"]:
                            cls.current_vertex.pop(vtx_i)
                            return
                    elif hole is not None:
                        if select_point["hole"] == hole and select_point["idx"] == vtx["idx"]:
                            cls.current_vertex.pop(vtx_i)
                            return

                elif sp_s and vtx_s:
                    if select_point["idx"] == vtx["idx"]:
                        cls.current_vertex.pop(vtx_i)
                        return
        cls.current_vertex.append(select_point)

    @classmethod
    def select_shape_vtx(cls, mouse, resolution, shape, ms):
        for v_idx in range(len(shape["vertices"])):
            if cls.vertex_hit(shape["vertices"][v_idx], ms, shape, None, None, None, v_idx, resolution):
                if mouse.Down(hg.MB_0):
                    cls.set_line_type(Draw2D.LINE_TYPE_SHAPE)
                    cls.add_vertex_to_selection(cls.point_hover)
                    if len(cls.current_vertex) > 0:
                        cls.set_ui_state(cls.UI_STATE_MOVING_VERTEX)
                    return True

    @classmethod
    def select_fold_vtx(cls, mouse, resolution, shape, ms):
        for fold_idx in range(len(shape["folds"])):
            fold = shape["folds"][fold_idx]
            for i in range(2):
                if cls.vertex_hit(fold["vertices"][i], ms, shape, fold, None, None, i, resolution):
                    if mouse.Down(hg.MB_0):
                        cls.set_line_type(Draw2D.LINE_TYPE_FOLD)
                        cls.add_vertex_to_selection(cls.point_hover)
                        cls.current_fold = fold_idx
                        if len(cls.current_vertex) > 0:
                            cls.set_ui_state(cls.UI_STATE_MOVING_VERTEX)
                        return True

    @classmethod
    def select_split_vtx(cls, mouse, resolution, shape, ms):
        for split_idx in range(len(shape["splits"])):
            split = shape["splits"][split_idx]
            for i in range(2):
                if cls.vertex_hit(split["vertices"][i], ms, shape, None, split, None, i, resolution):
                    if mouse.Down(hg.MB_0):
                        cls.set_line_type(Draw2D.LINE_TYPE_SPLIT)
                        cls.add_vertex_to_selection(cls.point_hover)
                        cls.current_split = split_idx
                        if len(cls.current_vertex) > 0:
                            cls.set_ui_state(cls.UI_STATE_MOVING_VERTEX)
                        return True

    @classmethod
    def select_hole_vtx(cls, mouse, resolution, shape, ms):
        for hole_idx in range(len(shape["holes"])):
            hole = shape["holes"][hole_idx]
            for i in range(len(hole["vertices"])):
                if cls.vertex_hit(hole["vertices"][i], ms, shape, None, None, hole, i, resolution):
                    if mouse.Down(hg.MB_0):
                        cls.set_line_type(Draw2D.LINE_TYPE_HOLE)
                        cls.add_vertex_to_selection(cls.point_hover)
                        cls.current_hole = hole_idx
                        if len(cls.current_vertex) > 0:
                            cls.set_ui_state(cls.UI_STATE_MOVING_VERTEX)
                        return True

    @classmethod
    def mouse_move_vertex(cls, mouse, resolution):
        if mouse.Down(hg.MB_0):
            ms = hg.Vec2(mouse.X(), mouse.Y())

            if len(cls.current_vertex) == 1 and (cls.current_vertex[0]["fold"] is not None or cls.current_vertex[0]["split"] is not None):
                m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, cls.flag_snap_to_vertex)
            else:
                m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)

            if cls.mouse_pos_prec is None:
                cls.mouse_pos_prec = m
            md = m - cls.mouse_pos_prec

            if hg.Len(md) > 1e-6:
                cls.mouse_pos_prec = m

                for vtx in cls.current_vertex:
                    shape = vtx["shape"]
                    fold = vtx["fold"]
                    split = vtx["split"]
                    hole = vtx["hole"]

                    # ------- Move fold vertex:

                    if fold is not None:
                        p = fold["vertices"][vtx["idx"]]

                    # ------- Move split vertex:

                    elif split is not None:
                        p = split["vertices"][vtx["idx"]]

                    # ------- Move hole vertex:
                    elif hole is not None:
                        p = hole["vertices"][vtx["idx"]]

                    # ------------ Move shape vertex:
                    else:
                        p = shape["vertices"][vtx["idx"]]

                    p.x += md.x
                    p.y += md.y

                cls.generates_shape(shape, cls.flag_render_holes)

        else:
            polygons_to_reset_eb = []
            for vtx in cls.current_vertex:
                shape = vtx["shape"]
                hole = vtx["hole"]
                if hole is not None:
                    if hole not in polygons_to_reset_eb:
                        polygons_to_reset_eb.append(hole)
                elif shape is not None:
                    if shape not in polygons_to_reset_eb:
                        polygons_to_reset_eb.append(shape)

            for polygon in polygons_to_reset_eb:
                cls.reset_polygon_edit_box(polygon)

            cls.set_ui_state(Draw2D.UI_STATE_DIRECT_SELECT)

    @classmethod
    def point_edge_proxymity(cls, p, polygons, resolution):
        # returns : polygon_idx, edge_idx, distance
        near_polygons = []
        for polygon_idx in range(len(polygons)):
            polygon = polygons[polygon_idx]
            n = len(polygon["vertices"])
            near_edges = []
            for v_idx in range(n):
                d = pol.point_edge_distance(p, polygon["vertices"][v_idx], polygon["vertices"][(v_idx + 1) % n])
                if d < cls.edge_hover_distance / resolution.y * cls.view2D.view_scale:
                    near_edges.append({"dist": d, "edge_idx": v_idx})
            if len(near_edges) > 0:
                near_edges.sort(key=lambda p: p["dist"])
                near_polygons.append({"dist": near_edges[0]["dist"], "edge_idx": near_edges[0]["edge_idx"], "polygon_idx": polygon_idx})
        if len(near_polygons) > 0:
            near_polygons.sort(key=lambda p: p["dist"])
            return near_polygons[0]["polygon_idx"], near_polygons[0]["edge_idx"], near_polygons[0]["dist"]
        else:
            return -1, -1, -1

    @classmethod
    def display_mouse_position(cls, mouse, resolution):
        ms = hg.Vec2(mouse.X(), mouse.Y())
        m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)
        cls.texts.push({"text": "mx: %.2f" % m.x, "pos": hg.Vec2(ms.x + 10, ms.y + 25) / resolution, "font": cls.texts.font_small})
        cls.texts.push({"text": "my: %.2f" % m.y, "pos": hg.Vec2(ms.x + 10, ms.y + 10) / resolution, "font": cls.texts.font_small})

    # ================================================== Drawing functions ================================
    @classmethod
    def mouse_draw(cls, mouse, keyboard, resolution):

        tp = cls.line_types[cls.line_type]

        ms = hg.Vec2(mouse.X(), mouse.Y())

        shape = cls.get_current_shape()

        if tp == "Shape":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)
            return cls.mouse_draw_shape(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Fold":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, cls.flag_snap_to_vertex)
            return cls.mouse_draw_fold(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Split":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, cls.flag_snap_to_vertex)
            return cls.mouse_draw_split(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Hole":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)
            return cls.mouse_draw_hole(shape, m, ms, mouse, keyboard, resolution)
        return False

    @classmethod
    def mouse_draw_update(cls, mouse, keyboard, resolution):

        tp = cls.line_types[cls.line_type]
        ms = hg.Vec2(mouse.X(), mouse.Y())

        shape = cls.get_current_shape()

        if tp == "Shape":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)
            cls.mouse_draw_shape_update(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Fold":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, cls.flag_snap_to_vertex)
            cls.mouse_draw_fold_update(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Split":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, cls.flag_snap_to_vertex)
            cls.mouse_draw_split_update(shape, m, ms, mouse, keyboard, resolution)
        elif tp == "Hole":
            m = cls.get_point_plane(ms, resolution, cls.flag_snap_to_grid, False)
            cls.mouse_draw_hole_update(shape, m, ms, mouse, keyboard, resolution)

    @classmethod
    def mouse_draw_shape(cls, shape, m, ms, mouse, keyboard, resolution):
        cls.point_hover = None
        if shape is not None and not shape["closed"]:
            for v_idx in range(len(shape["vertices"])):
                if cls.vertex_hit(shape["vertices"][v_idx], ms, shape, None, None, None, v_idx, resolution):
                    if v_idx == 0 or v_idx == len(shape["vertices"]) - 1:
                        if mouse.Down(hg.MB_0):
                            if v_idx == 0:
                                pol.reverse_table(shape["vertices"])
                            cls.undo_record()
                            shape = cls.get_current_shape()
                            shape["vertices"].append(hg.Vec2(shape["vertices"][-1]))
                            cls.set_ui_state(Draw2D.UI_STATE_DRAWING)
                            cls.point_hover = None
                            return True
                        else:
                            cls.display_mouse_message(mouse, resolution, "Continue shape")
                            return False

        if mouse.Pressed(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_DRAWING)
            cls.undo_record()
            cls.current_shape = len(cls.shapes)
            cls.shapes.append(cls.new_2d_shape(m))
            return True
        return False

    @classmethod
    def mouse_draw_shape_update(cls, shape, m, ms, mouse, keyboard, resolution):
        cls.current_shape = cls.mouse_draw_polygon_update(shape, "shape", cls.shapes, cls.current_shape, m, ms, mouse, keyboard, resolution)

    @classmethod
    def mouse_draw_fold(cls, shape, m, ms, mouse, keyboard, resolution):
        if shape is not None:
            if mouse.Pressed(hg.MB_0):
                cls.set_ui_state(Draw2D.UI_STATE_DRAWING)
                cls.current_fold = len(shape["folds"])
                cls.undo_record()
                shape = cls.get_current_shape()
                shape["folds"].append(cls.new_2d_fold(m))
                return True
        return False

    @classmethod
    def mouse_draw_fold_update(cls, shape, m, ms, mouse, keyboard, resolution):
        if shape is not None:
            fold = shape["folds"][cls.current_fold]
            fold["vertices"][-1] = m
            cls.constrain_vertex_to_ortho(keyboard, fold["vertices"][0], m)

            # --- Check geometric structure

            # ---
            cls.generates_shape(shape, cls.flag_render_holes)
            if keyboard.Pressed(hg.K_Enter) or keyboard.Pressed(hg.K_Return) or keyboard.Pressed(hg.K_Escape):
                cls.escape_drawing(shape)

            if mouse.Pressed(hg.MB_0):
                d = hg.Len(ms - cls.view2D.get_point_screen(fold["vertices"][0], resolution))
                if d <= cls.points_size:
                    shape["folds"].pop(cls.current_fold)
                    cls.current_fold = -1
                cls.set_ui_state(Draw2D.UI_STATE_WAIT_DRAW_IDLE)

    @classmethod
    def mouse_draw_split(cls, shape, m, ms, mouse, keyboard, resolution):

        if shape is not None:
            if mouse.Pressed(hg.MB_0):
                cls.set_ui_state(Draw2D.UI_STATE_DRAWING)
                cls.current_split = len(shape["splits"])
                cls.undo_record()
                shape = cls.get_current_shape()
                shape["splits"].append(cls.new_2d_split(m))
                return True
        return False

    @classmethod
    def mouse_draw_split_update(cls, shape, m, ms, mouse, keyboard, resolution):

        if shape is not None:
            split = shape["splits"][cls.current_split]
            split["vertices"][-1] = m
            cls.constrain_vertex_to_ortho(keyboard, split["vertices"][0], m)

            # --- Check geometric structure

            # ---
            cls.generates_shape(shape, cls.flag_render_holes)
            if keyboard.Pressed(hg.K_Enter) or keyboard.Pressed(hg.K_Return) or keyboard.Pressed(hg.K_Escape):
                cls.escape_drawing(shape)

            if mouse.Pressed(hg.MB_0):
                d = hg.Len(ms - cls.view2D.get_point_screen(split["vertices"][0], resolution))
                if d <= cls.split_points_size:
                    shape["splits"].pop(cls.current_split)
                    cls.current_split = -1
                cls.set_ui_state(Draw2D.UI_STATE_WAIT_DRAW_IDLE)

    @classmethod
    def mouse_draw_hole(cls, shape, m, ms, mouse, keyboard, resolution):

        if shape is not None:
            if mouse.Pressed(hg.MB_0):
                cls.set_ui_state(Draw2D.UI_STATE_DRAWING)
                cls.current_hole = len(shape["holes"])
                cls.undo_record()
                shape = cls.get_current_shape()
                shape["holes"].append(cls.new_2d_hole(m))
                return True
        return False

    @classmethod
    def mouse_draw_hole_update(cls, shape, m, ms, mouse, keyboard, resolution):
        cls.current_hole = cls.mouse_draw_polygon_update(shape, "hole", shape["holes"], cls.current_hole, m, ms, mouse, keyboard, resolution)
        cls.generates_shape(shape, cls.flag_render_holes)

    @classmethod
    def mouse_draw_polygon_update(cls, shape, object_name, polygons, current_polygon, m, ms, mouse, keyboard, resolution):
        polygon =cls.get_current_polygon()
        if polygon is None:
            cls.set_ui_state(Draw2D.UI_STATE_DRAW_IDLE)
            return -1
        v = polygon["vertices"]
        n = len(v)
        v[-1] = m

        cls.constrain_vertex_to_ortho(keyboard, v[-2], m)

        # --- Check geometric structure
        polygon["edit_error"] = None

        vertex_overlay = False
        edge_overlay = False
        first_overlay = False
        last_overlay = False
        edge_crossing = False

        p_first = cls.view2D.get_point_screen(v[0], resolution)
        p_last = cls.view2D.get_point_screen(v[-2], resolution)
        d_first = hg.Len(ms - p_first)
        d_last = hg.Len(ms - p_last)
        if d_first <= cls.points_size: first_overlay = True
        if d_last <= cls.points_size: last_overlay = True
        if not last_overlay:
            cls.flag_new_vertex = False

        # Vertex - vertices distance:

        if n > 3:
            for v_idx in range(1, n - 2):
                d = hg.Len(ms - cls.view2D.get_point_screen(v[v_idx], resolution))
                if d <= cls.points_size:
                    polygon["edit_error"] = v[v_idx]
                    vertex_overlay = True
                    break

        # Edge distance:
        if n > 2:
            for v_idx in range(n - 2):
                d_edge = pol.point_edge_distance(m, v[v_idx], v[(v_idx + 1)])
                if d_edge < cls.edge_hover_distance / resolution.y * cls.view2D.view_scale:
                    edge_overlay = True
                    polygon["edit_error"] = m

        # Edge crossing:
        p = v[-2]
        if hg.Len(m - p) > 1e-5 and n > 3:
            for v_idx in range(n - 3):
                pi, t1, t2 = pol.vectors2D_intersection(v[v_idx], v[v_idx + 1], p, m)
                if pi is not None:
                    polygon["edit_error"] = pi
                    edge_crossing = True
                    break

        # -------------------

        if keyboard.Pressed(hg.K_Enter) or keyboard.Pressed(hg.K_Return) or keyboard.Pressed(hg.K_Escape) or keyboard.Pressed(hg.K_Suppr):
            cls.escape_drawing(shape)

        """
        if keyboard.Pressed(hg.K_Suppr):
            if n == 2:
                polygons.pop(current_polygon)
                current_polygon = -1
                cls.set_ui_state(Draw2D.UI_STATE_DRAW_IDLE)
            else:
                v.pop(-2)
        """
        # -------- Check geometric validity:
        # /!\ Tests order is related to checks order (look at parameter in shape["edit_error"])
        if edge_crossing:
            cls.texts.push({"text": "Edge crossing !", "pos": hg.Vec2(ms.x + 10, ms.y - 25) / resolution, "font": cls.texts.font_small, "color": cls.alert_color})
        elif edge_overlay and not (first_overlay or last_overlay):
            cls.texts.push({"text": "Edge overlay !", "pos": hg.Vec2(ms.x + 10, ms.y - 25) / resolution, "font": cls.texts.font_small, "color": cls.alert_color})
        elif vertex_overlay and not (first_overlay or last_overlay):
            cls.texts.push({"text": "Vertex overlay !", "pos": hg.Vec2(ms.x + 10, ms.y - 25) / resolution, "font": cls.texts.font_small, "color": cls.alert_color})
        # --------
        else:
            if mouse.Pressed(hg.MB_0):
                v = polygon["vertices"]
                if first_overlay:
                    if n <= 3:
                        polygons.pop(current_polygon)
                        current_polygon = -1
                    else:
                        v.pop(-1)
                        polygon["closed"] = True
                        pol.make_polygon_cw(v)  # polygons must be clockwise
                        cls.generates_shape(shape, cls.flag_render_holes)
                        cls.reset_polygon_edit_box(polygon)
                    cls.set_ui_state(Draw2D.UI_STATE_WAIT_DRAW_IDLE)

                elif last_overlay:
                    v.pop(-1)
                    cls.reset_polygon_edit_box(polygon)
                    cls.set_ui_state(Draw2D.UI_STATE_WAIT_DRAW_IDLE)
                else:
                    cls.reset_polygon_edit_box(polygon)
                    cls.undo_record()
                    v.append(m)
                    cls.flag_new_vertex = True  # To avoid displaying "Stop drawing" at every new vertex.

                if current_polygon > -1 and "edit_error" in polygon:
                    del (polygon["edit_error"])

            else:
                if first_overlay:
                    if n <= 3:
                        txt = "Clear " + object_name
                    else:
                        txt = "Close " + object_name
                    cls.texts.push({"text": txt, "pos": hg.Vec2(ms.x + 10, ms.y - 25) / resolution, "font": cls.texts.font_small})
                    polygon["edit_error"] = None
                elif last_overlay and not cls.flag_new_vertex:
                    cls.texts.push({"text": "Stop drawing", "pos": hg.Vec2(ms.x + 10, ms.y - 25) / resolution, "font": cls.texts.font_small})
                    polygon["edit_error"] = None
        return current_polygon

    # ================================================== Add / Remove vertex tools ================================

    @classmethod
    def mouse_add_vertex_shape(cls, mouse, keyboard, resolution):
        cls.shape_hover = -1
        shape = cls.get_current_shape()
        if shape is not None:
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            shape_idx, edge_idx, dist = cls.point_edge_proxymity(m, cls.shapes, resolution)
            if shape_idx < 0 or shape_idx != cls.current_shape:
                return False
            else:
                cls.shape_hover = shape_idx
                if mouse.Pressed(hg.MB_0):
                    v0 = shape["vertices"][edge_idx]
                    v1 = shape["vertices"][(edge_idx + 1) % len(shape["vertices"])]
                    d0 = hg.Len(ms - cls.view2D.get_point_screen(v0, resolution))
                    d1 = hg.Len(ms - cls.view2D.get_point_screen(v1, resolution))
                    if d0 > cls.points_size and d1 > cls.points_size:
                        cls.undo_record()
                        shape = cls.get_current_shape()
                        shape["vertices"].insert(edge_idx + 1, m)
                        cls.generates_shape(shape, cls.flag_render_holes)
                        cls.reset_polygon_edit_box(shape)
                        cls.current_vertex = []
                        cls.point_hover = None
                        cls.set_ui_state(Draw2D.UI_STATE_WAIT_ADD_VERTEX_SHAPE)
                        return True
        return False

    @classmethod
    def mouse_remove_vertex_shape(cls, mouse, keyboard, resolution):
        cls.point_hover = None
        shape = cls.get_current_shape()
        if shape is not None:
            ms = hg.Vec2(mouse.X(), mouse.Y())
            for v_idx in range(len(shape["vertices"])):
                if cls.vertex_hit(shape["vertices"][v_idx], ms, shape, None, None, None, v_idx, resolution):
                    cls.shape_hover = -1
                    if mouse.Pressed(hg.MB_0):
                        cls.undo_record()
                        shape = cls.get_current_shape()
                        if len(shape["vertices"]) <= 3:
                            cls.shapes.pop(cls.current_shape)
                            cls.clear_selection()
                        else:
                            shape["vertices"].pop(v_idx)
                            cls.generates_shape(shape, cls.flag_render_holes)
                            cls.reset_polygon_edit_box(shape)
                            cls.current_vertex = []
                            cls.point_hover = None
                            cls.set_ui_state(Draw2D.UI_STATE_WAIT_REMOVE_VERTEX_SHAPE)
                    return True
        return False

    @classmethod
    def mouse_add_vertex_hole(cls, mouse, keyboard, resolution):
        cls.hole_hover = -1
        shape = cls.get_current_shape()
        if shape is not None:
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            cls.hole_hover, edge_idx, dist = cls.point_edge_proxymity(m, shape["holes"], resolution)
            if cls.hole_hover < 0:
                return False
            else:
                if mouse.Pressed(hg.MB_0):
                    cls.current_hole = cls.hole_hover
                    hole = cls.get_current_hole()
                    v0 = hole["vertices"][edge_idx]
                    v1 = hole["vertices"][(edge_idx + 1) % len(hole["vertices"])]
                    d0 = hg.Len(ms - cls.view2D.get_point_screen(v0, resolution))
                    d1 = hg.Len(ms - cls.view2D.get_point_screen(v1, resolution))
                    if d0 > cls.points_size and d1 > cls.points_size:
                        cls.undo_record()
                        shape = cls.get_current_shape()
                        hole = cls.get_current_hole()
                        hole["vertices"].insert(edge_idx + 1, m)
                        cls.generates_shape(shape, cls.flag_render_holes)
                        cls.reset_polygon_edit_box(hole)
                        cls.current_vertex = []
                        cls.point_hover = None
                        cls.set_ui_state(Draw2D.UI_STATE_WAIT_ADD_VERTEX_SHAPE)
                        return True
        return False

    @classmethod
    def mouse_remove_vertex_hole(cls, mouse, keyboard, resolution):
        cls.point_hover = None
        shape = cls.get_current_shape()
        if shape is not None:
            ms = hg.Vec2(mouse.X(), mouse.Y())
            m = cls.get_point_plane(ms, resolution, False, False)
            cls.hole_hover, edge_idx, dist = cls.point_edge_proxymity(m, shape["holes"], resolution)
            if cls.hole_hover < 0:
                return False
            else:
                hole = shape["holes"][cls.hole_hover]
                for v_idx in range(len(hole["vertices"])):
                    if cls.vertex_hit(hole["vertices"][v_idx], ms, shape, None, None, hole, v_idx, resolution):
                        hh = cls.hole_hover
                        cls.hole_hover = -1
                        if mouse.Pressed(hg.MB_0):
                            cls.current_hole = hh
                            cls.undo_record()
                            shape = cls.get_current_shape()
                            hole = cls.get_current_hole()
                            if len(hole["vertices"]) <= 3:
                                shape["holes"].pop(cls.current_hole)
                                cls.current_hole = -1
                            else:
                                hole["vertices"].pop(v_idx)
                                cls.generates_shape(shape, cls.flag_render_holes)
                                cls.reset_polygon_edit_box(hole)
                                cls.current_vertex = []
                                cls.point_hover = None
                                cls.set_ui_state(Draw2D.UI_STATE_WAIT_REMOVE_VERTEX_SHAPE)
                        return True
        return False

    # ================================================== Edit box ================================
    @classmethod
    def get_bounds(cls, vertices):
        v0 = vertices[0]
        dmin = hg.Vec2(v0.x, v0.y)
        dmax = hg.Vec2(v0.x, v0.y)
        for vtx in vertices:
            dmin.x = min(dmin.x, vtx.x)
            dmin.y = min(dmin.y, vtx.y)
            dmax.x = max(dmax.x, vtx.x)
            dmax.y = max(dmax.y, vtx.y)
        return dmin, dmax, dmax - dmin

    @classmethod
    def reset_polygon_edit_box(cls, polygon):
        eb = polygon["edit_box"]
        v = polygon["vertices"]
        dmin, dmax, dsize = cls.get_bounds(v)
        pos = dmin + dsize / 2
        eb.set_size(dsize)
        eb.set_position(pos)
        eb.reset()

    @classmethod
    def update_polygon_edit_box(cls, polygon):
        eb = polygon["edit_box"]
        eb.set_position(eb.position + cls.move_vector_snap)
        eb.reset_pivot()


    # ================================================== Copy / Paste ================================

    @classmethod
    def duplicate_shape(cls, shape):
        copy_shape = cls.new_2d_shape()
        cls.set_shape_state(copy_shape, cls.get_shape_state(shape))
        return copy_shape

    @classmethod
    def duplicate_fold(cls, fold):
        copy_fold = cls.new_2d_fold()
        cls.set_fold_state(copy_fold, cls.get_fold_state(fold))
        return copy_fold

    @classmethod
    def duplicate_split(cls, split):
        copy_split = cls.new_2d_split()
        cls.set_split_state(copy_split, cls.get_split_state(split))
        return copy_split

    @classmethod
    def duplicate_hole(cls, hole):
        copy_hole = cls.new_2d_hole()
        cls.set_hole_state(copy_hole, cls.get_hole_state(hole))
        return copy_hole

    @classmethod
    def user_copy(cls):
        if cls.current_shape > -1:
            cls.copy_shape = None
            cls.copy_fold = None
            cls.copy_split = None
            cls.copy_hole = None
            if cls.current_fold > -1:
                cls.copy_fold = cls.duplicate_fold(cls.get_current_fold())
            elif cls.current_split > -1:
                cls.copy_split = cls.duplicate_split(cls.get_current_split())
            elif cls.current_hole > -1:
                cls.copy_hole = cls.duplicate_hole(cls.get_current_hole())

            else:
                cls.copy_shape = cls.duplicate_shape(cls.get_current_shape())

    @classmethod
    def get_center(cls, vertices):
        center = hg.Vec2(0,0)
        for v in vertices:
            center += v
        return center / len(vertices)

    @classmethod
    def user_paste(cls, mouse, resolution):
        mp = cls.get_point_plane(hg.Vec2(mouse.X(), mouse.Y()), resolution, cls.flag_snap_to_grid, False)
        if cls.current_shape == -1:
            if cls.copy_shape is not None:
                cls.undo_record()
                paste_shape = cls.duplicate_shape(cls.copy_shape)
                center = cls.get_center(paste_shape["vertices"])
                cls.move_shape(paste_shape, mp-center)
                cls.add_shape(paste_shape)
                for hole in paste_shape["holes"]:
                    cls.reset_polygon_edit_box(hole)
                cls.reset_polygon_edit_box(paste_shape)
        else:
            if cls.copy_fold is not None:
                cls.undo_record()
                shape = cls.get_current_shape()
                paste_fold = cls.duplicate_fold(cls.copy_fold)
                center = cls.get_center(paste_fold["vertices"])
                cls.move_fold(paste_fold, mp - center)
                shape["folds"].append(paste_fold)
                cls.generates_shape(shape, cls.flag_render_holes)
                mem = cls.current_shape
                cls.clear_selection()
                cls.current_shape = mem
                cls.current_fold = len(shape["folds"]) - 1
            elif cls.copy_split is not None:
                cls.undo_record()
                shape = cls.get_current_shape()
                paste_split = cls.duplicate_split(cls.copy_split)
                center = cls.get_center(paste_split["vertices"])
                cls.move_split(paste_split, mp - center)
                shape["splits"].append(paste_split)
                cls.generates_shape(shape, cls.flag_render_holes)
                mem = cls.current_shape
                cls.clear_selection()
                cls.current_shape = mem
                cls.current_split = len(shape["splits"]) - 1
            elif cls.copy_hole is not None:
                cls.undo_record()
                shape = cls.get_current_shape()
                paste_hole = cls.duplicate_hole(cls.copy_hole)
                center = cls.get_center(paste_hole["vertices"])
                cls.move_hole(paste_hole, mp - center)
                cls.reset_polygon_edit_box(paste_hole)
                shape["holes"].append(paste_hole)
                cls.generates_shape(shape, cls.flag_render_holes)
                mem = cls.current_shape
                cls.clear_selection()
                cls.current_shape = mem
                cls.current_hole = len(shape["holes"]) -1
            elif cls.copy_shape is not None:
                cls.undo_record()
                paste_shape = cls.duplicate_shape(cls.copy_shape)
                center = cls.get_center(paste_shape["vertices"])
                cls.move_shape(paste_shape, mp-center)
                cls.add_shape(paste_shape)
                for hole in paste_shape["holes"]:
                    cls.reset_polygon_edit_box(hole)
                cls.reset_polygon_edit_box(paste_shape)

    # ================================================== Edit commands ================================

    @classmethod
    def constrain_vertex_to_ortho(cls, keyboard, m0, m1):
        if keyboard.Down(hg.K_LShift):
            vm = m1 - m0
            if abs(vm.x) >= abs(vm.y):
                m1.y = m0.y
            if abs(vm.x) < abs(vm.y):
                m1.x = m0.x

    @classmethod
    def escape_drawing(cls, shape):
        tp = cls.line_types[cls.line_type]
        if tp == "Shape":
            v = shape["vertices"]
            n = len(v)
            shape["edit_error"] = None
            if n == 2:
                cls.shapes.pop(cls.current_shape)
                cls.current_shape = -1
            else:
                v.pop(-1)
                cls.reset_polygon_edit_box(shape)

        elif tp == "Fold":
            shape["folds"].pop(cls.current_fold)
            cls.current_fold = -1

        elif tp == "Split":
            shape["splits"].pop(cls.current_split)
            cls.current_split = -1

        elif tp == "Hole":
            hole = shape["holes"][cls.current_hole]
            v = hole["vertices"]
            n = len(v)
            hole["edit_error"] = None
            if n == 2:
                shape["holes"].pop(cls.current_hole)
                cls.current_hole = -1
            else:
                v.pop(-1)
                cls.reset_polygon_edit_box(hole)

        cls.set_ui_state(Draw2D.UI_STATE_DRAW_IDLE)

    @classmethod
    def clear_selection(cls):
        cls.current_vertex = []
        cls.point_hover = None
        cls.current_fold = -1
        cls.current_split = -1
        cls.current_shape = -1
        cls.current_hole = -1


    # ================================================== UI STATES ================================

    @classmethod
    def set_ui_state(cls, state_id):
        for ui_state in cls.ui_states:
            if ui_state["id"] == state_id:
                cls.ui_state = ui_state
                break

    @classmethod
    def call_ui_state(cls, mouse, keyboard, resolution):
        cls.ui_state["function"](mouse, keyboard, resolution)

    @classmethod
    def get_current_ui_state_id(cls):
        return cls.ui_state["id"]

    @classmethod
    def ui(cls, mouse, keyboard, resolution):
        cls.texts.clear()
        if cls.flag_display_mouse_position:
            cls.display_mouse_position(mouse, resolution)

        if keyboard.Down(hg.K_LCtrl):

            if not cls.flag_tool_shortcut_mode:
                cls.state_mem = cls.get_current_ui_state_id()
                if cls.state_mem == Draw2D.UI_STATE_DRAWING:
                    cls.ctrl_mem_tool = cls.DRAW_SHAPE_TOOL_DIRECT_SELECT # When drawing a polygon, direct select is automatically enabled to facilitate vertices edition
                tool = cls.get_tool_from_id(cls.ctrl_mem_tool)
                cls.set_ui_state(tool["state"])
                cls.flag_tool_shortcut_mode = True

            tool = cls.get_tool_from_id(cls.ctrl_mem_tool)
            ms = hg.Vec2(mouse.X(), mouse.Y())
            cls.texts.push({"text": tool["name"], "pos": hg.Vec2(ms.x + 10, ms.y - 35) / resolution, "font": cls.texts.font_small, "color": hg.Color.Purple})

            # Undo / Redo

            if keyboard.Pressed(hg.K_W):
                cls.undo()
            elif keyboard.Pressed(hg.K_Y):
                cls.redo()

            # Copy / Paste

            if keyboard.Pressed(hg.K_C):
               cls.user_copy()
            elif keyboard.Pressed(hg.K_V):
                cls.user_paste(mouse, resolution)

        elif cls.flag_tool_shortcut_mode:
            cls.set_ui_state(cls.state_mem)
            cls.shape_hover = -1
            cls.point_hover = None
            cls.fold_hover = -1
            cls.split_hover = -1
            cls.hole_hover = -1
            cls.flag_tool_shortcut_mode = False

        if cls.flag_display_transform_box and not cls.flag_tool_shortcut_mode:
            current_state = cls.get_current_ui_state_id()
            if current_state in cls.transform_box_states:
                polygon = cls.get_current_polygon()
                if polygon is not None:
                    eb = polygon["edit_box"]
                    if eb.ui(mouse, keyboard, cls.view2D, resolution):
                        cls.undo_record()
                        shape = cls.get_current_shape()
                        if shape is not None:
                            cls.clear_shape_rendering_datas(shape)
                        cls.set_ui_state(cls.UI_STATE_TRANSFORM_POLYGON)

                    if eb.message != "":
                        cls.texts.push({"text": eb.message, "pos": hg.Vec2(mouse.X() + 10, mouse.Y() - 35) / resolution, "font": cls.texts.font_small, "color": hg.Color(0, 1, 1, 1)})

        cls.call_ui_state(mouse, keyboard, resolution)

    @classmethod
    def ui_drawing(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        cls.mouse_draw_update(mouse, keyboard, resolution)

    @classmethod
    def ui_move_vertex(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.mouse_move_vertex(mouse, resolution)

    @classmethod
    def ui_move_fold(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.mouse_move_fold(mouse, resolution)

    @classmethod
    def ui_move_split(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.mouse_move_split(mouse, resolution)

    @classmethod
    def ui_move_hole(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.mouse_move_hole(mouse, resolution)

    @classmethod
    def ui_move_shape(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.mouse_move_shape(mouse, resolution)

    @classmethod
    def ui_wait_remove_vertex_shape(cls, mouse, keyboard, resolution):
        if not mouse.Down(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_REMOVE_VERTEX_SHAPE)

    @classmethod
    def ui_remove_shape_vertex(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        tp = cls.line_types[cls.line_type]
        if tp == "Shape":
            cls.mouse_remove_vertex_shape(mouse, keyboard, resolution)
        elif tp == "Hole":
            cls.mouse_remove_vertex_hole(mouse, keyboard, resolution)

    @classmethod
    def ui_wait_add_vertex_shape(cls, mouse, keyboard, resolution):
        if not mouse.Down(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_ADD_VERTEX_SHAPE)

    @classmethod
    def ui_add_shape_vertex(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)

        tp = cls.line_types[cls.line_type]
        if tp == "Shape":
            cls.mouse_add_vertex_shape(mouse, keyboard, resolution)
        elif tp == "Hole":
            cls.mouse_add_vertex_hole(mouse, keyboard, resolution)

    @classmethod
    def ui_wait_remove_vertex_hole(cls, mouse, keyboard, resolution):
        if not mouse.Down(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_REMOVE_VERTEX_HOLE)

    @classmethod
    def ui_remove_hole_vertex(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        tp = cls.line_types[cls.line_type]
        if tp == "Hole":
            cls.mouse_remove_vertex_hole(mouse, keyboard, resolution)

    @classmethod
    def ui_wait_add_vertex_hole(cls, mouse, keyboard, resolution):
        if not mouse.Down(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_ADD_VERTEX_HOLE)

    @classmethod
    def ui_add_hole_vertex(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        tp = cls.line_types[cls.line_type]
        if tp == "Hole":
            cls.mouse_add_vertex_hole(mouse, keyboard, resolution)

    @classmethod
    def ui_select(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)

        if cls.mouse_fold_selection(mouse, resolution):
            cls.set_line_type(Draw2D.LINE_TYPE_FOLD)
            cls.reset_move_vector()
            cls.set_ui_state(cls.UI_STATE_MOVING_FOLD)

        elif cls.mouse_split_selection(mouse, resolution):
            cls.set_line_type(Draw2D.LINE_TYPE_SPLIT)
            cls.reset_move_vector()
            cls.set_ui_state(cls.UI_STATE_MOVING_SPLIT)

        elif cls.mouse_hole_selection(mouse, resolution):
            cls.set_line_type(Draw2D.LINE_TYPE_HOLE)
            cls.reset_move_vector()
            cls.set_ui_state(cls.UI_STATE_MOVING_HOLE)

        # Shape check selection MUST stay in last place
        elif cls.mouse_shape_selection(mouse, resolution):
            cls.set_line_type(Draw2D.LINE_TYPE_SHAPE)
            cls.reset_move_vector()
            cls.set_ui_state(cls.UI_STATE_MOVING_SHAPE)

        elif keyboard.Pressed(hg.K_Suppr):
            cls.cmd_delete()

    @classmethod
    def ui_direct_select(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        cls.mouse_vertex_selection(mouse, keyboard, resolution)

    @classmethod
    def ui_wait_draw_idle(cls, mouse, keyboard, resolution):
        if not mouse.Down(hg.MB_0):
            cls.set_ui_state(Draw2D.UI_STATE_DRAW_IDLE)

    @classmethod
    def ui_draw_idle(cls, mouse, keyboard, resolution):
        cls.view2D.update_view_scale(mouse, keyboard)
        cls.view2D.mouse_drag_view(mouse, keyboard, resolution)
        if not cls.mouse_draw(mouse, keyboard, resolution):
            if keyboard.Pressed(hg.K_Suppr):
                cls.cmd_delete()

    @classmethod
    def ui_transform_polygon(cls, mouse, keyboard, resolution):
        polygon = cls.get_current_polygon()


        if polygon is not None:
            tp = cls.line_types[cls.line_type]
            if tp == "Shape":
                shape = cls.get_current_shape()
            eb = polygon["edit_box"]
            if eb.ui(mouse, keyboard, cls.view2D, resolution):
                n = len(polygon["vertices"])

                if cls.transform_polygon_backup is None:
                    cls.transform_polygon_backup = {"vertices": [None] * n}
                    matrix = hg.InverseFast(eb.matrix)
                    for v_idx in range(n):
                        v = polygon["vertices"][v_idx]
                        cls.transform_polygon_backup["vertices"][v_idx] = hg.Vec3(v.x, v.y, 0) * matrix
                    if tp == "Shape":
                        cls.transform_polygon_backup["folds"] = []
                        cls.transform_polygon_backup["splits"] = []
                        cls.transform_polygon_backup["holes"] = []
                        for fold in shape["folds"]:
                            ft = []
                            for v in fold["vertices"]:
                                ft.append(hg.Vec3(v.x, v.y, 0) * matrix)
                            cls.transform_polygon_backup["folds"].append(ft)
                        for split in shape["splits"]:
                            st = []
                            for v in split["vertices"]:
                                st.append(hg.Vec3(v.x, v.y, 0) * matrix)
                            cls.transform_polygon_backup["splits"].append(st)
                        for hole in shape["holes"]:
                            ht = []
                            for vtx in hole["vertices"]:
                                ht.append(hg.Vec3(vtx.x, vtx.y, 0) * matrix)
                            cls.transform_polygon_backup["holes"].append(ht)

                matrix = eb.matrix
                for v_idx in range(n):
                    vt = cls.transform_polygon_backup["vertices"][v_idx] * matrix
                    v = polygon["vertices"][v_idx]
                    v.x, v.y = vt.x, vt.y
                if tp == "Shape":
                    for fold_idx in range(len(shape["folds"])):
                        for v_idx in range(2):
                            vt = cls.transform_polygon_backup["folds"][fold_idx][v_idx] * matrix
                            v = shape["folds"][fold_idx]["vertices"][v_idx]
                            v.x, v.y = vt.x, vt.y
                    for split_idx in range(len(shape["splits"])):
                        for v_idx in range(2):
                            vt = cls.transform_polygon_backup["splits"][split_idx][v_idx] * matrix
                            v = shape["splits"][split_idx]["vertices"][v_idx]
                            v.x, v.y = vt.x, vt.y
                    for hole_idx in range(len(shape["holes"])):
                        for v_idx in range(len(cls.transform_polygon_backup["holes"][hole_idx])):
                            vt = cls.transform_polygon_backup["holes"][hole_idx][v_idx] * matrix
                            v = shape["holes"][hole_idx]["vertices"][v_idx]
                            v.x, v.y = vt.x, vt.y

            else:
                cls.transform_polygon_backup = None
                pol.make_polygon_cw(polygon["vertices"])
                if tp == "Shape":
                    for hole in shape["holes"]:
                        pol.make_polygon_cw(hole["vertices"])
                        cls.reset_polygon_edit_box(hole)
                cls.set_ui_state(cls.get_tool_from_id(cls.draw_shape_tool_id)["state"])
                shape = cls.get_current_shape()
                if shape is not None:
                    cls.generates_shape(cls.get_current_shape(), True)

    # ==================================== Delete all ===========================================================

    @classmethod
    def cmd_delete(cls):
        tp = cls.line_types[cls.line_type]
        shape = cls.get_current_shape()
        if shape is not None:
            if tp == "Shape":
                cls.shapes.pop(cls.current_shape)
                cls.current_shape = -1
                cls.shape_hover = -1
                cls.current_vertex = []

            elif tp == "Fold":
                fold = cls.get_current_fold()
                if fold is not None:
                    shape["folds"].pop(cls.current_fold)
                    cls.current_fold = -1
                    cls.fold_hover = -1
                    cls.current_vertex = []
                    cls.generates_shape(shape, cls.flag_render_holes)

            elif tp == "Split":
                split = cls.get_current_split()
                if split is not None:
                    shape["splits"].pop(cls.current_split)
                    cls.current_split = -1
                    cls.split_hover = -1
                    cls.current_vertex = []
                    cls.generates_shape(shape, cls.flag_render_holes)

            elif tp == "Hole":
                hole = cls.get_current_hole()
                if hole is not None:
                    shape["holes"].pop(cls.current_hole)
                    cls.current_hole = -1
                    cls.hole_hover = -1
                    cls.current_vertex = []
                    cls.generates_shape(shape, cls.flag_render_holes)

    # ==================================== Main display ==========================================================

    @classmethod
    def update_display(cls, vid, resolution, main_state, flag_show_backdrops, dts):
        # ---------Color twinkles------------------
        cls.twinkle_t = (cls.twinkle_t + dts) % 1
        cls.point_hover_color = cls.point_hover_color_twinkle * (0.75 + 0.25 * abs(sin(((cls.twinkle_t / cls.twinkle_speed) % 1) * pi)))

        # ---------
        cls.lines2D = []
        cls.join_distance = cls.join_size / resolution.y * cls.view2D.view_scale
        current_ui_state = cls.get_current_ui_state_id()

        # cls.texts.push({"text": "Scale: %.2f" % cls.view2D.view_scale, "pos": hg.Vec2(0.91, 0.96)})

        # ---------------------

        hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, hg.ColorToABGR32(cls.background_color), 1.0, 0)
        hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
        vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(cls.view2D.cursor_position.x, cls.view2D.cursor_position.y, -1)), cls.view2D.view_scale, 0.1, 100, hg.Vec2(resolution.x / resolution.y, 1))
        hg.SetViewTransform(vid, vs.view, vs.proj)

        hg.Touch(vid)
        if flag_show_backdrops:
            Backdrops.display_maps(vid)

        # ---------------------------------
        vid += 1
        hg.SetViewClear(vid, 0, 0, 1.0, 0)
        hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
        # vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(cls.view2D.cursor_position.x, cls.view2D.cursor_position.y, -1)), cls.view2D.view_scale, 0.1, 100, hg.Vec2(Main.resolution.x / Main.resolution.y, 1))
        hg.SetViewTransform(vid, vs.view, vs.proj)

        hg.Touch(vid)

        if flag_show_backdrops:
            Backdrops.display_edit_boxes(vid, cls.view2D, resolution)
        if cls.point_hover is not None:
            cls.display_point_hover(vid, resolution)

        cls.display_current_vertex(vid, resolution)
        if cls.current_join_vertex is not None:
            cls.display_current_join_vertex(vid)
        if cls.fold_hover >= 0:
            cls.display_fold_hover(vid, resolution)
        if cls.split_hover >= 0:
            cls.display_split_hover(vid, resolution)
        if cls.hole_hover >= 0:
            cls.display_hole_hover(vid, resolution)

        if cls.view2D.grid_intensity > 1e-6:
            cls.draw_grid(resolution)

        if cls.flag_debug:
            if cls.flag_show_holey_faces:
                cls.display_holey_shape(vid, cls.get_current_shape(), cls.face_holey_color, resolution)

        cls.display_folds(vid, resolution)
        cls.display_shapes(vid, resolution)
        cls.display_holes(vid, resolution)
        cls.display_splits(vid, resolution)
        if cls.flag_display_transform_box and cls.main_state_id == main_state and not cls.flag_tool_shortcut_mode:
            if current_ui_state in cls.transform_box_display_states:
                cls.display_transform_box(vid, resolution)
        cls.flush_lines2D(vid)

        # Backdrops.update_display(vid,cls.view2D.cursor_position,cls.view2D.view_scale,resolution)
        shape = cls.get_current_shape()
        if shape is not None:
            cls.display_shape_infos(shape, resolution)


        # ---------------------------
        vid += 1
        cls.texts.display(vid, resolution)

        return vid + 1
