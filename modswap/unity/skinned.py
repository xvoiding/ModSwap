"""Swap a rigged Unity character: your model gets auto-rigged onto the character's own skeleton (same bones, same bind poses), so the game's
animations drive it. The body mesh is replaced, the clothing/eye meshes are emptied, and the texture is swapped.

Coordinates: the viewer/rig frame is X = left, Y = forward, Z = up, cm (fit.to_char); Unity mesh space is x right, y up, z forward, metres."""
import numpy as np
from PIL import Image
from .. import skin, edit, atlas
from . import mesh as umesh, patch, fit as ufit, skinscan

ADJ = ('width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose')


def character(P, m):
    """the skeleton (from the main body mesh's bone list + bind poses) and the original outline of one rigged character; cached"""
    key = (m['file'], m['top'], m['main_name'])
    cache = P.__dict__.setdefault('_chars', {})
    if key in cache: return cache[key]
    _, OL = P._both(m['file'])
    s = m['smrs'][m['main_smr']]
    bone_pids = [b['m_PathID'] for b in OL[s['pid']].read_typetree()['m_Bones']]
    _, OM = P._both(s['mesh'][0]); mt = OM[s['mesh'][1]].read_typetree()
    bp = np.array([[[e['e%d%d' % (r, c)] for c in range(4)] for r in range(4)] for e in mt['m_BindPose']], float)
    if len(bp) != len(bone_pids): raise ValueError('this character\'s bone list does not match its mesh')
    heads_u = np.linalg.inv(bp)[:, :3, 3]                      # bone head in mesh space = translation of the inverse bind pose
    span_u = float(heads_u[:, 1].max() - heads_u[:, 1].min())
    k = 1.0
    idx = {p: i for i, p in enumerate(bone_pids)}; names = []; parent = []
    for pid in bone_pids:
        tr = OL[pid].read(); names.append(OL[tr.m_GameObject.path_id].read().m_Name)
        f = tr.m_Father.path_id; hops = 0
        while f and f not in idx and f in OL and hops < 60: f = OL[f].read().m_Father.path_id; hops += 1
        parent.append(idx.get(f, -1))
    PP = []; TT = []; off = 0
    for it in m['smrs']:
        _, O2 = P._both(it['mesh'][0])
        try: pos, tris = umesh.read_geometry(O2[it['mesh'][1]])
        except Exception: continue
        PP.append(np.asarray(pos, np.float64)); TT.append(np.asarray(tris) + off); off += len(pos)
    hu = float(max(np.ptp(np.concatenate(PP)[:, 1]) if PP else 0, span_u))
    if hu > 0: k = float(np.clip(10 ** round(np.log10(hu / 1.7)), 1e-3, 1e3))       # some games author their models in cm (Granny is ~110 units tall): bring every character to a ~170 "cm" scale
    heads = ufit.to_char(heads_u, k)
    if PP: opos = ufit.to_char(np.concatenate(PP), k); otris = np.concatenate(TT)
    else:                                       # could not decode the original meshes: use the skeleton for the size, and draw no outline
        span = heads[:, 2].max() - heads[:, 2].min(); opos = np.array([[0, 0, heads[:, 2].min()], [0, 0, heads[:, 2].max() + 0.14 * span]]); otris = np.zeros((0, 3), np.int64)
    lo, hi = opos.min(0), opos.max(0)
    rig = dict(names=names, parent=parent, head=heads, ref_height=float(hi[2] - lo[2]), ref_min_z=float(lo[2]))
    have = {r for r, _ in skin.classify(names).values()}
    humanoid = bool(('pelvis' in have or 'spine' in have) and ('upperarm' in have or 'thigh' in have) and ('head' in have or 'neck' in have))
    ch = dict(rig=rig, opos=opos, otris=otris, lo=lo, hi=hi, humanoid=humanoid, k=k)
    cache[key] = ch; return ch


def _generic_weights(pos, rig, max_inf=4):
    head = np.array(rig['head'], float); par = rig['parent']; K = len(par); H = rig['ref_height']
    kids = {i: [j for j in range(K) if par[j] == i] for i in range(K)}
    D = np.empty((len(pos), K))
    for b in range(K):
        a = head[b]
        if kids[b]: t = head[kids[b]].mean(0)
        elif par[b] >= 0: t = a + (a - head[par[b]]) * 0.5
        else: t = a + np.array([0, 0, 1e-3])
        D[:, b] = skin._seg_dist(pos, a, t)
    order = np.argsort(D, axis=1)[:, :max_inf]; dd = np.take_along_axis(D, order, 1)
    w = 1.0 / (dd + 0.01 * H) ** 3; w[dd > dd[:, :1] * 3.0 + 0.03 * H] = 0; w /= w.sum(1, keepdims=True)
    return order.astype(np.int32), w


def fit(P, m, model, params):
    """-> dict(pos, nrm in the rig/game frame, tris, si, sw, C, info, vgroup, piv, static)"""
    ch = character(P, m); rig = ch['rig']
    adj = {k: float(v) for k, v in (params.get('adjust') or {}).items() if k in ADJ}
    up = params.get('up') or model.up; fwd = params.get('forward') or None; sc = float(params.get('scale') or 1.0)
    if ch['humanoid']:
        r = skin.autorig(model.pos, model.nrm, rig, up=up, forward=fwd, scale_mult=sc, adjust=adj, edits=params.get('edits') or None, tris=model.tris)
        return dict(pos=r['pos'], nrm=r['nrm'], tris=edit.keep_triangles(model.tris, r['hidden']), si=r['skin_i'], sw=r['skin_w'],
                    C=skin.rig_frame(rig), info=dict(r['info']), vgroup=r['vgroup'], piv=r['piv'], static=False)
    pos, nrm, info = ufit.fit_static(model, ch['lo'], ch['hi'], up=up, forward=fwd, scale=sc, adjust=adj)
    si, sw = _generic_weights(pos, rig)
    return dict(pos=pos, nrm=nrm, tris=model.tris, si=si, sw=sw, C=np.eye(3), info=info, vgroup=np.zeros(len(pos), np.uint8),
                piv=np.zeros((6, 3)), static=True)


def _main_texture(P, fn, env, O, mat_pid):
    """[file, pid] of the material's main texture (texture pointers are relative to the material's file)"""
    if mat_pid not in O: return None
    ext = skinscan.ext_actual(env, P.data); first = None
    for k, v in O[mat_pid].read().m_SavedProperties.m_TexEnvs:
        nm = getattr(k, 'name', k); tx = v.m_Texture
        ref = skinscan.deref(fn, ext, dict(m_FileID=tx.m_FileID, m_PathID=tx.m_PathID))
        if not ref: continue
        if nm in ('_MainTex', '_BaseMap', '_BaseColorMap', '_Diffuse'): return ref
        first = first or ref
    return first


def build(P, m, model, params, out_dir, log=print):
    import os
    f = fit(P, m, model, params)
    pos, nrm, tris, si, sw = f['pos'], f['nrm'], f['tris'], f['si'], f['sw']
    used = np.unique(tris); remap = -np.ones(len(pos), np.int64); remap[used] = np.arange(len(used))      # drop erased body parts
    pos, nrm, si, sw = pos[used], nrm[used], si[used], sw[used]; tris = remap[tris]
    uvs, vm = model.uv[used], model.vert_mat[used]
    imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in model.images]
    atl, cells = atlas.pack(imgs, uvs, vm, size=2048)
    uv = atlas.remap_uv(uvs, vm, cells, 2048); uv[:, 1] = 1.0 - uv[:, 1]
    Pu, Nu, tr = ufit.unity_arrays(pos, nrm, tris, k=character(P, m)['k'])
    log('rigging the model onto the character\'s skeleton (%d vertices)...' % len(Pu))
    held = {}; touched = set()

    try:
        def get(fn):
            if fn not in held: held[fn] = P._both(fn, current=True)      # patch the game's current files so mods stack
            return held[fn]
        s = m['smrs'][m['main_smr']]; main = tuple(s['mesh'])
        fn, pid = s['mesh']; patch.set_mesh(get(fn)[1][pid], Pu, Nu, uv, tr, n_sub=max(1, s['n_mats']), skin=(si, sw)); touched.add(fn)
        done = {main}
        for it in m['smrs']:
            k = tuple(it['mesh'])
            if k in done: continue
            done.add(k); fn2, pid2 = it['mesh']
            try: patch.empty_mesh(get(fn2)[1][pid2]); touched.add(fn2)
            except Exception as e: log('could not hide %s: %s' % (it['name'], e))
        mat = m.get('main_mat')
        if mat:
            env, O = get(mat[0]); tex = _main_texture(P, mat[0], env, O, mat[1])
            if tex:
                log('writing the texture...')
                tenv, TO = get(tex[0]); patch.set_texture(TO[tex[1]], Image.fromarray(atl), 'DXT1'); touched.add(tex[0])
                from .project import UnityProject
                UnityProject._white(O, mat[1]); touched.add(mat[0])
            else: log('note: could not find this character\'s texture, it will look untextured')
        os.makedirs(out_dir, exist_ok=True); out = {}
        for fn in touched:
            log('saving %s...' % fn)
            p = os.path.join(out_dir, fn)
            with open(p, 'wb') as fh: fh.write(held[fn][0].file.save())
            out[fn] = p
    finally:
        from .project import _close_env
        for h in list(held.values()):
            try: _close_env(h[0])
            except Exception: pass
        P.release()
    return out
