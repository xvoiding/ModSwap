"""Every kind of textured model must come out with the right colour at every triangle corner (ground truth from the source file, see texmatrix.py), through the real loaders and the atlas
the viewer and the builds use; and the viewer's own fit answer must agree.   python tests/test_texture_matrix.py"""
import os, sys, base64, io, tempfile, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texmatrix as T
from PIL import Image
S = T.Spec


def case(build, spec, tol=45, world=None):
    d = tempfile.mkdtemp(); path = build(spec, d); ok, bad, miss, _ = T.check(spec, path, None, tol=tol, world=world(T.write_fbx) if world else None)
    assert bad == 0 and miss == 0 and ok > 0, 'ok %d, wrong %d, unmatched triangles %d' % (ok, bad, miss)


def glb(spec, d):
    p = T.write_trimesh(spec, d, '.glb'); T.patch_glb(p, T.gltf_features(spec)); return p


# ---------------------------------------------------------------- OBJ
def test_obj_basic_shared_vertices_and_folders():
    case(lambda s, d: T.write_obj(s, d), S(n_mat=1)); case(lambda s, d: T.write_obj(s, d), S(n_mat=3, share_vertices=True))
    case(lambda s, d: T.write_obj(s, d, tex_sub='textures'), S(n_mat=4, shared_picture=True))


def test_obj_tiling_odd_sizes_many_materials():
    case(lambda s, d: T.write_obj(s, d), S(n_mat=3, tile=3)); case(lambda s, d: T.write_obj(s, d), S(n_mat=10, sizes=[(512, 128), (128, 512), (256, 256), (1024, 512), (64, 64)] * 2))
    case(lambda s, d: T.write_obj(s, d), S(n_tris=600, n_mat=60, sizes=[(64, 64)] * 60))


def test_obj_picture_formats_and_modes():
    for fmt in ('png', 'jpg', 'bmp', 'tga'): case(lambda s, d, f=fmt: T.write_obj(s, d, fmt=f), S(n_mat=3), tol=60 if fmt == 'jpg' else 45)
    for mode in ('RGBA', 'P', 'L', 'LA'): case(lambda s, d: T.write_obj(s, d), S(n_mat=2, mode=mode), tol=60)
    case(lambda s, d: T.write_obj(s, d, mtl_options='-s 1 1 1 -o 0 0 '), S(n_mat=2))


def test_obj_stress_huge_tiling_stray_and_nan_uvs():
    case(lambda s, d: T.write_obj(s, d), S(n_mat=2, tile=60))
    sp = S(n_mat=2); sp.uv[5, 1] = (900.0, -700.0); sp.skip = {(5, 1)}; case(lambda s, d: T.write_obj(s, d), sp)
    sp = S(n_mat=2); sp.uv[7, 0] = (float('nan'), float('nan')); sp.skip = {(7, 0)}; case(lambda s, d: T.write_obj(s, d), sp)


def test_missing_picture_does_not_break_the_others():
    d = tempfile.mkdtemp(); sp = S(n_mat=3); path = T.write_obj(sp, d); os.remove(os.path.join(d, 'tex1.png')); ok, bad, miss, _ = T.check(sp, path)
    assert ok >= 600 and miss == 0                                                       # (the corners of the material without picture are grey, not matched: that is fine)


def test_giant_pictures_are_shrunk_and_stay_correct():
    case(lambda s, d: T.write_obj(s, d), S(n_mat=4, sizes=[(4096, 4096)] * 4))


# ---------------------------------------------------------------- glTF / GLB / Collada
def test_glb_gltf_plain_and_shared_and_tiled():
    for ext in ('.glb', '.gltf'):
        case(lambda s, d, e=ext: T.write_trimesh(s, d, e), S(n_mat=3)); case(lambda s, d, e=ext: T.write_trimesh(s, d, e), S(n_mat=4, shared_picture=True)); case(lambda s, d, e=ext: T.write_trimesh(s, d, e), S(n_mat=2, tile=2))


def test_glb_sampler_wrap_modes_tint_and_texture_transform():
    case(glb, S(n_mat=3, tile=2, wrap=['repeat', 'mirror', 'clamp']))
    case(glb, S(n_mat=3, tint=[(0.2, 1.0, 0.5), None, (0.8, 0.3, 0.3)]), tol=60)
    case(glb, S(n_mat=3, tf=[((0.25, 0.5), 0.5, (2.0, 2.0)), None, ((0.1, -0.2), 0.0, (0.5, 1.0))]))


def test_collada():
    case(lambda s, d: T.write_dae(s, d), S(n_mat=3)); case(lambda s, d: T.write_dae(s, d), S(n_mat=4, shared_picture=True)); case(lambda s, d: T.write_dae(s, d), S(n_mat=2, tile=2))


# ---------------------------------------------------------------- FBX
def test_fbx_ascii_and_binary_every_layout():
    for binary in (False, True):
        case(lambda s, d: T.write_fbx(s, d, binary=binary), S(n_mat=3))
        case(lambda s, d: T.write_fbx(s, d, binary=binary, multi_model=True, mat_map='AllSame'), S(n_mat=3))
        case(lambda s, d: T.write_fbx(s, d, binary=binary, uv_map='ByPolygonVertex+Direct'), S(n_mat=3))
        case(lambda s, d: T.write_fbx(s, d, binary=binary, uv_map='ByControlPoint'), S(n_mat=3))
        case(lambda s, d: T.write_fbx(s, d, binary=binary, uv_map='ByControlPoint', spell_control='ByControllPoint'), S(n_mat=3))
        case(lambda s, d: T.write_fbx(s, d, binary=binary, multi_model=True, mat_map='AllSame', xform=((0.5, -0.25, 1.0), 90, 2.0)), S(n_mat=3), world=lambda f: f.world)
        case(lambda s, d: T.write_fbx(s, d, binary=binary), S(n_mat=4, shared_picture=True, tile=2))
    case(lambda s, d: T.write_fbx(s, d, binary=True, version=7500, compress=False), S(n_mat=3))
    case(lambda s, d: T.write_fbx(s, d, binary=True), S(n_mat=2, tile=2, wrap=['clamp', 'repeat']))


# ---------------------------------------------------------------- the viewer's own answer
def test_viewer_fit_answer_matches_ground_truth_for_several_formats():
    try: import test_insomniac_server as TS
    except Exception: print('   (no real Spider-Man files: skipped)'); return
    if TS.G is None: print('   (no real Spider-Man files: skipped)'); return
    from modswap.modelio import load_model
    server, sid = TS.setup(); up = os.path.join(server.UPLOADS, sid); ch = TS.wait(server, server.api_characters('sm'))['characters']; fam = next(c['index'] for c in ch if c['label'] == 'Classic Suit')
    cases = [('obj shared picture in textures/', lambda s, d: T.write_obj(s, d, tex_sub='textures'), S(n_mat=4, shared_picture=True, tile=2)), ('glb wrap/tint', glb, S(n_mat=3, tile=2, wrap=['repeat', 'mirror', 'clamp'], tint=[None, (0.5, 1, 1), None])),
             ('fbx binary multi-model', lambda s, d: T.write_fbx(s, d, binary=True, multi_model=True, mat_map='AllSame'), S(n_mat=3)), ('collada', lambda s, d: T.write_dae(s, d), S(n_mat=3))]
    for name, build, spec in cases:
        for f in os.listdir(up):
            fp = os.path.join(up, f)
            if os.path.isfile(fp): os.remove(fp)
            else:
                import shutil; shutil.rmtree(fp)
        path = build(spec, up)
        for root, dirs, files in os.walk(up):                                                    # the app's upload folder is flat: everything dropped goes in one folder
            for f in files:
                if root != up: os.replace(os.path.join(root, f), os.path.join(up, f))
        path = os.path.join(up, os.path.basename(path)); server.MODELS.clear(); server.ATLAS.clear()
        r = server.api_fit(dict(game='sm', family=fam, upload=sid, up='+Y', forward='+Z'))
        uv = np.frombuffer(base64.b64decode(r['new']['uv']), '<f4').reshape(-1, 2); atl = np.asarray(Image.open(io.BytesIO(base64.b64decode(r['atlas']))).convert('RGB')); S_ = atl.shape[0]
        m = load_model(path, up); assert len(uv) == len(m.pos), (name, len(uv), len(m.pos))
        cents = spec.pos.mean(1) if name != 'fbx binary multi-model' else spec.pos.mean(1); ok = bad = 0
        for t3 in m.tris:
            s = int(np.argmin(np.linalg.norm(cents - m.pos[t3].mean(0), axis=1)))
            for vi in t3:
                j = int(np.argmin(np.linalg.norm(spec.pos[s] - m.pos[vi], axis=1)))
                got = atl[min(int(uv[vi, 1] * S_), S_ - 1), min(int(uv[vi, 0] * S_), S_ - 1)]
                if np.abs(got.astype(int) - spec.expected(s, j).astype(int)).max() <= 60: ok += 1
                else: bad += 1
        assert bad == 0 and ok > 600, (name, ok, bad)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print('%d passed' % n)
