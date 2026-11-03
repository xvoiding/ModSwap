"""Which way is UP for a Unity model, so it is drawn standing and a swap is built the right way round.

Unity's world is y-up, but a model's own vertex data often is not: models exported with z-up (FBX / Blender / 3ds Max) carry a -90 degree rotation on their GameObject (or their armature) that
stands them up in the game. The viewer and the builder used to ignore that rotation, so such models showed lying on their face (and would have been built that way). Here the rotation is read from
the Transform chain, snapped to a clean 90-degree turn, and (for characters with a skeleton) checked against the skeleton: the head must be above the feet.

R maps the model's own vertex space to the 'standing' unity frame (x right, y up, z forward):   upright = local @ R.T        local = upright @ R"""
import itertools
import numpy as np

EYE = np.eye(3)


def _quat3(q, s):
    x, y, z, w = q; n = x * x + y * y + z * z + w * w
    if n < 1e-12: x = y = z = 0.0; w = 1.0; n = 1.0
    x, y, z, w = [v / np.sqrt(n) for v in (x, y, z, w)]
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    return R * np.array(s, float)[None, :]


def polar_rotation(M):
    """the rotation part of a 3x3 matrix that may also scale (a proper rotation, never a mirror)"""
    u, _, vt = np.linalg.svd(np.asarray(M, float)); R = u @ vt
    if np.linalg.det(R) < 0: u[:, -1] *= -1; R = u @ vt
    return R


def _signed_perms():
    out = []
    for p in itertools.permutations(range(3)):
        for s in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3)); [R.__setitem__((i, p[i]), s[i]) for i in range(3)]
            if np.linalg.det(R) > 0: out.append(R)
    return out


PERMS = _signed_perms()          # the 24 ways of turning a model by multiples of 90 degrees


def snap(R, tol_deg=15.0):
    """the closest 90-degree turn to R (R itself when it is not close to one: a model deliberately tilted)"""
    best = max(PERMS, key=lambda P: float(np.trace(P.T @ R))); c = (np.trace(best.T @ R) - 1) / 2
    return best if np.degrees(np.arccos(np.clip(c, -1, 1))) <= tol_deg else np.asarray(R, float)


def world_rotation(tf, go_pid):
    """tf = {'go': {game object id: transform id}, 'tf': {transform id: dict(father, q, s)}}: rotation of the GameObject's world transform (all parents included); identity when unknown"""
    t = tf['go'].get(go_pid); M = np.eye(3); hops = 0
    while t is not None and t in tf['tf'] and hops < 100:
        e = tf['tf'][t]; M = _quat3(e['q'], e['s']) @ M; t = e['father'] if e['father'] in tf['tf'] else None; hops += 1
    return polar_rotation(M)


def transform_table(O):
    """read every Transform of a serialized file once: -> {'go': {game object: transform}, 'tf': {transform: dict(father, q, s)}}"""
    go = {}; tfs = {}
    for pid, o in O.items():
        if o.type.name != 'Transform': continue
        try:
            t = o.read(); g = t.m_GameObject.path_id
            tfs[pid] = dict(father=t.m_Father.path_id, q=(t.m_LocalRotation.x, t.m_LocalRotation.y, t.m_LocalRotation.z, t.m_LocalRotation.w), s=(t.m_LocalScale.x, t.m_LocalScale.y, t.m_LocalScale.z)); go[g] = pid
        except Exception: continue
    return dict(go=go, tf=tfs)


def from_skeleton(names, heads, classify):
    """rotation that stands a skeleton up: from the feet / hips to the head / neck along the model's own axes, snapped. Left-right comes from the arms (or legs), so the character also faces the right way.
    None when the skeleton does not look like a person (no head and feet)."""
    roles = classify(names); heads = np.asarray(heads, float)
    pick = lambda *rs, side=None: [i for i, (r, s) in roles.items() if r in rs and (side is None or s == side)]
    top = pick('head', 'neck'); low = pick('foot', 'calf', 'thigh') or pick('pelvis')
    if not top or not low: return None
    u = heads[top].mean(0) - heads[low].mean(0)
    if np.linalg.norm(u) < 1e-9: return None
    a = int(np.argmax(np.abs(u))); up = np.zeros(3); up[a] = np.sign(u[a])
    L = pick('upperarm', 'thigh', 'clavicle', side='L'); Rr = pick('upperarm', 'thigh', 'clavicle', side='R')
    best = None
    for R in PERMS:
        if not np.allclose(R @ up, [0, 1, 0]): continue
        score = 0.0
        if L and Rr:                                      # the character's left must come out on the left: right = (R @ (L - R bones)) should point to -x
            lat = R @ (heads[Rr[0]] - heads[L[0]]); score = float(lat[0])
        if best is None or score > best[0]: best = (score, R)
    return None if best is None else best[1]


def choose(R_transform, names=None, heads=None, classify=None):
    """-> (R, how): the rotation from the transforms when the skeleton agrees (or there is none), otherwise the one the skeleton says"""
    R = snap(np.asarray(R_transform, float)); how = 'transforms' if not np.allclose(R, EYE) else 'none needed'
    if names is not None and heads is not None and classify is not None:
        sk = from_skeleton(names, heads, classify)
        if sk is not None:
            roles = classify(names); H = np.asarray(heads, float) @ R.T
            top = [i for i, (r, _) in roles.items() if r in ('head', 'neck')]; low = [i for i, (r, _) in roles.items() if r in ('foot', 'calf', 'thigh')] or [i for i, (r, _) in roles.items() if r == 'pelvis']
            d = H[top].mean(0) - H[low].mean(0)
            if d[1] < 0.8 * np.linalg.norm(d): R, how = sk, 'skeleton'                      # the head is not above the feet: trust the skeleton
    return R, how
