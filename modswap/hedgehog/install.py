"""Install / remove Sonic Frontiers character mods. A mod is a rewritten character .pac that REPLACES the original file, so:
  - the original is copied once to <game>/modswap_backup/ (with its SHA-256) before the first change, and every later build starts from that backup, never from a modified file;
  - uninstall / restore copy the backup back (byte for byte) and delete it;
  - state lives in <game>/modswap_backup/state.json, so the command line and the app see the same mods.
"""
import os, json, shutil, hashlib

CHAR_DIR = os.path.join('image', 'x64', 'raw', 'character')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


class Installer:
    def __init__(self, game_dir):
        self.root = game_dir; self.char_dir = os.path.join(game_dir, CHAR_DIR)
        if not os.path.isdir(self.char_dir): raise ValueError('no %s folder in %s: is this the Sonic Frontiers folder?' % (CHAR_DIR, game_dir))
        self.bdir = os.path.join(game_dir, 'modswap_backup'); self.state_path = os.path.join(self.bdir, 'state.json')

    def installed(self):
        try: return json.load(open(self.state_path))['mods']
        except Exception: return []

    def _save(self, mods):
        os.makedirs(self.bdir, exist_ok=True); tmp = self.state_path + '.tmp'; json.dump(dict(mods=mods), open(tmp, 'w'), indent=1); os.replace(tmp, self.state_path)

    def path(self, rel): return os.path.join(self.root, rel)
    def backup_path(self, rel): return os.path.join(self.bdir, rel.replace('\\', '/').replace('/', '__') + '.orig')

    def original_path(self, rel):
        """the ORIGINAL file for `rel` (the backup when a mod is installed over it)"""
        b = self.backup_path(rel); return b if os.path.isfile(b) else self.path(rel)

    def read_original(self, rel):
        p = self.original_path(rel)
        if not os.path.isfile(p): raise FileNotFoundError('this game has no %s' % rel)
        return open(p, 'rb').read()

    def install(self, mod_id, rel, data, name='', character=''):
        """replace the game's file `rel` by `data`. A new mod for a file that already carries a ModSwap mod replaces that mod."""
        cur = self.path(rel); b = self.backup_path(rel); mods = [m for m in self.installed() if m['file'] != rel and m['id'] != mod_id]
        os.makedirs(self.bdir, exist_ok=True)
        if not os.path.isfile(b):
            if not os.path.isfile(cur): raise FileNotFoundError('this game has no %s' % rel)
            shutil.copy2(cur, b)
        self._write(cur, data)
        mods.append(dict(id=mod_id, name=name or mod_id, file=rel, character=character, orig_sha=sha256(b), new_sha=hashlib.sha256(data).hexdigest(), size=len(data)))
        self._save(mods); return cur

    def _write(self, dst, data):
        tmp = dst + '.modswap_tmp'
        with open(tmp, 'wb') as f: f.write(data)
        try: os.replace(tmp, dst)
        except PermissionError:
            os.remove(tmp); raise PermissionError('Windows would not let ModSwap change %s: close the game and try again' % os.path.basename(dst))

    def _put_back(self, rel):
        b = self.backup_path(rel)
        if os.path.isfile(b):
            tmp = self.path(rel) + '.modswap_tmp'; shutil.copy2(b, tmp)
            try: os.replace(tmp, self.path(rel))
            except PermissionError: os.remove(tmp); raise PermissionError('Windows would not let ModSwap change %s: close the game and try again' % os.path.basename(rel))
            os.remove(b)

    def uninstall(self, mod_id):
        mods = self.installed(); gone = [m for m in mods if m['id'] == mod_id or m.get('group') == mod_id]
        for m in gone: self._put_back(m['file'])
        self._save([m for m in mods if m not in gone])

    def restore(self):
        """every file ModSwap changed, back to the original"""
        for m in self.installed(): self._put_back(m['file'])
        self._save([])
        if os.path.isdir(self.bdir) and not any(f != 'state.json' for f in os.listdir(self.bdir)):
            try: os.remove(self.state_path); os.rmdir(self.bdir)
            except OSError: pass
