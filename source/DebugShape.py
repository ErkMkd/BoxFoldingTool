# ================================================================
#  Debug shape
# ================================================================

import harfang as hg
import Polygons as pol
from math import pi, cos, sin, tan, floor
import data_converter as dc
from Draw2D import *
import tools2D as t2D


class DebugShape:
	vtx_decl = None
	shapes_program = None
	lines_render_state = None

	triangles = None

	view_scale = 50
	cursor_position = None

	texts = None

	background_color = None
	main_shape_color = None
	default_text_color = None
	triangles_color = None
	face_color = None
	selected_face_color = None

	points_size = 4

	step_state = None
	step_states = None

	STEP_STATE_MAIN_SHAPE_ID = 0
	STEP_STATE_FACES_ID = 1
	STEP_STATE_TRIANGLES_ID = 2

	flag_display_holes = True
	flag_display_holey_vertices_idx = True

	faces = None
	triangles = None
	explode_scale = 1.1
	current_face = 0
	faces_StringList = None

	@classmethod
	def init(cls, vtx_decl_2d, program_2d, text_overlay: t2D.TextOverlay, resolution):
		cls.vtx_decl = vtx_decl_2d
		cls.texts = text_overlay
		cls.shapes_program = program_2d
		cls.cursor_position = hg.Vec2(0, 0)
		cls.lines_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Less, hg.FC_Disabled)

		cls.background_color = hg.Color(0.3, 0.3, 0.3, 1)
		cls.default_text_color = hg.Vec4(0.8, 0.8, 0.5, 1)
		cls.triangles_color = hg.Color(0.9, 0.9, 0.9, 1)
		cls.face_color = hg.Color(0.6, 0.6, 0.6, 1)
		cls.selected_face_color = hg.Color(1, 0.9, 0.6, 1)
		cls.main_shape_color = hg.Color(1, 1, 1, 1)

		cls.step_states = [
			{"id": cls.STEP_STATE_MAIN_SHAPE_ID, "function": DebugShape.step_main_shape},
			{"id": cls.STEP_STATE_FACES_ID, "function": DebugShape.step_faces},
			{"id": cls.STEP_STATE_TRIANGLES_ID, "function": DebugShape.step_triangles}
		]
		cls.step_state = cls.step_states[cls.STEP_STATE_MAIN_SHAPE_ID]

	@classmethod
	def clear_all(cls):
		cls.faces = None
		cls.triangles = None

	@classmethod
	def mouse_drag_view(cls, mouse, resolution):
		if mouse.Down(hg.MB_1):
			mdx = mouse.DtX()
			mdy = mouse.DtY()

			md = hg.Vec2(mdx / resolution.y, mdy / resolution.y)

			cls.cursor_position = cls.cursor_position - md * cls.view_scale

	@classmethod
	def update_view_scale(cls, mouse, keyboard):
		# Mouse ctrl:
		w = mouse.Wheel()
		dz = 0.05

		if w == 0:
			if mouse.Down(hg.MB_2):
				w = mouse.DtY()
				dz = abs(w * 0.01)

		# Keyboard ctrl
		if w == 0:
			dz = 0.05
			if keyboard.Down(hg.K_Add):
				w = 1
			elif keyboard.Down(hg.K_Sub):
				w = -1

		# Zoom:
		if w != 0:
			if w < 0: dz *= -1
			cls.view_scale = cls.view_scale * (1 + dz)

	@classmethod
	def get_shape_bounds(cls, v):
		mn = hg.Vec2(1e6, 1e6)
		mx = hg.Vec2(-1e6, -1e6)
		for p in v:
			mn.x = min(mn.x, p.x)
			mn.y = min(mn.y, p.y)
			mx.x = max(mx.x, p.x)
			mx.y = max(mx.y, p.y)
		center = mn + (mx - mn) / 2
		return mn, mx, center

	@classmethod
	def get_triangles(cls, shape):
		cls.triangles = []
		v = shape["folded_vertices"]

		# bounds:
		mn, mx, shape_center = cls.get_shape_bounds(v)

		for face_idx in range(len(shape["faces"])):
			face = shape["faces"][face_idx]
			if "triangles" in face and face["triangles"] is not None:
				for t in face["triangles"]:
					v0 = v[t[0]]
					v1 = v[t[1]]
					v2 = v[t[2]]
					center = v0 + v1 + v2
					center = center / 3

					# v0 = (v0-center) # / cls.explode_scale + center
					# v1 = (v1-center) # / cls.explode_scale + center
					# v2 = (v2-center) # / cls.explode_scale + center
					vc = (center - shape_center) * cls.explode_scale - center + shape_center
					cls.triangles.append({"v": [v0 + vc, v1 + vc, v2 + vc], "idx": t})

	@classmethod
	def get_faces(cls, shape):
		cls.faces = []
		v = shape["folded_vertices"]
		cls.faces_StringList = hg.StringList()

		# bounds:
		mn, mx, shape_center = cls.get_shape_bounds(v)

		for face_idx in range(len(shape["faces"])):
			face = shape["faces"][face_idx]
			vface = {"v": [], "idx": [], "holey": []}
			center = hg.Vec2(0, 0)
			for v_idx in range(len(face["idx"])):
				vi = face["idx"][v_idx]
				fv = hg.Vec2(v[vi])
				vface["v"].append(fv)
				vface["idx"].append(vi)
				center += fv
			center = center / (len(vface["v"]))
			vc = (center - shape_center) * cls.explode_scale - center + shape_center
			for fv in vface["v"]:
				fv.x, fv.y = fv.x + vc.x, fv.y + vc.y
			if "holey_idx" in face:
				for part in face["holey_idx"]:
					vpart = []
					idx_part = []
					for hv_idx in part:
						hv = shape["holey_vertices"][hv_idx]
						vpart.append(hv + vc)
						idx_part.append(hv_idx)
					vface["holey"].append({"vertices": vpart, "idx": idx_part})

			cls.faces.append(vface)
			cls.faces_StringList.push_back("Face " + str(face_idx))


	@classmethod
	def display_faces(cls, vid):

		for face_idx in range(len(cls.faces)):
			face = cls.faces[face_idx]
			if face_idx == cls.current_face:
				color = cls.selected_face_color
			else:
				color = cls.face_color
			if cls.flag_display_holes and len(face["holey"]) > 0:
				for part in face["holey"]:
					cls.draw_polygon(vid, part["vertices"], color)
			else:
				cls.draw_polygon(vid, face["v"], color)

	@classmethod
	def draw_polygon(cls, vid, v, color):
		cp = dc.pack_color_RGba(color)
		line_count = len(v)
		if line_count > 0:
			vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
			vtx.Clear()

			va = v[0]
			n = len(v)
			for vi in range(1, line_count + 1):
				vb = v[vi % n]
				vtx.Begin((vi - 1) * 2).SetPos(hg.Vec3(va.x, va.y, 0)).SetColor0(cp).End()
				vtx.Begin((vi - 1) * 2 + 1).SetPos(hg.Vec3(vb.x, vb.y, 0)).SetColor0(cp).End()
				va = vb
			hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

	@classmethod
	def display_triangles(cls, vid, color):
		cp = dc.pack_color_RGba(color)
		line_count = len(cls.triangles) * 3
		if line_count > 0:
			vtx = hg.Vertices(cls.vtx_decl, line_count * 2)
			vtx.Clear()
			vi = 0
			for t in cls.triangles:
				v0 = t["v"][0]
				v1 = t["v"][1]
				v2 = t["v"][2]
				vtx.Begin(vi).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
				vtx.Begin(vi + 1).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
				vtx.Begin(vi + 2).SetPos(hg.Vec3(v1.x, v1.y, 0)).SetColor0(cp).End()
				vtx.Begin(vi + 3).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
				vtx.Begin(vi + 4).SetPos(hg.Vec3(v2.x, v2.y, 0)).SetColor0(cp).End()
				vtx.Begin(vi + 5).SetPos(hg.Vec3(v0.x, v0.y, 0)).SetColor0(cp).End()
				vi += 6
			hg.DrawLines(vid, vtx, cls.shapes_program, cls.lines_render_state)

	@classmethod
	def draw_square(cls, vid, p, s_size, color):
		cp = dc.pack_color_RGba(color)
		vtx = hg.Vertices(cls.vtx_decl, 8)
		vtx.Clear()
		size = s_size / 2
		p1 = hg.Vec3(p.x - size, p.y - size, 0)
		p2 = hg.Vec3(p.x - size, p.y + size, 0)
		p3 = hg.Vec3(p.x + size, p.y + size, 0)
		p4 = hg.Vec3(p.x + size, p.y - size, 0)

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
	def get_point_screen(cls, p: hg.Vec2, resolution: hg.Vec2):
		# renvoie la position à l'écran d'un point 2D du plan de travail
		ps = ((p - cls.cursor_position) / cls.view_scale) * resolution.y + resolution / 2
		return ps

	@classmethod
	def draw_point(cls, vid, p, resolution, color, psize):
		size = cls.view_scale / resolution.y * psize
		cls.draw_square(vid, p, size, color)

	@classmethod
	def display_shape(cls, vid, shape, resolution, color):
		v = shape["vertices"]
		cls.draw_polygon(vid, v, color)
		# draw points
		for p_idx in range(len(v)):
			p = v[p_idx]
			cls.draw_point(vid, p, resolution, color, cls.points_size)
			cls.texts.push({"text": str(p_idx), "pos": (cls.get_point_screen(p, resolution) + hg.Vec2(5, 5)) / resolution, "color": color, "font": cls.texts.font_small})

	@classmethod
	def display_triangles_vertices(cls, vid, resolution, color):
		for t in cls.triangles:
			for pidx in range(3):
				p = t["v"][pidx]
				cls.draw_point(vid, p, resolution, color, cls.points_size)
				cls.texts.push({"text": str(t["idx"][pidx]), "pos": (cls.get_point_screen(p, resolution) + hg.Vec2(5, 5)) / resolution, "color": color, "font": cls.texts.font_small})

	@classmethod
	def get_point_offset(cls, p, points):
		p_hash = str(int(int((p.x + 500) * 1000) * 1e6 + int((p.y + 500) * 1000)))
		if not p_hash in points:
			of7 = 0
			points[p_hash] = [p]
		else:
			of7 = len(points[p_hash])
			points[p_hash].append(p)
		return of7

	@classmethod
	def display_faces_vertices(cls, vid, resolution):
		points = {}
		for face_idx in range(len(cls.faces)):
			face = cls.faces[face_idx]
			if face_idx == cls.current_face:
				color = cls.selected_face_color
			else:
				color = cls.face_color
			if cls.flag_display_holes and len(face["holey"]) > 0:
				for part in face["holey"]:
					for pidx in range(len(part["vertices"])):
						p = part["vertices"][pidx]
						of7 = cls.get_point_offset(p, points)
						cls.draw_point(vid, p, resolution, color, cls.points_size)
						if cls.flag_display_holey_vertices_idx:
							p_num = str(part["idx"][pidx])
						else:
							p_num = str(pidx)
						cls.texts.push({"text": p_num, "pos": (cls.get_point_screen(p, resolution) + hg.Vec2(5, 5 + of7 * 12)) / resolution, "color": color, "font": cls.texts.font_small})
			else:
				for pidx in range(len(face["v"])):
					p = face["v"][pidx]
					of7 = cls.get_point_offset(p, points)
					cls.draw_point(vid, p, resolution, color, cls.points_size)
					cls.texts.push({"text": str(face["idx"][pidx]), "pos": (cls.get_point_screen(p, resolution) + hg.Vec2(5, 5 + of7 * 12)) / resolution, "color": color, "font": cls.texts.font_small})

	# ==============================================================================================
	@classmethod
	def gui(cls, resolution, main_panel_size):
		wn = "Debug shape"
		if hg.ImGuiBegin("Debug shape", True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
			hg.ImGuiSetWindowPos(wn, hg.Vec2(0, 20 + main_panel_size.y), hg.ImGuiCond_Always)
			hg.ImGuiSetWindowSize(wn, hg.Vec2(main_panel_size.x, resolution.y - 20 - main_panel_size.y), hg.ImGuiCond_Always)
			hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

			f, d = hg.ImGuiRadioButton("Main shape", int(cls.get_current_step_state_id()), int(DebugShape.STEP_STATE_MAIN_SHAPE_ID))
			if f:
				cls.set_step_state(DebugShape.STEP_STATE_MAIN_SHAPE_ID)
			f, d = hg.ImGuiRadioButton("Faces", int(cls.get_current_step_state_id()), int(DebugShape.STEP_STATE_FACES_ID))
			if f:
				cls.set_step_state(DebugShape.STEP_STATE_FACES_ID)
			f, d = hg.ImGuiRadioButton("Triangles", int(cls.get_current_step_state_id()), int(DebugShape.STEP_STATE_TRIANGLES_ID))
			if f:
				cls.set_step_state(DebugShape.STEP_STATE_TRIANGLES_ID)


			step_id = cls.get_current_step_state_id()

			if step_id == DebugShape.STEP_STATE_TRIANGLES_ID and cls.triangles is not None and len(cls.triangles) > 0:
				f, d = hg.ImGuiDragFloat("Explode scale", cls.explode_scale, 0.01, 1, 1000)
				if f:
					cls.explode_scale = d
			elif step_id == DebugShape.STEP_STATE_FACES_ID and cls.faces is not None and len(cls.faces) > 0:

				f, cls.flag_display_holes = hg.ImGuiCheckbox("Display holes", cls.flag_display_holes)
				f, cls.flag_display_holey_vertices_idx = hg.ImGuiCheckbox("Display holey indices", cls.flag_display_holey_vertices_idx)

				f, d = hg.ImGuiDragFloat("Explode scale", cls.explode_scale, 0.01, 1, 1000)
				if f:
					cls.explode_scale = d

				if cls.faces_StringList is not None:
					if cls.current_face >= cls.faces_StringList.size():
						cls.current_face = 0
					f, d = hg.ImGuiListBox("Faces", cls.current_face, cls.faces_StringList, min(30, cls.faces_StringList.size()))
					if f:
						cls.current_face = d

			hg.ImGuiEnd()

	# ==============================================================================================
	@classmethod
	def ui(cls, mouse, keyboard, resolution):
		cls.update_view_scale(mouse, keyboard)
		cls.mouse_drag_view(mouse, resolution)

	# ==============================================================================================
	@classmethod
	def set_step_state(cls, state_id):
		cls.step_state = cls.step_states[state_id]

	@classmethod
	def call_step_state(cls, vid, shape, resolution):
		cls.step_state["function"](vid, shape, resolution)

	@classmethod
	def get_current_step_state_id(cls):
		return cls.step_state["id"]

	@classmethod
	def step_main_shape(cls, vid, shape, resolution):
		cls.display_shape(vid, shape, resolution, cls.main_shape_color)

	@classmethod
	def step_faces(cls, vid, shape, resolution):
		cls.get_faces(shape)
		cls.display_faces(vid)
		cls.display_faces_vertices(vid, resolution)

	@classmethod
	def step_triangles(cls, vid, shape, resolution):
		cls.get_triangles(shape)
		cls.display_triangles(vid, cls.triangles_color)
		cls.display_triangles_vertices(vid, resolution, cls.triangles_color)



	# ==============================================================================================

	@classmethod
	def update_display(cls, vid, resolution):
		cls.texts.clear()
		# cls.texts.append({"text": "Scale: %.2f" % cls.view_scale, "pos": hg.Vec2(0.91, 0.96)})

		# ---------------------

		hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, hg.ColorToABGR32(cls.background_color), 1.0, 0)
		hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
		vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(cls.cursor_position.x, cls.cursor_position.y, -1)), cls.view_scale, 0.1, 100, hg.Vec2(resolution.x / resolution.y, 1))
		hg.SetViewTransform(vid, vs.view, vs.proj)

		hg.Touch(vid)
		shape = Draw2D.get_current_shape()
		if shape is not None:
			cls.call_step_state(vid, shape, resolution)

		# ---------------------------
		vid += 1
		cls.texts.display(vid, resolution)

		return vid + 1
