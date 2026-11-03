"""Games installed through other launchers (Epic Games, GOG, Xbox / Game Pass, Ubisoft Connect), found without logging in to anything.
Each finder returns [Found(...)] and never raises: a launcher that is not installed simply finds nothing."""
import os, re, sys, glob, json
from dataclasses import dataclass


@dataclass
class Found:
    source: str        # epic | gog | xbox | ubisoft
    key: str           # stable id inside that launcher
    name: str
    root: str


def _program_data():
    return os.environ.get('ProgramData') or r'C:\ProgramData'


def epic(manifest_dir=None):
    out = []
    d = manifest_dir or os.path.join(_program_data(), 'Epic', 'EpicGamesLauncher', 'Data', 'Manifests')
    for f in sorted(glob.glob(os.path.join(d, '*.item'))):
        try: m = json.load(open(f, encoding='utf-8', errors='replace'))
        except Exception: continue
        root = m.get('InstallLocation') or ''; name = m.get('DisplayName') or ''
        if not name or not os.path.isdir(root): continue
        if m.get('bIsIncompleteInstall') or str(m.get('AppCategories', '')).lower().find('plugins') >= 0: continue
        out.append(Found('epic', m.get('AppName') or re.sub(r'\W+', '-', name).lower(), name, os.path.normpath(root)))
    return out


def _reg_keys(hive, path, view64=True):
    try:
        import winreg
        flag = winreg.KEY_READ | (winreg.KEY_WOW64_64KEY if view64 else winreg.KEY_WOW64_32KEY)
        with winreg.OpenKey(hive, path, 0, flag) as k:
            n = winreg.QueryInfoKey(k)[0]
            for i in range(n):
                sub = winreg.EnumKey(k, i)
                try:
                    with winreg.OpenKey(k, sub) as s:
                        vals = {}; j = 0
                        while True:
                            try: nm, v, _ = winreg.EnumValue(s, j); vals[nm] = v; j += 1
                            except OSError: break
                        yield sub, vals
                except OSError: continue
    except Exception: return


def gog():
    out = []
    if not sys.platform.startswith('win'): return out
    import winreg
    for sub, v in _reg_keys(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\GOG.com\Games', view64=False):
        name, path = v.get('gameName'), v.get('path')
        if name and path and os.path.isdir(path): out.append(Found('gog', str(v.get('gameID') or sub), name, os.path.normpath(path)))
    return out


def ubisoft():
    out = []
    if not sys.platform.startswith('win'): return out
    import winreg
    for sub, v in _reg_keys(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs', view64=False):
        path = v.get('InstallDir')
        if path and os.path.isdir(path): out.append(Found('ubisoft', sub, os.path.basename(os.path.normpath(path)), os.path.normpath(path)))
    return out


def xbox(drives=None):
    """Game Pass / Microsoft Store games installed to <drive>:\\XboxGames\\<Name>\\Content"""
    out = []
    if drives is None:
        drives = ['%s:\\' % c for c in 'CDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.isdir('%s:\\' % c)] if sys.platform.startswith('win') else []
    for dr in drives:
        base = os.path.join(dr, 'XboxGames')
        if not os.path.isdir(base): continue
        for n in sorted(os.listdir(base)):
            c = os.path.join(base, n, 'Content')
            if os.path.isdir(c) and n.lower() != 'gaming services': out.append(Found('xbox', re.sub(r'\W+', '-', n).lower(), n, c))
    return out


def scan_all():
    seen, out = set(), []
    for fn in (epic, gog, ubisoft, xbox):
        try: found = fn()
        except Exception: found = []
        for f in found:
            k = f.root.lower()
            if k not in seen: seen.add(k); out.append(f)
    return sorted(out, key=lambda f: f.name.lower())
