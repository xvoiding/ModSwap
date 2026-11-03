"""Find the characters (skeletal meshes) and items (static meshes) inside an Unreal game's pak files.

Skeletal meshes are *verified* by reading their package header (export class == SkeletalMesh) rather than trusted by name.
Static meshes ("items": weapons, props, pickups...) are listed by name/folder; swapping them is not implemented yet.
"""
import os, re, json
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from .uepkg import parse_uasset

SKEL_NAME = re.compile(r'^(SK|SKM|SKEL)_', re.I)
NOT_MESH = re.compile(r'(_Skeleton|_PhysicsAsset|_Physics\d*|_PhysAsset\w*|_Anim\w*|_ABP|_BS|_AO)$', re.I)
ITEM_DIR = re.compile(r'(weapon|gun|item|tool|prop|pickup|gear|accessor|hat|sword|equipment|collectible|vehicle)', re.I)
STATIC_NAME = re.compile(r'^(SM|SMC|SMc|STM)_', re.I)


@dataclass
class Asset:
    path: str                  # inside the pak, without extension: Game/Content/.../SK_Name
    kind: str                  # 'skeletal' | 'static'
    name: str
    folder: str                # folder relative to Content/
    pak: str = ''
    skeleton: str = ''
    materials: list = field(default_factory=list)
    verified: bool = False
    verts: int = 0
    role: str = ''             # head / upper / lower / full / ... (filled by analyze_family)
    zmin: float = 0.0
    zmax: float = 0.0


@dataclass
class Family:
    key: str
    label: str
    skeleton: str
    assets: list = field(default_factory=list)


def _content_rel(path):
    m = re.search(r'/Content/(.*)$', '/' + path)
    return m.group(1) if m else path


def list_assets(paks, backend, log=lambda *a: None):
    """Merge file lists of all paks (later paks override earlier ones). -> {path_without_ext: (pak, [extensions])}"""
    files = {}
    bad = []; ok = 0
    for pk in paks:
        log('listing %s' % os.path.basename(pk))
        try: names = backend.list(pk)
        except Exception as e:                                       # one unreadable pak must not hide the others
            bad.append((os.path.basename(pk), str(e))); log('could not read %s: %s' % (os.path.basename(pk), str(e).strip().splitlines()[-1][:160] if str(e).strip() else e)); continue
        ok += 1
        for f in names:
            base, ext = os.path.splitext(f)
            if ext.lower() in ('.uasset', '.uexp', '.ubulk'): files.setdefault(base, [pk, set()]); files[base][0] = pk; files[base][1].add(ext.lower())
    if bad and not ok: raise RuntimeError('repak could not read any of this game\'s paks (first: %s): %s' % (bad[0][0], bad[0][1][-300:]))
    return {k: (v[0], sorted(v[1])) for k, v in files.items()}


SIBLING = re.compile(r'_(PhysicsAsset|Skeleton|PhysAsset\w*|Physics)$', re.I)
SCAN_VERSION = 2


def candidates(files):
    """(skeletal candidates, static candidates) from names only.
    Skeletal: SK_ / SKM_ / SKEL_ names, plus any asset that has a sibling "<name>_Skeleton" or "<name>_PhysicsAsset" (games that name
    their main character mesh just "Spongebob_mesh" or "Hero"). Every candidate is verified by its header afterwards."""
    sk, sm = [], []; have = set()
    stems = set()
    for base in files:
        m = SIBLING.search(base.rsplit('/', 1)[-1])
        if m: stems.add(base[:len(base) - len(m.group(0))])
    for base, (pk, exts) in files.items():
        if '.uasset' not in exts or '.uexp' not in exts: continue
        name = base.rsplit('/', 1)[-1]
        if (SKEL_NAME.match(name) or base in stems) and not NOT_MESH.search(name): sk.append(Asset(base, 'skeletal', name, os.path.dirname(_content_rel(base)), pk))
        elif STATIC_NAME.match(name) and (ITEM_DIR.search(base) or False): sm.append(Asset(base, 'static', name, os.path.dirname(_content_rel(base)), pk))
    return sorted(sk, key=lambda a: a.path), sorted(sm, key=lambda a: a.path)


def read_header(ua_bytes):
    """-> (export_class_name, skeleton_name, [material names]) from a .uasset header, or None."""
    try:
        d = parse_uasset(ua_bytes); N = d['names']
        s = lambda x: N[x[0]] if isinstance(x, tuple) else x
        if not d['exports']: return None
        c = d['exports'][0].get('class', 0)
        cls = s(d['imports'][-c - 1]['name']) if c < 0 and -c - 1 < len(d['imports']) else ''
        sk = next((s(im['name']) for im in d['imports'] if s(im['class_name']) == 'Skeleton'), '')
        mats = [s(im['name']) for im in d['imports'] if s(im['class_name']) in ('MaterialInstanceConstant', 'Material', 'MaterialInstance')]
        return cls, sk, mats
    except Exception:
        return None


def verify_skeletal(cands, backend, cache_dir, log=lambda *a: None):
    """Extract the .uasset headers of the candidates and keep those that really are SkeletalMeshes."""
    by_pak = defaultdict(list)
    for a in cands: by_pak[a.pak].append(a)
    out = []
    hdr = os.path.join(cache_dir, 'headers'); os.makedirs(hdr, exist_ok=True)
    for pk, assets in by_pak.items():
        log('reading %d asset headers' % len(assets))
        backend.unpack(pk, hdr, [a.path + '.uasset' for a in assets])
        for a in assets:
            f = os.path.join(hdr, a.path + '.uasset')
            if not os.path.exists(f): continue
            h = read_header(open(f, 'rb').read())
            if h and h[0] == 'SkeletalMesh':
                a.skeleton, a.materials, a.verified = h[1], h[2], True; out.append(a)
    return out


SATELLITE = re.compile(r'^(brokenparts?|broken|morph\w*|variants?|gore|gibs?|dismember\w*|severed|limbs?|debris)$', re.I)
PIECE = re.compile(r'^(brokenparts?|broken|gore|gibs?|dismember\w*|severed|limbs?|debris)$', re.I)
GENERIC = re.compile(r'^(skeletalmeshes|skeletal|meshes|mesh|models?|characters?|art|content|parts)$', re.I)


def _segs(folder): return [x for x in folder.replace('\\', '/').split('/') if x]


def _root(folder):
    """character folder: strip trailing BrokenParts / MorphTarget / Gore ... folders."""
    s = _segs(folder)
    while len(s) > 1 and (SATELLITE.match(s[-1]) or GENERIC.match(s[-1])): s.pop()
    return '/'.join(s)


def _is_piece(a): return any(PIECE.match(x) for x in _segs(a.folder))


def _is_satellite(a): return any(SATELLITE.match(x) for x in _segs(a.folder))


def _nice(root):
    for x in reversed(_segs(root)):
        if not GENERIC.match(x): return re.sub(r'[_\-]+', ' ', x).strip()
    return root


def families(skeletal):
    """Group skeletal meshes into *characters*.
    Meshes sharing a skeleton are one family. Dismember / broken-part pieces (Stanislav L arm, L forearm, torso ...) and morph variants,
    which usually each come with their own skeleton, are folded into the character whose folder they live under instead of
    showing up as dozens of separate "characters". Pieces are kept (role='piece') but are never swapped or used as references."""
    g = defaultdict(list)
    for a in skeletal:
        a.role = 'piece' if _is_piece(a) else a.role if a.role != 'piece' else ''
        key = a.skeleton or ('dir:' + '/'.join(a.folder.split('/')[:2]))
        g[key].append(a)
    fams = []
    for key, items in g.items():
        label = re.sub(r'^(SK_|SKEL_)|(_Skeleton|_Skel)$', '', key) if not key.startswith('dir:') else key[4:]
        top = defaultdict(int)
        for a in items: top['/'.join(a.folder.split('/')[:2])] += 1
        folder = max(top, key=top.get)
        fams.append(Family(key, '%s  (%s)' % (label, folder), key if not key.startswith('dir:') else '', sorted(items, key=lambda a: a.path)))
    mains = [f for f in fams if not all(_is_satellite(a) for a in f.assets)]
    by_root = {}
    for f in sorted(mains, key=lambda f: -len(f.assets)):
        for a in f.assets:
            if not _is_satellite(a): by_root.setdefault(a.folder, f)
    out = list(mains); merged = set()
    for f in fams:
        if f in mains: continue
        roots = {_root(a.folder) for a in f.assets}
        host = next((by_root[r] for r in roots if r in by_root), None)
        if host is None:                                    # a satellite with no body of its own: still show it, but as one entry per folder
            host = by_root.get(next(iter(roots)))
        if host is None:
            if all(_is_piece(a) for a in f.assets): continue        # loose gore / gib with no character: not swappable, skip
            out.append(f); continue
        host.assets = sorted(host.assets + f.assets, key=lambda a: a.path); merged.add(id(host))
    for f in out:
        if id(f) in merged:
            body = [a for a in f.assets if not _is_piece(a)]
            roots = defaultdict(int)
            for a in body: roots[_root(a.folder)] += 1
            r = max(roots, key=roots.get) if roots else ''
            f.label = '%s  (%s)' % (_nice(r), '/'.join(_segs(r)[:2]))
    return sorted(out, key=lambda f: -len([a for a in f.assets if a.role != 'piece']))


def scan_unreal(paks, backend, cache_dir, log=lambda *a: None):
    """Full scan -> dict(characters=[Family], items=[Asset])"""
    files = list_assets(paks, backend, log)
    sk_c, sm_c = candidates(files)
    log('%d skeletal candidates, %d item candidates' % (len(sk_c), len(sm_c)))
    sk = verify_skeletal(sk_c, backend, cache_dir, log)
    return dict(characters=families(sk), items=sm_c, total_files=len(files))


def save_scan(res, path):
    json.dump(dict(characters=[dict(key=f.key, label=f.label, skeleton=f.skeleton, assets=[asdict(a) for a in f.assets]) for f in res['characters']],
                   items=[asdict(a) for a in res['items']], total_files=res['total_files'], ver=SCAN_VERSION), open(path, 'w'), indent=1)


def load_scan(path):
    d = json.load(open(path))
    allsk = [Asset(**a) for f in d['characters'] for a in f['assets']]
    return dict(characters=families(allsk), items=[Asset(**a) for a in d['items']], total_files=d['total_files'])
