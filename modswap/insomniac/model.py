"""Spider-Man Remastered '.model' assets (DAT1 type 0x98906B9F): the section table and the standard vertex stream. Own implementation, checked on a real
classic-suit model (179,334 vertices, 1.82 m tall); ALERT (GPL) was only read to learn what the section tags mean.

An asset is  [36-byte header: u32 type, u32 size of the DAT1 part, u32 size of the part after it, ...][DAT1: '1TAD', u32 type, u32 total size, u32 section count,
(u32 tag, u32 offset, u32 size) x count, ... data]. Section offsets are counted from the start of DAT1 (byte 36).
Some tags: 0x0859863D index buffer, 0xA98BE69B standard vertices, 0x6B855EED uv1 vertices, 0x5CBA9DE9 colour vertices, 0x15DF9D3B joints, 0xEE31971C joint lookup,
0x5240C82B skin joint remap, 0x06EB7EFC look, 0x811902D7 look built, 0x283D0383 'built' (uv scale), 0xEFD92E68 physics.
The standard vertex stream is 16 bytes per vertex, stored in batches of 8 planar little-endian int16 streams (0x40000 bytes each batch of 8 x 0x8000 values for a
full batch): stream 0-1 packed normal/tangent words, 2-4 x y z, 5 w, 6-7 u v. Every stream is XOR-delta coded along the vertex index (value[i] = value[i-1] ^ stored[i]),
restarting at 0 in each batch. x y z are metres times 4096, y up.
"""
import struct
import numpy as np

DAT1_AT = 36
TAG_INDEX, TAG_STD_VERT, TAG_UV1, TAG_COL = 0x0859863D, 0xA98BE69B, 0x6B855EED, 0x5CBA9DE9
BATCH_BYTES = 8 * 0x10000
POS_SCALE = 4096.0


class Model:
    def __init__(self, data):
        if len(data) < DAT1_AT + 16 or data[DAT1_AT:DAT1_AT + 4] != b'1TAD': raise ValueError('not a DAT1 asset (no DAT1 marker at byte 36)')
        self.data = data; self.type = struct.unpack_from('<I', data, 0)[0]
        _, total, n = struct.unpack_from('<III', data, DAT1_AT + 4)
        if DAT1_AT + total != len(data): raise ValueError('asset is %d bytes, header says %d' % (len(data), DAT1_AT + total))
        self.sections = {}
        for i in range(n):
            tag, off, size = struct.unpack_from('<III', data, DAT1_AT + 16 + 12 * i)
            if DAT1_AT + off + size > len(data): raise ValueError('section %08X runs past the end of the asset' % tag)
            self.sections[tag] = (off, size)

    def section(self, tag):
        off, size = self.sections[tag]; return self.data[DAT1_AT + off:DAT1_AT + off + size]

    @property
    def vertex_count(self):
        return self.sections[TAG_STD_VERT][1] // 16

    def positions(self):
        """(N, 3) float64 metres, y up"""
        size = self.sections[TAG_STD_VERT][1]
        if size % 16: raise ValueError('standard vertex section is not a multiple of 16 bytes')
        raw = np.frombuffer(self.section(TAG_STD_VERT), np.uint8); out = np.zeros((size // 16, 3), np.int16); v0 = 0
        for o in range(0, size, BATCH_BYTES):
            blk = raw[o:o + BATCH_BYTES]; n = len(blk) // 16
            planes = blk.view('<u2').reshape(8, n)
            for c in range(3): out[v0:v0 + n, c] = np.bitwise_xor.accumulate(planes[2 + c]).view(np.int16)
            v0 += n
        return out / POS_SCALE


def encode_std_planes(pos_units, normals_words=None, uv_units=None):
    """the inverse of Model.positions for tests / writers: (N,3) int16 position units -> section bytes (other streams zero unless given)"""
    pos = np.asarray(pos_units, np.int16); n_total = len(pos); out = bytearray()
    per = BATCH_BYTES // 16
    for v0 in range(0, n_total, per):
        n = min(per, n_total - v0); planes = np.zeros((8, n), np.uint16)
        for c in range(3):
            v = pos[v0:v0 + n, c].view(np.uint16); planes[2 + c] = np.bitwise_xor(v, np.concatenate([[0], v[:-1]]).astype(np.uint16))
        out += planes.tobytes()
    return bytes(out)
