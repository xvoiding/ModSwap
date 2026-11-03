"""python -m modswap diagnose --model my.fbx|MODEL_FOLDER [--textures FOLDER] [--out report_folder]

Given a FOLDER it loads the files the way the app does when you drop them in (everything copied side by side into one folder). Besides the report it draws the model with its texture itself
(preview_front.png / preview_back.png, flat shading, no app viewer involved): if that picture looks right and the app's viewer looks wrong, the problem is in the viewer, not in the model data.

Loads a model exactly like the app does and checks, material by material, that every vertex finds the right colour in the texture atlas the viewer / the builds use. Writes
diagnose_report.txt plus atlas_1024.png (the atlas with each material's cell outlined) and one preview_<material>.png per material (the picture it was given)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from . import atlas
from .modelio import load_model


def sample(im, uv):
    a = np.asarray(im.convert('RGB')); h, w = a.shape[:2]; u = np.mod(uv[:, 0], 1.0); v = np.mod(uv[:, 1], 1.0)
    return a[np.minimum((v * h).astype(int), h - 1), np.minimum((u * w).astype(int), w - 1)]


def find_model(folder):
    """the model file inside a folder (any depth): fbx first, then glb / gltf / obj ... ; among several of one kind the biggest"""
    from .modelio import MODEL_EXT
    order = ('.fbx', '.glb', '.gltf', '.obj', '.dae', '.vrm', '.blend', '.ply', '.stl', '.3mf', '.off'); found = []
    for dp, dn, fs in os.walk(folder):
        for f in fs:
            e = os.path.splitext(f)[1].lower()
            if e in MODEL_EXT: found.append((order.index(e) if e in order else 99, -os.path.getsize(os.path.join(dp, f)), os.path.join(dp, f)))
    if not found: raise SystemExit('no model file (.fbx .glb .obj ...) found inside %s' % folder)
    return sorted(found)[0][2]


def render(m, atl, uv2, axis_view='front', px=640):
    """a plain software render: orthographic, painter's algorithm (far triangles first), every pixel takes its colour from the atlas through the triangle's uvs"""
    up, depth = ({'+Y': (1, 2), '-Y': (1, 2), '+Z': (2, 1), '-Z': (2, 1)}).get(m.up, (1, 2)); right = 0
    P = np.asarray(m.pos, np.float64); sx = P[:, right] * (1 if axis_view == 'front' else -1); sy = P[:, up]; dz = P[:, depth] * (1 if axis_view == 'front' else -1)
    w = np.ptp(sx) or 1; h = np.ptp(sy) or 1; sc = 0.92 * min(px / w, px / h); X = (sx - (sx.max() + sx.min()) / 2) * sc + px / 2; Y = px / 2 - (sy - (sy.max() + sy.min()) / 2) * sc
    img = np.zeros((px, px, 3), np.uint8); img[:] = (24, 24, 28); S = atl.shape[0]; order = np.argsort(dz[m.tris].mean(1))
    for t in order:
        a, b, c = m.tris[t]; x0, x1 = int(max(0, min(X[[a, b, c]]))), int(min(px - 1, max(X[[a, b, c]]) + 1)); y0, y1 = int(max(0, min(Y[[a, b, c]]))), int(min(px - 1, max(Y[[a, b, c]]) + 1))
        if x1 <= x0 or y1 <= y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5); d = (Y[b] - Y[c]) * (X[a] - X[c]) + (X[c] - X[b]) * (Y[a] - Y[c])
        if abs(d) < 1e-9: continue
        l1 = ((Y[b] - Y[c]) * (gx - X[c]) + (X[c] - X[b]) * (gy - Y[c])) / d; l2 = ((Y[c] - Y[a]) * (gx - X[c]) + (X[a] - X[c]) * (gy - Y[c])) / d; l3 = 1 - l1 - l2; k = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not k.any(): continue
        u = l1[k] * uv2[a, 0] + l2[k] * uv2[b, 0] + l3[k] * uv2[c, 0]; v = l1[k] * uv2[a, 1] + l2[k] * uv2[b, 1] + l3[k] * uv2[c, 1]
        img[(gy[k] - 0.5).astype(int), (gx[k] - 0.5).astype(int)] = atl[np.clip((v * S).astype(int), 0, S - 1), np.clip((u * S).astype(int), 0, S - 1)]
    return Image.fromarray(img)


ORIENT = [('as is', lambda u, v: (u, v)), ('flipped vertically', lambda u, v: (u, 1 - v)), ('flipped horizontally', lambda u, v: (1 - u, v)), ('turned 180', lambda u, v: (1 - u, 1 - v)),
          ('axes swapped', lambda u, v: (v, u)), ('turned 90', lambda u, v: (1 - v, u)), ('turned 270', lambda u, v: (v, 1 - u)), ('swapped + turned 180', lambda u, v: (1 - v, 1 - u))]


def orientation_sheet(m, imgs, out, px=420):
    """the model drawn with its picture in each of the 8 orientations (a picture that is flipped / turned relative to its uvs is the commonest reason a model looks 'scrambled'), on one sheet"""
    from PIL import ImageFont
    tiles = []
    for name, f in ORIENT:
        uv = m.uv.copy(); u, v = f(uv[:, 0], uv[:, 1]); uv[:, 0], uv[:, 1] = u, v
        atl, cells = atlas.pack(imgs, uv, m.vert_mat, size=1024); uv2 = atlas.remap_uv(uv, m.vert_mat, cells, 1024)
        t = render(m, atl, uv2, 'front', px).convert('RGB'); d = ImageDraw.Draw(t); d.rectangle([0, 0, px, 22], fill=(0, 0, 0)); d.text((6, 5), '%d: %s' % (len(tiles) + 1, name), fill=(255, 255, 0)); tiles.append(t)
    sheet = Image.new('RGB', (px * 4, px * 2))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 4) * px, (i // 4) * px))
    sheet.save(os.path.join(out, 'orientations.png'))


def flatten(folder):
    """copy the model and every picture of a folder tree side by side into one temp folder, like dropping them all into the app"""
    import shutil, tempfile
    from .modelio import MODEL_EXT, IMAGE_EXT
    d = tempfile.mkdtemp(prefix='modswap_diag_'); total = 0; seen = set()
    for dp, dn, fs in os.walk(folder):
        for f in sorted(fs):
            e = os.path.splitext(f)[1].lower(); p = os.path.join(dp, f)
            if (e in MODEL_EXT or e in IMAGE_EXT or e == '.mtl') and f not in seen and total < 400 * 1024 * 1024:
                shutil.copy2(p, os.path.join(d, f)); seen.add(f); total += os.path.getsize(p)
    return d


def run(model_path, texture_dir=None, out=None, log=print):
    out = out or os.getcwd(); os.makedirs(out, exist_ok=True); L = []
    def say(s=''): L.append(s); log(s)
    if os.path.isdir(model_path):
        folder = model_path; found = find_model(folder); flat = flatten(folder); model_path = os.path.join(flat, os.path.basename(found)); texture_dir = flat
        say('model file found: %s' % found); say('files copied side by side (like dropping them into the app): %s' % ', '.join(sorted(os.listdir(flat))[:12]))
    if model_path.lower().endswith('.obj'):
        for l in open(model_path, errors='ignore'):
            if l.startswith(('mtllib', 'usemtl', 'o ', 'g ')) and len(L) < 40: say('obj: ' + l.strip())
        mp = os.path.join(os.path.dirname(model_path), next((l.split(None, 1)[1].strip() for l in open(model_path, errors='ignore') if l.startswith('mtllib')), ''))
        if os.path.isfile(mp):
            for l in open(mp, errors='ignore'):
                if l.strip().lower().startswith(('newmtl', 'map_', 'kd')): say('mtl: ' + l.strip())
    m = load_model(model_path, texture_dir)
    say('model: %s' % model_path); say('vertices %d, triangles %d, materials %d, parts %d, up axis %s' % (len(m.pos), len(m.tris), len(m.mat_names), len(m.part_names), m.up))
    say('UV range: u %.3f .. %.3f, v %.3f .. %.3f  (outside 0..1 means the texture is tiled / mirrored)' % (m.uv[:, 0].min(), m.uv[:, 0].max(), m.uv[:, 1].min(), m.uv[:, 1].max()))
    vm = m.vert_mat; mixed = int((vm[m.tris].min(1) != vm[m.tris].max(1)).sum())
    say('triangles whose corners belong to different materials: %d (must be 0)' % mixed)
    imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in m.images]
    say(); say('%-3s %-28s %-12s %-16s %-9s %-9s %s' % ('#', 'material', 'picture', 'average colour', 'vertices', 'tris', 'uv range of this material'))
    tcount = np.bincount(m.tri_mat, minlength=len(m.mat_names)); vcount = np.bincount(vm, minlength=len(m.mat_names))
    for i, nm in enumerate(m.mat_names):
        im = m.images[i]; avg = tuple(int(x) for x in np.asarray(imgs[i].convert('RGB')).reshape(-1, 3).mean(0)); k = vm == i
        rng = ('u %.2f..%.2f v %.2f..%.2f' % (m.uv[k, 0].min(), m.uv[k, 0].max(), m.uv[k, 1].min(), m.uv[k, 1].max())) if k.any() else '-'
        say('%-3d %-28s %-12s %-16s %-9d %-9d %s' % (i, nm[:28], ('none (grey)' if im is None else '%dx%d' % im.size), str(avg), vcount[i], tcount[i], rng))
        imgs[i].save(os.path.join(out, 'preview_%02d_%s.png' % (i, ''.join(c for c in nm if c.isalnum() or c in '_-')[:30])))
    say(); worst = 0
    for size in (1024, 2048):
        atl, cells = atlas.pack(imgs, m.uv, vm, size=size); uv2 = atlas.remap_uv(m.uv, vm, cells, size); bad_total = 0
        for i in range(len(imgs)):
            k = np.flatnonzero(vm == i)
            if not len(k): continue
            want = sample(imgs[i], m.uv[k]); got = atl[np.minimum((uv2[k, 1] * size).astype(int), size - 1), np.minimum((uv2[k, 0] * size).astype(int), size - 1)]
            err = np.abs(want.astype(int) - got.astype(int)).max(1); bad = int((err > 40).sum()); bad_total += bad
            if bad > 0.02 * len(k): say('  atlas %d: material %d (%s): %d of %d vertices find a DIFFERENT colour in the atlas' % (size, i, m.mat_names[i], bad, len(k)))
        say('atlas %d: %d of %d vertices find a different colour than their own picture (0 is right)' % (size, bad_total, len(m.pos))); worst = max(worst, bad_total)
        if size == 1024:
            for view in ('front', 'back'): render(m, atl, uv2, view).save(os.path.join(out, 'preview_%s.png' % view))
            try: orientation_sheet(m, imgs, out)
            except Exception as e: say('(orientation sheet failed: %r)' % (e,))
            pic = Image.fromarray(atl).convert('RGB'); d = ImageDraw.Draw(pic)
            for i, c in enumerate(cells):
                if c is not None: d.rectangle([c.x, c.y, c.x + c.w, c.y + c.h], outline=(255, 0, 255)); d.text((c.x + 3, c.y + 3), str(i), fill=(255, 255, 0))
            pic.save(os.path.join(out, 'atlas_1024.png'))
    border = max(2, int(0.02 * len(m.pos)))                                                              # (a few vertices on island borders blend two colours when the picture is shrunk: normal)
    say(); say('verdict: ' + ('the atlas is consistent with the model; if the viewer still looks wrong the cause is elsewhere. Look at orientations.png: if one tile looks right, your picture is turned relative to its uvs.' if worst <= border and mixed == 0 else 'the model / atlas disagree: this is the bug'))
    open(os.path.join(out, 'diagnose_report.txt'), 'w', encoding='utf-8').write('\n'.join(L)); return worst, mixed


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument('--model', required=True); ap.add_argument('--textures'); ap.add_argument('--out')
    a = ap.parse_args(argv); run(a.model, a.textures, a.out)
