"""Hedgehog Engine 2 'Needle' containers (Sonic Frontiers .model files). Format worked out on real files; HedgeLib (MIT, Radfordhound) documents the container.

    'NEDARCV1' u32 size (BIG endian, counts from this field to the end of the file)  name string ('arc') padded to 4, then entries until the end:
        entry = 8-byte signature ('NEDLDIV1' lod info, 'NEDMDLV5' a model = one level of detail)  name string (padded to 4)  u32 size (BIG endian)  data[size]
"""
import struct
from dataclasses import dataclass

SIG_ARCHIVE, SIG_LOD, SIG_MODEL = b'NEDARCV1', b'NEDLDIV1', b'NEDMDLV5'


@dataclass
class Entry:
    sig: bytes
    name: str
    offset: int          # where the data starts in the archive
    size: int

    def data(self, blob): return blob[self.offset:self.offset + self.size]


def _name(b, p):
    z = b.index(b'\0', p); return b[p:z].decode('latin1'), (z + 1 + 3) & ~3


def parse(blob):
    """-> (archive name, [Entry]) of a NEDARCV1 container"""
    if blob[:8] != SIG_ARCHIVE: raise ValueError('not a Needle archive (starts with %r)' % bytes(blob[:8]))
    total = struct.unpack_from('>I', blob, 8)[0] + 8
    if total != len(blob): raise ValueError('archive says %d bytes, file has %d' % (total, len(blob)))
    name, pos = _name(blob, 12); out = []
    while pos + 8 < len(blob):
        sig = bytes(blob[pos:pos + 8]); nm, q = _name(blob, pos + 8); size = struct.unpack_from('>I', blob, q)[0]
        if q + 4 + size > len(blob): raise ValueError('entry %r runs past the end of the archive' % sig)
        out.append(Entry(sig, nm, q + 4, size)); pos = q + 4 + size
    return name, out


def build(entries, name='arc'):
    """[(sig, name, data)] -> archive bytes (the inverse of parse)"""
    def pad(b): return b + b'\0' * (-len(b) % 4)
    body = pad(name.encode('latin1') + b'\0')
    for sig, nm, data in entries:
        if len(data) % 4: raise ValueError('entry data must be a multiple of 4 bytes (names after it are aligned to the file)')
        body += sig + pad(nm.encode('latin1') + b'\0') + struct.pack('>I', len(data)) + bytes(data)
    return SIG_ARCHIVE + struct.pack('>I', len(body) + 4) + body


def model_chunks(blob):
    """the NEDMDLV5 chunks of a .model file, best level of detail first: -> [bytes]. A .model is either a Needle archive or a single bare chunk."""
    if bytes(blob[:8]) == SIG_ARCHIVE:
        _, es = parse(blob); return [e.data(blob) for e in es if e.sig == SIG_MODEL]
    return [bytes(blob)]
