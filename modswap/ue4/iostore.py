"""Unreal 5 games keep their assets in IoStore containers (.utoc/.ucas) instead of plain .pak files.

ModSwap reads and writes them with retoc (https://github.com/trumank/retoc, MIT, same author as repak):
  retoc list     - the file names inside a container
  retoc to-legacy - turns Zen packages back into .uasset/.uexp files ModSwap can edit (needs the game's AES key when the containers are encrypted)
  retoc to-zen    - turns edited .uasset/.uexp files into a mod container: <name>.utoc + <name>.ucas + <name>.pak (a tiny stub)
The version is pinned (v0.1.5) because the command line below was checked against exactly that release."""
import os, re, glob, shutil, subprocess, threading

RETOC_VERSION = 'v0.1.5'
RETOC_BASE = 'https://github.com/trumank/retoc/releases/download/%s/' % RETOC_VERSION
_DL_LOCK = threading.Lock()


def _tools_dir(): return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools')


def find_retoc():
    cands = [os.environ.get('MODSWAP_RETOC', '')]
    for exe in ('retoc.exe', 'retoc'):
        cands += [os.path.join(_tools_dir(), exe)]
        w = shutil.which(exe)
        if w: cands.append(w)
    cands += glob.glob(os.path.expanduser('~/tools/**/retoc'), recursive=True) + glob.glob(os.path.expanduser('~/tools/**/retoc.exe'), recursive=True)
    for c in cands:
        if c and os.path.isfile(c): return c
    return None


def _asset_name():
    import platform
    if os.name == 'nt': return 'retoc_cli-x86_64-pc-windows-msvc.zip'
    if platform.system() == 'Linux': return 'retoc_cli-x86_64-unknown-linux-gnu.tar.xz'
    return None


def download_retoc(log=print, base=None):
    """Fetch retoc into <app>/tools and check it against the sha256 file that is published next to it."""
    import urllib.request, hashlib, zipfile, tarfile, io
    name = _asset_name(); base = base or os.environ.get('MODSWAP_RETOC_BASE') or RETOC_BASE
    if not name: raise RuntimeError('No prebuilt retoc for this OS. Get one from https://github.com/trumank/retoc/releases and set MODSWAP_RETOC.')
    dest = _tools_dir(); os.makedirs(dest, exist_ok=True)
    log('downloading retoc %s (one-time, from github.com/trumank/retoc)...' % RETOC_VERSION)
    def get(u):
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'ModSwap'}), timeout=120) as r: return r.read()
    data = get(base + name)
    try: want = get(base + name + '.sha256').decode().split()[0].lower()
    except Exception: want = ''
    if not want: raise RuntimeError('retoc was downloaded but its checksum file could not be fetched, so it was not used.')
    if hashlib.sha256(data).hexdigest() != want: raise RuntimeError('retoc download failed its checksum, not using it.')
    exe = None
    if name.endswith('.zip'):
        z = zipfile.ZipFile(io.BytesIO(data))
        for n in z.namelist():
            if os.path.basename(n).lower() == 'retoc.exe':
                exe = os.path.join(dest, 'retoc.exe'); open(exe + '.part', 'wb').write(z.read(n)); os.replace(exe + '.part', exe); break
    else:
        t = tarfile.open(fileobj=io.BytesIO(data), mode='r:xz')
        for m in t.getmembers():
            if m.isfile() and os.path.basename(m.name) == 'retoc':
                exe = os.path.join(dest, 'retoc'); open(exe, 'wb').write(t.extractfile(m).read()); os.chmod(exe, 0o755); break
    if not exe: raise RuntimeError('the retoc archive did not contain the expected program.')
    log('retoc ready'); return exe


LINE = re.compile(r'^(\S+)\s+([0-9a-fA-F]+)\s+(\w+)\s+(?:\d+\s+)?(\S.*)$')
UE_VERSIONS = {'4.25': 'UE4_25', '4.26': 'UE4_26', '4.27': 'UE4_27', '5.0': 'UE5_0', '5.1': 'UE5_1', '5.2': 'UE5_2', '5.3': 'UE5_3', '5.4': 'UE5_4',
               '5.5': 'UE5_5', '5.6': 'UE5_6', '5.7': 'UE5_7'}


def ue_version_flag(v):
    """'5.1' -> 'UE5_1' (retoc's own spelling); '' / unknown -> None, which makes retoc work it out itself"""
    m = re.match(r'(\d+)\.(\d+)', v or '')
    return UE_VERSIONS.get('%s.%s' % m.groups()) if m else None


def containers(paks_dir):
    """the game's own .utoc files (never ModSwap's or other mods' containers in ~mods)"""
    out = []
    for p in sorted(glob.glob(os.path.join(paks_dir, '*.utoc'))):
        if os.path.basename(p).lower().startswith(('zz_modswap_', 'modswap_')): continue
        out.append(p)
    return out


class Retoc:
    def __init__(self, aes=None, version=None, exe=None, log=print):
        self.aes = aes; self.version = version
        self.exe = exe or find_retoc()
        if not self.exe:
            with _DL_LOCK:
                self.exe = find_retoc()
                if not self.exe:
                    try: self.exe = download_retoc(log)
                    except Exception as e: raise FileNotFoundError('retoc (the IoStore tool) was not found and the automatic download failed (%s). Download retoc_cli from https://github.com/trumank/retoc/releases/tag/%s, put retoc.exe in the tools folder next to ModSwap, or set MODSWAP_RETOC.' % (e, RETOC_VERSION))

    def _args(self, *a):
        return [self.exe] + (['--aes-key', self.aes] if self.aes else []) + list(a)

    def _run(self, args, timeout=1800):
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=os.path.dirname(self.exe) or None)
        if r.returncode != 0:
            msg = ((r.stderr or '') + (r.stdout or '')).strip().splitlines()
            raise RuntimeError('retoc %s failed: %s' % (args[-3] if len(args) > 3 else 'run', ' | '.join(msg[-4:])[-500:]))
        return r.stdout

    # ---------------------------------------------------------------- reading
    def list_packages(self, utoc, keep=None):
        """-> [(container, path inside the game as 'Game/Content/.../Name' without extension)] for every package in one container.
        `keep` is an optional regex on the file name (without folders) to cut a 300 000-entry list down while it streams."""
        p = subprocess.Popen(self._args('list', '--path', utoc), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                             cwd=os.path.dirname(self.exe) or None)
        rx = re.compile(keep) if keep else None; out = []
        for line in p.stdout:
            m = LINE.match(line.rstrip('\n'))
            if not m or m.group(3) != 'ExportBundleData': continue
            path = m.group(4).strip().replace('\\', '/')
            if path.startswith('../../../'): path = path[9:]
            base, ext = os.path.splitext(path)
            if ext.lower() != '.uasset': continue
            if rx and not rx.search(base.rsplit('/', 1)[-1]): continue
            out.append((m.group(1), base))
        err = p.stderr.read(); p.wait()
        if p.returncode != 0: raise RuntimeError('retoc list failed on %s: %s' % (os.path.basename(utoc), err.strip().splitlines()[-1][:300] if err.strip() else 'unknown error'))
        return out

    def to_legacy(self, paks_dir, out_dir, names, chunk=40, log=print):
        """Convert the packages whose file name contains any of `names` into .uasset/.uexp (+ .ubulk) under out_dir."""
        names = list(dict.fromkeys(n for n in names if n))
        os.makedirs(out_dir, exist_ok=True)
        for i in range(0, len(names), chunk):
            args = self._args('to-legacy') + (['--version', self.version] if self.version else [])
            for n in names[i:i + chunk]: args += ['-f', n]
            self._run(args + [paks_dir, out_dir])

    # ---------------------------------------------------------------- writing
    def to_zen(self, legacy_dir, out_utoc):
        """Pack edited legacy files into <out_utoc>/.ucas/.pak. legacy_dir must hold scriptobjects.bin next to the Game/Content tree."""
        if not self.version: raise RuntimeError('retoc needs the Unreal version to write a container (e.g. 5.1)')
        os.makedirs(os.path.dirname(out_utoc), exist_ok=True)
        self._run(self._args('to-zen', '--version', self.version, legacy_dir, out_utoc))
        base = os.path.splitext(out_utoc)[0]
        missing = [e for e in ('.utoc', '.ucas', '.pak') if not os.path.isfile(base + e)]
        if missing: raise RuntimeError('retoc did not write %s' % ', '.join(missing))
        return [base + e for e in ('.pak', '.utoc', '.ucas')]
