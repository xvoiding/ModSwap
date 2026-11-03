"""Model marketplace: a list of ready-made 3D models people can pick and use without hunting for them on a model site.

Where models come from (all merged into one list):
  1. the  marketplace/  folder next to ModSwap.exe          (ships with the app - drop your models in here)
  2. the  %APPDATA%\\ModSwap\\marketplace  folder             (per-user; the app has a button that opens it)
  3. any extra folders / online catalogs listed in  %APPDATA%\\ModSwap\\market.json
        {"folders": ["D:\\\\MyModels"], "urls": ["https://example.com/catalog.json"]}
  4. DEFAULT_CATALOG_URLS below (the "official" online catalog)

A model in a folder is one of:
  - a sub-folder (model file + textures + optional info.json / preview.png)       name = folder name
  - a .zip (optionally with a same-named .png/.jpg next to it as the picture)      name = file name
  - a single self-contained model file (.glb / .vrm / .fbx ...)
  - listed in a  catalog.json  inside the folder (see below)

catalog.json (works the same on a website and inside a folder; "url" and "preview" may be relative to the catalog):
  {"models": [{"name": "Big Smoke", "author": "someone", "description": "...", "category": "people", "tags": ["gta", "npc"],
               "games": ["Sparking Zero"], "url": "models/big_smoke.zip", "preview": "models/big_smoke.png", "size": 12345678}]}

info.json inside a model folder takes the same keys (name, author, description, category, tags, games, preview).
"""
import os, re, io, json, time, shutil, hashlib, zipfile, urllib.request, urllib.parse
from .games.library import config_dir
from .modelio import MODEL_EXT, IMAGE_EXT

DEFAULT_CATALOG_URLS = []            # put the address of your hosted catalog.json here to ship it with the app
MAX_DOWNLOAD = 1536 * 1024 * 1024     # a single model download is capped at 1.5 GB
KEEP = tuple(MODEL_EXT) + tuple(IMAGE_EXT) + ('.bin', '.mtl')
PREVIEW_NAMES = ('preview', 'thumb', 'thumbnail', 'cover', 'icon', 'poster')
_REG = {}                             # id -> entry (internal fields included)
_SF = {}                              # Sketchfab results seen this session (kept apart so re-listing the folders doesn't drop them)


# ------------------------------------------------------------------ settings / folders
def bundled_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'marketplace')


def user_dir():
    d = os.path.join(config_dir(), 'marketplace'); os.makedirs(d, exist_ok=True); return d


def settings():
    try: s = json.load(open(os.path.join(config_dir(), 'market.json'), encoding='utf-8'))
    except Exception: s = {}
    return dict(folders=[x for x in (s.get('folders') or []) if isinstance(x, str)], urls=[x for x in (s.get('urls') or []) if isinstance(x, str)])


def folders():
    seen, out = set(), []
    for d in [bundled_dir(), user_dir()] + settings()['folders']:
        d = os.path.abspath(os.path.expanduser(d)); k = os.path.normcase(d)
        if k not in seen and os.path.isdir(d): seen.add(k); out.append(d)
    return out


def catalog_urls():
    return list(dict.fromkeys(DEFAULT_CATALOG_URLS + settings()['urls']))


# ------------------------------------------------------------------ helpers
def _pretty(s):
    s = os.path.splitext(s)[0] if s.lower().endswith(('.zip',) + tuple(MODEL_EXT)) else s
    s = re.sub(r'[_]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s) or 'Model'


def _tags(v):
    if isinstance(v, str): v = re.split(r'[,;]', v)
    return [str(t).strip() for t in (v or []) if str(t).strip()][:12]


def _eid(*parts):
    return hashlib.sha1('|'.join(str(p) for p in parts).encode('utf-8', 'ignore')).hexdigest()[:12]


def _is_url(s): return bool(re.match(r'^https?://', str(s or ''), re.I))


def _join(base, rel):
    """resolve rel against a catalog's location (a folder path or a URL)"""
    if not rel: return ''
    if _is_url(rel): return rel
    if _is_url(base): return urllib.parse.urljoin(base, rel)
    return os.path.normpath(os.path.join(base, rel)) if not os.path.isabs(rel) else rel


def _find_preview(d, stem=None):
    try: names = os.listdir(d)
    except OSError: return ''
    low = {n.lower(): n for n in names}
    if stem:
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            if (stem + ext).lower() in low: return os.path.join(d, low[(stem + ext).lower()])
        return ''
    for p in PREVIEW_NAMES:
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            if p + ext in low: return os.path.join(d, low[p + ext])
    return ''


def _entry(src, name, kind, ref, meta):
    """one marketplace item. kind: dir | zip | file | url ; ref: path or url ; meta: info.json / catalog keys"""
    name = str(meta.get('name') or name or 'Model').strip()
    e = dict(id=_eid(src, kind, ref, name), name=name[:80], author=str(meta.get('author') or '')[:60],
             description=str(meta.get('description') or meta.get('desc') or '')[:400], category=str(meta.get('category') or '').strip().lower()[:24],
             tags=_tags(meta.get('tags')), games=_tags(meta.get('games')), size=int(meta.get('size') or 0), source=src, kind=kind, ref=ref,
             preview=meta.get('preview') or '')
    return e


def _dir_size(d):
    n = 0
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.lower().endswith(KEEP):
                try: n += os.path.getsize(os.path.join(dp, f))
                except OSError: pass
    return n


def _has_model(d):
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.lower().endswith(tuple(MODEL_EXT) + ('.zip',)): return True
    return False


# ------------------------------------------------------------------ local folders
def scan_folder(root, src='local'):
    out = []
    try: items = sorted(os.listdir(root), key=str.lower)
    except OSError: return out
    cat = os.path.join(root, 'catalog.json')
    if os.path.isfile(cat): out += parse_catalog(cat, root, 'local')
    claimed = set()
    for e in out:
        r = e.get('ref') or ''
        if r and not _is_url(r): claimed.add(os.path.normcase(os.path.abspath(r)))
    for n in items:
        p = os.path.join(root, n)
        if n.startswith(('.', '_')) or n.lower() == 'catalog.json' or n.lower() == 'readme.md': continue
        if os.path.normcase(os.path.abspath(p)) in claimed: continue
        if os.path.isdir(p):
            if not _has_model(p): continue
            meta = {}
            try: meta = json.load(open(os.path.join(p, 'info.json'), encoding='utf-8'))
            except Exception: pass
            pv = _join(p, meta.get('preview')) if meta.get('preview') else _find_preview(p)
            out.append(_entry(src, _pretty(n), 'dir', p, dict(meta, preview=pv, size=meta.get('size') or _dir_size(p))))
        elif n.lower().endswith('.zip') or n.lower().endswith(tuple(MODEL_EXT)):
            stem = os.path.splitext(n)[0]
            sz = 0
            try: sz = os.path.getsize(p)
            except OSError: pass
            out.append(_entry(src, _pretty(n), 'zip' if n.lower().endswith('.zip') else 'file', p, dict(size=sz, preview=_find_preview(root, stem))))
    return out


# ------------------------------------------------------------------ catalogs (json file or url)
def parse_catalog(where, base, src):
    """where: path/url of the json (for messages); base: folder/url that relative links resolve against"""
    if _is_url(where): raw = _http_json(where)
    else: raw = json.load(open(where, encoding='utf-8'))
    items = raw.get('models') if isinstance(raw, dict) else raw
    out = []
    for m in (items or []):
        if not isinstance(m, dict): continue
        ref = m.get('url') or m.get('download') or m.get('file') or m.get('path')
        if not ref: continue
        ref = _join(base, str(ref))
        if _is_url(base) and not _is_url(ref): continue                   # an online catalog may only point at web links, never at files on this PC
        name = m.get('name') or _pretty(os.path.basename(urllib.parse.urlparse(ref).path) or 'Model')
        pv = m.get('preview') or m.get('image') or m.get('thumb') or ''
        kind = 'url' if _is_url(ref) else ('dir' if os.path.isdir(ref) else 'zip' if ref.lower().endswith('.zip') else 'file')
        pv = _join(base, str(pv)) if pv else ''
        if _is_url(base) and pv and not _is_url(pv): pv = ''
        out.append(_entry('online' if kind == 'url' else src, str(name), kind, ref, dict(m, preview=pv)))
    return out


def _cache_dir():
    d = os.path.join(config_dir(), 'market_cache'); os.makedirs(d, exist_ok=True); return d


def _http_get(url, timeout=12, limit=None):
    if not _is_url(url): raise ValueError('only http(s) links are allowed')
    req = urllib.request.Request(url, headers={'User-Agent': 'ModSwap-Marketplace'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(limit + 1 if limit else -1)
    if limit and len(data) > limit: raise ValueError('that file is too big')
    return data


def _http_json(url):
    cache = os.path.join(_cache_dir(), 'cat_' + _eid(url) + '.json')
    try:
        data = _http_get(url, timeout=10, limit=16 * 1024 * 1024)
        obj = json.loads(data.decode('utf-8-sig'))
        open(cache, 'wb').write(data); return obj
    except Exception as ex:
        if os.path.isfile(cache):                                       # offline: show the copy from last time
            obj = json.load(open(cache, encoding='utf-8-sig')); _STALE.append(url); return obj
        raise ex


_STALE = []


# ------------------------------------------------------------------ the list
def listing():
    """everything available right now (public fields only) + notes about sources that couldn't be read"""
    _REG.clear(); _STALE.clear(); errors = []; entries = []
    for d in folders():
        try: entries += scan_folder(d)
        except Exception as ex: errors.append('%s: %s' % (d, ex))
    for u in catalog_urls():
        try: entries += parse_catalog(u, u, 'online')
        except Exception as ex: errors.append("couldn't reach the online catalog (%s)" % (str(ex)[:80]))
    seen = set(); pub = []
    for e in entries:
        if e['id'] in seen: continue
        seen.add(e['id']); _REG[e['id']] = e
        pub.append(dict(id=e['id'], name=e['name'], author=e['author'], description=e['description'], category=e['category'], tags=e['tags'], games=e['games'],
                        size=e['size'], source=e['source'], preview=bool(e['preview'])))
    pub.sort(key=lambda x: x['name'].lower())
    if _STALE: errors.append("online catalog is offline - showing the copy saved last time")
    return dict(models=pub, errors=errors, folder=user_dir(), bundled=bundled_dir(), online=bool(catalog_urls()))


def sketchfab_search(q='', sort='popular', cat='', cursor=''):
    """one page of Sketchfab results in the same shape as listing()['models'] (+ license, faces, url)"""
    from . import sketchfab
    rows, nxt = sketchfab.search(q, sort, cat, cursor)
    if len(_SF) > 1500: _SF.clear()
    pub = []
    for r in rows:
        mid = 'sf:' + r['uid']
        _SF[mid] = dict(id=mid, name=r['name'], author=r['author'], license=r['license'], url=r['url'], kind='sketchfab', ref=r['uid'], preview=r['preview'], size=0, source='sketchfab')
        pub.append(dict(id=mid, name=r['name'], author=r['author'], description='', category='', tags=[], games=[], size=0, source='sketchfab', preview=bool(r['preview']),
                        license=r['license'], faces=r['faces'], url=r['url']))
    return dict(models=pub, next=nxt, **sketchfab.status())


def _get(mid):
    if mid in _SF: return _SF[mid]
    if mid not in _REG: listing()
    e = _REG.get(mid)
    if not e: raise KeyError('that model is no longer in the marketplace - reopen the page')
    return e


def preview_jpeg(mid):
    """small JPEG of the model's picture, or None"""
    from PIL import Image
    e = _get(mid); pv = e.get('preview')
    if not pv: return None
    try:
        if _is_url(pv):
            cache = os.path.join(_cache_dir(), 'pv_' + _eid(pv) + '.jpg')
            if os.path.isfile(cache): return open(cache, 'rb').read()
            im = Image.open(io.BytesIO(_http_get(pv, timeout=12, limit=12 * 1024 * 1024)))
        else: im = Image.open(pv)
        im.load(); im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (16, 16, 16, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
        im.thumbnail((420, 420)); b = io.BytesIO(); im.save(b, 'JPEG', quality=86); data = b.getvalue()
        if _is_url(pv): open(cache, 'wb').write(data)
        return data
    except Exception:
        return None


# ------------------------------------------------------------------ getting a model onto this PC
def _copy_flat(src_dir, dest, names, budget):
    for dp, _, fs in os.walk(src_dir):
        for f in sorted(fs):
            if not f.lower().endswith(KEEP) or f.startswith('._'): continue
            p = os.path.join(dp, f); budget[0] += os.path.getsize(p)
            if budget[0] > MAX_DOWNLOAD: raise ValueError('that model is too big')
            out = f
            if os.path.exists(os.path.join(dest, out)): out = os.path.basename(dp) + '__' + f
            shutil.copyfile(p, os.path.join(dest, out)); names.append(out)


def fetch(mid, dest, log=lambda *a: None):
    """put the model's files (flat) into dest. Returns (display name, [file names])."""
    from .server import _extract_zip
    e = _get(mid); os.makedirs(dest, exist_ok=True); names = []
    log('Getting %s...' % e['name'])
    if e['kind'] == 'sketchfab':
        from . import sketchfab
        names += sketchfab.download(e['ref'], dest, log, e)
    elif e['kind'] == 'dir':
        _copy_flat(e['ref'], dest, names, [0])
    elif e['kind'] == 'file':
        shutil.copyfile(e['ref'], os.path.join(dest, os.path.basename(e['ref']))); names.append(os.path.basename(e['ref']))
    elif e['kind'] == 'zip':
        tmp = os.path.join(dest, '_copy.zip'); shutil.copyfile(e['ref'], tmp)       # _extract_zip deletes the zip it unpacks - never let that be the marketplace's original
        names += _extract_zip(tmp, dest)
    else:                                           # online
        url = e['ref']; tmp = os.path.join(dest, '_download.part'); got = 0; last = -1
        req = urllib.request.Request(url, headers={'User-Agent': 'ModSwap-Marketplace'})
        with urllib.request.urlopen(req, timeout=30) as r, open(tmp, 'wb') as out:
            total = int(r.headers.get('Content-Length') or 0) or e['size']
            while True:
                chunk = r.read(1 << 20)
                if not chunk: break
                got += len(chunk)
                if got > MAX_DOWNLOAD: raise ValueError('that model is too big')
                out.write(chunk)
                if total:
                    pct = int(got * 100 / total) // 10 * 10
                    if pct != last: last = pct; log('Downloading... %d%%' % min(pct, 100))
        head = open(tmp, 'rb').read(4)
        base = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(url).path)) or 'model'
        if head[:2] == b'PK' and not base.lower().endswith(tuple(MODEL_EXT)):
            z = os.path.join(dest, '_download.zip'); os.replace(tmp, z)
            try: names += _extract_zip(z, dest)
            finally: os.path.exists(z) and os.remove(z)
        else:
            if not base.lower().endswith(KEEP): base += '.glb' if head == b'glTF' else '.fbx'
            os.replace(tmp, os.path.join(dest, base)); names.append(base)
    if not any(n.lower().endswith(tuple(MODEL_EXT)) for n in names): raise ValueError("this entry has no 3D model file in it")
    log('Ready.')
    return e['name'], names


# ------------------------------------------------------------------ for whoever fills the marketplace
def build_catalog(src, out, base_url='', log=print):
    """Turn a folder of models into something you can host:  out/catalog.json  +  one .zip and one preview picture per model.
    Upload the whole out folder anywhere that gives direct links (GitHub, your own site...), then put the link to catalog.json in market.json
    (or in DEFAULT_CATALOG_URLS). base_url = the address out/ will be served from, e.g. https://raw.githubusercontent.com/me/models/main/"""
    from PIL import Image
    os.makedirs(out, exist_ok=True); models = []; used = set()
    for e in scan_folder(src):
        if e['kind'] == 'url': continue
        slug = re.sub(r'[^a-z0-9]+', '-', e['name'].lower()).strip('-') or 'model'
        while slug in used: slug += '-2'
        used.add(slug); zpath = os.path.join(out, slug + '.zip')
        if e['kind'] == 'zip': shutil.copyfile(e['ref'], zpath)
        else:
            with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
                if e['kind'] == 'file': z.write(e['ref'], os.path.basename(e['ref']))
                else:
                    for dp, _, fs in os.walk(e['ref']):
                        for f in sorted(fs):
                            if f.lower().endswith(KEEP): z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), e['ref']))
        item = dict(name=e['name'], author=e['author'], description=e['description'], category=e['category'], tags=e['tags'], games=e['games'],
                    url=base_url + slug + '.zip', size=os.path.getsize(zpath))
        if e.get('preview') and os.path.isfile(e['preview']):
            try:
                im = Image.open(e['preview']).convert('RGBA'); im.thumbnail((420, 420)); im.save(os.path.join(out, slug + '.png')); item['preview'] = base_url + slug + '.png'
            except Exception: pass
        models.append(item); log('  + %s  (%.1f MB)' % (e['name'], item['size'] / 1048576.0))
    json.dump(dict(models=models), open(os.path.join(out, 'catalog.json'), 'w', encoding='utf-8'), indent=1)
    log('wrote %d models to %s' % (len(models), os.path.join(out, 'catalog.json')))
    return len(models)
