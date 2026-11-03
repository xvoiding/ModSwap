"""Command line for Marvel's Spider-Man Remastered:

  python -m modswap spiderman suits                              which suits this game has
  python -m modswap spiderman slots   --suit classic             the suit's material slots (what texture each part uses)
  python -m modswap spiderman install --suit classic --model my.fbx [--name X] [--dry-run OUT.model]
  python -m modswap spiderman list                               what ModSwap has installed
  python -m modswap spiderman uninstall --id ID                  take one mod out
  python -m modswap spiderman restore                            the game exactly as it was (original index back, mod files removed)

--dir is the game folder (default: the usual Steam place). The game must be closed. Nothing outside asset_archive\\ is touched.
"""
import os, sys, time, hashlib, argparse
from types import SimpleNamespace

DEFAULT_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Marvel's Spider-Man Remastered"


def _game(a):
    d = a.dir or DEFAULT_DIR
    if not os.path.isdir(os.path.join(d, 'asset_archive')): sys.exit('no asset_archive folder in %s: pass --dir "<Spider-Man Remastered folder>"' % d)
    return d


def _guard(d):
    from ..games.running import ensure_closed
    try: ensure_closed(SimpleNamespace(root=d, name="Marvel's Spider-Man Remastered", exe=''))
    except RuntimeError as e: sys.exit(str(e))


def cmd_suits(a):
    from .install import Installer, find_suits
    I = Installer(_game(a)); toc = I.original_toc()
    s = find_suits(toc)
    print('%d suit(s) found in this game:' % len(s)); [print('  ' + x) for x in s]; toc.close()


def _load(I, suit):
    from . import model as M
    from .install import suit_model_path
    toc = I.original_toc(); path = suit_model_path(suit); i = toc.find(path)
    if i is None: sys.exit('this game has no suit "%s" (try: suits)' % suit)
    return toc, path, M.Model(toc.read(i, I.ad))


def cmd_slots(a):
    from . import materials as MT
    I = _install(a); toc, path, orig = _load(I, a.suit)
    rows = MT.slots(orig, toc, I.ad)
    for r in rows: print('slot %2d  %7d tris  %-34s %s' % (r['slot'], r['triangles'], r['shader'].split('/')[-1][:34], ', '.join(t.split('/')[-1] for t in r['textures'][:3])))
    print('slot ModSwap would use: %s' % MT.pick_single_texture_slot(rows, a.suit))
    toc.close()


def _install(a):
    from .install import Installer
    return Installer(_game(a))


def cmd_install(a):
    from ..modelio import load_model
    from . import swap as S, materials as MT
    d = _game(a); I = _install(a)
    if not a.dry_run: _guard(d)
    toc, path, orig = _load(I, a.suit)
    rows = MT.slots(orig, toc, I.ad)
    slot = a.material if a.material is not None else MT.pick_single_texture_slot(rows, a.suit)
    if slot is None: sys.exit('could not find a simple material slot in this suit; run `slots` and pass --material N')
    print('suit %s: all parts go on material slot %d (%s)' % (a.suit, slot, MT.colour_texture(rows, slot)))
    m = load_model(a.model, a.textures)
    print('model: %d vertices, %d triangles, %d textures' % (len(m.pos), len(m.tris), sum(i is not None for i in m.images)))
    adj = dict(width=a.width, height=a.height, depth=a.depth, yaw=a.yaw, pitch=a.pitch, roll=a.roll, dx=a.dx, dy=a.dy, dz=a.dz)
    fitted = S.fit(orig, m, up=a.up or getattr(m, 'up', '+Y'), forward=a.forward, scale=a.scale, adjust=adj, atlas_size=a.tex_size)
    from . import pipeline as PL
    items, atlas = PL.make_assets(toc, I.ad, path, orig, rows, slot, fitted, textures=not a.no_textures, flip_v=a.flip_v)
    asset = items[0][1]
    if a.atlas_out: __import__('PIL.Image', fromlist=['Image']).fromarray(atlas).save(a.atlas_out); print('texture picture written to', a.atlas_out)
    if a.dry_run:
        open(a.dry_run, 'wb').write(asset)
        for k, (tp, data) in enumerate(items[1:]): open('%s.%s' % (a.dry_run, os.path.basename(tp)), 'wb').write(data)
        print('dry run: wrote %s (%d bytes) + %d texture file(s); nothing installed' % (a.dry_run, len(asset), len(items) - 1)); toc.close(); return
    name = a.name or os.path.splitext(os.path.basename(a.model))[0]
    mid = hashlib.md5(('%s|%s|%s' % (a.suit, name, time.time())).encode()).hexdigest()[:10]
    I.install_group(mid, items, name)
    print('installed "%s" over suit %s: model%s' % (name, a.suit, '' if a.no_textures else ' + 3 textures'))
    print('undo with:  python -m modswap spiderman restore'); toc.close()


def cmd_list(a):
    mods = _install(a).installed()
    if not mods: print('nothing installed by ModSwap')
    seen = set()
    for m in mods:
        g = m.get('group', m['id'])
        if g in seen: continue
        seen.add(g); parts = [x for x in mods if x.get('group', x['id']) == g]
        print('%-12s %-24s %d file(s), %.1f MB   (%s)' % (g, m['name'][:24], len(parts), sum(x['size'] for x in parts) / 1e6, parts[0]['target']))


def cmd_uninstall(a):
    d = _game(a); _guard(d); I = _install(a)
    if a.id not in {m['id'] for m in I.installed()}: sys.exit('no installed mod with id %s (see: list)' % a.id)
    I.uninstall(a.id); print('removed', a.id)


def cmd_restore(a):
    d = _game(a); _guard(d); _install(a).restore(); print('game index and ModSwap files restored to the original')


def add_parser(sp):
    s = sp.add_parser('spiderman', help="Marvel's Spider-Man Remastered", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s.add_argument('--dir', help="the game folder (default: %s)" % DEFAULT_DIR)
    t = s.add_subparsers(dest='action', required=True)
    for n, f in (('suits', cmd_suits), ('list', cmd_list), ('restore', cmd_restore)): t.add_parser(n).set_defaults(f=f)
    x = t.add_parser('slots'); x.add_argument('--suit', default='classic'); x.set_defaults(f=cmd_slots)
    u = t.add_parser('uninstall'); u.add_argument('--id', required=True); u.set_defaults(f=cmd_uninstall)
    i = t.add_parser('install'); i.add_argument('--suit', default='classic'); i.add_argument('--model', required=True); i.add_argument('--textures'); i.add_argument('--name')
    i.add_argument('--material', type=int, help='material slot for every part (default: detected)'); i.add_argument('--up'); i.add_argument('--forward'); i.add_argument('--scale', type=float, default=1.0)
    i.add_argument('--flip-v', action='store_true', help='flip the texture picture upside down'); i.add_argument('--atlas-out', help='save the combined texture picture here')
    i.add_argument('--tex-size', type=int, default=1024, help='size of the colour texture, 512 / 1024 / 2048 (default 1024)'); i.add_argument('--no-textures', action='store_true', help='only the model (the suit keeps its own picture)')
    i.add_argument('--dry-run', metavar='OUT.model', help='build the model, write it to this file, install nothing')
    i.add_argument('--yaw', type=float, default=0.0); i.add_argument('--pitch', type=float, default=0.0); i.add_argument('--roll', type=float, default=0.0)
    for k in ('width', 'height', 'depth'): i.add_argument('--' + k, type=float, default=1.0)
    for k in ('dx', 'dy', 'dz'): i.add_argument('--' + k, type=float, default=0.0)
    i.set_defaults(f=cmd_install)
