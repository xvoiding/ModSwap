"""Reader for Marvel's Spider-Man Remastered's asset index: asset_archive/toc.

A toc is  [u32 magic 0x77AF12AF][u32 uncompressed size][zlib stream]  holding a 'DAT1' container: a small header and a list of sections.
The sections this reader uses (found by reading real files):
    0x506D7B8A  asset ids        one u64 per asset
    0x65BCF461  sizes            12 bytes per asset: u32 1, u32 size in bytes, u32 asset number
    0xDCD720B5  places           8 bytes per asset:  u32 archive number, u32 offset inside that archive
    0x398ABFF0  archives         72 bytes each: u32, u32, 64-byte name (g00s000, ..., 'mods\\name' for installed mods)
    Offsets are positions in the archive's DECOMPRESSED stream (see archive.py): most archives are 'DSAR' block-compressed.
An asset id is a hash of its lower-cased path: CRC-64/XZ run from the start value 0xC96C5795D7870F42, then >> 2, then the top bit set.
Nothing here writes to the game.
"""
import os, re, struct, zlib
import numpy as np

MAGIC = 0x77AF12AF
# materials / models point at other assets by PATH TEXT (e.g. 'characters\\hero\\hero_spiderman\\textures\\x_n.texture'), not by id
_PATH = re.compile(rb'[A-Za-z0-9_\-./\\ ]{3,200}\.(?:texture|material|model|materialgraph|skeleton|animclip|config)', re.I)
SEC_IDS, SEC_SIZES, SEC_PLACES, SEC_ARCHIVES = 0x506D7B8A, 0x65BCF461, 0xDCD720B5, 0x398ABFF0
_POLY = 0xC96C5795D7870F42
_TAB = []
for _i in range(256):
    _c = _i
    for _ in range(8): _c = (_c >> 1) ^ _POLY if _c & 1 else _c >> 1
    _TAB.append(_c)


def normalize(path):
    return re.sub('/+', '/', path.lower().replace('\\', '/')).strip()


def path_id(path):
    """the 64-bit asset id of a path like 'characters/hero/hero_spiderman_classic/hero_spiderman_classic.model'"""
    crc = _POLY
    for b in normalize(path).encode('latin1'): crc = ((crc >> 8) ^ _TAB[(crc ^ b) & 0xFF]) & 0xFFFFFFFFFFFFFFFF
    return (crc >> 2) | 0x8000000000000000


class Toc:
    def __init__(self, data):
        magic, size = struct.unpack_from('<II', data, 0)
        if magic != MAGIC: raise ValueError('not a Spider-Man toc (magic 0x%08X)' % magic)
        raw = zlib.decompressobj().decompress(data[8:])                      # (the stream of the .BAK copy has no terminator: read what is there)
        if len(raw) != size: raise ValueError('toc is cut short (%d of %d bytes)' % (len(raw), size))
        if raw[:4] != b'1TAD': raise ValueError('toc does not contain a DAT1 block')
        n = struct.unpack_from('<I', raw, 12)[0]; self.sections = {}
        for i in range(n):
            h, off, sz = struct.unpack_from('<III', raw, 16 + 12 * i); self.sections[h] = (off, sz)
        for need in (SEC_IDS, SEC_SIZES, SEC_PLACES, SEC_ARCHIVES):
            if need not in self.sections: raise ValueError('toc has no section 0x%08X' % need)
        self.raw = raw
        o, s = self.sections[SEC_IDS]; self.count = s // 8
        self.ids = np.frombuffer(raw, '<u8', self.count, o)
        o, s = self.sections[SEC_SIZES]; self._sizes = np.frombuffer(raw, '<u4', self.count * 3, o).reshape(-1, 3)
        o, s = self.sections[SEC_PLACES]; self._places = np.frombuffer(raw, '<u4', self.count * 2, o).reshape(-1, 2)
        o, s = self.sections[SEC_ARCHIVES]
        self.archives = [raw[o + k + 8:o + k + 72].split(b'\0')[0].decode('latin1') for k in range(0, s, 72)]
        self._order = None; self._open = {}

    @classmethod
    def open(cls, path):
        if os.path.isdir(path): path = os.path.join(path, 'toc')
        return cls(open(path, 'rb').read())

    # ---- lookups
    def find(self, path_or_id):
        """asset number of a path (or a 64-bit id), or None"""
        aid = path_or_id if isinstance(path_or_id, (int, np.integer)) else path_id(path_or_id)
        if self._order is None: self._order = np.argsort(self.ids, kind='stable')
        k = int(np.searchsorted(self.ids[self._order], np.uint64(aid)))
        if k < self.count and int(self.ids[self._order[k]]) == int(aid): return int(self._order[k])
        return None

    def size(self, i): return int(self._sizes[i, 1])
    def archive(self, i): return int(self._places[i, 0])
    def offset(self, i): return int(self._places[i, 1])
    def archive_name(self, i): return self.archives[self.archive(i)]

    def read(self, i, archive_dir):
        """the bytes of asset number i (decompressed if its archive is a DSAR archive), read from the archive files in archive_dir"""
        from .archive import Archive
        name = self.archive_name(i).replace('\\', os.sep); key = os.path.join(archive_dir, name)
        a = self._open.get(key)
        if a is None: a = self._open[key] = Archive(key)
        return a.read(self.offset(i), self.size(i))

    def close(self):
        for a in self._open.values(): a.close()
        self._open = {}

    def references(self, data, skip=()):
        """asset numbers whose id appears inside `data` as an 8-byte value (4- or 8-byte aligned). Ids are 64-bit hashes, so a chance match is
        practically impossible: this finds the textures / materials / meshes a file points at without having to understand the file."""
        found = {}
        b = bytes(data)
        for shift in (0, 4):
            n = (len(b) - shift) // 8
            if n <= 0: continue
            arr = np.frombuffer(b, '<u8', n, shift)
            if self._order is None: self._order = np.argsort(self.ids, kind='stable')
            sids = self.ids[self._order]
            k = np.searchsorted(sids, arr); k[k >= self.count] = 0
            for pos in np.flatnonzero(sids[k] == arr): found.setdefault(int(self._order[k[pos]]), int(shift + pos * 8))
        return [i for i in found if i not in skip]

    def path_references(self, data, skip=()):
        """asset numbers named by path text inside `data` (see _PATH). -> {asset number: the path as written}"""
        found = {}
        for m in _PATH.finditer(bytes(data)):
            txt = m.group().decode('latin1').strip()
            for cand in dict.fromkeys((txt, txt.split(' ')[-1])):            # (a stray word glued in front of the path: try the last word too)
                i = self.find(cand)
                if i is not None and i not in skip: found.setdefault(i, cand); break
        return found


# ------------------------------------------------------------------------------------------------ writing
def patched_raw(toc, redirects=None, new_archives=()):
    """The decompressed DAT1 block of `toc` with changes applied:
      redirects     {asset number: (archive number, offset, size)}   -> the asset is now read from there
      new_archives  names ('mods\\x') appended to the archive table (they get numbers len(archives), +1, ...)
    Only the sections that change are touched; the archive table is the last section, so appending to it moves nothing else."""
    raw = bytearray(toc.raw)
    ao, asz = toc.sections[SEC_ARCHIVES]
    if ao + asz != len(raw): raise ValueError('the archive table is not the last section of this toc: cannot append to it safely')
    so, _ = toc.sections[SEC_SIZES]; po, _ = toc.sections[SEC_PLACES]
    for i, (arch, off, size) in (redirects or {}).items():
        if not 0 <= i < toc.count: raise ValueError('no asset number %d' % i)
        struct.pack_into('<I', raw, so + 12 * i + 4, size)                       # size
        struct.pack_into('<II', raw, po + 8 * i, arch, off)                      # archive number, offset
    n = len(toc.archives)
    for k, name in enumerate(new_archives):
        e = struct.pack('<II', 0, 10000 + n + k) + name.encode('latin1')[:63].ljust(64, b'\0'); raw += e
    if new_archives:
        # section table entry of the archive table: size grows; DAT1 total (bytes 8..11) grows
        count = struct.unpack_from('<I', raw, 12)[0]
        for i in range(count):
            tag, off, sz = struct.unpack_from('<III', raw, 16 + 12 * i)
            if tag == SEC_ARCHIVES: struct.pack_into('<I', raw, 16 + 12 * i + 8, sz + 72 * len(new_archives))
        struct.pack_into('<I', raw, 8, len(raw))
    return bytes(raw)


def to_file_bytes(raw, level=9):
    """toc file bytes from a decompressed DAT1 block"""
    return struct.pack('<II', MAGIC, len(raw)) + zlib.compress(raw, level)
