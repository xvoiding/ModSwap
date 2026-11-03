"""Sonic Frontiers .model files: the Needle container (synthetic) and the NEDMDLV5 model reader (real character files, skipped without them).   python tests/test_hedgehog_model.py
Real files: set SONIC_CHARACTER_DIR to the game's image\\x64\\raw\\character folder (or the folder the collector wrote with sonic.pac / amy.pac in it)."""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.hedgehog import needle, hemodel as H, pacx

CHAR_DIR = next((p for p in (os.environ.get('SONIC_CHARACTER_DIR'), '/tmp/s2x/whole/image/x64/raw/character') if p and os.path.isfile(os.path.join(p, 'amy.pac'))), None)


def test_needle_roundtrip_and_errors():
    es = [(needle.SIG_LOD, 'lodinfo', b'\x01\x02\x03\x04'), (needle.SIG_MODEL, 'model', b'A' * 12), (needle.SIG_MODEL, 'model', b'')]
    blob = needle.build(es); name, got = needle.parse(blob)
    assert name == 'arc' and [(e.sig, e.name, e.data(blob)) for e in got] == [(s, n, d) for s, n, d in es]
    assert needle.build([(e.sig, e.name, e.data(blob)) for e in got]) == blob
    assert [len(c) for c in needle.model_chunks(blob)] == [12, 0] and needle.model_chunks(b'BARE-CHUNK') == [b'BARE-CHUNK']
    try: needle.build([(needle.SIG_MODEL, 'm', b'abc')]); raise AssertionError('unaligned data must be refused')
    except ValueError: pass
    for bad in (b'NEDARCV1' + struct.pack('>I', 999) + b'arc\0', b'NOTANEEDLE' * 3):
        try: needle.parse(bad); raise AssertionError('should fail')
        except ValueError: pass


def test_dec3n_normals_decode_to_unit_vectors():
    def enc(x, y, z): return sum((int(round(v * 511)) & 0x3FF) << s for v, s in ((x, 0), (y, 10), (z, 20)))
    w = np.array([enc(1, 0, 0), enc(0, -1, 0), enc(0, 0, 1), enc(-0.6, 0.8, 0)], np.uint32)
    n = H._decode_dec3n(w)
    assert np.allclose(n, [[1, 0, 0], [0, -1, 0], [0, 0, 1], [-0.6, 0.8, 0]], atol=2e-3)


def real_models():
    out = []
    for f in ('amy', 'sonic', 'knuckles', 'tails'):
        p = pacx.Pacx.open(os.path.join(CHAR_DIR, f + '.pac'))
        for n in p.split_names():
            s = p.split(n)
            for e in s.entries:
                if e.ext == 'model' and not e.is_proxy: out += [(f, ch) for ch in needle.model_chunks(s.read(e))]
    return out


def test_every_real_model_parses_with_sane_geometry_and_skin():
    if CHAR_DIR is None: print('   (no real Sonic files: skipped)'); return
    total = 0
    for f, ch in real_models():
        m = H.HeModel(ch); names, par, M = m.nodes(); meshes = m.meshes(); total += len(meshes)
        assert par[0] == -1 and max(par) < len(names) and all(p < i for i, p in enumerate(par) if p >= 0), f
        lo, hi = m.bounds()
        if len(names) > 50: assert 'Hips' in names and 0.5 < hi[1] - lo[1] < 3.0, 'a full character is about a metre tall: %s' % f
        for me in meshes:
            P = me.positions(); assert np.isfinite(P).all() and me.faces.max() < me.vertex_count and len(me.faces) > 0
            assert (P.min(0) > lo - 0.05).all() and (P.max(0) < hi + 0.05).all(), 'vertices lie inside the stored bounds'
            n = me.normals(); assert abs(np.linalg.norm(n, axis=1) - 1).max() < 1e-6
            sk = me.skin()
            if sk is not None:
                bi, bw = sk; assert abs(bw.sum(1) - 1).max() < 1e-6 and bi.max() < len(names)
    assert total >= 80, total


def test_skeleton_positions_make_sense():
    if CHAR_DIR is None: print('   (no real Sonic files: skipped)'); return
    f, ch = next((f, c) for f, c in real_models() if f == 'amy'); m = H.HeModel(ch); names = m.nodes()[0]; W = m.node_world()
    g = lambda n: W[names.index(n)]
    assert 0.3 < g('Hips')[1] < 0.7 and g('Head')[1] > g('Spine')[1] > g('Hips')[1] and g('Ear_L')[0] * g('Ear_R')[0] < 0, 'hips mid-height, head above, ears on opposite sides'


def test_vertex_count_matches_real_buffer_sizes():
    if CHAR_DIR is None: print('   (no real Sonic files: skipped)'); return
    f, ch = next((f, c) for f, c in real_models() if f == 'amy'); me = H.HeModel(ch).meshes()[0]
    assert len(me.vertex_data) == me.vertex_count * me.vertex_size and me.vertex_size in (40, 44) and me.material == 'chr_amy_cloth' and me.texture_units[0][0] in ('diffuse', 'specular', 'normal')


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
