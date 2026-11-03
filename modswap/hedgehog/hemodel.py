"""Hedgehog Engine 2 'NEDMDLV5' models (one level of detail of a Sonic Frontiers .model): READING. Layout worked out on real files (Sonic, Amy, Knuckles, Tails);
HedgeLib (MIT, Radfordhound) documents the same mesh / mesh-group / node structures for Sonic Forces, which this follows.

Two forms exist. Inside a Needle archive (the character models) pointers are relative little-endian values as described below; a bare chunk (some small .model files) keeps
them as BIG-endian offsets counted from byte 0x10 (`HeModel.relative` tells which). The rest is identical.
The chunk:  16-byte header (u32 size|flags, u32, u32 offset of the offset table, u32 number of entries in it), then data; the data starts at byte 0x10... but every
pointer is a LITTLE-endian u32 RELATIVE TO ITS OWN ADDRESS (target = address of the pointer + its value), while counts, sizes, floats and vertex data are BIG endian.
  model header (found by its node count; always 8 words): meshGroups (count, ptr), morphers (count, ptr), node count, ptr to node pointers, ptr to node matrices, ptr to bounds
  mesh group  (0x28 bytes + a name string): opaque, transparent, punch-through = (mesh count, ptr to mesh pointers) each, then 16 bytes for 'special' meshes
  mesh (0x2C): material name ptr | index count, ptr to u16 indices (triangle LIST) | vertex count | vertex size | ptr to vertices | ptr to vertex elements |
               bone count, ptr to bone table (u8 or u16 node numbers) | texture unit count, ptr to units (name ptr, index)
  vertex element (12 bytes): u32 byte offset, u32 format code, u32 usage (type << 16 | index); a format of 0xFFFFFFFF ends the list
  node: s32 parent, ptr to name. node matrices: 4x4 floats (big endian) = the INVERSE bind pose (world -> bone), rotation + translation in the first three rows.
Nothing here writes to the game.
"""
import struct
from dataclasses import dataclass, field
import numpy as np

# vertex element usages (type << 16 | index)
POSITION, BLENDWEIGHT, BLENDINDEX, NORMAL, UV, TANGENT, BINORMAL, COLOR = 0x00000, 0x10000, 0x20000, 0x30000, 0x50000, 0x60000, 0x70000, 0xA0000
# format codes seen in Sonic Frontiers: code -> (name, bytes)
FORMATS = {0x2A23B9: ('float3', 12), 0x2C23A5: ('float4', 16), 0x2C235F: ('half2', 4), 0x2A2187: ('dec3n', 4), 0x1A2086: ('ubyte4n', 4), 0x1A2286: ('ubyte4', 4),
           0x1A225A: ('ushort4', 8), 0x2C2359: ('half2', 4), 0x2C2A5F: ('half4', 8), 0x1A23B9: ('float2', 8)}


def _decode_dec3n(w):
    """10:10:10:2 signed normalised -> (N,3) floats (x lowest bits)"""
    def s(v): v = v.astype(np.int64); return np.where(v >= 512, v - 1024, v) / 511.0
    return np.stack([s(w & 0x3FF), s((w >> 10) & 0x3FF), s((w >> 20) & 0x3FF)], 1)


@dataclass
class Element:
    offset: int
    fmt: int
    usage: int


@dataclass
class Mesh:
    material: str
    faces: np.ndarray                 # (T,3) indices into this mesh's vertices
    vertex_count: int
    vertex_size: int
    vertex_data: bytes
    elements: list
    bones: list                       # node numbers the vertex bone indices refer to
    texture_units: list               # [(name, index)]
    group: int = 0
    slot: str = 'opaque'
    raw: dict = field(default_factory=dict)

    def element(self, usage): return next((e for e in self.elements if e.usage == usage), None)

    def _field(self, e, nbytes, dtype):
        v = np.frombuffer(self.vertex_data, np.uint8).reshape(self.vertex_count, self.vertex_size)
        return np.ascontiguousarray(v[:, e.offset:e.offset + nbytes]).view(dtype).reshape(self.vertex_count, -1)

    def positions(self):
        e = self.element(POSITION)
        if e is None or e.fmt != 0x2A23B9: raise ValueError('this mesh has no float3 position (format %s)' % (e and hex(e.fmt)))
        return self._field(e, 12, '>f4').astype(np.float64)

    def normals(self):
        e = self.element(NORMAL)
        if e is None: return None
        if e.fmt == 0x2A2187: n = _decode_dec3n(self._field(e, 4, '>u4')[:, 0])
        elif e.fmt == 0x2A23B9: n = self._field(e, 12, '>f4').astype(np.float64)
        else: raise ValueError('normal format %s not supported' % hex(e.fmt))
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)

    def uvs(self, index=0):
        e = self.element(UV + index)
        if e is None: return None
        if e.fmt in (0x2C235F, 0x2C2359): return self._field(e, 4, '>f2').astype(np.float64)
        if e.fmt == 0x1A23B9: return self._field(e, 8, '>f4').astype(np.float64)
        raise ValueError('uv format %s not supported' % hex(e.fmt))

    def colors(self):
        e = self.element(COLOR)
        return None if e is None or e.fmt not in (0x1A2086, 0x1A2286) else self._field(e, 4, 'u1')

    def skin(self):
        """-> (bone node numbers (N,4) int, weights (N,4) float summing to 1), or None for an unskinned mesh"""
        ei, ew = self.element(BLENDINDEX), self.element(BLENDWEIGHT)
        if ei is None or ew is None: return None
        if ei.fmt == 0x1A225A: idx = self._field(ei, 8, '>u2').astype(np.int64)
        else: idx = self._field(ei, 4, 'u1').astype(np.int64)
        w = self._field(ew, 4, 'u1').astype(np.float64) / 255.0
        tab = np.array(self.bones, np.int64); nodes = tab[np.minimum(idx, max(len(tab) - 1, 0))] if len(tab) else idx
        s = w.sum(1, keepdims=True); w = np.where(s > 0, w / np.maximum(s, 1e-9), 0)
        return nodes, w


class HeModel:
    def __init__(self, data):
        self.data = bytes(data)
        if len(self.data) < 0x40: raise ValueError('too short to be a model')
        self.size = struct.unpack_from('>I', self.data, 0)[0] & 0x0FFFFFFF
        if self.size != len(self.data): raise ValueError('model says %d bytes, chunk has %d' % (self.size, len(self.data)))
        self.table_at, self.table_count = struct.unpack_from('>II', self.data, 8)
        self.relative = True
        try: self.header = self._find_header()
        except ValueError:
            self.relative = False                       # a bare chunk (not inside a Needle archive) keeps its pointers as BIG-endian absolute offsets
            self.header = self._find_header()
        self._nodes = None

    # ------------------------------------------------------------ helpers
    def be(self, a): return struct.unpack_from('>I', self.data, a)[0]
    def sbe(self, a): return struct.unpack_from('>i', self.data, a)[0]
    def ptr(self, a): return a + struct.unpack_from('<I', self.data, a)[0] if self.relative else struct.unpack_from('>I', self.data, a)[0] + 0x10
    def cstr(self, a): e = self.data.index(b'\0', a); return self.data[a:e].decode('latin1')

    def pointer_table(self):
        """positions listed in the trailing offset table"""
        return [self.be(self.table_at + 4 * i) for i in range(self.table_count)]

    def _find_header(self):
        """the model header is the 8-word struct (…, node count, three pointers) near the start of the data; its pointers must land inside the chunk"""
        n = len(self.data)
        for a in range(0x10, min(n - 32, 0x400000), 4):
            try:
                gc, up, nc = self.be(a), self.be(a + 8), self.be(a + 16)
                if not (0 < gc < 64 and up < 64 and 0 < nc < 4096): continue
                np_, mp, bp = self.ptr(a + 20), self.ptr(a + 24), self.ptr(a + 28)
                if not all(0 < p < n for p in (np_, mp, bp, self.ptr(a + 4))): continue
                if mp + 64 * nc > n or np_ + 4 * nc > n: continue
                p0 = self.ptr(np_)
                if not 0 < p0 < n - 8 or not 0 < self.ptr(p0 + 4) < n: continue
                self.cstr(self.ptr(p0 + 4)); return a
            except (struct.error, ValueError): continue
        raise ValueError('could not find the model header')

    # ------------------------------------------------------------ nodes
    def nodes(self):
        """-> (names, parents, inverse-bind matrices (N,4,4))"""
        if self._nodes is None:
            h = self.header; nc = self.be(h + 16); tab = self.ptr(h + 20); mats = self.ptr(h + 24); names = []; par = []
            for i in range(nc):
                nd = self.ptr(tab + 4 * i); par.append(self.sbe(nd)); names.append(self.cstr(self.ptr(nd + 4)))
            M = np.array([struct.unpack_from('>16f', self.data, mats + 64 * i) for i in range(nc)], np.float64).reshape(nc, 4, 4)
            self._nodes = (names, par, M)
        return self._nodes

    def node_world(self):
        """(N,3) bind-pose node positions (the translation of each inverse-bind matrix, inverted)"""
        names, par, M = self.nodes(); out = np.zeros((len(names), 3))
        for i, m in enumerate(M):
            try: out[i] = np.linalg.inv(m)[:3, 3]
            except np.linalg.LinAlgError: out[i] = 0
        return out

    def bounds(self):
        b = self.ptr(self.header + 28); v = struct.unpack_from('>6f', self.data, b)
        return np.array([v[0], v[2], v[4]]), np.array([v[1], v[3], v[5]])

    # ------------------------------------------------------------ meshes
    def meshes(self):
        h = self.header; out = []; gc = self.be(h); gtab = self.ptr(h + 4)
        for gi in range(gc):
            g = self.ptr(gtab + 4 * gi)
            for si, slot in enumerate(('opaque', 'transparent', 'punch')):
                cnt = self.be(g + 8 * si)
                if not cnt: continue
                arr = self.ptr(g + 8 * si + 4)
                for k in range(cnt):
                    m = self.read_mesh(self.ptr(arr + 4 * k)); m.group, m.slot = gi, slot; out.append(m)
        return out

    def read_mesh(self, a):
        mat = self.cstr(self.ptr(a)); fc = self.be(a + 4); fp = self.ptr(a + 8); vc, vs = self.be(a + 12), self.be(a + 16); vp = self.ptr(a + 20); ep = self.ptr(a + 24)
        bc, bp = self.be(a + 28), self.ptr(a + 32); tc, tp = self.be(a + 36), self.ptr(a + 40)
        idx = np.frombuffer(self.data, '>u2', fc, fp).astype(np.int64)
        els = []; q = ep
        while self.be(q + 4) != 0xFFFFFFFF: els.append(Element(self.be(q), self.be(q + 4), self.be(q + 8))); q += 12
        nn = len(self.nodes()[0]); w = 1 if nn <= 255 else 2
        bones = [int.from_bytes(self.data[bp + w * i:bp + w * i + w], 'big') for i in range(bc)]
        units = []
        for i in range(tc):
            u = self.ptr(tp + 4 * i); units.append((self.cstr(self.ptr(u)), self.data[u + 4]))
        return Mesh(mat, idx[:len(idx) // 3 * 3].reshape(-1, 3), vc, vs, self.data[vp:vp + vc * vs], els, bones, units, raw=dict(at=a, faces_at=fp, vertices_at=vp, elements_at=ep, bones_at=bp, units_at=tp))
