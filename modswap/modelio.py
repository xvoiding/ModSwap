"""Model loading into a simple engine-neutral structure. Formats: see FORMATS (FBX/OBJ/glTF/GLB/VRM/DAE/PLY/STL/OFF/3MF built in; .blend/.3ds/USD/Alembic via Blender).

Model:  pos (N,3)  nrm (N,3)  uv (N,2, image convention: v=0 at TOP)  tris (T,3)  tri_mat (T,)
        images: list[PIL.Image] one per material (None if missing)   mat_names: list[str]
Vertices are per-corner welded (unique pos+normal+uv) so they can go straight into a game vertex buffer.
Source axes are kept as-is; use skin.autorig(..., up=, forward=) to convert to the game's axes.
"""
import os, re
from dataclasses import dataclass, field
import numpy as np
from PIL import Image


@dataclass
class Model:
    pos: np.ndarray
    nrm: np.ndarray
    uv: np.ndarray
    tris: np.ndarray
    tri_mat: np.ndarray
    images: list = field(default_factory=list)
    mat_names: list = field(default_factory=list)
    tri_part: np.ndarray = None          # which mesh object of the file each triangle belongs to
    part_names: list = field(default_factory=list)
    up: str = '+Y'                       # up axis the file declares (or a guess)
    source: str = ''

    @property
    def vert_mat(self):
        vm = np.zeros(len(self.pos), np.int32)
        vm[self.tris.reshape(-1)] = np.repeat(self.tri_mat, 3)
        return vm

    def subset(self, keep):
        """Model with only the given mesh parts (indices into part_names)."""
        if self.tri_part is None or len(self.part_names) < 2 or len(keep) == len(self.part_names): return self
        keep = set(int(k) for k in keep)
        sel = np.isin(self.tri_part, list(keep))
        if not sel.any(): raise ValueError('no mesh parts selected')
        t = self.tris[sel]; used = np.unique(t); remap = np.full(len(self.pos), -1, np.int64); remap[used] = np.arange(len(used))
        return Model(self.pos[used], self.nrm[used], self.uv[used], remap[t].astype(np.int32), self.tri_mat[sel], self.images, self.mat_names,
                     self.tri_part[sel], self.part_names, self.up, self.source)


FORMATS = [  # (label, extensions, how)
    ('FBX', '.fbx', 'built in'), ('OBJ', '.obj', 'built in'), ('glTF / GLB / VRM', '.gltf .glb .vrm', 'built in'),
    ('Collada', '.dae', 'built in'), ('PLY', '.ply', 'built in'), ('STL', '.stl', 'built in'), ('OFF', '.off', 'built in'),
    ('3MF', '.3mf', 'built in'), ('Blender', '.blend', 'needs Blender'), ('3DS', '.3ds', 'needs Blender'),
    ('USD', '.usd .usda .usdc .usdz', 'needs Blender'), ('Alembic', '.abc', 'needs Blender'), ('X3D / VRML', '.x3d .wrl', 'needs Blender'),
]
MODEL_EXT = tuple(e for _, exts, _ in FORMATS for e in exts.split())
IMAGE_EXT = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff', '.webp', '.dds')
_NOT_COLOR = ('normal', 'nrm', '_n.', 'bump', 'spec', 'rough', 'metal', 'occl', '_ao', 'mask', 'emis', 'height', 'disp', 'opacity', 'alpha', 'gloss', 'orm', 'mtrao')


def _smooth_normals(P, tris):
    fn = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, tris[:, k], fn)
    return vn / (np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12)


def _weld(pos_idx, uv_idx, P, UV, tri_mat_c):
    """corner arrays (len = 3*T) -> welded verts. Normals are smooth per position."""
    keys = np.stack([pos_idx, uv_idx], 1)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    pos = P[uniq[:, 0]]; uv = UV[uniq[:, 1]] if len(UV) else np.zeros((len(uniq), 2))
    tris = inv.reshape(-1, 3).astype(np.int32)
    return pos, uv, tris


MAX_PICTURE = 2048                                                         # no atlas is bigger, so a bigger picture only costs memory (twenty 8k pictures would need gigabytes)


def to_rgb(im):
    """any PIL picture -> an RGB picture: 16-bit and float greys are scaled (a plain convert() would clip them white), palette / alpha / CMYK / greys are converted, and it is shrunk to MAX_PICTURE"""
    try:
        if im.mode in ('I;16', 'I;16L', 'I;16B', 'I;16N'): im = Image.fromarray((np.asarray(im, np.float64) / 257.0).clip(0, 255).astype(np.uint8))
        elif im.mode == 'I': a = np.asarray(im, np.float64); im = Image.fromarray((a / (256.0 if a.max() > 255 else 1.0)).clip(0, 255).astype(np.uint8))
        elif im.mode == 'F': a = np.asarray(im, np.float64); im = Image.fromarray((a * (255.0 if a.max() <= 1.0 else 1.0)).clip(0, 255).astype(np.uint8))
        im = im.convert('RGB')
    except Exception: im = im.convert('RGB')
    if max(im.size) > MAX_PICTURE:
        k = -(-max(im.size) // MAX_PICTURE)
        im = im.reduce(k)                                                  # (a box average: much faster than a resize, and plenty for a picture that is shrunk again)
        if max(im.size) > MAX_PICTURE:
            f = MAX_PICTURE / float(max(im.size)); im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
    return im


_PICTURES = {}


def open_picture(src):
    """a file path or bytes -> RGB picture (or None when it can not be read). A file used by many materials is decoded once (each caller gets its own copy, loaders attach wrap modes to them)."""
    import io
    key = None
    if isinstance(src, str):
        try: key = (os.path.abspath(src), os.path.getmtime(src), os.path.getsize(src))
        except OSError: return None
        if key in _PICTURES: return _PICTURES[key].copy()
    try:
        im = Image.open(src if isinstance(src, str) else io.BytesIO(src))
        if im.format == 'JPEG' and max(im.size) > 2 * MAX_PICTURE: im.draft('RGB', (MAX_PICTURE, MAX_PICTURE))        # (decode a big JPEG at a reduced size)
        im.load(); im = to_rgb(im)
    except Exception: return None
    if key is not None:
        if len(_PICTURES) > 12: _PICTURES.pop(next(iter(_PICTURES)))
        _PICTURES[key] = im
    return im.copy()


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


def find_picture(cands, dirs):
    """a picture named by the file (its path as written first, then the bare file name anywhere near the model, any capitalisation) -> RGB PIL image or None"""
    names = [str(c).replace('\\', '/') for c in cands if c]
    for d in [x for x in dirs if x]:                                           # the path as written, relative to the model
        for n in names:
            p = os.path.join(d, n)
            if os.path.isfile(p):
                im = open_picture(p)
                if im is not None: return im
    bare = [os.path.basename(n) for n in names]
    for d in _near_dirs(dirs):
        low = {f.lower(): f for f in os.listdir(d)}
        for n in bare:
            if n.lower() in low:
                im = open_picture(os.path.join(d, low[n.lower()]))
                if im is not None: return im
    return None


def _mtl_path(rest):
    """the file of a 'map_Kd [options] file' line: the whole text when there are no options (spaces allowed), else the last word (options are -s 1 1 1, -o .., -clamp on ...)"""
    parts = rest.split()
    return rest.strip() if not any(x.startswith('-') for x in parts) else parts[-1]


def load_obj(path, texture_dir=None):
    P, UV, faces = [], [], []   # faces: list of (mat_id, [(vi,ti),...])
    mats = {}; cur = 0; mtl_files = []
    for line in open(path, errors='ignore'):
        if line.startswith('v '): P.append([float(x) for x in line.split()[1:4]])
        elif line.startswith('vt '): UV.append([float(x) for x in line.split()[1:3]])
        elif line.startswith('mtllib'): mtl_files.append(line.split(None, 1)[1].strip())
        elif line.startswith('usemtl'):
            n = line.split(None, 1)[1].strip(); cur = mats.setdefault(n, len(mats))
        elif line.startswith('f '):
            idx = []
            for tok in line.split()[1:]:
                p = tok.split('/'); vi = int(p[0]); ti = int(p[1]) if len(p) > 1 and p[1] else 0
                vi = vi - 1 if vi > 0 else len(P) + vi; ti = ti - 1 if ti > 0 else (len(UV) + ti if ti < 0 else -1)
                idx.append((vi, ti))
            for k in range(1, len(idx) - 1): faces.append((cur, [idx[0], idx[k], idx[k + 1]]))
    if not mats: mats['default'] = 0
    P = np.array(P, np.float64); UV = np.array(UV if UV else [[0, 0]], np.float64)
    pi = np.array([[c[0] for c in f[1]] for f in faces]).reshape(-1)
    ti = np.array([[max(c[1], 0) for c in f[1]] for f in faces]).reshape(-1)
    tri_mat = np.array([f[0] for f in faces], np.int32)
    pos, uv, tris = _weld(pi, ti, P, UV, tri_mat)
    uv = np.nan_to_num(uv.copy(), nan=0.0, posinf=0.0, neginf=0.0); uv[:, 1] = 1.0 - uv[:, 1]                    # obj v-up -> image v-down
    # materials / textures
    base = os.path.dirname(path); tex = {}; kd = {}
    for mf in mtl_files:
        mp = os.path.join(base, mf)
        if not os.path.exists(mp): mp = os.path.join(base, os.path.basename(mf.replace('\\', '/')))
        if not os.path.exists(mp): continue
        name = None
        for l in open(mp, errors='ignore'):
            l = l.strip()
            if l.startswith('newmtl'): name = l.split(None, 1)[1]
            elif l.lower().startswith('map_kd') and name: tex[name] = _mtl_path(l.split(None, 1)[1])
            elif l.lower().startswith('kd ') and name:
                try: kd[name] = tuple(int(round(max(0.0, min(1.0, float(x))) * 255)) for x in l.split()[1:4])
                except ValueError: pass
    names = sorted(mats, key=mats.get); images = []
    for n in names:
        f = tex.get(n)
        if f is None:   # obj/mtl material names often differ slightly (g0m0 vs g0m0.007): prefix match, then single-texture fallback
            cands = [v for k, v in tex.items() if k.startswith(n) or n.startswith(k)]
            f = cands[0] if cands else (list(tex.values())[0] if len(tex) == 1 else None)
        img = find_picture([f], [base, texture_dir]) if f else None
        if img is None and n in kd and not f: img = Image.new('RGB', (64, 64), kd[n])             # no picture named: the material's plain colour
        images.append(img)
    nrm = _smooth_normals(pos, tris)
    return Model(pos, nrm, uv, tris, tri_mat, images, names)


def load_fbx_via_blender(path, texture_dir=None):
    """Needs the `bpy` module (pip install bpy). Bakes the world transform, merges all meshes, triangulates."""
    import bpy, bmesh
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    pos, uv, tris, tri_mat, nrm = [], [], [], [], []
    names, images, mat_ids = [], [], {}
    off = 0
    for o in bpy.data.objects:
        if o.type != 'MESH' or len(o.data.polygons) == 0: continue
        me = o.data.copy(); me.transform(o.matrix_world); me.calc_loop_triangles()
        uvl = me.uv_layers.active
        for m in me.materials:
            key = m.name if m else 'none'
            if key not in mat_ids:
                mat_ids[key] = len(names); names.append(key); img = None
                if m and m.use_nodes:
                    for n in m.node_tree.nodes:
                        if n.type == 'TEX_IMAGE' and n.image:
                            p = bpy.path.abspath(n.image.filepath)
                            for cand in [p, os.path.join(texture_dir or '', os.path.basename(p))]:
                                if os.path.exists(cand): img = Image.open(cand).convert('RGB'); break
                            break
                images.append(img)
        corner = {}
        for lt in me.loop_triangles:
            ids = []
            for li, vi in zip(lt.loops, lt.vertices):
                u = tuple(uvl.data[li].uv) if uvl else (0, 0)
                k = (off, vi, round(u[0], 5), round(u[1], 5))
                if k not in corner:
                    corner[k] = len(pos)
                    pos.append(tuple(me.vertices[vi].co)); uv.append((u[0], 1.0 - u[1])); nrm.append(tuple(me.vertices[vi].normal))
                ids.append(corner[k])
            tris.append(ids)
            mname = me.materials[lt.material_index].name if me.materials and me.materials[lt.material_index] else 'none'
            tri_mat.append(mat_ids.get(mname, 0))
        off += 1
    return Model(np.array(pos, np.float64), np.array(nrm, np.float64), np.array(uv, np.float64),
                 np.array(tris, np.int32), np.array(tri_mat, np.int32), images, names)


def _smooth_by_position(pos, tris):
    """smooth normals averaged over all vertices at the same position (so UV seams don't show as hard edges)"""
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    q = np.round(pos / (np.ptp(pos, axis=0).max() * 1e-6 + 1e-12)).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True); inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, 3))
    for k in range(3): np.add.at(acc, inv[tris[:, k]], fn)
    n = acc[inv]; return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def _weld_corners(raw):
    """per-corner arrays -> shared vertices (same position + normal + uv)"""
    pos, uv, nrm = raw['pos'], raw['uv'], raw['nrm']
    scale = np.ptp(pos, axis=0).max() + 1e-12
    key = np.concatenate([np.round(pos / scale * 1e5), np.round(uv * 1e5)] + ([np.round(nrm * 1e3)] if nrm is not None else []), axis=1)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    pos2, uv2 = pos[first], uv[first]; nrm2 = nrm[first] if nrm is not None else None
    tris = inv[raw['tris']].astype(np.int32)
    return pos2, nrm2, uv2, tris


def guess_images(model, dirs):
    """Give materials without a texture a picture from the files that came with the model (by name, else the best colour map)."""
    from PIL import Image
    files = []
    for d in filter(None, dirs):
        if os.path.isdir(d): files += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(IMAGE_EXT) and not f.lower().endswith('.dds')]
    files = list(dict.fromkeys(files))
    if not files: return
    color = [f for f in files if not any(k in os.path.basename(f).lower() for k in _NOT_COLOR)] or files
    def open_(f):
        return open_picture(f)
    def toks(t): return {x for x in re.split(r'[^a-z]+', re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t).lower()) if len(x) > 2 and x not in ('mat', 'mtl', 'material', 'dif', 'diff', 'tex', 'col', 'png', 'jpg')}
    used = set()
    NOISE = {'textures', 'texture', 'images', 'image', 'img', 'copy'}
    def ident(f): return frozenset(toks(os.path.splitext(os.path.basename(f))[0]) - NOISE)      # 'hair_difa', '1_hair_difa' and 'textures__hair_difa' are the same texture dropped more than once
    def pick(cands):
        return sorted(cands, key=lambda f: (len(os.path.basename(f)), os.path.basename(f)))[0]
    for i, im in enumerate(model.images):
        if im is not None: continue
        mt = toks(model.mat_names[i] if i < len(model.mat_names) else '')
        if not mt: continue
        scored = sorted(((len(mt & ident(f)), f) for f in color if f not in used), key=lambda x: -x[0])
        if not scored or scored[0][0] <= 0: continue
        top = [f for sc, f in scored if sc == scored[0][0]]
        if len({ident(f) for f in top}) == 1:             # one texture (maybe several copies of it): unambiguous
            best = pick(top); model.images[i] = open_(best)
            used.update(f for f in color if ident(f) == ident(best))
    missing = [i for i, im in enumerate(model.images) if im is None]
    left = [f for f in color if f not in used]
    _seen = set(); left = [f for f in left if not (ident(f) in _seen or _seen.add(ident(f)))]      # one entry per distinct texture
    if len(missing) == 1 and left:                      # one untextured material and some pictures: take the most "diffuse looking" one
        pref = [f for f in left if any(k in os.path.basename(f).lower() for k in ('diff', 'albedo', 'base', 'color', 'colour', '_d.', '_bc', '_df'))]
        model.images[missing[0]] = open_((pref or left)[0])
    elif len(missing) == len(left) and missing:
        for i, f in zip(missing, left): model.images[i] = open_(f)


def from_raw(raw, texture_dir=None, path=''):
    if raw.get('per_corner'): pos, nrm, uv, tris = _weld_corners(raw); tm = raw['tri_mat']
    else: pos, nrm, uv, tris, tm = raw['pos'], raw['nrm'], raw['uv'], raw['tris'], raw['tri_mat']
    if nrm is None: nrm = _smooth_by_position(pos, tris)
    uv = np.nan_to_num(np.asarray(uv, np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    m = Model(np.asarray(pos, np.float64), np.asarray(nrm, np.float64), np.asarray(uv, np.float64), np.asarray(tris, np.int32), np.asarray(tm, np.int32),
              list(raw['images']), list(raw['mat_names']), raw.get('tri_part'), list(raw.get('part_names', [])), raw.get('up', '+Y'), path)
    guess_images(m, [os.path.dirname(os.path.abspath(path)) if path else None, texture_dir])
    for i, c in enumerate(raw.get('colors') or []):                 # no picture anywhere: flat material colour
        if m.images[i] is None and c is not None: m.images[i] = Image.new('RGB', (64, 64), c)
    return m


def load_model(path, texture_dir=None):
    return normalise_tiling(split_by_material(_load_model(path, texture_dir)))


def normalise_tiling(m):
    """Fold tiled uvs back toward 0..1: a texture that repeats can have each triangle's uvs moved by whole tiles without changing how it looks, which keeps every material's uv range
    small (a model tiled 60 times would otherwise need a cell 60 tiles wide). Mirrored axes move by 2 tiles (to keep the mirroring), clamped axes do not move. A vertex that two
    triangles want in different tiles is duplicated."""
    if len(m.tris) == 0: return m
    from .atlas import wrap_of
    modes = [wrap_of(im) if im is not None else ('repeat', 'repeat') for im in m.images]
    uvc = m.uv[m.tris]; mn = uvc.min(1); shift = np.zeros((len(m.tris), 2), np.int64)
    for ax in (0, 1):
        for mode in ('repeat', 'mirror'):
            sel = np.array([modes[t][ax] == mode for t in m.tri_mat], bool) if len(modes) else np.zeros(len(m.tris), bool)
            if sel.any(): step = 1 if mode == 'repeat' else 2; shift[sel, ax] = (np.floor(mn[sel, ax] / step) * step).astype(np.int64)
    shift = np.clip(shift, -100000, 100000)
    if not shift.any(): return m
    corner = np.stack([m.tris.reshape(-1).astype(np.int64), np.repeat(shift[:, 0], 3), np.repeat(shift[:, 1], 3)], 1)
    uniq, inv = np.unique(corner, axis=0, return_inverse=True); inv = inv.reshape(-1)
    uv = m.uv[uniq[:, 0]] - uniq[:, 1:3]
    return Model(m.pos[uniq[:, 0]], m.nrm[uniq[:, 0]], uv, inv.reshape(-1, 3).astype(np.int32), m.tri_mat, m.images, m.mat_names, m.tri_part, m.part_names, m.up, m.source)


def split_by_material(m):
    """Give every material its own copy of a vertex it shares with another material. The loaders weld by position + normal + uv only, so two materials that meet at the same
    point would otherwise share ONE vertex, and that vertex can map into only one material's part of the texture atlas: the other material's triangles would then stretch
    across the wrong part of the picture."""
    if len(m.tris) == 0 or len(m.images) < 2 and int(m.tri_mat.max(initial=0)) == 0: return m
    K = int(m.tri_mat.max()) + 1; corner = m.tris.reshape(-1).astype(np.int64) * K + np.repeat(m.tri_mat.astype(np.int64), 3)
    uniq, inv = np.unique(corner, return_inverse=True); old = uniq // K
    if len(uniq) == len(np.unique(m.tris)): return m                                  # nothing is shared between materials
    m2 = Model(m.pos[old], m.nrm[old], m.uv[old], inv.reshape(-1, 3).astype(np.int32), m.tri_mat, m.images, m.mat_names, m.tri_part, m.part_names, m.up, m.source)
    return m2


def _load_model(path, texture_dir=None):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.obj':
        m = load_obj(path, texture_dir)
        guess_images(m, [os.path.dirname(os.path.abspath(path)), texture_dir]); m.source = path; return m
    if ext == '.fbx':
        from .importers import fbx
        try: return from_raw(fbx.load(path, texture_dir), texture_dir, path)
        except Exception as e:
            try: return load_fbx_via_blender(path, texture_dir)            # last resort if the pure-python reader chokes (bpy / Blender)
            except Exception: raise ValueError('could not read this FBX: %s' % e)
    from .importers import generic
    if ext in generic.TRIMESH_EXT: return from_raw(generic.load_trimesh(path, texture_dir), texture_dir, path)
    if ext in generic.BLENDER_EXT: return from_raw(generic.load_via_blender(path, texture_dir), texture_dir, path)
    raise ValueError('unsupported model format %s (supported: %s)' % (ext or 'none', ', '.join(MODEL_EXT)))
