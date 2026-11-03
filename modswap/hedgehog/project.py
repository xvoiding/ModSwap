"""Sonic Frontiers as a ModSwap game: the same methods the app already calls on the Spider-Man / Unity projects. Characters are the character .pac files that hold a full set of
textures (a mod = the rewritten .pac); see sonic.py for how one is built and install.py for how it goes into the game."""
import os, json, zipfile, tempfile, shutil
import numpy as np
from . import pacx, sonic, hemodel as H, hewrite as W
from .install import Installer, CHAR_DIR

PRETTY = dict(sonic='Sonic', amy='Amy', knuckles='Knuckles', tails='Tails', big='Big', eggman='Dr. Eggman', supersonic='Super Sonic', soniccyber='Sonic (Cyber Space)', sonic_crown='Sonic (Crown)')
MAX_PAC = 40 * 1024 * 1024


def _title(stem): return PRETTY.get(stem.lower()) or stem.replace('_', ' ').title()


class SonicProject:
    def __init__(self, game, cache_root=None):
        self.game = game; self.I = Installer(game.root); self._chars = {}; self._list = None; self.notes = []

    def _files(self):
        return sorted(f for f in os.listdir(self.I.char_dir) if f.lower().endswith('.pac') and os.path.getsize(os.path.join(self.I.char_dir, f)) <= MAX_PAC)

    def _character(self, rel):
        if rel not in self._chars:
            self._chars[rel] = sonic.Character(self.I.read_original(rel))
        return self._chars[rel]

    def scan(self, log=print):
        if self._list is not None: return self._list
        out = []; files = self._files()
        for i, f in enumerate(files):
            rel = os.path.join(CHAR_DIR, f)
            try:
                ch = self._character(rel); ok, why = ch.texture_status()
            except Exception: continue                                          # not a character file (effects, scenery ...)
            out.append(dict(rel=rel, stem=os.path.splitext(f)[0], label=_title(os.path.splitext(f)[0]), model=ch.name, ok=ok, why=why, meshes=len(ch.model0.meshes()), host=ch.host))
            log('%d / %d: %s' % (i + 1, len(files), f))
        self._list = out; return out

    def describe(self, log=print):
        rows = self.scan(log)
        if not rows: raise ValueError('no character files found in %s' % self.I.char_dir)
        return [dict(index=i, label=r['label'], meshes=r['meshes'], body=[r['model']], layered=0, rigged=True, cat='character', hidden=not r['ok'],
                     note=('character model + its three textures' if r['ok'] else 'model only: ' + r['why'])) for i, r in enumerate(rows)]

    def model(self, i):
        rows = self.scan(); i = int(i)
        if not 0 <= i < len(rows): raise ValueError('that character is not in the list any more, press Rescan')
        r = rows[i]
        if not r['ok']: raise ValueError('%s cannot be swapped yet: %s' % (r['label'], r['why']))
        return dict(index=i, rel=r['rel'], label=r['label'], stem=r['stem'])

    # ------------------------------------------------------------ the original character for the viewer
    def geometry(self, m):
        ch = self._character(m['rel']); P = []; T = []; off = 0
        for me in ch.model0.meshes():
            if 'outline' in me.material or 'aura' in me.material: continue
            P.append(me.positions()); T.append(me.faces + off); off += me.vertex_count
        pos = W.from_model_space(np.concatenate(P)) * 100.0                      # viewer frame: X left, Y forward, Z up, centimetres
        return pos, np.concatenate(T).astype(np.int64), pos.min(0), pos.max(0)

    def fit(self, m, model, params, atlas_size=1024, log=lambda *a: None):
        p = params or {}; ch = self._character(m['rel'])
        f = ch.fit(model, up=p.get('up') or model.up, forward=p.get('forward') or None, scale=float(p.get('scale') or 1.0), adjust=p.get('adjust'), edits=p.get('edits') or None, atlas_size=atlas_size, log=log)
        f['pos_view'] = f['pos_rig'] * 100.0; return f

    def build(self, m, model, params, out_dir, log=print):
        """-> {file (relative to the game): temp file with its new bytes}"""
        ch = self._character(m['rel']); f = self.fit(m, model, params, atlas_size=1024, log=log)
        data, rep = ch.build(f, log=log); fn = os.path.join(out_dir, 'character.pac')
        with open(fn, 'wb') as fh: fh.write(data)
        return {m['rel']: fn}

    # ------------------------------------------------------------ recipes
    def make_recipe(self, m, upload_dir, params, name, dest):
        meta = dict(stem=m['stem'], name=name, params={k: v for k, v in (params or {}).items()})
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('recipe.json', json.dumps(meta))
            for f in sorted(os.listdir(upload_dir)):
                p = os.path.join(upload_dir, f)
                if os.path.isfile(p): z.write(p, 'model/' + f)
        return dest

    def install_files(self, files, name='mod', mod_id=''):
        dest = None
        for rel, fn in files.items(): dest = self.I.install(mod_id or 'mod', rel, open(fn, 'rb').read(), name, character=os.path.splitext(os.path.basename(rel))[0])
        return dest

    def install_recipe(self, zpath, name='mod', mod_id='', log=print):
        from ..modelio import load_model, MODEL_EXT
        tmp = tempfile.mkdtemp(prefix='modswap_recipe_')
        try:
            with zipfile.ZipFile(zpath) as z: meta = json.loads(z.read('recipe.json')); z.extractall(tmp)
            d = os.path.join(tmp, 'model'); order = ('.fbx', '.glb', '.gltf', '.obj', '.dae', '.vrm', '.blend', '.ply', '.stl', '.3mf', '.off')
            files = sorted((f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in MODEL_EXT), key=lambda f: (order.index(os.path.splitext(f)[1].lower()) if os.path.splitext(f)[1].lower() in order else 99, f))
            mdl = load_model(os.path.join(d, files[0]), d); parts = (meta.get('params') or {}).get('parts')
            if parts: mdl = mdl.subset(parts)
            rows = self.scan(); idx = next(i for i, r in enumerate(rows) if r['stem'] == meta['stem']); m = self.model(idx)
            out = os.path.join(tmp, 'out'); os.makedirs(out)
            return self.install_files(self.build(m, mdl, meta.get('params') or {}, out, log=log), name, mod_id=mod_id)
        finally: shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------ what is installed
    def installed(self): return {r['file']: dict(mod=r.get('group', r['id']), name=r['name']) for r in self.I.installed()}
    def active_ids(self): return list(dict.fromkeys(r.get('group', r['id']) for r in self.I.installed()))
    def uninstall_mod(self, mid, log=print): self.I.uninstall(mid); log('removed'); return mid

    def restore(self):
        had = [r['name'] for r in self.I.installed()]; self.I.restore(); return had

    def release(self): self._chars.clear()
