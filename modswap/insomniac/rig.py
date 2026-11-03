"""The rig description ModSwap's auto-rig (skin.autorig) needs, built from a Spider-Man .model.

Spider-Man's frame: x = character's left, y up, z forward (metres). The auto-rig's game frame: X left, Y forward, Z up. `rig_from_model` returns the rig in the auto-rig's
frame; `to_model_space` / `from_model_space` convert points between the two (a swap of y and z, so handedness flips: triangle winding flips with it)."""
import numpy as np


def _qm(x, y, z, w):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def joint_world(model):
    """(J,3) bind-pose joint positions in the model's frame, from the stored local scale / rotation / position and the parent links"""
    js = model.joints(); sc, q, p, _ = model.joint_transforms(); n = len(js); world = [None] * n

    def get(i, depth=0):
        if world[i] is not None: return world[i]
        if depth > 400: raise ValueError('joint parents form a loop')
        L = np.eye(4); L[:3, :3] = _qm(*q[i]) * sc[i]; L[:3, 3] = p[i]
        world[i] = L if js[i].parent < 0 else get(js[i].parent, depth + 1) @ L
        return world[i]
    return np.array([get(i)[:3, 3] for i in range(n)])


def to_model_space(p): p = np.asarray(p, float); return p[..., [0, 2, 1]]
from_model_space = to_model_space                               # (x, y, z) <-> (x, z, y): its own inverse


def rig_from_model(model, ref_vertices=None):
    """rig dict for skin.autorig. ref_vertices = the vertices that define the character's height (default: all of the model's)."""
    js = model.joints(); W = from_model_space(joint_world(model))
    P = from_model_space(model.positions() if ref_vertices is None else ref_vertices)
    return dict(names=[j.name for j in js], parent=[j.parent for j in js], head=W.tolist(), bonemap=list(range(len(js))), facing=[0.0, 1.0, 0.0],
                mesh_min=P.min(0).tolist(), mesh_max=P.max(0).tolist(), ref_height=float(P[:, 2].max() - P[:, 2].min()), ref_min_z=float(P[:, 2].min()))
