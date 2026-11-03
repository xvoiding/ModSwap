"""One Unity game = one UnityProject: list its swappable models, fit yours onto one, patch the asset files, install with a backup, undo."""
import os, re, io, gc, json, time, shutil, hashlib, zipfile, tempfile
import numpy as np
from PIL import Image
from ..games import library
from . import scan as uscan, mesh as umesh, patch, fit as ufit, skinned, orient


def _sha(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def _close_env(env):
    """UnityPy keeps every file it loaded open until Python's garbage collector gets round to it. On Windows an open file can't be deleted or renamed,
    so close the streams ourselves the moment we're done."""
    seen = set()

    def walk(f, depth=0):
        if f is None or id(f) in seen or depth > 5: return
        seen.add(id(f))
        for a in ('reader', 'stream', 'fp', 'file'):
            r = getattr(f, a, None)
            if r is None or isinstance(r, (str, bytes, int)): continue
            st = getattr(r, 'stream', None) or r
            for x in (st, r):
                c = getattr(x, 'close', None)
                if callable(c):
                    try: c()
                    except Exception: pass
            if not isinstance(r, (io.IOBase,)) and hasattr(r, 'files'): walk(r, depth + 1)
        fs = getattr(f, 'files', None)
        if isinstance(fs, dict):
            for v in list(fs.values()): walk(v, depth + 1)
    try: walk(env)
    except Exception: pass


def _slug(s): return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:40] or 'mod'


class UnityProject:
    def __init__(self, game, cache_root=None):
        self.game = game
        self.dir = os.path.join(cache_root or os.path.join(library.config_dir(), 'cache'), game.id); os.makedirs(self.dir, exist_ok=True)
        self.backup = os.path.join(self.dir, 'backup'); os.makedirs(self.backup, exist_ok=True)
        self.data = uscan.data_dir(game.root)
        self._env = {}; self._objc = {}; self._geo = {}; self._rot = {}

    # ------------------------------------------------------------ scan
    def scan(self, force=False, log=print):
        cache = os.path.join(self.dir, 'unity_scan.json')
        if not force and getattr(self, '_res', None): return self._res
        if not force and os.path.exists(cache):
            try:
                r = uscan.load(cache)
                if r.get('ver', 1) >= 3: self._res = r; return r
            except Exception: pass
        res = uscan.scan(self.game.root, log=log, resolve=self.orig_path)           # reads the original files (the backups, if a mod is installed)
        uscan.save(res, cache); self._res = res; gc.collect(); return res

    def models(self, log=print): return self.scan(log=log)['models']

    def model(self, i):
        ms = self.models()
        i = int(i)
        if not 0 <= i < len(ms): raise ValueError('that model is not in the list any more, press Rescan')
        return ms[i]

    def describe(self, log=print):
        out = []
        for m in self.models(log):
            note = []; cat = m.get('cat', 'prop')
            note.append({'character': 'person / creature', 'vehicle': 'vehicle', 'weapon': 'weapon', 'prop': 'object', 'scenery': 'scenery', 'level': 'level geometry', 'junk': 'unnamed mesh'}.get(cat, 'object'))
            v = m['verts']; note.append('%s verts' % ('%.1fk' % (v / 1000.0) if v >= 1000 else v))
            if len(m['parts']) > 1: note.append('%d parts' % len(m['parts']))
            if m['shared_mesh']: note.append('also changes %d other copies' % m['shared_mesh'])
            label = m.get('pretty') or m['label']
            if label == '?' or not label.strip(): label = m.get('main_name') or 'Unnamed'
            out.append(dict(index=m['index'], label='%s  (%d %s)' % (label, m['instances'], 'copy' if m['instances'] == 1 else 'copies'),
                            meshes=len(m['parts']), body=[p['name'] for p in m['parts']][:8], layered=0, note='  \u00B7  '.join(note),
                            rigged=m.get('kind') == 'skinned', cat=cat, hidden=cat not in ('character', 'vehicle', 'weapon', 'prop')))
        return out

    # ------------------------------------------------------------ files
    def orig_path(self, rel):
        man = self._manifest()['installed']; dst = os.path.join(self.data, rel)
        b = man.get(dst, {}).get('backup')
        return b if b and os.path.exists(b) else dst

    def _both(self, rel, current=False):
        """(env, {path_id: object}) of one serialized file. Default: the ORIGINAL contents (the backup, when mods are installed).
        current=True: the file as it is in the game right now, so a new mod is added on top of the mods already installed."""
        import UnityPy
        p = os.path.join(self.data, rel) if current else self.orig_path(rel); key = (p, os.path.getmtime(p), bool(current))
        if key not in self._env:
            while len(self._env) >= 3: k0 = next(iter(self._env)); _close_env(self._env.pop(k0)); self._objc.pop(k0, None)
            self._env[key] = UnityPy.load(p)
        if key not in self._objc: self._objc[key] = {o.path_id: o for o in self._env[key].objects}
        return self._env[key], self._objc[key]

    def _load(self, rel, current=False): return self._both(rel, current)[0]

    def release(self):
        """let go of every asset file we have open (the originals / backups we read from)"""
        for e in list(self._env.values()): _close_env(e)
        self._env.clear(); self._objc.clear(); self._geo.clear(); self._rot.clear(); gc.collect()

    # ------------------------------------------------------------ the original model's shape
    def geometry(self, m):
        """-> (pos_cm (N,3) in the viewer frame, tris, lo, hi) for the first copy of the model"""
        key = (m['file'], m['top'])
        if key in self._geo: return self._geo[key]
        env = self._load(m['file']); O = {o.path_id: o for o in env.objects}
        P = []; T = []; off = 0; cache = {}
        for mesh_id, M in m['place']:
            if mesh_id not in cache:
                try: cache[mesh_id] = umesh.read_geometry(O[mesh_id])
                except ValueError: cache[mesh_id] = None
            g = cache[mesh_id]
            if g is None: continue
            pos, tris = g
            q = (np.c_[pos.astype(np.float64), np.ones(len(pos))] @ np.array(M).T)[:, :3]
            P.append(q); T.append(tris + off); off += len(pos)
        if not P: raise ValueError('could not read this model\'s meshes')
        R = orient.snap(orient.world_rotation(orient.transform_table(O), m['top']))        # the rotation that stands the model up in the game (a -90 degree turn on its GameObject, ...)
        self._rot[key] = R
        pos = ufit.to_char(np.concatenate(P), 1.0, R); tris = np.concatenate(T)
        res = (pos, tris, pos.min(0), pos.max(0)); self._geo[key] = res; return res

    def orientation(self, m):
        """-> (R, M of the main mesh relative to the top GameObject): how the main mesh's own vertex space sits in the standing frame"""
        self.geometry(m); R = self._rot[(m['file'], m['top'])]
        M = next((np.array(M) for mid, M in m['place'] if mid == m['main']), np.eye(4))
        return R, M

    # ------------------------------------------------------------ build
    def build(self, m, model, params, out_dir, log=print):
        """patch the asset file(s); returns {relative file: patched temp file}"""
        if m.get('kind') == 'skinned': return skinned.build(self, m, model, params, out_dir, log)
        from .. import atlas
        env = self._load(m['file'], current=True); O = {o.path_id: o for o in env.objects}        # patch what is in the game now, so mods stack
        _, _, lo, hi = self.geometry(m)
        pos_c, nrm_c, info = ufit.fit_static(model, lo, hi, up=params.get('up') or model.up, forward=params.get('forward') or None,
                                             scale=float(params.get('scale') or 1.0), adjust=params.get('adjust') or {})
        R, Mm = self.orientation(m)
        P, Nn, tris = ufit.unity_arrays(pos_c, nrm_c, model.tris, R=R, M=Mm)
        imgs = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in model.images]
        atl, cells = atlas.pack(imgs, model.uv, model.vert_mat, size=2048)
        uv = atlas.remap_uv(model.uv, model.vert_mat, cells, 2048); uv[:, 1] = 1.0 - uv[:, 1]
        log('replacing the model (%d vertices)...' % len(P))
        for p in m['parts']:
            ns = max(1, len(p['mats']))
            if p['mesh'] == m['main']: patch.set_mesh(O[p['mesh']], P, Nn, uv, tris, n_sub=ns, log=log)
            else: patch.tiny_mesh(O[p['mesh']], n_sub=ns)
        tex = self._main_texture(O, m['main_mat'])
        if tex is not None:
            log('writing the texture...')
            patch.set_texture(O[tex], Image.fromarray(atl), 'DXT1'); self._white(O, m['main_mat'])
        else: log('note: could not find this model\'s texture, it will look untextured')
        os.makedirs(out_dir, exist_ok=True); out = os.path.join(out_dir, m['file'])
        log('saving %s...' % m['file'])
        with open(out, 'wb') as f: f.write(env.file.save())
        _close_env(env); self.release()
        return {m['file']: out}

    @staticmethod
    def _main_texture(O, mat_pid):
        if not mat_pid or mat_pid not in O: return None
        mat = O[mat_pid].read(); first = None
        for k, v in mat.m_SavedProperties.m_TexEnvs:
            nm = getattr(k, 'name', k); tx = v.m_Texture
            if tx.m_FileID != 0 or tx.m_PathID not in O: continue
            if nm in ('_MainTex', '_BaseMap', '_BaseColorMap', '_Diffuse'): return tx.m_PathID
            first = first or tx.m_PathID
        return first

    @staticmethod
    def _white(O, mat_pid):
        try:
            t = O[mat_pid].read_typetree(); changed = False
            for e in t['m_SavedProperties']['m_Colors']:
                key = e[0] if isinstance(e, (list, tuple)) else e['first']; val = e[1] if isinstance(e, (list, tuple)) else e['second']
                nm = key.get('name') if isinstance(key, dict) else key
                if nm in ('_Color', '_BaseColor', '_TintColor'): val.update(r=1.0, g=1.0, b=1.0, a=1.0); changed = True
            if changed: O[mat_pid].save_typetree(t)
        except Exception: pass

    # ------------------------------------------------------------ recipes (a saved mod = your model files + how it was fitted)
    def make_recipe(self, m, upload_dir, params, name, dest):
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('recipe.json', json.dumps(dict(kind='unity', name=name, model=m, params=params)))
            for f in os.listdir(upload_dir):
                p = os.path.join(upload_dir, f)
                if os.path.isfile(p): z.write(p, 'model/' + f)
        return dest

    def build_recipe(self, zpath, out_dir, log=print):
        from ..modelio import load_model, MODEL_EXT
        tmp = tempfile.mkdtemp(prefix='modswap_recipe_')
        with zipfile.ZipFile(zpath) as z: z.extractall(tmp)
        rec = json.load(open(os.path.join(tmp, 'recipe.json'))); d = os.path.join(tmp, 'model')
        order = ('.fbx', '.glb', '.gltf', '.obj', '.dae', '.vrm', '.blend', '.ply', '.stl')
        files = sorted([f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in MODEL_EXT], key=lambda f: (order.index(os.path.splitext(f)[1].lower()) if os.path.splitext(f)[1].lower() in order else 99, f))
        model = load_model(os.path.join(d, files[0]), d)
        if rec['params'].get('parts'): model = model.subset(rec['params']['parts'])
        files_out = self.build(rec['model'], model, rec['params'], out_dir, log=log)
        shutil.rmtree(tmp, ignore_errors=True)
        return rec, files_out

    # ------------------------------------------------------------ install / undo
    def install_files(self, files, name='mod', mod_id=''):
        """put the built files into the game. Mods stack: whatever other mods are installed stay (each file keeps ONE pristine backup, made the first time we touch it)"""
        man = self._manifest(); dests = []
        for rel, path in files.items():
            dst = os.path.join(self.data, rel); ent = man['installed'].get(dst)
            if ent and ent.get('backup') and os.path.exists(ent['backup']): bk = ent['backup']
            else:
                bk = os.path.join(self.backup, rel.replace('/', '__').replace('\\', '__') + '.orig'); shutil.copy2(dst, bk)
            self._put(path, dst)
            prev = (ent or {}).get('mods') or ([ent['mod']] if ent and ent.get('mod') else [])
            man['installed'][dst] = dict(name=name, mod=mod_id, mods=[x for x in prev if x != mod_id] + ([mod_id] if mod_id else []), time=time.time(), backup=bk, sha=_sha(dst)); dests.append(dst)
        if mod_id: man['order'] = [x for x in man.get('order', []) if x != mod_id] + [mod_id]
        self._save(man); return ', '.join(dests)

    def install_recipe(self, zpath, name='mod', mod_id='', log=print):
        out = tempfile.mkdtemp(prefix='modswap_build_')
        try:
            rec, files = self.build_recipe(zpath, out, log=log)          # built on top of what is installed now
            self.release()                                               # the build read game files: close them before we write over them
            return self.install_files(files, name, mod_id)
        finally: self.release(); shutil.rmtree(out, ignore_errors=True)

    def active_ids(self):
        ids = []
        for v in self._manifest()['installed'].values():
            for x in (v.get('mods') or ([v['mod']] if v.get('mod') else [])):
                if x not in ids: ids.append(x)
        return ids

    def uninstall_mod(self, mid, log=print):
        """take ONE mod out. The other installed mods stay: the originals go back, then the others are re-applied from their saved recipes"""
        from .. import mods as modlib
        order = [x for x in (self._manifest().get('order') or []) if x in self.active_ids()] + [x for x in self.active_ids() if x not in (self._manifest().get('order') or [])]
        if mid not in order: return []
        keep = [x for x in order if x != mid]
        info = {m['id']: m for m in modlib.list_mods(self.game.id)}
        gone = self.restore()
        for x in keep:
            try: zp = modlib.pak_path(self.game.id, x)
            except ValueError: log('skipping a mod that no longer exists'); continue
            log('putting back %s...' % info.get(x, {}).get('name', 'another mod'))
            self.install_recipe(zp, info.get(x, {}).get('name', 'mod'), x, log=log)
        return gone

    def installed(self): return self._manifest()['installed']

    def _put(self, src, dst):
        """copy over a game file; the game keeps its files open while it runs, so wait a moment and say plainly what to do if it does not let go"""
        last = None
        for i in range(8):
            try: shutil.copy2(src, dst); return
            except PermissionError as e: last = e; time.sleep(0.4)
            except OSError as e:
                if getattr(e, 'winerror', 0) in (5, 32, 33): last = e; time.sleep(0.4)
                else: raise RuntimeError(self._locked_msg(dst, e, 'install'))
        raise RuntimeError(self._locked_msg(dst, last, 'install'))

    def _locked_msg(self, dst, e, what):
        busy = getattr(e, 'winerror', 0) in (5, 32, 33) or isinstance(e, PermissionError)
        n = os.path.basename(dst)
        if busy: return 'Close %s completely first (check Task Manager), it still has %s open. Then press %s again.' % (self.game.name or 'the game', n, 'Restore' if what == 'restore' else 'Install')
        return 'could not %s %s: %s' % (what, n, e)

    def restore(self):
        self.release()                                       # we may still hold the backups open from building/scanning: Windows won't let us delete those
        try:
            for f in os.listdir(self.backup):
                if '.orig.old' in f:
                    try: os.remove(os.path.join(self.backup, f))
                    except OSError: pass
        except OSError: pass
        man = self._manifest(); gone = []
        for dst, v in list(man['installed'].items()):
            bk = v.get('backup')
            try:
                if os.path.exists(dst) and bk and os.path.exists(bk) and _sha(dst) == v.get('sha'): self._put(bk, dst)       # unchanged since we wrote it: put the original back
            except OSError as e: raise RuntimeError(self._locked_msg(dst, e, 'restore'))
            if bk and os.path.exists(bk): self._drop(bk)     # a leftover backup copy is harmless, never let it block the restore
            gone.append(dst); del man['installed'][dst]
        man['order'] = []
        self._save(man); self.release(); return gone

    @staticmethod
    def _drop(path):
        for i in range(6):
            try: os.remove(path); return True
            except FileNotFoundError: return True
            except OSError:
                gc.collect(); time.sleep(0.25)
        try: os.replace(path, path + '.old%d' % int(time.time()))       # still held by something: move it out of the way instead (cleaned up next time)
        except OSError: pass
        return False

    def _manifest(self):
        p = os.path.join(self.dir, 'installed.json')
        return json.load(open(p)) if os.path.exists(p) else dict(installed={})

    def _save(self, man): json.dump(man, open(os.path.join(self.dir, 'installed.json'), 'w'), indent=1)
