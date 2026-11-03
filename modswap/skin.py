"""Auto-rigging: put an unrigged (or differently rigged) humanoid mesh onto a game's humanoid skeleton.

Steps: convert axes -> scale/position to the game's character -> detect the mesh's arm pose and build a
"source" skeleton that matches it -> weight vertices to nearby body bones (segment distance, left/right aware)
-> linear-blend-skin the mesh from the source pose to the game's bind pose.

Rig dict: names[list], parent[list], head[(K,3)] bind-pose bone head positions in game space (Z up, +Y forward, +X = character's left),
          ref_height (float, height of the original character mesh), ref_min_z
"""
import re
import numpy as np

ROLE_PATTERNS = [
    ('pelvis',   r'(^|[^a-z])(pelvis|hips?)($|[^a-z])'),
    ('spine',    r'spine'),
    ('neck',     r'neck'),
    ('head',     r'(^|[^a-z])head($|[^a-z])'),
    ('clavicle', r'clavicle|shoulder'),
    ('lowerarm', r'lowerarm|forearm|fore_arm|lower_arm|arm_lower'),
    ('upperarm', r'upperarm|upper_arm|arm_upper|(^|[^a-z])arm($|[^a-z])'),
    ('hand',     r'(^|[^a-z])hand($|[^a-z])'),
    ('thigh',    r'thigh|upleg|up_leg|upperleg|upper_leg'),
    ('calf',     r'calf|lowerleg|lower_leg|shin|(^|[^a-z])leg($|[^a-z])'),
    ('foot',     r'(^|[^a-z])foot($|[^a-z])'),
]


def snake(name):
    """LeftForeArm -> left_fore_arm ; Spine_01 -> spine_01"""
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()


def side_of(name):
    n = snake(name)
    if re.search(r'(^|[_.\-:\s])l($|[_.\-\s])|left', n): return 'L'
    if re.search(r'(^|[_.\-:\s])r($|[_.\-\s])|right', n): return 'R'
    return 'C'


def classify(names):
    """-> {bone_index: (role, side)} for main-body deform bones."""
    out = {}
    for i, n in enumerate(names):
        low = snake(n)
        if re.search(r'index|middle|ring|pinky|thumb|finger|twist|(^|[^a-z])ik($|[^a-z])|ik_|_ik|corrective|helper|weapon|ball|toe|end$|(^|[^a-z])root$|^root', low): continue
        for role, pat in ROLE_PATTERNS:
            if re.search(pat, low):
                out[i] = (role, side_of(n)); break
    return out


def axis_basis(up, forward):
    """Basis (3x3) that maps source coords -> game coords (X=left, Y=forward, Z=up)."""
    def vec(s):
        v = np.zeros(3); v['xyz'.index(s[1].lower())] = 1.0 if s[0] == '+' else -1.0; return v
    U, F = vec(up), vec(forward)
    L = np.cross(U, F)
    return np.stack([L, F, U], 0)          # rows: new x = L.p, new y = F.p, new z = U.p


def detect_forward(pos, up='+Y', humanoid=False):
    """Which horizontal axis the model faces, e.g. '+Z'. Uses the feet (toes stick out in front of the leg line); falls back to head shape.
    humanoid=True: a person is much wider (shoulders, arms out in a T-pose) than deep, so the wide axis can't be the facing axis."""
    ua = 'xyz'.index(up[1].lower()); sgn = 1 if up[0] == '+' else -1
    h = pos[:, ua] * sgn; lo, H = h.min(), h.max() - h.min()
    feet = pos[h < lo + 0.04 * H]; legs = pos[(h > lo + 0.15 * H) & (h < lo + 0.30 * H)]
    axes = [a for a in range(3) if a != ua]
    if humanoid:
        up_body = pos[h > lo + 0.55 * H]
        if len(up_body) >= 30:
            ext = {a: float(np.percentile(up_body[:, a], 99.5) - np.percentile(up_body[:, a], 0.5)) for a in axes}
            wide = max(axes, key=lambda a: ext[a]); other = [a for a in axes if a != wide][0]
            if ext[wide] > 1.6 * ext[other]: axes = [other]
    if len(feet) >= 10 and len(legs) >= 10:
        dd = {a: float(feet[:, a].mean() - np.median(legs[:, a])) for a in axes}
        a = max(axes, key=lambda k: abs(dd[k]))
        if abs(dd[a]) > 0.004 * H: return ('+' if dd[a] > 0 else '-') + 'xyz'[a].upper()
    top = h > (lo + 0.88 * H); best = None
    for ax in axes:
        v = pos[top][:, ax]; c = np.median(v)
        ext = (np.percentile(v, 99.5) - c, c - np.percentile(v, 0.5)); score = abs(ext[0] - ext[1])
        if best is None or score > best[0]: best = (score, ax, '+' if ext[0] > ext[1] else '-')
    return best[2] + 'xyz'[best[1]].upper()


def _rot(a, b):
    a = a / (np.linalg.norm(a) + 1e-12); b = b / (np.linalg.norm(b) + 1e-12)
    v = np.cross(a, b); c = float(a @ b); s = np.linalg.norm(v)
    if s < 1e-9:
        if c > 0: return np.eye(3)
        ax = np.cross(a, [1, 0, 0]); ax = ax if np.linalg.norm(ax) > 1e-6 else np.cross(a, [0, 1, 0])
        ax /= np.linalg.norm(ax); return 2 * np.outer(ax, ax) - np.eye(3)
    k = v / s; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def _seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab + 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def rig_frame(rig):
    """Matrix C (rows = left, forward, up as unit axes in the game's coordinates), so that p_canonical = p_game @ C.T.
    Canonical space is X=left, Y=forward, Z=up. Game up is assumed to be +Z (Unreal); left comes from the arm bones."""
    f = rig.get('facing')
    if f is not None:                      # facing measured from the mesh geometry beats bone-name guessing (names can be mirrored)
        fwd = np.array(f, float); up = np.array([0, 0, 1.0])
        return np.stack([np.cross(fwd, up), fwd, up], 0)
    names = rig['names']; head = np.array(rig['head'], float); roles = classify(names)
    pick = lambda role, sd: [i for i, (r, s_) in roles.items() if r == role and s_ == sd]
    L = pick('upperarm', 'L') or pick('thigh', 'L'); R_ = pick('upperarm', 'R') or pick('thigh', 'R')
    if not (L and R_): return np.array([[1.0, 0, 0], [0, 1, 0], [0, 0, 1]])
    v = head[L[0]] - head[R_[0]]; v[2] = 0
    ax = int(np.argmax(np.abs(v))); left = np.zeros(3); left[ax] = np.sign(v[ax])
    up = np.array([0, 0, 1.0]); fwd = np.cross(up, left)
    return np.stack([left, fwd, up], 0)


def find_islands(pos, tris):
    """Label every vertex with the loose piece (connected part) of the model it belongs to. Vertices at the same spot are welded first,
    so a UV seam does not cut a piece in two. -> (N,) int labels"""
    pos = np.asarray(pos, float); n = len(pos)
    if len(tris) == 0: return np.arange(n)
    diag = np.linalg.norm(pos.max(0) - pos.min(0)) + 1e-9
    key = np.round((pos - pos.min(0)) / (diag * 1e-5)).astype(np.int64)
    _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
    a = np.concatenate([wid[tris[:, 0]], wid[tris[:, 1]], wid[tris[:, 2]]]); b = np.concatenate([wid[tris[:, 1]], wid[tris[:, 2]], wid[tris[:, 0]]])
    lab = np.arange(wid.max() + 1)
    for _ in range(500):
        m = np.minimum(lab[a], lab[b]); new = lab.copy()
        np.minimum.at(new, a, m); np.minimum.at(new, b, m); new = new[new]
        if (new == lab).all(): break
        lab = new
    return lab[wid]


def rigid_islands(order, w, isl, P, Hh, K, frac=0.42):
    """Small loose pieces (head, hair, eyes, a hand, a hat ...) move as ONE unit: every vertex of the piece gets the piece's bone
    weights (the bones that own most of it). Per-vertex weights would let a piece that sits near the shoulder be torn between the head and the arm bones.
    Big pieces (a whole body, a leg) keep their per-vertex weights so they can bend. -> (order, w, number of pieces made rigid)"""
    order = order.copy(); w = w.copy(); mx = order.shape[1]; count = 0
    idx = np.argsort(isl, kind='stable'); sl = isl[idx]; cuts = np.flatnonzero(np.diff(sl)) + 1
    for g in np.split(idx, cuts):
        if len(g) < 3: continue
        q = P[g]
        if np.linalg.norm(q.max(0) - q.min(0)) >= frac * Hh: continue
        acc = np.zeros(K); np.add.at(acc, order[g].ravel(), w[g].ravel())
        top = np.argsort(-acc)[:mx]; ww = acc[top]; ww = np.where(ww >= 0.6 * ww[0], ww, 0.0); ww = ww / (ww.sum() + 1e-12)      # only the bones that really own the piece
        order[g] = top; w[g] = ww; count += 1
    return order, w, count


def apply_adjust(P, Nn, cx, cy, z0, Hh, adj):
    """The user's fit sliders, applied to a model already scaled/placed on the character. (cx, cy) = pelvis, z0 = the character's feet, Hh = its height.
    The ORDER is what keeps the sliders from fighting each other (each one only does its own job):
      1. size   - width / depth / height stretch along the MODEL's own axes (nothing has been rotated yet, so no shearing)
      2. tilt   - pitch / roll lean the model about the pelvis, in the model's own frame
      3. turn   - yaw spins the whole (tilted) model about the vertical axis, LAST, so turning never changes how it leans
      4. nudge  - dx / dy / dz move it"""
    P = P.copy(); Nn = Nn.copy()
    mult = np.array([float(adj.get('width', 1) or 1), float(adj.get('depth', 1) or 1), float(adj.get('height', 1) or 1)])
    P = (P - [cx, cy, z0]) * mult + [cx, cy, z0]
    Nn = Nn / mult; Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12
    # tilt: pitch = lean forward(+)/back(-), roll = lean to the character's left(+)/right(-), both about the pelvis (at the SAME spot on
    # the model however tall it is, so the Height slider doesn't change the tilt either)
    pz = z0 + 0.5 * Hh * mult[2]
    for ang, ax in ((float(adj.get('pitch', 0) or 0), 0), (float(adj.get('roll', 0) or 0), 1)):
        if not ang: continue
        a_ = np.radians(-ang if ax == 0 else ang); c_, s_ = np.cos(a_), np.sin(a_)
        if ax == 0: R3 = np.array([[1, 0, 0], [0, c_, -s_], [0, s_, c_]])
        else: R3 = np.array([[c_, 0, s_], [0, 1, 0], [-s_, 0, c_]])
        ctr = np.array([cx, cy, pz]); P = (P - ctr) @ R3.T + ctr; Nn = Nn @ R3.T
    yaw = np.radians(float(adj.get('yaw', 0) or 0))
    if yaw:
        c_, s_ = np.cos(yaw), np.sin(yaw); Rz = np.array([[c_, -s_], [s_, c_]])
        P[:, :2] = (P[:, :2] - [cx, cy]) @ Rz.T + [cx, cy]; Nn[:, :2] = Nn[:, :2] @ Rz.T
    P = P + [float(adj.get('dx', 0) or 0), float(adj.get('dy', 0) or 0), float(adj.get('dz', 0) or 0)]
    return P, Nn


def autorig(pos, nrm, rig, up='+Y', forward=None, scale_mult=1.0, max_inf=4, power=3.0, adjust=None, edits=None, tris=None):
    """pos/nrm in source space. Returns dict(pos, nrm, skin_i (N,4), skin_w (N,4), flipped(bool), info)."""
    names = rig['names']; par = rig['parent']; head = np.array(rig['head'], float)
    C = rig_frame(rig); head = head @ C.T
    K = len(names); idx = {n: i for i, n in enumerate(names)}
    roles = classify(names); sidef = side_of
    larm = [i for i, (r, sd) in roles.items() if r in ('upperarm', 'thigh') and sd == 'L']
    if larm and np.median([head[i][0] for i in larm]) < 0:       # the skeleton's "left" bones sit on the character's right: swap sides
        flip = {'L': 'R', 'R': 'L', 'C': 'C'}
        roles = {i: (r, flip[sd]) for i, (r, sd) in roles.items()}; sidef = lambda n: flip[side_of(n)]
    forward = forward or detect_forward(pos, up, humanoid=True)
    B = axis_basis(up, forward)
    P = pos @ B.T; Nn = nrm @ B.T
    det_flip = np.linalg.det(B) < 0
    # --- scale & place
    H = P[:, 2].max() - P[:, 2].min()
    s = rig['ref_height'] / H * scale_mult
    P = (P - [0, 0, P[:, 2].min()]) * s + [0, 0, rig['ref_min_z']]
    zr = P[:, 2] - rig['ref_min_z']                      # height above the character's own feet (some rigs sit well below / above z=0)
    mid = (zr > 0.35 * rig['ref_height']) & (zr < 0.65 * rig['ref_height'])
    if not mid.any(): mid = np.ones(len(P), bool)
    pel = [i for i, (r, sd) in roles.items() if r == 'pelvis']
    pel_h = head[pel[0]] if pel else np.array([0, 0, rig['ref_min_z'] + 0.5 * rig['ref_height']])
    P[:, 0] -= np.median(P[mid, 0]) - pel_h[0]
    P[:, 1] -= np.median(P[mid, 1]) - pel_h[1]
    Hh = rig['ref_height']
    adj = adjust or {}
    if adj:      # user fit (size, tilt, turn, nudge). Done BEFORE weighting so the skinning follows
        P, Nn = apply_adjust(P, Nn, pel_h[0], pel_h[1], rig['ref_min_z'], Hh, adj)
    # --- source skeleton (match arm pose)
    src = head.copy(); R = [np.eye(3)] * K; kscale = [1.0] * K
    R = list(R)
    for sd, sg in (('L', +1), ('R', -1)):
        ch = {r: i for i, (r, ss) in roles.items() if ss == sd and r in ('upperarm', 'lowerarm', 'hand', 'clavicle')}
        if not all(k in ch for k in ('upperarm', 'lowerarm', 'hand')): continue
        sh = head[ch['upperarm']]
        cand = (P[:, 2] - rig['ref_min_z'] > 0.35 * Hh) & (sg * P[:, 0] > 0.10 * Hh)
        if cand.sum() < 30: continue
        d2 = np.linalg.norm(P[cand] - sh, axis=1)
        far = np.argsort(-d2)[:max(10, int(0.01 * cand.sum()))]
        tip = P[cand][far].mean(0)
        dsrc = (tip - sh); mesh_len = np.linalg.norm(dsrc); dsrc /= mesh_len
        fin = [i for i, n in enumerate(names) if sidef(n) == sd and re.search(r'middle_?0?3|index_?0?3', snake(n))]
        end = head[fin[0]] if fin else head[ch['hand']] + (head[ch['hand']] - head[ch['lowerarm']]) * 0.6
        rig_len = np.linalg.norm(end - sh)
        fr = {k: np.linalg.norm(head[ch[k]] - sh) / rig_len for k in ('lowerarm', 'hand')}
        for k in ('lowerarm', 'hand'): src[ch[k]] = sh + dsrc * mesh_len * fr[k]
        # rotation for each arm bone: source chain direction -> target direction
        chain = [ch['upperarm'], ch['lowerarm'], ch['hand']]
        ends = [head[ch['lowerarm']], head[ch['hand']], end]
        kk = rig_len / mesh_len
        for b, e in zip(chain, ends):
            R[b] = _rot(dsrc, e - head[b]); kscale[b] = kk
        if 'clavicle' in ch:
            R[ch['clavicle']] = np.eye(3)
        # fingers follow the hand
        for i in range(K):
            p = par[i]
            while p >= 0 and p != ch['hand']: p = par[p]
            if p == ch['hand']: src[i] = src[ch['hand']] + (head[i] - head[ch['hand']]); R[i] = R[ch['hand']]; kscale[i] = kk
    # --- bone segments of the source skeleton for weighting
    dbones = sorted(roles)
    kids = {i: [j for j in range(K) if par[j] == i] for i in range(K)}
    seg = {}
    for b in dbones:
        r, sd = roles[b]
        if r == 'foot':
            a = src[b]; seg[b] = (a, a + np.array([0, 0.13 * Hh, -0.55 * (a[2] - rig['ref_min_z'])]))
        elif r == 'hand':
            fin = [i for i, n in enumerate(names) if sidef(n) == sd and re.search(r'middle_?0?2', snake(n))]
            seg[b] = (src[b], src[fin[0]] if fin else src[b] + (src[b] - src[par[b]]) * 0.6)
        elif r == 'head':
            a = src[b]; seg[b] = (a, a + np.array([0, 0, 0.1 * Hh]))
        else:
            ks = [k for k in kids[b] if k in roles]
            if not ks and r in ('thigh', 'calf'): tail = np.array([src[b][0], src[b][1], rig['ref_min_z'] + 0.03 * Hh])     # the leg chain ends here (no knee/ankle bones): this bone carries the rest of the leg
            else: tail = src[ks[0]] if ks else src[b] + (src[b] - src[par[b]]) * 0.5
            seg[b] = (src[b], tail)
    # --- weights
    N = len(P); D = np.full((N, K), np.inf)
    for b in dbones:
        r, sd = roles[b]; a, t = seg[b]
        d = _seg_dist(P, a, t)
        if r in ('upperarm', 'lowerarm', 'hand', 'clavicle', 'thigh', 'calf', 'foot'):
            wrong = (P[:, 0] < -0.01 * Hh) if sd == 'L' else (P[:, 0] > 0.01 * Hh)
            d = np.where(wrong, d + 0.25 * Hh, d)       # soft left/right constraint
        D[:, b] = d
    order = np.argsort(D, axis=1)[:, :max_inf]
    dd = np.take_along_axis(D, order, 1)
    w = 1.0 / (dd + 0.01 * Hh) ** power
    w[dd > dd[:, :1] * 3.0 + 0.03 * Hh] = 0          # drop far-away influences
    w[:, 0] = np.where(w.sum(1) <= 0, 1.0, w[:, 0])       # never leave a vertex with no weight at all
    w /= w.sum(1, keepdims=True)
    n_rigid = 0
    if tris is not None and len(tris):                    # loose pieces of your model move as one unit (see rigid_islands)
        order, w, n_rigid = rigid_islands(order, w, find_islands(pos, tris), P, Hh, K)
    # --- LBS: source pose -> bind pose. Only when 'match_pose' is on: the default keeps your model exactly the shape/pose it has (just scaled + placed),
    # and only uses the matched skeleton to decide which bone owns which vertex.
    match = bool((adjust or {}).get('match_pose'))
    newP = np.zeros_like(P); newN = np.zeros_like(P)
    for j in range(order.shape[1] if match else 0):
        b = order[:, j]; wj = w[:, j:j + 1]
        for bi in np.unique(b):
            m = b == bi
            newP[m] += wj[m] * (head[bi] + kscale[bi] * (P[m] - src[bi]) @ R[bi].T)
            newN[m] += wj[m] * (Nn[m] @ R[bi].T)
    if not match: newP = P.copy(); newN = Nn.copy()
    newN /= np.linalg.norm(newN, axis=1, keepdims=True) + 1e-12
    from . import edit
    vg, piv = edit.auto_groups(rig, roles, order, w, head)
    newP, newN, hidden = edit.apply_edits(newP, newN, vg, piv, edits)            # hide / move / size / rotate body parts (character frame)
    newP = newP @ C; newN = newN @ C                      # back to the game's axes
    return dict(pos=newP, nrm=newN, p_scaled=(P @ C), skin_i=order.astype(np.int32), skin_w=w, mirrored=bool(det_flip), hidden=hidden, vgroup=vg, piv=piv,
                info=dict(forward=forward, scale=s, up=up, roles=roles, rigid_pieces=n_rigid, pivot=[float(pel_h[0]), float(pel_h[1]), float(rig['ref_min_z'])]))
