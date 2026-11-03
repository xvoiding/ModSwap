"""Body-part editing on a fitted model: auto-detected parts (head, torso, arms, legs), user-made parts (from a box / cut-line selection),
and per-part hide / move / size / rotate. Everything happens on the final bind-pose mesh (after skin weights are computed), so a moved
arm stays rigged as an arm. Frame: X = character's left, Y = forward, Z = up (centimetres, degrees)."""
import numpy as np
from .skin import classify

AUTO_NAMES = ['Torso', 'Head', 'Left arm', 'Right arm', 'Left leg', 'Right leg']


def rot_matrix(pitch=0.0, yaw=0.0, roll=0.0):
    """pitch = lean forward(+), yaw = turn (same sense as the Turn slider), roll = lean to the character's left(+)"""
    a, y, b = np.radians(-pitch), np.radians(yaw), np.radians(roll)
    ca, sa, cy, sy, cb, sb = np.cos(a), np.sin(a), np.cos(y), np.sin(y), np.cos(b), np.sin(b)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]); Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]); Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    return Rz @ Ry @ Rx


def auto_groups(rig, roles, skin_i, skin_w, head):
    """-> (vgroup (N,) uint8 index into AUTO_NAMES, pivots (6,3)).  roles = autorig's {bone: (role, side)}; head = bone heads in the character frame."""
    par = rig['parent']; K = len(par)
    def group_of_bone(i):
        j = i; seen = 0
        while j >= 0 and seen < 200:
            r = roles.get(j)
            if r:
                role, side = r
                if role in ('upperarm', 'lowerarm', 'hand'): return 2 if side == 'L' else 3 if side == 'R' else 0
                if role in ('thigh', 'calf', 'foot'): return 4 if side == 'L' else 5 if side == 'R' else 0
                if role == 'head': return 1
                return 0
            j = par[j]; seen += 1
        return 0
    bg = np.array([group_of_bone(i) for i in range(K)], np.uint8)
    dom = skin_i[np.arange(len(skin_i)), skin_w.argmax(1)]
    vg = bg[dom]
    piv = np.zeros((6, 3))
    for g, (role, side) in enumerate([(None, None), ('head', None), ('upperarm', 'L'), ('upperarm', 'R'), ('thigh', 'L'), ('thigh', 'R')]):
        found = [b for b, (r, s) in roles.items() if r == role and (side is None or s == side)]
        if found: piv[g] = head[found[0]]
    return vg, piv


def _unpack(mask_b64, n):
    import base64
    raw = np.frombuffer(base64.b64decode(mask_b64), np.uint8)
    return np.unpackbits(raw)[:n].astype(bool)


def apply_edits(P, N, vg, piv, edits):
    """edits = {'g': {'2': {hide, move[3], scale, rot[3]}}, 'c': [{mask(b64 packbits), hide, move, scale, rot}]} -> (P, N, hidden (N,) bool, custom masks)"""
    P = P.copy(); N = N.copy(); hidden = np.zeros(len(P), bool)
    if not edits: return P, N, hidden
    groups = []
    for k, op in (edits.get('g') or {}).items():
        k = int(k)
        if 0 <= k < 6: groups.append((vg == k, piv[k], op))
    for op in edits.get('c') or []:
        m = _unpack(op['mask'], len(P))
        if m.any(): groups.append((m, None, op))
    for m, pivot, op in groups:
        if op.get('hide'): hidden |= m; continue
        mv = np.array(op.get('move') or [0, 0, 0], float); sc = float(op.get('scale') or 1.0); rt = op.get('rot') or [0, 0, 0]
        if not mv.any() and abs(sc - 1) < 1e-9 and not any(rt): continue
        pv = np.array(op.get('pivot')) if op.get('pivot') else (pivot if pivot is not None else P[m].mean(0))
        R = rot_matrix(*[float(x or 0) for x in rt])
        P[m] = (P[m] - pv) @ R.T * sc + pv + mv
        N[m] = N[m] @ R.T
    return P, N, hidden


def keep_triangles(tris, hidden):
    """drop triangles whose majority of corners were erased"""
    if hidden is None or not hidden.any(): return tris
    return tris[hidden[tris].sum(1) < 2]
