"""There is no vertex limit: Unreal meshes switch to 32-bit indices, Unity 2017.3+ meshes too, and old Unity (hard 65,535 engine limit) is reduced
with a message instead of failing.   python tests/test_vertex_limit.py"""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.ue4 import buildsk, skmesh
from modswap.ue4.uepkg import R
from modswap.unity import patch


def grid_mesh(nx, ny):
    """a flat (nx*ny)-vertex sheet with triangles"""
    xs, ys = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    pos = np.stack([xs.ravel(), ys.ravel(), np.sin(xs.ravel() / 7) * 3], 1).astype(np.float32)
    i = np.arange(nx * ny).reshape(ny, nx); a, b, c, d = i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, :-1].ravel(), i[1:, 1:].ravel()
    tris = np.concatenate([np.stack([a, b, c], 1), np.stack([b, d, c], 1)]).astype(np.int64)
    nrm = np.tile(np.array([0, 0, 1], np.float32), (nx * ny, 1)); uv = (pos[:, :2] / max(nx, ny)).astype(np.float32)
    return pos, nrm, uv, tris


# ------------------------------------------------------------------ Unreal
def _read_block(blob):
    r = R(blob, 0); isz_flag = r.u8(); b = skmesh.bulk(r)
    return isz_flag, b, np.frombuffer(blob[b['start']:b['end']], '<u4' if b['isz'] == 4 else '<u2')


def test_ue_small_mesh_stays_16_bit():
    tris = np.array([[0, 1, 2], [2, 1, 3]]); blob = buildsk.idx_block(tris.astype('<u2').tobytes(), 2)
    flag, b, back = _read_block(blob)
    assert flag == 2 and b['isz'] == 2 and b['cnt'] == 6 and back.tolist() == tris.ravel().tolist()


def test_ue_big_mesh_uses_32_bit():
    pos, nrm, uv, tris = grid_mesh(300, 300)                 # 90,000 vertices (> 65,535)
    assert len(pos) > 65536 and tris.max() > 65535
    blob = buildsk.idx_block(tris.astype('<u4').tobytes(), len(tris))
    flag, b, back = _read_block(blob)
    assert flag == 4 and b['isz'] == 4 and b['cnt'] == 3 * len(tris)
    assert np.array_equal(back.astype(np.int64).reshape(-1, 3), tris), 'indices above 65535 were not kept'


def test_ue_rejects_garbage_index_size():
    try: buildsk.idx_block(b'\x00' * 9, 1); raise SystemExit('should have refused')
    except AssertionError: pass


# ------------------------------------------------------------------ Unity
class FakeObj:
    """stands in for a UnityPy Mesh object: just a typetree dict"""
    def __init__(self, with_index_format, idx_as_list=True):
        ch = [dict(stream=0, offset=0, format=0, dimension=0) for _ in range(8)]
        self.t = {'m_MeshCompression': 0, 'm_VertexData': {'m_VertexCount': 3, 'm_Channels': ch, 'm_DataSize': b''},
                  'm_IndexBuffer': [] if idx_as_list else b'', 'm_SubMeshes': [dict(firstByte=0, indexCount=3, topology=0, firstVertex=0, vertexCount=3, localAABB={}, baseVertex=0)],
                  'm_Skin': [], 'm_BindPose': [], 'm_BoneNameHashes': [], 'm_Shapes': {}, 'm_StreamData': {'offset': 0, 'size': 0, 'path': ''}}
        if with_index_format: self.t['m_IndexFormat'] = 0
    def read_typetree(self): return dict(self.t)
    def save_typetree(self, t): self.t = t


def _idx_bytes(t): ib = t['m_IndexBuffer']; return bytes(ib) if isinstance(ib, list) else ib


def test_unity_new_version_gets_32_bit_indices_and_keeps_every_vertex():
    pos, nrm, uv, tris = grid_mesh(300, 300); o = FakeObj(with_index_format=True); msgs = []
    patch.set_mesh(o, pos, nrm, uv, tris, log=msgs.append)
    t = o.t
    assert t['m_IndexFormat'] == 1 and t['m_VertexData']['m_VertexCount'] == len(pos) and not msgs
    assert t['m_SubMeshes'][0]['indexCount'] == tris.size and t['m_SubMeshes'][0]['vertexCount'] == len(pos)
    idx = np.frombuffer(_idx_bytes(t), '<u4'); assert idx.size == tris.size and np.array_equal(idx.reshape(-1, 3), tris)


def test_unity_small_mesh_stays_16_bit_on_new_version():
    pos, nrm, uv, tris = grid_mesh(20, 20); o = FakeObj(with_index_format=True)
    patch.set_mesh(o, pos, nrm, uv, tris)
    assert o.t['m_IndexFormat'] == 0 and len(_idx_bytes(o.t)) == tris.size * 2


def test_unity_old_version_is_reduced_not_refused():
    pos, nrm, uv, tris = grid_mesh(400, 400)                 # 160,000 vertices, Unity 5.x has no m_IndexFormat
    o = FakeObj(with_index_format=False, idx_as_list=False); msgs = []
    patch.set_mesh(o, pos, nrm, uv, tris, log=msgs.append)
    n = o.t['m_VertexData']['m_VertexCount']
    assert 1000 < n <= patch.LIMIT16, n
    idx = np.frombuffer(_idx_bytes(o.t), '<u2'); assert idx.size and idx.max() < n and idx.size % 3 == 0
    assert msgs and 'reduced from 160000' in msgs[0], msgs


def test_reduce_keeps_shape_uv_and_skin_consistent():
    pos, nrm, uv, tris = grid_mesh(400, 400)
    bi = np.tile(np.arange(4), (len(pos), 1)); bw = np.tile(np.array([.4, .3, .2, .1]), (len(pos), 1))
    P, Nn, UV, T, sk = patch.reduce_vertices(pos, nrm, uv, tris, (bi, bw))
    assert len(P) <= patch.LIMIT16 and len(P) == len(Nn) == len(UV) == len(sk[0]) == len(sk[1])
    assert T.max() < len(P) and T.min() >= 0 and (T[:, 0] != T[:, 1]).all() and (T[:, 1] != T[:, 2]).all() and (T[:, 0] != T[:, 2]).all()
    assert np.allclose(np.linalg.norm(Nn, axis=1), 1, atol=1e-4)
    assert np.abs(P.min(0) - pos.min(0)).max() < 15 and np.abs(P.max(0) - pos.max(0)).max() < 15     # still covers the same area
    assert np.allclose(sk[1].sum(1), 1) and sk[0].shape == (len(P), 4)
    # untouched when already small
    p2 = patch.reduce_vertices(pos[:100], nrm[:100], uv[:100], np.array([[0, 1, 2]]), None)
    assert len(p2[0]) == 100


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
