"""Marvel's Spider-Man Remastered as a ModSwap game: the same methods the app already calls on a Unity / Unreal project.
Characters are the game's suits. A mod = the suit's model + its colour / normal / gloss textures, installed through asset_archive\\toc (see install.py)."""
import os, io, json, zipfile, tempfile, shutil
import numpy as np
from . import model as M, rig as R, swap as S, materials as MT, pipeline as PL
from .install import Installer, find_suits, suit_model_path

TITLES = dict(classic='Classic Suit', noir='Spider-Man Noir Suit', punk='Spider-Punk Suit', scarlet='Scarlet Spider Suit', stealth='Stealth (Big Time) Suit', ironspider='Iron Spider Suit',
              velocity='Velocity Suit', vintage='Vintage Comic Suit', secretwar='Secret War Suit', fearitself='Fear Itself Suit', antiock='Anti-Ock Suit', base='Spider-Man (no suit)',
              advanced='Advanced Suit', advanced2='Advanced Suit 2.0', crimson='Crimson Cowl Suit', negative='Negative Suit', electric='Electrically Insulated Suit',
              webwarrior='Web Warrior Suit', upgraded='Upgraded Suit', spirit='Spirit Suit', homemade='Homemade Suit', ultimate='Ultimate Suit', miles='Miles Morales')


def _title(suit): return TITLES.get(suit) or suit.replace('_', ' ').title() + ' Suit'


class SpiderManProject:
    def __init__(self, game, cache_root=None):
        self.game = game; self.I = Installer(game.root); self._suits = {}; self.notes = []

    # ------------------------------------------------------------ the game's suits
    def suits(self):
        toc = self.I.toc_for_reading()
        try: return find_suits(toc)
        finally: toc.close()

    def describe(self, log=print):
        out = []
        for i, s in enumerate(self.suits()):
            out.append(dict(index=i, label=_title(s), meshes=1, body=[os.path.basename(suit_model_path(s))], layered=0, note='suit model + its textures', rigged=True, cat='character', hidden=False))
        if not out: raise ValueError('no suits found in this game folder (asset_archive\\toc is unreadable or from another game version)')
        log('%d suits' % len(out)); return out

    def model(self, i):
        s = self.suits(); i = int(i)
        if not 0 <= i < len(s): raise ValueError('that suit is not in the list any more, press Rescan')
        return dict(index=i, suit=s[i], label=_title(s[i]), path=suit_model_path(s[i]))

    def _load(self, m):
        """cached: the ORIGINAL suit (model, rig, material slots, the slot to re-skin, its outline for the viewer)"""
        c = self._suits.get(m['suit'])
        if c is not None: return c
        toc = self.I.toc_for_reading()
        try:
            i = toc.find(m['path']); orig = M.Model(toc.read(i, self.I.ad)); rows = MT.slots(orig, toc, self.I.ad)
        finally: toc.close()
        rg, ref = S.lod0_rig(orig); slot = MT.pick_single_texture_slot(rows, m['suit'])
        if slot is None: raise ValueError('this suit has no plain colour+normal+gloss material ModSwap can re-skin')
        P = []; T = []; off = 0; idx = orig.indices(); st = orig.streams()
        for mesh in orig.meshes()[:23]:
            if not mesh.vertex_count: continue
            P.append(st['pos'][mesh.vertex_start:mesh.vertex_start + mesh.vertex_count]); T.append(orig.triangles(mesh, idx) + off); off += mesh.vertex_count
        pos = R.from_model_space(np.concatenate(P)) * 100.0                         # the viewer's frame: X left, Y forward, Z up, centimetres
        c = dict(orig=orig, rows=rows, slot=slot, rig=rg, opos=pos, otris=np.concatenate(T).astype(np.int64)); self._suits[m['suit']] = c; return c

    def geometry(self, m):
        c = self._load(m); return c['opos'], c['otris'], c['opos'].min(0), c['opos'].max(0)

    # ------------------------------------------------------------ fit (preview) and build
    def fit(self, m, model, params, atlas_size=1024, log=lambda *a: None):
        c = self._load(m); p = params or {}
        f = S.fit(c['orig'], model, up=p.get('up') or model.up, forward=p.get('forward') or None, scale=float(p.get('scale') or 1.0), adjust=p.get('adjust'),
                  edits=p.get('edits') or None, atlas_size=atlas_size, log=log, rig=c['rig'])
        f['pos_view'] = f['pos_rig'] * 100.0; return f

    def build(self, m, model, params, out_dir, log=print):
        """-> {asset path: temp file with its new bytes}"""
        c = self._load(m); f = self.fit(m, model, params, atlas_size=int((params or {}).get('tex_size') or 1024), log=log)
        toc = self.I.toc_for_reading()
        try: items, _ = PL.make_assets(toc, self.I.ad, m['path'], c['orig'], c['rows'], c['slot'], f, log=log)
        finally: toc.close()
        files = {}
        for k, (path, data) in enumerate(items):
            fn = os.path.join(out_dir, 'asset_%d.bin' % k)
            with open(fn, 'wb') as fh: fh.write(data)
            files[path] = fn
        return files

    # ------------------------------------------------------------ recipes (what the library keeps: the model + settings, rebuilt on install)
    def make_recipe(self, m, upload_dir, params, name, dest):
        meta = dict(suit=m['suit'], name=name, params={k: v for k, v in (params or {}).items()})
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('recipe.json', json.dumps(meta))
            for f in sorted(os.listdir(upload_dir)):
                p = os.path.join(upload_dir, f)
                if os.path.isfile(p): z.write(p, 'model/' + f)
        return dest

    def install_files(self, files, name='mod', mod_id=''):
        items = [(path, open(fn, 'rb').read()) for path, fn in files.items()]
        self.I.install_group(mod_id or 'mod', items, name)
        return os.path.join(self.I.mods_dir, 'modswap_%s_0' % (mod_id or 'mod'))

    def install_recipe(self, zpath, name='mod', mod_id='', log=print):
        from ..modelio import load_model, MODEL_EXT
        tmp = tempfile.mkdtemp(prefix='modswap_recipe_')
        try:
            with zipfile.ZipFile(zpath) as z:
                meta = json.loads(z.read('recipe.json')); z.extractall(tmp)
            d = os.path.join(tmp, 'model'); order = ('.fbx', '.glb', '.gltf', '.obj', '.dae', '.vrm', '.blend', '.ply', '.stl', '.3mf', '.off')
            files = sorted((f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in MODEL_EXT), key=lambda f: (order.index(os.path.splitext(f)[1].lower()) if os.path.splitext(f)[1].lower() in order else 99, f))
            mdl = load_model(os.path.join(d, files[0]), d); parts = (meta.get('params') or {}).get('parts')
            if parts: mdl = mdl.subset(parts)
            m = self.model(self.suits().index(meta['suit'])); out = os.path.join(tmp, 'out'); os.makedirs(out)
            built = self.build(m, mdl, meta.get('params') or {}, out, log=log)
            return self.install_files(built, name, mod_id=mod_id)
        finally: shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------ what is installed
    def installed(self):
        return {r['target']: dict(mod=r.get('group', r['id']), name=r['name']) for r in self.I.installed() if r['target'].endswith('.model')}

    def active_ids(self): return list(dict.fromkeys(r.get('group', r['id']) for r in self.I.installed()))

    def uninstall_mod(self, mid, log=print):
        self.I.uninstall(mid); log('removed'); return mid

    def restore(self):
        had = [r['name'] for r in self.I.installed() if r['target'].endswith('.model')]; self.I.restore(); return had

    def release(self): self._suits.clear()
