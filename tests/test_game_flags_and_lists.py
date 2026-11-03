"""A stale 'supported: false' in games.json must not hide an Unreal game's swapping; mesh packages whose SkeletalMesh is not export 0 are still found;
main characters come first in the list.   python tests/test_game_flags_and_lists.py"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
cfg = tempfile.mkdtemp(prefix='ms_cfg_'); os.environ['XDG_CONFIG_HOME'] = cfg; os.environ['APPDATA'] = cfg
from modswap.games.library import Library, Game
from modswap import server
from modswap.ue4 import scan as S


def test_stale_unsupported_flag_is_ignored():
    p = os.path.join(cfg, 'games.json')
    json.dump({'games': [dict(id='steam-1', name='Just Die Already', root='/x', source='steam', engine='unreal', engine_version='4.25', supported=False),
                         dict(id='steam-2', name='Godot thing', root='/y', source='steam', engine='godot', supported=True)]}, open(p, 'w'))
    lib = Library(p)
    assert lib.games['steam-1'].supported is True and lib.games['steam-2'].supported is False
    assert server._game_json(lib.games['steam-1'])['supported'] is True and server._game_json(lib.games['steam-2'])['supported'] is False


def test_mesh_found_when_it_is_not_export_zero():
    names = ['SkeletalMesh', 'MorphTarget', 'Skeleton', 'Material']
    fake = dict(names=names, exports=[dict(**{'class': -2}), dict(**{'class': -1})],       # export 0 = MorphTarget, export 1 = SkeletalMesh
                imports=[dict(name=(0,), class_name=(0,)), dict(name=(1,), class_name=(1,)), dict(name=(2,), class_name=(2,))])
    fake['imports'] = [dict(name=(0,), class_name=(0,)), dict(name=(1,), class_name=(1,))]; fake['exports'] = [{'class': -2}, {'class': -1}]
    real = S.parse_uasset; S.parse_uasset = lambda b: fake
    try: h = S.read_header(b'')
    finally: S.parse_uasset = real
    assert h and h[0] == 'SkeletalMesh', h


def fam(label, folder, n=1):
    return S.Family(label, label, label, [S.Asset('G/Content/%s/SK_%s%d' % (folder, label, i), 'skeletal', 'SK_%s%d' % (label, i), folder) for i in range(n)])


def test_main_characters_listed_first_props_last():
    order = [f.label for f in sorted([fam('Fish_A', 'Characters/NPC', 6), fam('Rock', 'Models/Props', 9), fam('Spongebob', 'Characters/Main_characters', 1), fam('Boss', 'Characters/Bosses', 2)], key=S._list_order)]
    assert order == ['Spongebob', 'Fish_A', 'Boss', 'Rock'], order


def test_mesh_suffix_dropped_from_label():
    a = S.Asset('G/Content/Characters/Main_characters/Spongebob/Spongebob_mesh', 'skeletal', 'Spongebob_mesh', 'Characters/Main_characters/Spongebob'); a.skeleton = 'Spongebob_mesh_Skeleton'
    assert S.families([a])[0].label.startswith('Spongebob  (') , S.families([a])[0].label


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
