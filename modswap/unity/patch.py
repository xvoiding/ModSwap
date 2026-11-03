"""Replace Unity Mesh and Texture2D objects in a serialized file (sharedassetsN.assets, levelN, resources.assets ...).

Mesh layout written: one interleaved vertex stream, float32:  position(3) normal(3) uv0(2) tangent(4), uint16 indices, single submesh.
Works for meshes that are stored uncompressed (m_MeshCompression == 0), which is the Unity 5.x default for imported models.
"""
import numpy as np


def _aabb(pos):
    lo, hi = pos.min(0), pos.max(0)
    c, e = (lo + hi) / 2, (hi - lo) / 2
    return {'m_Center': {'x': float(c[0]), 'y': float(c[1]), 'z': float(c[2])}, 'm_Extent': {'x': float(e[0]), 'y': float(e[1]), 'z': float(e[2])}}


def _tangents(pos, nrm, uv, tris):
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = pos[b] - pos[a], pos[c] - pos[a]; d1, d2 = uv[b] - uv[a], uv[c] - uv[a]
    den = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]; den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    tT = (e1 * d2[:, [1]] - e2 * d1[:, [1]]) / den[:, None]
    acc = np.zeros_like(pos)
    for k in range(3): np.add.at(acc, tris[:, k], tT)
    T = acc - nrm * (acc * nrm).sum(1, keepdims=True)
    bad = np.linalg.norm(T, axis=1) < 1e-9
    T[bad] = np.cross(nrm[bad], [0.0, 1.0, 0.0]) + 1e-9
    return T / np.linalg.norm(T, axis=1, keepdims=True)


def set_mesh(obj, pos, nrm, uv, tris, n_sub=1, skin=None):
    """obj: UnityPy ObjectReader of a Mesh. pos/nrm (N,3), uv (N,2) with v UP (Unity), tris (M,3) clockwise-from-outside (Unity).
    skin=(bone_index (N,4), weight (N,4)) makes it a skinned mesh: the mesh keeps its bind poses and gets these weights."""
    t = obj.read_typetree()
    if t.get('m_MeshCompression', 0) != 0: raise ValueError('mesh is compressed')
    pos = np.asarray(pos, np.float32); nrm = np.asarray(nrm, np.float32); uv = np.asarray(uv, np.float32); tris = np.asarray(tris, np.int64)
    n = len(pos)
    if n > 65000: raise ValueError('too many vertices for a 16-bit mesh (%d)' % n)
    tan = _tangents(pos.astype(np.float64), nrm.astype(np.float64), uv.astype(np.float64), tris).astype(np.float32)
    data = np.concatenate([pos, nrm, uv, tan, np.ones((n, 1), np.float32)], axis=1).astype('<f4')      # 3+3+2+3+1 = 12 floats = 48 bytes
    vd = t['m_VertexData']
    vd['m_VertexCount'] = n
    if 'm_CurrentChannels' in vd: vd['m_CurrentChannels'] = (1 << 0) | (1 << 1) | (1 << 3) | (1 << 7)
    ch = vd['m_Channels']
    for i in range(len(ch)): ch[i].update(stream=0, offset=0, format=0, dimension=0)
    ch[0].update(offset=0, dimension=3); ch[1].update(offset=12, dimension=3); ch[3].update(offset=24, dimension=2)
    if len(ch) > 7: ch[7].update(offset=32, dimension=4)
    key = 'm_DataSize' if 'm_DataSize' in vd else '_typelessdata'
    vd[key] = data.tobytes()
    idx = tris.astype('<u2').ravel()
    t['m_IndexBuffer'] = list(idx.tobytes()) if isinstance(t['m_IndexBuffer'], list) else idx.tobytes()
    box = _aabb(pos)
    old = t['m_SubMeshes'][0] if t.get('m_SubMeshes') else {}
    sub = {k: v for k, v in old.items()}
    sub.update(firstByte=0, indexCount=int(idx.size), topology=0, firstVertex=0, vertexCount=n, localAABB=box)
    if 'baseVertex' in sub: sub['baseVertex'] = 0
    empty = dict(sub); empty.update(indexCount=0, vertexCount=0)
    t['m_SubMeshes'] = [sub] + [dict(empty) for _ in range(max(0, n_sub - 1))]
    if 'm_IndexFormat' in t: t['m_IndexFormat'] = 0
    if isinstance(t.get('m_StreamData'), dict): t['m_StreamData'].update(offset=0, size=0, path='')
    t['m_LocalAABB'] = box
    t['m_BakedConvexCollisionMesh'] = []; t['m_BakedTriangleCollisionMesh'] = []
    if skin is None:
        t['m_Skin'] = []; t['m_BindPose'] = []; t['m_BoneNameHashes'] = []
    else:
        bi, bw = np.asarray(skin[0], np.int64), np.asarray(skin[1], np.float64)
        bw = bw / np.maximum(bw.sum(1, keepdims=True), 1e-9)
        sample = (t.get('m_Skin') or [None])[0]
        if sample is not None and 'weight' in sample:
            t['m_Skin'] = [dict(weight=[float(x) for x in bw[i]], boneIndex=[int(x) for x in bi[i]]) for i in range(n)]
        else:
            t['m_Skin'] = [{**{'weight[%d]' % k: float(bw[i, k]) for k in range(4)}, **{'boneIndex[%d]' % k: int(bi[i, k]) for k in range(4)}} for i in range(n)]
    if isinstance(t.get('m_Shapes'), dict):
        t['m_Shapes'] = {k: [] for k in t['m_Shapes']}                     # blend shapes would no longer match the new vertices
    t['m_IsReadable'] = True
    obj.save_typetree(t)


def to_unity_tris(pos, tris):
    """Flip winding if the triangles currently face inwards (cross product of the edges should point away from the centre)."""
    a, b, c = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    nrm = np.cross(b - a, c - a); cen = (a + b + c) / 3 - pos.mean(0)
    out = (nrm * cen).sum(1)
    return tris[:, [0, 2, 1]] if (out > 0).mean() < 0.5 else tris


def tiny_mesh(obj, size=0.03, uv=(0.5, 0.5), n_sub=1):
    """Replace a mesh with a tiny cube (keeps a valid mesh for renderers / MeshColliders that still reference it)."""
    s = size
    P = np.array([[x, y, z] for x in (-s, s) for y in (-s, s) for z in (-s, s)], np.float32)
    F = [(0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6), (0, 1, 5), (0, 5, 4), (2, 6, 7), (2, 7, 3), (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5)]
    tris = to_unity_tris(P, np.array(F, np.int64))
    N = P / np.linalg.norm(P, axis=1, keepdims=True)
    set_mesh(obj, P, N, np.tile(np.array(uv, np.float32), (8, 1)), tris, n_sub)


def set_texture(obj, image, fmt='DXT1'):
    """image: PIL image (top-left origin). Replaces the Texture2D pixels (and size) in place."""
    from UnityPy.enums import TextureFormat
    tex = obj.read()
    try:
        tex.m_TextureFormat = getattr(TextureFormat, fmt)
        tex.image = image.convert('RGB' if fmt in ('DXT1', 'RGB24') else 'RGBA')
    except Exception:
        if fmt == 'RGB24': raise                      # the DXT compressor (etcpak) could not load on this machine: store the texture uncompressed instead (bigger, same look)
        tex = obj.read(); tex.m_TextureFormat = TextureFormat.RGB24; tex.image = image.convert('RGB')
    tex.save()


def empty_mesh(obj):
    """keep the mesh valid (bones, bind poses, vertices) but give it no triangles, so it draws nothing"""
    t = obj.read_typetree()
    t['m_IndexBuffer'] = [] if isinstance(t['m_IndexBuffer'], list) else b''
    for sm in t.get('m_SubMeshes') or []: sm['indexCount'] = 0
    obj.save_typetree(t)
