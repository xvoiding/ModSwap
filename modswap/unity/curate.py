"""Sort a Unity game's scanned models into something a person can read: people / vehicles / weapons / props, and hide the rest
(whole levels, map chunks, walls and floors, trees and rocks, primitives, tiles, and objects with random machine names).

Everything is still in the scan; each model just gets a `cat`:
    character  rigged people and creatures            vehicle   cars, trucks, boats, planes ...
    weapon     guns, swords ...                       prop      a plausible stand-alone object
    scenery    trees, rocks, walls, repeating tiles   level     big level / map geometry
    junk       primitives, tiny or nameless meshes
and a `score` used for ordering. The UI shows character / vehicle / weapon / prop by default and keeps the others behind "show hidden"."""
import re, collections
import numpy as np

SHOWN = ('character', 'vehicle', 'weapon', 'prop')
CAT_ORDER = {c: i for i, c in enumerate(('character', 'vehicle', 'weapon', 'prop', 'scenery', 'level', 'junk'))}

VEHICLE = set('truck car vehicle bus van jeep tank bike bicycle motorcycle motorbike boat ship airplane aeroplane helicopter heli train tractor taxi sedan suv tram kart ufo rocket jet submarine yacht canoe sled scooter limo'.split())
WEAPON = set('weapon gun pistol rifle shotgun smg sniper sword knife axe bow crossbow grenade launcher bazooka katana dagger spear mace shield blaster cannon revolver uzi'.split())
BEING = set('player enemy enemies npc character human person man woman boy girl guy lady zombie monster boss robot dog cat animal guard soldier cop police kid child baby skeleton ghost alien dragon goat chicken horse bear pig cow sheep wolf rat spider shark fish bird duck citizen worker civilian customer villager clown president'.split())
LEVEL = set('level map terrain scene world island city town village street road ground floor wall walls ceiling roof sky skybox dome water ocean sea lake river cave tunnel corridor hallway room hall arena stage landscape environment env scenery backdrop background lightmap occlusion navmesh collider colliders trigger bounds chunk tile tiles section combined batch lod decal ruins castle temple building buildings house houses tower towers bridge brdige stairs stair fence gate platform cliff cliffs mountain mountains hill hills'.split())
SCENERY = set('tree trees fir bush bushes grass cactus rock rocks stone stones boulder crystal grave candle lantern lamp pole pillar pillars column spike spikes pipe pipes cog cogs fracture cell debris rubble log logs stick fern flower flowers plant plants leaf leaves cloud clouds star stars sign banner flag cobweb web moss ice icicle snow sand dirt'.split())
GENERIC = set('cube plane sphere circle cylinder icosphere quad capsule cone torus mesh default gameobject object model group node geo geometry static new test temp empty root combined pb polysurface pcube psphere pcylinder untitled shape part piece prefab clone copy unnamed'.split())


def tokens(name):
    n = re.sub(r'([a-z])([A-Z])', r'\1 \2', name or '')
    n = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', n)
    out = []
    for t in re.split(r'[^A-Za-z]+', n):
        t = t.lower()
        if not t: continue
        out.append(t)
        if t.endswith('s') and len(t) > 3: out.append(t[:-1])
        if t.endswith('es') and len(t) > 4: out.append(t[:-2])
    return out


def name_ok(name):
    """False for names that carry no information: 'Cube.001', 'pb_Mesh-3725920', 'Combined Mesh (root: scene)', hashes, 'GameObject'"""
    n = (name or '').strip()
    if len(n) < 3: return False
    if re.search(r'combined mesh|root:\s*scene', n, re.I): return False
    base = re.sub(r'[\s._-]*\d+$', '', n)
    toks = [t for t in tokens(base) if len(t) > 1]
    if not toks or all(t in GENERIC for t in toks): return False
    letters = sum(c.isalpha() for c in n)
    if letters < 0.5 * len(n): return False                               # mostly digits / symbols
    if re.fullmatch(r'[0-9a-fA-F]{8,}|[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}', n): return False
    if len(n) >= 6 and not re.search(r'[aeiouyAEIOUY]', n): return False  # 'xkqzjw': no vowels
    if re.search(r'(.)\1{3,}', n): return False
    return True


def clean(n): return re.sub(r'\s*[\(\[]\d+[\)\]]$|[ _.-]?\d+$', '', n or '').strip()


def _kind_of(names):
    tk = set()
    for n in names: tk.update(tokens(n))
    if tk & VEHICLE: return 'vehicle'
    if tk & WEAPON: return 'weapon'
    if tk & BEING: return 'character'
    return None


def _has(names, bag):
    tk = set()
    for n in names: tk.update(tokens(n))
    return bool(tk & bag)


def pick_label(m):
    """the most informative name: the object's own name, else its parent's, else the mesh's"""
    own = clean(m.get('label_own') or m['label'].split(' › ')[-1]); par = clean(m.get('parent') or '')
    meshn = clean(m.get('main_name') or '')
    good = [n for n in (own, par, meshn) if name_ok(n)]
    if not good: return None
    if name_ok(own) and name_ok(par) and par.lower() not in own.lower() and par.lower() not in ('map', 'root', 'scene', 'level', 'props', 'stuff', 'static', 'objects'):
        return par + ' › ' + own
    return good[0]


def rate(m):
    """-> (cat, score, label or None)"""
    if m.get('kind') == 'skinned':
        names = [m['label'], m.get('main_name', '')] + [p['name'] for p in m.get('parts', [])]
        lab = pick_label(m) or m['label']
        # rigged things in a level are people unless the name says otherwise
        k = _kind_of(names)
        cat = 'vehicle' if k == 'vehicle' else 'weapon' if k == 'weapon' else 'character'
        s = 100 + (10 if m.get('hot') else 0) + min(m.get('bones', 0), 80) / 8.0 - (6 if not name_ok(lab) else 0) - (4 if m['instances'] > 40 else 0)
        return cat, s, lab
    own = [m['label'].split(' \u203A ')[-1], m.get('main_name') or ''] + [p['name'] for p in m.get('parts', [])]
    names = own + [m.get('parent') or '']
    lab = pick_label(m)
    lo, hi = np.array(m.get('lo', [0, 0, 0]), float), np.array(m.get('hi', [0, 0, 0]), float)
    ext = np.maximum(hi - lo, 0); big = float(ext.max()); small = float(ext.min())
    own_level = _has(own[:1], LEVEL) or _has([m.get('parent') or ''], LEVEL) and not _kind_of(own)
    kind = _kind_of(own) or (None if own_level or _has(own[:1], SCENERY) else _kind_of([m.get('parent') or '']))
    inst, verts, nparts = m['instances'], m['verts'], len(m['parts'])
    # --- hard rejections
    if kind is None:
        if own_level or re.search(r'combined mesh', ' '.join(names), re.I): return 'level', 0, lab
        if big > 60 or verts > 80000 or (nparts > 30 and inst == 1) or (big > 20 and small < 0.04 * big): return 'level', 0, lab
        if big < 0.03: return 'junk', 0, lab
    elif kind in ('vehicle', 'weapon', 'character'):
        if big > 150: return 'level', 0, lab
    if lab is None and kind is None: return 'junk', 0, None
    if verts < 40 and kind is None: return 'junk', 0, lab
    if kind is None:
        if _has(own[:1], SCENERY) or _has([m.get('parent') or ''], SCENERY): return 'scenery', 0, lab
        if inst >= 120: return 'scenery', 0, lab                    # a tile / brick / tree that is repeated everywhere
        if verts < 160 and nparts == 1 and not name_ok(clean(m.get('main_name') or '')) and not name_ok(clean(m['label'])): return 'junk', 0, lab
    # --- plausible: score it
    s = 20.0
    if kind: s += 60
    s += 8 if name_ok(clean(m['label'].split(' › ')[-1])) else 0
    s += 5 * min(np.log10(max(verts, 10)) - 1.5, 2.0)                # a few hundred to tens of thousands of verts is a real object
    s -= min(inst, 200) * 0.12                                       # the fewer copies the more it is a "thing"
    s += 4 if 0.3 < big < 25 else -4
    s += 3 if nparts > 1 else 0
    if m.get('hot'): s += 5
    return (kind or 'prop'), s, lab


def curate(models, cap_props=80):
    """annotate + order. Duplicates (same name and size in many levels) collapse into one entry. -> list with fresh `index`"""
    out = []; seen = {}
    for m in models:
        cat, score, lab = rate(m)
        m['cat'] = cat; m['score'] = round(float(score), 2)
        if lab: m['pretty'] = lab
        if cat in SHOWN:
            key = (cat, (lab or '').lower(), m['verts'] // 8, m.get('kind'))
            if lab and key in seen:
                d = seen[key]; d['instances'] += m['instances']; d['also'] = d.get('also', 0) + 1; continue
            seen[key] = m
        out.append(m)
    shown = [m for m in out if m['cat'] in SHOWN]
    props = sorted([m for m in shown if m['cat'] == 'prop'], key=lambda m: -m['score'])
    drop = {id(m) for m in props[cap_props:]}
    for m in out:
        if id(m) in drop: m['cat'] = 'scenery'                       # the long tail of props moves behind "show hidden"
    out.sort(key=lambda m: (CAT_ORDER[m['cat']], -m['score'], m['label']))
    for i, m in enumerate(out): m['index'] = i
    return out
