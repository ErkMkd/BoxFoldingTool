# ================================================================
#  3D Drawing - Folding
# ================================================================

import harfang as hg
from math import tan, pi, sin, cos, sqrt, pow
from Backdrops import *
from Draw2D import *


class ICamera:
	def __init__(self):
		self.pos = hg.Vec3(0, 0, 0)
		self.rot = hg.Vec3(0, 0, 0)
		self.fov = 10 / 180 * pi
		self.near = 0.0001
		self.far = 1
		self.view_matrix = None
		self.projection_matrix = None

	def compute_view_projection(self, resolution):
		cam = hg.TransformationMat4(self.pos, self.rot)
		self.view_matrix = hg.InverseFast(cam)
		self.projection_matrix = hg.ComputePerspectiveProjectionMatrix(self.near, self.far, hg.FovToZoomFactor(self.fov), hg.Vec2(resolution.x / resolution.y, 1))

	def SetPos(self, pos: hg.Vec3):
		self.pos = pos

	def SetRot(self, rot: hg.Vec3):
		self.rot = rot

	def compute_point_screen_pos(self, point3d: hg.Vec3, resolution):
		pos_view = self.view_matrix * point3d
		f, pos2d = hg.ProjectToScreenSpace(self.projection_matrix, pos_view, resolution)
		if f:
			return hg.Vec2(pos2d.x, pos2d.y)
		else:
			return None


class Draw3D:

	flag_debug = False

	vs_decl = None
	res = None
	shader = None
	shader_ref = None
	scene = None
	camera = None
	pipeline = None
	render_data = None

	cube_mdl = None
	ground_mdl = None

	empty_cam_pos = None
	empty_cam_rot = None

	current_shape = None
	model_view_proportion = 1.5
	shape_pos = None
	shape_rot = None
	model_matrix = None
	model_texture_outside = None
	model_texture_inside = None

	uniform_target_tex = None
	uniform_set_value_list_outside = None
	uniform_set_value_list_inside = None
	uniform_set_value_list_side = None
	uniform_set_texture_list_outside = None
	uniform_set_texture_list_inside = None
	uniform_set_texture_list_side = None

	view_scale = 50
	nominal_view_scale = 50
	cursor_position = None
	UI_rot_angle_Y = 0
	UI_rot_angle_X = 0

	# Draw folds:
	vtx_line_decl = None
	line_program = None
	fold_line_color = None
	hover_fold_line_color = None
	selected_fold_line_color = None
	fold_manifold_size = 10
	folds_manifolds = None
	current_fold = None
	hover_fold = None

	flag_generate_holes = True
	flag_display_outside_holey_triangles = False
	flag_display_inside_holey_triangles = False
	flag_display_side_holey_triangles = False
	flag_display_triangles = False
	flag_display_vertices = False
	flag_display_holey_vertices = False
	flag_display_faces = True
	flag_display_extruded_vertices = False
	flag_display_merged_vertices = False
	flag_display_outside_normales = False
	flag_display_inside_normales = False
	flag_display_sides_normales = False
	flag_compute_side_normals = False

	flag_merge_near_vertices = False
	merge_distance = 1e-6
	flag_mouse_moved = False

	# States:
	ui_state = None
	ui_states = None

	UI_STATE_IDLE = 0
	UI_STATE_FOLDING = 1
	UI_STATE_MOUSE_VIEW = 2

	@classmethod
	def init(cls, vtx_decl_2d, program_2d):

		cls.vs_decl = hg.VertexLayout()
		cls.vs_decl.Begin()
		cls.vs_decl.Add(hg.A_Position, 3, hg.AT_Float)
		cls.vs_decl.Add(hg.A_Normal, 3, hg.AT_Uint8, True, True)
		cls.vs_decl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
		cls.vs_decl.End()

		# Affichage lignes (folds)
		cls.vtx_line_decl = vtx_decl_2d
		cls.line_program = program_2d

		cls.cube_mdl = hg.CreateCubeModel(cls.vs_decl, 0.5, 0.5, 0.5)
		cls.ground_mdl = hg.CreateCubeModel(cls.vs_decl, 50, 0.01, 50)
		cls.shader_outside = hg.LoadProgramFromAssets("shaders/mdl_outside")
		cls.shader_inside = hg.LoadProgramFromAssets("shaders/mdl_inside")
		cls.shader_side = hg.LoadProgramFromAssets("shaders/mdl_side")

		cls.camera = ICamera()

		cls.empty_cam_pos = hg.Vec3(0, 1, -10)
		cls.empty_cam_rot = hg.Vec3(0, 0, 0)
		cls.camera.SetPos(cls.empty_cam_pos)
		cls.camera.SetRot(cls.empty_cam_rot)

		cls.cursor_position = hg.Vec2(0, 0)

		cls.shape_pos = hg.Vec3(0, 0, 0)
		cls.shape_rot = hg.Vec3(0, 0, 0)
		cls.model_matrix = hg.TransformationMat4(cls.shape_pos, cls.shape_rot, hg.Vec3(1, 1, 1))
		cls.fold_line_color = hg.Color(1, 0.2, 0.2, 1)
		cls.hover_fold_line_color = hg.Color(1, 0.5, 0.5, 1)
		cls.selected_fold_line_color = hg.Color(1, 0.9, 0.5, 1)

		cls.folds_manifolds = []

		cls.uniform_set_value_list_outside = hg.UniformSetValueList()
		cls.uniform_set_value_list_inside = hg.UniformSetValueList()
		cls.uniform_set_value_list_side = hg.UniformSetValueList()
		cls.uniform_set_texture_list_outside = hg.UniformSetTextureList()
		cls.uniform_set_texture_list_inside = hg.UniformSetTextureList()
		cls.uniform_set_texture_list_side = hg.UniformSetTextureList()

		cls.ui_states = [
			{"id": cls.UI_STATE_IDLE, "function": Draw3D.ui_idle},
			{"id": cls.UI_STATE_FOLDING, "function": Draw3D.ui_mouse_folding},
			{"id": cls.UI_STATE_MOUSE_VIEW, "function": Draw3D.ui_mouse_view}
		]
		cls.ui_state = cls.ui_states[cls.UI_STATE_IDLE]

	@classmethod
	def remove_all(cls):
		cls.current_shape = None

	@classmethod
	def rotate_point(cls, point, axis, angle):
		epsilon = 1e-5
		if abs(angle) < epsilon: return hg.Vec3(point)
		axe = hg.Normalize(axis)
		ep = 1 - epsilon
		cos_angle = max(min(ep, cos(angle)), -ep)
		sin_angle = max(min(ep, sin(angle)), -ep)
		dot_prod = point.x * axe.x + point.y * axe.y + point.z * axe.z
		return hg.Vec3(cos_angle * point.x + sin_angle * (axe.y * point.z - axe.z * point.y) + (1 - cos_angle) * dot_prod * axe.x,
					   cos_angle * point.y + sin_angle * (axe.z * point.x - axe.x * point.z) + (1 - cos_angle) * dot_prod * axe.y,
					   cos_angle * point.z + sin_angle * (axe.x * point.y - axe.y * point.x) + (1 - cos_angle) * dot_prod * axe.z)

	@classmethod
	def rotate_points_idx(cls, points_idx: list, points: list, axis: hg.Vec3, origine: hg.Vec3, angle):
		epsilon = 1e-5
		if abs(angle) < epsilon: return
		axe = hg.Normalize(axis)
		ep = 1 - epsilon
		cos_angle = max(min(ep, cos(angle)), -ep)
		sin_angle = max(min(ep, sin(angle)), -ep)
		for p_idx in points_idx:
			point = points[p_idx] - origine
			dot_prod = point.x * axe.x + point.y * axe.y + point.z * axe.z
			points[p_idx] = (hg.Vec3(cos_angle * point.x + sin_angle * (axe.y * point.z - axe.z * point.y) + (1 - cos_angle) * dot_prod * axe.x,
									 cos_angle * point.y + sin_angle * (axe.z * point.x - axe.x * point.z) + (1 - cos_angle) * dot_prod * axe.y,
									 cos_angle * point.z + sin_angle * (axe.x * point.y - axe.y * point.x) + (1 - cos_angle) * dot_prod * axe.z) + origine)

	@classmethod
	def center_vertices2D(cls, vertices):
		return cls.center_vertices(vertices, False)

	@classmethod
	def center_vertices(cls, vertices, f3d=True):
		v0 = vertices[0]
		if f3d:
			z = v0.z
		else:
			z = 0
		dmin = hg.Vec3(v0.x, v0.y, z)
		dmax = hg.Vec3(v0.x, v0.y, z)

		for vtx in vertices:
			if f3d:
				z = vtx.z
			else:
				z = 0
			dmin.x = min(dmin.x, vtx.x)
			dmin.y = min(dmin.y, vtx.y)
			dmin.z = min(dmin.z, z)
			dmax.x = max(dmax.x, vtx.x)
			dmax.y = max(dmax.y, vtx.y)
			dmax.z = max(dmax.z, z)
		dsize = dmax - dmin
		offset = (dsize * -1) / 2 - dmin

		# Copy vertices:
		centered_vertices = []
		for vtx in vertices:
			if f3d:
				z = vtx.z
			else:
				z = 0
			v = hg.Vec3(vtx.x + offset.x, vtx.y + offset.y, z + offset.z)
			centered_vertices.append(v)
		dmin += offset
		dmax += offset
		return centered_vertices, dmin, dmax

	@classmethod
	def compute_face_normale(cls, vertices, face):

		"""
		edges_len = []
		n = len(face["idx"])
		for v_idx in range(n):
			edges_len.append({"idx": v_idx, "vec": vertices[face["idx"][(v_idx + 1) % n]] - vertices[face["idx"][v_idx]]})
		edges_len.sort(key=lambda e: hg.Len(e["vec"]), reverse=True)
		face["normal"] = hg.Normalize(hg.Cross(edges_len[0]["vec"], edges_len[1]["vec"]))
		"""

		e = 1e-4
		if "triangles" in face and face["triangles"] is not None:
			f = False
			for triangle in face["triangles"]:
				v = vertices[triangle[0]]
				v1 = vertices[triangle[2]] - v
				v2 = vertices[triangle[1]] - v


				if hg.Len(v1) < e:
					v = vertices[triangle[2]]
					v1 = vertices[triangle[1]] - v
					v2 = vertices[triangle[0]] - v
				prod_vec = hg.Cross(hg.Normalize(v2), hg.Normalize(v1))
				v1_l = hg.Len(v1)
				v2_l = hg.Len(v2)
				pv_l = hg.Len(prod_vec)
				if v1_l > e and v2_l > e and pv_l > e:
					face["normal"] = hg.Normalize(prod_vec)
					f = True
					break
			if not f:
				face["normal"] = hg.Vec3(0, 0, 0)
		else:
			face["normal"] = hg.Vec3(0, 0, 0)

	@classmethod
	def compute_face_center(cls, vertices, face):
		center = hg.Vec3(0,0,0)
		n = len(face["idx"])
		for idx in face["idx"]:
			center += vertices[idx]
		face["center"] = center / n

	@classmethod
	def compute_vertex_faces_links(cls, n, faces):
		vertex_faces_links = []
		for v_idx in range(n):
			vertex_faces_links.append([])
			for f_idx in range(len(faces)):
				face = faces[f_idx]
				for vf_idx in face["idx"]:
					if vf_idx == v_idx:
						vertex_faces_links[v_idx].append(f_idx)
		return vertex_faces_links

	@classmethod
	def compute_vertex_faces_holey_links(cls, n, faces):
		vertex_faces_links = []
		for v_idx in range(n):
			vertex_faces_links.append({})
			for f_idx in range(len(faces)):
				face = faces[f_idx]
				for part_idx in range(len(face["holey_idx"])):
					part = face["holey_idx"][part_idx]
					for vf_idx in part:
						if vf_idx == v_idx:
							if not f_idx in vertex_faces_links[v_idx]:
								vertex_faces_links[v_idx][f_idx] = []
							vertex_faces_links[v_idx][f_idx].append(part_idx)
		return vertex_faces_links

	@classmethod
	def compute_smooth_normales(cls, shape):
		shape["smooth_normales"] = []
		if cls.flag_generate_holes:
			faces = shape["total_faces_holey"]
			vertex_faces_links = cls.compute_vertex_faces_holey_links(len(shape["total_vertices_holey"]), faces)
		else:
			faces = shape["total_faces"]
			vertex_faces_links = cls.compute_vertex_faces_links(len(shape["total_vertices"]), faces)

		for links in vertex_faces_links:
			nrm = hg.Vec3(0, 0, 0)
			for f_idx in links:
				nrm += faces[f_idx]["normal"]
			shape["smooth_normales"].append(hg.Normalize(nrm))

	@classmethod
	def compute_merge_vertices(cls, vertices):
		kill_idx = []
		kill_idx_links = []
		for v_idx0 in range(len(vertices)):
			if v_idx0 not in kill_idx:
				replace_list = []
				v0 = vertices[v_idx0]
				for v_idx1 in range(len(vertices)):
					if v_idx1 != v_idx0 and (v_idx1 not in kill_idx):
						v1 = vertices[v_idx1]
						if hg.Len(v1 - v0) < cls.merge_distance:
							kill_idx.append(v_idx1)
							replace_list.append(v_idx1)
				if len(replace_list) > 0:
					kill_idx_links.append({"main": v_idx0, "replace": replace_list})
		return kill_idx_links

	@classmethod
	def merge_vertices(cls, shape):
		if "merged_vertices" in shape:
			for replace in shape["merged_vertices"]:
				for face in shape["total_faces"]:
					for f_idx in range(len(face["idx"])):
						if face["idx"][f_idx] in replace["replace"]:
							face["idx"][f_idx] = replace["main"]
					if "triangles" in face and face["triangles"] is not None:
						for triangle in face["triangles"]:
							for t_idx in range(3):
								if triangle[t_idx] in replace["replace"]:
									triangle[t_idx] = replace["main"]

	@classmethod
	def merge_vertices_holey(cls,shape):
		if "merged_vertices_holey" in shape:
			for replace in shape["merged_vertices_holey"]:
				for face in shape["total_faces"]:
					for part in face["holey_idx"]:
						for f_idx in range(len(part)):
							if part[f_idx] in replace["replace"]:
								part[f_idx] = replace["main"]
					if "holey_triangles" in face and face["holey_triangles"] is not None:
						for triangles in face["holey_triangles"]:
							for triangle in triangles:
								for t_idx in range(3):
									if triangle[t_idx] in replace["replace"]:
										triangle[t_idx] = replace["main"]

	@classmethod
	def make_flat_material(cls, vertices, material):
		# print("---- Material: " + material["name"])
		material["vertices_flat"] = []
		material["normales_flat"] = []
		material["faces_flat"] = []
		material["uv_flat"] = []
		for face in material["faces"]:
			# Separate faces vertices:
			face_flat = {"idx": [], "triangles": []}
			face_idx_remap = {}
			for v_idx in face["idx"]:
				vf_idx = len(material["vertices_flat"])
				face_flat["idx"].append(vf_idx)
				face_idx_remap[v_idx] = vf_idx
				material["vertices_flat"].append(vertices[material["vertices"][v_idx]])
				material["uv_flat"].append(material["uv"][v_idx])
				material["normales_flat"].append(face["normal"])
			# Remap triangles indexes:
			if "triangles" in face and face["triangles"] is not None:
				for triangle in face["triangles"]:
					triangle_flat = []
					for t_idx in triangle:
						triangle_flat.append(face_idx_remap[t_idx])
					face_flat["triangles"].append(triangle_flat)
			material["faces_flat"].append(face_flat)

	@classmethod
	def compute_faces_matrices(cls, shape):
		v_org = shape["folded_vertices"]
		v_trans = shape["vertices3D"]
		azo = hg.Vec3(0, 0,-1)
		n = len(v_org)
		for face in shape["faces"]:
			center_org = hg.Vec3(0, 0, 0)
			center_trans = hg.Vec3(0, 0, 0)
			nv = len(face["idx"])
			ax_idx = 0
			edge_size_max = 0
			for v_idx in range(nv):
				idx = face["idx"][v_idx]
				po = v_org[idx]
				edge_size = hg.Len(v_org[face["idx"][(v_idx + 1) % nv]] - po)
				if edge_size > edge_size_max:
					edge_size_max = edge_size
					ax_idx = v_idx

				pt = v_trans[idx]
				center_org.x += po.x
				center_org.y += po.y
				center_trans += pt
			center_org /= nv
			center_trans /= nv

			axo = hg.Normalize(v_org[face["idx"][(ax_idx + 1) % nv]] - v_org[face["idx"][ax_idx]])

			axo = hg.Vec3(axo.x, axo.y, 0)
			rot_o = hg.Mat3()
			hg.SetAxises(rot_o, axo, hg.Cross(azo, axo), azo)
			face["matrix_org"] = hg.InverseFast(hg.TransformationMat4(center_org, rot_o))

			axt = hg.Normalize(v_trans[face["idx"][(ax_idx + 1) % nv]] - v_trans[face["idx"][ax_idx]])
			rot_t = hg.Mat3()
			hg.SetAxises(rot_t, axt, hg.Cross(face["normal"], axt), face["normal"])
			face["matrix_folded"] = hg.TransformationMat4(center_trans, rot_t)

	@classmethod
	def compute_folded_holeys(cls, shape):
		n = len(shape["holey_vertices"])
		folded_holey_vertices = [None] * n
		v = shape["holey_vertices"]
		computed_vertices = [False] * n
		for face in shape["faces"]:
			for holey in face["holey_idx"]:
				for idx in holey:
					if not computed_vertices[idx]:
						p = v[idx]
						p = face["matrix_org"] * hg.Vec3(p.x, p.y, 0)
						folded_holey_vertices[idx] = face["matrix_folded"] * p
						computed_vertices[idx] = True
		return folded_holey_vertices

	@classmethod
	def rotate_faces(cls, shape, idx0, idx1, alpha):
		n = len(shape["vertices3D"])  # folded_vertices
		rot_idx = []
		pa = shape["vertices3D"][idx0]
		pb = shape["vertices3D"][idx1]
		while idx0 != idx1:
			rot_idx.append(idx0)
			idx0 = (idx0 + 1) % n
		rot_idx.pop(0)
		axis = pb - pa
		cls.rotate_points_idx(rot_idx, shape["vertices3D"], axis, pa, alpha)

		# Rotate faces normales:
		flags_faces = [False] * len(shape["faces"])
		for idx in rot_idx:
			for f_idx in shape["vertex_faces_links"][idx]:
				if not flags_faces[f_idx]:
					face = shape["faces"][f_idx]
					face["normal"] = hg.Normalize(cls.rotate_point(face["normal"], axis, alpha))
					flags_faces[f_idx] = True

	@classmethod
	def extrude_vertices(cls, vertices, links, faces, thickness, uv):
		extruded_vertices = []
		extruded_uv = []
		for v_idx in range(len(vertices)):
			normal = hg.Vec3(0, 0, 0)
			dist = 0
			for face_idx in links[v_idx]:
				normal = normal + faces[face_idx]["normal"]
			if hg.Len(normal) > 1e-6:
				normal = hg.Normalize(normal)
				dot = hg.Dot(faces[links[v_idx][0]]["normal"], normal)
				if abs(dot) < 1e-6:
					dist = 0
				else:
					dist = thickness / dot
			extruded_vertices.append(vertices[v_idx] - normal * dist)
			uv_ext = uv[v_idx]
			extruded_uv.append(hg.Vec2(uv_ext))
		return extruded_vertices, extruded_uv

	@classmethod
	def extrude_holey_vertices(cls, vertices, links, faces, thickness, uv):
		extruded_vertices = []
		extruded_uv = []
		for v_idx in range(len(vertices)):
			normal = hg.Vec3(0, 0, 0)
			dist = 0
			for f_idx in links[v_idx]:
				normal = normal + faces[f_idx]["normal"]
			if hg.Len(normal) > 1e-6:
				normal = hg.Normalize(normal)
				dot = hg.Dot(faces[next(iter(links[v_idx]))]["normal"], normal)
				if abs(dot) < 1e-6:
					dist = 0
				else:
					dist = thickness / dot
			extruded_vertices.append(vertices[v_idx] - normal * dist)
			uv_ext = uv[v_idx]
			extruded_uv.append(hg.Vec2(uv_ext))
		return extruded_vertices, extruded_uv

	@classmethod
	def generate_inside_faces(cls, faces, flag_holes):
		inside_faces = []
		for face_idx in range(len(faces)):
			face = faces[face_idx]
			i_face = Draw2D.create_new_face()
			i_face["normal"] = face["normal"] * -1
			for v_idx in face["idx"]:
				i_face["idx"].append(v_idx)  # +n
			if "triangles" in face and face["triangles"] is not None:
				for triangle in face["triangles"]:
					e_tri = []
					for t_idx in range(len(triangle) - 1, -1, -1):
						e_tri.append(triangle[t_idx])  # +n
					i_face["triangles"].append(e_tri)

			if flag_holes:
				i_face["holey_idx"] = []
				for part in face["holey_idx"]:
					i_part = []
					for v_idx in part:
						i_part.append(v_idx)
					i_face["holey_idx"].append(i_part)
				if "holey_triangles" in face and face["holey_triangles"] is not None:
					i_face["holey_triangles"] = []
					for triangles in face["holey_triangles"]:
						e_tris = []
						for triangle in triangles:
							try:
								e_tris.append([triangle[2], triangle[1], triangle[0]])  # +n
							except:
								print("ERROR")
						i_face["holey_triangles"].append(e_tris)

			inside_faces.append(i_face)
		return inside_faces

	@classmethod
	def generate_side_faces(cls, shape):
		n = len(shape["vertices3D"])
		side_uv = [None] * (n * 2)
		side_faces = []
		for v_idx in range(n):
			s_face = Draw2D.create_new_face()
			v2 = (v_idx + 1) % n
			s_face["idx"] = [v_idx + n, v2 + n, v2, v_idx]
			s_face["triangles"].append([v_idx + n, v2 + n, v2])
			s_face["triangles"].append([v_idx + n, v2, v_idx])
			for f_idx in shape["vertex_faces_links"][v_idx]:
				face = shape["faces"][f_idx]
				if v2 in face["idx"]:
					ax0 = hg.Normalize(shape["vertices3D"][v2] - shape["vertices3D"][v_idx])
					ax1 = hg.Normalize(shape["inside_vertices"][v2] - shape["inside_vertices"][v_idx])
					ax = (ax0 + ax1) * 0.5
					s_face["normal"] = hg.Normalize(hg.Cross(ax, face["normal"]))
			side_faces.append(s_face)
			side_uv[v_idx] = hg.Vec2(0, 0)
			side_uv[v_idx + n] = hg.Vec2(0, 0)
		return side_faces, side_uv

	@classmethod
	def generate_side_faces_holey(cls, shape, vertices):
		n = len(shape["folded_holey_vertices"])
		side_uv = [None] * (n * 2)
		side_faces = []
		v = shape["holey_vertices"]
		# Lonely edges listing:
		edges_count = {}
		for face in shape["faces"]:
			for part in face["holey_idx"]:
				for idx in range(len(part)):
					edge = [part[idx], part[(idx + 1) % len(part)]]
					hash_edge = [edge[0], edge[1]]
					hash_edge.sort()
					hash = int(hash_edge[0] * 1000000 + hash_edge[1])
					if not hash in edges_count:
						edges_count[hash] = [edge, 1]
					else:
						edges_count[hash][1] += 1
		lonely_edges = []
		for k, edge in edges_count.items():
			if edge[1] == 1:
				lonely_edges.append(edge[0])

		for edge in lonely_edges:
			s_face = Draw2D.create_new_face()
			s_face["holey_idx"] = []
			s_face["holey_triangles"] = []
			v1 = edge[0]
			v2 = edge[1]
			s_face["holey_idx"].append([v1 + n, v2 + n, v2, v1])
			s_face["holey_triangles"].append([[v1 + n, v2 + n, v2], [v1 + n, v2, v1]])
			s_face["idx"] = s_face["holey_idx"][0]
			s_face["triangles"] = s_face["holey_triangles"][0]

			for f_idx in shape["vertex_faces_holey_links"][v1]:
				face = shape["faces"][f_idx]
				for part in face["holey_idx"]:
					if v1 in part and v2 in part:
						ax0 = hg.Normalize(shape["folded_holey_vertices"][v2] - shape["folded_holey_vertices"][v1])
						ax1 = hg.Normalize(shape["inside_vertices_holey"][v2] - shape["inside_vertices_holey"][v1])
						ax = (ax0 + ax1) * 0.5
						s_face["normal"] = hg.Normalize(hg.Cross(ax, face["normal"]))

			side_faces.append(s_face)
			side_uv[v1] = hg.Vec2(0, 0)
			side_uv[v1 + n] = hg.Vec2(0, 0)
			side_uv[v2] = hg.Vec2(0, 0)
			side_uv[v2 + n] = hg.Vec2(0, 0)
		return side_faces, side_uv

	@classmethod
	def convert_to_material_face(cls, face):
		if cls.flag_generate_holes and "holey_idx" in face:
			sub_faces = []
			for part_idx in range(len(face["holey_idx"])):
				sub_faces.append({"idx": face["holey_idx"][part_idx], "triangles": face["holey_triangles"][part_idx], "normal": face["normal"]})
			return sub_faces
		else:
			return [{"idx": face["idx"], "triangles": face["triangles"], "normal": face["normal"]}]

	@classmethod
	def make_shape_materials(cls, outside_faces, inside_faces, side_faces, outside_vertices, total_vertices, uv_outside, uv_inside, uv_side):
		outside_mat_faces = []
		inside_mat_faces = []
		side_mat_faces = []
		for face in outside_faces:
			outside_mat_faces = outside_mat_faces + cls.convert_to_material_face(face)
		for face in inside_faces:
			inside_mat_faces = inside_mat_faces + cls.convert_to_material_face(face)
		for face in side_faces:
			side_mat_faces = side_mat_faces + cls.convert_to_material_face(face)


		materials = [
			{"name": "outside",
			 "faces": outside_mat_faces,
			 "vertices": [i for i in range(0, len(outside_vertices))],
			 "uv": uv_outside,
			 "texture_filename": "",
			 "diffuse": hg.Color.White,
			 "specular": hg.Color.White,
			 "shininess": 50,
			 "ambient": hg.Color.Black,
			 "self_color": hg.Color.Black},

			{"name": "inside",
			 "faces": inside_mat_faces,
			 "vertices": [i for i in range(len(outside_vertices), len(total_vertices))],
			 "uv": uv_inside,
			 "texture_filename": "",
			 "diffuse": hg.Color.White,
			 "specular": hg.Color.White,
			 "shininess": 50,
			 "ambient": hg.Color.Black,
			 "self_color": hg.Color.Black},

			{"name": "side",
			 "faces": side_mat_faces,
			 "vertices": [i for i in range(0, len(total_vertices))],
			 "uv": uv_side,
			 "texture_filename": "",
			 "diffuse": hg.Color.White,
			 "specular": hg.Color.White,
			 "shininess": 50,
			 "ambient": hg.Color.Black,
			 "self_color": hg.Color.Black}
		]
		return materials

	@classmethod
	def make_shape_models(cls, shape):
		models = []

		for idx, material in enumerate(shape["materials"]):
			# print("#---- Model: " + material["name"])
			model_bld = hg.ModelBuilder()
			model_bld.Clear()
			remap_vertices = {}
			for v_idx in range(len(material["vertices_flat"])):
				vertex = hg.Vertex()
				vertex.pos = material["vertices_flat"][v_idx]
				vertex.normal = material["normales_flat"][v_idx]
				vertex.uv0 = material["uv_flat"][v_idx]
				nv_idx = model_bld.AddVertex(vertex)
				if nv_idx != v_idx:
					remap_vertices[v_idx] = nv_idx
			# Export model for debug:
			# print("model_bld.AddVertex(hg.Vec3(%f,%f,%f), hg.Vec3(%f,%f,%f), hg.Vec2(%f,%f))" % (v.x, v.y, v.z, n.x, n.y, n.z, uv.x, uv.y))

			for face in material["faces_flat"]:
				if "triangles" in face and face["triangles"] is not None:
					for triangle in face["triangles"]:
						for ri in range(3):
							if triangle[ri] in remap_vertices:
								triangle[ri] = remap_vertices[triangle[ri]]  # !!! Remove unused vertices at export !!!
						model_bld.AddTriangle(triangle[0], triangle[1], triangle[2])
			# Export model for debug:
			# print("model_bld.AddTriangle(%d, %d, %d)" % (triangle[0], triangle[1], triangle[2]))
			model_bld.EndList(0)
			models.append(model_bld.MakeModel(cls.vs_decl))
		return models

	@classmethod
	def generate_3d(cls, shape, flag_generate_models=True):
		if not shape["closed"]: return
		# Holes:
		if cls.flag_generate_holes and "holey_vertices" in shape:
			flag_holes = True
		else:
			flag_holes = False

		# Recentrage des sommets dépliés:
		shape["vertices3D"], dmin, dmax = cls.center_vertices2D(shape["folded_vertices"])  # folded_vertices

		# Generate UVs:

		shape["materials"] = []
		shape["materials_holey"] = []

		if Backdrops.bitmap is not None:
			bm_pos = Backdrops.bitmap_sprite["position"]
			bm_ratio = Backdrops.bitmap_sprite["width"] / Backdrops.bitmap_sprite["height"]
			bm_s = hg.Vec2(Backdrops.bitmap_sprite["scale"] * bm_ratio, -Backdrops.bitmap_sprite["scale"])
			bm_pos -= bm_s / 2
			cls.model_texture_outside = Backdrops.bitmap_texture
		else:
			bm_s = hg.Vec2(1, 1)
			bm_pos = bm_s * -1 / 2
			cls.model_texture_outside = Backdrops.default_texture

		if Backdrops.inside_texture is not None:
			cls.model_texture_inside = Backdrops.inside_texture
		else:
			cls.model_texture_inside = Backdrops.default_texture

		# UV:
		shape["uv"] = []
		for vtx in shape["folded_vertices"]:
			uv = (vtx - bm_pos) / bm_s
			shape["uv"].append(uv)

		if flag_holes:
			shape["uv_holey"] = []
			for vtx in shape["holey_vertices"]:
				uv = (vtx - bm_pos) / bm_s
				shape["uv_holey"].append(uv)

		# Vertex-faces links:
		shape["vertex_faces_links"] = cls.compute_vertex_faces_links(len(shape["vertices3D"]), shape["faces"])
		if flag_holes:
			shape["vertex_faces_holey_links"] = cls.compute_vertex_faces_holey_links(len(shape["holey_vertices"]), shape["faces"])

		# init faces normales:
		for face in shape["faces"]:
			face["normal"] = hg.Vec3(0, 0, -1)

		# Folding:

		for fold in shape["folds"]:
			if fold["valide"]:
				angle = fold["fold_angle"]

				if fold["segments_intersections"] is None:
					v0_idx = fold["intersections"][0]["idx"]
					v1_idx = fold["intersections"][1]["idx"]
					cls.rotate_faces(shape, v0_idx, v1_idx, angle)

				else:
					a = angle / (4 * fold["round_segments_rendered"])
					ns = len(fold["segments_intersections"])
					for i in range(ns):
						segment = fold["segments_intersections"][i]
						v0_idx = segment[0]["idx"]
						v1_idx = segment[1]["idx"]
						if i == 0 or i == ns - 1:
							cls.rotate_faces(shape, v0_idx, v1_idx, a)
						else:
							cls.rotate_faces(shape, v0_idx, v1_idx, 2 * a)
		# Center:
		shape["vertices3D"], dmin, dmax = cls.center_vertices(shape["vertices3D"])

		# Faces normales:
		#for face in shape["faces"]:
		#	cls.compute_face_normale(shape["vertices3D"], face)

		# Faces matrices: used to fold holey sub-faces
		if flag_holes:
			cls.compute_faces_matrices(shape)
			shape["folded_holey_vertices"] = cls.compute_folded_holeys(shape)

		# Extrusion - Generate vertices:
		shape["total_vertices"] = []
		shape["inside_vertices"], shape["inside_uv"] = cls.extrude_vertices(shape["vertices3D"], shape["vertex_faces_links"], shape["faces"], shape["thickness"], shape["uv"])

		if flag_holes:
			shape["total_vertices_holey"] = []
			shape["inside_vertices_holey"], shape["inside_uv_holey"] = cls.extrude_holey_vertices(shape["folded_holey_vertices"], shape["vertex_faces_holey_links"], shape["faces"], shape["thickness"], shape["uv_holey"])

		# Extrusion - Generate inside faces :
		shape["total_faces"] = []  # Used to compute vertices normals for export
		shape["inside_faces"] = cls.generate_inside_faces(shape["faces"], flag_holes)

		if flag_holes:
			shape["total_faces_holey"] = []

		# Extrusion - Generate sides faces :

		shape["side_faces"], shape["side_uv"] = cls.generate_side_faces(shape)

		if flag_holes:
			shape["side_faces_holey"], shape["side_uv_holey"] = cls.generate_side_faces_holey(shape, shape["folded_holey_vertices"])

		# Extrusion - Concatenate tables:
		inside_vertices_idx = len(shape["vertices3D"])
		shape["total_vertices"] = shape["vertices3D"] + shape["inside_vertices"]
		shape["total_uv"] = shape["uv"] + shape["inside_uv"]
		shape["total_faces"] = shape["inside_faces"] + shape["side_faces"]
		if cls.flag_compute_side_normals:
			for face in shape["side_faces"]:
				cls.compute_face_normale(shape["total_vertices"], face)
		shape["total_faces"] = shape["faces"] + shape["total_faces"]

		if flag_holes:
			inside_vertices_holey_idx = len(shape["folded_holey_vertices"])
			shape["total_vertices_holey"] = shape["folded_holey_vertices"] + shape["inside_vertices_holey"]
			shape["total_uv_holey"] = shape["uv_holey"] + shape["inside_uv_holey"]
			shape["total_faces_holey"] = shape["inside_faces"] + shape["side_faces_holey"]
			if cls.flag_compute_side_normals:
				for face in shape["side_faces_holey"]:
					cls.compute_face_normale(shape["total_vertices_holey"], face)
			shape["total_faces_holey"] = shape["faces"] + shape["total_faces_holey"]

		# Center:
		shape["total_vertices"], dmin, dmax = cls.center_vertices(shape["total_vertices"])
		shape["vertices3D"] = shape["total_vertices"][0:inside_vertices_idx]
		shape["inside_vertices"] = shape["total_vertices"][inside_vertices_idx:len(shape["total_vertices"])]  # Used for "display extruded vertices"

		for face in shape["faces"]:
			cls.compute_face_center(shape["vertices3D"], face)
		for face in shape["inside_faces"]:
			cls.compute_face_center(shape["inside_vertices"], face)
		for face in shape["side_faces"]:
			cls.compute_face_center(shape["total_vertices"], face)
		if "side_faces_holey" in shape:
			for face in shape["side_faces_holey"]:
				cls.compute_face_center(shape["total_vertices_holey"], face)

		if flag_holes:
			shape["total_vertices_holey"], hdmin, hdmax = cls.center_vertices(shape["total_vertices_holey"])
			shape["folded_holey_vertices"] = shape["total_vertices_holey"][0:inside_vertices_holey_idx]
			shape["inside_vertices_holey"] = shape["total_vertices_holey"][inside_vertices_holey_idx:len(shape["total_vertices_holey"])]  # Used for "display extruded vertices"

		# Cleanup - Merge near vertices:

		if "merged_vertices" in shape: del shape["merged_vertices"]
		if "merged_vertices_holey" in shape: del shape["merged_vertices_holey"]

		if cls.flag_merge_near_vertices:
			shape["merged_vertices"] = cls.compute_merge_vertices(shape["total_vertices"])
			cls.merge_vertices(shape)

			if flag_holes:
				shape["merged_vertices_holey"] = cls.compute_merge_vertices(shape["total_vertices_holey"])
				cls.merge_vertices_holey(shape)

		# Separate faces / vertices by materials:
		if flag_holes:
			shape["materials"] = cls.make_shape_materials(shape["faces"], shape["inside_faces"], shape["side_faces_holey"], shape["folded_holey_vertices"], shape["total_vertices_holey"], shape["uv_holey"], shape["inside_uv_holey"], shape["side_uv_holey"])
		else:
			shape["materials"] = cls.make_shape_materials(shape["faces"], shape["inside_faces"], shape["side_faces"], shape["vertices3D"], shape["total_vertices"], shape["uv"], shape["inside_uv"], shape["side_uv"])

		# Separate faces for multi-normales-per vertex:
		for material in shape["materials"]:
			cls.make_flat_material(shape["total_vertices_holey"] if flag_holes else shape["total_vertices"], material)

		# Make model:
		if flag_generate_models:
			shape["model"] = cls.make_shape_models(shape)

		shape["minmax"] = hg.MinMax(hg.Vec3(dmin.x, dmin.y, 0), hg.Vec3(dmax.x, dmax.y, 0))

	@classmethod
	def generate_3D_export(cls, shape):
		Draw2D.generates_shape(shape, cls.flag_generate_holes)
		cls.generate_3d(shape, False)
		cls.compute_smooth_normales(shape)
		if cls.flag_generate_holes and "holey_vertices" in shape:
			shape["vertices_export"] = shape["total_vertices_holey"]
		else:
			shape["vertices_export"] = shape["total_vertices"]

		default_filename = Backdrops.default_texture_filename.split("/")[-1]

		if Backdrops.bitmap_filename != "":
			shape["materials"][0]["texture_filename"] = Backdrops.bitmap_filename.split("/")[-1]
		else:
			shape["materials"][0]["texture_filename"] = default_filename

		if Backdrops.inside_texture_filename != "":
			shape["materials"][1]["texture_filename"] = Backdrops.inside_texture_filename.split("/")[-1]
		else:
			shape["materials"][1]["texture_filename"] = default_filename

		shape["materials"][2]["texture_filename"] = ""

	@classmethod
	def reset_model_matrix(cls):
		cls.UI_rot_angle_Y = 0
		cls.UI_rot_angle_X = 0
		cls.shape_rot = hg.Vec3(0, 0, 0)
		cls.model_matrix = hg.TransformationMat4(cls.shape_pos, cls.shape_rot, hg.Vec3(1, 1, 1))

		cls.uniform_target_tex_outside = hg.MakeUniformSetTexture("model_texture", cls.model_texture_outside, 0)
		cls.uniform_target_tex_inside = hg.MakeUniformSetTexture("model_texture", cls.model_texture_inside, 0)
		cls.uniform_set_value_list_outside.clear()
		cls.uniform_set_value_list_inside.clear()
		cls.uniform_set_value_list_side.clear()
		cls.uniform_set_texture_list_outside.clear()
		cls.uniform_set_texture_list_inside.clear()
		cls.uniform_set_texture_list_side.clear()
		cls.uniform_set_texture_list_outside.push_back(cls.uniform_target_tex_outside)
		cls.uniform_set_texture_list_inside.push_back(cls.uniform_target_tex_inside)
		cls.uniform_set_texture_list_side.push_back(cls.uniform_target_tex_inside)
		c = cls.current_shape["color"]
		cls.uniform_set_value_list_outside.push_back(hg.MakeUniformSetValue("color", hg.Vec4(c.r, c.g, c.b, c.a)))
		cls.uniform_set_value_list_inside.push_back(hg.MakeUniformSetValue("color", hg.Vec4(c.r, c.g, c.b, c.a)))
		cls.uniform_set_value_list_side.push_back(hg.MakeUniformSetValue("color", hg.Vec4(c.r, c.g, c.b, c.a)))
		cls.uniform_set_value_list_outside.push_back(hg.MakeUniformSetValue("ambient_color", hg.Vec4(0.2, 0.2, 0.3, 1)))
		cls.uniform_set_value_list_inside.push_back(hg.MakeUniformSetValue("ambient_color", hg.Vec4(0.2, 0.2, 0.3, 1)))
		cls.uniform_set_value_list_side.push_back(hg.MakeUniformSetValue("ambient_color", hg.Vec4(0.2, 0.2, 0.3, 1)))

	@classmethod
	def display_folds(cls, vid, shape, resolution):
		folds = shape["folds"]

		if len(folds) > 0:
			n = 0
			v = shape["vertices3D"]
			for fold in folds:
				if fold["valide"]: n += 2

			vtx = hg.Vertices(cls.vtx_line_decl, n)
			vtx.Clear()

			i = 0
			sfc = dc.pack_color_RGba(cls.selected_fold_line_color)
			hfc = dc.pack_color_RGba(cls.hover_fold_line_color)
			flc = dc.pack_color_RGba(cls.fold_line_color)
			for fold in folds:
				if fold["valide"]:
					if fold == cls.current_fold:
						color = sfc
					elif fold == cls.hover_fold:
						color = hfc
					else:
						color = flc
					v1 = cls.model_matrix * v[fold["intersections"][0]["idx"]]
					v2 = cls.model_matrix * v[fold["intersections"][1]["idx"]]
					vtx.Begin(i).SetPos(v1).SetColor0(color).End()
					vtx.Begin(i + 1).SetPos(v2).SetColor0(color).End()
					i += 2

			hg.DrawLines(vid, vtx, cls.line_program)

	@classmethod
	def display_extruded_vertices(cls, vid, shape, resolution):
		for v in shape["inside_vertices"]:
			v = cls.model_matrix * v
			p = cls.camera.compute_point_screen_pos(v, resolution)
			if p is not None:
				cls.draw_circle2D(vid, p, 2, hg.Color(1, 1, 0, 1))

	@classmethod
	def display_vertices(cls, vid, shape, resolution):
		for idx, material in enumerate(shape["materials"]):
			for v_idx in range(len(material["vertices_flat"])):
				v = material["vertices_flat"][v_idx]
				v = cls.model_matrix * v
				p = cls.camera.compute_point_screen_pos(v, resolution)
				if p is not None:
					cls.draw_circle2D(vid, p, 3, hg.Color(0, 1, 1, 1))

	@classmethod
	def display_folded_holey_vertices(cls, vid, shape, resolution):
		for v in shape["folded_holey_vertices"]:
			v = cls.model_matrix * v
			p = cls.camera.compute_point_screen_pos(v, resolution)
			if p is not None:
				cls.draw_circle2D(vid, p, 2, hg.Color(0, 1, 0, 1))
		for v in shape["inside_vertices_holey"]:
			v = cls.model_matrix * v
			p = cls.camera.compute_point_screen_pos(v, resolution)
			if p is not None:
				cls.draw_circle2D(vid, p, 2, hg.Color(1, 0, 0, 1))

	@classmethod
	def display_triangles(cls, vid, shape, resolution):
		colors = [hg.Color(1, 0, 0, 1), hg.Color(0, 1, 0, 1), hg.Color(1, 1, 0, 1)]
		for idx, material in enumerate(shape["materials"]):
			v = material["vertices_flat"]
			c = colors[idx]
			for face in material["faces_flat"]:
				if "triangles" in face and face["triangles"] is not None:
					for triangle in face["triangles"]:
						p0 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[0]], resolution)
						p1 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[1]], resolution)
						p2 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[2]], resolution)
						if p0 is not None and p1 is not None and p2 is not None:
							cls.draw_triangle2D(vid, p0, p1, p2, c)

	@classmethod
	def display_normales(cls, vid, faces, resolution):
		color_start = hg.Color(1, 1, 0, 1)
		color_end = hg.Color(1, 0, 0, 0.5)
		cs = dc.pack_color_RGba(color_start)
		ce = dc.pack_color_RGba(color_end)

		lines = []

		for face in faces:
			p0 = cls.camera.compute_point_screen_pos(cls.model_matrix * face["center"], resolution)
			p1 =  cls.camera.compute_point_screen_pos(cls.model_matrix * (face["center"] + face["normal"]), resolution)
			if p0 is not None and p1 is not None:
				lines.append([p0, p1])

		vtx = hg.Vertices(cls.vtx_line_decl, len(lines) * 2)
		vtx.Clear()
		i = 0
		for line in lines:
			vtx.Begin(i).SetPos(hg.Vec3(line[0].x, line[0].y, 1)).SetColor0(cs).End()
			vtx.Begin(i + 1).SetPos(hg.Vec3(line[1].x, line[1].y, 1)).SetColor0(ce).End()
			i += 2

		hg.DrawLines(vid, vtx, cls.line_program)

	@classmethod
	def display_holey_triangles_outside(cls, vid, shape, resolution):
		c = hg.Color(1, 1, 1, 1)
		v = shape["folded_holey_vertices"]
		for face in shape["faces"]:
			if "holey_triangles" in face and face["holey_triangles"] is not None:
				for triangles in face["holey_triangles"]:
					for triangle in triangles:
						p0 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[0]], resolution)
						p1 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[1]], resolution)
						p2 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[2]], resolution)
						if p0 is not None and p1 is not None and p2 is not None:
							cls.draw_triangle2D(vid, p0, p1, p2, c)

	@classmethod
	def display_holey_triangles_inside(cls, vid, shape, resolution):
		c = hg.Color(0.5, 0.5, 0.8, 1)
		v = shape["inside_vertices_holey"]
		for face in shape["inside_faces"]:
			if "holey_triangles" in face and face["holey_triangles"] is not None:
				for triangles in face["holey_triangles"]:
					for triangle in triangles:
						p0 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[0]], resolution)
						p1 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[1]], resolution)
						p2 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[2]], resolution)
						if p0 is not None and p1 is not None and p2 is not None:
							cls.draw_triangle2D(vid, p0, p1, p2, c)

	@classmethod
	def display_holey_triangles_side(cls, vid, shape, resolution):
		c = hg.Color(1, 0.5, 0.5, 1)
		v = shape["total_vertices_holey"]
		for face in shape["side_faces_holey"]:
			if "holey_triangles" in face and face["holey_triangles"] is not None:
				for triangles in face["holey_triangles"]:
					for triangle in triangles:
						p0 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[0]], resolution)
						p1 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[1]], resolution)
						p2 = cls.camera.compute_point_screen_pos(cls.model_matrix * v[triangle[2]], resolution)
						if p0 is not None and p1 is not None and p2 is not None:
							cls.draw_triangle2D(vid, p0, p1, p2, c)

	@classmethod
	def display_merged_vertices(cls, vid, shape, resolution):
		if "merged_vertices" in shape:
			for mv in shape["merged_vertices"]:
				v = cls.model_matrix * shape["vertices3D"][mv["main"]]
				p = cls.camera.compute_point_screen_pos(v, resolution)
				cls.draw_circle2D(vid, p, 4, hg.Color(0, 1, 0, 1))

	@classmethod
	def display_manifolds(cls, vid, shape, resolution):
		folds = shape["folds"]
		cls.folds_manifolds = []
		if len(folds) > 0:
			n = 0
			v = shape["vertices3D"]
			color = cls.fold_line_color
			for fold in folds:
				if fold["valide"]:
					if fold == cls.current_fold:
						color = cls.selected_fold_line_color
					elif fold == cls.hover_fold:
						color = cls.hover_fold_line_color
					else:
						color = cls.fold_line_color
					v1 = cls.model_matrix * v[fold["intersections"][0]["idx"]]
					v2 = cls.model_matrix * v[fold["intersections"][1]["idx"]]
					p3d = v1 + (v2 - v1) / 2
					p = cls.camera.compute_point_screen_pos(p3d, resolution)
					if p is not None:
						cls.folds_manifolds.append({"fold": fold, "pos": p})
						cls.draw_circle2D(vid, p, cls.fold_manifold_size, color)

	@classmethod
	def mouse_rot_model(cls, mouse):
		if mouse.Down(hg.MB_0):
			s = min(1, cls.view_scale / cls.nominal_view_scale)
			mdx = mouse.DtX()
			mdy = mouse.DtY() * 0.25
			if abs(mdx) > 1e-6 or abs(mdy) > 1e-6:
				cls.UI_rot_angle_Y = max(-180, min(180, cls.UI_rot_angle_Y - mdx * s * 0.25))
				cls.UI_rot_angle_X = max(-180, min(180, cls.UI_rot_angle_X + mdy * s ))
				return True
		return False

	@classmethod
	def update_view_scale(cls, mouse, keyboard):
		# Mouse ctrl:
		w = mouse.Wheel()
		dz = 0.1

		"""if w == 0:
			if mouse.Down(hg.MB_2):
				w = mouse.DtY()
				dz = abs(w * 0.01)
		"""
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
			cls.update_camera()
			return True
		return False

	@classmethod
	def reset_camera(cls):
		cls.cursor_position = hg.Vec2(0, 0)

	@classmethod
	def update_camera(cls):
		cls.camera.pos.x = cls.cursor_position.x
		cls.camera.pos.y = cls.cursor_position.y
		cls.camera.pos.z = -cls.view_scale
		cls.camera.rot = hg.Vec3(0, 0, 0)
		cls.camera.near = cls.view_scale * 0.1
		cls.camera.far = cls.view_scale * 2

	@classmethod
	def set_current_shape(cls, shape):
		cls.current_shape = shape
		if shape is None:
			cls.camera.pos = cls.empty_cam_pos
			cls.camera.rot = cls.empty_cam_rot
		else:
			cls.generate_3d(shape)
			mm = shape["minmax"]
			size = mm.mx - mm.mn
			cls.nominal_view_scale = cls.model_view_proportion * size.y / (2 * tan(cls.camera.fov / 2))
			cls.view_scale = cls.nominal_view_scale
			cls.camera.pos = hg.Vec3(0, 0, -cls.view_scale)
			cls.reset_camera()
			cls.update_camera()
			cls.reset_model_matrix()

	@classmethod
	def draw_square2D(cls, vid, p, s_size, color):
		cp = dc.pack_color_RGba(color)
		vtx = hg.Vertices(cls.vtx_line_decl, 8)
		vtx.Clear()
		size = s_size / 2
		p1 = hg.Vec3(p.x - size, p.y - size, 1)
		p2 = hg.Vec3(p.x - size, p.y + size, 1)
		p3 = hg.Vec3(p.x + size, p.y + size, 1)
		p4 = hg.Vec3(p.x + size, p.y - size, 1)

		vtx.Begin(0).SetPos(p1).SetColor0(cp).End()
		vtx.Begin(1).SetPos(p2).SetColor0(cp).End()

		vtx.Begin(2).SetPos(p2).SetColor0(cp).End()
		vtx.Begin(3).SetPos(p3).SetColor0(cp).End()

		vtx.Begin(4).SetPos(p3).SetColor0(cp).End()
		vtx.Begin(5).SetPos(p4).SetColor0(cp).End()

		vtx.Begin(6).SetPos(p4).SetColor0(cp).End()
		vtx.Begin(7).SetPos(p1).SetColor0(cp).End()

		hg.DrawLines(vid, vtx, cls.line_program)

	@classmethod
	def draw_circle2D(cls, vid, c, r, color):
		cp = dc.pack_color_RGba(color)
		numSegments = 32
		stp = 2 * pi / numSegments
		p0 = hg.Vec3(c.x + r, c.y, 1)
		p1 = hg.Vec3(0, 0, 1)
		vtx = hg.Vertices(cls.vtx_line_decl, numSegments * 2 + 2)
		vtx.Clear()

		for i in range(numSegments + 1):
			p1.x = r * cos(i * stp) + c.x
			p1.y = r * sin(i * stp) + c.y
			vtx.Begin(2 * i).SetPos(p0).SetColor0(cp).End()
			vtx.Begin(2 * i + 1).SetPos(p1).SetColor0(cp).End()
			p0.x, p0.y = p1.x, p1.y

		hg.DrawLines(vid, vtx, cls.line_program)

	@classmethod
	def draw_triangle2D(cls, vid, p0, p1, p2, color):
		cp = dc.pack_color_RGba(color)
		vtx = hg.Vertices(cls.vtx_line_decl, 6)
		vtx.Clear()
		vtx.Begin(0).SetPos(hg.Vec3(p0.x, p0.y, 1)).SetColor0(cp).End()
		vtx.Begin(1).SetPos(hg.Vec3(p1.x, p1.y, 1)).SetColor0(cp).End()
		vtx.Begin(2).SetPos(hg.Vec3(p1.x, p1.y, 1)).SetColor0(cp).End()
		vtx.Begin(3).SetPos(hg.Vec3(p2.x, p2.y, 1)).SetColor0(cp).End()
		vtx.Begin(4).SetPos(hg.Vec3(p2.x, p2.y, 1)).SetColor0(cp).End()
		vtx.Begin(5).SetPos(hg.Vec3(p0.x, p0.y, 1)).SetColor0(cp).End()
		hg.DrawLines(vid, vtx, cls.line_program)

	# ================================================== UI FUNCTIONS ================================

	@classmethod
	def set_ui_state(cls, state_id):
		cls.ui_state = cls.ui_states[state_id]

	@classmethod
	def call_ui_state(cls, mouse, keyboard, resolution):
		cls.ui_state["function"](mouse, keyboard, resolution)

	@classmethod
	def get_current_ui_state_id(cls):
		return cls.ui_state["id"]

	@classmethod
	def mouse_drag_view(cls, mouse, resolution):
		if mouse.Down(hg.MB_2):
			mdx = mouse.DtX()
			mdy = mouse.DtY()
			if abs(mdx) > 1e-6 or abs(mdy) > 1e-6:
				md = hg.Vec2(mdx / resolution.y, mdy / resolution.y)
				s = 2 * cls.view_scale * tan(cls.camera.fov / 2)
				cls.cursor_position = cls.cursor_position - md * s
				cls.update_camera()
				return True
		return False

	@classmethod
	def mouse_hover_manifolds(cls, mouse):
		ms = hg.Vec2(mouse.X(), mouse.Y())
		for manifold in cls.folds_manifolds:
			d = hg.Len(ms - manifold["pos"])
			if d <= cls.fold_manifold_size:
				return manifold["fold"]
		return None

	# ================================================== UI STATES ================================

	@classmethod
	def ui(cls, mouse, keyboard, resolution):
		cls.call_ui_state(mouse, keyboard, resolution)

	@classmethod
	def ui_idle(cls, mouse, keyboard, resolution):
		if cls.current_shape is not None:
			cls.hover_fold = cls.mouse_hover_manifolds(mouse)
			cls.update_view_scale(mouse, keyboard)
			if mouse.Down(hg.MB_0):
				if cls.hover_fold is not None:
					cls.current_fold = cls.hover_fold
					cls.hover_fold = None
					cls.set_ui_state(cls.UI_STATE_FOLDING)
				else:
					cls.flag_mouse_moved = False
					cls.set_ui_state(cls.UI_STATE_MOUSE_VIEW)
			elif mouse.Down(hg.MB_1) or mouse.Down(hg.MB_2):
				cls.flag_mouse_moved = False
				cls.set_ui_state(cls.UI_STATE_MOUSE_VIEW)

	@classmethod
	def ui_mouse_folding(cls, mouse, keyboard, resolution):
		if mouse.Down(hg.MB_0):
			md = hg.Vec2(mouse.DtX(), mouse.DtY())
			if md.y != 0:
				a = cls.current_fold["fold_angle"]
				cls.current_fold["fold_angle"] = max(-pi, min(pi, a + pow(md.y, 2) * 0.01 / 180 * pi * (md.y / abs(md.y))))
				Draw2D.generates_shape(cls.current_shape, False) #,cls.flag_generate_holes)
				cls.generate_3d(cls.current_shape)
		else:
			cls.set_ui_state(cls.UI_STATE_IDLE)
			Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
			cls.generate_3d(cls.current_shape)

	@classmethod
	def ui_mouse_view(cls, mouse, keyboard, resolution):
		if cls.update_view_scale(mouse, keyboard) or cls.mouse_rot_model(mouse) or cls.mouse_drag_view(mouse, resolution):
			cls.flag_mouse_moved = True
		cls.shape_rot.x = cls.UI_rot_angle_X / 180 * pi
		cls.shape_rot.y = cls.UI_rot_angle_Y / 180 * pi
		if not mouse.Down(hg.MB_0) and not mouse.Down(hg.MB_1) and not mouse.Down(hg.MB_2):
			if not cls.flag_mouse_moved:
				cls.current_fold = None
			cls.set_ui_state(cls.UI_STATE_IDLE)

	# ===================================================================================================

	@classmethod
	def gui(cls, resolution, main_panel_size):
		wn = "Draw 3D"
		if hg.ImGuiBegin(wn, True, hg.ImGuiWindowFlags_NoMove | hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoCollapse | hg.ImGuiWindowFlags_NoFocusOnAppearing | hg.ImGuiWindowFlags_NoBringToFrontOnFocus):
			hg.ImGuiSetWindowPos(wn, hg.Vec2(0, 20 + main_panel_size.y), hg.ImGuiCond_Always)
			hg.ImGuiSetWindowSize(wn, hg.Vec2(main_panel_size.x, resolution.y - 20 - main_panel_size.y), hg.ImGuiCond_Always)
			hg.ImGuiSetWindowCollapsed(wn, False, hg.ImGuiCond_Once)

			if cls.current_shape is not None:

				dc.panel_part_separator("RENDER SETTINGS")
				f, cls.flag_generate_holes = hg.ImGuiCheckbox("Render holes", cls.flag_generate_holes)
				if f:
					Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
					cls.generate_3d(cls.current_shape)

				dc.panel_part_separator("DISPLAY SETTINGS")

				f, cls.flag_display_vertices = hg.ImGuiCheckbox("Display vertices", cls.flag_display_vertices)
				f, cls.flag_display_extruded_vertices = hg.ImGuiCheckbox("Display extruded vertices", cls.flag_display_extruded_vertices)
				f, cls.flag_display_merged_vertices = hg.ImGuiCheckbox("Display merged vertices", cls.flag_display_merged_vertices)
				if cls.flag_debug:
					f, cls.flag_display_faces = hg.ImGuiCheckbox("Display faces", cls.flag_display_faces)
					f, cls.flag_display_holey_vertices = hg.ImGuiCheckbox("Display holey vertices", cls.flag_display_holey_vertices)
					f, cls.flag_display_triangles = hg.ImGuiCheckbox("Display triangles", cls.flag_display_triangles)
					f, cls.flag_display_outside_holey_triangles = hg.ImGuiCheckbox("Display outside holey triangles", cls.flag_display_outside_holey_triangles)
					f, cls.flag_display_inside_holey_triangles = hg.ImGuiCheckbox("Display inside holey triangles", cls.flag_display_inside_holey_triangles)
					f, cls.flag_display_side_holey_triangles = hg.ImGuiCheckbox("Display side holey triangles", cls.flag_display_side_holey_triangles)
					f, cls.flag_display_outside_normales = hg.ImGuiCheckbox("Display outside faces normales", cls.flag_display_outside_normales)
					f, cls.flag_display_inside_normales = hg.ImGuiCheckbox("Display inside faces normales", cls.flag_display_inside_normales)
					f, cls.flag_display_sides_normales = hg.ImGuiCheckbox("Display sides faces normales", cls.flag_display_sides_normales)
					f, cls.flag_compute_side_normals = hg.ImGuiCheckbox("Compute side_normals using tris", cls.flag_compute_side_normals)
					if f:
						cls.generate_3d(cls.current_shape)

				dc.panel_part_separator("VERTEX")

				f, cls.flag_merge_near_vertices = hg.ImGuiCheckbox("Merge near vertices", cls.flag_merge_near_vertices)
				if f:
					Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
					cls.generate_3d(cls.current_shape)
				if cls.flag_merge_near_vertices and "merged_vertices" in cls.current_shape:
					hg.ImGuiSameLine()
					n = 0
					for mv in cls.current_shape["merged_vertices"]:
						n += len(mv["replace"])
					hg.ImGuiText(str(n) + " deleted")
				f, d = hg.ImGuiDragFloat("Merge distance(nm)", Draw3D.merge_distance * 1e6, 1)
				if f:
					Draw3D.merge_distance = max(1, d) * 1e-6
					Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
					cls.generate_3d(cls.current_shape)

				dc.panel_part_separator("FOLD SETTINGS")

				f, Draw2D.flag_global_folds_settings = hg.ImGuiCheckbox("Set all folds", Draw2D.flag_global_folds_settings)

				if Draw2D.flag_global_folds_settings:
					f, d = hg.ImGuiDragFloat("round radius", Draw2D.round_radius, 0.001, 0.001, 1000)
					if f:
						Draw2D.round_radius = d
						Draw2D.update_folds_segments(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

					f, d = hg.ImGuiInputInt("round segments", Draw2D.round_segments_count)
					if f:
						Draw2D.round_segments_count = max(0, d)
						Draw2D.update_folds_segments(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

					f, d = hg.ImGuiDragFloat("Fold angle", Draw2D.folds_angle / pi * 180, 0.1, -180, 180)
					if f:
						Draw2D.folds_angle = d / 180 * pi
						Draw2D.update_folds_segments(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

				elif cls.current_fold is not None:
					f, d = hg.ImGuiDragFloat("round radius", cls.current_fold["round_radius"], 0.001, 0.001, 1000)
					if f:
						cls.current_fold["round_radius"] = d
						Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

					f, d = hg.ImGuiInputInt("round segments", cls.current_fold["round_segments_count"])
					if f:
						cls.current_fold["round_segments_count"] = max(0, d)
						Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

					f, d = hg.ImGuiDragFloat("Fold angle", cls.current_fold["fold_angle"] / pi * 180, 0.1, -180, 180)
					if f:
						cls.current_fold["fold_angle"] = d / 180 * pi
						Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
						cls.generate_3d(cls.current_shape)

				elif cls.hover_fold is not None:
					hg.ImGuiText("Fold angle: %.2f" % (cls.hover_fold["fold_angle"] / pi * 180))

				dc.panel_part_separator("SHAPE SETTINGS")

				f, d = hg.ImGuiDragFloat("Thickness", cls.current_shape["thickness"], 0.001)
				if f:
					cls.current_shape["thickness"] = max(0.001, d)
					cls.generate_3d(cls.current_shape)
				if hg.ImGuiButton("Unfold"):
					for fold in cls.current_shape["folds"]:
						fold["fold_angle"] = 0
					Draw2D.generates_shape(cls.current_shape, cls.flag_generate_holes)
					cls.generate_3d(cls.current_shape)

			hg.ImGuiEnd()

	@classmethod
	def update_display(cls, vid, resolution):

		# -- Display 3D :
		cls.camera.compute_view_projection(resolution)

		hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, hg.ColorToABGR32(Draw2D.background_color), 1.0, 0)
		hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
		hg.SetViewTransform(vid, cls.camera.view_matrix, cls.camera.projection_matrix)

		if cls.current_shape is not None:
			cls.model_matrix = hg.TransformationMat4(cls.shape_pos, cls.shape_rot, hg.Vec3(1, 1, 1))
			cls.display_folds(vid, cls.current_shape, resolution)
			# vid+=1
			rs = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Less, hg.FC_CounterClockwise)

			if cls.flag_display_faces and "model" in cls.current_shape and len(cls.current_shape["model"]) > 0:
				hg.DrawModel(vid, cls.current_shape["model"][0], cls.shader_outside, cls.uniform_set_value_list_outside, cls.uniform_set_texture_list_outside, cls.model_matrix, rs)
				hg.DrawModel(vid, cls.current_shape["model"][1], cls.shader_inside, cls.uniform_set_value_list_inside, cls.uniform_set_texture_list_inside, cls.model_matrix, rs)
				hg.DrawModel(vid, cls.current_shape["model"][2], cls.shader_side, cls.uniform_set_value_list_side, cls.uniform_set_texture_list_side, cls.model_matrix, rs)

			# -- Display 2D:

			vid += 1
			hg.SetViewClear(vid, 0, 0, 1.0, 0)
			hg.SetViewRect(vid, 0, 0, int(resolution.x), int(resolution.y))
			vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(resolution.x / 2, resolution.y / 2, 0)), resolution.y, 0.1, 100, hg.Vec2(resolution.x / resolution.y, 1))
			hg.SetViewTransform(vid, vs.view, vs.proj)
			cls.display_manifolds(vid, cls.current_shape, resolution)
			if cls.flag_display_merged_vertices: cls.display_merged_vertices(vid, cls.current_shape, resolution)
			if cls.flag_display_extruded_vertices: cls.display_extruded_vertices(vid, cls.current_shape, resolution)
			if cls.flag_display_vertices: cls.display_vertices(vid, cls.current_shape, resolution)
			if cls.flag_debug:
				if cls.flag_display_triangles: cls.display_triangles(vid, cls.current_shape, resolution)
				if "holey_vertices" in cls.current_shape:
					if cls.flag_display_holey_vertices: cls.display_folded_holey_vertices(vid, cls.current_shape, resolution)
					if cls.flag_display_outside_holey_triangles: cls.display_holey_triangles_outside(vid, cls.current_shape, resolution)
					if cls.flag_display_inside_holey_triangles: cls.display_holey_triangles_inside(vid, cls.current_shape, resolution)
					if cls.flag_display_side_holey_triangles: cls.display_holey_triangles_side(vid, cls.current_shape, resolution)
				if cls.flag_display_outside_normales: cls.display_normales(vid, cls.current_shape["faces"], resolution)
				if cls.flag_display_inside_normales: cls.display_normales(vid, cls.current_shape["inside_faces"], resolution)
				if cls.flag_generate_holes and "side_faces_holey" in cls.current_shape:
					if cls.flag_display_sides_normales: cls.display_normales(vid, cls.current_shape["side_faces_holey"], resolution)
				else:
					if cls.flag_display_sides_normales: cls.display_normales(vid, cls.current_shape["side_faces"], resolution)
		else:
			hg.Touch(vid)
