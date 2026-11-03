"""The sample collector reads a game folder and writes a small zip: file list, type summary, archive heads/tails, a few whole small files; it respects its size budget and never changes the game.   python tests/test_collect_samples.py"""
import os, sys, zipfile, tempfile, hashlib, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import collect_samples as C


def fake_game():
    root = tempfile.mkdtemp(prefix='ms_game_'); game = os.path.join(root, 'steamapps', 'common', 'Fake Game'); os.makedirs(os.path.join(game, 'data'))
    open(os.path.join(root, 'steamapps', 'appmanifest_123.acf'), 'w').write('"AppState"\n{\n "appid" "123"\n "installdir" "Fake Game"\n "buildid" "9999"\n}\n')
    big = bytes(range(256)) * (6 * 4096)                               # 6 MB archive: header + tail matter
    open(os.path.join(game, 'data', 'a.pac'), 'wb').write(b'PACx' + big)
    open(os.path.join(game, 'data', 'b.pac'), 'wb').write(b'PACx' + big[:4_000_000])
    for i in range(60): open(os.path.join(game, 'data', 'f%02d.dds' % i), 'wb').write(b'DDS ' + bytes([i]) * 1000)
    os.makedirs(os.path.join(game, 'asset_archive')); open(os.path.join(game, 'asset_archive', 'toc'), 'wb').write(b'TOC!' + bytes(range(256)) * 5000)
    open(os.path.join(game, 'Game.exe'), 'wb').write(b'MZ' + b'\0' * 5000)
    return game


def hashes(game):
    h = {}
    for d, _, fs in os.walk(game):
        for f in fs: h[os.path.join(d, f)] = hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest()
    return h


def test_collects_the_right_things_and_changes_nothing():
    game = fake_game(); before = hashes(game); out = os.path.join(tempfile.mkdtemp(), 'sub', 's.zip')
    C.collect(game, out, 60, log=lambda *a: None)
    z = zipfile.ZipFile(out); names = z.namelist()
    assert 'tree.txt' in names and 'extensions.txt' in names and 'manifest.txt' in names
    assert b'"buildid" "9999"' in z.read('manifest.txt')
    tree = z.read('tree.txt').decode(); assert 'data/a.pac' in tree and 'Game.exe' in tree and tree.count('.dds') == 60
    ext = z.read('extensions.txt').decode(); assert '.pac' in ext and '.dds' in ext
    heads = [n for n in names if n.startswith('heads/') and n.endswith('.head')]; tails = [n for n in names if n.endswith('.tail')]
    assert len(heads) == 2 and len(tails) >= 1, (heads, tails)
    a_head = z.read([n for n in heads if 'a.pac' in n][0]); assert a_head[:4] == b'PACx' and len(a_head) == C.HEAD
    small = [n for n in names if n.startswith('small/')]; assert 20 <= len([n for n in small if '.dds' in n]) <= C.PER_EXT + 1 and any('Game.exe' in n for n in small)
    idx = [n for n in names if n.startswith('index/')]; assert len(idx) == 1 and z.read(idx[0])[:4] == b'TOC!' and len(z.read(idx[0])) == 4 + 256 * 5000, idx
    assert hashes(game) == before, 'the collector must never modify the game folder'


def test_include_copies_named_files_whole_and_first():
    game = fake_game(); out = os.path.join(tempfile.mkdtemp(), 'inc.zip'); logs = []
    C.collect(game, out, 8, log=logs.append, include=['data/a.pac', 'DATA/*.DDS', 'nothing/here.bin'])          # patterns are case-insensitive; 8 MB budget
    z = zipfile.ZipFile(out); whole = [n for n in z.namelist() if n.startswith('whole/')]
    assert 'whole/data/a.pac' in whole and len([n for n in whole if n.endswith('.dds')]) == 60, whole[:5]
    assert z.read('whole/data/a.pac') == open(os.path.join(game, 'data', 'a.pac'), 'rb').read(), 'must be byte for byte'
    assert any('no file matches' in l and 'nothing/here.bin' in l for l in logs)
    # included files come first: a budget that only fits one of the big archives still gets the one that was asked for
    out2 = os.path.join(tempfile.mkdtemp(), 'inc2.zip'); logs2 = []
    C.collect(game, out2, 6.5, log=logs2.append, include=['data/a.pac', 'data/b.pac'])
    names2 = zipfile.ZipFile(out2).namelist(); assert 'whole/data/a.pac' in names2 and 'whole/data/b.pac' not in names2 and any('does not fit' in l for l in logs2)


def test_only_mode_skips_heads_and_small_files():
    game = fake_game(); out = os.path.join(tempfile.mkdtemp(), 'only.zip')
    C.collect(game, out, 20, log=lambda *a: None, include=['data/b.pac'], only=True)
    names = zipfile.ZipFile(out).namelist()
    assert 'whole/data/b.pac' in names and 'tree.txt' in names
    assert not [n for n in names if n.startswith(('heads/', 'small/'))], names


def test_respects_the_budget():
    game = fake_game(); out = os.path.join(tempfile.mkdtemp(), 's.zip')
    C.collect(game, out, 0.2, log=lambda *a: None)                   # 0.2 MB budget
    z = zipfile.ZipFile(out); total = sum(i.file_size for i in z.infolist())
    assert total <= 0.2 * 1024 * 1024 + 1, total
    assert 'tree.txt' in z.namelist()


def test_command_line_runs():
    game = fake_game(); out = os.path.join(tempfile.mkdtemp(), 'cli.zip')
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'collect_samples.py'), game, out, '--budget', '8', '--include', 'data/b.pac'], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.getsize(out) > 0 and 'zip written' in r.stdout, r.stderr
    assert 'whole/data/b.pac' in zipfile.ZipFile(out).namelist()


def test_missing_folder_is_a_clear_error():
    try: C.collect('/no/such/folder', '/tmp/x.zip', 1, log=lambda *a: None); raise AssertionError('should fail')
    except SystemExit as e: assert 'not a folder' in str(e)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
