"""Detect how a game's SkeletalMesh packages are laid out (which export is the mesh, UE4.26+ extras) by trial-parsing a sample."""
from .uepkg import parse_uasset
from .skmesh import walk

FOOTER = bytes.fromhex('c1832a9e')


def detect_sk_format(ua, ue):
    """-> dict(exp_idx, rtmask) that parses this mesh cleanly to its footer, or None."""
    d = parse_uasset(ua); N = d['names']
    s = lambda x: N[x[0]] if isinstance(x, tuple) else x
    cand = []
    for i, e in enumerate(d['exports']):
        c = e.get('class', 0)
        if c < 0 and -c - 1 < len(d['imports']) and s(d['imports'][-c - 1]['name']) == 'SkeletalMesh': cand.append(i)
    # stage 1: the two layouts games ModSwap already supports use (clean parse to the footer). stage 2: other cooks, matched strictly.
    stage1 = [(True, None, None), (False, None, None)]
    stage2 = [(True, False, False), (True, False, True), (True, True, False), (False, False, False), (False, True, True), (False, False, True), (False, True, False)]
    stage3 = [(False, None, None, True)]                                                           # UE4.23 cooks (SpongeBob Rehydrated): their own LOD layout
    stage0 = [(True, None, None, False, True)] if d.get('is_ue5') else []                        # UE5 cooks (retoc output, 'unversioned'): own header + large-world-coordinate layout
    for stage, variants in ((0, stage0), (1, stage1), (2, stage2), (3, stage3)):
        best = None
        for idx in cand or range(len(d['exports'])):
            for var in variants:
                rt, adj, tr = var[:3]; v423 = len(var) > 3 and var[3]; u5 = len(var) > 4 and var[4]
                try:
                    o = walk(ue, d, exp_idx=idx, verbose=False, rtmask=rt, all_lods=True, adj=adj, trail=tr, v423=v423, ue5=u5)
                except Exception:
                    continue
                rest = len(ue) - 4 - o['end']
                if ue[-4:] != FOOTER or not 0 <= rest <= 64: continue
                # the real layout ends exactly with [NumInlinedLODs u8][NumNonOptionalLODs u8][int32 0] (UE4.25+); a wrong guess leaves other bytes over
                tail_ok = rest == 6 and ue[o['end']] == ue[o['end'] + 1] == o['nlod'] and ue[o['end'] + 2:o['end'] + 6] == b'\0\0\0\0'
                if v423: tail_ok = rest == 8 and ue[o['end']:o['end'] + 8] == b'\0' * 8
                if stage >= 2 or u5:
                    if not tail_ok: continue
                score = rest
                if best is None or score < best[0]:
                    f = dict(exp_idx=idx, rtmask=rt)
                    if adj is not None: f['adj'] = adj
                    if tr is not None: f['trail'] = tr
                    if v423: f['v423'] = True
                    if u5: f['ue5'] = True
                    best = (score, f)
        if best: return best[1]
    return None


def diagnose_layout(ua, ue, name=''):
    """A plain-text report on why a skeletal mesh could not be read: engine / custom versions, every layout tried and where it stopped,
    and the bytes around the places that matter. Saved next to the cache so a new cook can be added from one file."""
    import traceback
    out = ['ModSwap mesh layout report', 'asset: %s' % name, 'uexp bytes: %d   uasset bytes: %d' % (len(ue), len(ua))]
    try:
        d = parse_uasset(ua)
    except Exception as e:
        return '\n'.join(out + ['uasset would not parse: %r' % (e,)])
    out.append('legacy %s  ue4 file version %s  ue5 %s  licensee %s  saved by %s' % (d.get('legacy'), d.get('ue4'), d.get('ue5'), d.get('lic'), (d.get('saved_ver') or ['?'] * 5)[-1]))
    out.append('package flags 0x%x  exports %d  imports %d  names %d' % (d['pkgflags'], len(d['exports']), len(d['imports']), len(d['names'])))
    out.append('custom versions (%d):' % len(d['custom']))
    for g, v in d['custom']: out.append('   %s = %d' % (g.hex() if isinstance(g, (bytes, bytearray)) else g, v))
    N = d['names']; s = lambda x: N[x[0]] if isinstance(x, tuple) else x
    for i, e in enumerate(d['exports'][:14]):
        c = e.get('class', 0)
        cn = s(d['imports'][-c - 1]['name']) if c < 0 and -c - 1 < len(d['imports']) else str(c)
        out.append('export %d: class %s name %s size %s offset %s' % (i, cn, s(e['name']) if 'name' in e else '?', e.get('size'), e.get('offset')))
    out.append('footer ok: %s   last 48 bytes: %s' % (ue[-4:] == FOOTER, ue[-48:].hex()))
    cand = [i for i, e in enumerate(d['exports']) if e.get('class', 0) < 0 and -e['class'] - 1 < len(d['imports']) and s(d['imports'][-e['class'] - 1]['name']) == 'SkeletalMesh']
    out.append('skeletal mesh exports: %s' % cand)
    for idx in cand or range(len(d['exports'])):
        for rt in (False, True):
            for adj in (None, False, True):
                for tr in (None, False, True):
                    for v423 in (False, True):
                        if v423 and tr: continue
                        tag = 'exp %d rtmask=%s adj=%s trail=%s v423=%s' % (idx, rt, adj, tr, v423)
                        try:
                            o = walk(ue, d, exp_idx=idx, verbose=False, rtmask=rt, all_lods=True, adj=adj, trail=tr, v423=v423)
                            rest = len(ue) - 4 - o['end']
                            out.append('  OK   %s -> end %d, %d bytes left, lods %s%s' % (tag, o['end'], rest, o.get('nlod'), ('  tail ' + ue[o['end']:o['end'] + rest].hex()) if 0 <= rest <= 32 else ''))
                        except Exception as ex:
                            tb = traceback.extract_tb(ex.__traceback__)[-1]
                            out.append('  fail %s -> %s: %s (%s:%d)' % (tag, type(ex).__name__, str(ex)[:80], tb.filename.split('/')[-1], tb.lineno))
    return '\n'.join(out)
