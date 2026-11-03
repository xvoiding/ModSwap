"""Characters named <Name>_mesh / <Name>_body next to <Name>_Skeleton / <Name>_PhysicsAsset are looked at (and header-verified later).   python tests/test_scan_candidates.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.ue4 import scan as S

EX = ['.uasset', '.uexp']
def files(*names): return {n: ('a.pak', EX) for n in names}
def cands(*names): return [a.name for a in S.candidates(files(*names))[0]]


def test_old_rules_still_work():
    assert cands('G/C/SK_Wally') == ['SK_Wally']
    assert cands('G/C/Hero', 'G/C/Hero_Skeleton') == ['Hero']                      # exact sibling (the 2.8.1 rule)
    assert cands('G/C/Hero', 'G/C/Hero_PhysicsAsset') == ['Hero']


def test_mesh_suffix_next_to_skeleton_is_now_found():
    got = cands('G/Chars/Patrick/Patrick_mesh', 'G/Chars/Patrick/Patrick_Skeleton', 'G/Chars/Sandy/Sandy_body', 'G/Chars/Sandy/Sandy_PhysicsAsset')
    assert sorted(got) == ['Patrick_mesh', 'Sandy_body'], got


def test_things_that_are_not_meshes_stay_out():
    got = cands('G/C/Patrick_mesh', 'G/C/Patrick_Skeleton', 'G/C/Patrick_PhysicsAsset', 'G/C/Patrick_Anim', 'G/C/Rock_mesh')
    assert 'Patrick_Skeleton' not in got and 'Patrick_PhysicsAsset' not in got and 'Patrick_Anim' not in got
    assert 'Rock_mesh' not in got                                                   # no skeleton next to it: not a character


def test_scan_version_bumped_so_old_caches_are_redone():
    assert S.SCAN_VERSION >= 3


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
