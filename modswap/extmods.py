"""Mods you downloaded yourself (not made by ModSwap): drop in a .pak / .utoc / .ucas / .zip / a folder and ModSwap puts every file where the
game wants it, remembers what it wrote, can switch the mod off and on, and removes it again (restoring anything it had to overwrite).

Unreal games:   .pak/.utoc/.ucas  ->  <Game>/Content/Paks/~mods/
                 files under Binaries/ Content/ Plugins/ inside a zip  ->  the same place inside <Game>/   (this is how the UTOC signature bypass is installed)
Other games:    the zip is unpacked into the game's folder exactly as the author packed it (what most mod pages tell you to do)
Program files (.dll .asi .exe .bat ...) are only written when the caller says the person confirmed it."""
import os, re, json, shutil, time, zipfile
from .games import library

PAK_EXT = ('.pak', '.utoc', '.ucas', '.sig')
CODE_EXT = ('.dll', '.asi', '.exe', '.bat', '.cmd', '.ps1', '.vbs', '.scr', '.msi', '.lnk', '.com', '.jar')
DOCS = re.compile(r'(^|/)(__MACOSX|\.git)(/|$)|(^|/)(readme|license|changelog|credits|thumbs\.db|desktop\.ini)[^/]*$', re.I)
SKIP = re.compile(r'(^|/)(__MACOSX|\.git)(/|$)|(^|/)(readme|license|changelog|credits|thumbs\.db|desktop\.ini)[^/]*$|\.(txt|md|url|nfo|jpg|jpeg|png|gif|webp|pdf|html?)$', re.I)
ANCHORS = ('Binaries', 'Content', 'Plugins', 'Config', 'Saved')
MODS_DIR = '~mods'
BIG = 4 * 1024 ** 3


def _slug(s): return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:40] or 'mod'


def _reg_path(gid):
    d = os.path.join(library.config_dir(), 'extmods'); os.makedirs(d, exist_ok=True)
    return os.path.join(d, re.sub(r'[^A-Za-z0-9_.-]', '_', gid) + '.json')


def _load(gid):
    try: return json.load(open(_reg_path(gid)))
    except Exception: return dict(mods=[])


def _save(gid, reg): json.dump(reg, open(_reg_path(gid), 'w'), indent=1)


def _walk_depth(root, depth):
    root = os.path.normpath(root); base = root.count(os.sep)
    for d, dirs, files in os.walk(root):
        if d.count(os.sep) - base >= depth: dirs[:] = []
        yield d, dirs, files


def locate(game):
    """-> dict(engine, root, paks (Paks folder or ''), project (the Unreal project folder, the one with Content/Binaries) or '')"""
    root = game.root; paks = ''; project = ''
    if game.engine == 'unreal':
        best = None
        for d, dirs, files in _walk_depth(root, 6):
            if os.path.basename(d).lower() == 'paks' and any(f.lower().endswith(('.pak', '.utoc')) for f in files):
                score = sum(1 for f in files if f.lower().endswith(('.pak', '.utoc')))
                if best is None or score > best[0]: best = (score, d)
        if best: paks = best[1]
        if not paks:
            for d, dirs, files in _walk_depth(root, 5):
                if os.path.basename(d).lower() == 'paks': paks = d; break
        if paks: project = os.path.dirname(os.path.dirname(paks))           # .../<Game>/Content/Paks -> .../<Game>
    return dict(engine=game.engine, root=root, paks=paks, project=project)


def mods_dir(game):
    loc = locate(game)
    if game.engine == 'unreal' and loc['paks']: return os.path.join(loc['paks'], MODS_DIR)
    return loc['root']


def bypass_status(game):
    """For Unreal games with IoStore containers: is a signature bypass (dsound.dll next to the game exe) in place?"""
    loc = locate(game)
    if not loc['paks'] or not any(f.lower().endswith('.utoc') for f in os.listdir(loc['paks'])): return dict(needed=False, present=False)
    b = os.path.join(loc['project'], 'Binaries', 'Win64')
    return dict(needed=True, present=any(os.path.isfile(os.path.join(b, n)) for n in ('dsound.dll', 'version.dll', 'winmm.dll')), folder=b)


# ------------------------------------------------------------------ planning what to write
def _entries(paths):
    """expand dropped files/folders/zips -> [(relative path inside the mod, reader)] ; reader() -> bytes stream context"""
    out = []; notes = []
    for p in paths:
        p = p.strip().strip('"')
        if os.path.isdir(p):
            top = os.path.basename(os.path.normpath(p))
            for d, _, fs in os.walk(p):
                for f in fs:
                    full = os.path.join(d, f); rel = os.path.relpath(full, os.path.dirname(os.path.normpath(p))).replace(os.sep, '/')
                    out.append((rel, ('file', full), os.path.getsize(full)))
        elif p.lower().endswith('.zip'):
            try: z = zipfile.ZipFile(p)
            except zipfile.BadZipFile: raise ValueError('%s is not a valid zip file' % os.path.basename(p))
            for i in z.infolist():
                if i.is_dir(): continue
                out.append((i.filename.replace('\\', '/'), ('zip', p, i.filename), i.file_size))
        elif p.lower().endswith(('.rar', '.7z', '.tar', '.gz', '.xz')):
            raise ValueError('%s is a %s archive. ModSwap can open .zip files: right-click it, choose Extract, then drop the extracted files or folder here.' % (os.path.basename(p), os.path.splitext(p)[1][1:].upper()))
        elif os.path.isfile(p): out.append((os.path.basename(p), ('file', p), os.path.getsize(p)))
        else: raise ValueError('could not find %s' % p)
    return out


def _safe_rel(rel):
    parts = [x for x in rel.replace('\\', '/').split('/') if x and x != '.']
    if any(x == '..' or ':' in x for x in parts): return None
    return parts


def plan(game, paths):
    """-> dict(items=[dict(src, dest, code, size)], skipped=[...], needs_code=[names]) without touching the disk"""
    loc = locate(game); ents = _entries(paths); items, skipped = [], []
    ue = game.engine == 'unreal' and loc['paks']
    for rel, src, size in ents:
        parts = _safe_rel(rel)
        if not parts: skipped.append(rel); continue
        name = parts[-1]; low = name.lower(); code = low.endswith(CODE_EXT)
        if size > BIG: skipped.append(rel); continue
        if ue:
            if low.endswith(PAK_EXT):
                if low.endswith('.sig'): continue                                       # signature files of the game's own paks, never part of a mod
                dest = os.path.join(loc['paks'], MODS_DIR, name)
            else:
                anchor = next((i for i, x in enumerate(parts[:-1]) if x in ANCHORS), None)
                if anchor is not None: dest = os.path.join(loc['project'], *parts[anchor:])
                elif len(parts) == 1 and code: dest = os.path.join(loc['project'], 'Binaries', 'Win64', name)     # e.g. dsound.dll straight at the zip's top
                else: skipped.append(rel); continue
        else:
            if DOCS.search(rel) and not code: skipped.append(rel); continue
            if len(parts) > 1 and len(set(r.split('/')[0] for r, _, _ in ents)) == 1 and not os.path.exists(os.path.join(loc['root'], parts[0])):
                parts = parts[1:]                                                       # a single wrapper folder named after the mod: drop it
            dest = os.path.join(loc['root'], *parts)
        items.append(dict(src=src, dest=dest, code=code, size=size, rel=rel))
    items = [i for i in items if not (ue and SKIP.search(i['rel']) and not i['code'] and not i['dest'].lower().endswith(PAK_EXT))]
    return dict(items=items, skipped=skipped, needs_code=sorted({os.path.basename(i['dest']) for i in items if i['code']}))


def _open(src):
    if src[0] == 'file': return open(src[1], 'rb')
    z = zipfile.ZipFile(src[1]); return _ZipFile(z, z.open(src[2]))


class _ZipFile:
    def __init__(s, z, f): s.z = z; s.f = f
    def read(s, n=-1): return s.f.read(n)
    def __enter__(s): return s
    def __exit__(s, *a): s.f.close(); s.z.close()


def install(game, paths, allow_code=False, name=None, log=print):
    """Write the mod's files. -> dict(mod=record, notes=[...]) ; raises ValueError('needs_confirm: ...') when program files need an OK."""
    pl = plan(game, paths)
    if not pl['items']: raise ValueError('nothing in there looks like a mod for this game (no .pak, .utoc, .ucas or game files). %s' % (('Skipped: ' + ', '.join(pl['skipped'][:4])) if pl['skipped'] else ''))
    if pl['needs_code'] and not allow_code:
        raise ValueError('needs_confirm: this mod contains program files (%s). Only continue if you trust where you downloaded it.' % ', '.join(pl['needs_code'][:6]))
    gid = game.id; reg = _load(gid)
    first = os.path.basename(os.path.normpath(paths[0])); mname = name or re.sub(r'\.(zip|pak|utoc|ucas)$', '', first, flags=re.I)
    mid = '%s-%d' % (_slug(mname), int(time.time())); bdir = os.path.join(os.path.dirname(_reg_path(gid)), 'backup', _slug(gid), mid)
    files, backups, notes = [], {}, []
    try:
        for it in pl['items']:
            dest = it['dest']; os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest):
                bk = os.path.join(bdir, str(len(backups))); os.makedirs(bdir, exist_ok=True); shutil.copy2(dest, bk); backups[dest] = bk
            with _open(it['src']) as s, open(dest + '.part', 'wb') as o: shutil.copyfileobj(s, o, 1 << 20)
            os.replace(dest + '.part', dest); files.append(dest); log('copied ' + os.path.basename(dest))
    except Exception:
        for f in files:                                                                 # half-installed: put everything back
            try: os.remove(f)
            except OSError: pass
        for dest, bk in backups.items():
            try: shutil.copy2(bk, dest)
            except OSError: pass
        raise
    rec = dict(id=mid, name=mname, files=files, backups=backups, time=time.time(), enabled=True, code=bool(pl['needs_code']))
    reg['mods'].append(rec); _save(gid, reg)
    if pl['skipped']: notes.append('skipped %d file(s) that are not part of the mod (readmes, pictures...)' % len(pl['skipped']))
    if any(f.lower().endswith('.utoc') for f in files):
        bp = bypass_status(game)
        if bp['needed'] and not bp['present']: notes.append('This game checks container signatures. Install the "UTOC Signature Bypass" for it too (drop its zip here), otherwise the game ignores this mod.')
    return dict(mod=_public(rec), notes=notes)


def _public(rec):
    on = rec.get('enabled', True)
    return dict(id=rec['id'], name=rec['name'], files=len(rec['files']), enabled=on, time=rec['time'], code=rec.get('code', False),
                size=sum(os.path.getsize(f + ('' if on else '.disabled')) for f in rec['files'] if os.path.exists(f + ('' if on else '.disabled'))))


def list_mods(game):
    reg = _load(game.id)
    return dict(mods=[_public(m) for m in sorted(reg['mods'], key=lambda m: -m['time'])], folder=mods_dir(game), bypass=bypass_status(game))


def _find(reg, mid):
    for m in reg['mods']:
        if m['id'] == mid: return m
    raise ValueError('that mod is not in the list any more')


def toggle(game, mid):
    reg = _load(game.id); m = _find(reg, mid); on = m.get('enabled', True)
    for f in m['files']:
        a, b = (f, f + '.disabled') if on else (f + '.disabled', f)
        if os.path.exists(a):
            try: os.replace(a, b)
            except OSError as e: raise ValueError('could not switch %s (is the game running?): %s' % (os.path.basename(f), e))
    m['enabled'] = not on; _save(game.id, reg); return _public(m)


def remove(game, mid):
    reg = _load(game.id); m = _find(reg, mid)
    for f in m['files']:
        for p in (f, f + '.disabled'):
            if os.path.exists(p):
                try: os.remove(p)
                except OSError as e: raise ValueError('could not remove %s (is the game running?): %s' % (os.path.basename(p), e))
    for dest, bk in m.get('backups', {}).items():
        try: shutil.copy2(bk, dest)
        except OSError: pass
    shutil.rmtree(os.path.join(os.path.dirname(_reg_path(game.id)), 'backup', _slug(game.id), m['id']), ignore_errors=True)
    for f in m['files']:                                                                # tidy up folders this mod created (only when empty)
        d = os.path.dirname(f)
        try:
            while d and os.path.basename(d) != os.path.basename(game.root) and not os.listdir(d) and os.path.normpath(d) != os.path.normpath(game.root): os.rmdir(d); d = os.path.dirname(d)
        except OSError: pass
    reg['mods'] = [x for x in reg['mods'] if x['id'] != mid]; _save(game.id, reg)
    return dict(removed=m['name'])
