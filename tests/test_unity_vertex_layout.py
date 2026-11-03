"""set_mesh writes the vertex data in the layout of the game's Unity version: 8 channels (<= 2017: uv0 is channel 3, tangent 7) or 14 (2018+: tangent 2, uv0 4, weights 12, bone indices 13).
Before, a 2018+ game (Megabonk) got its uvs in the colour channel: every vertex sampled one texel and a custom texture never showed."""
import os, sys, copy
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.unity import patch, mesh as umesh


class Obj:
    def __init__(self, t): self.t = t
    def read_typetree(self): return copy.deepcopy(self.t)
    def save_typetree(self, t): self.t = t


def tree(n_channels, skin_channels=False):
    ch = [dict(stream=0, offset=0, format=0, dimension=0) for _ in range(n_channels)]
    if skin_channels: ch[12].update(stream=1, offset=0, format=0, dimension=4); ch[13].update(stream=1, offset=16, format=11, dimension=4)
    return dict(m_Name='x', m_MeshCompression=0, m_VertexData=dict(m_VertexCount=3, m_Channels=ch, m_DataSize=b''), m_IndexBuffer=b'', m_SubMeshes=[dict(firstByte=0, indexCount=3, topology=0, baseVertex=0, firstVertex=0, vertexCount=3, localAABB={})],
                m_LocalAABB={}, m_IndexFormat=0, m_Skin=[], m_BindPose=[], m_BoneNameHashes=[], m_Shapes={}, m_StreamData=dict(offset=0, size=0, path=''), m_BakedConvexCollisionMesh=[], m_BakedTriangleCollisionMesh=[])


def channel(t, c, n):
    """what the GPU would read for channel c: (n, dimension) array, following the channel table like Unity does"""
    vd = t['m_VertexData']; ch = vd['m_Channels']; data = vd['m_DataSize']; dim = ch[c]['dimension'] & 0xF
    strides = {}
    for q in ch:
        d = q['dimension'] & 0xF
        if d: strides[q['stream']] = max(strides.get(q['stream'], 0), q['offset'] + d * 4)
    starts = {}; cur = 0
    for s in sorted(strides): starts[s] = cur; cur += strides[s] * n; cur = (cur + 15) // 16 * 16
    dt = '<i4' if ch[c]['format'] == 11 else '<f4'
    return np.ndarray((n, dim), dt, buffer=data, offset=starts[ch[c]['stream']] + ch[c]['offset'], strides=(strides[ch[c]['stream']], 4)).copy()


POS = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], np.float32); NRM = np.array([[0, 0, 1]] * 3, np.float32); UV = np.array([[0.1, 0.2], [0.9, 0.2], [0.1, 0.8]], np.float32); TRI = np.array([[0, 1, 2]])


def test_old_layout_uv_is_channel_3_and_tangent_channel_7():
    o = Obj(tree(8)); patch.set_mesh(o, POS, NRM, UV, TRI)
    assert np.allclose(channel(o.t, 0, 3), POS) and np.allclose(channel(o.t, 1, 3), NRM) and np.allclose(channel(o.t, 3, 3), UV) and channel(o.t, 7, 3).shape == (3, 4)
    assert np.allclose(umesh.read_geometry(o)[0], POS)


def test_modern_layout_uv_is_channel_4_and_tangent_channel_2():
    o = Obj(tree(14)); patch.set_mesh(o, POS, NRM, UV, TRI)
    assert np.allclose(channel(o.t, 0, 3), POS) and np.allclose(channel(o.t, 1, 3), NRM) and np.allclose(channel(o.t, 4, 3), UV), 'uv0 must be channel 4'
    assert channel(o.t, 2, 3).shape == (3, 4) and np.allclose(np.linalg.norm(channel(o.t, 2, 3)[:, :3], axis=1), 1, atol=1e-4) and channel(o.t, 3, 3).size == 0      # tangent in 2, no colour channel
    assert np.allclose(umesh.read_geometry(o)[0], POS) and o.t['m_Skin'] == []


def test_modern_skinned_mesh_keeps_weights_and_bone_indices_in_the_vertex_data():
    o = Obj(tree(14, skin_channels=True)); bi = np.array([[0, 1, 0, 0], [2, 0, 0, 0], [1, 2, 0, 0]]); bw = np.array([[.7, .3, 0, 0], [1, 0, 0, 0], [.5, .5, 0, 0]])
    patch.set_mesh(o, POS, NRM, UV, TRI, skin=(bi, bw))
    assert np.allclose(channel(o.t, 4, 3), UV) and np.allclose(channel(o.t, 12, 3), bw, atol=1e-6) and (channel(o.t, 13, 3) == bi).all() and o.t['m_Skin'] == []
    assert o.t['m_VertexData']['m_Channels'][13]['format'] == 11 and np.allclose(channel(o.t, 0, 3), POS)
