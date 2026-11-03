import struct, io

class R:
    def __init__(s, b, pos=0): s.b=b; s.p=pos
    def u8(s): v=s.b[s.p]; s.p+=1; return v
    def i32(s): v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def u32(s): v=struct.unpack_from('<I',s.b,s.p)[0]; s.p+=4; return v
    def i64(s): v=struct.unpack_from('<q',s.b,s.p)[0]; s.p+=8; return v
    def u16(s): v=struct.unpack_from('<H',s.b,s.p)[0]; s.p+=2; return v
    def f32(s): v=struct.unpack_from('<f',s.b,s.p)[0]; s.p+=4; return v
    def guid(s): v=s.b[s.p:s.p+16]; s.p+=16; return v.hex()
    def fstr(s):
        n=s.i32()
        if n==0: return ''
        if n>0:
            v=s.b[s.p:s.p+n-1].decode('latin1'); s.p+=n; return v
        n=-n
        v=s.b[s.p:s.p+(n-1)*2].decode('utf-16le'); s.p+=n*2; return v

def parse_uasset(b):
    r=R(b); d={}
    d['tag']=r.u32()
    assert d['tag']==0x9E2A83C1, hex(d['tag'])
    d['legacy']=r.i32()
    if d['legacy']!=-4: d['ue3']=r.i32()
    d['ue4']=r.i32()
    if d['legacy']<=-8: d['ue5']=r.i32()
    d['lic']=r.i32()
    cv=[]
    n=r.i32()
    for _ in range(n):
        g=r.guid(); v=r.i32(); cv.append((g,v))
    d['custom']=cv
    d['total_header']=r.i32()
    d['folder']=r.fstr()
    d['pkgflags']=r.u32()
    d['name_count']=r.i32(); d['name_off']=r.i32()
    # UE5 packages (legacy <= -8; an 'unversioned' cook writes all versions as 0 and means 'latest', as retoc's output does)
    u5 = d['legacy'] <= -8; v5 = d.get('ue5', 0) if u5 else 0; new5 = u5 and (v5 == 0 or v5 >= 1008)
    d['is_ue5'] = u5
    if new5: d['softpath_count']=r.i32(); d['softpath_off']=r.i32()
    if not (d['pkgflags'] & 0x80000000):  # FilterEditorOnly
        d['loc']=r.fstr()
    d['gather_count']=r.i32(); d['gather_off']=r.i32()
    d['export_count']=r.i32(); d['export_off']=r.i32()
    d['import_count']=r.i32(); d['import_off']=r.i32()
    d['depends_off']=r.i32()
    d['softref_count']=r.i32(); d['softref_off']=r.i32()
    d['searchable_off']=r.i32()
    d['thumb_off']=r.i32()
    d['guid']=r.guid()
    gen=r.i32(); d['gens']=[(r.i32(),r.i32()) for _ in range(gen)]
    d['saved_ver']=(r.u16(),r.u16(),r.u16(),r.u32(),r.fstr())
    d['compat_ver']=(r.u16(),r.u16(),r.u16(),r.u32(),r.fstr())
    d['compflags']=r.u32()
    nchunks=r.i32(); assert nchunks==0
    d['pkgsource']=r.u32()
    na=r.i32(); d['addl']=[r.fstr() for _ in range(na)]
    d['assetreg_off']=r.i32()
    d['bulk_start']=r.i64()
    d['worldtile_off']=r.i32()
    nc=r.i32(); d['chunkids']=[r.i32() for _ in range(nc)]
    d['preload_count']=r.i32(); d['preload_off']=r.i32()
    if u5 and (v5 == 0 or v5 >= 1001): d['names_from_export']=r.i32()
    if u5 and (v5 == 0 or v5 >= 1002): d['payload_toc_off']=r.i64()
    if u5 and (v5 == 0 or v5 >= 1009): d['dataresource_off']=r.i32()
    d['summary_end']=r.p
    d['_summary_fields_pos']={}  # filled by callers if needed
    # names
    r.p=d['name_off']; names=[]
    for _ in range(d['name_count']):
        s=r.fstr(); r.u16(); r.u16(); names.append(s)
    d['names']=names
    # imports
    r.p=d['import_off']; imps=[]
    for _ in range(d['import_count']):
        cp=(r.i32(),r.i32()); cn=(r.i32(),r.i32()); outer=r.i32(); on=(r.i32(),r.i32())
        if u5 and (v5 == 0 or v5 >= 1003): r.i32()                      # bImportOptional
        imps.append(dict(class_pkg=cp,class_name=cn,outer=outer,name=on))
    d['imports']=imps
    # exports
    r.p=d['export_off']; exps=[]
    for i in range(d['export_count']):
        e={}
        e['_pos']=r.p
        e['class']=r.i32(); e['super']=r.i32(); e['template']=r.i32(); e['outer']=r.i32()
        e['name']=(r.i32(),r.i32()); e['flags']=r.u32()
        e['_size_pos']=r.p
        e['size']=r.i64(); e['offset']=r.i64()
        e['forced']=r.i32(); e['notclient']=r.i32(); e['notserver']=r.i32()
        if u5 and (v5 == 0 or v5 >= 1005): e['pkgguid']=''
        else: e['pkgguid']=r.guid()
        if u5 and (v5 == 0 or v5 >= 1006): e['inherited']=r.i32()
        e['pkgflags']=r.u32()
        e['notalways']=r.i32(); e['isasset']=r.i32()
        if u5 and (v5 == 0 or v5 >= 1003): e['genhash']=r.i32()
        e['first_dep']=r.i32(); e['ser_before_ser']=r.i32(); e['create_before_ser']=r.i32()
        e['ser_before_create']=r.i32(); e['create_before_create']=r.i32()
        e['_end']=r.p
        exps.append(e)
    d['exports']=exps
    return d

def nm(d, pair):
    i,num=pair
    s=d['names'][i]
    return s if num==0 else f"{s}_{num-1}"

def objname(d, idx):
    if idx==0: return 'None'
    if idx<0:
        im=d['imports'][-idx-1]; return 'I:'+nm(d,im['name'])
    ex=d['exports'][idx-1]; return 'E:'+nm(d,ex['name'])
