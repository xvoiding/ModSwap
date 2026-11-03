"""Find rigged characters (SkinnedMeshRenderer groups) in a Unity game: Trump in Mr. President, Granny in Granny, Rick in Rick and Morty ...

A character = the skinned renderers that share a parent GameObject (body, clothes, eyes ...). Meshes/materials usually live in another file
(sharedassetsN.assets) than the scene that uses them, so every reference is resolved to [file, path_id]."""
import os, re, collections
from .scan import _strip, HOT


def ext_actual(env, dd):
    """env's external file list -> actual file names in the data folder (None if it is a built-in resource)"""
    have = {f.lower(): f for f in os.listdir(dd)}
    out = []
    for e in getattr(env.file, 'externals', None) or []:
        p = (getattr(e, 'path', None) or str(e)).replace('\\', '/')
        out.append(have.get(os.path.basename(p).lower()))
    return out


def deref(fname, ext, ptr):
    """PPtr dict -> [file, path_id] or None"""
    fid, pid = ptr.get('m_FileID', 0), ptr.get('m_PathID', 0)
    if not pid: return None
    if fid == 0: return [fname, pid]
    if 0 < fid <= len(ext) and ext[fid - 1]: return [ext[fid - 1], pid]
    return None


def mesh_info(env, pid):
    t = env_objs(env)[pid].read_typetree()
    vd = t.get('m_VertexData') or {}; n = int(vd.get('m_VertexCount', 0))
    if not n and t.get('m_MeshCompression', 0):
        n = int(((t.get('m_CompressedMesh') or {}).get('m_Vertices') or {}).get('m_NumItems', 0)) // 3
    return dict(name=t.get('m_Name', ''), verts=n, nbones=len(t.get('m_BindPose') or []), ok=n > 0)


def env_objs(env):
    o = getattr(env, '_ms_objs', None)
    if o is None:
        o = {x.path_id: x for x in env.objects}
        try: env._ms_objs = o
        except Exception: pass
    return o


def scan_file(dd, fname, path, getenv, minfo_cache, log=print):
    import UnityPy
    env = UnityPy.load(path or os.path.join(dd, fname)); O = env_objs(env); ext = ext_actual(env, dd)
    tf = {}; go_tf = {}; smr = []
    for pid, o in O.items():
        tn = o.type.name
        if tn == 'Transform':
            t = o.read(); tf[pid] = t.m_Father.path_id; go_tf[t.m_GameObject.path_id] = pid
        elif tn == 'SkinnedMeshRenderer':
            smr.append(pid)
    if not smr: return []
    father_go = {}
    for g, tp in go_tf.items():
        fp = tf.get(tp, 0)
        father_go[g] = O[fp].read().m_GameObject.path_id if fp in O else 0
    nameof = {}

    def gname(g):
        if g not in nameof:
            try: nameof[g] = O[g].read().m_Name
            except Exception: nameof[g] = '?'
        return nameof[g]
    items = []
    for pid in smr:
        t = O[pid].read_typetree(); go = t['m_GameObject']['m_PathID']
        mesh = deref(fname, ext, t['m_Mesh'])
        if not mesh: continue
        key = tuple(mesh)
        if key not in minfo_cache:
            try: minfo_cache[key] = mesh_info(env if mesh[0] == fname else getenv(mesh[0]), mesh[1])
            except Exception as e: minfo_cache[key] = dict(name='?', verts=0, nbones=0, ok=False)
        mi = minfo_cache[key]
        bones = [b['m_PathID'] for b in t['m_Bones'] if b['m_FileID'] == 0 and b['m_PathID']]
        if not mi['ok'] or not bones or len(bones) != mi['nbones']: continue
        mats = [deref(fname, ext, m) for m in t['m_Materials']]
        items.append(dict(pid=pid, go=go, name=gname(go), mesh=mesh, mesh_name=mi['name'], verts=mi['verts'], nbones=mi['nbones'],
                          mats=[m for m in mats if m], n_mats=len(mats), grp=father_go.get(go, 0) or go))
    groups = collections.defaultdict(list)
    for it in items: groups[it['grp']].append(it)
    mesh_users = collections.Counter(tuple(it['mesh']) for it in items)
    byname = collections.defaultdict(list)
    for g, its in groups.items(): byname[tuple(sorted(tuple(i['mesh']) for i in its))].append(g)
    models = []
    for sig, gs in byname.items():
        g = gs[0]; its = groups[g]
        main_i = max(range(len(its)), key=lambda i: (its[i]['nbones'], its[i]['verts']))
        main = its[main_i]
        if sum(i['verts'] for i in its) < 60: continue
        label0 = _strip(gname(g)); pg = father_go.get(g, 0) if g in father_go else 0
        par = _strip(gname(pg)) if pg and pg != g else ''
        label = (par + ' › ' + label0) if par and par.lower() not in ('map', 'root', 'scene') else label0
        hot = bool(HOT.search(label0) or HOT.search(par) or any(HOT.search(i['name']) for i in its))
        mm = main['mats'][0] if main['mats'] else None
        models.append(dict(kind='skinned', file=fname, top=g, label=label, parent=par, instances=len(gs), verts=int(sum(i['verts'] for i in its)),
                           main_smr=main_i, main_mat=mm, main_name=main['mesh_name'], n_mats=main['n_mats'], bones=main['nbones'],
                           smrs=its, parts=[dict(name=i['name'], verts=i['verts'], mesh=i['mesh']) for i in its],
                           shared_mesh=int(max(0, mesh_users[tuple(main['mesh'])] - len(gs))), shared_mat=0, hot=True if hot else False,
                           sig=[list(s) for s in sig]))
    log('%s: %d rigged characters' % (fname, len(models)))
    return models


def merge(models):
    """the same character shows up in many scene files; keep one entry"""
    out = collections.OrderedDict()
    for m in models:
        k = tuple(map(tuple, m['sig']))
        if k in out: out[k]['instances'] += m['instances']
        else: out[k] = m
    return list(out.values())
