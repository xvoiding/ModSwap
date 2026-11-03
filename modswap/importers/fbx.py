"""FBX importer written from scratch (binary 6.x/7.x incl. 7.5+ 64-bit offsets, and ASCII FBX). No Blender needed.

Reads meshes (with the scene hierarchy transforms baked in), per-corner normals + UVs, materials and their diffuse textures
(files on disk next to the model, or embedded in the FBX). Returns a RawMesh dict that modelio turns into a Model.
"""
import os, re, struct, zlib, io
import numpy as np

MAGIC = b'Kaydara FBX Binary  \x00\x1a\x00'


class Node:
    __slots__ = ('name', 'props', 'children')

    def __init__(self, name, props=None, children=None):
        self.name = name; self.props = props or []; self.children = children or []

    def get(self, name):
        for c in self.children:
            if c.name == name: return c
        return None

    def all(self, name): return [c for c in self.children if c.name == name]

    def val(self, name, default=None):
        c = self.get(name)
        return c.props[0] if c is not None and c.props else default


# ------------------------------------------------------------------------------------------------ binary
_ARR = {'f': ('<f4', 4), 'd': ('<f8', 8), 'l': ('<i8', 8), 'i': ('<i4', 4), 'b': ('?', 1)}


def _parse_binary(data):
    ver = struct.unpack_from('<I', data, 23)[0]; wide = ver >= 7500
    hdr = 24 if wide else 12; fmt = '<QQQ' if wide else '<III'

    def prop(p):
        t = chr(data[p]); p += 1
        if t == 'Y': return struct.unpack_from('<h', data, p)[0], p + 2
        if t == 'C': return bool(data[p]), p + 1
        if t == 'I': return struct.unpack_from('<i', data, p)[0], p + 4
        if t == 'F': return struct.unpack_from('<f', data, p)[0], p + 4
        if t == 'D': return struct.unpack_from('<d', data, p)[0], p + 8
        if t == 'L': return struct.unpack_from('<q', data, p)[0], p + 8
        if t in _ARR:
            n, enc, clen = struct.unpack_from('<III', data, p); p += 12
            dt, sz = _ARR[t]
            raw = data[p:p + clen] if enc == 1 else data[p:p + n * sz]
            if enc == 1: raw = zlib.decompress(raw)
            return np.frombuffer(raw, dtype=dt, count=n), p + (clen if enc == 1 else n * sz)
        if t == 'S':
            n = struct.unpack_from('<I', data, p)[0]; p += 4
            return data[p:p + n].decode('utf-8', 'replace'), p + n
        if t == 'R':
            n = struct.unpack_from('<I', data, p)[0]; p += 4
            return bytes(data[p:p + n]), p + n
        raise ValueError('bad FBX property type %r' % t)

    def node(p):
        end, npr, plen = struct.unpack_from(fmt, data, p)
        nl = data[p + hdr]
        if end == 0: return None, p + hdr + 1
        name = data[p + hdr + 1:p + hdr + 1 + nl].decode('latin1'); q = p + hdr + 1 + nl
        props = []
        for _ in range(npr):
            v, q = prop(q); props.append(v)
        children = []
        while q < end:
            c, q = node(q)
            if c is None: break
            children.append(c)
        return Node(name, props, children), end

    top = []; p = 27
    while p + hdr < len(data):
        n, p = node(p)
        if n is None: break
        top.append(n)
    return Node('', [], top)


# ------------------------------------------------------------------------------------------------ ascii
_num = re.compile(r'^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$')


def _split_vals(s):
    out = []; cur = ''; q = False
    for ch in s:
        if ch == '"': q = not q; cur += ch
        elif ch == ',' and not q: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out


def _conv(v):
    if v.startswith('"'): return v.strip('"')
    if _num.match(v): return int(v) if re.match(r'^[-+]?\d+$', v) else float(v)
    return v


def _parse_ascii(text):
    root = Node('', [], []); stack = [root]; lines = iter(text.splitlines())
    for line in lines:
        s = line.split(';')[0].strip() if not line.strip().startswith('"') else line.strip()
        if not s: continue
        if s == '}': stack.pop() if len(stack) > 1 else None; continue
        m = re.match(r'^([A-Za-z0-9_|:\.]+)\s*:\s*(.*)$', s)
        if not m: continue
        name, rest = m.group(1), m.group(2)
        opens = rest.endswith('{')
        if opens: rest = rest[:-1].strip()
        if name == 'a' and not opens:            # array payload; may continue over several lines
            while rest.endswith(','):
                rest += next(lines).strip()
            arr = np.array([float(x) for x in rest.split(',') if x.strip() != ''], dtype=np.float64)
            stack[-1].props = [arr]; continue
        vals = [_conv(v) for v in _split_vals(rest) if not v.startswith('*')]
        n = Node(name, vals, []); stack[-1].children.append(n)
        if opens: stack.append(n)
    # collapse "Vertices: *N { a: ... }" -> Vertices props=[array]
    def collapse(n):
        for c in n.children: collapse(c)
        if len(n.children) == 1 and n.children[0].name == 'a' and n.children[0].props and isinstance(n.children[0].props[0], np.ndarray):
            n.props = [n.children[0].props[0]]; n.children = []
    collapse(root); return root


def parse_fbx(data):
    if data[:len(MAGIC) - 3] == MAGIC[:-3]: return _parse_binary(data)
    return _parse_ascii(data.decode('utf-8', 'replace'))


# ------------------------------------------------------------------------------------------------ scene
def _name(s):
    s = str(s)
    if '\x00\x01' in s: a, b = s.split('\x00\x01', 1); return a            # binary: "Name\0\1Class"
    return s.split('::', 1)[1] if '::' in s else s


def _props70(n):
    out = {}
    p70 = n.get('Properties70') or n.get('Properties60')
    if p70:
        for p in p70.children:
            if p.props: out[str(p.props[0])] = p.props[4:] if len(p.props) > 4 else p.props[1:]
    return out


def _euler(deg, order=0):
    a = np.radians(np.array(deg, float)); c, s = np.cos(a), np.sin(a)
    Rx = np.array([[1, 0, 0], [0, c[0], -s[0]], [0, s[0], c[0]]])
    Ry = np.array([[c[1], 0, s[1]], [0, 1, 0], [-s[1], 0, c[1]]])
    Rz = np.array([[c[2], -s[2], 0], [s[2], c[2], 0], [0, 0, 1]])
    seq = {0: 'xyz', 1: 'xzy', 2: 'yzx', 3: 'yxz', 4: 'zxy', 5: 'zyx'}.get(int(order), 'xyz')
    R = np.eye(3); M = {'x': Rx, 'y': Ry, 'z': Rz}
    for ax in seq: R = M[ax] @ R            # first letter is applied first
    return R


def _local_matrix(props):
    g = lambda k, d: np.array(props[k][:3], float) if k in props and len(props[k]) >= 3 else np.array(d, float)
    T, R, S = g('Lcl Translation', [0, 0, 0]), g('Lcl Rotation', [0, 0, 0]), g('Lcl Scaling', [1, 1, 1])
    pre, post = g('PreRotation', [0, 0, 0]), g('PostRotation', [0, 0, 0])
    order = props['RotationOrder'][0] if 'RotationOrder' in props and props['RotationOrder'] else 0
    M = np.eye(4); M[:3, :3] = _euler(pre) @ _euler(R, order) @ np.linalg.inv(_euler(post)) @ np.diag(S); M[:3, 3] = T
    return M


def _geo_matrix(props):
    g = lambda k, d: np.array(props[k][:3], float) if k in props and len(props[k]) >= 3 else np.array(d, float)
    M = np.eye(4); M[:3, :3] = _euler(g('GeometricRotation', [0, 0, 0])) @ np.diag(g('GeometricScaling', [1, 1, 1])); M[:3, 3] = g('GeometricTranslation', [0, 0, 0])
    return M


def _layer(geo, kind):
    """-> (values (K,c), index or None, mapping str) for LayerElementNormal / UV / Material"""
    n = geo.get('LayerElement' + kind)
    if n is None: return None
    key = {'Normal': 'Normals', 'UV': 'UV', 'Material': 'Materials'}[kind]
    vals = n.get(key); idx = n.get(key[:-1] + 'Index') if kind != 'UV' else n.get('UVIndex')
    if kind == 'Normal': idx = n.get('NormalsIndex')
    if vals is None or not vals.props: return None
    v = np.asarray(vals.props[0], float if kind != 'Material' else np.int64)
    ix = np.asarray(idx.props[0], np.int64) if (idx is not None and idx.props and len(idx.props[0])) else None
    mp = n.val('MappingInformationType', 'ByPolygonVertex'); ref = n.val('ReferenceInformationType', 'Direct')
    if kind == 'Material': return v, None, mp
    c = 3 if kind == 'Normal' else 2
    return v.reshape(-1, c), (ix if ref == 'IndexToDirect' else None), mp


def _pick(layer, corner, vert, poly):
    """per-corner lookup into a layer element"""
    vals, ix, mp = layer
    sel = {'ByPolygonVertex': corner, 'ByVertice': vert, 'ByVertex': vert, 'ByPolygon': poly, 'ByControllPoint': vert}.get(mp)
    if sel is None: sel = np.zeros_like(corner)         # AllSame
    if ix is not None: sel = ix[np.minimum(sel, len(ix) - 1)]
    return vals[np.minimum(sel, len(vals) - 1)]


def _near_dirs(dirs, depth=3, limit=4000):
    """the given folders, then their sub-folders and the sub-folders of their parent (a model in 'source' with its pictures in a sibling 'textures' folder)"""
    out = []; seen = set()
    def add(d):
        d = os.path.abspath(d)
        if d not in seen and os.path.isdir(d): seen.add(d); out.append(d)
    for d in dirs:
        if d: add(d)
    n = 0
    for d in [x for x in dirs if x]:
        for root in (os.path.abspath(d), os.path.dirname(os.path.abspath(d))):
            if len(root) < 4: continue                                         # never walk a whole drive
            base = root.count(os.sep)
            for dp, dn, _ in os.walk(root):
                if dp.count(os.sep) - base >= depth: dn[:] = []
                add(dp); n += 1
                if n > limit: break
    return out


def _find_image(cands, dirs):
    from PIL import Image
    names = [os.path.basename(str(c).replace('\\', '/')) for c in cands if c]
    for d in _near_dirs(dirs):
        low = {f.lower(): f for f in os.listdir(d)}
        for n in names:
            if n.lower() in low:
                try: return Image.open(os.path.join(d, low[n.lower()])).convert('RGB')
                except Exception: pass
    return None


def load(path, texture_dir=None):
    from PIL import Image
    data = open(path, 'rb').read(); root = parse_fbx(data)
    objects = root.get('Objects'); conns = root.get('Connections')
    if objects is None: raise ValueError('not a valid FBX (no Objects block)')
    objs = {}
    for n in objects.children:
        if n.props and isinstance(n.props[0], (int, np.integer)): objs[int(n.props[0])] = n
    parent = {}; kids = {}; to_model = {}
    for c in (conns.children if conns else []):
        if c.name != 'C' or len(c.props) < 3: continue
        typ, src, dst = c.props[0], int(c.props[1]), int(c.props[2]); prop = c.props[3] if len(c.props) > 3 else ''
        kids.setdefault(dst, []).append((src, typ, prop)); parent.setdefault(src, []).append((dst, typ, prop))
    dirs = [os.path.dirname(os.path.abspath(path)), texture_dir]
    # global settings
    up = '+Y'
    gs = root.get('GlobalSettings')
    if gs:
        p = _props70(gs); ua = int(p['UpAxis'][0]) if p.get('UpAxis') else 1; us = int(p['UpAxisSign'][0]) if p.get('UpAxisSign') else 1
        up = ('+' if us >= 0 else '-') + 'xyz'[ua if ua in (0, 1, 2) else 1].upper()

    world = {}
    def get_world(mid):
        if mid in world: return world[mid]
        n = objs[mid]; M = _local_matrix(_props70(n))
        pm = [d for d, t, _ in parent.get(mid, []) if t == 'OO' and d in objs and objs[d].name == 'Model']
        world[mid] = (get_world(pm[0]) @ M) if pm else M
        return world[mid]

    # materials -> image
    mat_cache = {}
    def material_info(mid):
        if mid in mat_cache: return mat_cache[mid]
        mn = objs[mid]; name = _name(mn.props[1]) if len(mn.props) > 1 else 'mat'
        img = None; col = None
        best = None
        for src, typ, prop in kids.get(mid, []):
            tn = objs.get(src)
            if tn is None or tn.name != 'Texture': continue
            pl = str(prop).lower()
            if any(k in pl for k in ('normal', 'bump', 'specular', 'shininess', 'reflection', 'transparen', 'emissive', 'ambient', 'rough', 'metal', 'occlusion')): continue
            score = 2 if ('diffuse' in pl or 'base' in pl or 'color' in pl) else 1
            if best is None or score > best[0]: best = (score, src, tn)
        if best:
            tn = best[2]; cands = [tn.val('RelativeFilename'), tn.val('FileName')]
            for v in [objs.get(s) for s, t, _ in kids.get(best[1], []) if objs.get(s) is not None and objs[s].name == 'Video']:
                cands += [v.val('RelativeFilename'), v.val('Filename'), v.val('FileName')]
                content = v.get('Content')
                if content is not None and content.props and isinstance(content.props[0], (bytes, bytearray)) and len(content.props[0]) > 16 and img is None:
                    try: img = Image.open(io.BytesIO(content.props[0])).convert('RGB')
                    except Exception: pass
            if img is None: img = _find_image(cands, dirs)
        if img is None:
            p = _props70(mn); c = p.get('DiffuseColor') or p.get('Diffuse')
            if c and len(c) >= 3: col = tuple(int(round(max(0, min(1, float(x))) * 255)) for x in c[:3])
        mat_cache[mid] = (name, img, col)
        return mat_cache[mid]

    P, N, UV, TRIS, TMAT, TPART = [], [], [], [], [], []
    mat_index = {}; mat_names = []; mat_images = []; mat_colors = []; part_names = []; have_normals = True
    voff = 0
    for mid, mn in objs.items():
        if mn.name != 'Model': continue
        geos = [s for s, t, _ in kids.get(mid, []) if t == 'OO' and s in objs and objs[s].name == 'Geometry']
        if not geos: continue
        geo = objs[geos[0]]
        vs = geo.get('Vertices'); pvi = geo.get('PolygonVertexIndex')
        if vs is None or pvi is None or not len(pvi.props): continue
        verts = np.asarray(vs.props[0], float).reshape(-1, 3); pv = np.asarray(pvi.props[0], np.int64)
        ends = np.flatnonzero(pv < 0)
        if len(ends) == 0: continue
        starts = np.concatenate([[0], ends[:-1] + 1]); idx = np.where(pv < 0, ~pv, pv)
        # triangulate (fan); remember corner + polygon of every triangle corner
        sizes = ends - starts + 1
        tc = []; tp = []
        if np.all(sizes == 3):
            tc = (starts[:, None] + np.arange(3)[None]).astype(np.int64); tp = np.arange(len(starts))
        else:
            rows = []; prow = []
            for pi, (s0, sz) in enumerate(zip(starts, sizes)):
                for k in range(1, sz - 1): rows.append((s0, s0 + k, s0 + k + 1)); prow.append(pi)
            tc = np.array(rows, np.int64).reshape(-1, 3); tp = np.array(prow, np.int64)
        if len(tc) == 0: continue
        corner = tc.reshape(-1); vert = idx[corner]; poly = np.repeat(tp, 3)
        W = get_world(mid) @ _geo_matrix(_props70(mn))
        pos = (verts[vert] @ W[:3, :3].T) + W[:3, 3]
        nl = _layer(geo, 'Normal'); ul = _layer(geo, 'UV'); ml = _layer(geo, 'Material')
        if nl is not None:
            nrm = _pick(nl, corner, vert, poly); Wn = np.linalg.inv(W[:3, :3]).T; nrm = nrm @ Wn.T
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        else: nrm = None; have_normals = False
        uv = _pick(ul, corner, vert, poly).copy() if ul is not None else np.zeros((len(corner), 2))
        uv[:, 1] = 1.0 - uv[:, 1]
        # materials of this model, in connection order
        mats = [s for s, t, _ in kids.get(mid, []) if t == 'OO' and s in objs and objs[s].name == 'Material']
        local_to_global = []
        for m_id in mats or [None]:
            if m_id is None: nm, im, col = 'default', None, None
            else: nm, im, col = material_info(m_id)
            key = m_id if m_id is not None else ('none', len(mat_names))
            if key not in mat_index:
                mat_index[key] = len(mat_names); mat_names.append(nm)
                mat_images.append(im); mat_colors.append(col)
            local_to_global.append(mat_index[key])
        if ml is not None and len(ml[0]):
            mv = ml[0]; pm = mv[np.minimum(tp, len(mv) - 1)] if ml[2] == 'ByPolygon' else np.full(len(tp), int(mv[0]))
            tm = np.array(local_to_global)[np.clip(pm, 0, len(local_to_global) - 1)]
        else: tm = np.full(len(tp), local_to_global[0])
        # a negative determinant (mirrored transform) flips the winding
        t3 = np.arange(len(corner)).reshape(-1, 3) + voff
        if np.linalg.det(W[:3, :3]) < 0: t3 = t3[:, [0, 2, 1]]
        P.append(pos); UV.append(uv); N.append(nrm if nrm is not None else np.zeros((len(corner), 3)))
        TRIS.append(t3); TMAT.append(tm); TPART.append(np.full(len(tp), len(part_names))); part_names.append(_name(mn.props[1]) if len(mn.props) > 1 else 'mesh')
        voff += len(corner)
    if not P: raise ValueError('this FBX has no mesh geometry')
    return dict(pos=np.concatenate(P), nrm=np.concatenate(N) if have_normals else None, uv=np.concatenate(UV),
                tris=np.concatenate(TRIS).astype(np.int32), tri_mat=np.concatenate(TMAT).astype(np.int32),
                tri_part=np.concatenate(TPART).astype(np.int32), part_names=part_names,
                images=mat_images, colors=mat_colors, mat_names=mat_names, up=up, per_corner=True)
