# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                  Load/Save data conversions

# ===========================================================

import harfang as hg
from math import radians, degrees, floor
import json
import subprocess


def list_to_color(c: list):
	return hg.Color(c[0], c[1], c[2], c[3])


def color_to_list(c: hg.Color):
	return [c.r, c.g, c.b, c.a]


def list_to_vec2(v: list):
	return hg.Vec2(v[0], v[1])


def vec2_to_list(v: hg.Vec2):
	return [v.x, v.y]


def list_to_vec3(v: list):
	return hg.Vec3(v[0], v[1], v[2])


def list_to_vec3_radians(v: list):
	v = list_to_vec3(v)
	v.x = radians(v.x)
	v.y = radians(v.y)
	v.z = radians(v.z)
	return v


def vec3_to_list(v: hg.Vec3):
	return [v.x, v.y, v.z]


def vec3_to_list_degrees(v: hg.Vec3):
	l = vec3_to_list(v)
	l[0] = degrees(l[0])
	l[1] = degrees(l[1])
	l[2] = degrees(l[2])
	return l


def load_json_matrix(file_name):
	file = hg.OpenText(file_name)
	json_script = hg.ReadString(file)
	hg.Close(file)
	if json_script != "":
		script_parameters = json.loads(json_script)
		pos = list_to_vec3(script_parameters["position"])
		rot = list_to_vec3_radians(script_parameters["rotation"])
		return pos, rot
	return None, None


def save_json_matrix(pos: hg.Vec3, rot: hg.Vec3, output_filename):
	script_parameters = {"position": vec3_to_list(pos), "rotation": vec3_to_list_degrees(rot)}
	json_script = json.dumps(script_parameters, indent=4)
	file = hg.OpenWrite(output_filename)
	hg.WriteString(file, json_script)
	hg.Close(file)


def panel_part_separator(title="", spacing=10):
	cpos = hg.ImGuiGetCursorPos()
	hg.ImGuiSetCursorPos(cpos + hg.Vec2(0, spacing))
	hg.ImGuiSeparator()
	cpos = hg.ImGuiGetCursorPos()
	hg.ImGuiSetCursorPos(cpos + hg.Vec2(0, spacing))
	if title != "":
		hg.ImGuiTextColored(hg.Color(0.6, 0.6, 0.6), title)
		cpos = hg.ImGuiGetCursorPos()
		hg.ImGuiSetCursorPos(cpos + hg.Vec2(0, spacing))
		hg.ImGuiSeparator()
		cpos = hg.ImGuiGetCursorPos()
		hg.ImGuiSetCursorPos(cpos + hg.Vec2(0, spacing))


# execute commande line and show stdout:
def run_command(exe):
	def execute_com(command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		return iter(p.stdout.readline, b'')

	for line in execute_com(exe):
		print(line)


def pack_color_RGba(colorRGBA):
	a = colorRGBA.a / 1000
	b = floor(colorRGBA.b * 100)
	return hg.Color(colorRGBA.r, colorRGBA.g, b / 100 + a, 1)
