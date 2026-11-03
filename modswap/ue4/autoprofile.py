"""Work out a swap profile for a game's character on its own:
  * which meshes in the skeleton family are the *body* (swap) and which are layered *parts* (hide)
  * which textures the body's material uses, what each one is (colour / normal / packed mask) and its pixel format
  * the character's real height (from the head and leg pieces) so the new model is scaled correctly.
"""
import os, re
from .uepkg import parse_uasset
from .tex import parse_tex

PART = re.compile(r'(head|face|top|bottom|hair|hat|cap|mask|glove|shoe|boot|accessor|jacket|shirt|pant|beard|helmet|cloth|upper|lower|vest|cape|glass|wig|scarf|tie|belt|bag|backpack|wing|tail|(?<![a-z])(tongue|mustache|moustache|teeth|tooth|eyes?|lash(es)?|brows?)(?![a-z]))', re.I)
PLACEHOLDER_TEX = re.compile(r'(neutral|white|black|default|flat|clouds|noise|dummy|blank|grey|gray|checker)', re.I)

ROLES = [   # (regex on texture name suffix, role, flat colour for packed maps)
    (r'(_|^)(BC|BaseColor|Base_Color|Albedo|Diffuse|Diff|Color|Col|D|C|Tex)(_\w+)?$', 'diffuse', None),
    (r'(_|^)(N|Normal|NRM|NM|Norm)(_\w+)?$', 'normal', None),
    (r'(_|^)(MTRAO|MRAO|MRA)(_\w+)?$', 'flat', [0, 128, 255, 255]),
    (r'(_|^)(ORM|ARM|ORMH|OcclusionRoughnessMetallic)(_\w+)?$', 'flat', [255, 128, 0, 255]),
    (r'(_|^)(RMA)(_\w+)?$', 'flat', [128, 0, 255, 255]),
    (r'(_|^)(E|Emissive|Emission|Glow)(_\w+)?$', 'flat', [0, 0, 0, 255]),
    (r'(_|^)(O|Opacity|Alpha|A)(_\w+)?$', 'flat', [255, 255, 255, 255]),
    (r'(_|^)(M|Mask|Masks|R|Roughness|AO|Metallic|S|Spec|Specular)(_\w+)?$', 'flat', [0, 0, 0, 255]),
]
PF = {'PF_DXT1': 'bc1', 'PF_DXT5': 'bc3', 'PF_BC5': 'bc5'}


def gender(name):
    n = '_' + name.lower() + '_'
    if '_female_' in n or '_woman_' in n or '_girl_' in n: return 'f'
    if '_male_' in n or '_man_' in n or '_boy_' in n: return 'm'
    return ''


CODED = re.compile(r'^SK_\d{4}(?:_\d{2})+_([A-Za-z]+(?:_[A-Za-z]+)?)(?:_?\d+)*$')        # SK_0350_00_00_BDY_00, SK_0350_00_BASE, SK_0350_00_00_P_SKN_00


def part_code(name):
    """'SK_0350_00_00_BDY_00' -> 'BDY' (three-letter part codes some games use instead of words like Head / Body), else ''"""
    m = CODED.match(name); return m.group(1).upper() if m else ''


def suggest_plan(assets):
    """assets: Asset list of one skeleton family -> dict(targets=[paths], hide=[paths], keep=[paths])"""
    targets, hide, keep = [], [], []
    live = [a for a in assets if getattr(a, 'role', '') != 'piece']
    if live and all(part_code(a.name) for a in live) and any(part_code(a.name) == 'BDY' for a in live):
        for a in assets:                                        # coded names: BDY is the whole body, every other code is a layer on top of it
            c = part_code(a.name)
            if getattr(a, 'role', '') == 'piece': keep.append(a.path)
            elif c == 'BDY': targets.append(a.path)
            else: hide.append(a.path)
        return dict(targets=targets, hide=hide, keep=keep)
    for a in assets:
        if getattr(a, 'role', '') == 'piece': keep.append(a.path)            # dismember / broken-part pieces: left alone
        elif 'preview' in a.name.lower(): keep.append(a.path)
        elif PART.search(a.name + ' ' + a.folder): hide.append(a.path)
        else: targets.append(a.path)
    if not targets and assets:                     # nothing looked like a plain body: take the first mesh, leave the rest
        first = next((a for a in assets if a.path not in keep), assets[0]); targets = [first.path]; hide = [h for h in hide if h != first.path]
    return dict(targets=targets, hide=hide, keep=keep)


def _names(d):
    N = d['names']; return (lambda x: N[x[0]] if isinstance(x, tuple) else x)


def import_packages(ua_bytes, wanted_classes):
    """[(object name, '/Game/package/path')] for imports of the given classes."""
    d = parse_uasset(ua_bytes); s = _names(d); out = []
    for im in d['imports']:
        if s(im['class_name']) in wanted_classes:
            o = im['outer']
            pk = s(d['imports'][-o - 1]['name']) if o < 0 and -o - 1 < len(d['imports']) else ''
            out.append((s(im['name']), pk))
    return out


def game_path_to_rel(pkg, content_prefix):
    """'/Game/Characters/NPC/x' -> 'Goat2/Content/Characters/NPC/x' (content_prefix = 'Goat2/Content')."""
    return content_prefix + '/' + pkg[len('/Game/'):] if pkg.startswith('/Game/') else None


def classify_texture(name):
    for pat, role, color in ROLES:
        if re.search(pat, name, re.I): return role, color
    return None, None


def body_textures(orig, mesh_rel, content_prefix, extract, log=print, strict=False):
    """Textures to override for one body mesh. `extract(list_of_rel_bases)` must make the files exist under `orig`.
    strict: only textures that live next to the character's own files (SS/Characters/0350/...), never the game's shared ones."""
    ua = open(os.path.join(orig, mesh_rel + '.uasset'), 'rb').read()
    mats = import_packages(ua, ('MaterialInstanceConstant', 'Material', 'MaterialInstance'))
    mesh_top = mesh_rel[len(content_prefix) + 1:].split('/')[0]
    mi_rels = [r for r in (game_path_to_rel(p, content_prefix) for _, p in mats if p) if r]        # materials from /Engine/ etc. aren't in the game's own pak
    extract(mi_rels, exts=('.uasset', '.uexp'))
    seen, tex = set(), []
    for mi in mi_rels:
        f = os.path.join(orig, mi + '.uasset')
        if not os.path.exists(f): continue
        for name, pkg in import_packages(open(f, 'rb').read(), ('Texture2D',)):
            rel = game_path_to_rel(pkg, content_prefix)
            if not rel or rel in seen: continue
            if PLACEHOLDER_TEX.search(name): continue
            if pkg[len('/Game/'):].split('/')[0] != mesh_top and tex: pass
            seen.add(rel); tex.append((name, rel, pkg))
    if strict:
        mesh_dirs = mesh_rel[len(content_prefix) + 1:].split('/')[:-1]; k = min(3, len(mesh_dirs))
        own = [t for t in tex if t[2][len('/Game/'):].split('/')[:-1][:k] == mesh_dirs[:k]]
        if not own and tex: log('  the body material only uses shared textures (%d), so no texture is replaced' % len(tex))
    else: own = [t for t in tex if t[2][len('/Game/'):].split('/')[0] == mesh_top] or tex        # prefer the character's own folder over shared ones
    extract([t[1] for t in own], exts=('.uasset', '.uexp', '.ubulk'))
    out = []
    for name, rel, pkg in own:
        role, color = classify_texture(name)
        try: fmt = PF.get(parse_tex(os.path.join(orig, rel))['fmt'])
        except Exception as e: log('  cannot read texture %s: %r' % (name, e)); continue
        if role is None or fmt is None:
            log('  skipping texture %s (role=%s format=%s)' % (name, role, fmt)); continue
        e = dict(path=rel, format=fmt, role=role, size=2048 if role == 'diffuse' else 256)
        if role == 'flat': e['color'] = color
        out.append(e)
    return out


def make_profile(game_name, content_prefix, sk_format, family_assets, plan, orig, extract, log=print):
    """Full v2 profile dict for the swap described by `plan` (from suggest_plan, possibly edited by the user)."""
    family_assets = [a for a in family_assets if getattr(a, 'role', '') != 'piece']
    by_path = {a.path: a for a in family_assets}
    HEAD = re.compile(r'(head|face)', re.I); LOWER = re.compile(r'(bottom|pants|jeans|trouser|leg|shoe|boot|lower|short|skirt)', re.I)
    targets = []
    for tp in plan['targets']:
        a = by_path[tp]; g = gender(a.name)
        sib = [x for x in family_assets if gender(x.name) in (g, '') and x.path != tp and PART.search(x.name + ' ' + x.folder)]
        heads = [x.path for x in sib if HEAD.search(x.name + ' ' + x.folder)][:8]
        lowers = [x.path for x in sib if LOWER.search(x.name + ' ' + x.folder)][:8]
        extract(heads + lowers + [tp], exts=('.uasset', '.uexp'))
        t = dict(name=a.name, mesh=tp, textures=body_textures(orig, tp, content_prefix, extract, log, strict=bool(sk_format.get('ue5'))))
        if heads and lowers: t['ref_top_from'] = heads; t['ref_bottom_from'] = lowers
        targets.append(t)
    return dict(name=game_name, engine='ue4', sk_format=sk_format, pak_version='', mount='../../../', atlas=2048,
                targets=targets, hide=list(plan.get('hide', [])))
