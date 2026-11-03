"""Run a swap profile: turn a model into override files for every target mesh and hide the leftover pieces."""
import os, glob
from .ue4.swap import swap_character, hide_skmesh, JDA_FORMAT
from .ue4.rig import extract_rig, mesh_zrange


def target_rig(prof, orig, t):
    """The skeleton + reference height of one target mesh (height from the layered pieces when the profile lists them)."""
    fmt = prof.get('sk_format', JDA_FORMAT)
    base = os.path.join(orig, t['mesh'])
    h, z0 = t.get('ref_height'), t.get('ref_min_z')
    if t.get('ref_top_from') and t.get('ref_bottom_from'):      # median head-top / foot-bottom of the layered pieces (robust to odd hats)
        tops = sorted(mesh_zrange(os.path.join(orig, r), **fmt)[1] for r in t['ref_top_from'])
        bots = sorted(mesh_zrange(os.path.join(orig, r), **fmt)[0] for r in t['ref_bottom_from'])
        z0 = bots[len(bots) // 2]; h = tops[len(tops) // 2] - z0
    elif t.get('ref_from'):          # character height = span of these meshes (e.g. head + legs)
        zs = [mesh_zrange(os.path.join(orig, r), **fmt) for r in t['ref_from']]
        z0 = min(z[0] for z in zs); h = max(z[1] for z in zs) - z0
    return extract_rig(base, ref_height=h, ref_min_z=z0, **fmt)


def run_profile(prof, orig, model, out, up=None, forward=None, scale=1.0, adjust=None, edits=None, log=print):
    """prof: profile dict (see profiles/*.json). orig: folder with the extracted original game files. Returns list of written rel paths."""
    fmt = prof.get('sk_format', JDA_FORMAT)
    targets = prof.get('targets') or [prof]
    written = []
    for t in targets:
        rig = target_rig(prof, orig, t)
        files = swap_character(orig, t['mesh'], t.get('textures', prof.get('textures', [])), model, rig, out,
                               atlas_size=t.get('atlas', prof.get('atlas', 2048)), up=up or getattr(model, 'up', None) or prof.get('up', '+Y'),
                               forward=forward, scale_mult=scale, sk_format=fmt, adjust=adjust, edits=edits, log=log, notes=t.get('texture_notes'))
        written += files; log('swapped ' + t['mesh'])
    skip = {os.path.normpath(t['mesh']) for t in targets}
    hide = list(prof.get('hide', []))
    for pat in prof.get('hide_glob', []):
        for f in sorted(glob.glob(os.path.join(orig, pat + '.uasset'))):
            hide.append(os.path.relpath(f[:-7], orig).replace(os.sep, '/'))
    hidden, failed = 0, []
    for rel in dict.fromkeys(hide):
        if os.path.normpath(rel) in skip: continue
        try: written += hide_skmesh(orig, rel, out, sk_format=fmt); hidden += 1
        except Exception as e: failed.append((rel, repr(e)))
    for rel, err in failed: log('  could not hide %s: %s' % (rel, err))
    log('built %d swapped meshes, hid %d pieces' % (len(targets), hidden))
    return written
