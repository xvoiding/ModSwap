"""Generic texture atlas packing + UV remapping + mip/compress helpers.

Any number of source textures (one per material) are packed into a single square atlas
(the way most games' character materials expect: 1 material, 1 base-colour texture).
Textures whose UVs run outside 0..1 are tiled into a larger cell so wrapping still looks right.
"""
from dataclasses import dataclass
import numpy as np
from PIL import Image


@dataclass
class Cell:
    x: int          # pixel position of the cell in the atlas
    y: int
    w: int          # cell size in pixels
    h: int
    u0: float       # UV rect (in source-texture UV space) this cell covers
    v0: float
    u1: float
    v1: float
    src_w: int      # source texture size (before scaling)
    src_h: int


TILE_PIXELS = 4096 * 4096                                                   # most pixels a tiled cell is built from (bigger tilings are built from a smaller copy of the picture)


def uv_extents(uv, mat, n_mats, pad_frac=0.004, wraps=None):
    """Per-material UV bounds, at least 0..1 along each axis a texture is tiled. A CLAMPED axis only needs 0..1 (everything outside is the edge pixel, and remap_uv clamps to it). On other axes
    a few stray vertices far outside (a common modelling leftover) do not stretch the cell: when the range is wider than 4 tiles the extreme 0.2% (at least 2 values) on each side are
    ignored (the strays are clamped to the cell edge by remap_uv)."""
    out = []
    for m in range(n_mats):
        k = mat == m
        if not k.any():
            out.append((0.0, 0.0, 1.0, 1.0)); continue
        u = uv[k]; lo = u.min(0) - pad_frac; hi = u.max(0) + pad_frac
        for ax in (0, 1):
            if hi[ax] - lo[ax] > 4:
                v = np.sort(u[:, ax]); cut = max(2, int(0.002 * len(v))); cut = min(cut, (len(v) - 1) // 2); lo[ax] = v[cut] - pad_frac; hi[ax] = v[-1 - cut] + pad_frac
            if wraps is not None and wraps[m][ax] == 'clamp': lo[ax], hi[ax] = 0.0, 1.0
            if hi[ax] - lo[ax] > 16: c = 0.5 * (lo[ax] + hi[ax]); lo[ax], hi[ax] = c - 8, c + 8
        u0 = min(0.0, np.floor(lo[0] * 4) / 4); v0 = min(0.0, np.floor(lo[1] * 4) / 4)
        u1 = max(1.0, np.ceil(hi[0] * 4) / 4);  v1 = max(1.0, np.ceil(hi[1] * 4) / 4)
        if wraps is not None:
            if wraps[m][0] == 'clamp': u0, u1 = 0.0, 1.0
            if wraps[m][1] == 'clamp': v0, v1 = 0.0, 1.0
        out.append((u0, v0, u1, v1))
    return out


def wrap_of(im):
    """how a picture repeats outside 0..1: ('repeat'|'mirror'|'clamp' for u, same for v). Set by the loaders that know (glTF samplers, FBX wrap modes); repeat otherwise."""
    return getattr(im, 'wrap', ('repeat', 'repeat'))


def _wrap_index(n, a, b, mode):
    """source pixel index for every pixel of the uv range [a, b] of a picture that is n pixels wide per unit"""
    count = max(1, int(round((b - a) * n))); t = a + (np.arange(count) + 0.5) / n
    f = (1.0 - np.abs((t % 2.0) - 1.0)) if mode == 'mirror' else np.clip(t, 0.0, 1.0) if mode == 'clamp' else t % 1.0
    return np.minimum((f * n).astype(np.int64), n - 1)


def _same_picture_groups(images):
    """-> (group index per material, number of groups): materials whose pictures are pixel-identical share one group (many models use ONE texture for all their materials)"""
    import hashlib
    seen = {}; grp = []
    for im in images:
        key = (im.size, im.mode, wrap_of(im), hashlib.md5(im.tobytes()).hexdigest()); grp.append(seen.setdefault(key, len(seen)))
    return np.array(grp, np.int64), len(seen)


def pack(images, uv, mat, size=2048, gutter=4):
    """images: list of PIL images (index == material id). Returns (atlas RGB uint8 HxWx3, [Cell] per material). Materials that use the SAME picture share one cell, so a model with
    twenty materials and one 2048 texture gets that texture once, not twenty times shrunk."""
    grp, ng = _same_picture_groups(images)
    if ng < len(images):
        first = {}
        for i, g in enumerate(grp): first.setdefault(int(g), i)
        atl, gcells = _pack_distinct([images[first[g]] for g in range(ng)], uv, np.asarray(grp)[np.asarray(mat)], size, gutter)
        return atl, [gcells[int(g)] for g in grp]
    return _pack_distinct(images, uv, mat, size, gutter)


def _pack_distinct(images, uv, mat, size=2048, gutter=4):
    n = len(images)
    ext = uv_extents(uv, mat, n, wraps=[wrap_of(im) for im in images])
    # desired cell size at 1:1 texel density
    want = [((u1 - u0) * im.width, (v1 - v0) * im.height) for (u0, v0, u1, v1), im in zip(ext, images)]
    # find a global scale s so everything fits in size x size using shelf packing
    def try_pack(s):
        order = sorted(range(n), key=lambda i: -want[i][1])
        x = y = rowh = 0; pos = {}
        for i in order:
            w = int(np.ceil(want[i][0] * s)) + 2 * gutter; h = int(np.ceil(want[i][1] * s)) + 2 * gutter
            if w > size: return None
            if x + w > size: x = 0; y += rowh; rowh = 0
            if y + h > size: return None
            pos[i] = (x, y, w, h); x += w; rowh = max(rowh, h)
        return pos
    lo, hi, best = 0.002, 1.0, None
    p = try_pack(1.0)
    if p is not None: best = (1.0, p)
    else:
        for _ in range(30):
            mid = (lo + hi) / 2; p = try_pack(mid)
            if p is None: hi = mid
            else: lo = mid; best = (mid, p)
        if best is None: raise ValueError('textures cannot be packed')
    s, pos = best
    atlas = np.zeros((size, size, 3), np.uint8)
    cells = [None] * n
    for i, (x, y, w, h) in pos.items():
        u0, v0, u1, v1 = ext[i]
        im = images[i].convert('RGB')
        cw, ch = w - 2 * gutter, h - 2 * gutter
        # the part of the (repeated / mirrored / clamped) picture that the cell's uv rect covers, then resized to the cell
        src = np.array(im); wu, wv = wrap_of(images[i]); W0, H0 = im.width, im.height
        total = (u1 - u0) * W0 * (v1 - v0) * H0
        if total > TILE_PIXELS:                                                # a huge tiling: build it from a smaller copy of the picture
            f = (TILE_PIXELS / total) ** 0.5; src = np.array(im.resize((max(1, int(W0 * f)), max(1, int(H0 * f))), Image.LANCZOS))
        H1, W1 = src.shape[:2]
        reps = src[_wrap_index(H1, v0, v1, wv)][:, _wrap_index(W1, u0, u1, wu)]
        cell = np.array(Image.fromarray(reps).resize((cw, ch), Image.LANCZOS))
        padded = np.pad(cell, ((gutter, gutter), (gutter, gutter), (0, 0)), mode='edge')
        atlas[y:y + h, x:x + w] = padded
        cells[i] = Cell(x + gutter, y + gutter, cw, ch, u0, v0, u1, v1, im.width, im.height)
    return atlas, cells


def remap_uv(uv, mat, cells, size):
    out = np.zeros_like(uv, dtype=np.float64)
    for m, c in enumerate(cells):
        if c is None: continue
        k = mat == m
        uc = np.clip(uv[k, 0], c.u0, c.u1); vc = np.clip(uv[k, 1], c.v0, c.v1)                # (a stray uv outside the cell stays inside its own cell)
        out[k, 0] = (c.x + (uc - c.u0) / (c.u1 - c.u0) * c.w) / size
        out[k, 1] = (c.y + (vc - c.v0) / (c.v1 - c.v0) * c.h) / size
    return out


# ---------------------------------------------------------------- mips + BCn compression
def mip_chain(arr):
    cur = arr.astype(np.float32); out = []
    while True:
        h, w = cur.shape[:2]; out.append(cur)
        if h == 1 and w == 1: break
        cur = cur.reshape(max(h // 2, 1), 2 if h > 1 else 1, max(w // 2, 1), 2 if w > 1 else 1, -1).mean(axis=(1, 3))
    return out


def _rgba4(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8); h, w = a.shape[:2]
    if a.shape[2] == 3: a = np.dstack([a, np.full((h, w), 255, np.uint8)])
    if h < 4 or w < 4: a = np.pad(a, ((0, max(0, 4 - h)), (0, max(0, 4 - w)), (0, 0)), mode='edge')
    return a


def compress_chain(arr, kind):
    """kind: bc1 / bc3 / bc5. Returns [(w,h,bytes)] for every mip (min block 4x4)."""
    import etcpak
    fn = {'bc1': etcpak.compress_bc1, 'bc3': etcpak.compress_bc3, 'bc5': etcpak.compress_bc5}[kind]
    res = []
    for lvl in mip_chain(arr):
        a = _rgba4(lvl); h, w = a.shape[:2]
        res.append((w, h, bytes(fn(a.tobytes(), w, h))))
    return res
