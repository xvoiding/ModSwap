"""Each game's saved mods: every mod you build is kept (as a ready .pak) so you can install it, take it off, save a copy or delete it."""
import os, re, json, time, shutil
from .games import library


def _dir(gid):
    d = os.path.join(library.config_dir(), 'mods', re.sub(r'[^A-Za-z0-9_.-]', '_', gid)); os.makedirs(d, exist_ok=True); return d


def _slug(s): return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:40] or 'mod'


def add(gid, name, pak, character='', installed=False, source_dir=None, edit=None):
    """source_dir = the folder your model was uploaded to, edit = how it was fitted (family, sliders, body-part edits ...). Both are kept so the
    mod can be opened again and changed later (see edit_info / open_for_edit)."""
    mid = '%s-%d' % (_slug(name), int(time.time()))
    d = os.path.join(_dir(gid), mid); os.makedirs(d, exist_ok=True)
    shutil.copy2(pak, os.path.join(d, 'mod.pak'))
    if source_dir and os.path.isdir(source_dir) and edit is not None:
        try:
            shutil.copytree(source_dir, os.path.join(d, 'source'))
            json.dump(dict(edit, name=name, character=character), open(os.path.join(d, 'edit.json'), 'w'))
        except Exception: shutil.rmtree(os.path.join(d, 'source'), ignore_errors=True)      # never fail a build over the "edit later" copy
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


def edit_info(gid, mid):
    """-> the saved fit settings of a mod (family, up, forward, scale, width/height/depth, yaw/pitch/roll, dx/dy/dz, edits, parts, name), or None
    for a mod made before ModSwap kept them"""
    d = os.path.dirname(pak_path(gid, mid)); p = os.path.join(d, 'edit.json')
    if not (os.path.isfile(p) and os.path.isdir(os.path.join(d, 'source'))): return None
    try: return json.load(open(p))
    except Exception: return None


def open_for_edit(gid, mid, dest_dir):
    """copy the mod's model + textures into dest_dir (a fresh upload folder) and return its saved settings, so the fit screen can open it again"""
    info = edit_info(gid, mid)
    if info is None: raise ValueError("this mod was made before ModSwap kept its model, so it can't be reopened. Make it again from your model and it will be editable.")
    src = os.path.join(os.path.dirname(pak_path(gid, mid)), 'source')
    shutil.copytree(src, dest_dir, dirs_exist_ok=True)
    return info
