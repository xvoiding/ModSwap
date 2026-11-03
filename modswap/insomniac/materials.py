"""Which material does each mesh part of a Spider-Man .model use, and what does that material look like (shader, textures)?
The model keeps its materials as 16-byte records (u32, 8-byte asset id, u32) right after a table of offsets; mesh part k uses record k. Each record's id is a
material asset in the toc whose text names its shader and textures."""
import re, struct
from . import model as M

TAG_MATERIAL_LIST = 0x3250BB80
_TEXT = re.compile(rb'[\x20-\x7e]{6,}')


def material_ids(model, toc):
    """-> [asset number of the material for slot 0, 1, ...] (empty when the table cannot be found)"""
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
        pref = any(w in ' '.join(own) for w in ('rubber', 'suit', 'body'))
        out.append((tier, pref, r['triangles'], r['slot']))
    return sorted(out, reverse=True)


def pick_single_texture_slot(rows, suit):
    """The slot whose colour texture to replace: it re-skins that part without touching anything shared with other characters. Prefers the plain 'colour + normal + gloss' kind, then a name with
    'rubber' / 'suit' / 'body', then the most triangles; suits that have no plain material fall back to their most-used material that has its own colour texture. -> slot number or None"""
    c = slot_choices(rows, suit); return c[0][3] if c else None


def colour_texture(rows, slot):
    """path of the slot's colour (_c) texture, or None"""
    r = next((x for x in rows if x['slot'] == slot), None)
    return None if r is None else next((t for t in r['textures'] if t.lower().endswith('_c.texture')), None)
