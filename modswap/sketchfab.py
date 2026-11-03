"""Sketchfab inside the Marketplace: search millions of downloadable models and use one with a click.

  * Searching needs no account.
  * Downloading needs the user's own Sketchfab API token (sketchfab.com > Settings > Password & API > API token). It is kept on this PC only
    (Windows: encrypted for this Windows user), never shown again, and only ever sent to api.sketchfab.com.
  * Every model keeps its author's licence. We show it on the card and write a line to  %APPDATA%\\ModSwap\\sketchfab_credits.txt  for each model used.
"""
import os, re, io, sys, json, time, base64, shutil, zipfile, tempfile, urllib.request, urllib.parse, urllib.error
from .games.library import config_dir

API = 'https://api.sketchfab.com/v3'
UA = 'ModSwap-Marketplace'
SORTS = {'popular': '-likeCount', 'newest': '-publishedAt', 'views': '-viewCount'}
CATS = {'characters': 'characters-creatures', 'vehicles': 'cars-vehicles', 'weapons': 'weapons-military'}
MAX_ZIP = 800 * 1024 * 1024


# ------------------------------------------------------------------ token (kept locally)
def _path(): return os.path.join(config_dir(), 'sketchfab.json')


def _dpapi(data, protect):
    """Windows per-user encryption. Returns bytes, or None when unavailable (any other OS / any error)."""
    if not sys.platform.startswith('win'): return None
    try:
        import ctypes
        from ctypes import wintypes

        class BLOB(ctypes.Structure): _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]
        buf = ctypes.create_string_buffer(data, len(data)); inb = BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))); out = BLOB()
        f = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
        if not f(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(out)): return None
        res = ctypes.string_at(out.pbData, out.cbData); ctypes.windll.kernel32.LocalFree(out.pbData); return res
    except Exception:
        return None


def _load():
    try: return json.load(open(_path(), encoding='utf-8'))
    except Exception: return {}


def get_token():
    t = _load().get('token') or ''
    if t.startswith('dpapi:'):
        raw = _dpapi(base64.b64decode(t[6:]), False)
        return raw.decode('utf-8') if raw else ''
    return t


def _save(token, user):
    stored = token
    enc = _dpapi(token.encode('utf-8'), True)
    if enc and _dpapi(enc, False) == token.encode('utf-8'): stored = 'dpapi:' + base64.b64encode(enc).decode()     # only keep the encrypted form if it round-trips
    p = _path(); json.dump(dict(token=stored, user=user), open(p, 'w', encoding='utf-8'))
    try: os.chmod(p, 0o600)
    except Exception: pass


def status():
    d = _load(); ok = bool(get_token())
    return dict(connected=ok, user=d.get('user', '') if ok else '')


def disconnect():
    try: os.remove(_path())
    except OSError: pass
    return status()


def connect(token):
    """check the token with Sketchfab, then keep it"""
    token = (token or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9]{16,64}', token): raise ValueError("That doesn't look like a Sketchfab API token (it's a long string of letters and numbers).")
    me = _get('/me', token)
    user = me.get('displayName') or me.get('username') or 'your account'
    _save(token, user); return status()


# ------------------------------------------------------------------ http
def _get(path, token=None, timeout=20):
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if token: h['Authorization'] = 'Token ' + token
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=h), timeout=timeout) as r: return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise ValueError(_http_msg(e.code, bool(token)))
    except urllib.error.URLError as e:
        raise ValueError("Can't reach Sketchfab. Check your internet connection.")


def _http_msg(code, authed):
    if code == 401: return "Sketchfab didn't accept your token. Open the Sketchfab tab and paste it again." if authed else 'Sketchfab needs you to connect your account for that.'
    if code == 403: return "The author doesn't allow downloading this model."
    if code == 404: return 'Sketchfab no longer has that model.'
    if code == 429: return 'Sketchfab says slow down (too many requests). Wait a minute and try again.'
    return 'Sketchfab had a problem (error %d). Try again in a bit.' % code


# ------------------------------------------------------------------ search
def _license(m):
    lic = m.get('license')
    if isinstance(lic, dict): return lic.get('label') or lic.get('fullName') or lic.get('slug') or ''
    return str(lic or '')


def _thumb(m):
    imgs = ((m.get('thumbnails') or {}).get('images')) or []
    imgs = [i for i in imgs if isinstance(i, dict) and i.get('url')]
    if not imgs: return ''
    big = [i for i in imgs if (i.get('width') or 0) >= 200]
    pick = min(big, key=lambda i: i.get('width') or 0) if big else max(imgs, key=lambda i: i.get('width') or 0)
    return pick['url']


def search(q='', sort='popular', cat='', cursor=''):
    """one page (24) of downloadable models. Returns (rows, next_cursor)"""
    p = [('type', 'models'), ('downloadable', 'true'), ('count', '24')]
    if q.strip(): p.append(('q', q.strip()))
    if sort in SORTS: p.append(('sort_by', SORTS[sort]))          # any other value ("relevant") = Sketchfab's own best-match order
    if CATS.get(cat): p.append(('categories', CATS[cat]))
    if cursor: p.append(('cursor', cursor))
    r = _get('/search?' + urllib.parse.urlencode(p))
    rows = []
    for m in (r.get('results') or []):
        uid = m.get('uid')
        if not uid or m.get('isDownloadable') is False: continue
        u = m.get('user') or {}
        faces = m.get('faceCount') or 0
        rows.append(dict(uid=uid, name=str(m.get('name') or 'Model')[:80], author=str(u.get('displayName') or u.get('username') or '')[:60], license=_license(m),
                         faces=int(faces) if isinstance(faces, (int, float)) else 0, url=m.get('viewerUrl') or ('https://sketchfab.com/3d-models/' + uid), preview=_thumb(m)))
    return rows, ((r.get('cursors') or {}).get('next') or '')


# ------------------------------------------------------------------ download
def _safe_extract(zpath, dest):
    """unzip keeping folders, refusing anything that would land outside dest"""
    total = 0
    with zipfile.ZipFile(zpath) as z:
        for i in z.infolist():
            total += i.file_size
            if total > MAX_ZIP: raise ValueError('that model is too big')
        for i in z.infolist():
            parts = [x for x in i.filename.replace('\\', '/').split('/') if x and x not in ('.', '..')]
            if i.is_dir() or not parts: continue
            out = os.path.join(dest, *parts)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with z.open(i) as s, open(out, 'wb') as o: shutil.copyfileobj(s, o)


def _to_glb(folder, dest, name):
    """a Sketchfab glTF zip (scene.gltf + scene.bin + textures/) -> one self-contained .glb in dest. Falls back to copying the tree as-is."""
    gl = [os.path.join(dp, f) for dp, _, fs in os.walk(folder) for f in fs if f.lower().endswith(('.gltf', '.glb'))]
    if not gl: raise ValueError("Sketchfab's download had no 3D model in it")
    gl.sort(key=lambda p: (p.count(os.sep), p)); src = gl[0]
    safe = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')[:40] or 'model'
    if src.lower().endswith('.glb'):
        out = os.path.join(dest, safe + '.glb'); shutil.copyfile(src, out); return [os.path.basename(out)]
    try:
        import trimesh
        sc = trimesh.load(src, force='scene')
        data = sc.export(file_type='glb')
        out = os.path.join(dest, safe + '.glb'); open(out, 'wb').write(data); return [os.path.basename(out)]
    except Exception:
        names = []
        for dp, _, fs in os.walk(folder):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), folder); to = os.path.join(dest, rel); os.makedirs(os.path.dirname(to), exist_ok=True)
                shutil.copyfile(os.path.join(dp, f), to)
                if os.sep not in rel: names.append(rel)
        return names


def download(uid, dest, log=lambda *a: None, entry=None):
    tok = get_token()
    if not tok: raise ValueError('Connect your Sketchfab account first: paste your API token on the Sketchfab tab (one time).')
    log('Asking Sketchfab...')
    info = _get('/models/%s/download' % urllib.parse.quote(uid), tok)
    src = info.get('gltf') or info.get('glb')
    url = (src or {}).get('url')
    if not url: raise ValueError("Sketchfab doesn't offer this model as a download. Pick another one.")
    if not url.startswith('https://'): raise ValueError('Sketchfab sent an unexpected download link.')
    os.makedirs(dest, exist_ok=True); tmp = tempfile.mkdtemp(prefix='sfdl_'); zp = os.path.join(tmp, 'm.zip'); got = 0; last = -1
    try:
        total = int((src or {}).get('size') or 0)
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r, open(zp, 'wb') as out:      # the link is pre-signed: no token sent
            total = int(r.headers.get('Content-Length') or 0) or total
            while True:
                c = r.read(1 << 20)
                if not c: break
                got += len(c)
                if got > MAX_ZIP: raise ValueError('that model is too big')
                out.write(c)
                if total:
                    pct = int(got * 100 / total) // 10 * 10
                    if pct != last: last = pct; log('Downloading... %d%%' % min(pct, 100))
        head = open(zp, 'rb').read(4)
        ex = os.path.join(tmp, 'x'); os.makedirs(ex)
        if head[:2] == b'PK': log('Unpacking...'); _safe_extract(zp, ex)
        elif head == b'glTF': shutil.copyfile(zp, os.path.join(ex, 'model.glb'))
        else: raise ValueError('Sketchfab sent something that is not a model.')
        log('Preparing the model...')
        names = _to_glb(ex, dest, (entry or {}).get('name') or 'model')
    except urllib.error.HTTPError as e:
        raise ValueError(_http_msg(e.code, False))
    except urllib.error.URLError:
        raise ValueError("Lost the connection to Sketchfab while downloading.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if entry: credit(entry)
    return names


def credit(e):
    """one line per model used, so you always know who to thank / which licence applies"""
    try:
        with open(os.path.join(config_dir(), 'sketchfab_credits.txt'), 'a', encoding='utf-8') as f:
            f.write('%s  |  "%s" by %s  |  %s  |  %s\n' % (time.strftime('%Y-%m-%d'), e.get('name', ''), e.get('author', ''), e.get('license', '') or 'see page', e.get('url', '')))
    except Exception: pass
