"""Read a skeleton (bone names, parents, bind-pose head positions) out of a cooked UE4 SkeletalMesh."""
import numpy as np
from .uepkg import parse_uasset
from .skmesh import walk


def _qm(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def facing_from_mesh(pos):
    """Which way the original character faces, from the mesh itself: toes stick out in front of the leg axis.
    Returns a unit 3-vector along X or Y (game space, Z up), or None when it can't tell. Bone names can be mirrored, geometry can't."""
    z = pos[:, 2]; z0 = float(z.min()); H = float(z.max() - z0)
    feet = pos[z < z0 + 0.04 * H]; legs = pos[(z > z0 + 0.15 * H) & (z < z0 + 0.30 * H)]
    if len(feet) < 10 or len(legs) < 10: return None
    best = None
    for a in (0, 1):
        dd = float(feet[:, a].mean() - np.median(legs[:, a]))
        if best is None or abs(dd) > abs(best[0]): best = (dd, a)
    if abs(best[0]) < 0.01 * H: return None
    f = [0.0, 0.0, 0.0]; f[best[1]] = 1.0 if best[0] > 0 else -1.0
    return f


def read_mesh(base, exp_idx=1, rtmask=False, adj=None, trail=None, v423=False, ue5=False):
    """LOD0 (positions (N,3), triangles (T,3)) of a cooked SkeletalMesh, in game space."""
    d = parse_uasset(open(base + '.uasset', 'rb').read()); u = open(base + '.uexp', 'rb').read()
    L = walk(u, d, exp_idx=exp_idx, verbose=False, rtmask=rtmask, adj=adj, trail=trail, v423=v423, ue5=ue5)['lods'][0]
    pos = np.frombuffer(u[L['pos']['start']:L['pos']['end']], dtype='<f4').reshape(-1, 3).astype(np.float64)
    ix = L['idx']; ind = np.frombuffer(u[ix['start']:ix['end']], dtype='<u2' if ix['isz'] == 2 else '<u4').astype(np.int64)
    return pos, ind[:len(ind) // 3 * 3].reshape(-1, 3)


def extract_rig(base, exp_idx=1, rtmask=False, ref_height=None, ref_min_z=None, adj=None, trail=None, v423=False, ue5=False):
    """base = path to SK_xxx without extension. Returns the rig dict skin.autorig() expects."""
    d = parse_uasset(open(base + '.uasset', 'rb').read()); u = open(base + '.uexp', 'rb').read()
    o = walk(u, d, exp_idx=exp_idx, verbose=False, rtmask=rtmask, adj=adj, trail=trail, v423=v423, ue5=ue5)
    G, names, par = [], [], []
    for i, (ni, nn, p) in enumerate(o['bones']):
        q = o['pose'][i]; M = np.eye(4); M[:3, :3] = _qm(q[:4]); M[:3, 3] = q[4:7]
        G.append(M if p < 0 else G[p] @ M); names.append(d['names'][ni]); par.append(p)
    L = o['lods'][0]
    pos = np.frombuffer(u[L['pos']['start']:L['pos']['end']], dtype='<f4').reshape(-1, 3)
    return dict(names=names, parent=par, head=[g[:3, 3].tolist() for g in G],
                bonemap=list(L['sections'][0]['bonemap']),
                mesh_min=pos.min(0).tolist(), mesh_max=pos.max(0).tolist(), facing=facing_from_mesh(pos),
                ref_height=float(ref_height if ref_height else pos[:, 2].max() - pos[:, 2].min()),
                ref_min_z=float(ref_min_z if ref_min_z is not None else pos[:, 2].min()))


def mesh_zrange(base, exp_idx=1, rtmask=False, adj=None, trail=None, v423=False, ue5=False):
    """(min_z, max_z) of LOD0 vertex positions of a SkeletalMesh."""
    d = parse_uasset(open(base + '.uasset', 'rb').read()); u = open(base + '.uexp', 'rb').read()
    L = walk(u, d, exp_idx=exp_idx, verbose=False, rtmask=rtmask, adj=adj, trail=trail, v423=v423, ue5=ue5)['lods'][0]
    pos = np.frombuffer(u[L['pos']['start']:L['pos']['end']], dtype='<f4').reshape(-1, 3)
    return float(pos[:, 2].min()), float(pos[:, 2].max())
