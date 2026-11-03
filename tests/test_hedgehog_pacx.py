"""Hedgehog Engine 2 PACx reader.   python tests/test_hedgehog_pacx.py
The synthetic archive follows the byte layout of the real 'PACx403L' character archives (header, metadata with parent table / chunk table / strings,
embedded split data, LZ4 root, inner 'PACx402L' archives)."""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import lz4.block
from modswap.hedgehog import pacx as P


def lz4_chunks(data, size):
    return [(lz4.block.compress(data[i:i + size], store_size=False), len(data[i:i + size])) for i in range(0, len(data), size)]


def pad(b, n=16): return b + b'\0' * (-len(b) % n)


def build_inner(files, dep=None, kind=0x2):
    """files: [(ext, uid, bytes, flags)] -> inner 'PACx402L' archive. dep = (name, comp, unc, pos_in_outer, [(c,u)]) writes a dependency table."""
    strs = b''; ext_off = {}
    for e in {f[0] for f in files}: ext_off[e] = len(strs); strs += e.encode() + b'\0'
    dep_name_off = None
    if dep: dep_name_off = len(strs); strs += dep[0].encode() + b'\0'
    strs = pad(strs)
    deptab = b''
    nd = 0
    if dep:
        nd = 1; chunk_bytes = b''.join(struct.pack('<II', c, u) for c, u in dep[4])
        deptab = struct.pack('<QQ', 1, 0)                                    # (offsets filled below)
        deptab += struct.pack('<QIIIIQ', 0, dep[1], dep[2], dep[3], len(dep[4]), 0) + chunk_bytes
        deptab = pad(deptab, 16)
    ent_size = 0x30 * len(files); trees = 0
    fdata = b''; offs = []
    for _, _, b, _ in files: offs.append(len(fdata)); fdata += pad(b)
    base_str = 0x30 + trees + len(deptab) + ent_size; base_data = base_str + len(strs); off_tab = b'\0' * 16
    if dep:
        dep_pos = 0x30 + trees; ch_at = dep_pos + 16 + 32
        deptab = bytearray(deptab); struct.pack_into('<Q', deptab, 8, dep_pos + 16); struct.pack_into('<Q', deptab, 16, base_str + dep_name_off); struct.pack_into('<Q', deptab, 16 + 24, ch_at); deptab = bytes(deptab)
    ents = b''.join(struct.pack('<IIQQQQHhI', uid, len(b), 0, 0 if fl & 1 else base_data + offs[i], 0, base_str + ext_off[e], fl, -1, 0) for i, (e, uid, b, fl) in enumerate(files))
    total = 0x30 + trees + len(deptab) + len(ents) + len(strs) + len(fdata) + len(off_tab)
    hdr = struct.pack('<4s4sIIIIIIIIHHI', b'PACx', b'402L', 0x6DF713A2, total, trees, len(deptab), len(ents), len(strs), len(fdata), len(off_tab), kind, 0x108, nd)
    out = hdr + deptab + ents + strs + fdata + off_tab; assert len(out) == total; return out


def build_outer(root_files, split_name=None, split_files=None, parent='EffectCommon', chunk=100, flags_v3=0x208, flags_v4=0x83):
    split_blob = split = None
    if split_name:
        raw = build_inner(split_files); ch = lz4_chunks(raw, chunk); split_blob = b''.join(c for c, _ in ch); split = (split_name, len(split_blob), len(raw), None, [(len(c), u) for c, u in ch])
    # layout of the outer file: header 0x20 | metadata header 16 | parents 24 | chunk table | strings | offsets 8 | split data | root
    probe_chunks = 1 + 64                                                       # (the chunk table size depends on the root, so build the root first with a placeholder position)
    pos0 = 0x20 + 16 + 24; pk = 4 + 8 * 40; chunkt = pad(b'\0' * pk, 8); strt = pad(parent.encode() + b'\0'); 
    root_for_size = build_inner(root_files, dep=(split[0], split[1], split[2], 0, split[4]) if split else None, kind=0xd if split else 0x1)
    rch = lz4_chunks(root_for_size, chunk); chunk_tab = struct.pack('<I', len(rch)) + b''.join(struct.pack('<II', len(c), u) for c, u in rch); chunk_tab = pad(chunk_tab, 8)
    data_pos = pos0 + len(chunk_tab) + len(strt) + 8
    root = build_inner(root_files, dep=(split[0], split[1], split[2], data_pos, split[4]) if split else None, kind=0xd if split else 0x1)
    rch = lz4_chunks(root, chunk); rblob = b''.join(c for c, _ in rch)
    chunk_tab = pad(struct.pack('<I', len(rch)) + b''.join(struct.pack('<II', len(c), u) for c, u in rch), 8)
    parents = struct.pack('<QQQ', 1, 0x40, pos0 + len(chunk_tab) + 0)             # entry -> the string (right after the chunk table)
    body = parents + chunk_tab + strt + b'\0' * 8 + (split_blob or b'') ; root_off = 0x30 + len(body)
    total = root_off + len(rblob)
    head = struct.pack('<4s4sIIIIIHH', b'PACx', b'403L', 0x6DF713A2, total, root_off, len(rblob), len(root), flags_v4, flags_v3)
    meta = struct.pack('<4I', len(parents), len(chunk_tab), len(strt), 8)
    out = head + meta + body + rblob; assert len(out) == total, (len(out), total); return out


FILES_ROOT = [('level', 1, b'LEVELDATA' * 30, 0), ('dds', 2, b'proxy', 1), ('material', 3, b'MATERIAL!' * 20, 0)]
FILES_SPLIT = [('model', 7, b'NEDARCV1' + bytes(range(256)) * 9, 0), ('dds', 8, b'DDS ' + b'\x07' * 400, 0), ('material', 9, b'M' * 50, 0)]


def test_reads_outer_root_and_embedded_split():
    p = P.Pacx(build_outer(FILES_ROOT, 'amy.pac.000', FILES_SPLIT))
    assert p.version == '403L' and p.parents == ['EffectCommon'] and p.split_names() == ['amy.pac.000']
    assert [e.ext for e in p.root.entries] == ['level', 'dds', 'material'] and p.root.entries[1].is_proxy
    got = {(e.source, e.ext, e.uid): b for e, b in p.files()}
    assert ('root', 'dds', 2) not in got, 'proxy entries carry no data'
    assert got[('root', 'level', 1)] == b'LEVELDATA' * 30 and got[('amy.pac.000', 'model', 7)] == b'NEDARCV1' + bytes(range(256)) * 9
    assert got[('amy.pac.000', 'dds', 8)][:4] == b'DDS ' and got[('amy.pac.000', 'material', 9)] == b'M' * 50 and len(got) == 5


def test_archive_without_splits():
    p = P.Pacx(build_outer(FILES_ROOT)); assert p.split_names() == [] and len(list(p.files())) == 2


def test_chunk_boundaries_do_not_matter():
    for chunk in (37, 100, 4096, 10**6):
        p = P.Pacx(build_outer(FILES_ROOT, 'x.pac.000', FILES_SPLIT, chunk=chunk)); got = {e.uid: b for e, b in p.files()}
        assert got[7].startswith(b'NEDARCV1') and got[1] == b'LEVELDATA' * 30, chunk


def test_bad_archives_are_refused_clearly():
    good = build_outer(FILES_ROOT)
    cases = [(b'XXXX' + good[4:], 'not a PACx'), (good + b'\0', 'header says'), (good[:-10], 'header says'),
             (build_outer(FILES_ROOT, flags_v3=0x108), 'LZ4'), (build_outer(FILES_ROOT, flags_v4=0x03), 'metadata'),
             (good[:4] + b'999L' + good[8:], 'unsupported PACx version')]
    for data, msg in cases:
        try: P.Pacx(data); raise AssertionError('should have failed: ' + msg)
        except ValueError as e: assert msg in str(e), (msg, str(e))
    bad = bytearray(good); i = bad.index(struct.pack('<I', len(build_inner(FILES_ROOT))))      # a chunk table that does not add up
    struct.pack_into('<I', bad, i, 1); 
    try: P.Pacx(bytes(bad)); raise AssertionError('chunk table mismatch not noticed')
    except ValueError as e: assert 'add up' in str(e) or 'cut short' in str(e) or 'header says' in str(e)


def test_missing_split_and_proxy_read_errors():
    p = P.Pacx(build_outer(FILES_ROOT, 'amy.pac.000', FILES_SPLIT))
    try: p.split('nope.pac.000'); raise AssertionError('no such split')
    except KeyError: pass
    try: p.root.read(p.root.entries[1]); raise AssertionError('proxy')
    except ValueError as e: assert 'pointer' in str(e)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
