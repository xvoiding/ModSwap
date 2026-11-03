"""Fit your model onto a Unity model's footprint (rigid, no skinning): everything is done in the 'character frame' the app's viewer uses
(X = left, Y = forward, Z = up, centimetres) and converted to Unity's frame (x right, y up, z forward, metres) at the end."""
import numpy as np
from .. import skin
from . import patch


def to_char(p, k=1.0):     # unity local (x right, y up, z fwd), metres -> viewer frame cm.  k = unity units per metre (some games author in cm: k = 100)
    p = np.asarray(p, np.float64); return np.stack([-p[..., 0], p[..., 2], p[..., 1]], -1) * 100.0 / k


def to_unity(p, k=1.0):
    p = np.asarray(p, np.float64) / 100.0 * k; return np.stack([-p[..., 0], p[..., 2], p[..., 1]], -1)


def _rot(yaw, pitch, roll):
    y, p, r = np.radians([yaw, pitch, roll])
    Rz = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    Ry = np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]])
    return Rz @ Rx @ Ry


def fit_static(model, lo, hi, up='+Y', forward=None, scale=1.0, adjust=None):
    """lo/hi: footprint of the original in the viewer frame (cm). Returns (pos, nrm, info) in the viewer frame (cm)."""
    adj = dict(width=1, height=1, depth=1, yaw=0, pitch=0, roll=0, dx=0, dy=0, dz=0); adj.update(adjust or {})
    forward = forward or skin.detect_forward(model.pos, up)
    B = skin.axis_basis(up, forward)
    P = model.pos @ B.T; N = model.nrm @ B.T
    size = np.maximum(P.max(0) - P.min(0), 1e-6); osz = np.maximum(np.asarray(hi) - np.asarray(lo), 1e-6)
    s = float(min(osz / size)) * float(scale)                                # the biggest it can be and still sit inside the original
    P = P * s
    P = P * np.array([adj['width'], adj['depth'], adj['height']])           # X = width, Y = depth (length), Z = height
    c0 = np.array([(P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2, P[:, 2].min()])
    P = P - c0
    R = _rot(adj['yaw'], adj['pitch'], adj['roll'])
    pv = np.array([0, 0, (P[:, 2].max()) / 2])
    P = (P - pv) @ R.T + pv; N = N @ R.T
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    base = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    P = P + base + np.array([adj['dx'], adj['dy'], adj['dz']])
    return P, N, dict(forward=forward, up=up, scale=s, pivot=[float(base[0]), float(base[1]), float(base[2])])


def unity_arrays(pos_c, nrm_c, tris, k=1.0):
    """viewer frame -> unity local arrays with outward winding"""
    P = to_unity(pos_c, k).astype(np.float32)
    Nn = np.stack([-nrm_c[:, 0], nrm_c[:, 2], nrm_c[:, 1]], 1).astype(np.float32)
    return P, Nn, patch.to_unity_tris(P, np.asarray(tris, np.int64))
