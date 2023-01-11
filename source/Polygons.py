"""
 ===========================================================

              - HARFANG® 3D - www.harfang3d.com

                    - Polygons tools  -
            
        Polygon triangulation from Matthias Richter

 ===========================================================
"""

import harfang as hg


def get_thickness_vector_ortho(p1, p2, thickness):
    vw = (p2 - p1)
    if hg.Len(vw) < 1e-4: return None
    vwn = hg.Normalize(vw)
    return hg.Vec2(-vwn.y, vwn.x) * thickness


def get_quad_from_line2D(p1, p2, thickness):
    vw = p2 - p1
    vo = get_thickness_vector_ortho(p1, p2, thickness)
    if vo is None: return None, None, None, None
    p1 = p1 - vo / 2
    p2 = p1 + vo
    p3 = p2 + vw
    p4 = p3 - vo
    return p1, p2, p3, p4


def vector_det(x1, y1, x2, y2):
    return x1 * y2 - y1 * x2


# test wether a and b lie on the same side of the line c->d
def onSameSide(a, b, c, d):
    px, py = d.x - c.x, d.y - c.y
    l = vector_det(px, py, a.x - c.x, a.y - c.y)
    m = vector_det(px, py, b.x - c.x, b.y - c.y)
    return l * m >= 0


def pointInTriangle(p, a, b, c):
    return onSameSide(p, a, b, c) and onSameSide(p, b, a, c) and onSameSide(p, c, a, b)


# test whether any point in vertices (but pqr) lies in the triangle pqr
# note: vertices is *set*, not a list!
def anyPointInTriangle(vertices, p, q, r):
    for k, v in vertices.items():
        if v != p and v != q and v != r and pointInTriangle(v, p, q, r):
            return True
    return False


# returns true if three points make a clockwise turn
def cw(p, q, r):
    return vector_det(q.x - p.x, q.y - p.y, r.x - p.x, r.y - p.y) < 0


# test is the triangle pqr is an "ear" of the polygon
# note: vertices is *set*, not a list!
def isEar(p, q, r, vertices):
    return cw(p, q, r) and not anyPointInTriangle(vertices, p, q, r)


# returns true if three vertices lie on a line
def areCollinear(p, q, r, eps=1e-32):
    return abs(vector_det(q.x - p.x, q.y - p.y, r.x - p.x, r.y - p.y)) <= eps


def reverse_table(arr):
    i, j = 0, len(arr) - 1

    while i < j:
        arr[i], arr[j] = arr[j], arr[i]
        i += 1
        j -= 1


# triangulation by the method of kong
def triangulate(p_vertices):
    vertices = p_vertices

    if len(p_vertices) == 3:
        if cw(vertices[0], vertices[1], vertices[2]):
            return [p_vertices]
        else:
            reverse_table(vertices)
            return [p_vertices]

    elif len(p_vertices) == 4:

        s1 = cw(p_vertices[0], p_vertices[1], p_vertices[2])
        s2 = cw(p_vertices[0], p_vertices[2], p_vertices[3])
        if s1 != s2:
            if not cw(p_vertices[1], p_vertices[2], p_vertices[3]):
                reverse_table(p_vertices)
            return [[p_vertices[1], p_vertices[2], p_vertices[3]], [p_vertices[1], p_vertices[3], p_vertices[0]]]

        elif not s1:
            reverse_table(p_vertices)
        return [[p_vertices[0], p_vertices[1], p_vertices[2]], [p_vertices[0], p_vertices[2], p_vertices[3]]]

    next_idx, prev_idx = [], []
    for i in range(len(vertices)):
        next_idx.append(i + 1)
        prev_idx.append(i - 1)
    next_idx[len(next_idx) - 1], prev_idx[0] = 0, len(prev_idx) - 1

    concave = dict()
    for i, v in enumerate(vertices):
        if not cw(vertices[prev_idx[i]], v, vertices[next_idx[i]]):
            concave[i] = v

    triangles = []
    n_vert, current, skipped, next, prev = len(vertices), 0, 0, 0, 0
    while n_vert > 3:
        next, prev = next_idx[current], prev_idx[current]
        p, q, r = vertices[prev], vertices[current], vertices[next]
        if isEar(p, q, r, concave):
            if not areCollinear(p, q, r):
                triangles.append([p, q, r])
                next_idx[prev], prev_idx[next] = next, prev
                concave[current] = None
                n_vert, skipped = n_vert - 1, 0
        else:
            skipped += 1
            if skipped > n_vert:
                return None
        current = next

    next, prev = next_idx[current], prev_idx[current]
    p, q, r = vertices[prev], vertices[current], vertices[next]
    triangles.append([p, q, r])
    return triangles


def make_polygon_cw(vertices):
    triangulate_polygon(vertices)


def triangulate_polygon(vertices):
    triangles = triangulate(vertices)
    if triangles is None:
        reverse_table(vertices)
        return triangulate(vertices)
    else:
        return triangles


def triangulate_polygon_idx(vertices, polygon):
    triangles = triangulate_idx(vertices, polygon)
    if triangles is None:
        reverse_table(polygon)
        return triangulate_idx(vertices, polygon)
    else:
        return triangles


def polygon_contains(p_vertices, x, y):
    # test if an edge cuts the ray
    def cut_ray(p, q):
        return ((p.y > y and q.y < y) or (p.y < y and q.y > y)) and (x - p.x < (y - p.y) * (q.x - p.x) / (q.y - p.y))

    # test if the ray crosses boundary from interior to exterior.
    # this is needed due to edge cases, when the ray passes through
    # polygon corners
    def cross_boundary(p, q):
        return (p.y == y and p.x > x and q.y < y) or (q.y == y and q.x > x and p.y < y)

    v = p_vertices
    in_polygon = False
    p, q = v[len(v) - 1], v[len(v) - 1]
    for i in range(len(v)):
        p, q = q, v[i]
        if cut_ray(p, q) or cross_boundary(p, q):
            in_polygon = not in_polygon
    return in_polygon


def triangulate_idx(p_vertices, p_polygon):
    vertices = p_vertices
    pl = p_polygon
    if len(p_polygon) == 3:
        if cw(vertices[pl[0]], vertices[pl[1]], vertices[pl[2]]):
            return [p_polygon]
        else:
            return None
    elif len(p_polygon) == 4:

        s1 = cw(vertices[pl[0]], vertices[pl[1]], vertices[pl[2]])
        s2 = cw(vertices[pl[0]], vertices[pl[2]], vertices[pl[3]])
        if s1 != s2:
            if cw(vertices[pl[1]], vertices[pl[2]], vertices[pl[3]]):
                return [[pl[1], pl[2], pl[3]], [pl[1], pl[3], pl[0]]]
            else:
                return None
        elif s1:
            return [[pl[0], pl[1], pl[2]], [pl[0], pl[2], pl[3]]]
        else:
            return None

    next_idx, prev_idx = [], []
    for i in range(len(pl)):
        next_idx.append(i + 1)
        prev_idx.append(i - 1)
    next_idx[len(next_idx) - 1], prev_idx[0] = 0, len(prev_idx) - 1

    concave = dict()
    for i, v in enumerate(pl):
        if not cw(vertices[pl[prev_idx[i]]], vertices[v], vertices[pl[next_idx[i]]]):
            concave[i] = vertices[v]

    triangles = []
    n_vert, current, skipped, next, prev = len(pl), 0, 0, 0, 0
    while n_vert > 3:
        next, prev = next_idx[current], prev_idx[current]
        p, q, r = pl[prev], pl[current], pl[next]
        if isEar(vertices[p], vertices[q], vertices[r], concave):
            if not areCollinear(vertices[p], vertices[q], vertices[r]):
                triangles.append([p, q, r])
                next_idx[prev], prev_idx[next] = next, prev
                concave[current] = None
                n_vert, skipped = n_vert - 1, 0
        else:
            skipped += 1
            if skipped > n_vert:
                return None
        current = next

    next, prev = next_idx[current], prev_idx[current]
    p, q, r = pl[prev], pl[current], pl[next]
    triangles.append([p, q, r])
    return triangles


def flat_polygon3D(p_vertices, polygon):
    v = p_vertices
    p = polygon
    if len(p) < 3: return None
    # normal
    i = 0
    nrm_len = 0
    while nrm_len < 1e-32:
        if i > len(p) - 3: return None
        vx = hg.Normalize((v[p[i]] - v[p[i + 1]]))
        vy = hg.Normalize((v[p[i + 2]] - v[p[i + 1]]))
        nrm = hg.Cross(vx, vy)
        nrm_len = hg.Len(nrm)
        i += 1
    vx = vx * -1
    nrm = hg.Normalize(nrm)
    v0 = v[p[1]]
    vy = hg.Normalize(hg.Cross(vx, nrm))

    v2d = {}
    for i in range(len(p)):
        v1 = v[p[i]] - v0
        v2d[p[i]] = hg.Vector2(hg.Dot(vx, v1), hg.Dot(vy, v1))
    return v2d


def vectors2D_intersection(pA: hg.Vec2, pB: hg.Vec2, pC: hg.Vec2, pD: hg.Vec2, vertex_included=False, vertex_dist_epsilon=1e-6):
    # Returns: Intersection point, AB parameter(0:1), CD parameter(0:1)
    # Set vertex_dist_epsilon function of working precision.
    vAB = pB - pA
    if hg.Len(vAB) < vertex_dist_epsilon:
        return None, None, None

    vCD = pD - pC
    if hg.Len(vCD) < vertex_dist_epsilon:
        return None, None, None

    vCA = pA - pC

    if vertex_included:
        if hg.Len(vCA) < vertex_dist_epsilon:
            return hg.Vec2(pA), 0, 0

        if hg.Len(pD - pA) < vertex_dist_epsilon:
            return hg.Vec2(pA), 0, 1

        if hg.Len(pC - pB) < vertex_dist_epsilon:
            return hg.Vec2(pB), 1, 0

        if hg.Len(pD - pB) < vertex_dist_epsilon:
            return hg.Vec2(pB), 1, 1

    Uab = hg.Normalize(vAB) # / hg.Len(vAB)
    Ucd = hg.Normalize(vCD) # / hg.Len(vCD)
    Uca = hg.Normalize(vCA) # / hg.Len(vCA)

    # Colinéaires ?
    epsilon = 1e-4
    if abs(Uab.x * Ucd.y - Uab.y * Ucd.x) < epsilon: return None, None, None

    vCAp = Ucd * hg.Len(vCA) * hg.Dot(Uca, Ucd)

    vAAp = (vCA * -1) + vCAp
    Uaap = hg.Normalize(vAAp) # / hg.Len(vAAp)

    vAP = Uab * hg.Len(vAAp) / hg.Dot(Uaap, Uab)
    vCP = vCA + vAP

    s1 = hg.Dot(vAP, vAB)
    s2 = hg.Dot(vCP, vCD)
    l1 = hg.Len(vAB)
    l2 = hg.Len(vCD)
    if s1 < 0 or s2 < 0 or l1 < vertex_dist_epsilon or l2 < vertex_dist_epsilon: return None, None, None

    t1 = hg.Len(vAP) / l1
    t2 = hg.Len(vCP) / l2

    # Vertices included in intersection :
    if vertex_included and (-vertex_dist_epsilon < t1 < 1 + vertex_dist_epsilon and -vertex_dist_epsilon < t2 < 1 + vertex_dist_epsilon):
        p = pA + vAP

        if t1 <= 0:
            p = hg.Vec2(pA)
            t1 = 0
        elif t1 >= 1:
            p = hg.Vec2(pB)
            t1 = 1

        if t2 <= 0:
            p = hg.Vec2(pC)
            t2 = 0
        elif t2 >= 1:
            p = hg.Vec2(pD)
            t2 = 1

        return p, t1, t2

    # Vertices not included in intersection:
    elif vertex_dist_epsilon < t1 < 1 - vertex_dist_epsilon and vertex_dist_epsilon < t2 < 1 - vertex_dist_epsilon:
        return pA + vAP, t1, t2

    else:
        return None, None, None


def point_line_distance(p: hg.Vec2, l1: hg.Vec2, l2: hg.Vec2):
    vl = l2 - l1
    ul = hg.Normalize(vl)
    vp = p - l1
    vpp = ul * hg.Dot(ul, vp)
    pp = l1 + vpp
    return hg.Len(p - pp)


def point_edge_distance(p: hg.Vec2, l1: hg.Vec2, l2: hg.Vec2):
    vl = l2 - l1
    if hg.Len(vl)<1e-6:
        return hg.Len(l1-p)
    ul = hg.Normalize(vl)
    vp = p - l1
    vpp = ul * hg.Dot(ul, vp)
    if hg.Dot(vpp, ul) < 0:
        return hg.Len(vp)
    if hg.Len(vpp) / hg.Len(vl) > 1:
        return hg.Len(p - l2)
    pp = l1 + vpp
    return hg.Len(p - pp)


def compute_triangle_area(vertices, triangle):
    # get hypothenuse:
    dmax = 0
    hyp_idx = 0
    for v_idx in range(3):
        d = hg.Len(vertices[triangle[(v_idx + 1) % 3]] - vertices[triangle[v_idx]])
        if d > dmax:
            hyp_idx = v_idx
            dmax = d

    pA = vertices[triangle[hyp_idx]]
    pB = vertices[triangle[(hyp_idx + 1) % 3]]
    pC = vertices[triangle[(hyp_idx + 2) % 3]]
    vAB = pB - pA
    vBC = pC - pB
    vAC = pC - pA
    uAB = hg.Normalize(vAB)

    vACp = uAB * hg.Dot(vAC, uAB)
    pCp = pA + vACp

    dCCp = hg.Len(pCp - pC)
    dACp = hg.Len(pCp - pA)
    dBCp = hg.Len(pCp - pB)
    return dCCp * (dBCp + dACp) / 2


def sort_intersections(vertices1, vertices2, intersections, pol_id):
    if pol_id == 1:
        pol1_edge_idx = "pol1_edge_idx"
        pol2_edge_idx = "pol2_edge_idx"
        pol_confounded_weight = "pol1_confounded_weight"
        pol_inter_idx = "pol1_inter_idx"
        t = "t1"
    else:
        pol1_edge_idx = "pol2_edge_idx"
        pol2_edge_idx = "pol1_edge_idx"
        pol_confounded_weight = "pol2_confounded_weight"
        pol_inter_idx = "pol2_inter_idx"
        t = "t2"

    p1_edges_links = []
    n1 = len(vertices1)
    n2 = len(vertices2)
    for e_idx in range(n1):
        Uedge = hg.Normalize((vertices1[(e_idx + 1) % n1] - vertices1[e_idx]))
        p1_edges_links.append([])
        for intersection in intersections:
            if intersection[pol1_edge_idx] == e_idx:
                p1_edges_links[e_idx].append(intersection)
        ni = len(p1_edges_links[e_idx])
        if ni > 1:
            # Sort confounded vertices (By construction, only 2 vertices can be confounded)
            p1p0 = vertices1[e_idx]
            p1p1 = vertices1[(e_idx + 1) % n1]
            v1 = p1p1 - p1p0
            for i0_idx in range(ni):
                inter0 = p1_edges_links[e_idx][i0_idx]
                p2p0_0 = vertices2[inter0[pol2_edge_idx]]
                p2p1_0 = vertices2[(inter0[pol2_edge_idx] + 1) % n2]
                Ui0 = hg.Normalize(p2p1_0 - p2p0_0)
                ip0 = inter0["vertex"]
                for i1_idx in range(i0_idx + 1, ni):
                    inter1 = p1_edges_links[e_idx][i1_idx]
                    p2p0_1 = vertices2[inter1[pol2_edge_idx]]
                    p2p1_1 = vertices2[(inter1[pol2_edge_idx] + 1) % n2]
                    Ui1 = hg.Normalize(p2p1_1 - p2p0_1)
                    if abs((1 - abs(hg.Dot(Ui0,Ui1)))) < 1e-6: # Only colinear edges can cause confounded intersections
                        cos_edges = abs(hg.Dot(Uedge, Ui0)) # Edges incidence
                        confound_epsilon = cos_edges * 1e-2 + (1-cos_edges) * 1e-5
                        ip1 = inter1["vertex"]
                        l = hg.Len(ip1 - ip0)
                        if l < confound_epsilon:
                            v2 = p2p1_1 - p2p0_1
                            nrm = hg.Vec2(-v2.y, v2.x)
                            if hg.Dot(nrm, v1) > 0:
                                inter0[pol_confounded_weight] = 1
                                inter0[t] = inter1[t]
                            else:
                                inter1[pol_confounded_weight] = 1
                                inter1[t] = inter0[t]
                            break   # -> as long as only 2 vertices can be confounded
            p1_edges_links[e_idx].sort(key=lambda p: (p[t], p[pol_confounded_weight]))
            for inter_idx in range(len(p1_edges_links[e_idx])):
                p1_edges_links[e_idx][inter_idx][pol_inter_idx] = inter_idx
    return p1_edges_links

def invert_polygon_and_edges_links(vertices, edges_links, edge_idx_label, inter_idx_label):
    vertices_reversed = vertices[::-1]
    edges_links_reversed = edges_links[::-1]
    edges_links_reversed = edges_links_reversed[1:] + edges_links_reversed[:1]
    for eidx in range(len(edges_links_reversed)):
        intersections = edges_links_reversed[eidx]
        if len(intersections) > 1:
            intersections.reverse()
        for iidx in range(len(intersections)):
            inter = intersections[iidx]
            inter[edge_idx_label] = eidx
            inter[inter_idx_label] = iidx
    return vertices_reversed, edges_links_reversed

def rebuild_polygon(vertices1, vertices2, edges_links_1, edges_links_2, eid_start, iid_start):
    vertices = []

    pol = {"id": 1, "pol": vertices1, "edges": edges_links_1, "elbl": "pol1_edge_idx", "ilbl": "pol1_inter_idx"}
    pol_mem = {"id": 2, "pol": vertices2, "edges": edges_links_2, "elbl": "pol2_edge_idx", "ilbl": "pol2_inter_idx"}

    pol_id_start = 1
    # Entering or exiting intersection ?
    if iid_start >= 0:
        v = vertices1[(eid_start + 1) % len(vertices1)] - vertices1[eid_start]
        inter = edges_links_1[eid_start][iid_start]
        eidx = inter["pol2_edge_idx"]
        nrm = vertices2[(eidx + 1) % len(vertices2)] - vertices2[eidx]
        nrm.x, nrm.y = nrm.y, -nrm.x
        if hg.Dot(nrm,v) > 0:
            pol, pol_mem = pol_mem, pol
            eid_start = inter[pol["elbl"]]
            iid_start = inter[pol["ilbl"]]
            pol_id_start = 2

    eid = eid_start
    iid = iid_start

    while True:
        if iid >= 0:
            inter = pol["edges"][eid][iid]
            vertices.append(inter["vertex"])
            pol, pol_mem = pol_mem, pol
            eid = inter[pol["elbl"]]
            iid = inter[pol["ilbl"]] + 1
            if iid >= len(pol["edges"][eid]):
                iid = -1
                eid = (eid + 1) % len(pol["pol"])
        else:
            vertices.append(pol["pol"][eid])
            if len (pol["edges"][eid]) > 0:
                iid = 0
            else:
                eid = (eid + 1) % len(pol["pol"])

        if eid == eid_start and iid == iid_start and pol["id"] == pol_id_start:
            break
    return vertices

def is_vertice_polygons(p,polygons):
    for v in polygons:
        for p0 in v:
            if hg.Len(p0-p) < 1e-6:
                return True
    return False

#Subtracts polygon2 to polygon1
#Returns polygons list
def subtract_polygon(vertices1, vertices2, debug = False):
    ct = 0
    n1 = len(vertices1)
    n2 = len(vertices2)
    intersections = []
    for p1idx in range(n1):
        p1a = vertices1[p1idx]
        p1b = vertices1[(p1idx + 1) % n1]
        for p2idx in range(n2):
            p2a = vertices2[p2idx]
            p2b = vertices2[(p2idx + 1) % n2]
            pi, t1, t2 = vectors2D_intersection(p1a, p1b, p2a, p2b, True)
            if pi is not None:
                intersections.append({"pol1_edge_idx": p1idx, "pol2_edge_idx": p2idx, "vertex": pi, "t1": t1, "t2": t2, "pol1_confounded_weight": 0, "pol2_confounded_weight": 0, "pol1_inter_idx": 0, "pol2_inter_idx": 0})
                ct += 1

    # No intersection:
    if ct == 0:
        p = vertices2[0]
        # Polygon2 fully included in polygon1:
        if polygon_contains(vertices1, p.x, p.y):
            for p1idxe in range(n1):
                p0 = vertices1[p1idxe]
                f1 = False
                #find polygon2 entry vertex:
                for p2idxe in range(n2):
                    p1 = vertices2[p2idxe]
                    f2 = False
                    for p2idx in range(n2):
                        p2idx1 = (p2idx + 1) % n2
                        if p2idx != p2idxe and p2idx1 != p2idxe:
                            p2a = vertices2[p2idx]
                            p2b = vertices2[p2idx1]
                            pi, t1, t2 = vectors2D_intersection(p0, p1, p2a, p2b, True)
                            if pi is not None:
                                f2 = True
                                break
                    if not f2:
                        break
                if not f2:
                    for p1idx in range(p1idxe, p1idxe + n1):
                        p1idx0 = p1idx % n1
                        p1idx1 = (p1idx0 + 1) % n1
                        if p1idx0 != p1idxe and p1idx1 != p1idxe:
                            p2a = vertices1[p1idx0]
                            p2b = vertices1[p1idx1]
                            pi, t1, t2 = vectors2D_intersection(p0, p1, p2a, p2b, True)
                            if pi is not None:
                                f1 = True
                                break
                    if not f1:
                        break

            vertices = []
            for vidx in range(p1idxe, p1idxe + n1 + 1):
                vertices.append(vertices1[vidx % n1])
            for vidx in range(p2idxe, p2idxe - n2 - 1, -1):
                vertices.append(vertices2[vidx % n2])
            return True, [vertices]

        p = vertices1[0]
        # Polygon1 fully included in polygon2 (polygon 1 deleted):
        if polygon_contains(vertices2, p.x, p.y):
            return True, None
        # Polygon2 fully not included:
        else:
            return False, [vertices1]
    # Intersections:
    else:
        p1_edges_links = sort_intersections(vertices1, vertices2, intersections, 1)
        p2_edges_links = sort_intersections(vertices2, vertices1, intersections, 2)

        # Invert polygon2 to facilitate the reconstruction path:
        vertices2_reversed, p2_edges_links = invert_polygon_and_edges_links(vertices2, p2_edges_links, "pol2_edge_idx", "pol2_inter_idx")

        polygons = []
        # Search polygon1 entry vertex:

        for eid_start in range(n1):
            p0 = vertices1[eid_start]

            if not polygon_contains(vertices2, p0.x, p0.y) and not is_vertice_polygons(p0, polygons):
                iid_start = -1
                polygon = rebuild_polygon(vertices1, vertices2_reversed, p1_edges_links, p2_edges_links, eid_start, iid_start)
                if len(polygon) > 2: polygons.append(polygon)

            for iid_start in range(len(p1_edges_links[eid_start])):
                if not is_vertice_polygons(p1_edges_links[eid_start][iid_start]["vertex"], polygons):
                    polygon = rebuild_polygon(vertices1, vertices2_reversed, p1_edges_links, p2_edges_links, eid_start, iid_start)
                    if len(polygon) > 2: polygons.append(polygon)


        return True, polygons