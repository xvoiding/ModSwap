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
    thr=min([max(m['sx'],m['sy']) for m in o['mips'] if 'inline' not in m] or [128])
    # UE4.23 (and older) cooks store the offset of a .ubulk payload relative to the package's BulkDataStartOffset (stored = position in .ubulk - bulk_start);
    # later cooks store the plain position. Detect which one this template uses.
    bigm=[m for m in o['mips'] if 'inline' not in m]
    rel_off=bool(bigm) and bigm[0]['off']==-d['bulk_start']
    ubulk=bytearray(); bulk_fields=[]
    # bulk: levels with max(w,h)>=128 live in .ubulk; rest inline
    for lvl,(w,h,data) in enumerate(chain):
        big=(max(w,h)>=thr)
        buf+=i32(m0['cooked'])
        if big:
            buf+=u32(m0['flags'])+i32(len(data))+i32(len(data)); bulk_fields.append((len(buf),len(ubulk))); buf+=i64(len(ubulk)); ubulk+=data
        else:
            inl=[m for m in o['mips'] if 'inline' in m][0]
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

