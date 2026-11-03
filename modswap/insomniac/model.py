"""Spider-Man Remastered '.model' assets (DAT1 type 0x98906B9F): reading AND writing. Own implementation, checked against a real classic-suit model
(179,334 vertices, 212 joints, 59 mesh parts; decoded geometry drawn and recognised as Spider-Man). ALERT (GPL) was only read to learn what the section tags mean.

An asset is  [36-byte header: u32 type, u32 offset where the streamed geometry begins, u32 size of that part, 24 more bytes][DAT1 block]
DAT1: '1TAD', u32 type, u32 total size, u32 section count, (u32 tag, u32 offset, u32 size) x count, then a string area, then the sections (offsets count from
the start of DAT1 = byte 36, sections start on 16-byte boundaries). The strings (joint names ...) are addressed by absolute offset from the start of DAT1.

Sections used (tag: meaning):
  0859863D  index buffer: u16 indices, each stored as the difference from the previous one (int16, wrapping). Indices are relative to their mesh part.
  A98BE69B  standard vertices, 16 bytes each, in batches of 0x8000: eight planar streams [normal word u32 (2 planes)][x][y][z][tangent word][u][v] int16,
            every stream XOR-delta coded along the vertex index, restarting in each batch. x y z = metres * 4096 (y up), u v = value * 16384 (the 'built' section can change that).
  6B855EED  second uv set, int16 pairs, / 32768, plain.      5CBA9DE9  vertex colours, u32, plain.
  78D9CBDE  mesh parts, 64 bytes each: f32 centre x y z, u16 x4 (bounds, undecoded), u32 vertex start, index start, index count, vertex count,
            u16 flags, material, first skin batch, skin batch count (low byte = count), u16, u16, f32, f32, u32, u32.
  C61B1FF5  skin batches (16 bytes: u32 offset into the skin data, u32, u16, u16, u16 vertex count, u16 first vertex IN the mesh part); a batch holds <= 2560 vertices.
  DCA379A2  skin data: per batch, per group of 16 vertices:  u8 (influences - 1), then per vertex either one bone byte (1 influence) or (bone, weight) byte pairs; weight / 256.
            Bone numbers are indices into the joint list.
  15DF9D3B  joints, 16 bytes: s16 parent, u16 index, u16, u16, u32 name hash, u32 name offset.   DCC88A19: joint transforms (12 floats + 16 floats each).
  283D0383  'built': f32 bounding centre x3, radius, half extents x3; position scale (1/4096) at 0x2C; uv scale code at 0x30; LOD switch distances at 0x34..0x44;
            u32 at 0x60 (65535), u32 index count at 0x64, u32 vertex count at 0x68.
  06EB7EFC  'look': (start, count) mesh ranges per LOD, three rows of six.
Nothing here touches the game by itself.
"""
import struct
from dataclasses import dataclass
import numpy as np

DAT1_AT = 36
TAG_INDEX, TAG_STD_VERT, TAG_UV1, TAG_COL = 0x0859863D, 0xA98BE69B, 0x6B855EED, 0x5CBA9DE9
TAG_MESHES, TAG_SKIN_BATCH, TAG_SKIN_DATA, TAG_JOINTS, TAG_JOINT_XFORM = 0x78D9CBDE, 0xC61B1FF5, 0xDCA379A2, 0x15DF9D3B, 0xDCC88A19
TAG_BUILT, TAG_LOOK = 0x283D0383, 0x06EB7EFC
STREAM_TAGS = (TAG_INDEX, TAG_STD_VERT, TAG_UV1, TAG_COL)               # the streamed geometry: the second part of the asset
BATCH_VERTS = 0x8000
BATCH_BYTES = 8 * 0x10000
POS_SCALE = 4096.0
UV_SCALE = 1.0 / 16384.0
SKIN_BATCH = 2560
DEFAULT_TANGENT_WORD, DEFAULT_TANGENT2 = 0x7FF80200, 0x7E
_SQ2 = float(np.sqrt(2.0)); _Q = _SQ2 / (0x3FF / 2.0)


@dataclass
class Mesh:
    index: int
    raw: bytes
    center: tuple
    vertex_start: int
    index_start: int
    index_count: int
    vertex_count: int
    flags: int
    material: int
    first_skin_batch: int
    skin_batches: int            # low byte of the stored count

    def pack(self):
        e = bytearray(self.raw)
        struct.pack_into('<3f', e, 0, *self.center)
        struct.pack_into('<IIII', e, 20, self.vertex_start, self.index_start, self.index_count, self.vertex_count)
        struct.pack_into('<HHHH', e, 36, self.flags, self.material, self.first_skin_batch, self.skin_batches)
        struct.pack_into('<II', e, 56, self.vertex_start, 0)
        return bytes(e)


@dataclass
class Joint:
    index: int
    parent: int
    hash: int
    name: str


class Model:
    def __init__(self, data):
        if len(data) < DAT1_AT + 16 or data[DAT1_AT:DAT1_AT + 4] != b'1TAD': raise ValueError('not a DAT1 asset (no DAT1 marker at byte 36)')
        self.data = bytes(data); self.type = struct.unpack_from('<I', data, 0)[0]
        self.dat1_type, total, n = struct.unpack_from('<III', data, DAT1_AT + 4)
        if DAT1_AT + total != len(data): raise ValueError('asset is %d bytes, header says %d' % (len(data), DAT1_AT + total))
        self.sections = {}; self.order = []
        for i in range(n):
            tag, off, size = struct.unpack_from('<III', data, DAT1_AT + 16 + 12 * i)
            if DAT1_AT + off + size > len(data): raise ValueError('section %08X runs past the end of the asset' % tag)
            self.sections[tag] = (off, size); self.order.append(tag)
        self.head_size = 16 + 12 * n
        self.first_offset = min((o for o, _ in self.sections.values()), default=len(data) - DAT1_AT)
        self.part1, self.part2 = struct.unpack_from('<II', data, 4)

    # ---- raw access
    def section(self, tag):
        off, size = self.sections[tag]; return self.data[DAT1_AT + off:DAT1_AT + off + size]

    def string(self, offset):
        i = DAT1_AT + offset
        return self.data[i:self.data.index(b'\0', i)].decode('latin1')

    @property
    def vertex_count(self): return self.sections[TAG_STD_VERT][1] // 16

    # ---- geometry
    def streams(self):
        """dict: pos (N,3) metres, nword (N,) u32, tword (N,) int16, uv (N,2) int16 units, uv1 (N,2) int16, col (N,) u32"""
        size = self.sections[TAG_STD_VERT][1]
        if size % 16: raise ValueError('standard vertex section is not a multiple of 16 bytes')
        raw = np.frombuffer(self.section(TAG_STD_VERT), np.uint8); N = size // 16
        pos = np.zeros((N, 3), np.int16); nword = np.zeros(N, np.uint32); tword = np.zeros(N, np.int16); uv = np.zeros((N, 2), np.int16); v0 = 0
        for o in range(0, size, BATCH_BYTES):
            blk = raw[o:o + BATCH_BYTES]; n = len(blk) // 16; pl = blk.view('<u2').reshape(8, n)
            nword[v0:v0 + n] = np.bitwise_xor.accumulate(blk[:4 * n].view('<u4'))
            for c in range(3): pos[v0:v0 + n, c] = np.bitwise_xor.accumulate(pl[2 + c]).view(np.int16)
            tword[v0:v0 + n] = np.bitwise_xor.accumulate(pl[5]).view(np.int16)
            for c in range(2): uv[v0:v0 + n, c] = np.bitwise_xor.accumulate(pl[6 + c]).view(np.int16)
            v0 += n
        uv1 = np.frombuffer(self.section(TAG_UV1), '<i2').reshape(-1, 2) if TAG_UV1 in self.sections else np.zeros((N, 2), np.int16)
        col = np.frombuffer(self.section(TAG_COL), '<u4') if TAG_COL in self.sections else np.zeros(N, np.uint32)
        return dict(pos=pos / POS_SCALE, pos_units=pos, nword=nword, tword=tword, uv=uv, uv1=uv1, col=col)

    def positions(self): return self.streams()['pos']

    def indices(self):
        delta = np.frombuffer(self.section(TAG_INDEX), '<i2').astype(np.int64)
        return (np.cumsum(delta) % 65536).astype(np.uint16)

    def meshes(self):
        b = self.section(TAG_MESHES); out = []
        for i in range(len(b) // 64):
            e = b[64 * i:64 * i + 64]; vs, is_, ic, vc = struct.unpack_from('<IIII', e, 20); fl, mat, fsb, nsb = struct.unpack_from('<HHHH', e, 36)
            out.append(Mesh(i, e, struct.unpack_from('<3f', e, 0), vs, is_, ic, vc, fl, mat, fsb, nsb & 255))
        return out

    def triangles(self, mesh, idx=None):
        """(T,3) indices relative to the mesh part"""
        idx = self.indices() if idx is None else idx
        return idx[mesh.index_start:mesh.index_start + mesh.index_count].reshape(-1, 3).astype(np.int64)

    # ---- skeleton and skin
    def joints(self):
        b = self.section(TAG_JOINTS); out = []
        for i in range(len(b) // 16):
            parent, idx, _, _, h, so = struct.unpack_from('<hHHHII', b, 16 * i); out.append(Joint(i, parent, h, self.string(so)))
        return out

    def joint_transforms(self):
        """local (scale (J,3), quaternion xyzw (J,4), position (J,3)) and the 4x4 matrices (J,4,4)"""
        b = self.section(TAG_JOINT_XFORM); n = len(b) // 112
        m34 = np.frombuffer(b[:48 * n], '<f4').reshape(n, 12); off = 48 * n; off += -off % 64 if False else (-off) % 64
        m44 = np.frombuffer(b[off:off + 64 * n], '<f4').reshape(n, 4, 4) if len(b) >= off + 64 * n else None
        return m34[:, 0:3], m34[:, 4:8], m34[:, 8:11], m44

    def skin(self):
        """per vertex of the whole model: [(bone, weight), ...] (weights sum to 1)"""
        raw = self.section(TAG_SKIN_DATA); bt = self.section(TAG_SKIN_BATCH); N = self.vertex_count; out = [None] * N
        for m in self.meshes():
            if not m.vertex_count: continue
            for b in range(m.first_skin_batch, m.first_skin_batch + m.skin_batches):
                off, _, _, _, vc, fv = struct.unpack_from('<IIHHHH', bt, 16 * b); p = off
                for j in range(0, vc, 16):
                    groups = raw[p] + 1; p += 1
                    for z in range(min(16, vc - j)):
                        if groups == 1: lst = [(raw[p], 1.0)]; p += 1
                        else: lst = [(raw[p + 2 * g], raw[p + 2 * g + 1] / 256.0) for g in range(groups)]; p += 2 * groups
                        merged = {}
                        for bn, w in lst: merged[bn] = merged.get(bn, 0.0) + w
                        out[m.vertex_start + fv + j + z] = [(bn, w) for bn, w in merged.items() if w > 0] or [(lst[0][0], 1.0)]
        return out

    def built(self):
        f = np.frombuffer(self.section(TAG_BUILT), '<f4'); u = np.frombuffer(self.section(TAG_BUILT), '<u4')
        return dict(center=f[0:3].copy(), radius=float(f[3]), half=f[4:7].copy(), pos_scale=float(f[11]), lod_distances=f[13:18].copy(), index_count=int(u[25]), vertex_count=int(u[26]))


# ------------------------------------------------------------------------------------------------ normals / tangents
def decode_normal(words):
    w = np.asarray(words, np.uint32).astype(np.int64)
    nx = (w & 0x3FF) * _Q - _SQ2; ny = ((w >> 10) & 0x3FF) * _Q - _SQ2
    q = nx * nx + ny * ny; nw = np.sqrt(np.clip(1 - 0.25 * q, 0, None)); nz = 1 - 0.5 * q
    return np.stack([nx * nw, ny * nw, np.where((w >> 31) == 0, -nz, nz)], 1)


def _oct(v):
    """(n,3) unit vectors -> (a, b in 0..1, sign>0) as stored: x/y scaled by the xy-radius of the sphere cap, z folded into a sign bit"""
    z = v[:, 2]; s = z >= 0; az = np.abs(z); r = np.sqrt(np.clip(1 - (1 - az) / 2.0, 1e-12, None))
    return np.clip(v[:, 0] / r / (2 * _SQ2) + 0.5, 0, 1), np.clip(v[:, 1] / r / (2 * _SQ2) + 0.5, 0, 1), s


def encode_normal_tangent(nrm, tan=None, bitan_sign=None):
    """(N,3) normals (+ tangents, + bitangent sign +-1) -> (u32 words, int16 tangent words). Without tangents the engine's neutral defaults are written."""
    nrm = np.asarray(nrm, np.float64); nrm = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12); N = len(nrm)
    a, b, pos = _oct(nrm)
    word = (np.rint(a * 1023).astype(np.uint32) & 0x3FF) | ((np.rint(b * 1023).astype(np.uint32) & 0x3FF) << 10)
    word |= np.where(pos, 0x80000000, 0).astype(np.uint32)
    if tan is None: return (word & 0x800FFFFF) | (DEFAULT_TANGENT_WORD & 0x7FF00000), np.full(N, DEFAULT_TANGENT2, np.int16)
    t = np.asarray(tan, np.float64); t = t - nrm * (nrm * t).sum(1, keepdims=True); t = t / (np.linalg.norm(t, axis=1, keepdims=True) + 1e-12)
    ta, tb, tpos = _oct(t)
    word = (word & 0x800FFFFF) | ((np.rint(ta * 1023).astype(np.uint32) & 0x3FF) << 20) | np.where(tpos, 0x40000000, 0).astype(np.uint32)
    t2 = (np.rint(tb * 1023).astype(np.int64) & 0x3FF) | 0x7C00
    sgn = np.ones(N) if bitan_sign is None else np.asarray(bitan_sign)
    t2 = np.where(sgn > 0, -t2, t2)
    return word, t2.astype(np.int16)


def tangents_from_uv(pos, nrm, uv, tris):
    """per-vertex tangent (N,3) and bitangent sign (N,) from positions, normals and uvs"""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = pos[b] - pos[a], pos[c] - pos[a]; d1, d2 = uv[b] - uv[a], uv[c] - uv[a]
    den = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]; den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    tT = (e1 * d2[:, [1]] - e2 * d1[:, [1]]) / den[:, None]; tB = (e2 * d1[:, [0]] - e1 * d2[:, [0]]) / den[:, None]
    accT = np.zeros_like(pos); accB = np.zeros_like(pos)
    for k in range(3): np.add.at(accT, tris[:, k], tT); np.add.at(accB, tris[:, k], tB)
    T = accT - nrm * (nrm * accT).sum(1, keepdims=True); bad = np.linalg.norm(T, axis=1) < 1e-9
    T[bad] = np.cross(nrm[bad], [0.0, 1.0, 0.0]) + 1e-9
    T = T / np.linalg.norm(T, axis=1, keepdims=True)
    sign = np.where((np.cross(nrm, T) * accB).sum(1) >= 0, 1.0, -1.0)
    return T, sign


# ------------------------------------------------------------------------------------------------ encoders
def _xor_delta(a):
    a = np.asarray(a); return np.bitwise_xor(a, np.concatenate([np.zeros(1, a.dtype), a[:-1]]))


def encode_index(values):
    """u16 indices -> section bytes (differences, int16 wrapping)"""
    v = np.asarray(values, np.int64); d = np.diff(v, prepend=0); return (((d + 32768) % 65536) - 32768).astype('<i2').tobytes()


def encode_std(pos_units, nword, tword, uv_units):
    """the standard vertex section from per-vertex arrays (pos_units int16 (N,3), uv_units int16 (N,2))"""
    pos = np.asarray(pos_units, np.int16); N = len(pos); out = bytearray()
    nword = np.asarray(nword, np.uint32); tword = np.asarray(tword, np.int16); uv = np.asarray(uv_units, np.int16)
    for v0 in range(0, N, BATCH_VERTS):
        s = slice(v0, min(v0 + BATCH_VERTS, N))
        out += _xor_delta(nword[s]).astype('<u4').tobytes()
        for c in range(3): out += _xor_delta(pos[s, c].view(np.uint16)).astype('<u2').tobytes()
        out += _xor_delta(tword[s].view(np.uint16)).astype('<u2').tobytes()
        for c in range(2): out += _xor_delta(uv[s, c].view(np.uint16)).astype('<u2').tobytes()
    return bytes(out)


def quantise_weights(pairs):
    """[(bone, weight)] -> [(bone, byte)] with the bytes summing to 256 and each <= 255"""
    pairs = [(int(b), float(w)) for b, w in pairs if w > 0] or [(0, 1.0)]
    tot = sum(w for _, w in pairs); q = [max(0, int(round(256 * w / tot))) for _, w in pairs]
    d = 256 - sum(q); q[int(np.argmax(q))] += d
    out = []
    for (b, _), x in zip(pairs, q):
        while x > 255: out.append((b, 255)); x -= 255
        if x > 0 or not out: out.append((b, x))
    return out


def encode_skin(vertex_skins, mesh_vertex_counts, batch=SKIN_BATCH):
    """vertex_skins: per vertex [(bone, weight)], laid out mesh after mesh. -> (skin data bytes, batch table bytes, [(first batch, batch count) per mesh])"""
    data = bytearray(); table = bytearray(); ranges = []; v = 0; nb = 0
    for mc in mesh_vertex_counts:
        first = nb
        for s0 in range(0, mc, batch):
            cnt = min(batch, mc - s0); table += struct.pack('<IIHHHH', len(data), 0, 0, 0, cnt, s0)
            for j in range(0, cnt, 16):
                grp = [quantise_weights(vertex_skins[v + s0 + j + z]) for z in range(min(16, cnt - j))]; g = max(len(x) for x in grp)
                data.append(g - 1)
                for x in grp:
                    if g == 1: data.append(x[0][0])
                    else:
                        x = x + [(x[0][0], 0)] * (g - len(x))
                        for bn, w in x: data += bytes((bn, w))
            nb += 1
        ranges.append((first, nb - first)); v += mc
    return bytes(data), bytes(table), ranges


# ------------------------------------------------------------------------------------------------ container
def rebuild(model, replace):
    """a new asset: every section of `model` kept as it is, except those in `replace` {tag: bytes}. Sections keep their order and 16-byte alignment; the strings stay where
    they are; the two part sizes and the totals are recomputed."""
    n = len(model.order); head = 16 + 12 * n
    strings = model.data[DAT1_AT + head:DAT1_AT + model.first_offset]
    order = sorted(model.order, key=lambda t: model.sections[t][0]); body = bytearray(strings); cur = head + len(strings); placed = {}
    part1_end = None
    for tag in order:
        data = replace.get(tag, model.section(tag))
        if tag in STREAM_TAGS and part1_end is None: cur += -cur % 16; part1_end = cur
        else: cur += -cur % 16
        body += b'\0' * (cur - head - len(body)); placed[tag] = (cur, len(data)); body += data; cur += len(data)
    if part1_end is None: part1_end = cur
    total = cur; table = b''.join(struct.pack('<III', t, *placed[t]) for t in model.order)
    dat1 = b'1TAD' + struct.pack('<III', model.dat1_type, total, n) + table + bytes(body)
    assert len(dat1) == total
    return struct.pack('<III', model.type, part1_end, total - part1_end) + model.data[12:DAT1_AT] + dat1


def build_model(model, parts, lod_distance=4096.0):
    """Write a model with new geometry onto `model`'s skeleton and everything else.
    parts: list (max = the original's mesh slot count) of dicts
        pos (n,3) metres y up, nrm (n,3), uv (n,2) in 0..1, tris (m,3) indices local to the part, material (int), skin [per vertex [(bone, weight)]]
        optional: uv1 (n,2) in 0..1, col (n,) u32
    Every LOD slot is pointed at the new parts (so no lower-detail level of the old suit can show), LOD distances are pushed out, counts and the bounding box are updated.
    -> new asset bytes"""
    slots = model.meshes()
    if not 1 <= len(parts) <= len(slots): raise ValueError('need 1..%d parts, got %d' % (len(slots), len(parts)))
    pos = np.concatenate([np.asarray(p['pos'], np.float64) for p in parts]); nrm = np.concatenate([np.asarray(p['nrm'], np.float64) for p in parts])
    uv = np.concatenate([np.asarray(p['uv'], np.float64) for p in parts])
    N = len(pos)
    if N > 65535 * 3 or any(len(p['pos']) > 65535 for p in parts): raise ValueError('a part may have at most 65,535 vertices (split it)')
    tris = [np.asarray(p['tris'], np.int64) for p in parts]
    for p, t in zip(parts, tris):
        if len(t) and (t.min() < 0 or t.max() >= len(p['pos'])): raise ValueError('triangle index outside its part')
        if len(p['skin']) != len(p['pos']): raise ValueError('skin has %d entries for %d vertices' % (len(p['skin']), len(p['pos'])))
    # tangents per part (they need the part's own triangles)
    tw = np.zeros(N, np.uint32); t2 = np.zeros(N, np.int16); v0 = 0
    for p, t in zip(parts, tris):
        n = len(p['pos']); sl = slice(v0, v0 + n)
        T, sg = tangents_from_uv(np.asarray(p['pos'], np.float64), nrm[sl], np.asarray(p['uv'], np.float64), t) if len(t) else (None, None)
        w, x = encode_normal_tangent(nrm[sl], T, sg); tw[sl] = w; t2[sl] = x; v0 += n
    pos_units = np.clip(np.rint(pos * POS_SCALE), -32768, 32767).astype(np.int16)
    uv_units = np.clip(np.rint(uv / UV_SCALE), -32768, 32767).astype(np.int16)
    uv1 = np.concatenate([np.asarray(p.get('uv1', p['uv']), np.float64) for p in parts]); col = np.concatenate([np.asarray(p.get('col', np.full(len(p['pos']), 0xFFFFFFFF)), np.uint32) for p in parts])
    idx_all = np.concatenate([t.reshape(-1) for t in tris]) if tris else np.zeros(0, np.int64)
    skin_data, skin_table, ranges = encode_skin([s for p in parts for s in p['skin']], [len(p['pos']) for p in parts])
    # mesh table: new parts in the first slots, the rest cleared (the layout the game already accepted)
    entries = []; vs = 0; is_ = 0
    for k, slot in enumerate(slots):
        if k < len(parts):
            p = parts[k]; P = np.asarray(p['pos'], np.float64); c = (P.min(0) + P.max(0)) / 2 if len(P) else np.zeros(3)
            m = Mesh(k, slot.raw, tuple(float(x) for x in c), vs, is_, int(len(tris[k]) * 3), len(P), slot.flags, int(p['material']), ranges[k][0], ranges[k][1]); vs += len(P); is_ += m.index_count
            entries.append(m.pack())
        else: entries.append(bytes(64))
    K = len(parts)
    look = bytearray(model.section(TAG_LOOK))
    for row in (0, 8):
        for lod in range(6): struct.pack_into('<HH', look, 4 * (row + lod), 0, K)
    for lod in range(6): struct.pack_into('<HH', look, 4 * (16 + lod), 0, 0)
    built = bytearray(model.section(TAG_BUILT)); lo, hi = pos.min(0), pos.max(0); c = (lo + hi) / 2; r = float(np.linalg.norm(pos - c, axis=1).max())
    struct.pack_into('<7f', built, 0, *c, r, *((hi - lo) / 2))
    for i in range(5): struct.pack_into('<f', built, 0x34 + 4 * i, lod_distance)
    struct.pack_into('<II', built, 0x64, len(idx_all), N)
    return rebuild(model, {
        TAG_INDEX: encode_index(idx_all), TAG_STD_VERT: encode_std(pos_units, tw, t2, uv_units),
        TAG_UV1: np.clip(np.rint(uv1 * 32768.0), -32768, 32767).astype('<i2').tobytes(), TAG_COL: col.astype('<u4').tobytes(),
        TAG_MESHES: b''.join(entries), TAG_SKIN_BATCH: skin_table, TAG_SKIN_DATA: skin_data, TAG_LOOK: bytes(look), TAG_BUILT: bytes(built)})
