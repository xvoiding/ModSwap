"""ModSwap command line.

  python -m modswap swap  --profile profiles/jda_wally.json --orig <extracted game files> --model model.fbx --out out_dir [--forward -Z] [--up +Y]
  python -m modswap pack  --dir out_dir --pak MyMod_P.pak          (uses repak if installed)
  python -m modswap info  --model model.fbx                        (orientation / size guess)

  python -m modswap games [--scan]            list your games (--scan re-reads your Steam libraries)
  python -m modswap add --exe C:\\Games\\X\\X.exe  add a game that is not on Steam
  python -m modswap characters --game ID      detect the characters / items you can swap in a game
  python -m modswap apply --game ID --model m.fbx [--family 0]   swap + pack + install in one go
  python -m modswap restore --game ID         remove the mods ModSwap installed
  python -m modswap market list                                  models in the marketplace right now
  python -m modswap market build FOLDER [--out DIR] [--base-url URL]   turn a folder of models into a hostable catalog.json
  python -m modswap rebuild [--game ID] [--mod ID]   redo your saved mods with the current engine, keeping every setting (installed ones stay installed)
  python -m modswap spiderman suits|slots|install|list|uninstall|restore   Marvel's Spider-Man Remastered (see `spiderman -h`)
  python -m modswap sonic characters|install|list|uninstall|restore      Sonic Frontiers (see `sonic -h`)
  python -m modswap gui                       open the graphical app in your browser

A *profile* describes one game character: where its mesh and textures live and which engine adapter to use.
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np


def _adjust(a):
    """--width/--height/--depth are multipliers (1 = unchanged), --yaw degrees clockwise from above, --dx/--dy/--dz offsets in cm."""
    return dict(width=a.width, height=a.height, depth=a.depth, yaw=a.yaw, pitch=a.pitch, roll=a.roll, dx=a.dx, dy=a.dy, dz=a.dz)


def _fit_args(p):
    p.add_argument('--yaw', type=float, default=0.0, help='rotate (degrees, clockwise seen from above)')
    p.add_argument('--pitch', type=float, default=0.0, help='lean forward (+) / back (-), degrees')
    p.add_argument('--roll', type=float, default=0.0, help='lean left (+) / right (-), degrees')
    for k in ('width', 'height', 'depth'): p.add_argument('--' + k, type=float, default=1.0, help=k + ' multiplier')
    for k in ('dx', 'dy', 'dz'): p.add_argument('--' + k, type=float, default=0.0, help='offset in cm (x=left, y=forward, z=up)')


def cmd_swap(a):
    from .modelio import load_model
    from .build import run_profile
    prof = json.load(open(a.profile))
    if prof.get('engine', 'ue4') not in ('ue4', 'unreal'): sys.exit('engine %r not implemented yet' % prof.get('engine'))
    m = load_model(a.model, a.textures)
    run_profile(prof, a.orig, m, a.out, up=a.up or getattr(m, 'up', None), forward=a.forward, scale=a.scale, adjust=_adjust(a))
    print('wrote override files to', a.out)


def cmd_pack(a):
    exe = shutil.which('repak') or a.repak
    if not exe: sys.exit('repak not found; pass --repak /path/to/repak')
    subprocess.check_call([exe, 'pack', '--version', a.version, a.dir, a.pak])
    print('wrote', a.pak)


def cmd_info(a):
    from .modelio import load_model
    from .skin import detect_forward
    m = load_model(a.model, a.textures)
    ext = m.pos.max(0) - m.pos.min(0); up = '+' + 'XYZ'[int(np.argmax(ext))]
    print('verts', len(m.pos), 'tris', len(m.tris), 'materials', len(m.mat_names), 'textures', sum(i is not None for i in m.images))
    print('extent', ext.round(3), 'guessed up', up, 'guessed forward', detect_forward(m.pos, up))



def _lib():
    from .games.library import Library
    return Library()


def cmd_games(a):
    lib = _lib()
    if a.scan or not lib.games:
        n = lib.scan_steam(progress=lambda i, n, name: print('  [%d/%d] %s' % (i + 1, n, name), end='\r'))
        print('Steam scan done, %d new game(s)       ' % n)
    for g in lib.list():
        print('%-28s %-30s %-8s %-12s %s' % (g.id, g.name[:30], g.engine, g.engine_version[:12], 'SWAPPABLE' if g.supported else '(engine not supported yet)'))


def cmd_add(a):
    g = _lib().add_exe(a.exe, a.name)
    print('added %s (%s %s) root=%s%s' % (g.name, g.engine, g.engine_version, g.root, '' if g.supported else '  -- engine not supported yet'))


def _project(a):
    from .project import Project
    lib = _lib(); g = lib.games.get(a.game) or next((x for x in lib.games.values() if x.name.lower() == a.game.lower()), None)
    if not g: sys.exit('unknown game %r, run `modswap games`' % a.game)
    return Project(g)


def cmd_characters(a):
    P = _project(a); res = P.scan(force=a.rescan)
    print('CHARACTERS (swappable skeletal meshes, grouped by skeleton):')
    for i, f in enumerate(res['characters']):
        plan = P.plan(f)
        print('  [%d] %s  -- %d meshes; body to swap: %s; %d layered pieces' % (i, f.label, len(f.assets), ', '.join(os.path.basename(t) for t in plan['targets'][:4]), len(plan['hide'])))
    print('ITEMS (static meshes, detected; swapping them is not implemented yet): %d' % len(res['items']))
    for it in res['items'][:a.items]: print('   ', it.path.split('/Content/')[-1])


def cmd_apply(a):
    from .modelio import load_model
    P = _project(a); res = P.scan(); fam = res['characters'][a.family]
    plan = P.plan(fam); prof = P.make_profile(fam, plan)
    if a.dry_run: print(json.dumps(prof, indent=1)); return
    m = load_model(a.model, a.textures)
    pak = P.build(prof, m, a.name or os.path.splitext(os.path.basename(a.model))[0], forward=a.forward, up=a.up or getattr(m, 'up', None), scale=a.scale, adjust=_adjust(a))
    dest = P.install(pak, a.name or 'mod'); print('installed', dest)


def cmd_restore(a):
    for p in _project(a).restore(): print('removed', p)


def cmd_gui(a):
    from .server import serve
    serve(port=a.port, open_browser=not a.no_browser)


def cmd_serve(a):
    """engine only, for the desktop app: no browser, quits when the app closes its stdin"""
    from .server import serve
    serve(port=a.port, open_browser=False, watch_stdin=True)


def cmd_market(a):
    from . import market
    if a.action == 'list':
        r = market.listing()
        for m in r['models']: print('%-34s %-10s %-8s %6.1f MB  %s' % (m['name'][:34], m['category'] or '-', m['source'], m['size'] / 1048576.0, ', '.join(m['tags'])))
        print(len(r['models']), 'models.', *r['errors'])
    else:
        if not a.folder: sys.exit('market build needs a folder of models')
        out = a.out or os.path.join(a.folder, '_catalog')
        market.build_catalog(a.folder, out, a.base_url or '')


def cmd_rebuild(a):
    """redo saved mods with the current engine (e.g. after a texture fix) without choosing anything again"""
    from . import mods, server
    from .games.library import Library
    lib = Library(); done = skipped = failed = 0
    for gid, g in lib.games.items():
        if a.game and gid != a.game: continue
        for m in mods.list_mods(gid):
            if a.mod and m['id'] != a.mod: continue
            label = '%s / %s' % (g.name, m['name'])
            if mods.edit_info(gid, m['id']) is None:
                print('skipped  %s: made before ModSwap kept its model (make it once more and it can be rebuilt later)' % label); skipped += 1; continue
            print('rebuilding  %s ...' % label)
            try: server.rebuild_mod(gid, m['id'], log=print); print('done      %s' % label); done += 1
            except Exception as e: print('FAILED    %s: %s' % (label, e)); failed += 1
    print('\n%d rebuilt, %d skipped, %d failed.' % (done, skipped, failed))
    if failed: sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(prog='modswap'); sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('swap'); s.add_argument('--profile', required=True); s.add_argument('--orig', required=True)
    s.add_argument('--model', required=True); s.add_argument('--out', required=True); s.add_argument('--textures')
    s.add_argument('--up'); s.add_argument('--forward'); s.add_argument('--scale', type=float, default=1.0); _fit_args(s); s.set_defaults(f=cmd_swap)
    k = sp.add_parser('pack'); k.add_argument('--dir', required=True); k.add_argument('--pak', required=True)
    k.add_argument('--version', default='V9'); k.add_argument('--repak'); k.set_defaults(f=cmd_pack)
    i = sp.add_parser('info'); i.add_argument('--model', required=True); i.add_argument('--textures'); i.set_defaults(f=cmd_info)
    g = sp.add_parser('games'); g.add_argument('--scan', action='store_true'); g.set_defaults(f=cmd_games)
    ad = sp.add_parser('add'); ad.add_argument('--exe', required=True); ad.add_argument('--name'); ad.set_defaults(f=cmd_add)
    ch = sp.add_parser('characters'); ch.add_argument('--game', required=True); ch.add_argument('--rescan', action='store_true'); ch.add_argument('--items', type=int, default=10); ch.set_defaults(f=cmd_characters)
    ap = sp.add_parser('apply'); ap.add_argument('--game', required=True); ap.add_argument('--model', required=True); ap.add_argument('--textures'); ap.add_argument('--family', type=int, default=0)
    ap.add_argument('--name'); ap.add_argument('--up'); ap.add_argument('--forward'); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--dry-run', action='store_true'); _fit_args(ap); ap.set_defaults(f=cmd_apply)
    rs = sp.add_parser('restore'); rs.add_argument('--game', required=True); rs.set_defaults(f=cmd_restore)
    rb = sp.add_parser('rebuild'); rb.add_argument('--game'); rb.add_argument('--mod'); rb.set_defaults(f=cmd_rebuild)
    sv = sp.add_parser('serve'); sv.add_argument('--port', type=int, default=8765); sv.set_defaults(f=cmd_serve)
    mk = sp.add_parser('market'); mk.add_argument('action', choices=['list', 'build']); mk.add_argument('folder', nargs='?'); mk.add_argument('--out'); mk.add_argument('--base-url'); mk.set_defaults(f=cmd_market)
    gu = sp.add_parser('gui'); gu.add_argument('--port', type=int, default=8765); gu.add_argument('--no-browser', action='store_true'); gu.set_defaults(f=cmd_gui)
    from .insomniac.cli import add_parser as _sm; _sm(sp)
    from .hedgehog.cli import add_parser as _hh; _hh(sp)
    a = p.parse_args(argv); a.f(a)


if __name__ == '__main__':
    main()
