"""The 3D viewer stretches its picture over the 0..1 range of the texture coordinates it gets, so the picture it is sent must FILL that range (the Mario-model bug: a texture packed into only part of
the atlas was drawn scrambled in the viewer, while the build was right)."""
import io, os, sys, base64
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modswap import atlas, server


def _pic(seed, size=256):
    r = np.random.RandomState(seed); small = r.randint(0, 255, (16, 16, 3), np.uint8)
    return Image.fromarray(small).resize((size, size), Image.NEAREST)


def _sample(img, uv):
    a = np.asarray(img.convert('RGB')); h, w = a.shape[:2]
    return a[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)].astype(int)


def _check(images, uv, mat, tol=40):
    atl, cells = atlas.pack(images, uv, mat, size=1024); good = atlas.remap_uv(uv, mat, cells, 1024)
    uv2, png = server._viewer_tex(atl, good)
    assert np.allclose(uv2.min(0), 0, atol=1e-6) and np.allclose(uv2.max(0), 1, atol=1e-6), (uv2.min(0), uv2.max(0))        # the picture is stretched over the full range, whatever the viewer does
    pic2 = Image.open(io.BytesIO(base64.b64decode(png))); assert pic2.size == (1024, 1024)
    same = np.abs(_sample(Image.fromarray(atl), good) - _sample(pic2, uv2)).max(1)
    assert np.mean(same <= tol) > 0.92, np.mean(same <= tol)                                                              # every vertex still finds the colour it found in the atlas
    return cells


def test_plain_texture_fills_the_atlas_cell():
    r = np.random.RandomState(1); uv = r.uniform(0.007, 0.999, (3000, 2)); uv[:, 1] = np.clip(uv[:, 1], 0.0016, 0.998)
    cells = _check([_pic(1)], uv, np.zeros(3000, int))
    c = cells[0]; assert (c.u0, c.v0, c.u1, c.v1) == (0.0, 0.0, 1.0, 1.0), c            # no more -0.25..1.25 cell wasting a fifth of the resolution


def test_texture_using_part_of_the_picture():
    r = np.random.RandomState(2); uv = r.uniform(0.2, 0.55, (2000, 2)); _check([_pic(2)], uv, np.zeros(2000, int))


def test_several_materials_packed_side_by_side():
    r = np.random.RandomState(3); n = 4000; mat = r.randint(0, 3, n); uv = r.uniform(0.01, 0.99, (n, 2)); _check([_pic(3), _pic(4, 128), _pic(5, 512)], uv, mat)


def test_tiled_texture():
    r = np.random.RandomState(4); uv = r.uniform(-0.2, 2.3, (3000, 2)); _check([_pic(6)], uv, np.zeros(3000, int), tol=60)
