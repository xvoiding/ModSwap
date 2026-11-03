"""Write UE4 Texture2D packages (uasset/uexp/ubulk) from a template texture of the same pixel format."""
import struct
from .uepkg import R, parse_uasset
from .tex import parse_tex

def rename_names(ua, mapping):
    d=parse_uasset(ua); ua=bytearray(ua); r=R(bytes(ua),d['name_off']); n=0
    for _ in range(d['name_count']):
        p=r.p; ln=r.i32(); s=bytes(ua[r.p:r.p+ln-1]).decode('latin1'); r.p+=ln; r.u16(); r.u16()
        if s in mapping:
            t=mapping[s]; assert len(t)==len(s)
            ua[p+4:p+4+len(t)]=t.encode('latin1'); n+=1
    return bytes(ua), n

def i32(x): return struct.pack('<i',x)
def u32(x): return struct.pack('<I',x)
def i64(x): return struct.pack('<q',x)

def build_texture(tmpl_base, out_base, chain, rename, size=2048, first_mip=None):
    AT = size
    o=parse_tex(tmpl_base); u=o['u']; d=o['d']; H=d['total_header']
    ua,nr=rename_names(open(tmpl_base+'.uasset','rb').read(), rename); assert nr>=1 or not rename,(nr,)
    props=bytearray(u[:o['props_end']])
    imp=[q for q in o['props'] if q[0]=='ImportedSize']; assert imp, 'template has no ImportedSize property'
    props[imp[0][5]:imp[0][5]+8]=struct.pack('<ii',AT,AT)
    for q in o['props']:                       # a LODBias on the template would drop our top mip
        if q[0]=='LODBias' and q[2]==4: props[q[5]:q[5]+4]=struct.pack('<i',0)
    m0=o['mips'][0]
    fmtbytes=u[o['hdr_pos']+12:o['mips'][0]['pos']-8]
    nm=len(chain)
    buf=bytearray(props)
    buf+=u[o['props_end']:o['hdr_pos']]        # guid bool, strip flags, cooked, fmt name, skip(int64) placeholder
    skip_pos=o['skip_pos']
    buf+=struct.pack('<iiI',AT,AT,o['packed'])+fmtbytes
    buf+=i32(o['first_mip'] if first_mip is None else first_mip)+i32(nm)
    # UE4.23 (and older) cooks store the offset of a .ubulk payload relative to the package's BulkDataStartOffset (stored = position in .ubulk - bulk_start);
    # later cooks store the plain position. Detect which one this template uses.
    bigm=[m for m in o['mips'] if 'inline' not in m]; inls=[m for m in o['mips'] if 'inline' in m]
    # Mips at or above `thr` live in the .ubulk, smaller ones inline - exactly like the template. A template with NO separate-file mips (a small or
    # never-streamed texture) keeps everything inline, so ours must too: the old code wrote big mips with the template's inline flags and a payload in
    # the .ubulk, which the game cannot read (blurry blobs / flat grey).
    if bigm: thr=min(max(m['sx'],m['sy']) for m in bigm); bulk_flags=bigm[0]['flags']
    else: thr=None; bulk_flags=None
    rel_off=bool(bigm) and bigm[0]['off']==-d['bulk_start']
    ubulk=bytearray(); bulk_fields=[]
    # bulk: levels with max(w,h)>=128 live in .ubulk; rest inline
    for lvl,(w,h,data) in enumerate(chain):
        big=(thr is not None and max(w,h)>=thr) or (not inls)         # (a template with only separate-file mips keeps ours there too)
        buf+=i32(m0['cooked'])
        if big:
            buf+=u32(bulk_flags if bulk_flags is not None else m0['flags'])+i32(len(data))+i32(len(data)); bulk_fields.append((len(buf),len(ubulk))); buf+=i64(len(ubulk)); ubulk+=data
        else:
            inl=inls[0]
            # header is cooked,flags,count,disk (16) + off(8) = 24 bytes, payload follows
            payload_pos=len(buf)+4+4+4+8
            buf+=u32(inl['flags'])+i32(len(data))+i32(len(data))+i64(H+payload_pos)+data
        buf+=i32(w if w>=4 else 4)+i32(h if h>=4 else 4)+i32(1)
    tail_pos=len(buf)
    buf+=o['tail']
    struct.pack_into('<q',buf,skip_pos,H+tail_pos+4)
    exp_size=len(buf)-4
    if rel_off:
        for at,pos_in_ubulk in bulk_fields: struct.pack_into('<q',buf,at,pos_in_ubulk-(H+exp_size))     # bulk_start is set to H+exp_size below
    ue=bytes(buf)
    ua=bytearray(ua)
    e=d['exports'][0]
    struct.pack_into('<q',ua,e['_size_pos'],exp_size)
    bpos=ua.find(struct.pack('<q',d['bulk_start'])); assert bpos>0
    struct.pack_into('<q',ua,bpos,H+exp_size)
    open(out_base+'.uasset','wb').write(ua); open(out_base+'.uexp','wb').write(ue); open(out_base+'.ubulk','wb').write(ubulk)
    return len(ubulk)



# ---------------------------------------------------------------- read back / verify
def mip_payload(base, o, i):
    """the pixel bytes of mip i of a texture package on disk (inline or in its .ubulk)"""
    m = o['mips'][i]
    if 'inline' in m: return m['inline']
    ub = open(base + '.ubulk', 'rb').read()
    bigm = [x for x in o['mips'] if 'inline' not in x]
    rel = bigm[0]['off'] == -o['d']['bulk_start']
    pos = m['off'] + o['d']['bulk_start'] if rel else m['off']
    return ub[pos:pos + m['count']]


def check_texture(base, chain):
    """Read a texture package we just wrote and verify it hangs together the way the game will read it: every mip's size, flags and payload,
    where the payload sits (inline or in the .ubulk), the pointers in the header. -> list of problems (empty = fine)."""
    probs = []
    try: o = parse_tex(base)
    except Exception as e: return ['the written texture cannot be read back: %r' % (e,)]
    d, u = o['d'], o['u']; H = d['total_header']; ub = open(base + '.ubulk', 'rb').read() if __import__('os').path.exists(base + '.ubulk') else b''
    if o['nmips'] != len(chain): probs.append('mip count %d, expected %d' % (o['nmips'], len(chain)))
    if d['exports'][0]['size'] != len(u) - 4: probs.append('export size %d does not match the data (%d)' % (d['exports'][0]['size'], len(u) - 4))
    if d['bulk_start'] != H + len(u) - 4: probs.append('bulk data start points to %d, expected %d' % (d['bulk_start'], H + len(u) - 4))
    if o['skip'] != H + o['tail_pos'] + 4: probs.append('skip pointer %d, expected %d' % (o['skip'], H + o['tail_pos'] + 4))
    bulk_total = 0
    for i, ((w, h, data), m) in enumerate(zip(chain, o['mips'])):
        tag = 'mip %d (%dx%d)' % (i, w, h)
        if (m['sx'], m['sy']) != (max(w, 4), max(h, 4)): probs.append('%s: header says %dx%d' % (tag, m['sx'], m['sy']))
        if m['count'] != len(data) or m['disk'] != len(data): probs.append('%s: size %d/%d, expected %d' % (tag, m['count'], m['disk'], len(data)))
        if 'inline' in m:
            if m['flags'] & 0x100: probs.append('%s: inline mip flagged as separate-file' % tag)
            if m['inline'] != data: probs.append('%s: inline pixels differ from what was meant to be written' % tag)
            if m['off'] != H + m['pos'] + 24: probs.append('%s: inline payload offset %d, expected %d' % (tag, m['off'], H + m['pos'] + 24))
        else:
            if not m['flags'] & 0x100: probs.append('%s: separate-file mip is not flagged as such (flags 0x%x)' % (tag, m['flags']))
            bulk_total += len(data)
            try:
                if mip_payload(base, o, i) != data: probs.append('%s: the .ubulk bytes at its offset differ from what was meant to be written' % tag)
            except Exception as e: probs.append('%s: payload unreadable (%r)' % (tag, e))
    if bulk_total != len(ub): probs.append('.ubulk is %d bytes, mips need %d' % (len(ub), bulk_total))
    return probs


def describe_texture(base):
    """one-line-per-fact summary of a texture package (for the texture report)"""
    o = parse_tex(base); d = o['d']; out = []
    out.append('format %s  %dx%d  mips %d  first_mip %s  packed 0x%x' % (o['fmt'], o['sx'], o['sy'], o['nmips'], o['first_mip'], o['packed']))
    out.append('properties: ' + ', '.join('%s(%s)' % (q[0], q[1]) for q in o['props']))
    bigm = [m for m in o['mips'] if 'inline' not in m]
    out.append('separate-file (.ubulk) mips: %d of %d | offsets %s' % (len(bigm), o['nmips'], 'relative to bulk start' if bigm and bigm[0]['off'] == -d['bulk_start'] else 'plain'))
    for i, m in enumerate(o['mips'][:4]): out.append('  mip %d: %dx%d  %s  flags 0x%x  %d bytes' % (i, m['sx'], m['sy'], 'inline' if 'inline' in m else 'ubulk', m['flags'], m['count']))
    return out


def bc3_alpha_median(data):
    """median of the alpha channel of BC3/DXT5 pixel data (block = 8 bytes alpha + 8 bytes colour)"""
    import numpy as np
    n = len(data) // 16
    if n == 0: return 255
    b = np.frombuffer(data[:n * 16], np.uint8).reshape(n, 16)[:, :8]
    a0 = b[:, 0].astype(np.int32); a1 = b[:, 1].astype(np.int32)
    bits = np.zeros(n, np.uint64)
    for k in range(6): bits |= b[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    pal = np.zeros((n, 8), np.int32); pal[:, 0] = a0; pal[:, 1] = a1
    for k in range(2, 8):
        pal[:, k] = np.where(a0 > a1, ((8 - k) * a0 + (k - 1) * a1) // 7, np.where(k < 6, ((6 - k) * a0 + (k - 1) * a1) // 5, 0 if k == 6 else 255))
    idx = np.stack([((bits >> np.uint64(3 * i)) & np.uint64(7)).astype(np.int64) for i in range(16)], 1)
    return int(np.median(np.take_along_axis(pal, idx, 1)))
