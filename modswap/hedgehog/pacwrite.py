"""Write a Sonic Frontiers .pac back after changing the CONTENT of a split archive (same size or not). Layout (checked on the real files):

    0x20 header | metadata (4 sizes, parents, chunk table of the root, strings, offsets) | split chunks, back to back | pad to 16 | root chunks | pad to 16

Everything is LZ4 in 64 KB chunks. A changed split gets new chunks, so its compressed size and position change; the root archive lists each split's size / position / chunk table,
so those fields are patched in the root, which is then compressed again. Header: file size and root offset. The metadata blocks are copied unchanged.
"""
import struct
import lz4.block
from .pacx import Pacx, HEADER

CHUNK = 65536


def _compress(data):
    out = []
    for i in range(0, len(data), CHUNK):
        raw = data[i:i + CHUNK]; out.append((lz4.block.compress(raw, mode='high_compression', store_size=False), len(raw)))
    return out


def _pad16(n): return (-n) % 16


def rebuild(pac, new_splits):
    """pac: a Pacx. new_splits: {split name: new decompressed bytes of that inner archive}. -> the new file's bytes"""
    d = pac.data; sizes = struct.unpack_from('<4I', d, 0x20); meta_end = 0x30 + sum(sizes)
    deps = pac.root.deps(); unknown = set(new_splits) - {x[0] for x in deps}
    if unknown: raise KeyError('no split named %s' % sorted(unknown))
    root = bytearray(pac.root.data); out = bytearray(d[:meta_end]); pos = meta_end
    for k, (name, comp, unc, p0, chunks) in enumerate(deps):
        if name in new_splits:
            raw = bytes(new_splits[name]); ch = _compress(raw); blob = b''.join(c for c, _ in ch); sizes_c = [(len(c), u) for c, u in ch]; unc = len(raw)
        else:
            blob = d[p0:p0 + comp]; sizes_c = list(chunks)
        # patch this split's dependency entry in the root: compressed size, uncompressed size, position, (chunk count), chunk table entries
        e = pac.root.dep_table_at() + 32 * k
        name_off, _, _, _, cc, chunk_tab = struct.unpack_from('<QIIIIQ', root, e)
        if cc != len(sizes_c): raise ValueError('split %s would need %d chunks instead of %d: a split may not change its chunk count' % (name, len(sizes_c), cc))
        struct.pack_into('<QIIIIQ', root, e, name_off, len(blob), unc, pos, cc, chunk_tab)
        for i, (c, u) in enumerate(sizes_c): struct.pack_into('<II', root, chunk_tab + 8 * i, c, u)
        out += blob; pos += len(blob)
    out += b'\0' * _pad16(len(out)); root_off = len(out)
    rch = _compress(bytes(root)); out += b''.join(c for c, _ in rch)
    ct = 0x20 + 16 + sizes[0]; old_n = struct.unpack_from('<I', d, ct)[0]
    if len(rch) != old_n: raise ValueError('the root archive needs %d chunks instead of %d' % (len(rch), old_n))
    for i, (c, u) in enumerate(rch): struct.pack_into('<II', out, ct + 4 + 8 * i, len(c), u)
    out += b'\0' * _pad16(len(out))
    h = list(HEADER.unpack_from(d, 0)); h[3] = len(out); h[4] = root_off; h[5] = sum(len(c) for c, _ in rch); h[6] = len(root)
    HEADER.pack_into(out, 0, *h)
    return bytes(out)
