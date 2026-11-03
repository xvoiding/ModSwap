"""Spider-Man .model section table and standard vertex decoding.   python tests/test_insomniac_model.py"""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.insomniac import model as M


def build_asset(sections):
    """sections: {tag: bytes} -> asset with a 36-byte header + DAT1"""
    n = len(sections); head = 16 + 12 * n; off = head; table = b''; body = b''
    for tag, b in sections.items(): table += struct.pack('<III', tag, off, len(b)); body += b; off += len(b)
    dat1 = b'1TAD' + struct.pack('<III', 0x98906B9F, off, n) + table + body
    return struct.pack('<III', 0x98906B9F, len(dat1), 0) + b'\0' * 24 + dat1


def test_positions_round_trip_across_batches():
    rng = np.random.default_rng(5); n = 0x8000 * 2 + 777                      # three batches, the last one partial
    units = rng.integers(-7000, 7500, (n, 3)).astype(np.int16)
    a = M.Model(build_asset({M.TAG_STD_VERT: M.encode_std_planes(units), 0x15DF9D3B: b'J' * 64}))
    assert a.vertex_count == n and np.array_equal(np.round(a.positions() * M.POS_SCALE).astype(np.int16), units)
    assert a.type == 0x98906B9F and set(a.sections) == {M.TAG_STD_VERT, 0x15DF9D3B} and a.section(0x15DF9D3B) == b'J' * 64


def test_positions_are_metres():
    units = np.array([[0, 0, 0], [4096, 8192, -4096], [-2048, 7455, 100]], np.int16)       # 1 m, 2 m ... (height 7455/4096 = 1.82 m)
    a = M.Model(build_asset({M.TAG_STD_VERT: M.encode_std_planes(units)})); p = a.positions()
    assert np.allclose(p[1], [1, 2, -1]) and abs(p[2, 1] - 1.82) < 0.001


def test_bad_assets_are_refused():
    good = build_asset({M.TAG_STD_VERT: M.encode_std_planes(np.zeros((4, 3), np.int16))})
    for data, msg in ((b'\0' * 100, 'not a DAT1'), (good + b'\0', 'header says'), (good[:-5], 'header says')):
        try: M.Model(data); raise AssertionError('should fail: ' + msg)
        except ValueError as e: assert msg in str(e), e
    bad = bytearray(good); struct.pack_into('<I', bad, 36 + 16 + 8, 10**7)                  # a section that claims a huge size
    try: M.Model(bytes(bad)); raise AssertionError('oversize section')
    except ValueError as e: assert 'past the end' in str(e)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
