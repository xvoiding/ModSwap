"""Which material does each mesh part of a Spider-Man .model use, and what does that material look like (shader, textures)?
The model keeps its materials as 16-byte records (u32, 8-byte asset id, u32) right after a table of offsets; mesh part k uses record k. Each record's id is a
material asset in the toc whose text names its shader and textures."""
import re, struct
from . import model as M

TAG_MATERIAL_LIST = 0x3250BB80
_TEXT = re.compile(rb'[\x20-\x7e]{6,}')


def _path_strings(model):
    """the material paths the model names in its string area (the material list section holds a (path, name) pair of string offsets per material)"""
    off, size = model.sections[TAG_MATERIAL_LIST]; d = model.data; out = []
    for k in range(0, size // 8 - 1, 2):
        o = struct.unpack_from('<Q', d, M.DAT1_AT + off + 8 * k)[0]
        if not 0 < o < len(d) - M.DAT1_AT: break
        e = d.find(b'\0', M.DAT1_AT + o); b = d[M.DAT1_AT + o:e]
        if not b or not all(32 <= c < 127 for c in b): break
        out.append(b.decode('latin1'))
    return out


def material_ids(model, toc):
    """-> [asset number of the material for slot 0, 1, ...] (empty when the table cannot be found). Slot k = the k-th material path the model names; the 16-byte record table after the section is the fallback."""
    try:
        ids = [toc.find(p) for p in _path_strings(model)]
        if ids and all(i is not None for i in ids): return ids
        ids = [i for i in ids if i is not None]
    except Exception: ids = []
    scan = _scan_ids(model, toc)
    return ids if len(ids) > len(scan) else scan


def _scan_ids(model, toc):
    off, size = model.sections[TAG_MATERIAL_LIST]; off += M.DAT1_AT; data = model.data
    first = None
    for p in range(off, min(len(data) - 8, off + size + 512), 4):
        if toc.find(struct.unpack_from('<Q', data, p)[0]) is not None: first = p; break
    if first is None: return []
    out = []; p = first
    while p + 8 <= len(data) and len(out) < 256:
        i = toc.find(struct.unpack_from('<Q', data, p)[0])
        if i is None: break
        out.append(i); p += 16
    return out


def describe(toc, ad, i):
    """-> dict(shader=..., textures=[paths as written], size)"""
    try: b = toc.read(i, ad)
    except Exception: return dict(shader='', textures=[], size=toc.size(i))
    words = [m.group().decode('latin1') for m in _TEXT.finditer(b) if b'Material Built' not in m.group()]
    shader = next((w for w in words if 'materialtemplates' in w.lower() or 'materialgraph' in w.lower()), '')
    return dict(shader=shader.replace('\\', '/'), textures=[w.replace('\\', '/') for w in words if w.lower().endswith('.texture')], size=toc.size(i))


def slots(model, toc, ad):
    """-> list of dict(slot, material (asset number), shader, textures, triangles) for every slot the model has"""
    ids = material_ids(model, toc); tri = {}
    for m in model.meshes(): tri[m.material] = tri.get(m.material, 0) + m.index_count // 3
    out = []
    for k, i in enumerate(ids):
        d = describe(toc, ad, i); d.update(slot=k, material=i, triangles=tri.get(k, 0)); out.append(d)
    return out


def folder_of(suit):
    """the asset folder a character's own textures live in: hero_spiderman_<suit> for suits, npc_<x> for the other characters"""
    s = suit.lower(); return s if s.startswith('npc_') else 'hero_spiderman_%s' % s


ACC_WORDS = set('glass lens lense eye button strap zip chain logo teeth mouth hair visor wrist cuff badge pad trim frame spider clasp ring tube wire cable light led jewel gem bolt rivet shoe sole glove boot spike stud lace patch gun belt'.split())
ACC_PREFIX = ('webshoot', 'shooter', 'fasten', 'buckle', 'gauntlet', 'accessor', 'hardware', 'emblem', 'goggle', 'helmet', 'pouch', 'holster', 'tubing')


def _accessory(name):
    """True when a texture name (the part after the suit's name) says it is a small add-on piece, not the main cloth: whole words only ('damagemask' is not a 'gem')"""
    import re
    toks = re.findall('[a-z]+', name.lower())
    return any(t.rstrip('s') in ACC_WORDS or t.startswith(ACC_PREFIX) or any(w in t for w in ('frame', 'lens', 'emissive', 'glow', 'eyes')) for t in toks)


def slot_choices(rows, suit):
    """-> [(tier, preferred name, triangles, slot)] best first. Only slots whose colour texture is in the character's OWN folder qualify (replacing a shared texture would re-skin other characters).
    tier 3 = the plain 'colour + normal + gloss' kind (the colour texture is the whole look), 2 = another shader with its own colour + normal + gloss, 1 = another shader with its own colour texture."""
    out = []; folder = folder_of(suit)
    for r in rows:
        tex = [t.lower().replace('\\', '/') for t in r['textures']]; sh = r['shader'].lower()
        own_c = [t for t in tex if t.endswith('_c.texture') and folder in t]
        if not own_c: continue
        has = lambda role: any(t.endswith('_%s.texture' % role) and folder in t for t in tex)
        plain = 'basic_normal_gloss' in sh and 'alpha' not in sh and 'detail' not in sh and 'eye' not in sh
        tier = 3 if plain and has('n') and has('g') else 2 if has('n') and has('g') else 1
        own = [t for t in tex if folder in t]
        names = ' '.join(re.sub('hero|spiderman|' + re.escape(suit.lower().replace('npc_', '')), '', t.rsplit('/', 1)[-1]).strip('_') for t in own)       # (the part of the name after the suit's: 'body_c.texture', 'trim_n.texture' ...)
        pref = any(w in names for w in ('rubber', 'suit', 'body', 'torso', 'main', 'vest', 'upper', 'arms_legs'))
        main = not _accessory(names)                              # (the whole model goes on this one material: a main cloth / body material, not a lens, a button or the webshooters)
        out.append((tier, main, pref, r['triangles'], r['slot']))
    return sorted(out, reverse=True)


def pick_single_texture_slot(rows, suit):
    """The slot whose colour texture to replace: it re-skins that part without touching anything shared with other characters. Prefers the plain 'colour + normal + gloss' kind, then a name with
    'rubber' / 'suit' / 'body', then the most triangles; suits that have no plain material fall back to their most-used material that has its own colour texture. -> slot number or None"""
    c = slot_choices(rows, suit); return c[0][-1] if c else None


def colour_texture(rows, slot):
    """path of the slot's colour (_c) texture, or None"""
    r = next((x for x in rows if x['slot'] == slot), None)
    return None if r is None else next((t for t in r['textures'] if t.lower().endswith('_c.texture')), None)
