$input v_color0

#include <bgfx_shader.sh>

void main() {
	vec4 color = v_color0;
	float v = color.b*100.;
	float vf = floor(v);
	color.a = (v-vf)*10.;
	color.b = vf/100.;
	gl_FragColor = color;
}
