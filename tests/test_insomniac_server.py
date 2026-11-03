"""Spider-Man through the app's own server functions (characters, fit for the 3D viewer, apply, mods list, uninstall, restore) on a fake game folder that holds
the REAL classic-suit assets (skipped without them).   python tests/test_insomniac_server.py"""
import os, sys, json, time, tempfile, hashlib, base64
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
cfg = tempfile.mkdtemp(prefix='ms_cfg_'); os.environ['XDG_CONFIG_HOME'] = cfg; os.environ['APPDATA'] = cfg
from test_insomniac_cli import real_game, SAMPLES, sha
from humanoid_fixture import humanoid

G = real_game()


def setup():
    os.makedirs(os.path.join(cfg, 'ModSwap'), exist_ok=True)
    json.dump({'games': [dict(id='sm', name="Marvel's Spider-Man Remastered", root=G, source='steam', engine='unknown')]}, open(os.path.join(cfg, 'ModSwap', 'games.json'), 'w'))
    from modswap import server
    server.UPLOADS = tempfile.mkdtemp(prefix='ms_up_')
    sid = 'up1'; d = os.path.join(server.UPLOADS, sid); os.makedirs(d)
    h = humanoid(); h.images[0].save(os.path.join(d, 'tex.png'))
    with open(os.path.join(d, 'hero.obj'), 'w') as f:
        f.write('mtllib hero.mtl\nusemtl m\n'); [f.write('v %f %f %f\n' % tuple(p)) for p in h.pos]; [f.write('vt %f %f\n' % (u, 1 - v)) for u, v in h.uv]
        [f.write('vn %f %f %f\n' % tuple(n)) for n in h.nrm]; [f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % tuple(x for i in t for x in (i + 1, i + 1, i + 1))) for t in h.tris + 0]
    open(os.path.join(d, 'hero.mtl'), 'w').write('newmtl m\nKd 1 1 1\nmap_Kd tex.png\n')
    return server, sid


def wait(server, jid):
    for _ in range(600):
        j = server.JOBS[jid]
        if j['done']: break
        time.sleep(0.2)
    assert not j['error'], j['error']; return j['result']


def test_whole_flow():
    if G is None: print('   (no real samples: skipped)'); return
    server, sid = setup(); ad = os.path.join(G, 'asset_archive'); before = sha(os.path.join(ad, 'toc'))
    from modswap.games.library import Library
    gj = server._game_json(Library().games['sm']); assert gj['engine'] == 'insomniac' and gj['supported'] is True, gj
    ch = wait(server, server.api_characters('sm'))['characters']; assert ch and ch[0]['label'].endswith('Suit') and ch[0]['rigged'], ch
    fam = next(c['index'] for c in ch if c['label'] == 'Classic Suit')
    body = dict(game='sm', family=fam, upload=sid, up='+Y', forward='+Z', scale=1.0)
    f = server.api_fit(body)
    n, t = f['new']['n'], f['new']['t']
    pos = np.frombuffer(base64.b64decode(f['new']['pos']), '<f4').reshape(-1, 3); idx = np.frombuffer(base64.b64decode(f['new']['idx']), '<u4').reshape(-1, 3)
    opos = np.frombuffer(base64.b64decode(f['orig']['pos']), '<f4').reshape(-1, 3)
    assert len(pos) == n and len(idx) == t and idx.max() < n and np.isfinite(pos).all() and len(base64.b64decode(f['new']['uv'])) == n * 8
    assert 160 < f['height'] < 200, 'the suit is about 1.8 m = 180 cm tall in the viewer'
    assert abs((pos[:, 2].max() - pos[:, 2].min()) - (opos[:, 2].max() - opos[:, 2].min())) < 15, 'your model is fitted to the suit\'s height'
    assert abs(pos[:, 0].mean()) < 10 and pos[:, 2].min() > -15, 'centred and standing on the floor'
    r = wait(server, server.api_apply(dict(body, name='Granny', install=True)))
    assert r.get('mod') and r.get('installed'), r
    mods = server.api_mods('sm'); assert mods['anyInstalled'] and [m['active'] for m in mods['mods']] == [True], mods
    from modswap.insomniac.toc import Toc
    t = Toc.open(ad); assert t.archive_name(t.find('characters/hero/hero_spiderman_classic/hero_spiderman_classic.model')).startswith('mods\\')
    wait(server, server.api_apply(dict(body, name='Granny 2', install=True)))                    # a second mod for the same suit replaces the first
    mods = server.api_mods('sm'); assert sum(m['active'] for m in mods['mods']) == 1 and len(mods['mods']) == 2, mods
    mid = next(m['id'] for m in mods['mods'] if m['active'])
    wait(server, server.api_mod_uninstall(dict(game='sm', id=mid))['job']); assert sha(os.path.join(ad, 'toc')) == before, 'uninstalling the only active mod restores the original index'
    inst = server.api_mod_install(dict(game='sm', id=mid, name='again')); wait(server, inst['job']); assert sha(os.path.join(ad, 'toc')) != before, 'a saved mod installs again from the library'
    server.api_restore('sm'); assert sha(os.path.join(ad, 'toc')) == before and os.listdir(os.path.join(ad, 'mods')) == []


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
