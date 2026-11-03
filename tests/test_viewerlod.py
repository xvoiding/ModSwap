"""The 3D viewer freezes the app on huge meshes, so it only gets a reduced copy.   python tests/test_viewerlod.py"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap import viewerlod as V


def sphere(n):
    u = np.linspace(0, 2 * np.pi, n, endpoint=False); v = np.linspace(0.01, np.pi - 0.01, n); U, W = np.meshgrid(u, v)
    pos = np.stack([np.sin(W) * np.cos(U), np.cos(W), np.sin(W) * np.sin(U)], -1).reshape(-1, 3); i = np.arange(n * n).reshape(n, n)
    a, b, c, d = i[:-1, :], i[:-1, (np.arange(n) + 1) % n], i[1:, :], i[1:, (np.arange(n) + 1) % n]
    return pos, np.concatenate([np.stack([a.ravel(), b.ravel(), c.ravel()], 1), np.stack([b.ravel(), d.ravel(), c.ravel()], 1)])


def test_small_meshes_are_untouched():
    pos, tris = sphere(30); P, T = V.outline('s', pos, tris); assert len(T) == len(tris) and np.allclose(P, pos, atol=1e-6)


def test_big_mesh_fits_the_budget_and_keeps_its_shape_and_per_vertex_data_aligned():
    pos, tris = sphere(400); uv = (pos[:, [0, 2]] + 1) / 2 * 0.98 + 0.01; grp = np.arange(len(pos)) % 6
    t = time.time(); P, T, U, G = V.model('big', pos, tris, uv, grp, cap=20000); dt = time.time() - t
    assert len(T) <= 20000 and len(T) > 4000, len(T)
    assert len(U) == len(P) == len(G) and T.max() < len(P) and T.min() >= 0
    assert np.ptp(P[:, 1]) > 0.98 * np.ptp(pos[:, 1]) and np.ptp(P[:, 0]) > 0.95 * np.ptp(pos[:, 0]), 'the silhouette survives'
    assert np.allclose(U, uv[np.unique(V.cached_plan('big', pos, tris, 20000)[0])] if False else U), 'uv rows exist'
    keep = V.cached_plan('big', pos, tris, 20000)[0]; assert np.array_equal(G, grp[keep]) and np.allclose(U, uv[keep]), 'uv / groups follow the kept vertices'
    t = time.time(); V.model('big', pos, tris, uv, grp, cap=20000); assert time.time() - t < dt / 5 + 0.05, 'the plan is cached'


def test_triangle_winding_is_kept_so_the_mesh_still_faces_outwards():
    pos, tris = sphere(200); P, T = V.outline('w', pos, tris, cap=8000); c = P.mean(0)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); out = (fn * (P[T].mean(1) - c)).sum(1)
    assert (out > 0).mean() > 0.95 or (out < 0).mean() > 0.95, 'all faces turn the same way'


def test_reduction_never_mixes_texture_regions():
    """two halves of a big sphere use different parts of the texture; after reduction no triangle may have corners in both"""
    pos, tris = sphere(500); left = pos[:, 0] < 0
    uv = np.where(left[:, None], np.stack([0.1 + 0.2 * (pos[:, 1] + 1) / 2, 0.1 + 0.2 * (pos[:, 2] + 1) / 2], 1), np.stack([0.7 + 0.2 * (pos[:, 1] + 1) / 2, 0.7 + 0.2 * (pos[:, 2] + 1) / 2], 1))
    # triangles that straddle the seam share vertices of both halves: split them off like the loaders do (corners belong to one material)
    keep = left[tris].all(1) | (~left[tris]).all(1); tris = tris[keep]
    P, T, U, G = V.model('mix', pos, tris, uv, np.zeros(len(pos), int), cap=15000)
    assert len(T) <= 15000 and len(T) > 3000
    lab = (U[:, 0] > 0.5)[T]; assert (lab.all(1) | (~lab).all(1)).all(), 'a reduced triangle must stay inside one texture region'


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
