"""Reader for Unreal .locres localization files (versions 1-3). Used only to turn ids like 0350 into the names players know."""
import struct

MAGIC = bytes.fromhex('0E14747567 4A03FC4A15909DC3377F1B'.replace(' ', ''))


class _R:
    def __init__(s, b): s.b = b; s.p = 0
    def i32(s): v = struct.unpack_from('<i', s.b, s.p)[0]; s.p += 4; return v
    def u32(s): v = struct.unpack_from('<I', s.b, s.p)[0]; s.p += 4; return v
    def i64(s): v = struct.unpack_from('<q', s.b, s.p)[0]; s.p += 8; return v
    def u8(s): v = s.b[s.p]; s.p += 1; return v
    def fstr(s):
        n = s.i32()
        if n == 0: return ''
        if n < 0:
            n = -n; v = s.b[s.p:s.p + n * 2 - 2].decode('utf-16-le', 'replace'); s.p += n * 2; return v
        v = s.b[s.p:s.p + n - 1].decode('utf-8', 'replace'); s.p += n; return v


def parse(data):
    """-> {namespace: {key: text}}"""
    r = _R(data); ver = 0; offset = None
    if data[:16] == MAGIC:
        r.p = 16; ver = r.u8()
        if ver >= 2: offset = r.i64()
    else: ver = 0                                                       # legacy files have no magic
    strings = None
    if offset is not None:
        save = r.p; r.p = offset
        n = r.i32(); strings = []
        for _ in range(n):
            strings.append(r.fstr())
            if ver >= 2: r.i32()
        r.p = save
        if ver >= 3: r.i32()
    out = {}
    nns = r.i32()
    for _ in range(nns):
        if ver >= 3: r.u32()
        ns = r.fstr(); nk = r.i32(); d = out.setdefault(ns, {})
        for _ in range(nk):
            if ver >= 3: r.u32()
            key = r.fstr(); r.u32()
            if strings is not None:
                idx = r.i32(); d[key] = strings[idx] if 0 <= idx < len(strings) else ''
            else: d[key] = r.fstr()
    return out
