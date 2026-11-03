"""Find the swappable (non-skinned) models in a Unity game: groups of meshes that appear together, like a truck = body + cab + wheels."""
import os, re, json, collections
import numpy as np
from . import mesh as umesh

SKIP_FILES = ('globalgamemanagers', 'resources.assets.resS')
HOT = re.compile(r'truck|car|vehicle|bus|van|player|enemy|npc|character|human|zombie|monster|boss|robot|weapon|gun|sword|ship|airplane|boat|bike|tank', re.I)


def data_dir(root):
    """the folder that holds the serialized files ('<Game>_Data', up to 3 levels down); the one with the most asset files wins"""
    best = None; best_n = -1; root = os.path.normpath(root); base = root.count(os.sep)
    for d, dirs, files in os.walk(root):
        if d.count(os.sep) - base >= 3: dirs[:] = []; continue
        low = {f.lower() for f in files}
        if 'globalgamemanagers' in low or 'data.unity3d' in low or 'maindata' in low:
            n = len([f for f in low if f.startswith(('level', 'sharedassets', 'resources'))])
            if n > best_n: best, best_n = d, n
    return best


def serialized_files(dd):
    out = []
    for f in sorted(os.listdir(dd)):
        p = os.path.join(dd, f)
        if not os.path.isfile(p): continue
        if re.fullmatch(r'level\d+|sharedassets\d+\.assets|resources\.assets', f, re.I) and os.path.getsize(p) > 4096: out.append(f)
    return out


def _ptr(p):
    return (p.m_FileID, p.m_PathID) if p is not None else (0, 0)


def _quat_mat(q, s, p):
    x, y, z, w = q; n = x * x + y * y + z * z + w * w
    if n < 1e-12: x = y = z = 0.0; w = 1.0; n = 1.0
    x, y, z, w = [v / np.sqrt(n) for v in (x, y, z, w)]
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s)[None, :]; M[:3, 3] = p
    return M


def _strip(n): return re.sub(r'\s*[\(\[]\d+[\)\]]$|[ _-]?\d+$|\.\d+$', '', n).strip() or n


def scan_file(dd, fname, log=print, path=None):
    import UnityPy
    env = UnityPy.load(path or os.path.join(dd, fname))
    O = {o.path_id: o for o in env.objects}
    tf = {}; go_tf = {}
    mf = {}; mr = {}; skinned = set()
    for pid, o in O.items():
        tn = o.type.name
        if tn in ('Transform',):
            t = o.read(); g = t.m_GameObject.path_id
            tf[pid] = dict(go=g, father=t.m_Father.path_id, p=(t.m_LocalPosition.x, t.m_LocalPosition.y, t.m_LocalPosition.z),
                           q=(t.m_LocalRotation.x, t.m_LocalRotation.y, t.m_LocalRotation.z, t.m_LocalRotation.w),
                           s=(t.m_LocalScale.x, t.m_LocalScale.y, t.m_LocalScale.z))
            go_tf[g] = pid
        elif tn == 'MeshFilter':
            m = o.read(); fid, mp = _ptr(m.m_Mesh)
            mf[m.m_GameObject.path_id] = (mp if fid == 0 else 0)
        elif tn == 'MeshRenderer':
            m = o.read(); mr[m.m_GameObject.path_id] = [p.m_PathID if p.m_FileID == 0 else 0 for p in m.m_Materials if p is not None]
        elif tn == 'SkinnedMeshRenderer':
            skinned.add(o.read().m_GameObject.path_id)
    has = {g for g, mp in mf.items() if mp and mp in O and g in mr and g in go_tf}
    father_go = {g: (tf[tf[go_tf[g]]['father']]['go'] if tf[go_tf[g]]['father'] in tf else 0) for g in go_tf}
    memo = {}

    def top_of(g):               # topmost mesh-bearing GameObject of the chain g -> root, if g is a mesh GO
        chain = []; cur = g; res = g if g in has else 0
        while cur:
            if cur in has: res = cur
            cur = father_go.get(cur, 0)
        return res
    tops = collections.defaultdict(list)
    for g in has: tops[top_of(g)].append(g)
    mesh_users = collections.Counter(mf[g] for g in has); mat_users = collections.Counter(m for g in has for m in mr[g][:1])
    mesh_cache = {}

    def mbounds(mp):
        if mp not in mesh_cache:
            try: mesh_cache[mp] = umesh.bounds(O[mp])
            except Exception: mesh_cache[mp] = None
        return mesh_cache[mp]
    groups = {}
    for top, gos in tops.items():
        if any(g in skinned for g in gos): continue
        parts = collections.Counter(mf[g] for g in gos)
        sig = (mf[top], tuple(sorted(parts.items())))
        groups.setdefault(sig, []).append((top, gos))
    models = []
    nameof = {}

    def gname(g):
        if g not in nameof:
            try: nameof[g] = O[g].read().m_Name
            except Exception: nameof[g] = '?'
        return nameof[g]
    for sig, inst in groups.items():
        top, gos = inst[0]; parts = []; lo = np.full(3, 1e9); hi = np.full(3, -1e9); bad = False
        topM = None
        for g in gos:
            M = np.eye(4); cur = g                           # transform of g relative to the top GameObject
            while cur and cur != top:
                t = tf[go_tf[cur]]; M = _quat_mat(t['q'], t['s'], t['p']) @ M; cur = father_go.get(cur, 0)
            b = mbounds(mf[g])
            if b is None: bad = True; break
            nm, nv, c, e, comp = b
            if comp: bad = True; break
            corners = np.array([[c[0] + sx * e[0], c[1] + sy * e[1], c[2] + sz * e[2], 1] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) @ M.T
            lo = np.minimum(lo, corners[:, :3].min(0)); hi = np.maximum(hi, corners[:, :3].max(0))
            parts.append(dict(go=g, mesh=mf[g], name=nm, verts=nv, mats=mr[g], M=M.tolist(), ext=(2 * e).tolist()))
        if bad or not parts: continue
        place = [[p['mesh'], p['M']] for p in parts]
        # one entry per distinct mesh, with how many times it appears inside one model
        byMesh = collections.OrderedDict()
        for p in parts:
            d = byMesh.setdefault(p['mesh'], dict(mesh=p['mesh'], name=p['name'], verts=p['verts'], mats=p['mats'], count=0, vol=float(np.prod(p['ext']))))
            d['count'] += 1
        verts = sum(d['verts'] * d['count'] for d in byMesh.values())
        if verts < 24: continue
        main = max(byMesh.values(), key=lambda d: d['vol'] * (1 if d['count'] == 1 else 0.5))
        main_mesh = main['mesh']; main_mat = (main['mats'] or [0])[0]
        n = len(inst)
        total_mesh = {m: mesh_users[m] for m in byMesh}
        shared_mesh = sum(max(0, total_mesh[m] - d['count'] * n) for m, d in byMesh.items())
        shared_mat = max(0, mat_users.get(main_mat, 0) - sum(d['count'] for d in byMesh.values() if (d['mats'] or [0])[0] == main_mat) * n) if main_mat else 0
        label0 = _strip(gname(top))
        par = ''
        pg = father_go.get(top, 0)
        if pg: par = _strip(gname(pg))
        label = (par + ' \u203A ' + label0) if par and par.lower() not in ('map', 'root', 'scene') else label0
        hot = bool(HOT.search(label0) or HOT.search(par) or any(HOT.search(d['name']) for d in byMesh.values()))
        models.append(dict(file=fname, top=top, label=label, parent=par, instances=n, verts=int(verts), main=main_mesh, main_mat=main_mat,
                           main_name=main['name'], n_mats=len(main['mats']), parts=list(byMesh.values()),
                           lo=lo.tolist(), hi=hi.tolist(), place=place, shared_mesh=int(shared_mesh), shared_mat=int(shared_mat), hot=hot,
                           inst_tops=[t for t, _ in inst][:3]))
    log('%s: %d models' % (fname, len(models)))
    return models


def scan(root, log=print, only=None, resolve=None):
    import UnityPy
    from . import skinscan
    dd = data_dir(root)
    if not dd: raise RuntimeError('could not find the Unity data folder in %s' % root)
    files = serialized_files(dd)
    if not files: raise RuntimeError('this game keeps its assets in bundles (data.unity3d / AssetBundles), which ModSwap cannot edit yet')
    models = []; rigged = []; errs = []
    envs = collections.OrderedDict(); minfo = {}

    def getenv(name):
        if name in envs: envs.move_to_end(name); return envs[name]
        envs[name] = UnityPy.load((resolve(name) if resolve else None) or os.path.join(dd, name))
        while len(envs) > 3: envs.popitem(last=False)
        return envs[name]
    for f in files:
        if only and f not in only: continue
        log('reading %s ...' % f)
        p = resolve(f) if resolve else None
        try: models += scan_file(dd, f, log, p)
        except Exception as e: errs.append('%s: %s' % (f, e)); log('skipped %s (%s)' % (f, e))
        try: rigged += skinscan.scan_file(dd, f, p, getenv, minfo, log)
        except Exception as e: errs.append('%s (characters): %s' % (f, e)); log('could not read characters in %s (%s)' % (f, e))
    rigged = skinscan.merge(rigged)
    if not models and not rigged:
        if errs and len(errs) >= len(files): raise RuntimeError('could not read this game\'s Unity files (%s). It may be a Unity version ModSwap cannot read yet.' % errs[0][:160])
        raise RuntimeError('no swappable models found in this game\'s Unity files.')
    def key(m): return (not m['hot'], -m['instances'] if m['instances'] < 400 else 0, -m['verts'])
    models.sort(key=key); rigged.sort(key=lambda m: (not m['hot'], -m['bones'], -m['verts']))
    from .curate import curate
    allm = curate((rigged + models)[:4000])               # sorted into people / vehicles / weapons / props; levels, scenery and junk are tagged and hidden by default
    return dict(dir=dd, models=allm, ver=3)


def save(res, path): json.dump(res, open(path, 'w'))
def load(path): return json.load(open(path))
