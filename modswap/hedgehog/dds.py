"""DDS textures as Sonic Frontiers stores them (BC1 'DXT1', BC3 'DXT5', BC5 'ATI2', BC7 through a DX10 header), read and written with the SAME size, format and mip count as an
original texture so the file keeps its exact length (the .pac then needs no moving of anything else). Full mip chain down to 1x1; blocks are 4x4, tiny mips padded to one block."""
import struct
import numpy as np
from PIL import Image

HDR = 128
FOURCC = {b'DXT1': ('bc1', 8), b'DXT5': ('bc3', 16), b'ATI2': ('bc5', 16)}
DXGI = {98: ('bc7', 16), 99: ('bc7', 16), 71: ('bc1', 8), 72: ('bc1', 8), 77: ('bc3', 16), 78: ('bc3', 16), 83: ('bc5', 16), 84: ('bc5', 16)}


class Dds:
    def __init__(self, data):
        d = bytes(data)
        if d[:4] != b'DDS ' or struct.unpack_from('<I', d, 4)[0] != 124: raise ValueError('not a DDS file')
        self.data = d; self.height, self.width = struct.unpack_from('<II', d, 12); self.mips = max(1, struct.unpack_from('<I', d, 28)[0])
        cc = d[84:88]; self.dx10 = cc == b'DX10'
        if self.dx10: self.dxgi = struct.unpack_from('<I', d, 128)[0]; kind = DXGI.get(self.dxgi); self.data_at = 148
        elif cc in FOURCC: kind = FOURCC[cc]; self.dxgi = None; self.data_at = 128
        else: raise ValueError('unsupported DDS format %r' % cc)
        if kind is None: raise ValueError('unsupported DXGI format %d' % self.dxgi)
        self.kind, self.block = kind
        if self.data_at + sum(self.level_size(i) for i in range(self.mips)) != len(d): raise ValueError('DDS size does not match its header (%dx%d, %d mips, %s)' % (self.width, self.height, self.mips, self.kind))

    def level_dims(self, i): return max(1, self.width >> i), max(1, self.height >> i)
    def level_size(self, i): w, h = self.level_dims(i); return ((w + 3) // 4) * ((h + 3) // 4) * self.block

    def decode(self, level=0):
        """(H, W, 4) RGBA of one mip"""
        import texture2ddecoder as D
        w, h = self.level_dims(level); off = self.data_at + sum(self.level_size(i) for i in range(level)); blob = self.data[off:off + self.level_size(level)]
        fn = dict(bc1=D.decode_bc1, bc3=D.decode_bc3, bc5=D.decode_bc5, bc7=D.decode_bc7)[self.kind]
        return np.frombuffer(fn(blob, w, h), np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]


def _pad4(a):
    h, w = a.shape[:2]
    if h % 4 or w % 4: a = np.pad(a, ((0, -h % 4), (0, -w % 4), (0, 0)), mode='edge')
    return a


def _encode(rgba, kind):
    import etcpak
    a = _pad4(np.ascontiguousarray(rgba, np.uint8)); h, w = a.shape[:2]; b = a.tobytes()
    return bytes({'bc1': etcpak.compress_bc1, 'bc3': etcpak.compress_bc3, 'bc5': etcpak.compress_bc5, 'bc7': etcpak.compress_bc7}[kind](b, w, h))


def write_like(template, rgba):
    """a DDS with `template`'s header, size, format and mip count holding the picture `rgba` ((H, W, 3|4) uint8, any size: it is resized to the template's)"""
    t = template if isinstance(template, Dds) else Dds(template)
    a = np.asarray(rgba, np.uint8)
    if a.shape[2] == 3: a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    img = Image.fromarray(a, 'RGBA'); out = bytearray(t.data[:t.data_at])
    for i in range(t.mips):
        w, h = t.level_dims(i); m = np.asarray(img if (w, h) == img.size else img.resize((w, h), Image.LANCZOS if i == 0 else Image.BOX))
        out += _encode(m, t.kind)
    if len(out) != len(t.data): raise ValueError('internal error: new DDS is %d bytes, the original %d' % (len(out), len(t.data)))
    return bytes(out)


def flat_like(template, rgba):
    t = template if isinstance(template, Dds) else Dds(template)
    return write_like(t, np.tile(np.array(rgba, np.uint8), (8, 8, 1)))


def blank_from_header(header):
    """a Dds with the given header (128 bytes, or 148 with a DX10 extension) and zeroed pixels: the template for a texture that only exists as a header (streaming stub)"""
    h = bytes(header); cc = h[84:88]; h = h[:148] if cc == b'DX10' else h[:128]
    height, width = struct.unpack_from('<II', h, 12); mips = max(1, struct.unpack_from('<I', h, 28)[0])
    kind = DXGI.get(struct.unpack_from('<I', h, 128)[0]) if cc == b'DX10' else FOURCC.get(cc)
    if kind is None or len(h) < (148 if cc == b'DX10' else 128): raise ValueError('unsupported DDS header in a streaming stub')
    n = sum(((max(1, width >> i) + 3) // 4) * ((max(1, height >> i) + 3) // 4) * kind[1] for i in range(mips))
    return Dds(h + b'\0' * n)
