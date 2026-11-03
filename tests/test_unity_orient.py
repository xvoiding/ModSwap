"""Unity models whose own vertex data is z-up (a -90 degree turn on their GameObject stands them up in the game) are drawn standing and built back the right way round."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap import skin
from modswap.unity import orient as O, fit as F


def rotx(deg):
    a = np.radians(deg); return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])


def test_a_minus_90_turn_on_the_game_object_is_found_and_snapped():
    q = (-0.70710678, 0, 0, 0.70710678)                                       # unity's -90 degrees about x, scale 100 (a cm-authored fbx)
    R = O.snap(O.polar_rotation(O._quat3(q, (100, 100, 100))))
    assert np.allclose(R, rotx(-90), atol=1e-9) and np.allclose(R @ [0, 0, 1], [0, 1, 0]), R                  # data z becomes up (y)
    assert np.allclose(O.snap(O.polar_rotation(O._quat3((0, 0, 0, 1), (1, 1, 1)))), np.eye(3))
    tilt = O.polar_rotation(rotx(30)); assert np.allclose(O.snap(tilt), tilt)                                  # a deliberate 30 degree tilt is not forced to a 90 degree turn


def test_viewer_and_build_are_inverse_of_each_other_through_rotation_and_mesh_matrix():
    r = np.random.RandomState(0); L = r.randn(50, 3); N = r.randn(50, 3); N /= np.linalg.norm(N, axis=1, keepdims=True)
    R = rotx(-90); M = np.eye(4); M[:3, :3] = rotx(25) * 0.01; M[:3, 3] = [1, 2, 3]                           # the mesh object sits on a child GameObject (scaled 0.01, turned, offset)
    top = (np.c_[L, np.ones(50)] @ M.T)[:, :3]; pos_c = F.to_char(top, 1.0, R)                                  # what the viewer shows
    tris = np.array([[0, 1, 2], [3, 4, 5]]); P, Nn, T = F.unity_arrays(pos_c, np.stack([-(N @ M[:3, :3].T @ R.T)[:, 0], (N @ M[:3, :3].T @ R.T)[:, 2], (N @ M[:3, :3].T @ R.T)[:, 1]], 1), tris, R=R, M=M)
    assert np.abs(P - L).max() < 1e-4, np.abs(P - L).max()                                                         # built back into the mesh's own space
    pos_none = F.to_char(L)                                                                                        # no rotation: unchanged behaviour
    P0, _, _ = F.unity_arrays(pos_none, N, tris); assert np.abs(P0 - L).max() < 1e-4


def test_skeleton_stands_a_z_up_character_up_and_overrides_a_wrong_transform():
    names = ['Hips', 'Spine', 'Neck', 'Head', 'LeftUpperArm', 'RightUpperArm', 'LeftUpLeg', 'RightUpLeg', 'LeftFoot', 'RightFoot']
    H = np.array([[0, 0, 1.0], [0, 0, 1.3], [0, 0, 1.6], [0, 0, 1.75], [0.2, 0, 1.55], [-0.2, 0, 1.55], [0.1, 0, 0.95], [-0.1, 0, 0.95], [0.1, 0, 0.1], [-0.1, 0, 0.1]])     # z-up data
    R = O.from_skeleton(names, H, skin.classify); up = H @ R.T
    assert np.allclose(R @ [0, 0, 1], [0, 1, 0]) and up[3, 1] > up[8, 1] + 1.5 and abs(np.linalg.det(R) - 1) < 1e-9
    assert up[4, 0] < up[5, 0], 'the character\'s left arm comes out on the left (x is right in unity)'
    R2, how = O.choose(np.eye(3), names, H, skin.classify); assert how == 'skeleton' and np.allclose(R2, R)           # transforms say "no turn" but the head is not above the feet
    R3, how = O.choose(rotx(-90), names, H, skin.classify); assert how == 'transforms'                              # the transform already stands it up: kept
    Hy = H[:, [0, 2, 1]] * [1, 1, -1]; assert O.choose(np.eye(3), names, Hy, skin.classify)[1] == 'none needed'      # y-up data is left alone
