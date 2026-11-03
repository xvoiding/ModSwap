"""Spider-Man Remastered '.texture' assets (DAT1 type 0x5C4580B9): reading and writing. Layout, checked on 60+ real textures (every pixel size below is reproduced exactly):

  asset  = [36-byte header][DAT1, 92 bytes][pixel data]
  header : u32 type, u32 92 (DAT1 size), u32 pixel bytes, 0, 0, u32 pixel bytes, 0, 0, 0
  DAT1   : '1TAD', u32 type, u32 92, u32 1 section, (u32 tag 4EDE3593, u32 offset 48, u32 size 44), padding to 48
  section (44 bytes, from asset byte 84):
     0 u32 pixel bytes             4 u32 streaming budget (0 when the whole texture is stored, else ~15 x pixel bytes rounded up to 4096)
     8 u16 width, u16 height of the FULL texture      12 u16 width, u16 height of what is STORED here (a big texture stores only its smaller mips)
    16 u16 slices (1; 2D array textures have more), u8 + u8 usage codes (colour 91 00, normal 10 01, gloss 11 xx)
    20 u32 DXGI format (98 = BC7, 99 = BC7 sRGB, 71 / 72 = BC1 / sRGB, 77 / 78 = BC3 ...)    28 u16 1, u8 stored mip count, u8 flag
    32 4 bytes (02 01 01 01)
  pixel data: the mips from the stored size down to a short side of 8 (4x4 blocks, tightly packed), largest first.
Writing starts from a real texture of the same role (so every code byte is the game's own) and changes size, format fields and pixels. Nothing here touches the game by itself."""
import struct
import numpy as np
from PIL import Image

TYPE = 0x5C4580B9
DESC_AT = 84
PIXELS_AT = 128
BLOCK = {98: 16, 99: 16, 71: 8, 72: 8, 77: 16, 78: 16}           # bytes per 4x4 block
BC7, BC7_SRGB, BC1, BC1_SRGB = 98, 99, 71, 72


class Texture:
    def __init__(self, data):
        data = bytes(data)
        if len(data) < PIXELS_AT or struct.unpack_from('<I', data, 0)[0] != TYPE or data[36:40] != b'1TAD': raise ValueError('not a Spider-Man texture asset')
        self.data = data
        self.pixel_bytes, self.stream = struct.unpack_from('<II', data, DESC_AT)
        self.full_w, self.full_h, self.width, self.height, self.slices = struct.unpack_from('<5H', data, DESC_AT + 8)
        self.fmt = struct.unpack_from('<I', data, DESC_AT + 20)[0]
        self.mips = data[DESC_AT + 30]
        if PIXELS_AT + self.pixel_bytes != len(data): raise ValueError('texture says %d pixel bytes, file has %d' % (self.pixel_bytes, len(data) - PIXELS_AT))

    @property
    def pixels(self): return self.data[PIXELS_AT:]

    def levels(self): return levels(self.width, self.height)

    def decode(self, level=0):
        """-> (H, W, 4) uint8 RGBA of one stored mip (BC7 / BC1 / BC3 only)"""
        import texture2ddecoder as D
        if self.slices != 1: raise ValueError('array textures are not decoded')
        w, h = self.levels()[level]; off = sum(size(a, b, self.fmt) for a, b in self.levels()[:level]); blob = self.pixels[off:off + size(w, h, self.fmt)]
        fn = {98: D.decode_bc7, 99: D.decode_bc7, 71: D.decode_bc1, 72: D.decode_bc1, 77: D.decode_bc3, 78: D.decode_bc3}.get(self.fmt)
        if fn is None: raise ValueError('format %d is not decoded' % self.fmt)
        return np.frombuffer(fn(blob, w, h), np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]


def levels(w, h):
    """stored mip sizes: down to a short side of 8, at least one"""
    out = [(w, h)]
    while min(w, h) >= 16: w, h = max(1, w // 2), max(1, h // 2); out.append((w, h))
    return out


def size(w, h, fmt): return ((w + 3) // 4) * ((h + 3) // 4) * BLOCK[fmt]


def _encode(rgba, fmt):
    import etcpak
    h, w = rgba.shape[:2]; b = np.ascontiguousarray(rgba, np.uint8).tobytes()
    if fmt in (98, 99): return bytes(etcpak.compress_bc7(b, w, h))
    if fmt in (71, 72): return bytes(etcpak.compress_bc1(b, w, h))
    if fmt in (77, 78): return bytes(etcpak.compress_bc3(b, w, h))
    raise ValueError('cannot write format %d' % fmt)


def write_like(template, rgba):
    """a new texture asset with the picture `rgba` ((H, W, 3 or 4) uint8, H and W multiples of 8), in the format and with the code bytes of `template` (a Texture or its bytes)"""
    t = template if isinstance(template, Texture) else Texture(template)
    if t.slices != 1: raise ValueError('cannot write over an array texture')
    a = np.asarray(rgba, np.uint8)
    if a.ndim != 3 or a.shape[2] not in (3, 4): raise ValueError('picture must be (H, W, 3 or 4)')
    if a.shape[2] == 3: a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    h, w = a.shape[:2]
    if w % 8 or h % 8 or w > 8192 or h > 8192: raise ValueError('texture size must be a multiple of 8 (got %dx%d)' % (w, h))
    lv = levels(w, h); img = Image.fromarray(a, 'RGBA'); out = bytearray()
    for lw, lh in lv:
        m = a if (lw, lh) == (w, h) else np.asarray(img.resize((lw, lh), Image.BOX if (lw < w) else Image.LANCZOS))
        out += _encode(m, t.fmt)
    d = bytearray(t.data[:PIXELS_AT]); n = len(out)
    struct.pack_into('<I', d, 8, n); struct.pack_into('<I', d, 20, n)
    struct.pack_into('<I', d, DESC_AT, n); struct.pack_into('<I', d, DESC_AT + 4, 0)          # (whole texture stored here: no streaming budget)
    struct.pack_into('<4H', d, DESC_AT + 8, w, h, w, h); d[DESC_AT + 30] = len(lv)
    return bytes(d) + bytes(out)


def flat(template, rgba, side=64):
    """a small solid-colour texture in `template`'s format (a flat normal map, a neutral gloss map)"""
    return write_like(template, np.tile(np.array(rgba, np.uint8), (side, side, 1)))
