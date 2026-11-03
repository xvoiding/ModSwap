"""UE4 character swap: replace a SkeletalMesh (+ its textures) with a new model, writing override files for a *_P.pak.

    swap_character(orig_dir, sk_rel, textures, model, rig, out_dir, sk_format=dict(exp_idx=0, rtmask=True))

orig_dir holds the original game files extracted from the pak (same relative paths as in the pak, minus the Content/ prefix
style the profile uses). `textures` entries are dicts:
    {path, format: bc1|bc3|bc5, role: diffuse|normal|flat|overlay, size: px (optional), color: [r,g,b,a] (flat only)}
Every listed texture is rewritten at its ORIGINAL path (pawn blueprints and master materials load textures by path, so
a separate material does not stick).

sk_format describes the engine's cook layout:
    UE4.25 (Just Die Already): exp_idx=1, rtmask=False
    UE4.26+/5 (Goat Simulator 3): exp_idx=0, rtmask=True  (section has a RecomputeTangents mask byte, LODs have a trailing int)
"""
import os, struct
import numpy as np
from PIL import Image

from . import buildsk
from .uepkg import parse_uasset
from .skmesh import walk
from .texwrite import build_texture
from .. import atlas, skin

JDA_FORMAT = dict(exp_idx=1, rtmask=False)
UE427_FORMAT = dict(exp_idx=0, rtmask=True)
UE51_FORMAT = dict(exp_idx=0, rtmask=True, ue5=True)


def tangent_frame(pos, nrm, uv, tris):
    """Per-vertex tangent (N,3) and bitangent sign (N,) in the engine's convention (B = +v direction, v pointing down)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = pos[b] - pos[a], pos[c] - pos[a]; d1, d2 = uv[b] - uv[a], uv[c] - uv[a]
    den = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    tT = (e1 * d2[:, [1]] - e2 * d1[:, [1]]) / den[:, None]
    tB = (e2 * d1[:, [0]] - e1 * d2[:, [0]]) / den[:, None]
    accT = np.zeros_like(pos); accB = np.zeros_like(pos)
    for k in range(3):
        np.add.at(accT, tris[:, k], tT); np.add.at(accB, tris[:, k], tB)
    T = accT - nrm * (accT * nrm).sum(1, keepdims=True)
    bad = np.linalg.norm(T, axis=1) < 1e-9
    T[bad] = np.cross(nrm[bad], [0, 0, 1.0]) + 1e-9
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    sgn = np.sign((np.cross(nrm, T) * accB).sum(1)); sgn[sgn == 0] = 1
    return T, sgn


def _quant_weights(si, sw, b2l):
    N = len(si); out = np.zeros((N, 8), np.uint8)
    for v in range(N):
        ws = sw[v]; order = [k for k in np.argsort(-ws) if ws[k] > 0][:4]
        w = np.array([ws[k] for k in order]); w = w / w.sum()
        w8 = np.rint(w * 255).astype(int); w8[0] += 255 - w8.sum()
        for j, k in enumerate(order):
            out[v, j] = b2l[int(si[v][k])]; out[v, 4 + j] = w8[j]
    return out


def _mode_color(o):
    """most common vertex color of the original mesh (games often use it as a material mask; the common value is the neutral one)"""
    if not o.col: return np.array([0, 0, 0, 255], np.uint8)
    c = np.frombuffer(o.col, np.uint8).reshape(-1, 4)
    u, n = np.unique(c, axis=0, return_counts=True)
    return u[int(np.argmax(n))]


def _norm_tex(t):
    if isinstance(t, dict): return t
    rel, kind, role = t
    return dict(path=rel, format=kind, role=role)


def _write(out_dir, rel, data, written):
    p = os.path.join(out_dir, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data); written.append(rel)


def is_humanoid(rig):
    """does the skeleton have the pieces autorig needs (a pelvis/spine, arms or legs, a head/neck)? Heads-only, animals, fish ... do not"""
    have = {r for r, _ in skin.classify(rig['names']).values()}
    return bool(('pelvis' in have or 'spine' in have) and ('upperarm' in have or 'thigh' in have) and ('head' in have or 'neck' in have))


def generic_fit(o, model, rig, up='+Y', forward=None, scale_mult=1.0, adjust=None, max_inf=4):
    """non-humanoid skeletons (a head mesh, a fish, a sponge): fit the model inside the original's footprint and weight every vertex to the nearest bones.
    Same answer shape as skin.autorig."""
    from ..unity import fit as ufit
    from ..unity.skinned import _generic_weights
    C = skin.rig_frame(rig)
    if o is not None: opos = np.frombuffer(o.pos, '<f4').reshape(-1, 3).astype(np.float64) @ C.T
    else:
        a, b = np.array(rig['mesh_min'], float), np.array(rig['mesh_max'], float)
        opos = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]) @ C.T
    lo, hi = opos.min(0), opos.max(0)
    pos, nrm, info = ufit.fit_static(model, lo, hi, up=up, forward=forward, scale=scale_mult, adjust=adjust)
    rig_c = dict(rig, head=np.array(rig['head'], float) @ C.T, ref_height=float(hi[2] - lo[2]), ref_min_z=float(lo[2]))
    si, sw = _generic_weights(pos, rig_c, max_inf)
    n = len(pos); si4 = np.zeros((n, 4), np.int32); sw4 = np.zeros((n, 4)); si4[:, :si.shape[1]] = si; sw4[:, :sw.shape[1]] = sw
    return dict(pos=pos @ C, nrm=nrm @ C, skin_i=si4, skin_w=sw4, mirrored=False, hidden=None, vgroup=np.zeros(n, np.uint8), piv=np.zeros((6, 3)),
                info=dict(forward=info['forward'], scale=info['scale'], up=up, roles={}, pivot=info['pivot']))


def swap_character(orig_dir, sk_rel, textures, model, rig, out_dir, atlas_size=2048,
                   up='+Y', forward=None, scale_mult=1.0, overlay_fn=None, sk_format=None, adjust=None, edits=None, log=print):
    fmt = sk_format or JDA_FORMAT
    o = buildsk.Orig(os.path.join(orig_dir, sk_rel), **fmt)
    if is_humanoid(rig): r = skin.autorig(model.pos, model.nrm, rig, up=up, forward=forward, scale_mult=scale_mult, adjust=adjust, edits=edits, tris=model.tris)
    else:
        log('this skeleton is not a humanoid: fitting your model to its size and skinning to the nearest bones')
        r = generic_fit(o, model, rig, up=up, forward=forward, scale_mult=scale_mult, adjust=adjust)
    from .. import edit as _edit
    pos, nrm, tris = r['pos'], r['nrm'], _edit.keep_triangles(model.tris, r['hidden']).copy()
    # winding: engine data has cross(e1,e2) pointing against the vertex normal
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    if np.sign((fn * nrm[tris].sum(1)).sum(1)).mean() > 0: tris = tris[:, [0, 2, 1]]
    log('autorig forward=%s scale=%.3f mirrored=%s' % (r['info']['forward'], r['info']['scale'], r['mirrored']))

    # ---- atlas
    mats = model.vert_mat
    images = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in model.images]
    atl, cells = atlas.pack(images, model.uv, mats, size=atlas_size)
    uv = atlas.remap_uv(model.uv, mats, cells, atlas_size)
    T, sgn = tangent_frame(pos, nrm, uv, tris)

    # ---- bones: use the original section's bone map when it covers every bone we skin to, otherwise all used bones
    used = sorted({int(b) for b, w in zip(r['skin_i'].ravel(), r['skin_w'].ravel()) if w > 0})
    if set(used) <= set(o.bonemap): bm, required = None, None; bmap = list(o.bonemap)
    else:
        bm = used; bmap = used
        required = sorted(set(range(len(rig['names']))) | set(o.L['required_bones']))
        log('bone map widened: %d -> %d bones' % (len(o.bonemap), len(bm)))
    b2l = {g: i for i, g in enumerate(bmap)}

    # ---- mesh buffers
    N, nT = len(pos), len(tris)
    idx_dt = '<u2' if N < 65536 else '<u4'          # no vertex limit: big meshes get 32-bit indices
    if idx_dt == '<u4': log('big mesh (%d vertices): using 32-bit indices' % N)
    q = lambda a: np.clip(np.rint(a * 127), -127, 127).astype(np.int8)
    tan = np.zeros((N, 8), np.int8); tan[:, 0:3] = q(T); tan[:, 3] = 127; tan[:, 4:7] = q(nrm); tan[:, 7] = np.where(sgn >= 0, 127, -127)
    sk = _quant_weights(r['skin_i'], r['skin_w'], b2l)
    col = np.tile(_mode_color(o), (N, 1))
    lod = buildsk.build_lod(o, pos.astype('<f4').tobytes(), tan.tobytes(), uv.astype('<f2').tobytes(), sk.tobytes(),
                            col.tobytes(), tris.astype(idx_dt).tobytes(), N, nT, adjbytes=None, bonemap=bm, required=required)
    mn, mx = pos.min(0).astype(float), pos.max(0).astype(float); c, ext = (mn + mx) / 2, (mx - mn) / 2
    ua, ue, mesh_at = buildsk.assemble_auto(o, [lod] * len(o.o['lods']), N)
    bpos = mesh_at + (o.o['skel_start'] - o.mesh_start) + 2                  # the bounds sit 2 bytes (strip flags) after the mesh's start marker
    if fmt.get('ue5'): bounds = struct.pack('<7d', *c, *ext, float(np.linalg.norm(ext))); ue = ue[:bpos] + bounds + ue[bpos + 56:]       # UE5: doubles
    else: bounds = struct.pack('<7f', *c, *ext, float(np.linalg.norm(ext))); ue = ue[:bpos] + bounds + ue[bpos + 28:]
    written = []
    _write(out_dir, sk_rel + '.uasset', ua, written); _write(out_dir, sk_rel + '.uexp', ue, written)
    d2 = parse_uasset(ua); walk(ue, d2, exp_idx=fmt['exp_idx'], verbose=False, rtmask=fmt['rtmask'], all_lods=True, adj=fmt.get('adj'), trail=fmt.get('trail'), v423=fmt.get('v423', False), ue5=fmt.get('ue5', False))   # re-parse sanity check
    log('mesh ok: %d verts, %d tris, %d LODs' % (N, nT, len(o.o['lods'])))

    # ---- textures
    for t in map(_norm_tex, textures):
        rel, kind, role = t['path'], t['format'], t['role']; size = int(t.get('size', atlas_size))
        if role == 'diffuse':
            arr = atl if size == atlas_size else np.array(Image.fromarray(atl).resize((size, size), Image.LANCZOS))
        elif role == 'normal':
            arr = np.zeros((size, size, 3), np.uint8); arr[...] = (128, 128, 255)
        elif role == 'flat':
            arr = np.zeros((size, size, 4), np.uint8); arr[...] = t.get('color', [128, 128, 128, 255])
        elif role == 'overlay':
            arr = np.dstack([np.zeros((size, size, 3), np.uint8), np.zeros((size, size), np.uint8)])
            if overlay_fn: arr = overlay_fn(atl)
        else: raise ValueError('unknown texture role ' + role)
        chain = atlas.compress_chain(arr, kind)
        tb = os.path.join(orig_dir, rel); ob = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(ob), exist_ok=True)
        build_texture(tb, ob, chain, {}, size=size, first_mip=0)
        written += [rel + e for e in ('.uasset', '.uexp', '.ubulk')]
        log('texture %s (%dpx %s)' % (os.path.basename(rel), size, kind))
    return written


def hide_skmesh51(orig_dir, sk_rel, out_dir, fmt):
    """UE5.1: keep the package byte-for-byte and flatten the position buffer of every LOD to the origin, so every triangle has zero area.
    (Works for pieces that carry vertex colours or morph buffers, which cannot be rebuilt yet.)"""
    from .skmesh import walk
    base = os.path.join(orig_dir, sk_rel); ua = open(base + '.uasset', 'rb').read(); ue = bytearray(open(base + '.uexp', 'rb').read())
    o = walk(bytes(ue), parse_uasset(ua), exp_idx=fmt.get('exp_idx', 0), verbose=False, rtmask=fmt.get('rtmask', True), all_lods=True, ue5=True)
    for L in o['lods']:
        a, b = L['pos']['start'], L['pos']['end']; ue[a:b] = bytes(b - a)
    w = []; _write(out_dir, sk_rel + '.uasset', ua, w); _write(out_dir, sk_rel + '.uexp', bytes(ue), w)
    return w


def hide_skmesh(orig_dir, sk_rel, out_dir, sk_format=None):
    """Replace a SkeletalMesh with an invisible one (a single zero-area triangle) so layered pieces (clothes, heads)
    don't cover the swapped body. Keeps materials, skeleton, bounds and LOD count so the game is none the wiser."""
    fmt = sk_format or UE427_FORMAT
    if fmt.get('ue5'): return hide_skmesh51(orig_dir, sk_rel, out_dir, fmt)
    o = buildsk.Orig(os.path.join(orig_dir, sk_rel), **fmt)
    N, nT = 3, 1
    pos = np.zeros((N, 3), '<f4')
    tan = np.zeros((N, 8), np.int8); tan[:, 0] = 127; tan[:, 3] = 127; tan[:, 6] = 127; tan[:, 7] = 127
    sk = np.zeros((N, 8), np.uint8); sk[:, 4] = 255
    lod = buildsk.build_lod(o, pos.tobytes(), tan.tobytes(), np.zeros((N, 2), '<f2').tobytes(), sk.tobytes(),
                            np.tile(_mode_color(o), (N, 1)).tobytes(), np.array([0, 1, 2], '<u2').tobytes(), N, nT)
    ua, ue, _ = buildsk.assemble_auto(o, [lod] * len(o.o['lods']), N)
    w = []; _write(out_dir, sk_rel + '.uasset', ua, w); _write(out_dir, sk_rel + '.uexp', ue, w)
    return w
