"""Find the Steam install, its library folders and the installed games (no Steam login or network needed)."""
import os, re, sys, glob
from dataclasses import dataclass

SKIP_NAMES = re.compile(r'^(Steamworks Common Redistributables|Steam Linux Runtime.*|Proton.*|Steam Controller Configs|SteamVR|Wallpaper Engine)$', re.I)


# ---------------------------------------------------------------- Valve KeyValues (VDF/ACF) text format
def parse_vdf(text):
    """Parse Valve's KeyValues text format into nested dicts. Handles quotes, escapes, // comments."""
    tokens = re.findall(r'"((?:[^"\\]|\\.)*)"|(\{)|(\})', re.sub(r'//[^\n]*', '', text))
    pos = 0

    def block():
        nonlocal pos
        out = {}
        while pos < len(tokens):
            s, lb, rb = tokens[pos]
            if rb: pos += 1; return out
            if lb: pos += 1; continue
            key = s.replace('\\\\', '\\'); pos += 1
            if pos >= len(tokens): break
            s2, lb2, rb2 = tokens[pos]
            if lb2: pos += 1; out[key] = block()
            elif rb2: break
            else: out[key] = s2.replace('\\\\', '\\'); pos += 1
        return out
    return block()


# ---------------------------------------------------------------- locating Steam
def steam_roots():
    """Candidate Steam install directories that exist on this machine."""
    cands = []
    if sys.platform.startswith('win'):
        try:
            import winreg
            for hive, key, name in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                    (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath'),
                                    (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Valve\Steam', 'InstallPath')):
                try:
                    with winreg.OpenKey(hive, key) as k: cands.append(winreg.QueryValueEx(k, name)[0])
                except OSError: pass
        except ImportError: pass
        for env in ('ProgramFiles(x86)', 'ProgramFiles'):
            if os.environ.get(env): cands.append(os.path.join(os.environ[env], 'Steam'))
    elif sys.platform == 'darwin':
        cands.append(os.path.expanduser('~/Library/Application Support/Steam'))
    else:
        h = os.path.expanduser('~')
        cands += [h + '/.steam/steam', h + '/.local/share/Steam', h + '/.var/app/com.valvesoftware.Steam/.local/share/Steam']
    seen, out = set(), []
    for c in cands:
        c = os.path.normpath(c)
        if c.lower() not in seen and os.path.isdir(os.path.join(c, 'steamapps')): seen.add(c.lower()); out.append(c)
    return out


def library_folders(steam_root):
    """All Steam library directories (each contains a steamapps/ folder), including the main install."""
    libs = [os.path.normpath(steam_root)]
    vdf = os.path.join(steam_root, 'steamapps', 'libraryfolders.vdf')
    if os.path.exists(vdf):
        try:
            data = parse_vdf(open(vdf, encoding='utf-8', errors='replace').read())
            root = data.get('libraryfolders') or data.get('LibraryFolders') or {}
            for k, v in root.items():
                p = v.get('path') if isinstance(v, dict) else (v if k.isdigit() else None)
                if p: libs.append(os.path.normpath(p))
        except Exception: pass
    seen, out = set(), []
    for l in libs:
        if l.lower() not in seen and os.path.isdir(os.path.join(l, 'steamapps')): seen.add(l.lower()); out.append(l)
    return out


@dataclass
class SteamGame:
    appid: str
    name: str
    root: str          # folder with the game's files
    library: str
    size_on_disk: int = 0


def installed_games(library):
    out = []
    for mf in sorted(glob.glob(os.path.join(library, 'steamapps', 'appmanifest_*.acf'))):
        try: st = parse_vdf(open(mf, encoding='utf-8', errors='replace').read()).get('AppState', {})
        except Exception: continue
        name, inst = st.get('name'), st.get('installdir')
        if not name or not inst or SKIP_NAMES.match(name): continue
        root = os.path.join(library, 'steamapps', 'common', inst)
        if not os.path.isdir(root): continue
        try: size = int(st.get('SizeOnDisk', 0))
        except ValueError: size = 0
        out.append(SteamGame(st.get('appid', ''), name, root, library, size))
    return out


def scan_steam(roots=None):
    """Every installed Steam game across every library folder. `roots` overrides auto-detection (for tests / custom installs)."""
    games, seen = [], set()
    for sr in (roots if roots is not None else steam_roots()):
        for lib in library_folders(sr):
            for g in installed_games(lib):
                if g.root.lower() not in seen: seen.add(g.root.lower()); games.append(g)
    return sorted(games, key=lambda g: g.name.lower())
