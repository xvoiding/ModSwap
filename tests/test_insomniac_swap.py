"""Fitting a user model onto Spider-Man's skeleton and writing the asset.   python tests/test_insomniac_swap.py
The pipeline test needs a real classic-suit model (env SPIDERMAN_MODEL or the collector's output) and is skipped without one."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from modswap.insomniac import model as M, swap as S, rig as R
from humanoid_fixture import humanoid


def test_split_parts_limits_and_keeps_every_triangle():
    rng = np.random.default_rng(2); n = 500
    pos = rng.normal(size=(n, 3)); nrm = pos / np.linalg.norm(pos, axis=1, keepdims=True); uv = rng.uniform(size=(n, 2)); tris = rng.integers(0, n, (900, 3)); skins = [[(i % 7, 1.0)] for i in range(n)]
    parts = S.split_parts(pos, nrm, uv, tris, skins, limit=120)
    assert len(parts) > 3 and all(len(p['pos']) <= 120 for p in parts) and sum(len(p['tris']) for p in parts) == 900
    flat = np.concatenate([p['pos'][p['tris']] for p in parts])
    assert np.allclose(flat.reshape(-1, 3), pos[tris].reshape(-1, 3)), 'triangles must keep their corners, in order'
    for p in parts:
        assert p['tris'].max() < len(p['pos']) and len(p['skin']) == len(p['pos']) == len(p['uv']) == len(p['nrm'])
    one = S.split_parts(pos, nrm, uv, tris, skins); assert len(one) == 1 and len(one[0]['pos']) <= n


def test_frame_swap_is_its_own_inverse():
    p = np.random.default_rng(1).normal(size=(10, 3)); assert np.array_equal(R.from_model_space(R.to_model_space(p)), p) and np.array_equal(R.to_model_space(p)[:, 1], p[:, 2])


def test_skins_from_autorig_drops_zero_weights():
    out = S.skins_from_autorig(np.array([[3, 4, 5, 6], [1, 1, 1, 1]]), np.array([[0.7, 0.3, 0.0, 0.0], [1.0, 0, 0, 0]]))
    assert out[0] == [(3, 0.7), (4, 0.3)] and out[1] == [(1, 1.0)]


def real_model():
    for p in (os.environ.get('SPIDERMAN_MODEL'), '/tmp/sm2/assets/BF45D48B5314EC76.bin'):
        if p and os.path.isfile(p): return open(p, 'rb').read()


def test_real_suit_pipeline_with_a_humanoid():
    raw = real_model()
    if raw is None: print('   (no real model available: skipped)'); return
    orig = M.Model(raw); fitted = S.fit(orig, humanoid(), up='+Y', forward='+Z', log=lambda *a: None); asset, atl = S.build(orig, fitted, material=5, log=lambda *a: None)
    new = M.Model(asset); st = new.streams(); P = st['pos']; sk = new.skin(); js = new.joints()
    assert new.vertex_count == len(humanoid().pos) and abs((P[:, 1].max() - P[:, 1].min()) - 1.81) < 0.05, 'fitted to the suit\'s height'
    dom = lambda v: js[max(sk[v], key=lambda t: t[1])[0]].name
    head = np.flatnonzero(P[:, 1] > 1.58); assert all(dom(v) == 'head' for v in head)
    assert all(dom(v) in ('LF_wrist', 'LF_loarm') for v in np.flatnonzero(P[:, 0] > 0.55)), 'the character\'s left arm tip must be skinned to the left (LF_) arm'
    assert all(dom(v) in ('RT_wrist', 'RT_loarm') for v in np.flatnonzero(P[:, 0] < -0.55))
    A = np.array(Image.fromarray(atl)); UV = st['uv'] * M.UV_SCALE; col = A[(UV[:, 1] * A.shape[0]).astype(int), (UV[:, 0] * A.shape[1]).astype(int)]
    PAL = np.array([(200, 40, 40), (230, 190, 150), (40, 160, 60), (40, 60, 200), (170, 60, 200), (220, 200, 40)])          # torso, head, left arm, right arm, left leg, right leg
    nearest = lambda c: np.argmin(((c.astype(int)[:, None, :] - PAL[None]) ** 2).sum(2), 1)
    assert np.mean(nearest(col[P[:, 0] > 0.55]) == 2) > 0.97, 'the left arm must carry the left-arm texture cell'
    assert np.mean(nearest(col[P[:, 0] < -0.55]) == 3) > 0.97, 'the right arm must carry the right-arm texture cell'
    assert np.mean(nearest(col[P[:, 1] > 1.58]) == 1) > 0.97, 'the head must carry the head texture cell'
    assert new.sections[M.TAG_INDEX][1] > 0 and new.part1 + new.part2 == len(asset) - 36


def test_too_many_parts_is_a_clear_error():
    raw = real_model()
    if raw is None: return
    orig = M.Model(raw); fitted = S.fit(orig, humanoid(), up='+Y', forward='+Z', log=lambda *a: None)
    old = S.MAX_PART_VERTS; S.MAX_PART_VERTS = 2
    try:
        try: S.build(orig, dict(fitted), material=5, log=lambda *a: None); raise AssertionError('should refuse')
        except (ValueError, TypeError) as e: assert 'mesh parts' in str(e) or isinstance(e, TypeError)
    finally: S.MAX_PART_VERTS = old


def test_offset_sliders_are_centimetres_not_metres():
    raw = real_model()
    if raw is None: print('   (no real model available: skipped)'); return
    orig = M.Model(raw); h = humanoid(); quiet = lambda *a: None
    base = S.fit(orig, h, up='+Y', forward='+Z', log=quiet)['pos']
    for k, axis in (('dx', 0), ('dy', 2), ('dz', 1)):                                   # model frame: x = left, y = up, z = forward
        d = (S.fit(orig, h, up='+Y', forward='+Z', adjust={k: 10.0}, log=quiet)['pos'] - base).mean(0) * 100
        assert abs(d[axis] - 10) < 0.01 and abs(np.delete(d, axis)).max() < 0.01, (k, d)
    f0 = S.fit(orig, h, up='+Y', forward='+Z', log=quiet); f1 = S.fit(orig, h, up='+Y', forward='+Z', edits={'g': {'1': {'move': [0, 0, 10]}}, 'c': []}, log=quiet)
    sel = f0['vgroup'] == 1; d = f1['pos'] - f0['pos']
    assert sel.any() and abs(d[sel].mean(0)[1] * 100 - 10) < 0.01 and np.abs(d[~sel]).max() < 1e-9, 'a 10 cm part move moves that part 10 cm'


def test_scale_lengths_only_touches_moves_and_pivots():
    from modswap import edit
    e = {'g': {'2': {'move': [10, 0, -5], 'scale': 1.5, 'rot': [0, 0, 30]}}, 'c': [{'mask': 'x', 'move': [0, 20, 0], 'pivot': [100, 0, 50], 'scale': 2}]}
    o = edit.scale_lengths(e, 0.01)
    assert o['g']['2']['move'] == [0.1, 0.0, -0.05] and o['g']['2']['scale'] == 1.5 and o['g']['2']['rot'] == [0, 0, 30]
    assert o['c'][0]['move'] == [0.0, 0.2, 0.0] and o['c'][0]['pivot'] == [1.0, 0.0, 0.5] and o['c'][0]['mask'] == 'x' and e['g']['2']['move'] == [10, 0, -5], 'the original is not changed'
    assert edit.scale_lengths(None, 0.01) is None


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
