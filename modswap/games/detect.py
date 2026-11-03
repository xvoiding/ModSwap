"""Guess a game's engine from the files in its folder, and find a game root from an .exe."""
import os, re, glob, mmap, struct
from dataclasses import dataclass, field

# engines the swap pipeline can write today
SUPPORTED = {'unreal', 'unity', 'insomniac'}


@dataclass
class EngineInfo:
    engine: str                 # unreal | unity | godot | source | source2 | gamemaker | unknown
    version: str = ''
    detail: str = ''
    paks: list = field(default_factory=list)
    blocked: str = ''

    @property
    def supported(self): return self.engine in SUPPORTED and not self.blocked

    @property
    def label(self):
        names = {'unreal': 'Unreal Engine', 'unity': 'Unity', 'godot': 'Godot', 'source': 'Source', 'source2': 'Source 2', 'gamemaker': 'GameMaker',
                 'rpgmaker': 'RPG Maker', 'cryengine': 'CryEngine', 'insomniac': 'Insomniac Engine', 'unknown': 'Unknown engine'}
        return (names.get(self.engine, self.engine) + (' ' + self.version if self.version else '')).strip()


def _walk(root, depth):
    root = os.path.normpath(root); base = root.count(os.sep)
    for d, dirs, files in os.walk(root):
        if d.count(os.sep) - base >= depth: dirs[:] = []
        yield d, dirs, files


def find_paks(root, depth=6):
    """Unreal pak files, ordered so that later entries override earlier ones (patch paks last)."""
    paks = []
    for d, dirs, files in _walk(root, depth):
        if os.path.basename(d).lower() == 'paks' or os.path.basename(os.path.dirname(d)).lower() == 'paks':
            for f in files:
                if f.lower().endswith('.pak') and not f.lower().startswith('zz_modswap_'): paks.append(os.path.join(d, f))     # not our own installed mods
    key = lambda p: (os.path.basename(p).lower().endswith('_p.pak'), len(re.findall(r'_\d+_p', p.lower())) and int(re.findall(r'_(\d+)_p', p.lower())[-1]), p.lower())
    return sorted(set(paks), key=key)


def pak_version(path):
    """Read the version number from a pak footer (UE pak v1..v11). Returns int or None."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2); size = f.tell()
            for off in (44, 61, 221, 189, 205, 157, 173):      # footer sizes across versions
                if size < off: continue
                f.seek(size - off); b = f.read(off)
                i = b.find(b'\xe1\x12\x6f\x5a')
                if i >= 0: return int.from_bytes(b[i + 4:i + 8], 'little')
    except OSError: pass
    return None



def _find_in_file(path, needles, limit=400 * 1024 * 1024):
    """first needle found in the file (memory-mapped, so big executables are fine) -> (needle, offset, mmap bytes after it) or None"""
    try:
        with open(path, 'rb') as f:
            if os.path.getsize(path) == 0: return None
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                for nd in needles:
                    i = mm.find(nd, 0, min(len(mm), limit))
                    if i >= 0: return nd, mm[i:i + 64]
            finally: mm.close()
    except (OSError, ValueError): pass
    return None


def unreal_version(root, exes):
    """exact UE version from the shipping executable's build string ('++UE4+Release-4.27' / '++UE5+Release-5.3')"""
    cands = [e for e in exes if e.lower().endswith('-shipping.exe')] or exes
    for e in cands[:3]:
        for nd in (b'++UE4+Release-', b'++UE5+Release-', '++UE4+Release-'.encode('utf-16-le'), '++UE5+Release-'.encode('utf-16-le')):
            hit = _find_in_file(e, [nd])
            if hit:
                raw = hit[1].decode('utf-16-le', 'ignore') if len(nd) > 14 + 2 and nd[1:2] == b'\x00' else hit[1].decode('latin1', 'ignore')
                m = re.search(r'Release-(\d+\.\d+)', raw)
                if m: return m.group(1)
    return ''


def unity_version(root):
    """Unity editor version from globalgamemanagers / data.unity3d / the player's resource files"""
    cands = []
    for d, dirs, files in _walk(root, 3):
        for f in files:
            if f.lower() in ('globalgamemanagers', 'data.unity3d', 'unity default resources', 'mainData'.lower()): cands.append(os.path.join(d, f))
    for c in cands[:4]:
        try:
            b = open(c, 'rb').read(4096)
            m = re.search(rb'(\d{4}\.\d+\.\d+[fpab]\d+|\d\.\d+\.\d+[fpab]\d+)', b)
            if m: return m.group(1).decode()
        except OSError: pass
    return ''


def godot_version(root):
    """Godot version from a .pck header (GDPC, pack format, major, minor, patch)"""
    for d, dirs, files in _walk(root, 3):
        for f in files:
            if f.lower().endswith('.pck'):
                try:
                    b = open(os.path.join(d, f), 'rb').read(24)
                    if b[:4] == b'GDPC': pv, ma, mi, pa = struct.unpack_from('<4I', b, 4); return '%d.%d.%d' % (ma, mi, pa)
                except OSError: pass
    return ''


def detect_engine(root):
    root = os.path.normpath(root)
    names = set(); exes = []; dirs_seen = set()
    for d, dirs, files in _walk(root, 4):
        for x in dirs: dirs_seen.add(x.lower())
        for f in files:
            names.add(f.lower())
            if f.lower().endswith('.exe'): exes.append(f)
    # ---- Insomniac (Marvel's Spider-Man): everything is read through asset_archive\toc
    if os.path.isfile(os.path.join(root, 'asset_archive', 'toc')) or os.path.isfile(os.path.join(root, 'asset_archive', 'toc.BAK')):
        return EngineInfo('insomniac', '', 'asset_archive\\toc')
    # ---- Unreal
    paks = find_paks(root)
    if paks or any(e.lower().endswith('-shipping.exe') for e in exes) or ('engine' in dirs_seen and 'binaries' in dirs_seen):
        v = pak_version(paks[0]) if paks else None
        guess = {11: '4.27+ / 5.x', 10: '4.26 / 4.27', 9: '4.25-4.26', 8: '4.22-4.24', 7: '4.21', 3: '4.0-4.19'}.get(v, '')
        exact = unreal_version(root, [os.path.join(d, e) for d, _, fs in _walk(root, 4) for e in fs if e.lower().endswith('.exe') and os.path.getsize(os.path.join(d, e)) > 20e6])
        ver = exact or guess
        io = any(n.endswith('.utoc') for n in names)
        detail = ('pak v%s' % v) if v else ('%d pak file(s), version unreadable' % len(paks) if paks else 'no pak found (loose or IoStore cook?)')
        if io: detail += ', IoStore (.utoc/.ucas)'
        try:
            from ..ue4 import aes as _aes
            if any((_aes.footer(p) or {}).get('encrypted') for p in paks[:40]): detail += ', encrypted file lists'
        except Exception: pass
        return EngineInfo('unreal', ver, detail, paks)
    # ---- Unity
    if 'unityplayer.dll' in names or any(x.endswith('_data') for x in dirs_seen) and ('globalgamemanagers' in names or 'data.unity3d' in names):
        il2cpp = 'gameassembly.dll' in names
        from ..unity import scan as _us
        dd = _us.data_dir(root); blocked = ''
        return EngineInfo('unity', unity_version(root), ('IL2CPP' if il2cpp else 'Mono') + (', assets in bundles (not supported yet)' if blocked else ''), blocked=blocked)
    # ---- Godot
    if any(n.endswith('.pck') for n in names) or '.godot' in dirs_seen or 'project.godot' in names: return EngineInfo('godot', godot_version(root), 'pck')
    # ---- Source / Source 2
    if 'gameinfo.txt' in names or any(n.endswith('.vpk') for n in names):
        return EngineInfo('source2' if ('engine2.dll' in names) else 'source', '', 'vpk')
    # ---- others
    if 'data.win' in names or 'game.droid' in names: return EngineInfo('gamemaker')
    if 'package.nw' in names or 'rpg_core.js' in names: return EngineInfo('rpgmaker')
    if 'crysystem.dll' in names: return EngineInfo('cryengine')
    return EngineInfo('unknown')


def find_game_root(exe_path):
    """Given any game .exe, walk upward to the folder that holds the game's content (e.g. the UE project folder)."""
    exe_dir = os.path.dirname(os.path.abspath(exe_path)); cur = exe_dir
    for _ in range(5):
        if find_paks(cur, 2) or os.path.isdir(os.path.join(cur, 'Content', 'Paks')): return cur
        parent = os.path.dirname(cur)
        if parent == cur: break
        # stop at Steam's "common" folder: the game's own folder is one level below it
        if os.path.basename(parent).lower() == 'common': return cur
        cur = parent
    # fall back: for ".../Binaries/Win64/Game-Win64-Shipping.exe" the root is 3 levels up
    parts = exe_dir.replace('\\', '/').split('/')
    if 'Binaries' in parts: return os.sep.join(parts[:parts.index('Binaries')]) or exe_dir
    return exe_dir
