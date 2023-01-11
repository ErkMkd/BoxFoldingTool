# ================================================================
#  Edit 2D graphics box
# ================================================================

import harfang as hg
from math import pi, cos, sin, atan2
import data_converter as dc


class View2D:

	def __init__(self):

		self.view_scale = 50
		self.cursor_position = hg.Vec2(0, 0)
		self.backdrops_intensity = 1
		self.grid_size = 1
		self.grid_subdivisions = 10
		self.grid_intensity = 1

	def reset(self):
		self.view_scale = 50
		self.cursor_position = hg.Vec2(0, 0)
		self.backdrops_intensity = 1
		self.grid_size = 1
		self.grid_subdivisions = 10
		self.grid_intensity = 1

	def get_state(self):
		state = dict(self.__dict__)
		state["cursor_position"] = dc.vec2_to_list(self.cursor_position)
		return state

	def set_state(self,state):
		for k, v in state.items():
			if k == "cursor_position":
				self.cursor_position = dc.list_to_vec2(state["cursor_position"])
			elif hasattr(self, k):
				setattr(self, k, v)

	def update_view_scale(self, mouse, keyboard):
		# Mouse ctrl:
		w = mouse.Wheel()
		dz = 0.1

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
			self.view_scale = max(0.0001, self.view_scale * (1 + dz))

	def mouse_drag_view(self, mouse, keyboard, resolution):
		if mouse.Down(hg.MB_2):
			mdx = mouse.DtX()
			mdy = mouse.DtY()

			md = hg.Vec2(mdx / resolution.y, mdy / resolution.y)

			self.cursor_position = self.cursor_position - md * self.view_scale

	def get_point_screen(self, p: hg.Vec2, resolution: hg.Vec2):
		# renvoie la position à l'écran d'un point 2D du plan de travail
		ps = ((p - self.cursor_position) / self.view_scale) * resolution.y + resolution / 2
		return ps

	def get_point_plane(self, ps: hg.Vec2, resolution: hg.Vec2):
		p = (ps - resolution / 2) / resolution.y * self.view_scale + self.cursor_position
		return p


class TextOverlay:

	def __init__(self, resolution):
		self.font_program = hg.LoadProgramFromAssets("core/shader/font.vsb", "core/shader/font.fsb")
		self.font_small = hg.LoadFontFromAssets("font/default.ttf", 16 / 1080 * resolution.y)
		self.font_big = hg.LoadFontFromAssets("font/default.ttf", 24 / 1080 * resolution.y)
		self.text_matrx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(0), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1))
		self.text_uniform_set_values = hg.UniformSetValueList()
		self.text_uniform_set_texture_list = hg.UniformSetTextureList()
		self.text_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)
		self.default_text_color = hg.Vec4(0.8, 0.8, 0.5, 1)
		self.texts = []

	def clear(self):
		self.texts = []

	def push(self, text_object):
		self.texts.append(text_object)

	def display(self, vid, resolution):
		hg.SetViewClear(vid, 0, 0, 1.0, 0)
		hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))

		ratio = resolution.x / resolution.y
		vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(resolution.x / 2, resolution.y / 2, 0)), resolution.y, 0.1, 100, hg.Vec2(ratio, -1))
		hg.SetViewTransform(vid, vs.view, vs.proj)

		for text in self.texts:
			self.text_uniform_set_values.clear()
			if not "color" in text:
				color = self.default_text_color
			else:
				color = text["color"]
				color = hg.Vec4(color.r, color.g, color.b, color.a)
			self.text_uniform_set_values.push_back(hg.MakeUniformSetValue("u_color", color))  # Color
			pos = text["pos"] * resolution
			hg.DrawText(vid, text["font"], text["text"], self.font_program, "u_tex", 0, self.text_matrx, hg.Vec3(pos.x, resolution.y - pos.y, 1), hg.DTHA_Left, hg.DTVA_Bottom, self.text_uniform_set_values, self.text_uniform_set_texture_list, self.text_render_state)


class Edit2DBox:
	FLAG_SCALE = 0b1
	FLAG_SCALEXY = 0b10
	FLAG_ROTATE = 0b100
	FLAG_MOVE = 0b1000

	transform_cell_size = 10
	transform_cell_f2_dist = 5
	vtx_decl = None
	line_program = None

	UI_STATE_IDLE = 0
	UI_STATE_MOVING = 1
	UI_STATE_MOVING_PIVOT = 2
	UI_STATE_SCALING = 3
	UI_STATE_ROTATING = 4

	@classmethod
	def init(cls, vtx_decl, line_program):
		cls.vtx_decl = vtx_decl
		cls.line_program = line_program

	@classmethod
	def addBoxes(cls, flags, boxes: list):
		xmin = boxes[0].position.x - boxes[0].size.x / 2 * boxes[0].scale.x
		xmax = boxes[0].position.x + boxes[0].size.x / 2 * boxes[0].scale.x
		ymin = boxes[0].position.y - boxes[0].size.y / 2 * boxes[0].scale.y
		ymax = boxes[0].position.y + boxes[0].size.y / 2 * boxes[0].scale.y
		for bidx in range(1, len(boxes)):
			bx = boxes[bidx]
			xmin = min(xmin, bx.position.x - bx.size.x / 2 * bx.scale.x)
			xmax = max(xmax, bx.position.x + bx.size.x / 2 * bx.scale.x)
			ymin = min(ymin, bx.position.y - bx.size.y / 2 * bx.scale.y)
			ymax = max(ymax, bx.position.y + bx.size.y / 2 * bx.scale.y)
		return Edit2DBox(flags, hg.Vec2((xmin + xmax) / 2, (ymin + ymax) / 2), hg.Vec2(xmax - xmin, ymax - ymin), hg.Vec2(1, 1))

	def __init__(self, flags, pos: hg.Vec2, size: hg.Vec2, scale: hg.Vec2):
		self.flags = flags

		self.lines_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Less, hg.FC_Disabled)

		self.size = size
		self.pivot = hg.Vec2(0, 0)
		self.position = pos

		self.scale = scale
		self.angle = 0

		self.cells_color = hg.Color(0.2, 1, 0.2, 1)
		self.box_color = hg.Color(0.2, 1, 0.2, 1)

		self.flag_moving = False
		self.flag_scaling = False
		self.flag_rotating = False
		self.flag_moving_pivot = False
		self.scale_start_vector = None
		self.scale_start_vector_pos = None
		self.rotate_start_vector = None
		self.start_angle = 0
		self.start_position = hg.Vec2(0, 0)
		self.move_pivot_start_pos = None
		self.move_pivot_start_pivot = None

		self.flag_lock_scale_axis = False
		self.locked_axis = 0

		self.message = ""

		self.transform_cells_positions = []
		self.matrix = None
		self.update_matrix()
		self.update_transform_cells_position()

	def get_state(self):
		state = {
			"size": dc.vec2_to_list(self.size),
			"position": dc.vec2_to_list(self.position),
			"angle": self.angle,
			"scale": dc.vec2_to_list(self.scale),
			"pivot": dc.vec2_to_list(self.pivot)
		}
		return state

	def set_state(self, state):
		self.size = dc.list_to_vec2(state["size"])
		self.position = dc.list_to_vec2(state["position"])
		self.scale = dc.list_to_vec2(state["scale"])
		self.angle = state["angle"]
		self.pivot = dc.list_to_vec2(state["pivot"])
		self.update_matrix()
		self.update_transform_cells_position()

	def contains(self, p):
		ps = self.position - (self.size / 2 * self.scale)
		pe = self.position + (self.size / 2 * self.scale)
		return ps.x < p.x < pe.x and ps.y < p.y < pe.y

	def get_ui_state(self):
		if self.flag_moving_pivot: return Edit2DBox.UI_STATE_MOVING_PIVOT
		if self.flag_moving: return Edit2DBox.UI_STATE_MOVING
		if self.flag_scaling: return Edit2DBox.UI_STATE_SCALING
		return Edit2DBox.UI_STATE_IDLE

	def get_untransformed_bounds(self):
		dmin = self.position - self.size * 0.5
		dmax = self.position + self.size * 0.5
		return dmin, dmax, self.size

	def set_colors(self, box_color, cells_color):
		self.box_color = box_color
		self.cells_color = cells_color

	def set_scale(self, scale):
		self.scale.x = scale
		self.scale.y = scale
		self.update_matrix()
		self.update_transform_cells_position()

	def set_scale_xy(self, scale):
		self.scale.x, self.scale.y = scale.x, scale.y
		self.update_matrix()
		self.update_transform_cells_position()

	def set_scale_x(self, sx):
		self.scale.x = sx
		self.update_matrix()
		self.update_transform_cells_position()

	def set_scale_y(self, sy):
		self.scale.y = sy
		self.update_matrix()
		self.update_transform_cells_position()

	def set_position(self, position):
		self.position.x, self.position.y = position.x, position.y
		self.update_matrix()
		self.update_transform_cells_position()

	def reset_pivot(self):
		self.pivot.x, self.pivot.y = self.position.x, self.position.y

	def set_size(self, size):
		self.size.x, self.size.y = size.x, size.y
		self.update_matrix()
		self.update_transform_cells_position()

	def reset(self):
		self.reset_pivot()
		self.scale.x = self.scale.y = 1
		self.angle = 0
		self.update_matrix()
		self.update_transform_cells_position()

	def update_matrix(self):
		self.matrix = hg.TransformationMat4(hg.Vec3(self.position.x, self.position.y, 0), hg.Vec3(0, 0, self.angle), hg.Vec3(self.scale.x, self.scale.y, 1))

	def update_transform_cells_position(self):
		pe = self.size / 2
		ps = pe * -1
		self.transform_cells_positions = [
			hg.Vec3(ps.x, ps.y, 0) * self.matrix,
			hg.Vec3(ps.x, pe.y, 0) * self.matrix,
			hg.Vec3(pe.x, pe.y, 0) * self.matrix,
			hg.Vec3(pe.x, ps.y, 0) * self.matrix
			]
		for i in range(4):
			p = self.transform_cells_positions[i]
			self.transform_cells_positions[i] = hg.Vec2(p.x, p.y)

	def draw_box(self, vid, position, size, angle, color):
		cp = dc.pack_color_RGba(color)
		vtx = hg.Vertices(Edit2DBox.vtx_decl, 8)
		vtx.Clear()

		pe = size / 2
		ps = pe * -1

		mat = hg.TransformationMat4(hg.Vec3(position.x, position.y, 0), hg.Vec3(0, 0, angle))

		p1 = hg.Vec3(ps.x, ps.y, 0) * mat
		p2 = hg.Vec3(ps.x, pe.y, 0) * mat
		p3 = hg.Vec3(pe.x, pe.y, 0) * mat
		p4 = hg.Vec3(pe.x, ps.y, 0) * mat

		vtx.Begin(0).SetPos(p1).SetColor0(cp).End()
		vtx.Begin(1).SetPos(p2).SetColor0(cp).End()

		vtx.Begin(2).SetPos(p2).SetColor0(cp).End()
		vtx.Begin(3).SetPos(p3).SetColor0(cp).End()

		vtx.Begin(4).SetPos(p3).SetColor0(cp).End()
		vtx.Begin(5).SetPos(p4).SetColor0(cp).End()

		vtx.Begin(6).SetPos(p4).SetColor0(cp).End()
		vtx.Begin(7).SetPos(p1).SetColor0(cp).End()

		hg.DrawLines(vid, vtx, Edit2DBox.line_program, self.lines_render_state)

	def draw_point(self, vid, view: View2D, resolution: hg.Vec2, p: hg.Vec2, color: hg.Color, psize, angle):  # psize: pixels size
		size = view.view_scale / resolution.y * psize
		self.draw_box(vid, p, hg.Vec2(size, size), angle, color)

	def draw_point_circle(self, vid, view, resolution, c, r, color):
		ray = view.view_scale / resolution.y * r
		self.draw_circle(vid, c, ray, color)

	def draw_point_cross(self, vid, view, resolution, c, r, color):
		ray = view.view_scale / resolution.y * r
		self.draw_cross(vid, c, ray, color)

	def draw_circle(self, vid, c, r, color):
		cp = dc.pack_color_RGba(color)
		numSegments = 32
		stp = 2 * pi / numSegments
		p0 = hg.Vec3(c.x + r, c.y, 0)
		p1 = hg.Vec3(0, 0, 0)
		vtx = hg.Vertices(Edit2DBox.vtx_decl, numSegments * 2 + 2)
		vtx.Clear()

		for i in range(numSegments + 1):
			p1.x = r * cos(i * stp) + c.x
			p1.y = r * sin(i * stp) + c.y
			vtx.Begin(2 * i).SetPos(p0).SetColor0(cp).End()
			vtx.Begin(2 * i + 1).SetPos(p1).SetColor0(cp).End()
			p0.x, p0.y = p1.x, p1.y

		hg.DrawLines(vid, vtx, Edit2DBox.line_program, self.lines_render_state)

	def draw_cross(self, vid, c, r, color):
		cp = dc.pack_color_RGba(color)
		vtx = hg.Vertices(Edit2DBox.vtx_decl, 4)
		vtx.Clear()
		p1 = hg.Vec3(c.x - r, c.y, 0)
		p2 = hg.Vec3(c.x + r, c.y, 0)
		p3 = hg.Vec3(c.x, c.y - r, 0)
		p4 = hg.Vec3(c.x, c.y + r, 0)

		vtx.Begin(0).SetPos(p1).SetColor0(cp).End()
		vtx.Begin(1).SetPos(p2).SetColor0(cp).End()

		vtx.Begin(2).SetPos(p3).SetColor0(cp).End()
		vtx.Begin(3).SetPos(p4).SetColor0(cp).End()

		hg.DrawLines(vid, vtx, Edit2DBox.line_program, self.lines_render_state)

	def display(self, vid, view: View2D, resolution: hg.Vec2):

		self.draw_box(vid, self.position, self.size * self.scale, self.angle, self.box_color)

		# corners cells:
		for cell in self.transform_cells_positions:
			self.draw_point(vid, view, resolution, cell, self.cells_color, self.transform_cell_size, self.angle)

		# pivot:
		self.draw_point_circle(vid, view, resolution, self.pivot, self.transform_cell_size / 2 * 1.414, self.cells_color)
		self.draw_point_cross(vid, view, resolution, self.pivot, self.transform_cell_size / 2 * 1.414, self.cells_color)
		# center:
		self.draw_point_circle(vid, view, resolution, self.position, self.transform_cell_size / 2 * 1.414, self.cells_color)

	def rotate_vector2D(self, v, a):
		cos_a = cos(a)
		sin_a = sin(a)
		return hg.Vec2(v.x * cos_a - v.y * sin_a , v.x * sin_a + v.y * cos_a)

	def ui(self, mouse: hg.Mouse, keyboard: hg.Keyboard, view: View2D, resolution: hg.Vec2):
		self.message = ""
		# hover cells:
		flag_hover_scale_cell = False
		flag_hover_rotate_cell = False
		start_transform_vector = None
		cell_hovered = None
		ms = hg.Vec2(mouse.X(), mouse.Y())
		mp = view.get_point_plane(ms, resolution)

		s = self.size * self.scale
		ps = view.get_point_screen(self.position - s / 2, resolution)
		pe = view.get_point_screen(self.position + s / 2, resolution)

		flag_f2 = False
		for cell_pos in self.transform_cells_positions:
			cell = view.get_point_screen(cell_pos, resolution)
			dist = hg.Len(ms - cell)
			if (self.flags & self.FLAG_ROTATE) != 0:
				if self.transform_cell_size/2 <= dist <= self.transform_cell_f2_dist + self.transform_cell_size:
					flag_hover_rotate_cell = True
					cell_hovered = cell

					self.message = "Rotate"
					break
			if (self.flags & (self.FLAG_SCALE | self.FLAG_SCALEXY)) != 0:
				if not flag_f2 and dist <= self.transform_cell_size/2:
						flag_hover_scale_cell = True
						cell_hovered = cell
						self.message = "Scale"
						break

		if flag_hover_rotate_cell:
			start_transform_vector = cell - (view.get_point_screen(self.pivot, resolution))

		if flag_hover_scale_cell:
			start_transform_vector = cell -(view.get_point_screen(self.pivot, resolution))

		# Hover pivot:
		flag_hover_pivot = False
		piv_s = view.get_point_screen(self.pivot, resolution)
		if hg.Len(ms - piv_s) <= self.transform_cell_size:
			flag_hover_pivot = True
			self.message = "Pivot"

		# mouse pointer in box ?
		flag_hover_box = False
		if (self.flags & self.FLAG_MOVE) != 0:
			if not flag_hover_scale_cell:
				if ps.x < ms.x < pe.x and ps.y < ms.y < pe.y:
					flag_hover_box = True

		# User action:
		if mouse.Down(hg.MB_0):
			mdx = mouse.DtX()
			mdy = mouse.DtY()
			md = hg.Vec2(mdx / resolution.y, mdy / resolution.y) * view.view_scale
			md_r = self.rotate_vector2D(md, -self.angle)

			if self.flag_scaling:
				m_vector = ms - view.get_point_screen(self.pivot, resolution)

				if (self.flags & self.FLAG_SCALE) != 0:
					m_vector_r = self.rotate_vector2D(m_vector, -self.angle)
					ustv = hg.Normalize(self.scale_start_vector)
					dot = hg.Dot(ustv, m_vector_r)
					scale_vector = ustv * dot
					s = hg.Len(scale_vector) / hg.Len(self.scale_start_vector)
					sp = hg.Len(scale_vector) / hg.Len(self.scale_start_vector_pos)
					if dot < 0 :
						s = -s
						sp = -sp
					self.set_scale(s)
					self.position = (self.start_position - self.pivot) * sp + self.pivot


				elif (self.flags & self.FLAG_SCALEXY) != 0:
					m_vector_r = self.rotate_vector2D(m_vector, -self.angle)
					#scale_start_vector_r = self.rotate_vector2D(self.scale_start_vector, -self.angle)
					s = m_vector_r / self.scale_start_vector
					sp = m_vector / self.scale_start_vector_pos

					shift_down = keyboard.Down(hg.K_LShift)
					if shift_down and not self.flag_lock_scale_axis:
						if hg.Len(md_r)>0:
							self.flag_lock_scale_axis = True
							if abs(md_r.x) >= abs(md_r.y): self.locked_axis = 0
							elif abs(md_r.y) > abs(md_r.x): self.locked_axis = 1
					elif not shift_down:
						self.flag_lock_scale_axis = False

					if abs(self.scale_start_vector.x) > 1e-4 and abs(self.scale_start_vector.y) > 1e-4 and not self.flag_lock_scale_axis:
						self.set_scale_xy(s)
					else:
						if abs(self.scale_start_vector.x) < 1e-4 or self.locked_axis == 1:
							self.set_scale_y(s.y)

						elif abs(self.scale_start_vector.y) < 1e-4 or self.locked_axis == 0:
							self.set_scale_x(s.x)

					if abs(self.scale_start_vector_pos.x) < 1e-4:
						sp.x = 1
					if abs(self.scale_start_vector_pos.y) < 1e-4:
						sp.y = 1

					self.position = (self.start_position - self.pivot) * sp + self.pivot
				self.update_matrix()
				self.update_transform_cells_position()
				return True

			elif self.flag_rotating:
				m_vector = ms - (view.get_point_screen(self.pivot, resolution))
				u_start = hg.Normalize(self.rotate_start_vector)
				u_current = hg.Normalize(m_vector)
				cos_a = hg.Dot(u_start, u_current)
				sin_a = u_start.x * u_current.y - u_current.x * u_start.y
				d_angle = atan2(sin_a, cos_a)
				self.angle = d_angle + self.start_angle
				vp = self.start_position - self.pivot
				self.position = self.rotate_vector2D(vp, d_angle) + self.pivot
				self.update_matrix()
				self.update_transform_cells_position()
				return True


			elif self.flag_moving_pivot:
				cs = view.get_point_screen(self.position, resolution)
				if cell_hovered is not None:
					mp = view.get_point_plane(cell_hovered, resolution)
				elif hg.Len(ms - cs) <= self.transform_cell_size:
					mp = hg.Vec2(self.position)
				self.pivot.x, self.pivot.y = mp.x, mp.y
				self.update_matrix()
				self.update_transform_cells_position()
				return True

			elif self.flag_moving:
				self.position.x += md.x
				self.position.y += md.y
				self.pivot.x += md.x
				self.pivot.y += md.y
				self.update_matrix()
				self.update_transform_cells_position()
				return True

			elif flag_hover_pivot:
				self.flag_moving_pivot = True
				self.move_pivot_start_pivot = hg.Vec2(self.pivot)
				return True

			elif flag_hover_rotate_cell:
				self.flag_rotating = True
				self.start_angle = self.angle
				self.rotate_start_vector = start_transform_vector
				self.start_position.x, self.start_position.y = self.position.x, self.position.y
				return True

			elif flag_hover_scale_cell:
				self.flag_lock_scale_axis = False
				self.flag_scaling = True
				self.scale_start_vector = self.rotate_vector2D(start_transform_vector, -self.angle) / hg.Vec2(abs(self.scale.x), abs(self.scale.y))
				self.scale_start_vector_pos = start_transform_vector
				self.start_position = hg.Vec2(self.position)
				return True

			elif flag_hover_box:
				# if mdx!=0 or mdy!=0:
				self.flag_moving = True
				return True
		else:
			self.flag_moving = False
			self.flag_scaling = False
			self.flag_moving_pivot = False
			self.flag_rotating = False
		return False
