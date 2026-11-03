"""ModSwap app: a small local web server (stdlib only) + the UI in modswap/web.   python -m modswap gui

Runs on your machine only (127.0.0.1). Long work (scanning a game, building a mod) runs as background jobs with a live log.
"""
import re, os, sys, io, json, base64, threading, traceback, uuid, tempfile, webbrowser, shutil, zipfile, mimetypes, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

import numpy as np

from .games.library import Library, config_dir
from .games import detect, running

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
UPLOADS = os.path.join(tempfile.gettempdir(), 'modswap_uploads')
JOBS = {}
LOCK = threading.RLock()
MODELS = {}      # (path, mtime) -> Model
FITCTX = {}      # (game id, family) -> context
ATLAS = {}       # (model key, parts) -> (atlas array, uv)

mimetypes.add_type('application/javascript', '.js'); mimetypes.add_type('image/svg+xml', '.svg')


# ------------------------------------------------------------------ jobs
def _job(fn):
    jid = uuid.uuid4().hex[:8]; j = dict(id=jid, log=[], done=False, error=None, result=None); JOBS[jid] = j

    def log(*a): j['log'].append(' '.join(str(x) for x in a))

    def run():
        try:
            with LOCK: j['result'] = fn(log)
        except Exception as e:
            j['error'] = _msg(e); j['log'].append(traceback.format_exc(limit=4))
        finally: j['done'] = True
    threading.Thread(target=run, daemon=True).start()
    return jid


# ------------------------------------------------------------------ games
def _game(lib, gid):
    g = lib.games.get(gid)
    if not g: raise KeyError('unknown game ' + str(gid))
    return g


def _where(e):
    """'file.py:123' of the innermost ModSwap frame of an unexpected error (so a bug report says where)"""
    try:
        tb = e.__traceback__; last = None
        while tb:
            fn = tb.tb_frame.f_code.co_filename
            if os.sep + 'modswap' + os.sep in fn or '/modswap/' in fn: last = (os.path.basename(fn), tb.tb_lineno)
            tb = tb.tb_next
        return '%s:%d' % last if last else ''
    except Exception: return ''


def _msg(e):
    m = '%s' % e
    if isinstance(e, (TypeError, KeyError, IndexError, AttributeError, UnboundLocalError)):
        w = _where(e); m = "Internal error: %s%s" % (m, ' (at %s)' % w if w else '')
    return m


def _unity_ok(g):
    return g.engine == 'unity'            # every Unity game is tried; if its files can't be edited the scan says why


def _game_json(g):
    label = detect.EngineInfo(g.engine, g.engine_version).label
    return dict(id=g.id, name=g.name, root=g.root, source=g.source, engine=g.engine, version=g.engine_version, label=label,
                detail=g.engine_detail, supported=g.supported or _unity_ok(g), paks=len(g.paks or []), appid=g.appid)


ART_PREF = ('library_header.jpg', 'header.jpg', 'library_capsule.jpg', 'capsule_616x353.jpg', 'library_600x900.jpg', 'library_hero.jpg')


def find_art(appid):
    """cover picture Steam already downloaded for this game (no internet needed), or None"""
    if not appid or not re.fullmatch(r'\d+', str(appid)): return None
    from .games import steam
    for root in steam.steam_roots():
        base = os.path.join(root, 'appcache', 'librarycache')
        hits = {}
        d = os.path.join(base, str(appid))
        if os.path.isdir(d):
            for dp, _, fs in os.walk(d):
                for f in fs: hits.setdefault(f.lower(), os.path.join(dp, f))
        for f in ART_PREF: hits.setdefault(f, os.path.join(base, '%s_%s' % (appid, f)))        # older flat layout
        for f in ART_PREF:
            if os.path.isfile(hits.get(f, '')): return hits[f]
    return None


def _project(g):
    if g.engine == 'unity':
        from .unity.project import UnityProject
        return UnityProject(g)
    from .project import Project, IoStoreProject, is_iostore
    if g.engine == 'unreal' and is_iostore(g): return IoStoreProject(g)
    return Project(g)


def api_redetect(gid):
    lib = Library(); g = _game(lib, gid)
    e = detect.detect_engine(g.root)
    g.engine, g.engine_version, g.engine_detail, g.supported, g.paks = e.engine, e.version, e.detail, e.supported, e.paks
    lib.save(); return dict(game=_game_json(g))


def api_characters(gid):
    lib = Library(); g = _game(lib, gid)

    def work(log):
        P = _project(g)
        if g.engine == 'unity':
            log('reading the game files...'); ch = P.describe(log=log); return dict(characters=ch, items=[], total_files=0, unity=True, rigged=sum(1 for c in ch if c.get('rigged')), hidden=sum(1 for c in ch if c.get('hidden')), engine='2.6')
        log('reading the game files...'); res = P.scan(log=log)
        chars = []
        propish = re.compile(r'(^|/)(props?|foliage|trees?|furniture|setdecoration|decorations?|weapons?|equippables?|swingables?|items?|pickups?|vehicles?)(/|$)', re.I)
        for i, f in enumerate(res['characters']):
            if all(propish.search(x.folder) or x.role == 'piece' for x in f.assets) and any(propish.search(x.folder) for x in f.assets): continue   # props, not people
            plan = P.plan(f)
            chars.append(dict(index=i, label=f.label, meshes=len(f.assets), body=[os.path.basename(t) for t in plan['targets']][:8],
                              layered=len(plan['hide'])))
        items = [dict(name=a.name, folder=a.folder) for a in res['items']]
        return dict(characters=chars, items=items, total_files=res.get('total_files', 0))
    return _job(work)


def _ctx(gid, fam, log=print):
    """profile + rigs + original outline for one character group (cached)"""
    key = (gid, int(fam))
    if key in FITCTX: return FITCTX[key]
    from .build import target_rig
    from .preview import load_original
    lib = Library(); g = _game(lib, gid); P = _project(g); res = P.scan(log=log)
    family = res['characters'][int(fam)]; plan = P.plan(family); prof = P.make_profile(family, plan, log=log)
    P.extract([t['mesh'] for t in prof['targets']], exts=('.uasset', '.uexp'))
    ctx = dict(P=P, prof=prof, family=family, rigs={}, orig={})
    FITCTX[key] = ctx; return ctx


def _target(ctx, i):
    from .build import target_rig
    from .preview import load_original
    prof = ctx['prof']; t = prof['targets'][i]
    if i not in ctx['rigs']:
        ctx['rigs'][i] = target_rig(prof, ctx['P'].orig, t)
        ctx['orig'][i] = load_original(ctx['P'].orig, t['mesh'], prof['sk_format'], ctx['rigs'][i])
    return t, ctx['rigs'][i], ctx['orig'][i]


# ------------------------------------------------------------------ models
def _model_file(sid):
    from .modelio import MODEL_EXT
    d = os.path.join(UPLOADS, _sid(sid))
    if not os.path.isdir(d): raise ValueError('no files uploaded yet')
    files = [f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in MODEL_EXT]
    if not files: raise ValueError('no model file in your upload (drop an .fbx, .obj, .glb ...)')
    order = {e: i for i, e in enumerate(('.fbx', '.glb', '.gltf', '.obj', '.dae', '.vrm', '.blend', '.ply', '.stl', '.3mf', '.off'))}
    files.sort(key=lambda f: (order.get(os.path.splitext(f)[1].lower(), 99), f))
    return d, os.path.join(d, files[0])


def _sid(s): return ''.join(c for c in str(s) if c.isalnum())[:24] or 'x'


def get_model(sid, parts=None):
    from .modelio import load_model
    d, path = _model_file(sid); key = (path, os.path.getmtime(path), len(os.listdir(d)), tuple(sorted((f, os.path.getmtime(os.path.join(d, f)), os.path.getsize(os.path.join(d, f))) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))))     # any changed texture file reloads the model + preview atlas
    if key not in MODELS:
        MODELS.clear(); MODELS[key] = load_model(path, d)
    m = MODELS[key]
    return key, (m.subset(parts) if parts else m)


def api_inspect(sid):
    from . import skin
    from PIL import Image
    key, m = get_model(sid)
    thumbs = []
    for im in m.images[:8]:
        if im is None: thumbs.append(None); continue
        t = im.copy(); t.thumbnail((96, 96)); b = io.BytesIO(); t.convert('RGB').save(b, 'JPEG', quality=80); thumbs.append(base64.b64encode(b.getvalue()).decode())
    counts = np.bincount(m.tri_part, minlength=max(1, len(m.part_names))) if m.tri_part is not None else [len(m.tris)]
    fwd = skin.detect_forward(m.pos, m.up)
    return dict(file=os.path.basename(key[0]), verts=int(len(m.pos)), tris=int(len(m.tris)), materials=len(m.mat_names), textured=int(sum(i is not None for i in m.images)),
               up=m.up, forward=fwd, thumbs=thumbs, mat_names=m.mat_names[:12],
               parts=[dict(i=i, name=n, tris=int(counts[i]) if i < len(counts) else 0) for i, n in enumerate(m.part_names)]
                     or [dict(i=0, name=os.path.splitext(os.path.basename(key[0]))[0], tris=int(len(m.tris)))])


def _b64(a, dt): return base64.b64encode(np.ascontiguousarray(a, dt).tobytes()).decode()


def api_fit(body):
    """auto-rig your model onto the selected character and return both meshes for the 3D viewport"""
    from . import atlas, preview, edit
    from PIL import Image
    gid, fam = body['game'], body['family']
    if _is_unity(gid): return _unity_fit(body)
    with LOCK:
        ctx = _ctx(gid, fam); ti = int(body.get('target') or 0)
        t, rig, (opos, otris) = _target(ctx, ti)
        parts = body.get('parts') or None
        mkey, m = get_model(body['upload'], parts)
        adj = {k: float(body.get(k) or (1 if k in ('width', 'height', 'depth') else 0)) for k in ('width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose')}
        pos, nrm, tris, info = preview.fit_model(m, rig, up=body.get('up') or m.up, forward=body.get('forward') or None,
                                                 scale=float(body.get('scale') or 1.0), adjust=adj, edits=body.get('edits') or None)
        if not np.isfinite(pos).all(): raise RuntimeError("ModSwap couldn't fit your model onto this character (the numbers came out invalid). Try another model orientation, or pick a different character.")
        akey = (mkey, tuple(parts or ()))
        if akey not in ATLAS:
            ATLAS.clear()
            imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in m.images]
            atl, cells = atlas.pack(imgs, m.uv, m.vert_mat, size=1024); ATLAS[akey] = (atl, atlas.remap_uv(m.uv, m.vert_mat, cells, 1024))
        atl, uv = ATLAS[akey]
        b = io.BytesIO(); Image.fromarray(atl).save(b, 'PNG', compress_level=1)     # PNG: no JPEG smearing of the preview texture
        if 'origb64' not in ctx: ctx['origb64'] = {}
        if ti not in ctx['origb64']: ctx['origb64'][ti] = dict(pos=_b64(opos, '<f4'), idx=_b64(otris, '<u4'), n=len(opos), t=len(otris))
        return dict(orig=ctx['origb64'][ti],
                    new=dict(pos=_b64(pos, '<f4'), idx=_b64(tris, '<u4'), uv=_b64(uv, '<f4'), n=len(pos), t=len(tris)),
                    atlas=base64.b64encode(b.getvalue()).decode(),
                    info=dict(forward=info['forward'], scale=float(info['scale']), pivot=info['pivot'], up=info['up']),
                    groups=dict(names=edit.AUTO_NAMES, ids=_b64(info['vgroup'], 'u1'), pivots=[[float(x) for x in p] for p in info['piv']]),
                    targets=[x['name'] if 'name' in x else os.path.basename(x['mesh']) for x in ctx['prof']['targets']], target=ti,
                    height=float(opos[:, 2].max() - opos[:, 2].min()))


def _is_unity(gid):
    return _game(Library(), gid).engine == 'unity'


UFIT = {}


def _unity_fit(body):
    """same answer shape as the Unreal fit, so the 3D viewer works unchanged"""
    from . import atlas, edit
    from .unity import fit as ufit
    from PIL import Image
    gid = body['game']; g = _game(Library(), gid)
    with LOCK:
        P = UFIT.get(gid)
        if P is None: UFIT[gid] = P = _project(g)
        m = P.model(body['family'])
        parts = body.get('parts') or None
        mkey, mdl = get_model(body['upload'], parts)
        adj = {k: float(body.get(k) or (1 if k in ('width', 'height', 'depth') else 0)) for k in ('width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose')}
        if m.get('kind') == 'skinned': return _unity_fit_rigged(P, m, mkey, mdl, body, adj)
        opos, otris, lo, hi = P.geometry(m)
        pos, nrm, info = ufit.fit_static(mdl, lo, hi, up=body.get('up') or mdl.up, forward=body.get('forward') or None, scale=float(body.get('scale') or 1.0), adjust=adj)
        akey = (mkey, tuple(parts or ()))
        if akey not in ATLAS:
            ATLAS.clear()
            imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in mdl.images]
            atl, cells = atlas.pack(imgs, mdl.uv, mdl.vert_mat, size=1024); ATLAS[akey] = (atl, atlas.remap_uv(mdl.uv, mdl.vert_mat, cells, 1024))
        atl, uv = ATLAS[akey]
        b = io.BytesIO(); Image.fromarray(atl).save(b, 'PNG', compress_level=1)     # PNG: no JPEG smearing of the preview texture
        return dict(orig=dict(pos=_b64(opos, '<f4'), idx=_b64(otris, '<u4'), n=len(opos), t=len(otris)),
                    new=dict(pos=_b64(pos, '<f4'), idx=_b64(mdl.tris, '<u4'), uv=_b64(uv, '<f4'), n=len(pos), t=len(mdl.tris)),
                    atlas=base64.b64encode(b.getvalue()).decode(),
                    info=dict(forward=info['forward'], scale=float(info['scale']), pivot=info['pivot'], up=info['up']), static=True,
                    groups=dict(names=edit.AUTO_NAMES, ids=_b64(np.zeros(len(pos)), 'u1'), pivots=[[0.0, 0.0, 0.0]] * 6),
                    targets=[m['label']], target=0, height=float(hi[2] - lo[2]))


def _unity_fit_rigged(P, m, mkey, mdl, body, adj):
    """rigged character: auto-rig your model onto the character's skeleton and show it (same answer shape as the Unreal fit)"""
    from . import atlas, edit
    from .unity import skinned
    from PIL import Image
    ch = skinned.character(P, m)
    f = skinned.fit(P, m, mdl, dict(up=body.get('up') or None, forward=body.get('forward') or None, scale=float(body.get('scale') or 1.0), adjust=adj, edits=body.get('edits') or None))
    C = f['C']; pos = f['pos'] @ C.T; opos = ch['opos'] @ C.T          # the viewer shows the character frame (X left, Y forward, Z up)
    parts = body.get('parts') or None; akey = (mkey, tuple(parts or ()))
    if akey not in ATLAS:
        ATLAS.clear()
        imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in mdl.images]
        atl, cells = atlas.pack(imgs, mdl.uv, mdl.vert_mat, size=1024); ATLAS[akey] = (atl, atlas.remap_uv(mdl.uv, mdl.vert_mat, cells, 1024))
    atl, uv = ATLAS[akey]
    b = io.BytesIO(); Image.fromarray(atl).save(b, 'PNG', compress_level=1)     # PNG: no JPEG smearing of the preview texture
    info = f['info']; tris = f['tris']
    if not np.isfinite(pos).all(): raise RuntimeError("ModSwap couldn't fit your model onto this character (the numbers came out invalid). Try another model orientation in the Up/Forward options, or pick a different character.")
    return dict(orig=dict(pos=_b64(opos, '<f4'), idx=_b64(ch['otris'], '<u4'), n=len(opos), t=len(ch['otris'])),
                new=dict(pos=_b64(pos, '<f4'), idx=_b64(tris, '<u4'), uv=_b64(uv, '<f4'), n=len(pos), t=len(tris)),
                atlas=base64.b64encode(b.getvalue()).decode(),
                info=dict(forward=info['forward'], scale=float(info['scale']), pivot=[float(x) for x in info['pivot']], up=info['up']), static=bool(f['static']),
                groups=dict(names=edit.AUTO_NAMES, ids=_b64(f['vgroup'], 'u1'), pivots=[[float(x) for x in p] for p in f['piv']]),
                targets=[m['label']], target=0, height=float(ch['hi'][2] - ch['lo'][2]))


def _edit_record(body):
    """what the fit screen needs to open a finished mod again"""
    return {k: body.get(k) for k in ('family', 'target', 'up', 'forward', 'scale', 'width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose', 'parts', 'edits') if body.get(k) is not None}


def api_mod_edit(body):
    """reopen a saved mod: its model + textures go into a fresh upload, and its fit settings come back so the fit screen can restore every slider"""
    from . import mods
    sid = uuid.uuid4().hex[:12]; d = os.path.join(UPLOADS, sid)
    info = mods.open_for_edit(body['game'], body['id'], d)
    return dict(upload=sid, settings=info, file=os.path.basename(_model_file(sid)[1]))


def _active_ids(P):
    ids = []
    for v in P.installed().values():
        for x in (v.get('mods') or ([v['mod']] if v.get('mod') else [])):
            if x not in ids: ids.append(x)
    return ids


def _replace_same_character(g, P, mid, character, log):
    """a new mod for a character that already wears another of your mods replaces that one (the others stay installed)"""
    from . import mods
    if not character: return
    for m in mods.list_mods(g.id):
        if m['id'] != mid and m['id'] in _active_ids(P) and (m.get('character') or '') == character:
            log('%s already has "%s": taking that one out first...' % (character, m['name']))
            P.uninstall_mod(m['id'], log=log)


def _unity_apply(g, body, sid, name):
    import tempfile, shutil
    from . import mods
    from .unity import project as up
    def work(log):
        P = _project(g); m = P.model(body['family']); parts = body.get('parts') or None
        key, mdl = get_model(sid, parts)
        adj = {k: float(body.get(k) or (1 if k in ('width', 'height', 'depth') else 0)) for k in ('width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose')}
        params = dict(up=body.get('up') or None, forward=body.get('forward') or None, scale=float(body.get('scale') or 1.0), adjust=adj, parts=parts, edits=body.get('edits') or None)
        log('model: %s' % m['label'])
        tmp = tempfile.mkdtemp(prefix='modswap_build_')
        try:
            chlabel = re.sub(r'\s{2}\(.*\)$', '', m['label'])
            if body.get('install', True):
                running.ensure_closed(g); _replace_same_character(g, P, '', chlabel, log)
            files = P.build(m, mdl, params, tmp, log=log)           # built on top of the mods already installed; a broken model never touches the game
            zpath = os.path.join(tmp, 'recipe.zip'); P.make_recipe(m, os.path.dirname(key[0]), params, name, zpath)
            mid = mods.add(g.id, name, zpath, character=chlabel, source_dir=os.path.dirname(key[0]), edit=_edit_record(body))
            if body.get('install', True):
                log('installing the mod into the game (original is backed up)...')
                dest = P.install_files(files, name, mod_id=mid); log('done -> ' + dest); return dict(installed=dest, mod=mid)
            log('saved. You can install it any time from the game page.'); return dict(saved=True, mod=mid)
        finally: shutil.rmtree(tmp, ignore_errors=True)
    return _job(work)


def api_apply(body):
    lib = Library(); g = _game(lib, body['game']); sid = body['upload']; name = (body.get('name') or 'mod').strip() or 'mod'
    _model_file(sid)
    if g.engine == 'unity': return _unity_apply(g, body, sid, name)

    def work(log):
        parts = body.get('parts') or None
        key, m = get_model(sid, parts)
        ctx = _ctx(body['game'], body['family'], log=log); prof = ctx['prof']; P = ctx['P']
        log('character group: %s' % ctx['family'].label)
        adj = {k: float(body.get(k) or (1 if k in ('width', 'height', 'depth') else 0)) for k in ('width', 'height', 'depth', 'yaw', 'pitch', 'roll', 'dx', 'dy', 'dz', 'match_pose')}
        log('rigging %s onto the skeleton...' % os.path.basename(key[0]))
        pak = P.build(prof, m, name, forward=body.get('forward') or None, up=body.get('up') or None, scale=float(body.get('scale') or 1.0), adjust=adj, edits=body.get('edits') or None, log=log)
        from . import mods
        install = body.get('install', True)
        mid = mods.add(body['game'], name, pak, character=re.sub(r'\s{2}\(.*\)$', '', ctx['family'].label), source_dir=os.path.dirname(key[0]), edit=_edit_record(body))
        if install:
            log('installing the mod into the game...')
            running.ensure_closed(g)
            _replace_same_character(g, P, mid, re.sub(r'\s{2}\(.*\)$', '', ctx['family'].label), log)
            dest = P.install(pak, name, mod_id=mid); log('done -> ' + dest)
            for n in getattr(P, 'notes', []): log(n)
            return dict(installed=dest, mod=mid, notes=list(getattr(P, 'notes', [])))
        log('saved. You can install it any time from the game page.')
        return dict(saved=True, mod=mid)
    return _job(work)


def api_mods(gid):
    from . import mods
    lib = Library(); g = _game(lib, gid); P = _project(g)
    active = set(_active_ids(P))
    # a mod installed before the library existed has no id: show nothing for it, Undo still removes it
    return dict(mods=mods.list_mods(gid, active), anyInstalled=bool(P.installed()))


def api_mod_install(body):
    from . import mods
    lib = Library(); g = _game(lib, body['game']); P = _project(g)
    pak = mods.pak_path(body['game'], body['id']); name = body.get('name') or 'mod'
    running.ensure_closed(g)
    meta = next((m for m in mods.list_mods(body['game']) if m['id'] == body['id']), {})
    if g.engine == 'unity':
        def work(log):
            _replace_same_character(g, P, body['id'], meta.get('character') or '', log)
            return dict(installed=P.install_recipe(pak, name, mod_id=body['id'], log=log))
        return dict(job=_job(work))
    _replace_same_character(g, P, body['id'], meta.get('character') or '', lambda *a: None)
    dest = P.install(pak, name, mod_id=body['id'])
    return dict(installed=dest, notes=list(getattr(P, 'notes', [])))


def api_mod_uninstall(body):
    """take ONE mod out of the game; the other installed mods stay"""
    g = _game(Library(), body['game']); P = _project(g); mid = body['id']
    running.ensure_closed(g)
    return dict(job=_job(lambda log: dict(removed=P.uninstall_mod(mid, log=log))))


def api_mod_delete(body):
    from . import mods
    lib = Library(); g = _game(lib, body['game']); P = _project(g)
    if body['id'] in _active_ids(P): running.ensure_closed(g); P.uninstall_mod(body['id'])
    mods.delete(body['game'], body['id']); return dict(deleted=True)


def api_restore(gid):
    lib = Library(); g = _game(lib, gid); running.ensure_closed(g)
    return dict(removed=_project(g).restore())


def _closed(gid):
    g = _game(Library(), gid); running.ensure_closed(g); return g


def _ext(body):
    from . import extmods
    return extmods


def api_ext_list(gid):
    from . import extmods
    g = _game(Library(), gid); r = extmods.list_mods(g); loc = extmods.locate(g)
    r['can_install'] = bool(g.engine != 'unreal' or loc['paks']); r['engine'] = g.engine
    return r


def api_ext_install(body):
    from . import extmods
    g = _game(Library(), body['game']); running.ensure_closed(g); paths = [p for p in (body.get('paths') or []) if p]
    if not paths: raise ValueError('drop a mod file or folder first')
    try: return extmods.install(g, paths, allow_code=bool(body.get('allow_code')), name=(body.get('name') or None))
    except ValueError as e:
        if str(e).startswith('needs_confirm'): return dict(needs_confirm=str(e)[len('needs_confirm:'):].strip())
        raise


def api_market_get(body):
    """download / copy a marketplace model into this upload session so it loads exactly like a model the user dropped in"""
    from . import market
    sid = _sid(body['upload']); mid = body['id']
    def work(log):
        d = os.path.join(UPLOADS, sid); shutil.rmtree(d, ignore_errors=True); MODELS.clear(); ATLAS.clear()
        try: name, names = market.fetch(mid, d, log)
        except Exception:
            shutil.rmtree(d, ignore_errors=True); raise
        return dict(name=name, names=names)
    return _job(work)


def api_market_open():
    from . import market
    d = market.user_dir()
    if sys.platform.startswith('win'): os.startfile(d)
    else: subprocess.Popen(['xdg-open', d])
    return dict(opened=d, bundled=market.bundled_dir())


def api_reset(gid):
    """panic button: take every mod ModSwap installed in this game out again (swapped characters and mod files) and put replaced files back"""
    from . import extmods
    g = _closed(gid); n = 0
    try: n += len(_project(g).restore())
    except Exception as e: sys.stderr.write('restore failed: %r\n' % (e,))
    for m in list(extmods.list_mods(g)['mods']):
        extmods.remove(g, m['id']); n += 1
    return dict(removed=n)


def api_ext_open(body):
    from . import extmods
    g = _game(Library(), body['game']); d = extmods.mods_dir(g)
    while d and not os.path.isdir(d): d = os.path.dirname(d)
    if sys.platform.startswith('win'): os.startfile(d)
    else: subprocess.Popen(['xdg-open', d])
    return dict(opened=d)


def _win_open_dialog(title, flt):
    """Native Windows 'Open' dialog via ctypes (the bundled Python has no tkinter). Returns a path or ''."""
    import ctypes
    from ctypes import wintypes
    class OFN(ctypes.Structure):
        _fields_ = [('lStructSize', wintypes.DWORD), ('hwndOwner', wintypes.HWND), ('hInstance', wintypes.HINSTANCE), ('lpstrFilter', wintypes.LPCWSTR),
                    ('lpstrCustomFilter', wintypes.LPWSTR), ('nMaxCustFilter', wintypes.DWORD), ('nFilterIndex', wintypes.DWORD), ('lpstrFile', wintypes.LPWSTR),
                    ('nMaxFile', wintypes.DWORD), ('lpstrFileTitle', wintypes.LPWSTR), ('nMaxFileTitle', wintypes.DWORD), ('lpstrInitialDir', wintypes.LPCWSTR),
                    ('lpstrTitle', wintypes.LPCWSTR), ('Flags', wintypes.DWORD), ('nFileOffset', wintypes.WORD), ('nFileExtension', wintypes.WORD),
                    ('lpstrDefExt', wintypes.LPCWSTR), ('lCustData', wintypes.LPARAM), ('lpfnHook', ctypes.c_void_p), ('lpTemplateName', wintypes.LPCWSTR)]
    buf = ctypes.create_unicode_buffer(1024)
    o = OFN(); o.lStructSize = ctypes.sizeof(OFN); o.lpstrFilter = flt; o.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR); o.nMaxFile = 1024
    o.lpstrTitle = title; o.Flags = 0x00080000 | 0x00001000 | 0x00000800 | 0x00000008        # explorer | file must exist | path must exist | no change dir
    return buf.value if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(o)) else ''


def pick_exe():
    if sys.platform.startswith('win'):
        try: return dict(path=_win_open_dialog('Pick the game .exe', 'Game (*.exe)\0*.exe\0All files\0*.*\0\0'))
        except Exception: pass
    try:
        import tkinter
        from tkinter import filedialog
        r = tkinter.Tk(); r.withdraw(); r.attributes('-topmost', True)
        p = filedialog.askopenfilename(title='Pick the game .exe', filetypes=[('Game', '*.exe'), ('All', '*.*')]); r.destroy()
        return dict(path=p or '')
    except Exception as e:
        return dict(path='', error='no file dialog here, paste the path instead')


def _extract_zip(zpath, dest, depth=0, budget=None):
    """Unpack a model zip flat into dest (models, textures, .mtl/.bin). Handles nested zips and same-named files in different folders."""
    from .modelio import MODEL_EXT, IMAGE_EXT
    budget = budget if budget is not None else [0]; names = []
    keep = MODEL_EXT + IMAGE_EXT + ('.bin', '.mtl')
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            parts = [x for x in info.filename.replace('\\', '/').split('/') if x and x not in ('.', '..') and not x.startswith('__MACOSX')]
            if info.is_dir() or not parts or parts[-1].startswith('._'): continue
            base = parts[-1]; low = base.lower()
            if low.endswith('.zip') and depth < 3:
                budget[0] += info.file_size
                if budget[0] > 800 * 1024 * 1024: raise ValueError('zip is too big')
                tmp = os.path.join(dest, '_nested_%d.zip' % len(names))
                with z.open(info) as src, open(tmp, 'wb') as out: shutil.copyfileobj(src, out)
                try: names += _extract_zip(tmp, dest, depth + 1, budget)
                except zipfile.BadZipFile: os.path.exists(tmp) and os.remove(tmp)
                continue
            if not low.endswith(keep): continue
            budget[0] += info.file_size
            if budget[0] > 800 * 1024 * 1024: raise ValueError('zip is too big')
            out_name = base
            if os.path.exists(os.path.join(dest, out_name)) and len(parts) > 1: out_name = parts[-2] + '__' + base   # same name in another folder
            k = 1
            while os.path.exists(os.path.join(dest, out_name)): out_name = '%d_%s' % (k, base); k += 1
            with z.open(info) as src, open(os.path.join(dest, out_name), 'wb') as out: shutil.copyfileobj(src, out)
            names.append(out_name)
    os.remove(zpath); return names


# ------------------------------------------------------------------ http
class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a): pass

    def _send(self, obj, code=200, ctype='application/json'):
        b = obj if isinstance(obj, bytes) else (obj.encode() if isinstance(obj, str) else json.dumps(obj).encode())
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0); return self.rfile.read(n) if n else b''

    def _guard(self, fn):
        try: self._send(fn())
        except Exception as e:
            try: sys.stderr.write(traceback.format_exc() + '\n'); sys.stderr.flush()        # lands in %APPDATA%\\ModSwap\\modswap.log
            except Exception: pass
            self._send(dict(error=_msg(e), kind=type(e).__name__), 400)

    def _static(self, path):
        rel = 'index.html' if path in ('', '/') else unquote(path).lstrip('/')
        full = os.path.normpath(os.path.join(WEB, rel))
        if not full.startswith(WEB) or not os.path.isfile(full): return self._send(dict(error='not found'), 404)
        ct = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        self._send(open(full, 'rb').read(), ctype=ct + ('; charset=utf-8' if ct.startswith('text') or ct.endswith('javascript') else ''))

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == '/api/games': return self._guard(lambda: dict(games=[_game_json(g) for g in Library().list()]))
        if u.path == '/api/mods': return self._guard(lambda: api_mods(q.get('game', [''])[0]))
        if u.path == '/api/market':
            from . import market
            return self._guard(market.listing)
        if u.path == '/api/sketchfab':
            from . import market
            return self._guard(lambda: market.sketchfab_search(q.get('q', [''])[0], q.get('sort', ['popular'])[0], q.get('cat', [''])[0], q.get('cursor', [''])[0]))
        if u.path == '/api/sketchfab_status':
            from . import sketchfab
            return self._guard(sketchfab.status)
        if u.path == '/api/market_preview':
            from . import market
            try: jpg = market.preview_jpeg(q.get('id', [''])[0])
            except Exception: jpg = None
            if not jpg: return self._send(dict(error='no preview'), 404)
            return self._send(jpg, ctype='image/jpeg')
        if u.path == '/api/ext_mods': return self._guard(lambda: api_ext_list(q.get('game', [''])[0]))
        if u.path == '/api/art':
            g = Library().games.get(q.get('id', [''])[0]); f = find_art(g.appid) if g else None
            if not f: return self._send(dict(error='no art'), 404)
            return self._send(open(f, 'rb').read(), ctype=mimetypes.guess_type(f)[0] or 'image/jpeg')
        if u.path == '/api/formats':
            from .modelio import FORMATS
            from .importers.generic import find_blender
            return self._guard(lambda: dict(formats=[dict(name=a, ext=b, how=c) for a, b, c in FORMATS], blender=bool(find_blender())))
        if u.path == '/api/job':
            j = JOBS.get(q.get('id', [''])[0]); return self._send(j or dict(error='no such job'), 200 if j else 404)
        if u.path.startswith('/api/'): return self._send(dict(error='not found'), 404)
        self._static(u.path)

    def do_POST(self):
        u = urlparse(self.path); raw = self._body()
        try: body = json.loads(raw or b'{}')
        except Exception: body = {}
        r = u.path
        if r == '/api/scan_steam':
            def f():
                lib = Library(); n = lib.scan_steam()
                try: n += lib.scan_others()                                    # Epic / GOG / Xbox / Ubisoft
                except Exception as e: sys.stderr.write('launcher scan failed: %r\n' % (e,))
                return dict(new=n, games=[_game_json(g) for g in lib.list()])
            return self._guard(f)
        if r == '/api/add':
            def f():
                lib = Library(); g = lib.add_exe(body['exe'].strip().strip('"'), body.get('name') or None)
                return dict(game=_game_json(g), games=[_game_json(x) for x in lib.list()])
            return self._guard(f)
        if r == '/api/remove':
            def f():
                lib = Library(); lib.remove(body['game']); return dict(games=[_game_json(x) for x in lib.list()])
            return self._guard(f)
        if r == '/api/redetect': return self._guard(lambda: api_redetect(body['game']))
        if r == '/api/pick_exe': return self._guard(pick_exe)
        if r == '/api/characters': return self._guard(lambda: dict(job=api_characters(body['game'])))
        if r == '/api/inspect': return self._guard(lambda: api_inspect(body['upload']))
        if r == '/api/fit': return self._guard(lambda: api_fit(body))
        if r == '/api/apply': return self._guard(lambda: dict(job=api_apply(body)))
        if r == '/api/restore': return self._guard(lambda: api_restore(body['game']))
        if r == '/api/mod_install': return self._guard(lambda: api_mod_install(body))
        if r == '/api/mod_uninstall': return self._guard(lambda: api_mod_uninstall(body))
        if r == '/api/mod_edit': return self._guard(lambda: api_mod_edit(body))
        if r == '/api/mod_delete': return self._guard(lambda: api_mod_delete(body))
        if r == '/api/ext_install': return self._guard(lambda: api_ext_install(body))
        if r == '/api/ext_toggle': return self._guard(lambda: _ext(body).toggle(_closed(body['game']), body['id']))
        if r == '/api/ext_remove': return self._guard(lambda: _ext(body).remove(_closed(body['game']), body['id']))
        if r == '/api/market_get': return self._guard(lambda: dict(job=api_market_get(body)))
        if r == '/api/sketchfab_connect':
            from . import sketchfab
            return self._guard(lambda: sketchfab.connect(body.get('token')) if (body.get('token') or '').strip() else sketchfab.disconnect())
        if r == '/api/market_open': return self._guard(api_market_open)
        if r == '/api/reset_game': return self._guard(lambda: api_reset(body['game']))
        if r == '/api/ext_open': return self._guard(lambda: api_ext_open(body))
        self._send(dict(error='not found'), 404)

    def do_PUT(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path != '/api/upload': return self._send(dict(error='not found'), 404)

        def f():
            sid = _sid(q['sid'][0]); name = os.path.basename(q['name'][0].replace('\\', '/')) or 'file'
            d = os.path.join(UPLOADS, sid); os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name); open(p, 'wb').write(self._body())
            names = [name]
            if name.lower().endswith('.zip'): names = _extract_zip(p, d)
            return dict(ok=True, names=names)
        self._guard(f)

    def do_DELETE(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        sid = _sid(q.get('sid', [''])[0])
        shutil.rmtree(os.path.join(UPLOADS, sid), ignore_errors=True); MODELS.clear(); ATLAS.clear()
        self._send(dict(ok=True))


def serve(port=8765, open_browser=True, watch_stdin=False):
    shutil.rmtree(UPLOADS, ignore_errors=True); os.makedirs(UPLOADS, exist_ok=True)
    for p in range(port, port + 20):
        try: srv = ThreadingHTTPServer(('127.0.0.1', p), H); break
        except OSError: continue
    else: raise RuntimeError('no free port')
    srv.daemon_threads = True
    url = 'http://127.0.0.1:%d/' % p
    print('ModSwap is running at', url, ' (close this window to quit)', flush=True)
    if watch_stdin:      # the desktop app owns this process: when it closes (stdin hits EOF) we quit too
        def _watch():
            try: sys.stdin.read()
            except Exception: pass
            os._exit(0)
        threading.Thread(target=_watch, daemon=True).start()
    if open_browser: threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
