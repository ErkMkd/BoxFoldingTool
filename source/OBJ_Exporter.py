# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                  Export OBJ file

# ===========================================================
import harfang as hg

flag_inverse_uv = True
flag_inverse_X = True


def get_material(m_idx, materials):
	mtl = materials[m_idx]
	ambient, diffuse, specular, self_color = mtl["ambient"], mtl["diffuse"], mtl["specular"], mtl["self_color"]
	OBJ_mtl = "newmtl " + mtl["name"] + "\n"
	OBJ_mtl += "Ka %6f %6f %6f\n" % (ambient.r, ambient.g, ambient.b)
	OBJ_mtl += "Kd %6f %6f %6f\n" % (diffuse.r, diffuse.g, diffuse.b)
	OBJ_mtl += "Ks %6f %6f %6f\n" % (specular.r, specular.g, specular.b)
	OBJ_mtl += "Ke %6f %6f %6f\n" % (self_color.r, self_color.g, self_color.b)
	OBJ_mtl += "d 1.0\n"
	OBJ_mtl += "Ni 1.0\n"
	OBJ_mtl += "Ns %6f\n" % mtl["shininess"]
	OBJ_mtl += "illum 2\n"
	if mtl["texture_filename"] != "":
		OBJ_mtl += "map_Kd " + mtl["texture_filename"] + "\n"
	if m_idx < len(materials) - 1: OBJ_mtl += "\n"
	return OBJ_mtl

def convert_flat_to_obj(file_name, obj_name, materials):
	OBJ_script = "# HARFANG 3D \n# Box Folding Tool 1.0\nmtllib " + file_name + ".mtl\no " + obj_name + "\n"
	OBJ_mtl = "# HARFANG 3D \n# Box Folding Tool 1.0\n# Material Count: " + str(len(materials)) + "\n"
	script_v = ""
	script_vt = ""
	script_vn = ""
	script_f = ""
	vidx_of7 = 1
	for m_idx, mtl in enumerate(materials):
		n=len(mtl["vertices_flat"])
		for v_idx in range(n):
			v = mtl["vertices_flat"][v_idx]
			if flag_inverse_X:
				v = v * hg.Vec3(-1, 1, 1)
			vt = mtl["uv_flat"][v_idx]
			vn = mtl["normales_flat"][v_idx]
			if flag_inverse_uv:
				vt = vt * hg.Vec2(1, -1)
			script_v += "v %6f %6f %6f\n" % (v.x, v.y, v.z)
			script_vt += "vt %6f %6f\n" % (vt.x, vt.y)
			script_vn += "vn %6f %6f %6f\n" % (vn.x, vn.y, vn.z)

		script_f += "usemtl " + mtl["name"] + "\n"
		for face in mtl["faces_flat"]:
			if "triangles" in face and face["triangles"] is not None:
				for triangle in face["triangles"]:
					a,b,c = triangle[0] + vidx_of7, triangle[1] + vidx_of7, triangle[2] + vidx_of7
					script_f += "f " + str(a) + "/" + str(a) + "/" + str(a) + " " + str(b) + "/" + str(b) + "/" + str(b) + " " + str(c) + "/" + str(c) + "/" + str(c) + "\n"

		OBJ_mtl += get_material(m_idx, materials)

		vidx_of7 += n

	OBJ_script = OBJ_script + script_v + script_vt + script_vn + script_f
	return OBJ_script, OBJ_mtl


def convert_to_obj(file_name, obj_name, vertices: list, normales: list, materials: list):
	OBJ_script = "# HARFANG 3D \n# Box Folding Tool 1.0\nmtllib " + file_name + ".mtl\no " + obj_name + "\n"
	for v in vertices:
		if flag_inverse_X:
			v = v * hg.Vec3(-1, 1, 1)
		OBJ_script += "v %6f %6f %6f\n" % (v.x, v.y, v.z)
	materials_uvidx = []
	uvidx = 0
	for mtl in materials:
		for uv in mtl["uv"]:
			if flag_inverse_uv:
				uv = uv * hg.Vec2(1, -1)
			OBJ_script += "vt %6f %6f\n" % (uv.x, uv.y)
		materials_uvidx.append(uvidx)
		uvidx += len(mtl["uv"])

	for n in normales:
		OBJ_script += "vn %6f %6f %6f\n" % (n.x, n.y, n.z)

	OBJ_mtl = "# HARFANG 3D \n# Box Folding Tool 1.0\n# Material Count: " + str(len(materials)) + "\n"
	for m_idx, mtl in enumerate(materials):
		OBJ_script += "usemtl " + mtl["name"] + "\n"
		for face in mtl["faces"]:
			for tr in face["triangles"]:
				a, b, c = mtl["vertices"][tr[0]] + 1, mtl["vertices"][tr[1]] + 1, mtl["vertices"][tr[2]] + 1
				ta, tb, tc = tr[0] + materials_uvidx[m_idx] + 1, tr[1] + materials_uvidx[m_idx] + 1, tr[2] + materials_uvidx[m_idx] + 1
				OBJ_script += "f " + str(a) + "/" + str(ta) + "/" + str(a) + " " + str(b) + "/" + str(tb) + "/" + str(b) + " " + str(c) + "/" + str(tc) + "/" + str(c) + "\n"

		OBJ_mtl += get_material(m_idx, materials)

	return OBJ_script, OBJ_mtl
