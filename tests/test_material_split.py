"""Vertices shared by two materials must not smear one material's texture across the other's triangles.   python tests/test_material_split.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image
from modswap import modelio, atlas


def shared_vertex_model():
    # two quads side by side; the middle two vertices (1, 2) are used by BOTH materials, with identical position + uv + normal (so a welder keeps them as one)
    pos = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [2, 0, 0], [2, 1, 0]], float)
    uv = np.array([[0.1, 0.1], [0.5, 0.1], [0.5, 0.9], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9]])
    tris = np.array([[0, 1, 2], [0, 2, 3], [1, 4, 5], [1, 5, 2]], np.int32); tri_mat = np.array([0, 0, 1, 1], np.int32)
    imgs = [Image.new('RGB', (64, 64), (230, 20, 20)), Image.new('RGB', (64, 64), (20, 20, 230))]
    return modelio.Model(pos, np.tile([0, 0, 1.0], (6, 1)), uv, tris, tri_mat, imgs, ['red', 'blue'])


def wrong_colours(m, size=256):
    atl, cells = atlas.pack(m.images, m.uv, m.vert_mat, size=size); uv = atlas.remap_uv(m.uv, m.vert_mat, cells, size); bad = 0
    for t, mat in zip(m.tris, m.tri_mat):
        want = np.array(m.images[mat].getpixel((0, 0)))
        for k in t:
            got = atl[min(int(uv[k, 1] * size), size - 1), min(int(uv[k, 0] * size), size - 1)]
            bad += int(np.abs(got.astype(int) - want).max() > 60)
    return bad


def test_before_the_fix_a_shared_vertex_has_the_wrong_colour():
    assert wrong_colours(shared_vertex_model()) > 0, 'the fixture must show the problem'


def test_split_gives_every_triangle_corner_its_own_materials_colour():
    m = modelio.split_by_material(shared_vertex_model())
    assert wrong_colours(m) == 0 and len(m.pos) == 8
    flat = m.pos[m.tris].reshape(-1, 3); orig = shared_vertex_model(); assert np.allclose(flat, orig.pos[orig.tris].reshape(-1, 3)), 'triangles keep their corners'
    assert np.array_equal(m.tri_mat, orig.tri_mat)


def test_nothing_shared_means_nothing_changes():
    m = shared_vertex_model(); m.tris = np.array([[0, 1, 2], [0, 2, 1], [3, 4, 5], [3, 5, 4]], np.int32)
    assert modelio.split_by_material(m) is m


def test_single_material_models_are_untouched():
    m = shared_vertex_model(); m.tri_mat[:] = 0; assert modelio.split_by_material(m) is m


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
