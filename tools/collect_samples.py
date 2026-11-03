"""Collect a SMALL sample of a game's files into one zip, so the file formats can be studied without sending the whole game.

    runtime\\python.exe tools\\collect_samples.py "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Sonic Frontiers" samples\\sonic_frontiers.zip [--budget 60]

What goes in the zip (nothing is changed or uploaded; it only READS the game folder):
  tree.txt           every file: relative path, size
  extensions.txt     how many files / how many MB per file type
  manifest.txt       the Steam appmanifest of the game (version / build id), if found
  heads/...          the first 256 KB and the last 64 KB of every big file (archive headers and file tables live there)
  index/...          index files such as Spider-Man's 'toc', whole (up to 40 MB)
  small/...          whole copies of small files (up to 3 MB each), a few of every file type
The zip stays under --budget MB (default 60), so it can be pushed to GitHub.
"""
import os, sys, re, zipfile, hashlib, argparse, collections

HEAD = 256 * 1024; TAIL = 64 * 1024; SMALL = 3 * 1024 * 1024; PER_EXT = 25


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(d, f)
            try: yield p, os.path.getsize(p)
            except OSError: continue


def find_manifest(root):
    """steamapps/appmanifest_<id>.acf whose "installdir" is this folder"""
    steamapps = os.path.dirname(os.path.dirname(os.path.abspath(root))); name = os.path.basename(os.path.abspath(root)).lower()
    try: names = [n for n in os.listdir(steamapps) if n.startswith('appmanifest_') and n.endswith('.acf')]
    except OSError: return None
    for n in names:
        try: txt = open(os.path.join(steamapps, n), encoding='utf-8', errors='replace').read()
        except OSError: continue
        m = re.search(r'"installdir"\s+"([^"]+)"', txt)
        if m and m.group(1).lower() == name: return txt
    return None


class Budgeted:
    def __init__(self, z, budget): self.z = z; self.left = budget; self.skipped = 0
    def add(self, arcname, data):
        if len(data) > self.left: self.skipped += 1; return False
        self.z.writestr(arcname, data); self.left -= len(data); return True


def arc(prefix, rel, suffix=''):
    h = hashlib.md5(rel.encode('utf-8', 'replace')).hexdigest()[:6]
    return '%s/%s__%s%s' % (prefix, re.sub(r'[^A-Za-z0-9._-]+', '_', rel)[-110:], h, suffix)


def collect(root, out_zip, budget_mb=60, log=print):
    root = os.path.abspath(root)
    if not os.path.isdir(root): raise SystemExit('not a folder: ' + root)
    files = list(walk(root))
    log('%d files, %.1f GB in %s' % (len(files), sum(s for _, s in files) / 1e9, root))
    os.makedirs(os.path.dirname(os.path.abspath(out_zip)), exist_ok=True)
    byext = collections.defaultdict(list)
    for p, s in files: byext[os.path.splitext(p)[1].lower()].append((p, s))
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        B = Budgeted(z, int(budget_mb * 1024 * 1024))
        rel = lambda p: os.path.relpath(p, root).replace(os.sep, '/')
        B.add('tree.txt', '\n'.join('%12d  %s' % (s, rel(p)) for p, s in files).encode('utf-8', 'replace'))
        B.add('extensions.txt', '\n'.join('%-14s %8d files %10.1f MB' % (e or '(none)', len(v), sum(s for _, s in v) / 1e6) for e, v in sorted(byext.items(), key=lambda kv: -sum(s for _, s in kv[1]))).encode())
        mf = find_manifest(root)
        if mf: B.add('manifest.txt', mf.encode('utf-8', 'replace'))
        # index files that say where every asset lives (Spider-Man's 'toc'): taken WHOLE, up to 40 MB, before anything else uses the budget
        for p, sz in files:
            if os.path.basename(p).lower() in ('toc', 'toc.bak') or p.lower().endswith('.toc'):
                if sz <= 40 * 1024 * 1024:
                    try: B.add(arc('index', rel(p)), open(p, 'rb').read())
                    except OSError: pass
        # archive headers: the start and end of every big file (bounded: biggest-count extensions get a cap so the budget is shared fairly)
        big = [(p, s) for p, s in files if s > SMALL]
        per = collections.Counter(); n_heads = 0
        for p, s in sorted(big, key=lambda x: x[1]):
            e = os.path.splitext(p)[1].lower()
            if per[e] >= 400: continue
            try:
                with open(p, 'rb') as f:
                    head = f.read(HEAD); f.seek(max(HEAD, s - TAIL)); tail = f.read(TAIL) if s > HEAD + TAIL else b''
            except OSError: continue
            if B.add(arc('heads', rel(p), '.head'), head):
                n_heads += 1; per[e] += 1
                if tail: B.add(arc('heads', rel(p), '.tail'), tail)
        # whole small files: a few of every type, spread across the folder tree
        n_small = 0
        for e, items in sorted(byext.items(), key=lambda kv: len(kv[1])):
            cand = [(p, s) for p, s in items if 0 < s <= SMALL]
            cand.sort(key=lambda x: x[0]); step = max(1, len(cand) // PER_EXT)
            for p, s in cand[::step][:PER_EXT]:
                try: data = open(p, 'rb').read()
                except OSError: continue
                if B.add(arc('small', rel(p)), data): n_small += 1
        log('zip written: %s  (%d big-file heads, %d small files, %.1f MB, %d items did not fit the budget)' % (out_zip, n_heads, n_small, os.path.getsize(out_zip) / 1e6, B.skipped))
    return out_zip


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_folder'); ap.add_argument('out_zip'); ap.add_argument('--budget', type=float, default=60, help='max size of the collected data in MB (default 60)')
    a = ap.parse_args(); collect(a.game_folder, a.out_zip, a.budget)
