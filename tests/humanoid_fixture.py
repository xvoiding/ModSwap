"""A tessellated box-built humanoid (torso, head, two arms, two legs; Y up, facing +Z, T-pose, 1.74 m) with a coloured texture, as a stand-in for a user model."""
import numpy as np
from PIL import Image
from modswap.modelio import Model
def box(lo, hi, uvrect, n=8):
    lo, hi = np.array(lo, float), np.array(hi, float); P = []; Nn = []; UV = []; T = []
    faces = [((1,0,0), [(1,0,0),(1,1,0),(1,1,1),(1,0,1)]), ((-1,0,0), [(0,0,1),(0,1,1),(0,1,0),(0,0,0)]), ((0,1,0), [(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),
             ((0,-1,0), [(0,0,1),(0,0,0),(1,0,0),(1,0,1)]), ((0,0,1), [(0,0,1),(1,0,1),(1,1,1),(0,1,1)]), ((0,0,-1), [(1,0,0),(0,0,0),(0,1,0),(1,1,0)])]
    u0, v0, u1, v1 = uvrect
    for nrm_, corners in faces:
        c = [lo + (hi - lo) * np.array(k) for k in corners]; base = len(P)
        for a in range(n + 1):
            for b in range(n + 1):
                u, v = a / n, b / n
                P.append(c[0] * (1-u) * (1-v) + c[1] * u * (1-v) + c[2] * u * v + c[3] * (1-u) * v); Nn.append(nrm_)
                UV.append((u0 + (u1 - u0) * (0.1 + 0.8 * u), v0 + (v1 - v0) * (0.1 + 0.8 * v)))      # inset: no vertex sits on a cell border
        for a in range(n):
            for b in range(n):
                i = base + a * (n + 1) + b; T += [(i, i + 1, i + n + 2), (i, i + n + 2, i + n + 1)]
    return np.array(P), np.array(Nn, float), np.array(UV), np.array(T)
def humanoid():
    parts = [((-0.18, 0.90, -0.10), (0.18, 1.45, 0.10), (0.0, 0.0, 0.25, 0.25)),            # torso (texture cell 0)
             ((-0.10, 1.48, -0.11), (0.10, 1.74, 0.11), (0.25, 0.0, 0.5, 0.25)),             # head
             ((0.18, 1.33, -0.05), (0.78, 1.45, 0.05), (0.5, 0.0, 0.75, 0.25)),              # left arm (T pose, +x = its left)
             ((-0.78, 1.33, -0.05), (-0.18, 1.45, 0.05), (0.75, 0.0, 1.0, 0.25)),            # right arm
             ((0.02, 0.0, -0.07), (0.17, 0.90, 0.08), (0.0, 0.25, 0.25, 0.5)),               # left leg
             ((-0.17, 0.0, -0.07), (-0.02, 0.90, 0.08), (0.25, 0.25, 0.5, 0.5))]             # right leg
    P, N, UV, T = [], [], [], []
    for lo, hi, rect in parts:
        p, n, uv, t = box(lo, hi, rect); T.append(t + len(sum(P, []) if False else np.concatenate(P) if P else np.zeros((0, 3)))); P.append(p); N.append(n); UV.append(uv)
    img = np.zeros((256, 256, 3), np.uint8); img[:] = (90, 90, 90)
    cols = [(200, 40, 40), (230, 190, 150), (40, 160, 60), (40, 60, 200), (170, 60, 200), (220, 200, 40)]
    for k, ((lo, hi, rect), c) in enumerate(zip(parts, cols)):
        u0, v0, u1, v1 = rect; img[int(v0 * 256):int(v1 * 256), int(u0 * 256):int(u1 * 256)] = c
    pos = np.concatenate(P); tris = np.concatenate(T).astype(np.int32)
    return Model(pos, np.concatenate(N), np.concatenate(UV), tris, np.zeros(len(tris), np.int32), [Image.fromarray(img)], ['mat'], up='+Y', source='procedural')
