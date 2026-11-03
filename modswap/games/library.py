"""The user's game list: Steam games found by scanning plus games added by hand (via their .exe). Persisted as JSON."""
import os, re, json, sys
from dataclasses import dataclass, asdict, field
from . import steam, detect


def config_dir():
    if sys.platform.startswith('win'): base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin': base = os.path.expanduser('~/Library/Application Support')
    else: base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    d = os.path.join(base, 'ModSwap'); os.makedirs(d, exist_ok=True); return d


@dataclass
class Game:
    id: str
    name: str
    root: str
    source: str                  # steam | manual
    engine: str = 'unknown'
    engine_version: str = ''
    engine_detail: str = ''
    supported: bool = False
    appid: str = ''
    exe: str = ''
    paks: list = field(default_factory=list)


def _slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-') or 'game'


def from_steam(g):
    e = detect.detect_engine(g.root)
    return Game(id='steam-' + (g.appid or _slug(g.name)), name=g.name, root=g.root, source='steam', engine=e.engine,
                engine_version=e.version, engine_detail=e.detail, supported=e.supported, appid=g.appid, paks=e.paks)


def from_exe(exe_path, name=None):
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path): raise FileNotFoundError(exe_path)
    root = detect.find_game_root(exe_path); e = detect.detect_engine(root)
    nm = name or re.sub(r'(-Win64-Shipping|-WinGDK-Shipping|-Shipping)$', '', re.sub(r'\.exe$', '', os.path.basename(exe_path), flags=re.I), flags=re.I)
    return Game(id='manual-' + _slug(nm), name=nm, root=root, source='manual', engine=e.engine, engine_version=e.version,
                engine_detail=e.detail, supported=e.supported, exe=exe_path, paks=e.paks)


class Library:
    def __init__(self, path=None):
        self.path = path or os.path.join(config_dir(), 'games.json')
        self.games = {}
        if os.path.exists(self.path):
            try:
                for d in json.load(open(self.path)).get('games', []):
                    g = Game(**d)
                    if g.engine == 'unknown' and os.path.isfile(os.path.join(g.root, 'asset_archive', 'toc')): g.engine, g.engine_detail = 'insomniac', 'asset_archive\\toc'      # saved before ModSwap knew this engine
                    if g.engine == 'unknown' and os.path.isdir(os.path.join(g.root, 'image', 'x64', 'raw', 'character')): g.engine, g.engine_detail = 'hedgehog2', 'image\\x64\\raw\\character\\*.pac'
                    g.supported = g.engine in detect.SUPPORTED          # decided by the engine NOW, not by a flag an older ModSwap saved
                    self.games[d['id']] = g
            except Exception: pass

    def save(self):
        json.dump({'games': [asdict(g) for g in self.games.values()]}, open(self.path, 'w'), indent=1)

    def scan_others(self, found=None):
        """games from Epic / GOG / Xbox / Ubisoft launchers; returns how many are new"""
        from . import launchers
        found = launchers.scan_all() if found is None else found; new = 0
        for f in found:
            e = detect.detect_engine(f.root)
            g = Game(id='%s-%s' % (f.source, _slug(f.key)), name=f.name, root=f.root, source=f.source, engine=e.engine, engine_version=e.version,
                     engine_detail=e.detail, supported=e.supported, paks=e.paks)
            if g.id not in self.games: new += 1
            self.games[g.id] = g
        for gid in [k for k, g in self.games.items() if g.source in ('epic', 'gog', 'xbox', 'ubisoft') and not os.path.isdir(g.root)]: del self.games[gid]
        self.save(); return new

    def scan_steam(self, roots=None, progress=None):
        found = steam.scan_steam(roots); new = 0
        for i, sg in enumerate(found):
            if progress: progress(i, len(found), sg.name)
            g = from_steam(sg)
            if g.id not in self.games: new += 1
            old = self.games.get(g.id)
            self.games[g.id] = g
        for gid in [k for k, g in self.games.items() if g.source == 'steam' and not os.path.isdir(g.root)]: del self.games[gid]
        self.save(); return new

    def add_exe(self, exe, name=None):
        g = from_exe(exe, name); self.games[g.id] = g; self.save(); return g

    def remove(self, gid):
        self.games.pop(gid, None); self.save()

    def list(self, only_supported=False):
        gs = sorted(self.games.values(), key=lambda g: g.name.lower())
        return [g for g in gs if g.supported] if only_supported else gs
