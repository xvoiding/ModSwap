import sys, struct
from .uepkg import R, parse_uasset
from .skmesh import skip_tagged_props
def parse_tex(base, verbose=True):
    d=parse_uasset(open(base+'.uasset','rb').read()); u=open(base+'.uexp','rb').read()
    r=R(u,0); props=skip_tagged_props(r,d)
    o=dict(d=d,u=u,props=props,props_end=r.p)
    o['guidbool']=r.i32(); o['strip1']=(r.u8(),r.u8()); o['strip2']=(r.u8(),r.u8()); o['cooked']=r.i32()
    o['fmtname']=(r.i32(),r.i32()); o['skip_pos']=r.p; o['skip']=r.i64()
    o['hdr_pos']=r.p
    o['sx'],o['sy'],o['packed']=r.i32(),r.i32(),r.u32()
    o['fmt']=r.fstr(); o['first_mip']=r.i32(); n=r.i32(); o['nmips']=n
    mips=[]
    for i in range(n):
        m=dict(pos=r.p); m['cooked']=r.i32(); m['flags']=r.u32(); m['count']=r.i32(); m['disk']=r.i32(); m['off']=r.i64()
        if not (m['flags']&0x100) :   # not in separate file => inline payload
            m['inline']=u[r.p:r.p+m['count']]; r.p+=m['count']
        m['sx'],m['sy'],m['sz']=r.i32(),r.i32(),r.i32(); m['end']=r.p; mips.append(m)
    o['mips']=mips; o['tail_pos']=r.p; o['tail']=u[r.p:]
    return o
