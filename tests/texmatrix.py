"""Ground-truth texture tests. A model is generated from a SPEC whose colour at every triangle corner is known (flat colour patches in the pictures, uvs at patch centres), written in
several formats, loaded by ModSwap's real loaders, run through the atlas (what the viewer and the builds use), and every loaded triangle corner is compared with the colour the SOURCE file says
it must have. Triangles are matched by their corner positions, so nothing of ModSwap's own bookkeeping is trusted."""
import os, sys, struct, tempfile, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap import atlas
from modswap.modelio import load_model

GRID = 8                                                                   # a picture = GRID x GRID flat colour patches


def picture(seed, w=256, h=256, mode='RGB'):
    r = np.random.default_rng(seed); cols = r.integers(30, 226, (GRID, GRID, 3)).astype(np.uint8)
    a = np.repeat(np.repeat(cols, h // GRID, 0), w // GRID, 1)
    im = Image.fromarray(a)
    if mode != 'RGB':                                                      # the expected colours are what the converted picture really holds at the patch centres
        im = im.convert(mode); rgb = np.asarray(im.convert('RGB')); cols = rgb[(np.arange(GRID) * (h // GRID) + h // GRID // 2)[:, None], (np.arange(GRID) * (w // GRID) + w // GRID // 2)[None, :]]
    return im, cols


def srgb_tint(rgb, f):
    a = np.asarray(rgb, np.float64) / 255.0; lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4) * np.asarray(f, np.float64)
    out = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.maximum(lin, 0), 1 / 2.4) - 0.055); return np.clip(out, 0, 1) * 255


def wrap_t(t, mode):
    return (1.0 - abs((t % 2.0) - 1.0)) if mode == 'mirror' else min(max(t, 1e-7), 1 - 1e-7) if mode == 'clamp' else t % 1.0


def patch_of(cols, u, v):
    """colour of the patch at uv (v UP, wrap = repeat)"""
    return cols[min(int((1 - (v % 1.0)) * GRID), GRID - 1), min(int((u % 1.0) * GRID), GRID - 1)]


class Spec:
    """n_mat pictures; triangles belong to a material; every corner has a position and a uv that sits at the CENTRE of a random patch (+ an integer tile offset)"""
    def __init__(self, n_tris=240, n_mat=3, seed=1, shared_picture=False, tile=0, sizes=None, share_vertices=False, wrap=None, tint=None, tf=None, mode='RGB'):
        r = np.random.default_rng(seed); self.n_mat = n_mat; self.pics = []; self.skip = set(); self.wrap = wrap or ['repeat'] * n_mat; self.tint = tint or [None] * n_mat; self.tf = tf or [None] * n_mat
        for m in range(n_mat):
            w, h = (sizes[m] if sizes else (256, 256)); im, cols = picture(100 + (0 if shared_picture else m), w, h, mode); self.pics.append((im, cols))
        self.mat = r.integers(0, n_mat, n_tris); self.pos = np.zeros((n_tris, 3, 3)); self.uv = np.zeros((n_tris, 3, 2))
        for t in range(n_tris):
            c = r.uniform(-1, 1, 3); self.pos[t] = c + r.normal(scale=0.03, size=(3, 3))                 # tiny triangle somewhere: unique centroid
            gx, gy = r.integers(0, GRID, 2); self.uv[t] = [((gx + 0.5) / GRID, 1 - (gy + 0.5) / GRID)] * 3 + r.uniform(-0.2 / GRID, 0.2 / GRID, (3, 2))
            if tile: self.uv[t] += r.integers(-tile, tile + 1, 2)
        if share_vertices:                                                                                # triangles of different materials meet at the same positions
            for t in range(1, n_tris, 3): self.pos[t, 0] = self.pos[t - 1, 1]

    def expected(self, t, c):
        m = self.mat[t]; u, v = self.uv[t, c]; vg = 1.0 - v                                  # uv in glTF space (v down), where the texture transform is defined
        if self.tf[m] is not None:
            (ox, oy), rot, (sx, sy) = self.tf[m]; cs, sn = np.cos(rot), np.sin(rot); u, vg = cs * u * sx + sn * vg * sy + ox, -sn * u * sx + cs * vg * sy + oy
        u = wrap_t(u, self.wrap[m]); vg = wrap_t(vg, self.wrap[m]); col = patch_of(self.pics[m][1], u, 1.0 - vg)
        return col if self.tint[m] is None else srgb_tint(col, self.tint[m])


# ------------------------------------------------------------------ writers
def write_obj(spec, d, name='m', tex_sub='', fmt='png', mtl_options=''):
    os.makedirs(os.path.join(d, tex_sub), exist_ok=True); L = ['mtllib %s.mtl' % name]; M = []
    for m, (im, _) in enumerate(spec.pics):
        fn = 'tex%d.%s' % (m, fmt); im.save(os.path.join(d, tex_sub, fn), **({'quality': 95, 'progressive': True} if fmt == 'jpg' else {})); M += ['newmtl mat%d' % m, 'Kd 1 1 1', 'map_Kd %s%s' % (mtl_options, (tex_sub + '/' if tex_sub else '') + fn)]
    open(os.path.join(d, name + '.mtl'), 'w').write('\n'.join(M))
    order = np.argsort(spec.mat, kind='stable'); vi = 1; cur = -1
    for t in order:
        if spec.mat[t] != cur: cur = spec.mat[t]; L.append('usemtl mat%d' % cur)
        for c in range(3): L.append('v %.6f %.6f %.6f' % tuple(spec.pos[t, c]))
        for c in range(3): L.append('vt %.6f %.6f' % tuple(spec.uv[t, c]))
        L.append('f ' + ' '.join('%d/%d' % (vi + c, vi + c) for c in range(3))); vi += 3
    p = os.path.join(d, name + '.obj'); open(p, 'w').write('\n'.join(L)); return p


def write_trimesh(spec, d, ext, tex_sub=''):
    import trimesh
    os.makedirs(d, exist_ok=True); scene = trimesh.Scene()
    for m in range(spec.n_mat):
        ts = np.flatnonzero(spec.mat == m)
        if not len(ts): continue
        V = spec.pos[ts].reshape(-1, 3); UV = spec.uv[ts].reshape(-1, 2); F = np.arange(len(V)).reshape(-1, 3)
        me = trimesh.Trimesh(vertices=V, faces=F, process=False); me.visual = trimesh.visual.TextureVisuals(uv=UV, material=trimesh.visual.material.PBRMaterial(baseColorTexture=spec.pics[m][0], name='mat%d' % m) if ext in ('.glb', '.gltf') else trimesh.visual.material.SimpleMaterial(image=spec.pics[m][0], name='mat%d' % m))
        scene.add_geometry(me, geom_name='part%d' % m, node_name='part%d' % m)
    p = os.path.join(d, 'm' + ext)
    if ext == '.dae': scene.export(p, file_type='dae')
    else: scene.export(p)
    return p


class L(int): pass                                                         # an FBX 64-bit id


def _fbx_tree(spec, tex_sub, uv_map='ByPolygonVertex+IndexToDirect', mat_map='ByPolygon', multi_model=False, xform=None, spell_control='ByControlPoint'):
    """-> (nodes, world position function). Nodes are (name, [props], [children]); numpy arrays are FBX arrays."""
    A = lambda vals, dt: np.asarray(vals, dt)
    n = len(spec.mat); props70 = lambda *p: ('Properties70', [], [('P', list(x), []) for x in p])
    def geometry(gid, ts, mat_local):
        V = spec.pos[ts].reshape(-1, 3); k = len(ts); pvi = []
        for t in range(k): pvi += [3 * t, 3 * t + 1, ~(3 * t + 2)]
        uvs = spec.uv[ts].reshape(-1, 2); kind, _, ref = uv_map.partition('+')
        if kind == 'ByControlPoint': layer = [('MappingInformationType', [spell_control], []), ('ReferenceInformationType', ['Direct'], []), ('UV', [A(uvs.reshape(-1), '<f8')], [])]
        elif ref == 'IndexToDirect': layer = [('MappingInformationType', [kind], []), ('ReferenceInformationType', ['IndexToDirect'], []), ('UV', [A(uvs.reshape(-1), '<f8')], []), ('UVIndex', [A(np.arange(len(uvs)), '<i4')], [])]
        else: layer = [('MappingInformationType', [kind], []), ('ReferenceInformationType', ['Direct'], []), ('UV', [A(uvs.reshape(-1), '<f8')], [])]
        mats = ('AllSame', [0]) if mat_map == 'AllSame' else ('ByPolygon', mat_local)
        return ('Geometry', [L(gid), 'Geometry::g%d' % gid, 'Mesh'], [('Vertices', [A(V.reshape(-1), '<f8')], []), ('PolygonVertexIndex', [A(pvi, '<i4')], []),
                ('LayerElementUV', [0], [('Version', [101], []), ('Name', [''], [])] + layer),
                ('LayerElementMaterial', [0], [('Version', [101], []), ('MappingInformationType', [mats[0]], []), ('ReferenceInformationType', ['IndexToDirect'], []), ('Materials', [A(mats[1], '<i4')], [])])])
    objs = []; conn = []
    for m in range(spec.n_mat):
        objs.append(('Material', [L(100 + m), 'Material::mat%d' % m, ''], []))
        objs.append(('Texture', [L(200 + m), 'Texture::t%d' % m, ''], [('Type', ['TextureVideoClip'], []), ('FileName', ['C:/author/%s/tex%d.png' % (tex_sub, m)], []), ('RelativeFilename', ['%s/tex%d.png' % (tex_sub, m)], []), ('WrapModeU', [1 if spec.wrap[m] == 'clamp' else 0], []), ('WrapModeV', [1 if spec.wrap[m] == 'clamp' else 0], [])]))
        conn.append(('C', ['OP', L(200 + m), L(100 + m), 'DiffuseColor'], []))
    xf = []
    if xform:
        T, rz, S = xform; xf = [('Lcl Translation', 'Lcl Translation', '', 'A', float(T[0]), float(T[1]), float(T[2])), ('Lcl Rotation', 'Lcl Rotation', '', 'A', 0.0, 0.0, float(rz)), ('Lcl Scaling', 'Lcl Scaling', '', 'A', float(S), float(S), float(S))]
    def model(mid): return ('Model', [L(mid), 'Model::m%d' % mid, 'Mesh'], [props70(*xf)])
    if multi_model:
        for m in range(spec.n_mat):
            ts = np.flatnonzero(spec.mat == m)
            if not len(ts): continue
            objs += [geometry(1000 + m, ts, [0] * len(ts)), model(2000 + m)]
            conn += [('C', ['OO', L(1000 + m), L(2000 + m)], []), ('C', ['OO', L(100 + m), L(2000 + m)], [])]
    else:
        objs += [geometry(1000, np.arange(n), [int(x) for x in spec.mat]), model(2000)]; conn.append(('C', ['OO', L(1000), L(2000)], []))
        for m in range(spec.n_mat): conn.append(('C', ['OO', L(100 + m), L(2000)], []))
    if xform:
        T, rz, S = xform; c, sn = np.cos(np.radians(rz)), np.sin(np.radians(rz)); R = np.array([[c, -sn, 0], [sn, c, 0], [0, 0, 1]])
        world = lambda P: (np.asarray(P) @ R.T) * S + np.asarray(T)
    else: world = lambda P: np.asarray(P)
    top = [('FBXHeaderExtension', [], [('FBXVersion', [7400], [])]), ('GlobalSettings', [], [props70(('UpAxis', 'int', 'Integer', '', 1))]), ('Objects', [], objs), ('Connections', [], conn)]
    return top, world


def _ascii(nodes, ind=0):
    out = []; pad = ' ' * ind
    for name, props, kids in nodes:
        if len(props) == 1 and isinstance(props[0], np.ndarray) and not kids:
            a = props[0]; out.append('%s%s: *%d {\n%s a: %s\n%s}' % (pad, name, len(a), pad, ','.join(('%.9g' % x) if a.dtype.kind == 'f' else str(int(x)) for x in a), pad)); continue
        ps = ', '.join(('"%s"' % p) if isinstance(p, str) else ('%.9g' % p if isinstance(p, float) else str(int(p))) for p in props)
        if kids: out.append('%s%s: %s {\n%s\n%s}' % (pad, name, ps, _ascii(kids, ind + 1), pad))
        else: out.append('%s%s: %s' % (pad, name, ps))
    return '\n'.join(out)


def _binary(nodes, version=7400, compress=True):
    import zlib
    wide = version >= 7500; hdr = 24 if wide else 12; nul = b'\0' * (25 if wide else 13)
    def prop(p):
        if isinstance(p, L): return b'L' + struct.pack('<q', int(p))
        if isinstance(p, bool): return b'C' + bytes([int(p)])
        if isinstance(p, int): return b'I' + struct.pack('<i', p)
        if isinstance(p, float): return b'D' + struct.pack('<d', p)
        if isinstance(p, str): b = p.encode('utf-8'); return b'S' + struct.pack('<I', len(b)) + b
        a = np.asarray(p); t, dt = {'f': (b'd', '<f8'), 'i': (b'i', '<i4'), 'u': (b'i', '<i4')}[a.dtype.kind]; raw = a.astype(dt).tobytes()
        if compress: z = zlib.compress(raw); return t + struct.pack('<III', len(a), 1, len(z)) + z
        return t + struct.pack('<III', len(a), 0, len(raw)) + raw
    def node(nd, base):
        name, props, kids = nd; pb = b''.join(prop(p) for p in props); nm = name.encode('latin1'); head = hdr + 1 + len(nm); body_at = base + head + len(pb)
        kb = b''; at = body_at
        for k in kids:
            kk = node(k, at); kb += kk; at += len(kk)
        if kids: kb += nul
        end = base + head + len(pb) + len(kb)
        return (struct.pack('<QQQ' if wide else '<III', end, len(props), len(pb)) if True else b'') + bytes([len(nm)]) + nm + pb + kb
    out = b'Kaydara FBX Binary  \x00\x1a\x00' + struct.pack('<I', version); at = len(out)
    for nd in nodes:
        b = node(nd, at); out += b; at += len(b)
    return out + nul + b'\0' * 160


def write_fbx(spec, d, tex_sub='textures', binary=False, version=7400, compress=True, **kw):
    os.makedirs(os.path.join(d, tex_sub), exist_ok=True)
    for m, (im, _) in enumerate(spec.pics): im.save(os.path.join(d, tex_sub, 'tex%d.png' % m))
    tree, world = _fbx_tree(spec, tex_sub, **kw); p = os.path.join(d, 'm.fbx')
    if binary: open(p, 'wb').write(_binary(tree, version, compress))
    else: open(p, 'w').write('; FBX 7.3.0 project file\n' + _ascii(tree) + '\n')
    write_fbx.world = world; return p


def write_dae(spec, d):
    """Collada: one <geometry> per material, <effect> with a texture sampler, library_images, a scene with one node per geometry"""
    os.makedirs(d, exist_ok=True); X = ['<?xml version="1.0" encoding="utf-8"?>', '<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">', '<asset><up_axis>Y_UP</up_axis></asset>']
    imgs = effs = mats = geos = nodes = ''
    for m, (im, _) in enumerate(spec.pics):
        im.save(os.path.join(d, 'tex%d.png' % m))
        imgs += '<image id="img%d"><init_from>tex%d.png</init_from></image>' % (m, m)
        effs += ('<effect id="eff%d"><profile_COMMON><newparam sid="surf%d"><surface type="2D"><init_from>img%d</init_from></surface></newparam><newparam sid="samp%d"><sampler2D><source>surf%d</source></sampler2D></newparam>'
                 '<technique sid="common"><phong><diffuse><texture texture="samp%d" texcoord="UVMap"/></diffuse></phong></technique></profile_COMMON></effect>' % (m, m, m, m, m, m))
        mats += '<material id="mat%d" name="mat%d"><instance_effect url="#eff%d"/></material>' % (m, m, m)
        ts = np.flatnonzero(spec.mat == m)
        if not len(ts): continue
        V = spec.pos[ts].reshape(-1, 3); UV = spec.uv[ts].reshape(-1, 2); k = len(V)
        geos += ('<geometry id="geo%d"><mesh><source id="pos%d"><float_array id="posa%d" count="%d">%s</float_array><technique_common><accessor source="#posa%d" count="%d" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>'
                 '<source id="uv%d"><float_array id="uva%d" count="%d">%s</float_array><technique_common><accessor source="#uva%d" count="%d" stride="2"><param name="S" type="float"/><param name="T" type="float"/></accessor></technique_common></source>'
                 '<vertices id="vtx%d"><input semantic="POSITION" source="#pos%d"/></vertices><triangles material="m%d" count="%d"><input semantic="VERTEX" source="#vtx%d" offset="0"/><input semantic="TEXCOORD" source="#uv%d" offset="1" set="0"/><p>%s</p></triangles></mesh></geometry>'
                 % (m, m, m, 3 * k, ' '.join('%.7f' % x for x in V.reshape(-1)), m, k, m, m, 2 * k, ' '.join('%.7f' % x for x in UV.reshape(-1)), m, k, m, m, m, k // 3, m, m, ' '.join('%d %d' % (i, i) for i in range(k))))
        nodes += '<node id="n%d"><instance_geometry url="#geo%d"><bind_material><technique_common><instance_material symbol="m%d" target="#mat%d"><bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/></instance_material></technique_common></bind_material></instance_geometry></node>' % (m, m, m, m)
    X += ['<library_images>%s</library_images>' % imgs, '<library_effects>%s</library_effects>' % effs, '<library_materials>%s</library_materials>' % mats, '<library_geometries>%s</library_geometries>' % geos,
          '<library_visual_scenes><visual_scene id="S">%s</visual_scene></library_visual_scenes>' % nodes, '<scene><instance_visual_scene url="#S"/></scene>', '</COLLADA>']
    p = os.path.join(d, 'm.dae'); open(p, 'w').write('\n'.join(X)); return p


def patch_glb(path, fn):
    """rewrite the JSON chunk of a .glb with fn(json) (to add samplers, KHR_texture_transform, baseColorFactor ...)"""
    import json
    d = open(path, 'rb').read(); n = struct.unpack_from('<I', d, 12)[0]; js = json.loads(d[20:20 + n].decode()); rest = d[20 + n:]
    fn(js); b = json.dumps(js).encode(); b += b' ' * (-len(b) % 4)
    out = d[:12] + struct.pack('<I', len(b)) + b'JSON' + b + rest; open(path, 'wb').write(out[:8] + struct.pack('<I', len(out)) + out[12:])


def gltf_features(spec):
    """an fn for patch_glb that applies the spec's wrap / tint / transform to the materials mat0, mat1 ..."""
    MODE = {'repeat': 10497, 'clamp': 33071, 'mirror': 33648}
    def fn(js):
        js['samplers'] = [{'wrapS': MODE[w], 'wrapT': MODE[w]} for w in ('repeat', 'mirror', 'clamp')]
        for mt in js['materials']:
            m = int(mt['name'].replace('mat', '')); pbr = mt['pbrMetallicRoughness']; bt = pbr['baseColorTexture']
            js['textures'][bt['index']]['sampler'] = ('repeat', 'mirror', 'clamp').index(spec.wrap[m])
            if spec.tint[m] is not None: pbr['baseColorFactor'] = list(spec.tint[m]) + [1.0]
            if spec.tf[m] is not None:
                (ox, oy), rot, (sx, sy) = spec.tf[m]; bt.setdefault('extensions', {})['KHR_texture_transform'] = dict(offset=[ox, oy], rotation=rot, scale=[sx, sy]); js.setdefault('extensionsUsed', []).append('KHR_texture_transform')
    return fn


# ------------------------------------------------------------------ the check
def check(spec, path, texture_dir=None, size=1024, tol=45, world=None):
    """-> (matched corners, wrong corners, unmatched triangles, notes). Loads `path`, packs the atlas like the viewer, compares every corner with the source."""
    m = load_model(path, texture_dir); imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in m.images]
    atl, cells = atlas.pack(imgs, m.uv, m.vert_mat, size=size); uv2 = atlas.remap_uv(m.uv, m.vert_mat, cells, size)
    P0 = spec.pos if world is None else np.stack([world(p) for p in spec.pos]); cents = P0.mean(1); ok = bad = miss = 0; notes = []
    for t3 in m.tris:
        cen = m.pos[t3].mean(0); d = np.linalg.norm(cents - cen, axis=1); s = int(np.argmin(d))
        if d[s] > 1e-3: miss += 1; continue
        for vi in t3:
            j = int(np.argmin(np.linalg.norm(P0[s] - m.pos[vi], axis=1)))
            if np.linalg.norm(P0[s, j] - m.pos[vi]) > 1e-3 or (s, j) in spec.skip: continue
            got = atl[min(int(uv2[vi, 1] * size), size - 1), min(int(uv2[vi, 0] * size), size - 1)]
            if np.abs(got.astype(int) - spec.expected(s, j).astype(int)).max() <= tol: ok += 1
            else: bad += 1
    return ok, bad, miss, notes
