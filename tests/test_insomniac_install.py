"""Installing / removing Spider-Man mods: the toc is always rebuilt from toc.BAK, so everything is reversible.   python tests/test_insomniac_install.py"""
import os, sys, hashlib, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modswap.insomniac import install as I
from modswap.insomniac.toc import Toc, path_id
from test_insomniac_toc import fake_game

MODEL = 'characters/hero/hero_spiderman_classic/hero_spiderman_classic.model'
BASE = 'characters/hero/hero_spiderman_base/hero_spiderman_base.model'


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def game():
    g, ids, blobs = fake_game(with_bak=False); return g, blobs, os.path.join(g, 'asset_archive')


def test_install_redirects_the_asset_and_keeps_the_original_toc():
    g, blobs, ad = game(); orig_hash = sha(os.path.join(ad, 'toc')); inst = I.Installer(g)
    inst.install('m1', MODEL, b'NEW-MODEL-BYTES', 'My mod')
    assert sha(os.path.join(ad, 'toc.BAK')) == orig_hash, 'the original toc must be kept untouched as toc.BAK'
    t = Toc.open(ad); i = t.find(MODEL)
    assert t.archive_name(i) == 'mods\\modswap_m1' and t.read(i, ad) == b'NEW-MODEL-BYTES' and t.size(i) == 15
    assert t.read(t.find(BASE), ad) == blobs['base'], 'other assets must read as before'
    assert [m['id'] for m in inst.installed()] == ['m1']
    assert inst.read_original(MODEL) == blobs['model'], 'the original model stays readable through toc.BAK'


def test_installing_for_the_same_target_replaces_and_other_targets_stack():
    g, blobs, ad = game(); inst = I.Installer(g)
    inst.install('a', MODEL, b'FIRST'); inst.install('b', MODEL, b'SECOND-LONGER'); inst.install('c', BASE, b'OTHER-SUIT')
    t = Toc.open(ad)
    assert t.read(t.find(MODEL), ad) == b'SECOND-LONGER' and t.read(t.find(BASE), ad) == b'OTHER-SUIT'
    assert sorted(m['id'] for m in inst.installed()) == ['b', 'c']
    assert sorted(os.listdir(os.path.join(ad, 'mods'))) == ['modswap_b', 'modswap_c'], 'the replaced mod\'s file must be removed'


def test_uninstall_one_leaves_the_others():
    g, blobs, ad = game(); inst = I.Installer(g); inst.install('a', MODEL, b'AAAA'); inst.install('c', BASE, b'CCCC')
    inst.uninstall('a'); t = Toc.open(ad)
    assert t.read(t.find(MODEL), ad) == blobs['model'] and t.read(t.find(BASE), ad) == b'CCCC' and [m['id'] for m in inst.installed()] == ['c']


def test_restore_puts_the_game_back_byte_for_byte():
    g, blobs, ad = game(); orig = sha(os.path.join(ad, 'toc')); inst = I.Installer(g)
    inst.install('a', MODEL, b'AAAA'); inst.install('c', BASE, b'CCCC'); assert sha(os.path.join(ad, 'toc')) != orig
    inst.restore(); assert sha(os.path.join(ad, 'toc')) == orig and inst.installed() == [] and os.listdir(os.path.join(ad, 'mods')) == []
    inst.install('again', MODEL, b'ZZ'); assert Toc.open(ad).read(Toc.open(ad).find(MODEL), ad) == b'ZZ', 'installing again after a restore works'


def test_a_mod_of_the_earlier_session_in_the_toc_is_replaced_not_stacked():
    g, ids, blobs = fake_game(with_bak=True); ad = os.path.join(g, 'asset_archive')                      # toc.BAK = original, toc = patched by "another tool"
    before = Toc.open(ad); assert before.archive_name(before.find(MODEL)).startswith('mods\\')
    inst = I.Installer(g); inst.install('mine', MODEL, b'MINE'); t = Toc.open(ad)
    assert t.read(t.find(MODEL), ad) == b'MINE' and len(t.archives) == len(Toc(open(os.path.join(ad, 'toc.BAK'), 'rb').read()).archives) + 1


def test_clear_errors():
    d = tempfile.mkdtemp()
    try: I.Installer(d); raise AssertionError('no toc')
    except ValueError as e: assert 'Spider-Man' in str(e)
    g, blobs, ad = game(); inst = I.Installer(g)
    try: inst.install('x', 'no/such/asset.model', b'x'); raise AssertionError('missing target')
    except KeyError as e: assert 'no asset' in str(e)
    inst.install('a', MODEL, b'A'); os.remove(os.path.join(ad, 'toc.BAK'))
    try: inst.install('b', BASE, b'B'); raise AssertionError('lost backup')
    except ValueError as e: assert 'toc.BAK is missing' in str(e)


def test_suit_probe():
    g, blobs, ad = game(); t = Toc.open(ad); assert I.find_suits(t) == ['classic', 'base']
    assert I.suit_model_path('noir') == 'characters/hero/hero_spiderman_noir/hero_spiderman_noir.model'


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
