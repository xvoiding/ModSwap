"""Keep the 3D viewer responsive. The viewer builds its meshes (and an edge mesh for the outline) on the app's UI thread, so a character with 200,000 triangles, or a huge user model,
freezes the window ("Not responding") on every slider change. The viewer only needs a recognisable shape, so it gets a reduced copy: a PLAN picks which vertices to keep (grid clustering,
the finest grid that still fits the triangle budget) once, and the plan is applied to every later fit of the same model. Builds never use this: game files are made from the full model."""
import zlib
import numpy as np

OUTLINE_TRIS = 14000          # the faint original character
MODEL_TRIS = 90000            # your model
_PLANS = {}


def _clean(T):
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    if not len(T): return T
    _, first = np.unique(np.sort(T, axis=1), axis=0, return_index=True); return T[np.sort(first)]


def plan(pos, tris, cap):
    """-> (keep: indices of the vertices to keep, tris: triangles in the kept numbering) or None when the mesh already fits"""
    tris = np.asarray(tris, np.int64)
    if len(tris) <= cap: return None
    pos = np.asarray(pos, np.float64); lo = pos.min(0); ext = float(max((pos.max(0) - lo).max(), 1e-9))
    def cluster(res):
        q = np.minimum(np.floor((pos - lo) / ext * res), res - 1).astype(np.int64)
        return np.unique((q[:, 0] * res + q[:, 1]) * res + q[:, 2], return_inverse=True)[1].ravel()
    a, b, best = 4, 1024, None
    while a <= b:
        mid = (a + b) // 2; inv = cluster(mid); T = inv[tris]; T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
        if len(T) > 3 * cap: b = mid - 1; continue                             # clearly too many: no need to look for duplicates
        T = _clean(T)
        if len(T) <= cap: best = (inv, T); a = mid + 1
        else: b = mid - 1
    inv, T = best if best is not None else (cluster(4), _clean(cluster(4)[tris]))
    first = np.unique(inv, return_index=True)[1]                           # one real vertex per cluster
    used, new = np.unique(T, return_inverse=True)
    return first[used], new.reshape(-1, 3).astype(np.int64)


def cached_plan(key, pos, tris, cap):
    k = (key, len(tris), zlib.crc32(np.ascontiguousarray(tris, np.int64).tobytes()), cap)
    if k not in _PLANS:
        if len(_PLANS) > 8: _PLANS.pop(next(iter(_PLANS)))
        _PLANS[k] = plan(pos, tris, cap)
    return _PLANS[k]


def apply(p, tris, *arrays):
    """-> (tris, *arrays) for the plan (unchanged when the plan is None)"""
    if p is None: return (tris,) + tuple(arrays)
    keep, T = p; return (T,) + tuple(None if a is None else np.asarray(a)[keep] for a in arrays)


def outline(key, pos, tris, cap=OUTLINE_TRIS):
    """-> (pos, tris) for the faint original character"""
    T, P = apply(cached_plan(key, pos, tris, cap), tris, pos); return np.asarray(P, np.float32), T


def model(key, pos, tris, uv, group, cap=MODEL_TRIS):
    """-> (pos, tris, uv, group) for the user's model (uv / group have one row per vertex)"""
    T, P, U, G = apply(cached_plan(key, pos, tris, cap), tris, pos, uv, group); return np.asarray(P, np.float32), T, U, G
