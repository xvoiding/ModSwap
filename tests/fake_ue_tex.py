"""Builds a small but structurally real UE4 Texture2D package (.uasset/.uexp/.ubulk) so the texture writer can be tested without any game files.
mode: 'bulk' (big mips in a .ubulk, small ones inline) or 'inline' (every mip inline, like a small / never-streamed texture).
rel:  4.23-style bulk offsets (stored = position in .ubulk - bulk start) instead of plain positions."""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap import atlas

NAMES = ['/Script/Engine', 'Texture2D', 'ImportedSize', 'StructProperty', 'IntPoint', 'LODBias', 'IntProperty', 'None', 'PF_DXT1', 'TestTex']


def fstr(s): b = s.encode('latin1') + b'\0'; return struct.pack('<i', len(b)) + b
def i32(x): return struct.pack('<i', x)
def u32(x): return struct.pack('<I', x)
def i64(x): return struct.pack('<q', x)
N = {n: i for i, n in enumerate(NAMES)}


def make_texture(base, size=256, kind='bc1', mode='bulk', rel=False, thr=64, seed=1):
    rng = np.random.default_rng(seed)
    img = rng.integers(0, 255, (size, size, 3), dtype=np.uint8)
    chain = atlas.compress_chain(img, kind)
    # ---- header (.uasset): summary, names, imports, exports
    def build_header(total, bulk_start, exp_size):
        names = b''.join(fstr(n) + struct.pack('<HH', 0, 0) for n in NAMES)
        imports = struct.pack('<iiiiiiii', N['/Script/Engine'], 0, N['Texture2D'], 0, 0, N['TestTex'], 0, 0)[:28]
        imports = i32(N['/Script/Engine']) + i32(0) + i32(N['Texture2D']) + i32(0) + i32(0) + i32(N['TestTex']) + i32(0)
        s_len = 0
        def summary(name_off, imp_off, exp_off):
            b = u32(0x9E2A83C1) + i32(-7) + i32(864) + i32(517) + i32(0) + i32(0) + i32(total) + fstr('None') + u32(0x80000000)
            b += i32(len(NAMES)) + i32(name_off) + i32(0) + i32(0) + i32(1) + i32(exp_off) + i32(1) + i32(imp_off) + i32(0) + i32(0) + i32(0) + i32(0) + i32(0)
            b += b'\x11' * 16 + i32(0)
            b += struct.pack('<HHHI', 4, 25, 0, 1) + fstr('++UE4+Release-4.25') + struct.pack('<HHHI', 4, 25, 0, 1) + fstr('++UE4+Release-4.25')
            b += u32(0) + i32(0) + u32(0) + i32(0) + i32(0) + i64(bulk_start) + i32(0) + i32(0) + i32(0) + i32(0)
            return b
        n_off = len(summary(0, 0, 0)); i_off = n_off + len(names); e_off = i_off + len(imports)
        exp = i32(-1) + i32(0) + i32(0) + i32(0) + i32(N['TestTex']) + i32(0) + u32(0) + i64(exp_size) + i64(total) + i32(0) + i32(0) + i32(0) + b'\0' * 16 + u32(0) + i32(0) + i32(1) + i32(-1) + i32(-1) + i32(-1) + i32(-1) + i32(-1)
        return summary(n_off, i_off, e_off) + names + imports + exp
    probe = build_header(0, 0, 0); H = len(probe)
    # ---- export (.uexp)
    props = (i32(N['ImportedSize']) + i32(0) + i32(N['StructProperty']) + i32(0) + i32(8) + i32(0) + i32(N['IntPoint']) + i32(0) + b'\0' * 16 + b'\0' + struct.pack('<ii', size, size)
             + i32(N['LODBias']) + i32(0) + i32(N['IntProperty']) + i32(0) + i32(4) + i32(0) + b'\0' + i32(0) + i32(N['None']) + i32(0))
    body = bytearray(props)
    body += i32(0) + b'\0\0' + b'\0\0' + i32(1) + i32(N['PF_DXT1']) + i32(0)         # guid bool, strip flags x2, cooked, pixel-format name
    skip_pos = len(body); body += i64(0)
    body += struct.pack('<iiI', size, size, 0) + fstr('PF_DXT1') + i32(0) + i32(len(chain))
    ubulk = bytearray(); fixups = []
    for w, h, data in chain:
        big = mode == 'bulk' and max(w, h) >= thr
        body += i32(1)
        if big:
            body += u32(0x100) + i32(len(data)) + i32(len(data)); fixups.append((len(body), len(ubulk))); body += i64(0); ubulk += data
        else:
            payload = len(body) + 4 + 4 + 4 + 8
            body += u32(0x40) + i32(len(data)) + i32(len(data)) + i64(H + payload) + data
        body += i32(max(w, 4)) + i32(max(h, 4)) + i32(1)
    tail_pos = len(body); body += b'\0' * 8 + bytes.fromhex('c1832a9e')
    exp_size = len(body) - 4; bulk_start = H + exp_size
    for at, p in fixups: struct.pack_into('<q', body, at, p - bulk_start if rel else p)
    struct.pack_into('<q', body, skip_pos, H + tail_pos + 4)
    ua = build_header(H, bulk_start, exp_size); assert len(ua) == H
    os.makedirs(os.path.dirname(base), exist_ok=True)
    open(base + '.uasset', 'wb').write(ua); open(base + '.uexp', 'wb').write(bytes(body)); open(base + '.ubulk', 'wb').write(bytes(ubulk))
    return img, chain
