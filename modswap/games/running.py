"""Is the game open right now? Windows will not let ModSwap change files a running game has open, and a half-changed install is worse than none."""
import os, sys, subprocess, time

_CACHE = {}


def _exes(root):
    hit = _CACHE.get(root)
    if hit and time.time() - hit[0] < 300: return hit[1]
    names = set(); base = os.path.normpath(root).count(os.sep)
    for d, dirs, files in os.walk(root):
        if d.count(os.sep) - base >= 5: dirs[:] = []
        for f in files:
            if f.lower().endswith('.exe'):
                try:
                    if os.path.getsize(os.path.join(d, f)) > 5 * 1024 * 1024: names.add(f.lower())
                except OSError: pass
    _CACHE[root] = (time.time(), names); return names


def _tasks():
    if not sys.platform.startswith('win'): return set()
    try:
        r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=20, creationflags=0x08000000)
        return {l.split('","')[0].strip('"').lower() for l in r.stdout.splitlines() if l.strip()}
    except Exception: return set()


def running_exe(game):
    """name of a running program that belongs to this game, or ''"""
    try:
        mine = _exes(game.root)
        if getattr(game, 'exe', ''): mine = mine | {os.path.basename(game.exe).lower()}
        live = _tasks() & mine
        return sorted(live)[0] if live else ''
    except Exception: return ''


def ensure_closed(game):
    n = running_exe(game)
    if n: raise RuntimeError('Close %s first (%s is open). Windows will not let ModSwap change a game while it is running.' % (game.name, n))
