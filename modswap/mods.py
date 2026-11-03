"""Each game's saved mods: every mod you build is kept (as a ready .pak) so you can install it, take it off, save a copy or delete it."""
import os, re, json, time, shutil
from .games import library


def _dir(gid):
    d = os.path.join(library.config_dir(), 'mods', re.sub(r'[^A-Za-z0-9_.-]', '_', gid)); os.makedirs(d, exist_ok=True); return d


def _slug(s): return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:40] or 'mod'


def add(gid, name, pak, character='', installed=False):
    mid = '%s-%d' % (_slug(name), int(time.time()))
    d = os.path.join(_dir(gid), mid); os.makedirs(d, exist_ok=True)
    shutil.copy2(pak, os.path.join(d, 'mod.pak'))
    for e in ('.utoc', '.ucas'):                                  # IoStore mods are a set: .pak + .utoc + .ucas
        side = os.path.splitext(pak)[0] + e
        if os.path.isfile(side): shutil.copy2(side, os.path.join(d, 'mod' + e))
    json.dump(dict(id=mid, name=name, created=time.time(), character=character), open(os.path.join(d, 'meta.json'), 'w'))
    return mid


def list_mods(gid, active_ids=()):
    out = []
    base = _dir(gid)
    for mid in os.listdir(base):
        mp = os.path.join(base, mid, 'meta.json'); pk = os.path.join(base, mid, 'mod.pak')
        if not (os.path.isfile(mp) and os.path.isfile(pk)): continue
        try: m = json.load(open(mp))
        except Exception: continue
        m['size'] = sum(os.path.getsize(os.path.join(base, mid, f)) for f in os.listdir(os.path.join(base, mid)) if f.startswith('mod.')); m['pak'] = pk; m['active'] = mid in active_ids
        out.append(m)
    return sorted(out, key=lambda m: -m.get('created', 0))


def pak_path(gid, mid):
    p = os.path.join(_dir(gid), re.sub(r'[^A-Za-z0-9_.-]', '_', mid), 'mod.pak')
    if not os.path.isfile(p): raise ValueError('that mod no longer exists')
    return p


def delete(gid, mid):
    d = os.path.dirname(pak_path(gid, mid)); shutil.rmtree(d, ignore_errors=True)
