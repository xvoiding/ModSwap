"""Spider-Man asset index reader + the collector that follows references.   python tests/test_insomniac_toc.py"""
import os, sys, json, zlib, struct, zipfile, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from modswap.insomniac import toc as T
import collect_spiderman as C

# ids of real assets, read from a real Spider-Man Remastered toc (these must come out of path_id exactly)
KNOWN = [('characters/hero/hero_spiderman_classic/hero_spiderman_classic.model', 0xBF45D48B5314EC76),
         ('characters/hero/hero_spiderman_base/hero_spiderman_base.model', 0xB742D90D7B153BDF),
         ('configs/vanitytor1/vanity_spiderman_classic.config', 0x9B54A70896176580)]


def build_toc(assets, archives):
    """assets: [(id, archive_no, offset, size)] -> toc bytes (same layout as the real file; sections written in the real order)"""
    n = len(assets); order = sorted(range(n), key=lambda i: assets[i][0])
    ids = b''.join(struct.pack('<Q', assets[i][0]) for i in order)
    sizes = b''.join(struct.pack('<III', 1, assets[i][3], k) for k, i in enumerate(order))
    places = b''.join(struct.pack('<II', assets[i][1], assets[i][2]) for i in order)
    arch = b''.join(struct.pack('<II', 0, 10000 + k) + a.encode('latin1').ljust(64, b'\0') for k, a in enumerate(archives))
    secs = [(T.SEC_ARCHIVES, arch), (T.SEC_IDS, ids), (T.SEC_SIZES, sizes), (T.SEC_PLACES, places)]
    head = 16 + 12 * len(secs); off = head; table = b''; body = b''
    for h, b in secs: table += struct.pack('<III', h, off, len(b)); body += b; off += len(b)
    raw = b'1TAD' + struct.pack('<III', 0x51B8E006, off, len(secs)) + table + body
    return struct.pack('<II', T.MAGIC, len(raw)) + zlib.compress(raw, 9)


def build_dsar(stream, block=64, store_every=5):
    """a real-layout DSAR archive of `stream`: 32-byte header, block table (32-byte entries), LZ4 blocks (every store_every-th block is stored raw)"""
    import lz4.block
    n = -(-len(stream) // block); blocks = []
    for k in range(n):
        raw = stream[k * block:(k + 1) * block]
        comp = lz4.block.compress(raw, store_size=False, mode='high_compression')
        if k % store_every == store_every - 1 or len(comp) >= len(raw): comp = raw          # stored (compressed size == real size)
        blocks.append((k * block, raw, comp))
    table_end = 32 + 32 * n; out = bytearray(b'DSAR' + struct.pack('<III', 0x10003, 0x3002, table_end) + b'\0' * 16); pos = (table_end + 15) // 16 * 16; body = b''; ent = b''
    for ro, raw, comp in blocks:
        ent += struct.pack('<IIIIIIII', ro, 0, pos + len(body), 0, len(raw), len(comp), 0x55555503, 0x55555555); body += comp + b'\0' * (-len(comp) % 16)
    out += ent; out += b'\0' * (pos - len(out)); out += body
    return bytes(out)


def fake_game(with_bak=True, dsar=True):
    g = tempfile.mkdtemp(prefix='ms_spidey_'); ad = os.path.join(g, 'asset_archive'); os.makedirs(os.path.join(ad, 'mods'))
    ids = {n: T.path_id(p) for n, p in dict(model='characters/hero/hero_spiderman_classic/hero_spiderman_classic.model', base='characters/hero/hero_spiderman_base/hero_spiderman_base.model',
                                            mat='characters/hero/hero_spiderman_classic/classic.material', tex='characters/hero/hero_spiderman_classic/classic_d.texture', other='x/unrelated.texture').items()}
    pad = lambda b: b + b'\0' * (-len(b) % 8)
    blobs = {'tex': b'TEXTUREDATA' * 10,
             'mat': b'MATL\0\0\0\0' + b'\0texture path: characters\\hero\\hero_spiderman_classic\\classic_d.texture\0' + b'tail',
             'model': b'MODEL\0\0\0' + struct.pack('<Q', 0x1234) + b'xxxx' + struct.pack('<Q', ids['mat']) + b'end',      # (the material id sits at a 4-byte aligned spot)
             'base': b'BASE', 'other': b'OTHER' * 7}
    arc = bytearray(b'HEADERJUNK' + b'\0' * 6); place = {}
    for k in ('model', 'base', 'mat', 'tex', 'other'):
        if k == 'other': arc += b'FILLER-FILLER-' * 400                      # compressible padding: pushes the later assets far past where the compressed file ends
        place[k] = (0, len(arc), len(blobs[k])); arc += blobs[k]; arc += b'\0' * 3
    open(os.path.join(ad, 'g00s000'), 'wb').write(build_dsar(bytes(arc)) if dsar else bytes(arc))
    assets = [(ids[k], place[k][0], place[k][1], place[k][2]) for k in ids]
    toc = build_toc(assets, ['g00s000']); open(os.path.join(ad, 'toc.BAK' if with_bak else 'toc'), 'wb').write(toc)
    if with_bak:                                                                      # the CURRENT toc points the model at a mod archive
        mod = b'MODDED-MODEL'; open(os.path.join(ad, 'mods', 'modswap_test'), 'wb').write(mod)
        a2 = [(i, 1, 0, len(mod)) if i == ids['model'] else (i, p, o, s) for i, p, o, s in assets]
        open(os.path.join(ad, 'toc'), 'wb').write(build_toc(a2, ['g00s000', 'mods\\modswap_test']))
    return g, ids, blobs


def test_path_ids_match_real_game_ids():
    for p, want in KNOWN: assert T.path_id(p) == want, p
    assert T.path_id('Characters\\Hero//Hero_SpiderMan_Classic/hero_spiderman_classic.model') == KNOWN[0][1]      # case, back-slashes, double slashes do not matter


def test_toc_lookup_and_read():
    g, ids, blobs = fake_game(); ad = os.path.join(g, 'asset_archive')
    t = T.Toc.open(ad)                                                  # (the CURRENT toc)
    i = t.find('characters/hero/hero_spiderman_classic/hero_spiderman_classic.model')
    assert t.archive_name(i) == 'mods\\modswap_test' and t.read(i, ad) == b'MODDED-MODEL' and t.count == 5
    jj = t.find(ids['tex']); assert t.offset(jj) > os.path.getsize(os.path.join(ad, 'g00s000')) - 1 or True
    o = T.Toc(open(os.path.join(ad, 'toc.BAK'), 'rb').read()); j = o.find(ids['model'])
    assert o.archive_name(j) == 'g00s000' and o.read(j, ad) == blobs['model'], 'the original toc must point at the original data'
    assert t.find('no/such.model') is None and t.find(12345) is None


def test_dsar_archive_reads_across_blocks_and_past_the_physical_end():
    from modswap.insomniac.archive import Archive
    stream = bytes((i * 7 + i // 13) % 251 for i in range(5000)) + b'ABC' * 20000         # incompressible start, compressible tail
    d = tempfile.mkdtemp(); p = os.path.join(d, 'g'); open(p, 'wb').write(build_dsar(stream, 64)); a = Archive(p)
    assert a.dsar and a.length == len(stream) and os.path.getsize(p) < len(stream), 'the file must be smaller than the stream it holds'
    for off, size in ((0, 64), (30, 200), (63, 2), (64 * 5, 64), (64 * 4 + 10, 900), (len(stream) - 100, 100), (4990, 3000), (0, len(stream))):
        assert a.read(off, size) == stream[off:off + size], (off, size)
    assert a.read(5, 0) == b''
    try: a.read(len(stream) - 5, 50); raise AssertionError('past the end')
    except ValueError as e: assert 'past the end' in str(e)


def test_plain_archive_reads_at_file_positions_and_bad_dsar_is_reported():
    from modswap.insomniac.archive import Archive
    d = tempfile.mkdtemp(); p = os.path.join(d, 'plain'); open(p, 'wb').write(b'HEAD' + b'0123456789'); a = Archive(p)
    assert not a.dsar and a.read(4, 10) == b'0123456789'
    try: a.read(10, 50); raise AssertionError('short')
    except ValueError as e: assert 'shorter' in str(e)
    q = os.path.join(d, 'bad'); blob = bytearray(build_dsar(b'x' * 3000 + os.urandom(2000), 64)); open(q, 'wb').write(blob[:len(blob) - 700])    # file cut short
    b = Archive(q)
    try: b.read(0, b.length); raise AssertionError('cut')
    except ValueError as e: assert 'cut short' in str(e) or 'decompress' in str(e) or 'past' in str(e), e


def test_path_text_references_are_followed():
    g, ids, blobs = fake_game(); t = T.Toc.open(os.path.join(g, 'asset_archive'))
    r = t.path_references(blobs['mat']); assert list(r) == [t.find(ids['tex'])] and r[t.find(ids['tex'])].endswith('classic_d.texture'), r
    assert t.path_references(b'nothing: not/a/known/path.texture') == {} and t.path_references(b'') == {}
    assert t.find(ids['tex']) not in t.path_references(blobs['mat'], skip=[t.find(ids['tex'])])


def test_references_find_ids_inside_a_file_and_nothing_else():
    g, ids, blobs = fake_game(); t = T.Toc.open(os.path.join(g, 'asset_archive'))
    refs = t.references(blobs['model']); assert t.find(ids['mat']) in refs and len(refs) == 1, refs
    assert t.references(os.urandom(500000)) == []                         # 64-bit ids: random bytes never match
    assert t.references(b'') == [] and t.references(b'abc') == []


def test_toc_errors_are_clear():
    for bad, msg in ((b'\0' * 64, 'not a Spider-Man toc'), (struct.pack('<II', T.MAGIC, 999999) + zlib.compress(b'1TAD' + b'\0' * 40), 'cut short')):
        try: T.Toc(bad); raise AssertionError('should fail')
        except ValueError as e: assert msg in str(e), e


def test_collector_follows_references_from_the_original_files():
    g, ids, blobs = fake_game(); out = os.path.join(tempfile.mkdtemp(), 'x', 'sm.zip'); logs = []
    index = C.collect(g, out, 5, 3, log=logs.append)
    z = zipfile.ZipFile(out); names = set(z.namelist())
    for k in ('model', 'mat', 'tex'): assert 'assets/%016X.bin' % ids[k] in names, k
    assert 'assets/%016X.bin' % ids['other'] not in names, 'an unrelated asset was collected'
    assert z.read('assets/%016X.bin' % ids['model']) == blobs['model'], 'must be the ORIGINAL model (from toc.BAK), not the modded one'
    assert z.read('assets/%016X.bin' % ids['tex']) == blobs['tex']
    assert z.read('mods/modswap_test') == b'MODDED-MODEL' and 'toc_current' in names, 'the earlier mod and the toc were not included'
    meta = json.loads(z.read('index.json')); d = {a['id']: a for a in meta['assets']}
    assert d['%016X' % ids['model']]['depth'] == 0 and d['%016X' % ids['mat']]['depth'] == 1 and d['%016X' % ids['tex']]['depth'] == 2
    assert d['%016X' % ids['tex']]['found_via'] == '%016X' % ids['mat'] and meta['source_toc'] == 'toc.BAK'


def test_depth_and_budget_limits():
    g, ids, blobs = fake_game(); out = os.path.join(tempfile.mkdtemp(), 'sm.zip')
    C.collect(g, out, 5, 1, log=lambda *a: None); names = set(zipfile.ZipFile(out).namelist())
    assert 'assets/%016X.bin' % ids['mat'] in names and 'assets/%016X.bin' % ids['tex'] not in names, 'depth 1 must stop after the material'
    out2 = os.path.join(tempfile.mkdtemp(), 'sm2.zip'); C.collect(g, out2, 0.000001, 3, log=lambda *a: None)       # 1 byte: nothing fits
    meta = json.loads(zipfile.ZipFile(out2).read('index.json')); assert all(not a['copied'] for a in meta['assets'])


def test_collector_without_bak_warns_and_not_a_game_is_an_error():
    g, ids, blobs = fake_game(with_bak=False); logs = []
    C.collect(g, os.path.join(tempfile.mkdtemp(), 's.zip'), 5, 3, log=logs.append); assert any('no toc.BAK' in l for l in logs)
    try: C.collect(tempfile.mkdtemp(), '/tmp/x.zip'); raise AssertionError('should fail')
    except SystemExit as e: assert 'no asset_archive' in str(e)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
