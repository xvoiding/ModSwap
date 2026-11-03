"""'python -m modswap rebuild' redoes saved mods with the current engine, keeping every setting, replacing in place.   python tests/test_rebuild_mods.py"""
import os, sys, json, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
cfg = tempfile.mkdtemp(prefix='ms_cfg_'); os.environ['XDG_CONFIG_HOME'] = cfg; os.environ['APPDATA'] = cfg
from modswap import mods, server, cli
from modswap.games.library import Library

os.makedirs(os.path.join(cfg, 'ModSwap'), exist_ok=True)
json.dump({'games': [dict(id='g1', name='Test Game', root='/x', source='steam', engine='unreal', engine_version='4.25')]}, open(os.path.join(cfg, 'ModSwap', 'games.json'), 'w'))
BODY = dict(game='g1', family='fam', target=0, up='+Z', forward='-Y', scale=1.1, width=1.2, height=1, depth=0.9, yaw=33, pitch=-5, roll=2, dx=1, dy=0, dz=-3,
            parts=[0], edits={'g': {'2': {'move': [0, 0, 4]}}, 'c': []})
CALLS = []


def new_mod(name='Hero'):
    d = tempfile.mkdtemp(); open(os.path.join(d, 'hero.obj'), 'w').write('v 0 0 0\n'); open(os.path.join(d, 'tex.png'), 'wb').write(b'PNG')
    pak = os.path.join(d, 'b.pak'); open(pak, 'wb').write(b'OLDPAK')
    return mods.add('g1', name, pak, character='Wally', source_dir=d, edit=server._edit_record(BODY))


class FakeProject:
    active = []
    def installed(self): return {'k': {'mods': list(FakeProject.active)}}


def fake_apply(fail=False):
    def apply(body):
        CALLS.append(dict(body)); jid = 'job%d' % len(CALLS)
        d = os.path.join(server.UPLOADS, body['upload']); assert os.path.isfile(os.path.join(d, 'hero.obj')), 'model was not restored for the rebuild'
        if fail: server.JOBS[jid] = dict(done=True, log=['boom'], error='the build failed', result=None); return jid
        pak = os.path.join(d, 'new.pak'); open(pak, 'wb').write(b'NEWPAK')
        nid = mods.add('g1', body['name'], pak, character='Wally', source_dir=d, edit=server._edit_record(body))
        server.JOBS[jid] = dict(done=True, log=['built'], error=None, result=dict(mod=nid)); return jid
    return apply


def setup(fail=False, active=()):
    server._project = lambda g: FakeProject(); FakeProject.active = list(active); server.api_apply = fake_apply(fail); CALLS.clear()


def test_rebuild_keeps_every_setting_and_replaces_the_old_mod():
    old = new_mod('Hero'); setup()
    new = server.rebuild_mod('g1', old)
    b = CALLS[0]
    for k in ('family', 'target', 'up', 'forward', 'scale', 'width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'parts', 'edits'): assert b[k] == BODY[k], k
    assert b['name'] == 'Hero' and b['game'] == 'g1' and b['install'] is False
    ids = [m['id'] for m in mods.list_mods('g1')]
    assert new in ids and old not in ids, 'old entry should be replaced by the new one'
    assert open(mods.pak_path('g1', new), 'rb').read() == b'NEWPAK'


def test_installed_mod_comes_back_installed():
    old = new_mod('Installed'); setup(active=[old])
    new = server.rebuild_mod('g1', old); assert CALLS[0]['install'] is True


def test_failed_rebuild_leaves_the_old_mod_alone():
    old = new_mod('Keep'); setup(fail=True)
    try: server.rebuild_mod('g1', old); raise SystemExit('should have failed')
    except RuntimeError as e: assert 'build failed' in str(e)
    assert old in [m['id'] for m in mods.list_mods('g1')] and open(mods.pak_path('g1', old), 'rb').read() == b'OLDPAK'


def test_mod_without_saved_model_is_refused_clearly():
    d = tempfile.mkdtemp(); pak = os.path.join(d, 'b.pak'); open(pak, 'wb').write(b'x'); old = mods.add('g1', 'Ancient', pak); setup()
    try: server.rebuild_mod('g1', old); raise SystemExit('should refuse')
    except ValueError as e: assert 'before ModSwap kept its model' in str(e)


def test_cli_rebuild_all_reports_counts(capsys=None):
    for m in mods.list_mods('g1'): mods.delete('g1', m['id'])
    a = new_mod('A'); b = new_mod('B')
    d = tempfile.mkdtemp(); pak = os.path.join(d, 'b.pak'); open(pak, 'wb').write(b'x'); mods.add('g1', 'Ancient', pak)
    setup()
    import io, contextlib; buf = io.StringIO()
    with contextlib.redirect_stdout(buf): cli.main(['rebuild'])
    out = buf.getvalue()
    assert '2 rebuilt, 1 skipped, 0 failed' in out, out
    assert sorted(m['name'] for m in mods.list_mods('g1')) == ['A', 'Ancient', 'B']


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed'); shutil.rmtree(cfg, ignore_errors=True)
