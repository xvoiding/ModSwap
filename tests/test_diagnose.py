"""python -m modswap diagnose: a folder is loaded like the app does it, the picture in a sibling folder is found even when the MTL names another file, and the report + software previews are written.   python tests/test_diagnose.py"""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texmatrix as T
from modswap import diagnose
from modswap.modelio import load_model


def layout():
    d = tempfile.mkdtemp(); os.makedirs(d + '/source'); os.makedirs(d + '/textures'); sp = T.Spec(n_mat=1, n_tris=300); T.write_obj(sp, d + '/source')
    os.replace(d + '/source/tex0.png', d + '/textures/texture.png'); mt = open(d + '/source/m.mtl').read().replace('tex0.png', 'not_the_real_name.png'); open(d + '/source/m.mtl', 'w').write(mt); return d, sp


def test_folder_mode_finds_the_picture_and_writes_report_and_previews():
    d, sp = layout(); worst, mixed = diagnose.run(d, None, d + '/out', log=lambda *a: None); rep = open(d + '/out/diagnose_report.txt').read()
    assert worst == 0 and mixed == 0 and 'none (grey)' not in rep and '256x256' in rep and 'map_Kd not_the_real_name.png' in rep, rep
    for f in ('atlas_1024.png', 'preview_front.png', 'preview_back.png', 'diagnose_report.txt'): assert os.path.isfile(os.path.join(d, 'out', f)), f


def test_app_style_loading_assigns_the_only_picture_to_the_only_material():
    d, sp = layout(); flat = diagnose.flatten(d); m = load_model(os.path.join(flat, 'm.obj'), flat); assert m.images[0] is not None and m.images[0].size == (256, 256)
    m2 = load_model(os.path.join(d, 'source', 'm.obj'), None); assert m2.images[0] is not None, 'a picture in the sibling textures folder is found without flattening too'


def test_preview_is_drawn_from_the_texture():
    d, sp = layout(); diagnose.run(d, None, d + '/out', log=lambda *a: None)
    from PIL import Image
    a = np.asarray(Image.open(d + '/out/preview_front.png')); assert len(np.unique(a.reshape(-1, 3), axis=0)) > 8, 'the preview shows several texture colours, not a flat fill'


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
