"""Thin wrapper around the `repak` command line tool (https://github.com/trumank/repak) for listing / unpacking / packing .pak files.

repak is looked up in: $MODSWAP_REPAK, next to this app (tools/), PATH, ~/tools/**.
Swap in a different backend (anything with list/unpack/pack) for tests."""
import os, glob, shutil, subprocess, sys


def find_repak():
    cands = [os.environ.get('MODSWAP_REPAK', '')]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for exe in ('repak.exe', 'repak', 'repak_cli.exe'):
        cands += [os.path.join(here, 'tools', exe), os.path.join(here, exe)]
        w = shutil.which(exe)
        if w: cands.append(w)
    cands += glob.glob(os.path.expanduser('~/tools/**/repak'), recursive=True) + glob.glob(os.path.expanduser('~/tools/**/repak.exe'), recursive=True)
    for c in cands:
        if c and os.path.isfile(c): return c
    return None


REPAK_BASE = 'https://github.com/trumank/repak/releases/latest/download/'


def _asset_name():
    import platform
    if os.name == 'nt': return 'repak_cli-x86_64-pc-windows-msvc.zip'
    if platform.system() == 'Linux': return 'repak_cli-x86_64-unknown-linux-gnu.tar.xz'
    return None


def download_repak(log=print, base=None):
    """Fetch repak (the open-source .pak packer) into <app>/tools, verified against the release's sha256 file."""
    import urllib.request, hashlib, zipfile, tarfile, io, tempfile, stat
    name = _asset_name(); base = base or os.environ.get('MODSWAP_REPAK_BASE') or REPAK_BASE
    if not name: raise RuntimeError('No prebuilt repak for this OS. Get one from https://github.com/trumank/repak/releases and set MODSWAP_REPAK.')
    dest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'); os.makedirs(dest, exist_ok=True)
    log('downloading repak (one-time)...')
    def get(u):
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'ModSwap'}), timeout=90) as r: return r.read()
    data = get(base + name)
    try:
        want = get(base + name + '.sha256').decode().split()[0].lower()
        if hashlib.sha256(data).hexdigest() != want: raise RuntimeError('repak download failed its checksum, not using it.')
    except RuntimeError: raise
    except Exception: log('(no checksum file found, skipping verification)')
    exe = None
    if name.endswith('.zip'):
        z = zipfile.ZipFile(io.BytesIO(data))
        for n in z.namelist():
            if os.path.basename(n).lower() in ('repak.exe', 'repak_cli.exe'):
                exe = os.path.join(dest, 'repak.exe'); open(exe + '.part', 'wb').write(z.read(n)); os.replace(exe + '.part', exe); break
    else:
        t = tarfile.open(fileobj=io.BytesIO(data), mode='r:xz')
        for m in t.getmembers():
            if m.isfile() and os.path.basename(m.name) in ('repak', 'repak_cli'):
                exe = os.path.join(dest, 'repak'); open(exe, 'wb').write(t.extractfile(m).read()); os.chmod(exe, 0o755); break
    if not exe: raise RuntimeError('repak archive did not contain the expected program.')
    log('repak ready'); return exe


import threading
_DL_LOCK = threading.Lock()


class Repak:
    def __init__(self, exe=None, log=print, aes=None):
        self.aes = aes
        self.exe = exe or find_repak()
        if not self.exe:
            with _DL_LOCK:                                   # two requests at once must not both download (one got "Permission denied")
                self.exe = find_repak()
                if not self.exe:
                    try: self.exe = download_repak(log)
                    except Exception as e: self._fail(e)

    def _fail(self, e):
        raise FileNotFoundError('repak not found and the automatic download failed (%s). Download repak from https://github.com/trumank/repak/releases, put repak.exe in the tools/ folder, or set MODSWAP_REPAK.' % e)

    def _run(self, args, timeout=3600):
        # repak takes -a/--aes-key as a *global* option (before the subcommand: `repak -a KEY list x.pak`); args[0] is the subcommand
        full = [self.exe] + self._k() + args
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0: raise RuntimeError('repak %s failed: %s' % (args[0], (r.stderr or r.stdout).strip()[-400:]))
        return r.stdout

    def _k(self): return ['--aes-key', self.aes] if self.aes else []

    def info(self, pak): return self._run(['info', pak])

    def list(self, pak):
        return [l.strip().replace('\\', '/') for l in self._run(['list', pak]).splitlines() if l.strip()]

    def unpack(self, pak, out_dir, includes=None, chunk=60):
        os.makedirs(out_dir, exist_ok=True)
        if not includes: self._run(['unpack', pak, '-o', out_dir, '-f', '-q']); return
        for i in range(0, len(includes), chunk):                    # keep the command line short (Windows limit)
            args = ['unpack', pak, '-o', out_dir, '-f', '-q']
            for p in includes[i:i + chunk]: args += ['-i', p]
            self._run(args)

    def pack(self, in_dir, out_pak, version='V11', seed=0, mount='../../../'):
        args = ['pack', '--version', version, '--mount-point', mount, '--path-hash-seed', str(int(seed)), in_dir, out_pak]
        if version in ('V8A', 'V8B', 'V9', 'V7', 'V6', 'V5', 'V4', 'V3'): args = ['pack', '--version', version, '--mount-point', mount, in_dir, out_pak]
        self._run(args)
