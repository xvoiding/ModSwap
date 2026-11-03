"""Fit a user's model onto a Spider-Man .model: auto-rig it to the suit's skeleton, atlas its textures, split it into mesh parts the format can hold, and write the new asset.

    fitted = fit(orig_model, user_model, ...)          # geometry + skin in Spider-Man's frame
    asset, atlas_rgb = build(orig_model, fitted)       # new .model bytes + the texture picture the model's uvs point into
"""
import numpy as np
from .. import skin, atlas, edit
from . import model as M, rig as R

MAX_PART_VERTS = 60000          # a part's indices are 16-bit, so at most 65,535 vertices


def split_parts(pos, nrm, uv, tris, skins, limit=None):
    """cut a mesh into parts of at most `limit` vertices. Triangles are taken in order; a vertex shared by two parts is duplicated. -> list of part dicts (without material)"""
    limit = MAX_PART_VERTS if limit is None else limit
    parts = []; cur = None
    def new():
        return dict(map={}, v=[], t=[])
    cur = new()
    def close(c):
        if not c['t']: return
        v = np.array(c['v'], np.int64)
        parts.append(dict(pos=pos[v], nrm=nrm[v], uv=uv[v], tris=np.array(c['t'], np.int64), skin=[skins[i] for i in v]))
    for t in tris:
        need = sum(1 for x in t if x not in cur['map'])
        if len(cur['v']) + need > limit: close(cur); cur = new()
        loc = []
        for x in t:
            if x not in cur['map']: cur['map'][x] = len(cur['v']); cur['v'].append(int(x))
            loc.append(cur['map'][x])
        cur['t'].append(loc)
    close(cur)
    return parts


def skins_from_autorig(skin_i, skin_w):
    out = []
    for bi, bw in zip(skin_i, skin_w):
        lst = [(int(b), float(w)) for b, w in zip(bi, bw) if w > 1e-4]
        out.append(lst or [(int(bi[0]), 1.0)])
    return out


def fit(orig, user, up='+Y', forward=None, scale=1.0, adjust=None, edits=None, lod0_meshes=23, atlas_size=2048, log=print):
    """-> dict(pos, nrm, uv, tris, skin, atlas (H,W,3) uint8, info) all in Spider-Man's frame (metres, y up, +z forward), ready for build()"""
    meshes = orig.meshes(); st = orig.streams()
    ref = np.concatenate([st['pos'][m.vertex_start:m.vertex_start + m.vertex_count] for m in meshes[:lod0_meshes] if m.vertex_count])
    rg = R.rig_from_model(orig, ref)
    r = skin.autorig(user.pos, user.nrm, rg, up=up, forward=forward, scale_mult=scale, adjust=adjust, edits=edits, tris=user.tris)
    log('auto-rig: scale %.3f, facing %s' % (r['info']['scale'], r['info']['forward']))
    pos = R.to_model_space(r['pos']); nrm = R.to_model_space(r['nrm'])
    tris = edit.keep_triangles(user.tris, r['hidden']).copy()
    tris = tris[:, [0, 2, 1]]                                   # y/z swap mirrors the model: keep the triangles facing outwards
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    if np.sign((fn * nrm[tris].sum(1)).sum(1)).mean() < 0: tris = tris[:, [0, 2, 1]]
    images = [im if im is not None else None for im in user.images]
    from PIL import Image
    images = [im if im is not None else Image.new('RGB', (64, 64), (160, 160, 160)) for im in images]
    atl, cells = atlas.pack(images, user.uv, user.vert_mat, size=atlas_size)
    uv = atlas.remap_uv(user.uv, user.vert_mat, cells, atlas_size)
    return dict(pos=pos, nrm=nrm, uv=uv, tris=tris, skin=skins_from_autorig(r['skin_i'], r['skin_w']), atlas=atl, info=r['info'])


def build(orig, fitted, material, uv_flip_v=False, log=print):
    """-> (new asset bytes, atlas picture). `material` = the mesh-table material slot all parts use (its texture is the one to replace)."""
    uv = fitted['uv'].copy()
    if uv_flip_v: uv[:, 1] = 1.0 - uv[:, 1]
    parts = split_parts(fitted['pos'], fitted['nrm'], uv, fitted['tris'], fitted['skin'])
    slots = len(orig.meshes())
    if len(parts) > slots: raise ValueError('this model needs %d mesh parts but the suit has room for %d; simplify it' % (len(parts), slots))
    for p in parts: p['material'] = int(material)
    log('writing %d mesh part(s): %d vertices, %d triangles' % (len(parts), sum(len(p['pos']) for p in parts), sum(len(p['tris']) for p in parts)))
    return M.build_model(orig, parts), fitted['atlas']
