"""The fit sliders must each do only their own job: turning must not change the lean, and size must not shear after a turn.
Run:  python -m pytest tests/test_fit_sliders.py   (or just  python tests/test_fit_sliders.py)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap import skin

CX, CY, Z0, HH = 3.0, -2.0, 0.0, 180.0


def person():
    """a stick 'person': feet, pelvis, head on the vertical axis, plus a hand out to the character's left (+X) and a nose in front (+Y)"""
    P = np.array([[CX, CY, Z0], [CX, CY, 90.0], [CX, CY, 170.0], [CX + 60, CY, 140.0], [CX, CY + 12, 168.0]], float)
    return P, np.tile([0, 1.0, 0], (len(P), 1))


def lean_from_vertical(P):
    """angle (deg) between feet->head and the vertical, and the compass direction of that lean"""
    v = P[2] - P[0]; ang = np.degrees(np.arccos(v[2] / np.linalg.norm(v)))
    return ang


def run(adj):
    P, N = person(); return skin.apply_adjust(P, N, CX, CY, Z0, HH, adj)


def test_turn_does_not_change_lean():
    for pitch, roll in ((20, 0), (0, 15), (25, 10)):
        base = lean_from_vertical(run(dict(pitch=pitch, roll=roll))[0])
        for yaw in (30, 90, 180, -120):
            got = lean_from_vertical(run(dict(pitch=pitch, roll=roll, yaw=yaw))[0])
            assert abs(got - base) < 1e-6, ('turning changed the lean', pitch, roll, yaw, base, got)


def test_lean_direction_follows_the_model_when_turned():
    """'lean forward' must lean toward the model's OWN front (where its nose points) at every turn angle, and 'lean left' toward its own left.
    (If the tilt is done around fixed world axes after the turn, a turned model leans sideways instead.)"""
    unit = lambda v: v / np.linalg.norm(v)
    for yaw in (0, 40, 90, 180, -75):
        P, _ = run(dict(pitch=20, yaw=yaw))
        fwd = unit(P[4, :2] - P[2, :2])                        # nose is in front of the head: the model's own forward, in the world
        lean = unit(P[2, :2] - P[0, :2])                       # which way the head leans away from the feet
        assert np.dot(fwd, lean) > 1 - 1e-9, ('forward lean went sideways after turning', yaw, np.dot(fwd, lean))
        P, _ = run(dict(roll=15, yaw=yaw))
        left = np.array([-fwd[1], fwd[0]])                     # the model's own left (X = left, Y = forward in the character frame)
        lean = unit(P[2, :2] - P[0, :2])
        assert np.dot(left, lean) > 1 - 1e-9 or np.dot(-left, lean) > 1 - 1e-9, ('side lean went off-axis after turning', yaw)


def test_size_does_not_shear_after_turn():
    """width x2 must double how far the hand sticks out sideways (along the MODEL's own width axis) and leave how far the nose sticks out
    front-to-back alone, at ANY turn angle. If the stretch is applied after the turn it skews instead."""
    side = lambda P: np.hypot(*(P[3, :2] - P[1, :2]))          # hand, sideways reach (60 cm to start with)
    front = lambda P: np.hypot(*(P[4, :2] - P[1, :2]))         # nose, front reach (12 cm to start with)
    for yaw in (0, 35, 90, 200):
        P, _ = run(dict(width=2.0, yaw=yaw))
        assert abs(side(P) - 120.0) < 1e-6, ('width did not double the sideways reach', yaw, side(P))
        assert abs(front(P) - 12.0) < 1e-6, ('width changed the front-to-back depth (sheared)', yaw, front(P))
        assert abs(lean_from_vertical(P)) < 1e-6              # a width change must not lean the model
    for yaw in (0, 35, 90, 200):
        P, _ = run(dict(depth=3.0, yaw=yaw))
        assert abs(front(P) - 36.0) < 1e-6 and abs(side(P) - 60.0) < 1e-6, ('depth sheared', yaw, front(P), side(P))


def test_height_does_not_change_lean():
    base = lean_from_vertical(run(dict(pitch=20))[0])
    for h in (0.5, 1.7):
        assert abs(lean_from_vertical(run(dict(pitch=20, height=h))[0]) - base) < 1e-6


def test_nudge_only_moves():
    P0, _ = run(dict(pitch=10, yaw=40)); P1, _ = run(dict(pitch=10, yaw=40, dx=5, dy=-3, dz=2))
    assert np.allclose(P1 - P0, [5, -3, 2])


def test_identity():
    P, N = person(); P2, N2 = skin.apply_adjust(P, N, CX, CY, Z0, HH, dict(width=1, depth=1, height=1))
    assert np.allclose(P, P2) and np.allclose(N, N2)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
