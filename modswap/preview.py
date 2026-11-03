"""Fit preview: draw the original character's outline with your model rigged on top of it, from the front, side and above.

Everything is drawn in the *character frame*: X = character's left, Y = forward (the way the original faces), Z = up.
That is the same frame skin.autorig works in, so what you see is what gets written into the game files.
"""
import io, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import skin
from .ue4.rig import read_mesh

CYAN = (0, 225, 255); ORANGE = (255, 150, 70); GREEN = (80, 230, 140)

# view name -> (screen_x, screen_y, depth, toward_viewer) as functions of canonical (X left, Y forward, Z up)
VIEWS = {
    'front': (lambda p: p[:, 0], lambda p: -p[:, 2], lambda p: p[:, 1], np.array([0, 1.0, 0])),     # you look at its face; its left is on your right
    'side':  (lambda p: p[:, 1], lambda p: -p[:, 2], lambda p: -p[:, 0], np.array([-1.0, 0, 0])),   # from its right side, it faces right
    'top':   (lambda p: -p[:, 0], lambda p: -p[:, 1], lambda p: p[:, 2], np.array([0, 0, 1.0])),    # from above, it faces up
}


def load_original(orig_dir, mesh_rel, sk_format, rig):
    """Original mesh as (positions, triangles) in the character frame."""
    import os
    pos, tris = read_mesh(os.path.join(orig_dir, mesh_rel), **sk_format)
    C = skin.rig_frame(rig)
    return pos @ C.T, tris


def fit_model(model, rig, up='+Y', forward=None, scale=1.0, adjust=None, edits=None):
    """Run the auto-rig and return (positions, normals, triangles) of your model in the character frame + the rig info.
    info['vgroup'] = which auto body part (edit.AUTO_NAMES) each vertex belongs to."""
    from . import edit
    from .ue4.swap import is_humanoid, generic_fit
    if is_humanoid(rig): r = skin.autorig(model.pos, model.nrm, rig, up=up, forward=forward, scale_mult=scale, adjust=adjust, edits=edits, tris=model.tris)
    else: r = generic_fit(None, model, rig, up=up, forward=forward, scale_mult=scale, adjust=adjust)
    C = skin.rig_frame(rig)
    pos, nrm = r['pos'] @ C.T, r['nrm'] @ C.T
    tris = edit.keep_triangles(model.tris, r['hidden'])
    r['info']['vgroup'] = r['vgroup']; r['info']['piv'] = r['piv']
    return pos, nrm, tris, r['info']


def _layout(view, clouds, size, pad=18):
    sx, sy = VIEWS[view][0], VIEWS[view][1]
    allp = np.concatenate(clouds)
    x, y = sx(allp), sy(allp)
    w, h = size
    s = min((w - 2 * pad) / max(x.max() - x.min(), 1e-6), (h - 2 * pad) / max(y.max() - y.min(), 1e-6))
    ox = w / 2 - (x.max() + x.min()) / 2 * s; oy = h / 2 - (y.max() + y.min()) / 2 * s
    return lambda p: np.stack([sx(p) * s + ox, sy(p) * s + oy], 1)


def _render(view, orig, new, size):
    (op, ot), (npos, nnrm, nt) = orig, new
    to_px = _layout(view, [op, npos], size)
    depth = VIEWS[view][2]; toward = VIEWS[view][3]
    w, h = size
    img = Image.new('RGBA', size, (16, 18, 22, 255)); d = ImageDraw.Draw(img)
    # feet line + centre line
    zb = to_px(np.array([[0, 0, op[:, 2].min()]]))[0]
    d.line([(8, zb[1]), (w - 8, zb[1])], fill=(60, 66, 78, 255), width=1)
    # original: faint fill + outline
    m = Image.new('L', size, 0); md = ImageDraw.Draw(m)
    q = to_px(op)
    for t in ot: md.polygon([tuple(q[t[0]]), tuple(q[t[1]]), tuple(q[t[2]])], fill=255)
    fill = Image.new('RGBA', size, CYAN + (0,)); fill.putalpha(m.point(lambda v: 40 if v else 0)); img = Image.alpha_composite(img, fill)
    # new model, shaded, painter's order
    q2 = to_px(npos); fn = np.cross(npos[nt[:, 1]] - npos[nt[:, 0]], npos[nt[:, 2]] - npos[nt[:, 0]])
    vn = nnrm[nt].sum(1)                                   # orient face normals with the vertex normals
    fn = fn * np.sign((fn * vn).sum(1, keepdims=True) + 1e-12)
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    light = 0.30 + 0.70 * np.clip(fn @ toward, 0, 1)
    dep = depth(npos)[nt].mean(1)
    layer = Image.new('RGBA', size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for i in np.argsort(dep):
        t = nt[i]; c = tuple(int(v * light[i]) for v in ORANGE) + (225,)
        ld.polygon([tuple(q2[t[0]]), tuple(q2[t[1]]), tuple(q2[t[2]])], fill=c)
    img = Image.alpha_composite(img, layer)
    edge = m.filter(ImageFilter.MaxFilter(3)); inner = m.filter(ImageFilter.MinFilter(3))
    ring = np.array(edge, np.int16) - np.array(inner, np.int16)
    ol = np.zeros((h, w, 4), np.uint8); ol[ring > 0] = CYAN + (255,)
    img = Image.alpha_composite(img, Image.fromarray(ol, 'RGBA'))
    d = ImageDraw.Draw(img)
    d.text((8, 6), view.upper(), fill=(150, 160, 175, 255))
    if view == 'top':       # which way the original faces: arrow up
        d.line([(w - 22, 40), (w - 22, 14)], fill=GREEN + (255,), width=2); d.polygon([(w - 22, 8), (w - 28, 18), (w - 16, 18)], fill=GREEN + (255,))
        d.text((w - 56, 44), 'faces', fill=GREEN + (255,))
    if view == 'side':
        d.line([(w - 44, 20), (w - 14, 20)], fill=GREEN + (255,), width=2); d.polygon([(w - 8, 20), (w - 18, 14), (w - 18, 26)], fill=GREEN + (255,))
        d.text((w - 56, 28), 'faces', fill=GREEN + (255,))
    return img


def render_all(orig, new, size=(300, 460)):
    """-> {'front': b64png, 'side': ..., 'top': ...}"""
    out = {}
    for v in ('front', 'side', 'top'):
        sz = (size[0], size[0]) if v == 'top' else size
        buf = io.BytesIO(); _render(v, orig, new, sz).convert('RGB').save(buf, 'PNG', optimize=True)
        out[v] = base64.b64encode(buf.getvalue()).decode()
    return out
