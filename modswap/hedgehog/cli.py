"""Command line for Sonic Frontiers:

  python -m modswap sonic characters                                   which characters can be swapped (their .pac holds the textures)
  python -m modswap sonic install --character sonic --model my.fbx [--textures FOLDER] [--name X] [--dry-run OUT.pac]
  python -m modswap sonic list                                         what ModSwap has installed
  python -m modswap sonic uninstall --id ID                            take one mod out (the original .pac comes back byte for byte)
  python -m modswap sonic restore                                      every changed file back to the original

--dir is the game folder (default: the usual Steam place). The game must be closed. The original .pac files are copied to <game>\\modswap_backup first.
"""
import os, sys, time, hashlib, argparse
from types import SimpleNamespace

DEFAULT_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\SonicFrontiers"


def _game(a):
    d = a.dir or DEFAULT_DIR
    if not os.path.isdir(os.path.join(d, 'image', 'x64', 'raw', 'character')): sys.exit('no image\\x64\\raw\\character folder in %s: pass --dir "<Sonic Frontiers folder>"' % d)
    return d


def _guard(d):
    from ..games.running import ensure_closed
    try: ensure_closed(SimpleNamespace(root=d, name='Sonic Frontiers', exe=''))
    except RuntimeError as e: sys.exit(str(e))


def _project(a):
    from .project import SonicProject
    return SonicProject(SimpleNamespace(root=_game(a), id='cli', name='Sonic Frontiers'))


def cmd_characters(a):
    P = _project(a); rows = P.scan(log=lambda *x: None)
    for r in rows: print('%-12s %-22s %s' % (r['stem'], r['label'], 'ready' if r['ok'] else 'model only: ' + r['why']))
    print('%d character file(s); "ready" ones can be swapped with textures.' % len(rows))


def cmd_install(a):
    from ..modelio import load_model
    d = _game(a)
    if not a.dry_run: _guard(d)
    P = _project(a); rows = P.scan(log=lambda *x: None)
    i = next((k for k, r in enumerate(rows) if r['stem'].lower() == a.character.lower()), None)
    if i is None: sys.exit('no character "%s" (try: characters)' % a.character)
    try: m = P.model(i)
    except ValueError as e: sys.exit(str(e))
    mdl = load_model(a.model, a.textures)
    print('model: %d vertices, %d triangles, %d textures' % (len(mdl.pos), len(mdl.tris), sum(x is not None for x in mdl.images)))
    adj = dict(width=a.width, height=a.height, depth=a.depth, yaw=a.yaw, pitch=a.pitch, roll=a.roll, dx=a.dx, dy=a.dy, dz=a.dz)
    params = dict(up=a.up, forward=a.forward, scale=a.scale, adjust=adj)
    ch = P._character(m['rel']); f = P.fit(m, mdl, params, log=print)
    if a.atlas_out: __import__('PIL.Image', fromlist=['Image']).fromarray(f['atlas']).save(a.atlas_out); print('texture picture written to', a.atlas_out)
    data, rep = ch.build(f, textures=not a.no_textures)
    if a.dry_run: open(a.dry_run, 'wb').write(data); print('dry run: wrote %s (%d bytes); nothing installed' % (a.dry_run, len(data))); return
    name = a.name or os.path.splitext(os.path.basename(a.model))[0]; mid = hashlib.md5(('%s|%s|%s' % (a.character, name, time.time())).encode()).hexdigest()[:10]
    P.I.install(mid, m['rel'], data, name, character=m['stem'])
    print('installed "%s" over %s%s\nundo with:  python -m modswap sonic restore' % (name, m['label'], '' if not a.no_textures else ' (model only)'))


def cmd_list(a):
    mods = _project(a).I.installed()
    if not mods: print('nothing installed by ModSwap')
    for m in mods: print('%-12s %-24s %-40s %.1f MB' % (m['id'], m['name'][:24], m['file'], m['size'] / 1e6))


def cmd_uninstall(a):
    d = _game(a); _guard(d); P = _project(a)
    if a.id not in {m['id'] for m in P.I.installed()}: sys.exit('no installed mod with id %s (see: list)' % a.id)
    P.I.uninstall(a.id); print('removed', a.id)


def cmd_restore(a):
    d = _game(a); _guard(d); _project(a).I.restore(); print('every file ModSwap changed is back to the original')


def add_parser(sp):
    s = sp.add_parser('sonic', help='Sonic Frontiers', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s.add_argument('--dir', help='the game folder (default: %s)' % DEFAULT_DIR); t = s.add_subparsers(dest='action', required=True)
    for n, f in (('characters', cmd_characters), ('list', cmd_list), ('restore', cmd_restore)): t.add_parser(n).set_defaults(f=f)
    u = t.add_parser('uninstall'); u.add_argument('--id', required=True); u.set_defaults(f=cmd_uninstall)
    i = t.add_parser('install'); i.add_argument('--character', default='sonic'); i.add_argument('--model', required=True); i.add_argument('--textures'); i.add_argument('--name')
    i.add_argument('--up'); i.add_argument('--forward'); i.add_argument('--scale', type=float, default=1.0); i.add_argument('--atlas-out'); i.add_argument('--no-textures', action='store_true')
    i.add_argument('--dry-run', metavar='OUT.pac', help='build the .pac, write it to this file, install nothing')
    i.add_argument('--yaw', type=float, default=0.0); i.add_argument('--pitch', type=float, default=0.0); i.add_argument('--roll', type=float, default=0.0)
    for k in ('width', 'height', 'depth'): i.add_argument('--' + k, type=float, default=1.0)
    for k in ('dx', 'dy', 'dz'): i.add_argument('--' + k, type=float, default=0.0)
    i.set_defaults(f=cmd_install)
