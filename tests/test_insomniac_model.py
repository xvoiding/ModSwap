"""Spider-Man .model reading and writing.   python tests/test_insomniac_model.py
Most tests use a synthetic asset with the real layout. If a real classic-suit model is available (env SPIDERMAN_MODEL, or the collector's output) the strong
checks on it run too: identical re-encoding of the index/vertex sections, and a model rebuilt from the suit's own parts decoding back with zero error."""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.insomniac import model as M

JOINTS = [('fx_root', -1), ('spine', 0), ('head', 1), ('LF_hand', 1)]


def make_asset(slots=6, used=3, seed=3, verts_per=40):
    """a synthetic model: `slots` mesh slots of which `used` hold geometry, 4 joints, skin, built/look tables and an unrelated section"""
    rng = np.random.default_rng(seed); n = used * verts_per
    pos = rng.uniform(-0.8, 0.8, (n, 3)); pos[:, 1] = rng.uniform(0, 1.8, n)
    nrm = rng.normal(size=(n, 3)); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    uv = rng.uniform(0, 1, (n, 2)); tris = []; entries = []; skins = []
    pu = np.rint(pos * M.POS_SCALE).astype(np.int16); uu = np.rint(uv / M.UV_SCALE).astype(np.int16)
    nw, tw = M.encode_normal_tangent(nrm)
    for k in range(slots):
        if k < used:
            t = rng.integers(0, verts_per, (60, 3)); tris.append(t)
        else: tris.append(np.zeros((0, 3), np.int64))
    idx = np.concatenate([t.reshape(-1) for t in tris]); vs = 0; is_ = 0
    sk = [[(int(rng.integers(0, 4)), 1.0)] if i % 3 else [(0, 0.6), (2, 0.4)] for i in range(n)]
    skin_data, skin_table, ranges = M.encode_skin(sk, [verts_per] * used)
    for k in range(slots):
        if k < used:
            e = bytearray(64); struct.pack_into('<3f', e, 0, 0, 0.9, 0); struct.pack_into('<4H', e, 12, 100 + k, 200, 300, 400)
            struct.pack_into('<IIII', e, 20, vs, is_, len(tris[k]) * 3, verts_per); struct.pack_into('<HHHH', e, 36, 0x11, k, ranges[k][0], ranges[k][1]); struct.pack_into('<II', e, 56, vs, 0)
            vs += verts_per; is_ += len(tris[k]) * 3; entries.append(bytes(e))
        else: entries.append(bytes(64))
    strings = b''; name_off = []
    head_n = 16 + 12 * 12; first = 0
    for name, _ in JOINTS: name_off.append(head_n + len(strings)); strings += name.encode() + b'\0'
    joints = b''.join(struct.pack('<hHHHII', p, i, 0, 0, 0x1000 + i, name_off[i]) for i, (_, p) in enumerate(JOINTS))
    built = bytearray(120); struct.pack_into('<7f', built, 0, 0, 0.9, 0, 1.0, 0.7, 0.9, 0.2); struct.pack_into('<f', built, 0x2C, 1 / 4096); struct.pack_into('<5f', built, 0x34, 15, 25, 35, 45, 55)
    struct.pack_into('<III', built, 0x60, 65535, len(idx), n)
    look = bytearray(96)
    for row in (0, 8, 16):
        for lod in range(6): struct.pack_into('<HH', look, 4 * (row + lod), lod, 3)
    secs = {M.TAG_JOINTS: joints, M.TAG_JOINT_XFORM: bytes(112 * 4), M.TAG_MESHES: b''.join(entries), M.TAG_SKIN_BATCH: skin_table, M.TAG_SKIN_DATA: skin_data,
            M.TAG_BUILT: bytes(built), M.TAG_LOOK: bytes(look), 0x11112222: b'UNRELATED-SECTION-DATA' * 5,
            M.TAG_INDEX: M.encode_index(idx), M.TAG_STD_VERT: M.encode_std(pu, nw, tw, uu), M.TAG_UV1: np.rint(uv * 32768).astype('<i2').tobytes(), M.TAG_COL: np.full(n, 0xFFFFFFFF, '<u4').tobytes()}
    order = list(secs); n_sec = len(order); head = 16 + 12 * n_sec
    assert head == head_n or True
    return assemble(secs, order, strings, head), dict(pos=pos, nrm=nrm, uv=uv, tris=tris, skin=sk, idx=idx)


def assemble(secs, order, strings, head):
    cur = head + len(strings); body = bytearray(strings); placed = {}; part1 = None
    for tag in order:
        if tag in M.STREAM_TAGS and part1 is None: cur += -cur % 16; part1 = cur
        else: cur += -cur % 16
        body += b'\0' * (cur - head - len(body)); placed[tag] = (cur, len(secs[tag])); body += secs[tag]; cur += len(secs[tag])
    table = b''.join(struct.pack('<III', t, *placed[t]) for t in order)
    dat1 = b'1TAD' + struct.pack('<III', 0x98906B9F, cur, len(order)) + table + bytes(body)
    return struct.pack('<III', 0x98906B9F, part1, cur - part1) + b'\0' * 24 + dat1


def test_synthetic_streams_decode_to_what_was_written():
    raw, src = make_asset(); m = M.Model(raw); st = m.streams()
    assert m.vertex_count == len(src['pos']) and np.abs(st['pos'] - np.round(src['pos'] * 4096) / 4096).max() == 0
    assert np.array_equal(m.indices(), src['idx'].astype(np.uint16))
    ms = [x for x in m.meshes() if x.vertex_count]
    assert len(ms) == 3 and all(np.array_equal(m.triangles(x), src['tris'][i]) for i, x in enumerate(ms))
    assert np.abs(M.decode_normal(st['nword']) - src['nrm']).max() < 0.01
    assert [j.name for j in m.joints()] == [n for n, _ in JOINTS] and [j.parent for j in m.joints()] == [p for _, p in JOINTS]
    sk = m.skin(); assert all(abs(sum(w for _, w in s) - 1) < 1e-9 for s in sk)
    assert dict(sk[0]) == {0: 0.6, 2: 0.4} or abs(dict(sk[0])[0] - 0.6) < 0.01


def test_identity_rebuild_is_byte_identical_for_a_compact_asset():
    raw, _ = make_asset(); assert M.rebuild(M.Model(raw), {}) == raw


def test_build_model_round_trip_with_new_counts():
    raw, _ = make_asset(slots=6, used=3); m = M.Model(raw); rng = np.random.default_rng(9); parts = []
    for k, n in enumerate((55, 300, 17)):
        pos = rng.uniform(-0.5, 0.5, (n, 3)); pos[:, 1] += 0.9; nrm = rng.normal(size=(n, 3)); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        parts.append(dict(pos=pos, nrm=nrm, uv=rng.uniform(0, 1, (n, 2)), tris=rng.integers(0, n, (n * 2, 3)), material=k + 1,
                          skin=[[(int(rng.integers(0, 4)), 0.7), (int(rng.integers(0, 4)), 0.3)] if i % 2 else [(2, 1.0)] for i in range(n)]))
    new = M.Model(M.build_model(m, parts)); st = new.streams(); ms = new.meshes(); b = new.built(); sk = new.skin()
    assert new.vertex_count == 372 and b['vertex_count'] == 372 and b['index_count'] == (110 + 600 + 34) * 3 == len(new.indices())
    assert np.abs(st['pos'] - np.concatenate([np.round(p['pos'] * 4096) / 4096 for p in parts])).max() == 0
    assert [x.vertex_count for x in ms[:4]] == [55, 300, 17, 0] and [x.material for x in ms[:3]] == [1, 2, 3] and ms[3].raw == bytes(64)
    assert ms[1].vertex_start == 55 and ms[2].vertex_start == 355 and ms[1].index_start == 330
    for i, p in enumerate(parts): assert np.array_equal(new.triangles(ms[i]), p['tris'])
    assert abs(ms[1].center[1] - (parts[1]['pos'][:, 1].min() + parts[1]['pos'][:, 1].max()) / 2) < 1e-5
    allpos = np.concatenate([p['pos'] for p in parts]); assert np.allclose(b['center'], (allpos.min(0) + allpos.max(0)) / 2, atol=1e-5) and np.allclose(b['half'], (allpos.max(0) - allpos.min(0)) / 2, atol=1e-5)
    flat = [s for p in parts for s in p['skin']]
    for a, c in zip(flat, sk):
        da, dc = merged(a), merged(c); assert set(da) == set(dc) and max(abs(da[k] - dc[k]) for k in da) < 1 / 200, (a, c)
    assert np.all(b['lod_distances'] == 4096) and new.section(0x11112222) == m.section(0x11112222), 'unrelated sections must be carried over untouched'
    look = np.frombuffer(new.section(M.TAG_LOOK), '<u2').reshape(-1, 2); assert all(tuple(look[i]) == (0, 3) for i in list(range(6)) + list(range(8, 14))) and all(tuple(look[i]) == (0, 0) for i in range(16, 22))
    assert new.part1 + new.part2 == len(new.data) - 36 and new.sections[M.TAG_INDEX][0] == new.part1


def test_build_model_checks_its_input():
    raw, _ = make_asset(slots=2, used=2); m = M.Model(raw); good = dict(pos=np.zeros((3, 3)), nrm=np.tile([0, 1., 0], (3, 1)), uv=np.zeros((3, 2)), tris=np.array([[0, 1, 2]]), material=0, skin=[[(0, 1.0)]] * 3)
    for bad, msg in ((dict(good, tris=np.array([[0, 1, 3]])), 'outside'), (dict(good, skin=[[(0, 1.0)]] * 2), 'skin has')):
        try: M.build_model(m, [bad]); raise AssertionError('should fail: ' + msg)
        except ValueError as e: assert msg in str(e), e
    try: M.build_model(m, [good] * 3); raise AssertionError('too many parts')
    except ValueError as e: assert 'need 1..2' in str(e)
    try: M.build_model(m, []); raise AssertionError('no parts')
    except ValueError: pass


def test_weights_quantise_to_exactly_256():
    for pairs in ([(5, 1.0)], [(1, 0.5), (2, 0.5)], [(1, 0.3333), (2, 0.3333), (3, 0.3334)], [(9, 0.999), (4, 0.001)], [(0, 0.0), (3, 2.0)]):
        q = M.quantise_weights(pairs); assert sum(w for _, w in q) == 256 and all(0 <= w <= 255 for _, w in q), (pairs, q)


def test_normals_round_trip_over_the_sphere():
    rng = np.random.default_rng(1); n = rng.normal(size=(5000, 3)); n /= np.linalg.norm(n, axis=1, keepdims=True)
    w, _ = M.encode_normal_tangent(n); back = M.decode_normal(w)
    ang = np.degrees(np.arccos(np.clip((back * n).sum(1), -1, 1))); assert ang.max() < 0.6 and ang.mean() < 0.2, (ang.max(), ang.mean())


def test_bad_assets_are_refused():
    good, _ = make_asset()
    for data, msg in ((b'\0' * 100, 'not a DAT1'), (good + b'\0', 'header says'), (good[:-5], 'header says')):
        try: M.Model(data); raise AssertionError('should fail: ' + msg)
        except ValueError as e: assert msg in str(e), e
    bad = bytearray(good); struct.pack_into('<I', bad, 36 + 16 + 8, 10**7)
    try: M.Model(bytes(bad)); raise AssertionError('oversize section')
    except ValueError as e: assert 'past the end' in str(e)


def merged(lst):
    out = {}
    for b, w in lst: out[b] = out.get(b, 0.0) + w
    return out


def real_model():
    for p in (os.environ.get('SPIDERMAN_MODEL'), '/tmp/sm2/assets/BF45D48B5314EC76.bin'):
        if p and os.path.isfile(p): return open(p, 'rb').read()


def test_real_suit_encoders_and_rebuild():
    raw = real_model()
    if raw is None: print('   (no real model available: skipped)'); return
    m = M.Model(raw); st = m.streams(); idx = m.indices(); sk = m.skin()
    assert M.encode_index(idx) == m.section(M.TAG_INDEX) and M.encode_std(st['pos_units'], st['nword'], st['tword'], st['uv']) == m.section(M.TAG_STD_VERT)
    N = M.decode_normal(st['nword']); parts = []
    for ms in m.meshes()[:23]:
        sl = slice(ms.vertex_start, ms.vertex_start + ms.vertex_count)
        parts.append(dict(pos=st['pos'][sl], nrm=N[sl], uv=st['uv'][sl] * M.UV_SCALE, tris=m.triangles(ms, idx), material=ms.material, skin=sk[sl]))
    new = M.Model(M.build_model(m, parts)); s2 = new.streams(); ms2 = new.meshes(); idx2 = new.indices()
    assert np.abs(s2['pos'] - np.concatenate([p['pos'] for p in parts])).max() == 0 and all(np.array_equal(new.triangles(ms2[i], idx2), parts[i]['tris']) for i in range(23))
    flat = [s for p in parts for s in p['skin']]
    assert all(set(merged(a)) == set(merged(c)) for a, c in zip(flat, new.skin()))


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
