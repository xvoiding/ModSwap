"""The Spider-Man command line against a fake game folder that holds the REAL classic-suit model and its materials (skipped without them).   python tests/test_insomniac_cli.py"""
import os, sys, struct, tempfile, hashlib, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modswap.insomniac import toc as T, cli as C, model as M
from modswap.insomniac.toc import Toc
from test_insomniac_toc import build_toc
from humanoid_fixture import humanoid

SAMPLES = next((p for p in (os.environ.get('SPIDERMAN_ASSETS'), '/tmp/s4/x/assets', '/tmp/sm2/assets') if p and os.path.isfile(os.path.join(p, 'A816085E5C2AFAEB.bin'))), '/tmp/sm2/assets')
MODEL = 'characters/hero/hero_spiderman_classic/hero_spiderman_classic.model'


def real_game():
    if not os.path.isfile(os.path.join(SAMPLES, 'BF45D48B5314EC76.bin')): return None
    g = tempfile.mkdtemp(prefix='ms_cli_'); ad = os.path.join(g, 'asset_archive'); os.makedirs(ad)
    arc = bytearray(); assets = []
    for f in sorted(os.listdir(SAMPLES)):
        if not f.endswith('.bin'): continue
        b = open(os.path.join(SAMPLES, f), 'rb').read(); assets.append((int(f[:-4], 16), 0, len(arc), len(b))); arc += b + b'\0' * (-len(b) % 16)
    open(os.path.join(ad, 'g00s000'), 'wb').write(bytes(arc))                                  # (a plain archive: the reader accepts those too)
    open(os.path.join(ad, 'toc'), 'wb').write(build_toc(assets, ['g00s000'])); return g


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try: __import__('modswap.cli', fromlist=['main']).main(list(args))
        except SystemExit as e:
            if e.code not in (None, 0): return out.getvalue() + 'EXIT: %s' % e.code
    return out.getvalue()


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def test_slots_pick_the_rubber_material():
    g = real_game()
    if g is None: print('   (no real samples: skipped)'); return
    out = run('spiderman', '--dir', g, 'slots', '--suit', 'classic')
    assert 'hero_spiderman_classic_rubber_c.texture' in out and 'slot ModSwap would use: 3' in out, out


def test_dry_run_install_restore_roundtrip():
    g = real_game()
    if g is None: print('   (no real samples: skipped)'); return
    import modswap.modelio as MIO
    MIO.load_model = lambda path, textures=None: humanoid()
    ad = os.path.join(g, 'asset_archive'); before = sha(os.path.join(ad, 'toc'))
    out_model = os.path.join(g, 'out.model'); png = os.path.join(g, 'atlas.png')
    out = run('spiderman', '--dir', g, 'install', '--suit', 'classic', '--model', 'x.fbx', '--forward', '+Z', '--dry-run', out_model, '--atlas-out', png)
    assert 'nothing installed' in out and os.path.isfile(out_model) and os.path.isfile(png) and sha(os.path.join(ad, 'toc')) == before, out
    M.Model(open(out_model, 'rb').read())                                                      # re-reads cleanly
    out = run('spiderman', '--dir', g, 'install', '--suit', 'classic', '--model', 'x.fbx', '--forward', '+Z', '--name', 'Test')
    assert 'installed "Test"' in out and '+ 3 textures' in out, out
    assert 'Test' in run('spiderman', '--dir', g, 'list')
    from modswap.insomniac import texture as TX
    t = Toc.open(ad); data = t.read(t.find(MODEL), ad); M.Model(data)
    rub = 'characters/hero/hero_spiderman_classic/textures/hero_spiderman_classic_rubber_%s.texture'
    tc = TX.Texture(t.read(t.find(rub % 'c'), ad)); assert (tc.width, tc.height, tc.fmt) == (1024, 1024, 99) and tc.mips == 8, 'colour texture replaced by the 1024 picture'
    tn = TX.Texture(t.read(t.find(rub % 'n'), ad)); assert tuple(tn.decode(0)[0, 0]) == (127, 127, 0, 255)
    assert len(os.listdir(os.path.join(ad, 'mods'))) == 4 and 'Test' in run('spiderman', '--dir', g, 'list')
    assert t.archive_name(t.find(MODEL)).startswith('mods\\') and len(M.Model(data).meshes()) == len(M.Model(open(os.path.join(SAMPLES, 'BF45D48B5314EC76.bin'), 'rb').read()).meshes())
    run('spiderman', '--dir', g, 'restore')
    assert sha(os.path.join(ad, 'toc')) == before and 'nothing installed' in run('spiderman', '--dir', g, 'list')


def test_not_a_game_folder():
    assert 'no asset_archive folder' in run('spiderman', '--dir', tempfile.mkdtemp(), 'suits')


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1
    print('%d passed' % n)
