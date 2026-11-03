"""Install / remove Spider-Man Remastered mods. The game reads every asset through asset_archive/toc, so a mod is:
    - a plain archive file asset_archive/mods/<id> holding the new asset bytes, and
    - a toc whose entry for the replaced asset points at that file (the file is appended to the toc's archive list).
The ORIGINAL toc is kept as asset_archive/toc.BAK and the toc is always rebuilt from it plus the mods that are installed, so removing a mod, or all of them, puts the
game back exactly (the .BAK is not touched again). A small state file asset_archive/modswap_mods.json lists what ModSwap installed.
"""
import os, json, shutil
from .toc import Toc, patched_raw, to_file_bytes, path_id

from .names import SUITS as SUIT_WORDS, NPCS as NPC_WORDS


def suit_model_path(suit):
    """suits: characters/hero/hero_spiderman_<id>/...; everyone else (ids that start with npc_): characters/npc/npc_<x>/..."""
    if suit.startswith('npc_'): return 'characters/npc/%s/%s.model' % (suit, suit)
    return 'characters/hero/hero_spiderman_%s/hero_spiderman_%s.model' % (suit, suit)


def find_suits(toc, extra=(), npcs=True):
    """character ids whose model exists in this toc (ids are hashes of paths, so a list of likely names is tried; only real hits are returned): the suits first, then the other characters"""
    out = [w for w in dict.fromkeys(list(SUIT_WORDS) + list(extra)) if toc.find(suit_model_path(w)) is not None]
    if npcs: out += sorted(w for w in dict.fromkeys('npc_' + n for n in NPC_WORDS) if toc.find(suit_model_path(w)) is not None)
    return out


class Installer:
    def __init__(self, game_dir):
        self.ad = os.path.join(game_dir, 'asset_archive')
        if not os.path.isfile(os.path.join(self.ad, 'toc')): raise ValueError('no asset_archive\\toc in %s: is this the Marvel\'s Spider-Man Remastered folder?' % game_dir)
        self.toc_path = os.path.join(self.ad, 'toc'); self.bak = os.path.join(self.ad, 'toc.BAK')
        self.mods_dir = os.path.join(self.ad, 'mods'); self.state_path = os.path.join(self.ad, 'modswap_mods.json')

    # ---- state
    def installed(self):
        try: return json.load(open(self.state_path))['mods']
        except Exception: return []

    def _save(self, mods): json.dump(dict(mods=mods), open(self.state_path, 'w'), indent=1)

    def original_toc(self):
        """the original toc (toc.BAK), made from the current toc the first time"""
        if not os.path.isfile(self.bak):
            if self.installed(): raise ValueError('mods are recorded as installed but toc.BAK is missing: verify the game files in Steam before installing')
            shutil.copy2(self.toc_path, self.bak)
        return Toc(open(self.bak, 'rb').read())

    def toc_for_reading(self):
        """the original toc for READING (toc.BAK when it exists, else the current toc). Unlike original_toc() this never makes a backup."""
        return Toc(open(self.bak if os.path.isfile(self.bak) else self.toc_path, 'rb').read())

    # ---- actions
    def read_original(self, path, toc=None):
        """the ORIGINAL bytes of the asset at `path` (from the .BAK toc, whatever mods are installed)"""
        toc = toc or self.original_toc(); i = toc.find(path)
        if i is None: raise KeyError('this game has no asset %s' % path)
        try: return toc.read(i, self.ad)
        finally: toc.close()

    def install(self, mod_id, target_path, data, name=''):
        """put `data` (a new asset) in place of the asset at `target_path`. Installing for a target that already has a ModSwap mod replaces that mod."""
        toc = self.original_toc(); i = toc.find(target_path)
        if i is None: raise KeyError('this game has no asset %s' % target_path)
        os.makedirs(self.mods_dir, exist_ok=True)
        mods = [m for m in self.installed() if m['target'] != target_path and m['id'] != mod_id]
        fn = 'modswap_%s' % mod_id
        with open(os.path.join(self.mods_dir, fn), 'wb') as f: f.write(data)
        mods.append(dict(id=mod_id, name=name or mod_id, target=target_path, file=fn, size=len(data)))
        self._write_toc(toc, mods); self._save(mods); self._clean_unused(mods)
        return os.path.join(self.mods_dir, fn)

    def install_group(self, group_id, items, name=''):
        """one mod made of several assets: items = [(target path, new bytes)]. Each asset gets its own archive file; uninstalling the group id removes all of them.
        An asset that already has a ModSwap mod is replaced."""
        toc = self.original_toc()
        for path, _ in items:
            if toc.find(path) is None: raise KeyError('this game has no asset %s' % path)
        os.makedirs(self.mods_dir, exist_ok=True); targets = {p for p, _ in items}
        mods = [m for m in self.installed() if m['target'] not in targets and m['id'] != group_id and m.get('group') != group_id]
        for k, (path, data) in enumerate(items):
            fn = 'modswap_%s_%d' % (group_id, k)
            with open(os.path.join(self.mods_dir, fn), 'wb') as f: f.write(data)
            mods.append(dict(id='%s.%d' % (group_id, k), group=group_id, name=name or group_id, target=path, file=fn, size=len(data)))
        self._write_toc(toc, mods); self._save(mods); self._clean_unused(mods)

    def uninstall(self, mod_id):
        toc = self.original_toc(); mods = [m for m in self.installed() if m['id'] != mod_id and m.get('group') != mod_id]
        self._write_toc(toc, mods); self._save(mods); self._clean_unused(mods)

    def restore(self):
        """the game exactly as it was: original toc back, every ModSwap mod file removed"""
        if os.path.isfile(self.bak):
            tmp = self.toc_path + '.tmp'; shutil.copy2(self.bak, tmp); os.replace(tmp, self.toc_path)
        self._save([]); self._clean_unused([])

    # ---- internals
    def _write_toc(self, toc, mods):
        redirects = {}; names = []
        for k, m in enumerate(mods):
            names.append('mods\\' + m['file']); redirects[toc.find(m['target'])] = (len(toc.archives) + k, 0, m['size'])
        raw = patched_raw(toc, redirects, names); tmp = self.toc_path + '.tmp'
        with open(tmp, 'wb') as f: f.write(to_file_bytes(raw))
        try: os.replace(tmp, self.toc_path)
        except PermissionError: os.remove(tmp); raise PermissionError('Windows would not let ModSwap change asset_archive\\toc: close the game and try again')

    def _clean_unused(self, mods):
        keep = {m['file'] for m in mods}
        if not os.path.isdir(self.mods_dir): return
        for f in os.listdir(self.mods_dir):
            if f.startswith('modswap_') and f not in keep:
                try: os.remove(os.path.join(self.mods_dir, f))
                except OSError: pass
