"""A mod you built can be opened again: its model, textures and every fit setting come back.   python tests/test_edit_mod.py"""
import os, sys, tempfile, shutil, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
cfg = tempfile.mkdtemp(prefix='modswap_test_cfg_'); os.environ['XDG_CONFIG_HOME'] = cfg; os.environ['APPDATA'] = cfg      # never touch the real settings
from modswap import mods, server


def make_upload():
    d = tempfile.mkdtemp(prefix='modswap_test_up_'); os.makedirs(os.path.join(d, 'textures'))
    open(os.path.join(d, 'hero.obj'), 'w').write('v 0 0 0\n'); open(os.path.join(d, 'textures', 'skin.png'), 'wb').write(b'PNGDATA')
    pak = os.path.join(d, 'built.pak'); open(pak, 'wb').write(b'PAK'); return d, pak


BODY = dict(game='g1', family='fam3', target=1, up='+Z', forward='-Y', scale=1.25, width=1.1, height=0.9, depth=1.0, yaw=35, pitch=-12, roll=4, dx=1, dy=2, dz=3,
            parts=[0, 2], edits={'g': {'2': {'move': [0, 0, 5], 'rot': [10, 20, 30]}}, 'c': []}, upload='ignored', name='ignored')


def test_roundtrip_keeps_every_setting_and_the_model_files():
    d, pak = make_upload()
    mid = mods.add('g1', 'Hero', pak, character='Wally', source_dir=d, edit=server._edit_record(BODY))
    info = mods.edit_info('g1', mid)
    for k in ('family', 'target', 'up', 'forward', 'scale', 'width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'parts', 'edits'):
        assert info[k] == BODY[k], (k, info.get(k), BODY[k])
    assert 'upload' not in info and info['name'] == 'Hero' and info['character'] == 'Wally'
    r = server.api_mod_edit(dict(game='g1', id=mid))                     # what the "Edit" button will call
    up = os.path.join(server.UPLOADS, r['upload'])
    assert r['file'] == 'hero.obj' and r['settings']['yaw'] == 35 and r['settings']['edits']['g']['2']['rot'] == [10, 20, 30]
    assert open(os.path.join(up, 'textures', 'skin.png'), 'rb').read() == b'PNGDATA'        # textures come back too
    shutil.rmtree(d, ignore_errors=True)                                 # the original upload can be gone: the mod keeps its own copy
    assert mods.open_for_edit('g1', mid, tempfile.mkdtemp(prefix='again_'))['pitch'] == -12


def test_old_mods_without_source_say_so_plainly():
    d, pak = make_upload(); mid = mods.add('g1', 'Old', pak)
    assert mods.edit_info('g1', mid) is None
    try: mods.open_for_edit('g1', mid, tempfile.mkdtemp(prefix='x_')); raise SystemExit('should refuse')
    except ValueError as e: assert "can't be reopened" in str(e)


def test_deleting_a_mod_removes_its_source_too():
    d, pak = make_upload(); mid = mods.add('g1', 'Temp', pak, source_dir=d, edit=server._edit_record(BODY))
    folder = os.path.dirname(mods.pak_path('g1', mid)); assert os.path.isdir(os.path.join(folder, 'source'))
    mods.delete('g1', mid); assert not os.path.exists(folder)


def test_listing_still_works_with_the_extra_files():
    d, pak = make_upload(); mid = mods.add('g1', 'Listed', pak, source_dir=d, edit=server._edit_record(BODY))
    m = next(x for x in mods.list_mods('g1') if x['id'] == mid); assert m['name'] == 'Listed' and m['size'] > 0


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed'); shutil.rmtree(cfg, ignore_errors=True)
