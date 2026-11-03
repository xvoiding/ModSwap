"""python -m modswap diagnose --model my.fbx [--textures FOLDER] [--out report_folder]

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


def run(model_path, texture_dir=None, out=None, log=print):
    out = out or os.getcwd(); os.makedirs(out, exist_ok=True); L = []
    def say(s=''): L.append(s); log(s)
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
            pic = Image.fromarray(atl).convert('RGB'); d = ImageDraw.Draw(pic)
            for i, c in enumerate(cells):
                if c is not None: d.rectangle([c.x, c.y, c.x + c.w, c.y + c.h], outline=(255, 0, 255)); d.text((c.x + 3, c.y + 3), str(i), fill=(255, 255, 0))
            pic.save(os.path.join(out, 'atlas_1024.png'))
    say(); say('verdict: ' + ('the atlas is consistent with the model; if the viewer still looks wrong the cause is elsewhere (send this report and a screenshot)' if worst == 0 and mixed == 0 else 'the model / atlas disagree: this is the bug'))
    open(os.path.join(out, 'diagnose_report.txt'), 'w', encoding='utf-8').write('\n'.join(L)); return worst, mixed


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument('--model', required=True); ap.add_argument('--textures'); ap.add_argument('--out')
    a = ap.parse_args(argv); run(a.model, a.textures, a.out)
