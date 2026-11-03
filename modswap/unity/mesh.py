"""Read a Unity Mesh object into plain arrays (positions + triangles), for the layouts Unity writes uncompressed."""
import numpy as np

FMT_SIZE = {0: 4, 1: 2, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 1, 8: 2, 9: 2, 10: 4, 11: 4}
FMT_DT = {0: '<f4', 1: '<f2'}


def _raw(x):
    return bytes(x) if not isinstance(x, (bytes, bytearray)) else bytes(x)


def read_geometry(obj):
    """-> (pos (N,3) float32, tris (M,3) int64). Raises ValueError for meshes this reader cannot decode."""
    t = obj.read_typetree()
    if t.get('m_MeshCompression', 0) not in (0, None): return _read_compressed(obj)
    vd = t['m_VertexData']; n = int(vd['m_VertexCount'])
    data = _raw(vd.get('m_DataSize', vd.get('_typelessdata', b'')))
    ch = vd.get('m_Channels') or []
    if not ch or n == 0: raise ValueError('empty mesh')
    # stream strides + start offsets (streams are stored one after another, each padded to 16 bytes)
    strides = {}
    for c in ch:
        d = int(c['dimension']) & 0xF
        if d: strides[c['stream']] = max(strides.get(c['stream'], 0), int(c['offset']) + d * FMT_SIZE.get(int(c['format']), 4))
    starts = {}; cur = 0
    for s in sorted(strides):
        starts[s] = cur; cur += strides[s] * n; cur = (cur + 15) // 16 * 16
    p = ch[0]; fmt = int(p['format']); dim = int(p['dimension']) & 0xF
    if dim < 3 or fmt not in FMT_DT: raise ValueError('unsupported position format')
    base = starts[p['stream']] + int(p['offset'])
    arr = np.ndarray((n, 3), dtype=FMT_DT[fmt], buffer=data, offset=base, strides=(strides[p['stream']], FMT_SIZE[fmt]))
    pos = np.array(arr, np.float32)
    ib = _raw(t['m_IndexBuffer']); wide = int(t.get('m_IndexFormat', 0) or 0) == 1
    idx = np.frombuffer(ib, '<u4' if wide else '<u2').astype(np.int64); isz = 4 if wide else 2
    tris = []
    for sm in t['m_SubMeshes']:
        if int(sm.get('topology', 0)) != 0 or int(sm['indexCount']) == 0: continue
        a = int(sm['firstByte']) // isz; part = idx[a:a + int(sm['indexCount'])] + int(sm.get('baseVertex', 0) or 0)
        tris.append(part.reshape(-1, 3))
    if not tris: raise ValueError('no triangles')
    return pos, np.concatenate(tris)


def bounds(obj):
    """cheap: (center, extent) arrays from the stored AABB"""
    t = obj.read_typetree(); b = t['m_LocalAABB']
    c = np.array([b['m_Center'][k] for k in 'xyz']); e = np.array([b['m_Extent'][k] for k in 'xyz'])
    return t['m_Name'], int(t['m_VertexData']['m_VertexCount']), c, e, int(t.get('m_MeshCompression', 0) or 0)


def _read_compressed(obj):
    """compressed meshes: let UnityPy decode them"""
    try:
        from UnityPy.helpers.MeshHelper import MeshHandler
        h = MeshHandler(obj.read()); h.process()
        pos = np.asarray(h.m_Vertices, np.float32).reshape(-1, 3)
        tris = np.asarray([tuple(t) for sm in h.get_triangles() for t in sm], np.int64).reshape(-1, 3)
    except Exception as e: raise ValueError('compressed mesh (%s)' % e)
    if not len(pos) or not len(tris): raise ValueError('empty mesh')
    return pos, tris
