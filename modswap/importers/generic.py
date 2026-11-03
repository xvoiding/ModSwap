"""glTF/GLB/VRM, Collada, PLY, STL, OFF, 3MF through trimesh; everything else (.blend, .3ds, USD, Alembic...) through Blender if it is installed."""
import os, sys, glob, shutil, subprocess, tempfile
import numpy as np

TRIMESH_EXT = {'.glb', '.gltf', '.vrm', '.dae', '.ply', '.stl', '.off', '.3mf', '.obj'}
BLENDER_EXT = {'.blend', '.3ds', '.abc', '.usd', '.usda', '.usdc', '.usdz', '.x3d', '.wrl', '.x', '.fbx', '.dae', '.ma'}


def load_trimesh(path, texture_dir=None):
    import trimesh
    from PIL import Image
    ext = os.path.splitext(path)[1].lower()
    scene = trimesh.load(path, force='scene', file_type='glb' if ext == '.vrm' else None)
    P, N, UV, TR, TM, TP = [], [], [], [], [], []; names = []; images = []; mats = []; voff = 0
    for node in list(scene.graph.nodes_geometry):
        T, gname = scene.graph[node]; m = scene.geometry[gname].copy(); m.apply_transform(T)
        if len(m.faces) == 0: continue
        uv = None; img = None; col = None
        vis = m.visual
        if getattr(vis, 'kind', '') == 'texture':
            if getattr(vis, 'uv', None) is not None: uv = np.array(vis.uv, float)
            mat = vis.material
            for a in ('baseColorTexture', 'image'):
                im = getattr(mat, a, None)
                if im is not None: img = im.convert('RGB'); break
            if img is None and getattr(mat, 'baseColorFactor', None) is not None:
                col = tuple(int(x) for x in np.array(mat.baseColorFactor)[:3])
        elif getattr(vis, 'kind', '') in ('vertex', 'face'):
            try: col = tuple(int(x) for x in np.array(m.visual.to_color().vertex_colors)[:, :3].mean(0))
            except Exception: pass
        if uv is None: uv = np.zeros((len(m.vertices), 2))
        uv = uv.copy(); uv[:, 1] = 1.0 - uv[:, 1]
        if img is None and col is not None: img = Image.new('RGB', (64, 64), col)
        try: vn = np.array(m.vertex_normals, float)          # normals stored in the file (computing them needs scipy: skip, we smooth ourselves)
        except Exception: vn = None
        P.append(np.array(m.vertices, float)); N.append(vn); UV.append(uv)
        TR.append(np.array(m.faces, np.int64) + voff); voff += len(m.vertices)
        TM.append(np.full(len(m.faces), len(mats))); TP.append(np.full(len(m.faces), len(names)))
        mats.append(str(getattr(getattr(vis, 'material', None), 'name', None) or node)); images.append(img); names.append(str(node))
    if not P: raise ValueError('no mesh found in this file')
    return dict(pos=np.concatenate(P), nrm=np.concatenate(N) if all(n is not None for n in N) else None, uv=np.concatenate(UV), tris=np.concatenate(TR).astype(np.int32),
                tri_mat=np.concatenate(TM).astype(np.int32), tri_part=np.concatenate(TP).astype(np.int32), part_names=names,
                images=images, mat_names=mats, up='+Z' if os.path.splitext(path)[1].lower() in ('.ply', '.stl', '.off', '.3mf') else '+Y',
                per_corner=False)


def find_blender():
    cands = [os.environ.get('MODSWAP_BLENDER'), shutil.which('blender')]
    for root in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)'), '/Applications', '/usr/bin', '/opt'):
        if not root: continue
        cands += sorted(glob.glob(os.path.join(root, 'Blender Foundation', 'Blender*', 'blender.exe')), reverse=True)
        cands += sorted(glob.glob(os.path.join(root, 'Steam', 'steamapps', 'common', 'Blender', 'blender.exe')))
        cands += glob.glob(os.path.join(root, 'Blender.app', 'Contents', 'MacOS', 'Blender'))
    return next((c for c in cands if c and os.path.isfile(c)), None)


_SCRIPT = r'''
import bpy, sys, os
src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
ext = os.path.splitext(src)[1].lower()
if ext == '.blend': bpy.ops.wm.open_mainfile(filepath=src)
elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=src)
elif ext == '.dae': bpy.ops.wm.collada_import(filepath=src)
elif ext == '.3ds':
    try: bpy.ops.import_scene.autodesk_3ds(filepath=src)
    except Exception: bpy.ops.wm.import_3ds(filepath=src) if hasattr(bpy.ops.wm, 'import_3ds') else None
elif ext in ('.usd', '.usda', '.usdc', '.usdz'): bpy.ops.wm.usd_import(filepath=src)
elif ext == '.abc': bpy.ops.wm.alembic_import(filepath=src)
elif ext in ('.x3d', '.wrl'): bpy.ops.import_scene.x3d(filepath=src)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_image_format='AUTO')
'''


def load_via_blender(path, texture_dir=None):
    exe = find_blender()
    if not exe:
        raise RuntimeError('%s files need Blender installed (free, blender.org). Install it, or export your model as FBX / glTF / OBJ.' % os.path.splitext(path)[1])
    tmp = tempfile.mkdtemp(prefix='modswap_blender_'); out = os.path.join(tmp, 'converted.glb'); scr = os.path.join(tmp, 'conv.py')
    open(scr, 'w').write(_SCRIPT)
    r = subprocess.run([exe, '-b', '--factory-startup', '--python', scr, '--', os.path.abspath(path), out], capture_output=True, text=True, timeout=600)
    if not os.path.exists(out): raise RuntimeError('Blender could not convert %s:\n%s' % (os.path.basename(path), (r.stderr or r.stdout)[-600:]))
    try: return load_trimesh(out)
    finally: shutil.rmtree(tmp, ignore_errors=True)
