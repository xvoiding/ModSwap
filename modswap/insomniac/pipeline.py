"""Everything between 'a user's model' and 'the assets to put in the game' for one Spider-Man suit. Used by the command line and by the app."""
from . import swap as S, materials as MT, texture as TX

NEUTRAL = {'n': (127, 127, 0, 255), 'g': (36, 56, 255, 255)}       # flat normal map, neutral gloss map (the values the real rubber textures average to)


def textures_for(toc, ad, rows, slot, atlas):
    """-> [(texture path, new asset bytes)] for the slot's colour / normal / gloss textures: your picture, a flat normal map, a neutral gloss map"""
    r = next(x for x in rows if x['slot'] == slot); out = []
    for role in 'cng':
        path = next((t for t in r['textures'] if t.lower().endswith('_%s.texture' % role)), None)
        if path is None: continue
        i = toc.find(path)
        if i is None: raise ValueError('this game has no texture %s' % path)
        tpl = TX.Texture(toc.read(i, ad))
        out.append((path, TX.write_like(tpl, atlas) if role == 'c' else TX.flat(tpl, NEUTRAL[role])))
    return out


def make_assets(toc, ad, suit_path, orig, rows, slot, fitted, textures=True, flip_v=False, log=print):
    """-> [(path, bytes)]: the new suit model first, then its textures"""
    asset, atlas = S.build(orig, fitted, slot, uv_flip_v=flip_v, log=log)
    items = [(suit_path, asset)]
    if textures:
        items += textures_for(toc, ad, rows, slot, atlas)
        log('textures: colour %dx%d (BC7) + flat normal + neutral gloss' % (atlas.shape[1], atlas.shape[0]))
    return items, atlas
