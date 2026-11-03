"""One unreadable character must not make the whole game 'unreadable': the mesh layout falls back to what the game's other characters (or an earlier success) show.
python tests/test_game_format.py"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from types import SimpleNamespace as NS
from modswap import project as PRJ
from modswap.ue4 import autoprofile

FMT_A = dict(exp_idx=1, rtmask=False)


def fake_detect(ua, ue):
    """stand-in for the real trial parse: files starting with GOOD parse (the layout is in the file), anything else does not"""
    if ua.startswith(b'GOOD'): return json.loads(ua[4:].decode())
    raise AssertionError('cloth mapping data present')


def asset(path, role=''): return NS(path=path, role=role, name=path.rsplit('/', 1)[-1], folder='x')
def family(key, *assets): return NS(key=key, label=key, assets=list(assets))


def project(files, families, scan_calls):
    d = tempfile.mkdtemp(prefix='ms_proj_'); orig = os.path.join(d, 'orig'); os.makedirs(orig)
    for rel, content in files.items():
        os.makedirs(os.path.dirname(os.path.join(orig, rel + '.uasset')), exist_ok=True)
        open(os.path.join(orig, rel + '.uasset'), 'wb').write(content); open(os.path.join(orig, rel + '.uexp'), 'wb').write(b'x')
    P = PRJ.Project.__new__(PRJ.Project); P.orig = orig; P.dir = d; P.game = NS(name='Test Game')
    P.extract = lambda *a, **k: None
    def scan(log=print): scan_calls.append(1); return dict(characters=families)
    P.scan = scan; P._main_pak = lambda: (_ for _ in ()).throw(RuntimeError('no pak'))
    return P


def run(P, fam, logs):
    PRJ.detect_sk_format = fake_detect; autoprofile.make_profile = lambda *a, **k: dict(sk_format=a[2], targets=[])
    return P.make_profile(fam, dict(targets=[fam.assets[0].path], hide=[], keep=[]), log=logs.append)


GOOD = b'GOOD' + json.dumps(FMT_A).encode()
BAD = b'cloth'


def test_own_files_readable():
    calls = []; fam = family('A', asset('G/Content/Chars/A/SK_A')); P = project({'G/Content/Chars/A/SK_A': GOOD}, [fam], calls)
    prof = run(P, fam, []); assert prof['sk_format'] == FMT_A and not calls
    assert P._cached_format() == FMT_A                                    # remembered for the next character that cannot be read


def test_unreadable_character_uses_the_games_other_characters():
    calls = []; bad = family('Bad', asset('G/Content/Chars/Bad/SK_Bad')); ok = family('Ok', asset('G/Content/Chars/Ok/SK_Ok'))
    P = project({'G/Content/Chars/Bad/SK_Bad': BAD, 'G/Content/Chars/Ok/SK_Ok': GOOD}, [bad, ok], calls); logs = []
    prof = run(P, bad, logs)
    assert prof['sk_format'] == FMT_A and calls and any('other characters' in l for l in logs), logs


def test_earlier_success_is_used_without_rescanning():
    calls = []; bad = family('Bad', asset('G/Content/Chars/Bad/SK_Bad')); P = project({'G/Content/Chars/Bad/SK_Bad': BAD}, [bad], calls)
    json.dump(dict(ver=1, fmt=FMT_A), open(P._format_file(), 'w'))
    prof = run(P, bad, []); assert prof['sk_format'] == FMT_A and not calls, 'the cached layout must be used before looking at other characters'


def test_pieces_are_not_used_to_learn_the_layout():
    calls = []; bad = family('Bad', asset('G/Content/Chars/Bad/SK_Bad')); gore = family('Gore', asset('G/Content/Gore/SK_Gore', role='piece'))
    P = project({'G/Content/Chars/Bad/SK_Bad': BAD, 'G/Content/Gore/SK_Gore': GOOD}, [bad, gore], calls)
    try: run(P, bad, []); raise AssertionError('only a gore piece parsed: the game should still count as unreadable')
    except RuntimeError as e: assert 'mesh layout' in str(e)


def test_nothing_readable_anywhere_still_gives_the_report_error():
    calls = []; bad = family('Bad', asset('G/Content/Chars/Bad/SK_Bad')); b2 = family('B2', asset('G/Content/Chars/B2/SK_B2'))
    P = project({'G/Content/Chars/Bad/SK_Bad': BAD, 'G/Content/Chars/B2/SK_B2': BAD}, [bad, b2], calls)
    try: run(P, bad, []); raise AssertionError('should fail')
    except RuntimeError as e: assert 'could not understand the mesh layout of G/Content/Chars/Bad/SK_Bad' in str(e) and 'report:' in str(e), str(e)


def test_corrupt_cache_is_ignored():
    calls = []; bad = family('Bad', asset('G/Content/Chars/Bad/SK_Bad')); ok = family('Ok', asset('G/Content/Chars/Ok/SK_Ok'))
    P = project({'G/Content/Chars/Bad/SK_Bad': BAD, 'G/Content/Chars/Ok/SK_Ok': GOOD}, [bad, ok], calls); open(P._format_file(), 'w').write('{not json')
    assert run(P, bad, [])['sk_format'] == FMT_A and calls


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
