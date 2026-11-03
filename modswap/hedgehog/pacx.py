"""Reader for Hedgehog Engine 2 PACx archives (Sonic Frontiers: 'PACx403L'). Layout worked out on real files, format reference: HedgeLib (MIT).

A .pac file (outer, 'PACx' v403/'v4'):
    0x00  header, 0x20 bytes: 'PACx', 3-char version + endian ('403L'), u32 uid, u32 file size, u32 offset of the root data,
          u32 root compressed size, u32 root uncompressed size, u16 flags(v4), u16 flags(v3: 0x200 = LZ4)
    0x20  metadata (flags v4 & 0x80): u32 sizes of [parents, chunk table, strings, offsets], then those four blocks in that order.
          The chunk table is  u32 count + count x (u32 compressed size, u32 uncompressed size).
    root  the 'root' = an inner PACx ('402L') archive, stored as the LZ4 chunks of that table, back to back, starting at the root offset.
An inner archive ('v3'): 0x30-byte header
    'PACx', '402L', u32 uid, u32 file size, u32 treesSize, u32 depTableSize, u32 dataEntriesSize, u32 strTableSize, u32 fileDataSize,
    u32 offTableSize, u16 type, u16 flags, u32 depCount
  followed by  trees | dependency table | data entries (0x30 bytes each) | strings | file data | offset table.   Offsets inside are plain positions in the
  decompressed archive. A data entry: u32 uid, u32 size, u64, u64 data offset, u64, u64 extension string offset, u16 flags (1 = proxy: the data is in a split),
  s16 split index, u32.
  The dependency table (u64 count, u64 offset, then entries of: u64 name offset, u32 compressed size, u32 uncompressed size, u32 position IN THE OUTER FILE,
  u32 chunk count, u64 offset of the chunk table) lists the SPLIT archives ('amy.pac.000') embedded in the outer file, again as LZ4 chunks; a split is
  another inner archive and holds the real model / dds / material data.
Nothing here writes to the game.
"""
import struct
from dataclasses import dataclass

HEADER = struct.Struct('<4s4sIIIIIHH')
V3 = struct.Struct('<4s4sIIIIIIIIHHI')
ENTRY = struct.Struct('<IIQQQQHhI')
NOT_HERE = 1


def _lz4(data, size):
    try: import lz4.block
    except ImportError: raise RuntimeError('the "lz4" Python package is needed to read Sonic Frontiers archives (it ships in ModSwap\'s runtime folder)')
    return lz4.block.decompress(data, uncompressed_size=size)


def _chunks(buf, pos, chunks):
    out = bytearray()
    for c, u in chunks:
        if pos + c > len(buf): raise ValueError('archive is cut short (chunk at %d needs %d bytes)' % (pos, c))
        out += _lz4(buf[pos:pos + c], u); pos += c
    return bytes(out)


@dataclass
class Entry:
    ext: str
    uid: int
    size: int
    offset: int
    flags: int
    split: int
    source: str              # 'root' or the split's name
    name: str = ''           # the file's name without extension (filled in by Inner.read_names)
    index: int = -1          # position in the archive's data entry table

    @property
    def is_proxy(self): return bool(self.flags & NOT_HERE)


class Inner:
    """one decompressed inner ('402L') archive"""
    def __init__(self, data, name='root'):
        h = V3.unpack_from(data, 0)
        if h[0] != b'PACx': raise ValueError('not a PACx archive')
        (_, self.version, self.uid, self.file_size, trees, deps, dents, strs, fdata, offt, self.type, self.flags, self.dep_count) = h
        if self.file_size != len(data): raise ValueError('inner archive is %d bytes, header says %d' % (len(data), self.file_size))
        self.data = data; self.name = name; self.dep_pos = 0x30 + trees; ent0 = self.dep_pos + deps
        self.entries = []
        for i in range(dents // ENTRY.size):
            uid, size, _, off, _, ext, fl, sp, _ = ENTRY.unpack_from(data, ent0 + ENTRY.size * i)
            self.entries.append(Entry(self._cstr(ext), uid, size, off, fl, sp, name, index=i))
        self.ent0 = ent0
        try: self.read_names()
        except (struct.error, ValueError, IndexError): pass            # names are a convenience: an unreadable tree must not stop the archive from loading

    def _cstr(self, p):
        e = self.data.index(b'\0', p); return self.data[p:e].decode('latin1')

    def read_names(self):
        """file names from the trees section: one tree of extensions, each pointing at a radix tree of file names (a node holds a FRAGMENT of the name; the full name is the
        fragments from the root down). Sets Entry.name."""
        d = self.data; NODE = struct.Struct('<QQQiiiHBB')
        def nodes(tree_at):
            n, _, nodes_at, _ = struct.unpack_from('<IIQQ', d, tree_at); out = []
            for i in range(n):
                name_p, data_p, ch_p, parent, glob, didx, cc, has, _ = NODE.unpack_from(d, nodes_at + 40 * i)
                out.append((self._cstr(name_p) if name_p else '', data_p, parent, has))
            return out
        def full(ns, i):
            parts = []
            while i >= 0 and len(parts) < 64: parts.append(ns[i][0]); i = ns[i][2]
            return ''.join(reversed(parts))
        by_addr = {self.ent0 + 0x30 * e.index: e for e in self.entries}
        for ti, (tname, tdata, _, thas) in enumerate(nodes(0x30)):
            if not thas or not tdata: continue
            fn = nodes(tdata)
            for i, (nm, data_p, parent, has) in enumerate(fn):
                if has and data_p in by_addr: by_addr[data_p].name = full(fn, i)

    def read(self, e):
        if e.is_proxy: raise ValueError('this entry is only a pointer; its data is in a split archive')
        if e.offset + e.size > len(self.data): raise ValueError('entry runs past the end of the archive')
        return self.data[e.offset:e.offset + e.size]

    def dep_table_at(self):
        """position of the first dependency entry (the table starts with u64 count, u64 offset)"""
        return struct.unpack_from('<Q', self.data, self.dep_pos + 8)[0]

    def deps(self):
        """[(name, compressed size, uncompressed size, position in the outer file, [(comp, uncomp) chunks])]"""
        if not self.dep_count: return []
        cnt, off = struct.unpack_from('<QQ', self.data, self.dep_pos); out = []
        for k in range(cnt):
            name, comp, unc, pos, cc, ch = struct.unpack_from('<QIIIIQ', self.data, off + 32 * k)
            out.append((self._cstr(name), comp, unc, pos, [struct.unpack_from('<II', self.data, ch + 8 * i) for i in range(cc)]))
        return out


class Pacx:
    def __init__(self, data):
        sig, ver, self.uid, size, root, rc, ru, self.flags_v4, self.flags_v3 = HEADER.unpack_from(data, 0)
        if sig != b'PACx': raise ValueError('not a PACx archive (starts with %r)' % sig)
        self.version = ver.decode('latin1')
        if not self.version.startswith('403') and not self.version.startswith('402') and not self.version.startswith('405'): raise ValueError('unsupported PACx version %s' % self.version)
        if size != len(data): raise ValueError('file is %d bytes, header says %d' % (len(data), size))
        if not self.flags_v3 & 0x200: raise ValueError('only LZ4-compressed PACx archives are supported (flags 0x%x)' % self.flags_v3)
        if not self.flags_v4 & 0x80: raise ValueError('no metadata block, so no chunk table')
        parents, chunkt, _, _ = struct.unpack_from('<4I', data, 0x20); ct = 0x20 + 16 + parents
        count = struct.unpack_from('<I', data, ct)[0]; chunks = [struct.unpack_from('<II', data, ct + 4 + 8 * i) for i in range(count)]
        if sum(c for c, _ in chunks) != rc or sum(u for _, u in chunks) != ru: raise ValueError('chunk table does not add up to the root sizes')
        self.data = data; self.root = Inner(_chunks(data, root, chunks), 'root'); self._splits = {}
        self.parents = []
        if parents >= 16:                                                  # parent table: u64 count, u64 offset, then u64 path offsets (positions relative to the archive start)
            n, off = struct.unpack_from('<QQ', data, 0x30)
            for k in range(n):
                p = struct.unpack_from('<Q', data, off + 8 * k)[0]
                if p < len(data): self.parents.append(data[p:data.index(b'\0', p)].decode('latin1'))

    @classmethod
    def open(cls, path): return cls(open(path, 'rb').read())

    def split_names(self): return [d[0] for d in self.root.deps()]

    def split(self, name):
        """the decompressed inner archive of the embedded split `name` (e.g. 'amy.pac.000')"""
        if name not in self._splits:
            for n, comp, unc, pos, chunks in self.root.deps():
                if n == name:
                    buf = _chunks(self.data, pos, chunks)
                    if len(buf) != unc: raise ValueError('split %s decompressed to %d bytes, expected %d' % (n, len(buf), unc))
                    self._splits[name] = Inner(buf, name); break
            else: raise KeyError('no split named %s' % name)
        return self._splits[name]

    def files(self):
        """every real (non-proxy) entry of the root and of all splits -> (Entry, bytes)"""
        for e in self.root.entries:
            if not e.is_proxy: yield e, self.root.read(e)
        for n in self.split_names():
            s = self.split(n)
            for e in s.entries:
                if not e.is_proxy: yield e, s.read(e)
