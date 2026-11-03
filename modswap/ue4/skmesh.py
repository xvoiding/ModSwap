import struct, sys
from .uepkg import R, parse_uasset, nm

def skip_tagged_props(r, d, verbose=False):
    props=[]
    while True:
        ni=r.i32(); nn=r.i32()
        name=d['names'][ni]
        if name=='None': break
        ti=r.i32(); tn=r.i32(); typ=d['names'][ti]
        size=r.i32(); aidx=r.i32()
        extra=None
        if typ=='StructProperty':
            extra=(d['names'][r.i32()], r.i32()); r.p+=16
        elif typ=='BoolProperty':
            extra=r.u8()
        elif typ in ('ByteProperty','EnumProperty'):
            extra=(d['names'][r.i32()], r.i32())
        elif typ=='ArrayProperty':
            extra=(d['names'][r.i32()], r.i32())
        elif typ in ('MapProperty','SetProperty'):
            extra=((d['names'][r.i32()], r.i32()),(d['names'][r.i32()], r.i32()))
        hasguid=r.u8()
        if hasguid: r.p+=16
        props.append((name,typ,size,aidx,extra,r.p))
        r.p+=size
    return props

def bulk(r, what=''):
    isz=r.i32(); cnt=r.i32()
    start=r.p
    r.p+=isz*cnt
    return dict(isz=isz,cnt=cnt,start=start,end=r.p)


def _lod423(r, uexp, out):
    """UE4.23 FSkeletalMeshLODRenderData: [strip 2][sections][index buffer][ActiveBoneIndices][RequiredBones][positions][tangents+UVs]
    [skin weights][(colour)][adjacency][...]. No BuffersSize / stream strip / lookup / profiles. Verified against SpongeBob Rehydrated."""
    L={}; L['start']=r.p
    L['strip']=(r.u8(),r.u8())
    ns=r.i32(); secs=[]
    for _ in range(ns):
        S={}; S['start']=r.p
        S['strip']=(r.u8(),r.u8())
        S['mat']=struct.unpack_from('<h',uexp,r.p)[0]; r.p+=2
        S['base_index']=r.i32(); S['ntri']=r.i32(); S['recompute_tangent']=r.i32(); S['cast_shadow']=r.i32(); S['base_vertex']=r.u32()
        nc=r.i32(); S['cloth']=nc; assert nc==0, 'cloth mapping data present'
        n=r.i32(); S['bonemap']=struct.unpack_from('<%dH'%n,uexp,r.p); r.p+=2*n
        S['nverts']=r.i32(); S['maxinf']=r.i32()
        S['cloth_asset_idx']=struct.unpack_from('<h',uexp,r.p)[0]; r.p+=2
        S['clothing_guid']=r.guid(); S['clothing_lod']=r.i32()
        S['dup_pos']=r.p
        if not (S['strip'][1] & 1):
            n1=r.i32(); r.p+=n1*4; n2=r.i32(); r.p+=n2*8; S['dup']=(n1,n2)
        S['disabled']=r.i32(); S['end']=r.p; secs.append(S)
    L['sections']=secs; L['after_sections']=r.p
    L['idx_datasize']=r.u8(); L['idx']=bulk(r)
    L['idx_end']=r.p
    n=r.i32(); L['active_bones']=struct.unpack_from('<%dh'%n,uexp,r.p); r.p+=2*n
    L['bones_end_active']=r.p
    n=r.i32(); L['required_bones']=struct.unpack_from('<%dh'%n,uexp,r.p); r.p+=2*n
    L['stream_start']=r.p; L['stream_strip']=(0,0)
    L['pos_stride']=r.i32(); L['pos_n']=r.i32(); L['pos']=bulk(r)
    L['smvb_strip']=(r.u8(),r.u8())
    L['ntex']=r.i32(); L['smvb_n']=r.i32(); L['fullUV']=r.i32(); L['hiTan']=r.i32()
    L['tan']=bulk(r); L['uv']=bulk(r)
    L['sw_strip']=(r.u8(),r.u8())
    L['sw_extra']=r.i32(); L['sw_nverts']=r.i32(); L['sw_varbones']=0; L['sw_maxinf']=8 if L['sw_extra'] else 4; L['sw_numbones']=L['sw_nverts']*L['sw_maxinf']; L['sw_16bit']=0
    L['sw']=bulk(r)
    L['lk_strip']=(0,0); L['lk_n']=0; L['lk']=dict(start=r.p,end=r.p,isz=4,cnt=0)
    L['after_skin']=r.p
    if out['has_col']:
        L['col_strip']=(r.u8(),r.u8()); L['col_stride']=r.i32(); L['col_n']=r.i32(); L['col']=bulk(r) if L['col_n']>0 else None
    else: L['col_strip']=(0,0); L['col_stride']=0; L['col_n']=0; L['col']=None
    L['after_color']=r.p
    if L['strip'][1] & 1: L['adj_datasize']=None; L['adj']=dict(start=r.p,end=r.p,isz=0,cnt=0)
    else: L['adj_datasize']=r.u8(); L['adj']=bulk(r)
    L['after_adj']=r.p
    L['profiles']=0; L['lod_end']=r.p
    return L


def find_native_ue5(uexp, d, base):
    """UE5 cooks from retoc are 'unversioned' (no property names), so there is no property list to skip. Find the native USkeletalMesh data by its
    reference skeleton (bone table: count, then (name, number, parent) with the first parent -1 and the second 0), then step back over the material
    array (40 bytes each), the bounds (7 doubles) and the strip flags. Returns the position of the strip flags."""
    NN=len(d['names']); I=lambda q: struct.unpack_from('<i',uexp,q)[0]; end=min(len(uexp)-40, base+400000)
    for q in range(base, end):
        nb=I(q)
        if not 2<=nb<=2000: continue
        a,n0,par=I(q+4),I(q+8),I(q+12)
        if not (0<=a<NN and n0==0 and par==-1): continue
        if nb>1 and not (0<=I(q+16)<NN and I(q+24)==0): continue
        for n in range(0,64):
            cp=q-40*n-4
            if cp-62>=base and I(cp)==n: return dict(refskel=q, mat_count_pos=cp, nmat=n, skel_start=cp-58)
    raise ValueError('no reference skeleton found in this UE5 mesh')

def walk(uexp, d, exp_idx=1, verbose=True, rtmask=False, all_lods=False, _dbg=None, adj=None, trail=None, v423=False, ue5=False):
    """adj / trail: None = the layout implied by rtmask and the strip flags; True/False forces the adjacency buffer / the per-LOD trailing int32
    (some cooks, e.g. GTA III Definitive, have neither). v423: the UE4.23 skin-weight layout (extra-influences flag instead of the 4.24 header, no lookup
    buffer, no skin weight profiles, no trailing int32)"""
    e=d['exports'][exp_idx]
    base=e['offset']-d['total_header']
    r=R(uexp, base)
    out={}
    out['export_start']=base
    if ue5:
        nat=find_native_ue5(uexp,d,base); out['native']=nat; props=[]; out['props']=props; out['props_end']=nat['skel_start']-4
        out['ue5']=True
    else:
        props=skip_tagged_props(r,d)
        out['props']=props
        out['props_end']=r.p
    # UE4.26+: the colour buffer is only serialized when USkeletalMesh::bHasVertexColors is set
    out['adj_on']=adj; out['trail_on']=trail
    out['has_col']=any(p[0]=='bHasVertexColors' and p[4]==1 for p in props) if (rtmask or v423) else True
    if verbose:
        for p in props: print('  prop',p[0],p[1],'size',p[2],'extra',p[4],'@',p[5])
    if ue5: r.p=out['props_end']
    out['hasguid']=r.i32()   # object guid bool
    out['skel_start']=r.p
    out['strip']=(r.u8(),r.u8())
    if ue5: out['bounds']=struct.unpack_from('<7d',uexp,r.p); r.p+=56        # large world coordinates: doubles
    else: out['bounds']=struct.unpack_from('<7f',uexp,r.p); r.p+=28
    out['mat_start']=r.p
    nmat=r.i32(); mats=[]
    for _ in range(nmat):
        obj=r.i32(); slot=(r.i32(),r.i32()); imp=r.i32(); uv=struct.unpack_from('<2i4f',uexp,r.p); r.p+=24
        mats.append((obj,slot,imp,uv))
    out['mats']=mats; out['mat_end']=r.p
    out['refskel_start']=r.p
    nb=r.i32(); bones=[]
    for _ in range(nb):
        bones.append((r.i32(),r.i32(),r.i32()))  # name idx, name num, parent
    out['bones']=bones
    npose=r.i32(); out['pose_start']=r.p
    if ue5: pose=[struct.unpack_from('<10d',uexp,r.p+i*80) for i in range(npose)]; r.p+=npose*80
    else: pose=[struct.unpack_from('<10f',uexp,r.p+i*40) for i in range(npose)]; r.p+=npose*40
    out['pose']=pose
    nmap=r.i32(); out['namemap']=[(r.i32(),r.i32(),r.i32()) for _ in range(nmap)]
    out['refskel_end']=r.p
    out['bCooked']=r.i32()
    out['lod_array_start']=r.p
    nlod=r.i32(); out['nlod']=nlod; lods=[]
    for li in range(nlod):
        if v423:
            L=_lod423(r,uexp,out); lods.append(L)
            if not all_lods: break
            continue
        L={}
        if _dbg is not None: _dbg['L']=L; _dbg['r']=r
        L['start']=r.p
        L['strip']=(r.u8(),r.u8())
        L['cooked_out']=r.i32(); L['inlined']=r.i32()
        n=r.i32(); L['required_bones']=struct.unpack_from('<%dh'%n,uexp,r.p); r.p+=2*n
        ns=r.i32(); secs=[]
        for _ in range(ns):
            S={}
            S['start']=r.p
            S['strip']=(r.u8(),r.u8())
            S['mat']=struct.unpack_from('<h',uexp,r.p)[0]; r.p+=2
            S['base_index']=r.i32(); S['ntri']=r.i32()
            S['recompute_tangent']=r.i32()
            if rtmask: S['rt_mask']=r.u8()
            S['cast_shadow']=r.i32()
            if ue5: S['vis_rt']=r.i32()                    # UE5: bVisibleInRayTracing
            S['base_vertex']=r.u32()
            nc=r.i32(); S['cloth']=nc; r.p+=nc*0  # expect 0
            assert nc==0, 'cloth mapping data present'
            n=r.i32(); S['bonemap']=struct.unpack_from('<%dH'%n,uexp,r.p); r.p+=2*n
            S['nverts']=r.i32(); S['maxinf']=r.i32()
            S['cloth_asset_idx']=struct.unpack_from('<h',uexp,r.p)[0]; r.p+=2
            # FClothingSectionData: GUID 16 + int32 AssetLodIndex
            S['clothing_guid']=r.guid(); S['clothing_lod']=r.i32()
            # DuplicatedVerticesBuffer (if not stripped class flag 1)
            S['dup_pos']=r.p
            if not (S['strip'][1] & 1):
                # TArray<int32> DupVertData ; TArray<FIndexLengthPair> DupVertIndexData  (fixed arrays with element size prefix)
                n1=r.i32(); r.p+=n1*4
                n2=r.i32(); r.p+=n2*8
                S['dup']=(n1,n2)
            S['disabled']=r.i32()
            S['end']=r.p
            secs.append(S)
        L['sections']=secs
        n=r.i32(); L['active_bones']=struct.unpack_from('<%dh'%n,uexp,r.p); r.p+=2*n
        L['buffers_size']=r.u32()
        L['stream_start']=r.p
        L['stream_strip']=(r.u8(),r.u8())
        # indices
        L['idx_datasize']=r.u8()
        L['idx']=bulk(r)
        # position
        L['pos_stride']=r.i32(); L['pos_n']=r.i32()
        L['pos']=bulk(r)
        # static mesh vertex buffer
        L['smvb_strip']=(r.u8(),r.u8())
        L['ntex']=r.i32(); L['smvb_n']=r.i32(); L['fullUV']=r.i32(); L['hiTan']=r.i32()
        L['tan']=bulk(r); L['uv']=bulk(r)
        # skin weights
        L['sw_strip']=(r.u8(),r.u8())
        if v423:
            L['sw_extra']=r.i32(); L['sw_nverts']=r.i32(); L['sw_varbones']=0; L['sw_maxinf']=8 if L['sw_extra'] else 4; L['sw_numbones']=L['sw_nverts']*L['sw_maxinf']; L['sw_16bit']=0
            L['sw']=bulk(r)
            L['lk_strip']=(0,0); L['lk_n']=0; L['lk']=dict(start=r.p,end=r.p,isz=4,cnt=0)
        else:
            L['sw_varbones']=r.i32(); L['sw_maxinf']=r.i32(); L['sw_numbones']=r.i32(); L['sw_nverts']=r.i32()
            L['sw_16bit']=r.i32()
            L['sw']=bulk(r)
            L['lk_strip']=(r.u8(),r.u8())
            L['lk_n']=r.i32()
            L['lk']=bulk(r)
        L['after_skin']=r.p
        if ue5:
            # UE5.1: whatever follows the skin weights up to the end of the streamed block (colour, adjacency, cloth, profiles) is empty on the meshes
            # seen so far; its size comes from the LOD's own BuffersSize, so it is kept as an opaque block that must be all zero
            end=L['stream_start']+L['buffers_size']; tail=uexp[r.p:end]
            assert end>=r.p, 'UE5 mesh: the streamed block ends before the skin weights do'
            L['ue5_extra']=bool(any(tail))                 # vertex colours / morph buffers / adjacency / profiles: fine to skip over (hide), not fine to rewrite (swap)
            L['col_strip']=(0,0); L['col_stride']=0; L['col_n']=0; L['col']=None; L['adj_datasize']=None
            L['adj']=dict(start=end,end=end,isz=0,cnt=0); L['profiles']=0; L['ue5_tail']=len(tail); L['after_color']=L['after_adj']=r.p=end; L['lod_end']=end
            lods.append(L)
            if not all_lods: break
            continue
        # color vertex buffer (bHasVertexColors)
        if out['has_col']:
            L['col_strip']=(r.u8(),r.u8()); L['col_stride']=r.i32(); L['col_n']=r.i32()
            L['col']=bulk(r) if L['col_n']>0 else None
        else: L['col_strip']=(0,0); L['col_stride']=0; L['col_n']=0; L['col']=None
        L['after_color']=r.p
        # adjacency index buffer
        if (adj is False) or (adj is None and L['stream_strip'][1] & 1): L['adj_datasize']=None; L['adj']=dict(start=r.p,end=r.p,isz=0,cnt=0)   # class data (adjacency) stripped
        else: L['adj_datasize']=r.u8(); L['adj']=bulk(r)
        L['after_adj']=r.p
        # skin weight profiles TMap
        L['profiles']=0 if v423 else r.i32()
        if (False if v423 else (rtmask if trail is None else trail)): L['trail']=r.i32()      # UE4.26+: extra int32 per LOD (morph target buffer info, 0 here)
        L['lod_end']=r.p
        lods.append(L)
        if not all_lods: break
    out['lods']=lods
    out['end']=r.p
    return out
