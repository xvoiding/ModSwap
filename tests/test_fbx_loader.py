"""FBX loading with ONE shared texture in a sub-folder (the usual Sketchfab layout), checked against ground truth: every part must sample the colour of its own texture quadrant.   python tests/test_fbx_loader.py"""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image
from modswap import atlas
from modswap.modelio import load_model

QUAD = {(0, 0): (220, 40, 40), (1, 0): (240, 190, 150), (0, 1): (40, 70, 200)}        # hat, face, body


def make(out, tex_in='textures', n_parts=3, W=256):
    os.makedirs(os.path.join(out, tex_in), exist_ok=True); img = np.zeros((W, W, 3), np.uint8); img[:] = (250, 250, 250)
    for (qx, qy), c in QUAD.items(): img[qy * W // 2:(qy + 1) * W // 2, qx * W // 2:(qx + 1) * W // 2] = c
    Image.fromarray(img).save(os.path.join(out, tex_in, 'texture.png'))
    parts = [('hat', (-0.2, 1.6, -0.2, 0.2, 1.8, 0.2), (0, 0)), ('face', (-0.2, 1.3, -0.2, 0.2, 1.6, 0.2), (1, 0)), ('body', (-0.25, 0.0, -0.15, 0.25, 1.3, 0.15), (0, 1))][:n_parts]
    arr = lambda a: '*%d {\n a: %s\n }' % (len(a), ','.join('%.6f' % x if isinstance(x, float) else str(x) for x in a)); objs = []; conn = []
    for i, (n, (x0, y0, z0, x1, y1, z1), (qx, qy)) in enumerate(parts):
        V = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]; quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        pvi = [c for q in quads for c in q]
        for k in range(3, 24, 4): pvi[k] = ~pvi[k]
        tab = [(qx * .5 + u, 1 - (qy * .5 + v)) for u, v in ((0.05, 0.05), (0.45, 0.05), (0.45, 0.45), (0.05, 0.45))]
        objs.append('Geometry: %d, "Geometry::%s", "Mesh" {\n Vertices: %s\n PolygonVertexIndex: %s\n LayerElementUV: 0 {\n  MappingInformationType: "ByPolygonVertex"\n  ReferenceInformationType: "IndexToDirect"\n  UV: %s\n  UVIndex: %s\n }\n'
                    ' LayerElementMaterial: 0 {\n  MappingInformationType: "AllSame"\n  ReferenceInformationType: "IndexToDirect"\n  Materials: %s\n }\n}'
                    % (1000 + i, n, arr([c for v in V for c in v]), arr(pvi), arr([c for uv in tab for c in uv]), arr([k for _ in range(6) for k in range(4)]), arr([0])))
        objs.append('Model: %d, "Model::%s", "Mesh" {\n Properties70: {\n }\n}' % (2000 + i, n)); objs.append('Material: %d, "Material::mat_%s", "" {\n}' % (3000 + i, n))
        conn += ['C: "OO", %d, %d' % (1000 + i, 2000 + i), 'C: "OO", %d, %d' % (3000 + i, 2000 + i), 'C: "OP", 4001, %d, "DiffuseColor"' % (3000 + i)]
    objs.append('Texture: 4001, "Texture::tex", "" {\n Type: "TextureVideoClip"\n FileName: "C:/author/pc/%s/texture.png"\n RelativeFilename: "%s/texture.png"\n}' % (tex_in, tex_in))
    path = os.path.join(out, 'source', 'mario.fbx'); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write('; FBX 7.3.0 project file\nFBXHeaderExtension: {\n FBXVersion: 7300\n}\nGlobalSettings: {\n Properties70: {\n  P: "UpAxis", "int", "Integer", "",1\n }\n}\nObjects: {\n' + '\n'.join(objs) + '\n}\nConnections: {\n' + '\n'.join(conn) + '\n}\n')
    return path


def colours(m, size):
    imgs = m.images; atl, cells = atlas.pack(imgs, m.uv, m.vert_mat, size=size); uv = atlas.remap_uv(m.uv, m.vert_mat, cells, size)
    return atl[np.minimum((uv[:, 1] * size).astype(int), size - 1), np.minimum((uv[:, 0] * size).astype(int), size - 1)], cells


def test_texture_in_a_sibling_folder_is_found_and_every_part_gets_its_own_colour():
    d = tempfile.mkdtemp(); path = make(d); m = load_model(path)             # model in source/, picture in textures/ (no texture folder passed)
    assert len(m.mat_names) == 3 and all(im is not None for im in m.images), 'the picture next to the model folder must be found'
    assert len(m.part_names) == 3 and len(m.tris) == 36
    for size in (1024, 2048):
        col, _ = colours(m, size)
        for part, c in zip(range(3), QUAD.values()):
            sel = m.vert_mat == part; assert sel.any() and (np.abs(col[sel].astype(int) - np.array(c)).max(1) <= 12).mean() > 0.97, (size, part)


def test_materials_sharing_one_picture_share_one_cell():
    d = tempfile.mkdtemp(); m = load_model(make(d, W=1024)); _, cells = colours(m, 1024)
    assert cells[0] is cells[1] is cells[2], 'one picture, one cell'
    assert cells[0].w >= 900, 'the shared picture keeps (nearly) the whole atlas instead of a third of it'


def test_picture_in_the_model_folder_and_in_a_far_folder_still_works():
    d = tempfile.mkdtemp(); path = make(d, tex_in='tex'); m = load_model(path); assert all(im is not None for im in m.images)
    m2 = load_model(path, texture_dir=os.path.join(d, 'tex')); assert all(im is not None for im in m2.images)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
