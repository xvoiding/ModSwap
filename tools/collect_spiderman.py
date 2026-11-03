"""Collect Spider-Man Remastered's suit models and everything they point to, plus the earlier ModSwap test mod, into one zip.

    runtime\\python.exe tools\\collect_spiderman.py "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Marvel's Spider-Man Remastered" samples\\spiderman_assets.zip

It READS the game only. It uses asset_archive\\toc.BAK (the original index) when it exists, so the assets come out in their ORIGINAL form even though a
mod is installed, starts from the suit models, then follows every asset id found inside each file (materials, textures, ...) a few levels deep.
The zip holds assets/<id>.bin for every asset reached, index.json (id, size, where it came from, which file pointed at it), and the
earlier mod's archive (asset_archive\\mods\\*) and toc.
"""
import os, sys, json, zipfile, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modswap.insomniac.toc import Toc, path_id

SEEDS = ['characters/hero/hero_spiderman_classic/hero_spiderman_classic.model', 'characters/hero/hero_spiderman_base/hero_spiderman_base.model']
MAX_ASSET = 48 * 1024 * 1024        # bigger assets are listed in index.json but not copied
MAX_SCAN = 24 * 1024 * 1024         # bigger ones are copied but not searched for references (big textures do not point at anything)


def collect(game, out_zip, budget_mb=150, depth=3, log=print):
    ad = os.path.join(game, 'asset_archive')
    if not os.path.isdir(ad): raise SystemExit('no asset_archive folder in ' + game)
    bak = os.path.join(ad, 'toc.BAK'); src = bak if os.path.isfile(bak) else os.path.join(ad, 'toc')
    log('reading the index: %s%s' % (src, '' if src == bak else '  (no toc.BAK: a mod may already be installed, the assets may be modified)'))
    toc = Toc.open(src); budget = int(budget_mb * 1024 * 1024); used = 0
    seen = {}; queue = []; index = []; known_paths = {}
    for p in SEEDS:
        i = toc.find(p)
        if i is None: log('  not in this game: ' + p); continue
        seen[i] = 0; queue.append((i, 0, p)); known_paths[i] = p; log('  start: %s' % p)
    os.makedirs(os.path.dirname(os.path.abspath(out_zip)), exist_ok=True)
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as z:
        k = 0
        while k < len(queue):
            i, d, why = queue[k]; k += 1
            rec = dict(id='%016X' % int(toc.ids[i]), path=known_paths.get(i), asset=i, size=toc.size(i), archive=toc.archive_name(i), offset=toc.offset(i), depth=d, found_via=why if isinstance(why, str) else None, copied=False)
            index.append(rec)
            if toc.size(i) > MAX_ASSET or used + toc.size(i) > budget: rec['note'] = 'not copied (size/budget)'; continue
            try: data = toc.read(i, ad)
            except (OSError, ValueError) as e: rec['note'] = 'unreadable: %s' % e; continue
            z.writestr('assets/%s.bin' % rec['id'], data); used += len(data); rec['copied'] = True
            if d < depth and len(data) <= MAX_SCAN:
                for j in toc.references(data, skip=seen):
                    seen[j] = d + 1; queue.append((j, d + 1, '%s' % rec['id']))
                for j, path in toc.path_references(data, skip=seen).items():            # materials name their textures by path text
                    seen[j] = d + 1; queue.append((j, d + 1, '%s' % rec['id'])); known_paths[j] = path
            if k % 25 == 0: log('  %d assets, %.1f MB so far' % (k, used / 1e6))
        z.writestr('index.json', json.dumps(dict(archives=toc.archives, source_toc=os.path.basename(src), assets=index), indent=1))
        # the earlier ModSwap mod and the toc it patched
        mods = os.path.join(ad, 'mods')
        if os.path.isdir(mods):
            for f in sorted(os.listdir(mods)):
                p = os.path.join(mods, f)
                if os.path.isfile(p) and os.path.getsize(p) <= 120 * 1024 * 1024: z.write(p, 'mods/' + f); log('  included the earlier mod file: mods/%s (%.1f MB)' % (f, os.path.getsize(p) / 1e6))
        cur = os.path.join(ad, 'toc')
        if os.path.isfile(cur): z.write(cur, 'toc_current')
    by = {}
    for r in index: by[r['depth']] = by.get(r['depth'], 0) + 1
    log('zip written: %s | %d assets reached %s | %d copied, %.1f MB of assets | %.1f MB zip' % (out_zip, len(index), dict(sorted(by.items())), sum(r['copied'] for r in index), used / 1e6, os.path.getsize(out_zip) / 1e6))
    return index


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_folder'); ap.add_argument('out_zip'); ap.add_argument('--budget', type=float, default=150, help='max MB of assets to copy (default 150)')
    ap.add_argument('--depth', type=int, default=3, help='how many levels of references to follow (default 3)')
    a = ap.parse_args(); collect(a.game_folder, a.out_zip, a.budget, a.depth)
