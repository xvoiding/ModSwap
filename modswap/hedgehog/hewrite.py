"""Put a user's model into a Sonic Frontiers NEDMDLV5 model WITHOUT changing the file's size or moving anything.

The game's own meshes are slots with a fixed amount of room (vertex bytes, index bytes, bone table). A swap fills the slots with the user's triangles (counts are lowered to what
is used, the bone table is rewritten, vertices/indices are written big-endian in the slot's own vertex layout), hides every other slot (one degenerate triangle) and, when a slot has
to take another slot's material (the plain 'cloth' material for all of them), re-points its material name / texture units at that mesh's strings. Pointers are self-relative and only
ever written FORWARD (the game's own files have no backward ones), so a slot can only borrow the material of a mesh that comes later in the file.
Because nothing moves, the trailing pointer table stays valid and the .pac needs no relocation (see pacwrite).
"""
import struct
import numpy as np
from .. import skin as SK, atlas, edit
from . import hemodel as H

MAX_INFLUENCES = 4


# ------------------------------------------------------------------ frame + rig
def to_model_space(p): p = np.asarray(p, float); return p[..., [0, 2, 1]]
from_model_space = to_model_space                                # auto-rig frame (X left, Y forward, Z up) <-> the model's (x left, y up, z forward)


def rig_from_hemodel(model, ref_vertices):
    names, par, _ = model.nodes(); W = from_model_space(model.node_world()); P = from_model_space(ref_vertices)
    return dict(names=names, parent=par, head=W.tolist(), bonemap=list(range(len(names))), facing=[0.0, 1.0, 0.0], mesh_min=P.min(0).tolist(), mesh_max=P.max(0).tolist(),
                ref_height=float(P[:, 2].max() - P[:, 2].min()), ref_min_z=float(P[:, 2].min()))


def lod_reference(model):
    """vertices that define the character's size: every non-outline mesh of this level of detail"""
    return np.concatenate([m.positions() for m in model.meshes() if 'outline' not in m.material and 'aura' not in m.material])


def front_is_ccw(model):
    """True when the game's own triangles are counter-clockwise seen from outside (checked against its stored normals)"""
    m = max((x for x in model.meshes() if 'outline' not in x.material), key=lambda x: x.vertex_count); P = m.positions(); N = m.normals(); F = m.faces
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); return float((fn * N[F].sum(1)).sum()) > 0


def metres(adjust):
    """the fit sliders' Left/right, Forward/back, Up/down are CENTIMETRES but this rig is in METRES (the auto-rig adds them in rig units): without this 1 cm moved the model 1 m"""
    a = dict(adjust or {})
    for k in ('dx', 'dy', 'dz'):
        if a.get(k): a[k] = float(a[k]) * 0.01
    return a


# ------------------------------------------------------------------ fitting the user's model
def fit(model0, user, up='+Y', forward=None, scale=1.0, adjust=None, edits=None, atlas_size=1024, log=print):
    """-> dict(pos, nrm, uv, tris, skin_i (N,4) node numbers, skin_w (N,4), atlas, info ...) in the game's model frame (metres, y up, +z forward)"""
    rg = rig_from_hemodel(model0, lod_reference(model0))
    r = SK.autorig(user.pos, user.nrm, rg, up=up, forward=forward, scale_mult=scale, adjust=metres(adjust), edits=edit.scale_lengths(edits, 0.01), tris=user.tris)
    log('auto-rig: scale %.3f, facing %s' % (r['info']['scale'], r['info']['forward']))
    pos = to_model_space(r['pos']); nrm = to_model_space(r['nrm'])
    tris = edit.keep_triangles(user.tris, r['hidden']).copy(); tris_view = tris.copy()
    tris = tris[:, [0, 2, 1]]                                           # the y/z swap mirrors the model
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]]); outward = np.sign((fn * nrm[tris].sum(1)).sum(1)).mean() >= 0
    ccw = front_is_ccw(model0)
    if outward != ccw: tris = tris[:, [0, 2, 1]]                         # (outward == True means ccw so far)
    from PIL import Image
    images = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in user.images]
    atl, cells = atlas.pack(images, user.uv, user.vert_mat, size=atlas_size); uv = atlas.remap_uv(user.uv, user.vert_mat, cells, atlas_size)
    return dict(pos=pos, nrm=nrm, uv=uv, tris=tris, skin_i=np.asarray(r['skin_i']), skin_w=np.asarray(r['skin_w']), atlas=atl, info=r['info'], pos_rig=r['pos'], tris_view=tris_view,
                vgroup=r['vgroup'], piv=r['piv'], rig=rg)


# ------------------------------------------------------------------ vertex encoders
def _dec3n(v):
    v = np.asarray(v, float); v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    c = np.clip(np.rint(v * 511), -511, 511).astype(np.int64) & 0x3FF
    return (c[:, 0] | (c[:, 1] << 10) | (c[:, 2] << 20) | (3 << 30)).astype('>u4')


def tangent_frame(pos, nrm, uv, tris):
    """tangent = direction of increasing u, binormal = direction of DEcreasing v (the game's convention, measured on its own meshes), both made perpendicular to the normal"""
    e1 = pos[tris[:, 1]] - pos[tris[:, 0]]; e2 = pos[tris[:, 2]] - pos[tris[:, 0]]
    du1, du2 = uv[tris[:, 1], 0] - uv[tris[:, 0], 0], uv[tris[:, 2], 0] - uv[tris[:, 0], 0]; dv1, dv2 = uv[tris[:, 1], 1] - uv[tris[:, 0], 1], uv[tris[:, 2], 1] - uv[tris[:, 0], 1]
    det = du1 * dv2 - du2 * dv1; r = np.where(np.abs(det) > 1e-12, 1.0 / np.where(np.abs(det) > 1e-12, det, 1), 0.0)
    tu = (e1 * dv2[:, None] - e2 * dv1[:, None]) * r[:, None]; tv = (e2 * du1[:, None] - e1 * du2[:, None]) * r[:, None]
    T = np.zeros_like(pos); B = np.zeros_like(pos)
    for k in range(3): np.add.at(T, tris[:, k], tu); np.add.at(B, tris[:, k], tv)
    B = -B
    def ortho(V, fallback):
        V = V - nrm * (V * nrm).sum(1, keepdims=True); L = np.linalg.norm(V, axis=1, keepdims=True)
        bad = (L[:, 0] < 1e-9); V = V / np.maximum(L, 1e-9)
        if bad.any(): V[bad] = fallback[bad]
        return V
    ref = np.where(np.abs(nrm[:, [1]]) < 0.9, np.array([[0, 1.0, 0]]), np.array([[1.0, 0, 0]])); t0 = np.cross(nrm, ref); t0 /= np.maximum(np.linalg.norm(t0, axis=1, keepdims=True), 1e-9)
    T = ortho(T, t0); B = ortho(B, np.cross(nrm, t0))
    return T, B


def _weights_u8(w):
    w = np.asarray(w, float); w = w / np.maximum(w.sum(1, keepdims=True), 1e-9); q = np.floor(w * 255).astype(np.int64); rem = 255 - q.sum(1)
    q[np.arange(len(q)), w.argmax(1)] += rem; return q.astype(np.uint8)


def encode_vertices(mesh, pos, nrm, uv, bone_idx, bone_w, tan, bit):
    """the mesh slot's vertex buffer (N * vertex_size bytes) for these vertices, written in the slot's own vertex layout"""
    n = len(pos); buf = np.zeros((n, mesh.vertex_size), np.uint8)
    def put(e, raw): buf[:, e.offset:e.offset + raw.shape[1]] = raw
    for e in mesh.elements:
        if e.usage == H.POSITION and e.fmt == 0x2A23B9: put(e, np.ascontiguousarray(pos.astype('>f4')).view(np.uint8).reshape(n, 12))
        elif e.usage in (H.NORMAL, H.TANGENT, H.BINORMAL) and e.fmt == 0x2A2187:
            v = {H.NORMAL: nrm, H.TANGENT: tan, H.BINORMAL: bit}[e.usage]; put(e, np.ascontiguousarray(_dec3n(v)).view(np.uint8).reshape(n, 4))
        elif (e.usage & 0xFFFF0000) == H.UV and e.fmt in (0x2C235F, 0x2C2359): put(e, np.ascontiguousarray(uv.astype('>f2')).view(np.uint8).reshape(n, 4))
        elif e.usage == H.COLOR and e.fmt in (0x1A2086, 0x1A2286): put(e, np.full((n, 4), 255, np.uint8))
        elif e.usage == H.BLENDINDEX and e.fmt == 0x1A2286: put(e, bone_idx.astype(np.uint8))
        elif e.usage == H.BLENDWEIGHT and e.fmt == 0x1A2086: put(e, _weights_u8(bone_w))
        else: raise ValueError('vertex element usage %#x format %#x is not supported by the writer' % (e.usage, e.fmt))
    return buf


# ------------------------------------------------------------------ skin helpers
def clean_skin(si, sw, nodes_parent, max_bones):
    """-> (node numbers (N,4), weights (N,4)) with at most `max_bones` distinct nodes overall: the least-used bones hand their weight to their parent bone"""
    si = np.array(si, np.int64); sw = np.array(sw, float); sw[sw < 1e-4] = 0
    for _ in range(4096):
        used = np.unique(si[sw > 0])
        if len(used) <= max_bones: break
        load = {int(b): float(sw[(si == b)].sum()) for b in used}; victim = min(load, key=load.get)
        p = nodes_parent[victim]
        if p < 0: p = int(max(load, key=load.get))
        si[si == victim] = p
    # merge duplicate bones inside a vertex (after remapping), keep the 4 strongest, renormalise
    out_i = np.zeros_like(si); out_w = np.zeros_like(sw)
    for v in range(len(si)):
        acc = {}
        for b, w in zip(si[v], sw[v]):
            if w > 0: acc[int(b)] = acc.get(int(b), 0.0) + float(w)
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES]
        if not top: top = [(int(si[v, 0]), 1.0)]
        s = sum(w for _, w in top)
        for k, (b, w) in enumerate(top): out_i[v, k] = b; out_w[v, k] = w / s
    return out_i, out_w


# ------------------------------------------------------------------ filling the slots
class CapacityError(ValueError):
    """the model does not fit into the slots of this level of detail"""
    def __init__(self, msg, need_vertices=0, room_vertices=0): super().__init__(msg); self.need_vertices = need_vertices; self.room_vertices = room_vertices


def _host(meshes):
    opaque = [m for m in meshes if m.slot == 'opaque']
    for key in ('cloth', 'body', 'skin'):
        c = [m for m in opaque if key in m.material and 'outline' not in m.material]
        if c: return max(c, key=lambda m: m.vertex_count)
    if not opaque: raise ValueError('this model has no opaque mesh to host a swap')
    return max(opaque, key=lambda m: m.vertex_count)


def slots_for(meshes):
    """-> (host mesh, [slots to fill, host first]). A slot can borrow the host's material only if it comes BEFORE the host in the file (pointers only go forward)."""
    host = _host(meshes)
    use = [m for m in meshes if m.slot == 'opaque' and m.raw['at'] <= host.raw['at'] and 'outline' not in m.material and m is not host]
    return host, [host] + sorted(use, key=lambda m: -m.vertex_count)


def capacity(slots): return sum(m.vertex_count for m in slots)


def _assign(slots, tris, si, sw):
    """greedy: triangles in order go into the current slot until its vertices / indices / bone table run out. -> [(slot, global vertex list, local tris, bone list)]"""
    out = []; k = 0; cur = None
    def new():
        return dict(map={}, v=[], t=[], bones=set())
    cur = new()
    def close():
        nonlocal k, cur
        if cur['t']: out.append((slots[k], cur['v'], cur['t'], sorted(cur['bones'])))
        k += 1; cur = new()
    for t in tris:
        while True:
            if k >= len(slots): raise CapacityError('your model has more triangles / vertices / bones than this character\'s mesh slots can hold', 0, capacity(slots))
            s = slots[k]; nv = [x for x in dict.fromkeys(int(i) for i in t) if x not in cur['map']]
            nb = {int(b) for x in t for b, w in zip(si[x], sw[x]) if w > 0} - cur['bones']
            if (len(cur['v']) + len(nv) <= s.vertex_count and 3 * (len(cur['t']) + 1) <= 3 * len(s.faces) and len(cur['bones']) + len(nb) <= len(s.bones)): break
            if not cur['t']: raise CapacityError('a single triangle of your model needs more bones than any mesh slot of this character has (%d)' % len(s.bones), 0, capacity(slots))
            close()
        for x in nv: cur['map'][x] = len(cur['v']); cur['v'].append(x)
        cur['bones'] |= nb; cur['t'].append([cur['map'][int(i)] for i in t])
    close(); return out


def fill(chunk, fitted, log=print, skin=None):
    """-> (new chunk bytes (same length), report). Raises CapacityError when the model does not fit."""
    model = H.HeModel(chunk); meshes = model.meshes(); names, parent, _ = model.nodes(); data = bytearray(chunk); nn = len(names)
    host, slots = slots_for(meshes)
    pos, nrm, uv, tris = fitted['pos'], fitted['nrm'], fitted['uv'], np.asarray(fitted['tris'], np.int64)
    si, sw = skin if skin is not None else clean_skin(fitted['skin_i'], fitted['skin_w'], parent, len(host.bones))
    placed = _assign(slots, tris, si, sw)
    w = 1 if nn <= 255 else 2; host_name = model.ptr(host.raw['at']); host_units = host.raw['units_at']; used = set()
    for slot, verts, lt, bones in placed:
        a = slot.raw['at']; v = np.array(verts, np.int64); lt = np.array(lt, np.int64); P, N, U = pos[v], nrm[v], uv[v]
        T, B = tangent_frame(P, N, U, lt)
        table = {b: i for i, b in enumerate(bones)}; bi = np.zeros((len(v), 4), np.int64); bw = np.zeros((len(v), 4))
        for r, g in enumerate(v):
            for c in range(4):
                if sw[g, c] > 0: bi[r, c] = table[int(si[g, c])]; bw[r, c] = sw[g, c]
            if bw[r].sum() == 0: bw[r, 0] = 1.0
        vb = encode_vertices(slot, P, N, U, bi, bw, T, B)
        if len(vb) > slot.vertex_count * slot.vertex_size: raise CapacityError('internal: too many vertices for a slot')
        va = slot.raw['vertices_at']; data[va:va + vb.size] = vb.tobytes()
        fa = slot.raw['faces_at']; data[fa:fa + lt.size * 2] = lt.reshape(-1).astype('>u2').tobytes()
        ba = slot.raw['bones_at']
        for i, b in enumerate(bones): data[ba + w * i:ba + w * i + w] = int(b).to_bytes(w, 'big')
        struct.pack_into('>I', data, a + 4, int(lt.size)); struct.pack_into('>I', data, a + 12, len(v)); struct.pack_into('>I', data, a + 28, len(bones))
        if slot is not host:
            if not (host_name > a and host_units > a + 40): raise ValueError('internal: a slot can only borrow the material of a mesh that comes later in the file')
            struct.pack_into('<I', data, a, host_name - a); struct.pack_into('>I', data, a + 36, len(host.texture_units)); struct.pack_into('<I', data, a + 40, host_units - (a + 40))
        used.add(a)
    for m in meshes:                                                   # everything else disappears: one degenerate triangle
        a = m.raw['at']
        if a in used: continue
        fa = m.raw['faces_at']; data[fa:fa + 6] = b'\0' * 6; struct.pack_into('>I', data, a + 4, 3)
    lo, hi = model.bounds(); b = model.ptr(model.header + 28)
    nlo = np.minimum(lo, pos.min(0)); nhi = np.maximum(hi, pos.max(0)); struct.pack_into('>6f', data, b, nlo[0], nhi[0], nlo[1], nhi[1], nlo[2], nhi[2])
    rep = dict(host=host.material, slots=[(s.material, len(vv), len(t), len(bb)) for s, vv, t, bb in placed], vertices=sum(len(vv) for _, vv, _, _ in placed), triangles=sum(len(t) for _, _, t, _ in placed))
    log('filled %d slot(s): %s' % (len(placed), ', '.join('%s %dv/%dt/%db' % x for x in rep['slots'])))
    return bytes(data), rep


def fill_fitting(chunk, fitted, log=print):
    """fill, and when the model is too big for this level of detail reduce it (grid clustering) until it fits: the limit shrinks by whichever room (vertices or triangles) runs out first"""
    from ..unity.patch import reduce_vertices
    model = H.HeModel(chunk); _, parent, _ = model.nodes(); host, slots = slots_for(model.meshes())
    try: return fill(chunk, fitted, log)
    except CapacityError as first:
        vert_room = capacity(slots); tri_room = sum(len(s.faces) for s in slots); limit = min(vert_room, len(fitted['pos']))
        si, sw = clean_skin(fitted['skin_i'], fitted['skin_w'], parent, len(host.bones))
        for _ in range(30):
            limit = int(limit * 0.9)
            if limit < 64: break
            P, N, U, T, sk = reduce_vertices(fitted['pos'], fitted['nrm'], fitted['uv'], np.asarray(fitted['tris'], np.int64), skin=(si, sw), limit=limit)
            if len(T) > tri_room:                                              # too many triangles left: aim lower in one step
                limit = int(limit * tri_room / len(T) * 0.97); continue
            small = dict(fitted, pos=np.asarray(P, float), nrm=np.asarray(N, float), uv=np.asarray(U, float), tris=T)
            try:
                out = fill(chunk, small, log, skin=clean_skin(sk[0], sk[1], parent, len(host.bones)))
                log('your model was reduced from %d to %d vertices (%d to %d triangles) to fit this level of detail' % (len(fitted['pos']), len(P), len(fitted['tris']), len(T))); return out
            except CapacityError: continue
        raise first
