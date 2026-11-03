import sys, struct, numpy as np
from .uepkg import R, parse_uasset
from .skmesh import walk, skip_tagged_props

def i32(x): return struct.pack('<i',x)
def u32(x): return struct.pack('<I',x)
def bulk(isz,data,cnt=None):
    if cnt is None: cnt=len(data)//isz
    assert len(data)==isz*cnt
    return i32(isz)+i32(cnt)+bytes(data)

class Orig:
    """parsed original SK_Wally"""
    def __init__(s, base, exp_idx=1, rtmask=False, adj=None, trail=None, v423=False, ue5=False):
        s.base=base; s.exp_idx=exp_idx; s.rtmask=rtmask; s.adj_on=adj; s.v423=v423; s.ue5=ue5; s.trail_on=(False if v423 else (rtmask if trail is None else trail))
        s.ua=open(base+'.uasset','rb').read(); s.u=open(base+'.uexp','rb').read()
        s.d=parse_uasset(s.ua); s.o=walk(s.u,s.d,exp_idx=exp_idx,verbose=False,rtmask=rtmask,all_lods=True,adj=adj,trail=trail,v423=v423,ue5=ue5); s.L=s.o['lods'][0]
        L=s.L; u=s.u
        s.idx=u[L['idx']['start']:L['idx']['end']]
        s.pos=u[L['pos']['start']:L['pos']['end']]
        s.tan=u[L['tan']['start']:L['tan']['end']]
        s.uv=u[L['uv']['start']:L['uv']['end']]
        s.skin=u[L['sw']['start']:L['sw']['end']]
        s.has_col=s.o['has_col']
        s.col=u[L['col']['start']:L['col']['end']] if L['col'] else b''
        s.adj=u[L['adj']['start']:L['adj']['end']]
        s.ntex=L.get('ntex',1)
        s.N=L['pos_n']; s.T=L['sections'][0]['ntri']
        S0=L['sections'][0]
        s.sec=S0
        s.exp1_size=s.d['exports'][0]['size']
        s.mesh_start=s.d['exports'][exp_idx]['offset']-s.d['total_header']
        s.bonemap=list(S0['bonemap'])

def build_morph(orig, new_nverts):
    u=orig.u; d=orig.d
    r=R(u,0); skip_tagged_props(r,d); props_end=r.p
    head=u[:props_end]+u[props_end:props_end+4]+u[props_end+4:props_end+6]   # props + guidbool + strip flags
    out=bytearray(head)
    out+=i32(1)                    # MorphLODModels count
    out+=i32(0)                    # Vertices: none
    out+=i32(new_nverts)           # NumBaseMeshVerts
    out+=i32(1)+i32(0)             # SectionIndices [0]
    out+=i32(0)                    # bGeneratedByEngine
    return bytes(out)


def build_lod423(orig, pos, tanbytes, uvbytes, skinbytes, colbytes, idxbytes, N, T, adjbytes=None, bonemap=None, required=None):
    """UE4.23 LOD: [strip][sections][index buffer][active bones][required bones][positions][tangents+UVs][skin weights][(colour)][adjacency?]"""
    u=orig.u; L=orig.L; S0=orig.sec
    bm=list(bonemap) if bonemap is not None else orig.bonemap
    out=bytearray()
    out+=bytes([L['strip'][0], L['strip'][1] if adjbytes is not None else (L['strip'][1] | 1)])     # class flag 1 = adjacency data stripped
    out+=i32(1)
    sec=bytearray()
    sec+=u[S0['start']:S0['start']+4]                       # strip flags, material index
    sec+=i32(0)+i32(T)
    sec+=u[S0['start']+12:S0['start']+20]                   # bRecomputeTangent, bCastShadow
    sec+=u32(0)+i32(0)                                      # base vertex, cloth mapping count
    sec+=i32(len(bm))+struct.pack('<%dH'%len(bm),*bm)
    sec+=i32(N)+i32(4)
    sec+=u[S0['dup_pos']-22:S0['dup_pos']]                  # cloth asset index + clothing section data
    if not (S0['strip'][1] & 1):
        sec+=i32(1)+i32(0)                                  # one dummy duplicated-vertex entry (an empty array makes a 0-byte D3D buffer => crash)
        sec+=i32(N)+b'\x00'*(8*N)
    sec+=u[S0['end']-4:S0['end']]                           # bDisabled
    out+=sec
    out+=bytes([2])+bulk(2,idxbytes,cnt=3*T)
    ab=sorted(bm) if bonemap is not None else list(L['active_bones'])
    out+=i32(len(ab))+struct.pack('<%dh'%len(ab),*ab)
    rq=sorted(required) if required is not None else list(L['required_bones'])
    out+=i32(len(rq))+struct.pack('<%dh'%len(rq),*rq)
    out+=i32(12)+i32(N)+bulk(12,pos,cnt=N)
    out+=bytes([L['smvb_strip'][0],L['smvb_strip'][1]])+i32(1)+i32(N)+i32(0)+i32(0)
    out+=bulk(8,tanbytes,cnt=N)+bulk(4,uvbytes,cnt=N)
    out+=bytes([L['sw_strip'][0],L['sw_strip'][1]])+i32(0)+i32(N)+bulk(1,skinbytes,cnt=N*8)
    if orig.has_col: out+=bytes([L['col_strip'][0],L['col_strip'][1]])+i32(4)+i32(N)+bulk(4,colbytes,cnt=N)
    if adjbytes is not None: out+=bytes([2])+bulk(2,adjbytes)
    return bytes(out)


def build_lod51(orig, pos, tanbytes, uvbytes, skinbytes, idxbytes, N, T, bonemap=None, required=None):
    """UE5.1 LOD (verified on a real Sparking Zero body mesh): [strip,cookedout,inlined,required bones][1 section][active bones][BuffersSize]
    [stream strip][index buffer][positions][tangents + UVs][skin weights][lookup buffer][empty tail kept as in the original]. A section has the
    extra bVisibleInRayTracing flag. The UV set is written as many times as the original has channels."""
    u=orig.u; L=orig.L; S0=orig.sec; nt=max(1,L['ntex'])
    out=bytearray()
    if required is None: out+=u[L['start']:S0['start']-4]                           # strip, cookedout, inlined, required bones
    else: out+=u[L['start']:L['start']+10]+i32(len(required))+struct.pack('<%dh'%len(required),*required)
    out+=i32(1)
    sec=bytearray()
    sec+=u[S0['start']:S0['start']+4]                                              # strip flags, material index
    sec+=i32(0)+i32(T)
    sec+=u[S0['start']+12:S0['start']+12+4+1+4+4]                                  # bRecomputeTangent, tangent mask channel, bCastShadow, bVisibleInRayTracing
    sec+=u32(0)+i32(0)                                                             # base vertex, cloth mapping count
    bm=list(bonemap) if bonemap is not None else orig.bonemap
    sec+=i32(len(bm))+struct.pack('<%dH'%len(bm),*bm)
    sec+=i32(N)+i32(4)
    sec+=u[S0['dup_pos']-22:S0['dup_pos']]                                          # cloth asset index + clothing section data
    sec+=i32(1)+i32(0)                                                             # one dummy duplicated-vertex entry (an empty array makes a 0-byte D3D buffer)
    sec+=i32(N)+b'\x00'*(8*N)
    sec+=u[S0['end']-4:S0['end']]                                                  # bDisabled
    out+=sec
    if bonemap is not None: ab=sorted(bm); out+=i32(len(ab))+struct.pack('<%dh'%len(ab),*ab)
    else:
        ab_start=L['sections'][-1]['end']; nab=struct.unpack_from('<i',u,ab_start)[0]; out+=u[ab_start:ab_start+4+2*nab]   # active bones follow the last section
    st=bytearray()
    st+=bytes([L['stream_strip'][0],L['stream_strip'][1]])
    st+=bytes([2])+bulk(2,idxbytes,cnt=3*T)
    st+=i32(12)+i32(N)+bulk(12,pos,cnt=N)
    st+=bytes([L['smvb_strip'][0],L['smvb_strip'][1]])+i32(nt)+i32(N)+i32(0)+i32(0)
    st+=bulk(8,tanbytes,cnt=N)+bulk(4,bytes(uvbytes)*nt,cnt=N*nt)
    st+=bytes([L['sw_strip'][0],L['sw_strip'][1]])+i32(0)+i32(4)+i32(N*4)+i32(N)+i32(0)
    st+=bulk(1,skinbytes,cnt=N*8)
    st+=bytes([L['lk_strip'][0],L['lk_strip'][1]])+i32(0)+bulk(4,b'',cnt=0)
    # the tail after the skin weights: all zero on plain meshes (12 bytes). Meshes that carry vertex colours or face-morph batches keep those per
    # original vertex, which the new mesh does not have, so they are dropped and the plain empty tail is written instead (shape is unchanged, the
    # new body just has no baked colours / morphs).
    st+=u[L['after_skin']:L['lod_end']] if not L.get('ue5_extra') else b'\x00'*12
    out+=u32(len(st))+st                                                           # BuffersSize = bytes of the streamed block that follow it
    return bytes(out)

def build_lod(orig, pos, tanbytes, uvbytes, skinbytes, colbytes, idxbytes, N, T, adjbytes=None, bonemap=None, required=None):
    """returns bytes for LOD0 element (from LOD start to lod_end)"""
    if orig.ue5: return build_lod51(orig,pos,tanbytes,uvbytes,skinbytes,idxbytes,N,T,bonemap,required)
    if orig.v423: return build_lod423(orig,pos,tanbytes,uvbytes,skinbytes,colbytes,idxbytes,N,T,adjbytes,bonemap,required)
    u=orig.u; L=orig.L; S0=orig.sec
    out=bytearray()
    if required is None:
        out+=u[L['start']:S0['start']-4]       # strip, cookedout, inlined, required bones
    else:
        out+=u[L['start']:L['start']+10]+i32(len(required))+struct.pack('<%dh'%len(required),*required)
    out+=i32(1)                                # number of sections
    # section
    sec=bytearray()
    sec+=u[S0['start']:S0['start']+2]           # strip flags
    sec+=u[S0['start']+2:S0['start']+4]         # material index (int16)
    sec+=i32(0)+i32(T)                          # base index, num triangles
    # recompute tangent bool + cast shadow bool + base vertex (copy orig bytes then patch)
    o_=S0['start']+4+8
    sec+=u[o_:o_+4]                             # bRecomputeTangent
    if orig.rtmask:
        sec+=u[o_+4:o_+5]; o_+=1                # RecomputeTangentsVertexMaskChannel (UE4.26+)
    sec+=u[o_+4:o_+8]                           # bCastShadow
    sec+=u32(0)                                 # base vertex index
    sec+=i32(0)                                 # cloth mapping count
    bm=list(bonemap) if bonemap is not None else orig.bonemap
    sec+=i32(len(bm))+struct.pack('<%dH'%len(bm),*bm)
    sec+=i32(N)+i32(4)                          # NumVertices, MaxBoneInfluences
    cl=S0['dup_pos']-20-2                        # cloth asset idx (int16) + clothing section data (20)
    sec+=u[cl:S0['dup_pos']]
    # duplicated vertices buffer: none
    if adjbytes is not None and 'dup_keep' in orig.__dict__:
        pass
    sec+=i32(1)+i32(0)                           # TArray<int32> DuplicatedVerticesIndices: one dummy entry (empty array => 0-byte D3D buffer => crash)
    sec+=i32(N)+b'\x00'*(8*N)                    # per-vertex {index,length} = 0
    sec+=u[S0['end']-4:S0['end']]               # bDisabled
    out+=sec
    # active bones
    if bonemap is not None:
        ab=sorted(bm); out+=i32(len(ab))+struct.pack('<%dh'%len(ab),*ab)
    else:
        ab_start=L['sections'][-1]['end']; nab=struct.unpack_from('<i',u,ab_start)[0]    # active bones follow the LAST section
        out+=u[ab_start:ab_start+4+2*nab]
    # streamed buffers
    st=bytearray()
    strip_class=(L['stream_strip'][1] if orig.adj_on is False else (0 if adjbytes is not None else 1))     # cooks without an adjacency buffer keep their own flag
    st+=bytes([L['stream_strip'][0],strip_class])
    st+=bytes([2])+bulk(2,idxbytes,cnt=3*T)
    st+=i32(12)+i32(N)+bulk(12,pos,cnt=N)
    st+=bytes(u[L['stream_start']+2+1+8+len(orig.idx)+8+ (0):0]) if False else b''
    st+=bytes([L['smvb_strip'][0],L['smvb_strip'][1]])+i32(1)+i32(N)+i32(0)+i32(0)
    st+=bulk(8,tanbytes,cnt=N)+bulk(4,uvbytes,cnt=N)
    if orig.v423:                                # UE4.23: [strip][bExtraBoneInfluences=0 (4 per vertex)][NumVertices][weights]; no lookup buffer
        st+=bytes([L['sw_strip'][0],L['sw_strip'][1]])+i32(0)+i32(N)
        st+=bulk(1,skinbytes,cnt=N*8)
    else:
        st+=bytes([L['sw_strip'][0],L['sw_strip'][1]])+i32(0)+i32(4)+i32(N*4)+i32(N)+i32(0)
        st+=bulk(1,skinbytes,cnt=N*8)
        st+=bytes([L['lk_strip'][0],L['lk_strip'][1]])+i32(0)+bulk(4,b'',cnt=0)
    if orig.has_col: st+=bytes([L['col_strip'][0],L['col_strip'][1]])+i32(4)+i32(N)+bulk(4,colbytes,cnt=N)
    if adjbytes is not None:
        st+=bytes([2])+bulk(2,adjbytes)
    if not orig.v423: st+=i32(0)                 # skin weight profiles (UE4.24+)
    if orig.trail_on: st+=i32(0)                 # UE4.26+: per-LOD trailing int32 (not in every cook)
    out+=u32(len(st)+4)                          # BuffersSize
    out+=st
    return bytes(out)

def assemble(orig, lodbytes, new_nverts, morph=None):
    u=orig.u
    morph_b = morph if morph is not None else u[:orig.exp1_size]
    mesh_prefix=u[orig.mesh_start:orig.L['start']]
    mesh_tail=u[orig.L['lod_end']:]
    uexp=morph_b+mesh_prefix+lodbytes+mesh_tail
    size1=len(morph_b); size2=len(uexp)-4-size1
    ua=bytearray(orig.ua); d=orig.d
    hdr=d['total_header']
    e1,e2=d['exports']
    struct.pack_into('<q',ua,e1['_size_pos'],size1); struct.pack_into('<q',ua,e1['_size_pos']+8,hdr)
    struct.pack_into('<q',ua,e2['_size_pos'],size2); struct.pack_into('<q',ua,e2['_size_pos']+8,hdr+size1)
    bpos=ua.find(struct.pack('<q',d['bulk_start'])); assert bpos==169
    struct.pack_into('<q',ua,bpos,hdr+size1+size2)
    return bytes(ua), uexp


def assemble_single(orig, lodblobs):
    """Packages whose only export is the SkeletalMesh (UE4.26+ cooks). lodblobs: one bytes object per LOD."""
    u=orig.u; L0=orig.o['lods'][0]; Ln=orig.o['lods'][-1]
    uexp=u[:L0['start']]+b''.join(lodblobs)+u[Ln['lod_end']:]
    ua=bytearray(orig.ua); d=orig.d; hdr=d['total_header']; e=d['exports'][orig.exp_idx]
    struct.pack_into('<q',ua,e['_size_pos'],len(uexp)-4)
    bpos=ua.find(struct.pack('<q',d['bulk_start'])); assert bpos>0
    struct.pack_into('<q',ua,bpos,hdr+len(uexp)-4)
    return bytes(ua), uexp


def _morph_at(orig, i, new_nverts):
    u=orig.u; d=orig.d; e=d['exports'][i]; base=e['offset']-d['total_header']
    r=R(u,base); skip_tagged_props(r,d); props_end=r.p
    return u[base:props_end+6]+i32(1)+i32(0)+i32(new_nverts)+i32(1)+i32(0)+i32(0)

def assemble_auto(orig, lodblobs, new_nverts):
    """Any package layout. -> (uasset, uexp, position of the mesh export's start in the uexp). Other exports are kept; morph targets are emptied
    (their vertex deltas point at the old mesh's vertices)."""
    u=orig.u; d=orig.d; hdr=d['total_header']; ex=d['exports']
    if len(ex)==1:
        ua,ue=assemble_single(orig,lodblobs); return ua,ue,0
    if not orig.v423 and not orig.ue5:
        morph=build_morph(orig,new_nverts); ua,ue=assemble(orig,lodblobs[0],new_nverts,morph=morph); return ua,ue,len(morph)
    N=d['names']; nm=lambda x: N[x[0]] if isinstance(x,tuple) else x
    L0=orig.o['lods'][0]; Ln=orig.o['lods'][-1]
    for a,b in zip(ex,ex[1:]): assert a['offset']+a['size']==b['offset'], 'exports are not contiguous'
    segs=[]; mesh_at=0; pos=0
    for i,e in enumerate(ex):
        base=e['offset']-hdr
        if i==orig.exp_idx: seg=u[base:L0['start']]+b''.join(lodblobs)+u[Ln['lod_end']:base+e['size']]; mesh_at=pos
        else:
            c=e.get('class',0); cn=nm(d['imports'][-c-1]['name']) if c<0 and -c-1<len(d['imports']) else ''
            seg=_morph_at(orig,i,new_nverts) if (cn=='MorphTarget' and not orig.ue5) else u[base:base+e['size']]
        segs.append(seg); pos+=len(seg)
    uexp=b''.join(segs)+u[-4:]
    ua=bytearray(orig.ua); cur=hdr
    for e,seg in zip(ex,segs):
        struct.pack_into('<q',ua,e['_size_pos'],len(seg)); struct.pack_into('<q',ua,e['_size_pos']+8,cur); cur+=len(seg)
    bpos=ua.find(struct.pack('<q',d['bulk_start'])); assert bpos>0
    struct.pack_into('<q',ua,bpos,hdr+len(uexp)-4)
    return bytes(ua), uexp, mesh_at
