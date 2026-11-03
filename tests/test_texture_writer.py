"""The texture writer must produce a package the game can read back, for every cook convention: separate-file (.ubulk) mips with plain offsets,
with 4.23-style relative offsets, and templates that keep every mip inline.   python tests/test_texture_writer.py"""
import os, sys, io, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image
from fake_ue_tex import make_texture
from ddsutil import dds
from modswap import atlas
from modswap.ue4 import texwrite
from modswap.ue4.tex import parse_tex

CASES = [('bulk', False), ('bulk', True), ('inline', False)]


def picture(n=2048):
    yy, xx = np.mgrid[0:n, 0:n]; a = np.zeros((n, n, 3), np.uint8)
    a[..., 0] = xx * 255 // (n - 1); a[..., 1] = yy * 255 // (n - 1); a[..., 2] = ((xx // 128 + yy // 128) % 2) * 200
    a[:n // 8, :n // 8] = (255, 255, 255)
    return a


def write(mode, rel, kind='bc1', size=2048):
    d = tempfile.mkdtemp(prefix='ms_tex_'); tb = os.path.join(d, 'tmpl', 'T'); ob = os.path.join(d, 'out', 'T')
    make_texture(tb, 256, kind, mode, rel); os.makedirs(os.path.dirname(ob))
    img = picture(size); chain = atlas.compress_chain(img, kind)
    texwrite.build_texture(tb, ob, chain, {}, size=size, first_mip=0)
    return tb, ob, img, chain


def test_written_texture_reads_back_clean_for_every_convention():
    for mode, rel in CASES:
        tb, ob, img, chain = write(mode, rel)
        probs = texwrite.check_texture(ob, chain)
        assert not probs, (mode, rel, probs)


def test_pixels_survive_the_round_trip():
    for mode, rel in CASES:
        tb, ob, img, chain = write(mode, rel)
        o = parse_tex(ob); data = texwrite.mip_payload(ob, o, 0); w, h = o['mips'][0]['sx'], o['mips'][0]['sy']
        out = np.array(Image.open(io.BytesIO(dds(w, h, data, b'DXT1'))).convert('RGB')).astype(int)
        assert (w, h) == (2048, 2048) and np.abs(out - img.astype(int)).mean() < 6, (mode, rel, np.abs(out - img.astype(int)).mean())


def test_inline_template_keeps_every_mip_inline_and_flagged_inline():
    tb, ob, img, chain = write('inline', False)
    o = parse_tex(ob)
    assert all('inline' in m and not m['flags'] & 0x100 for m in o['mips']), 'a mip of an all-inline template ended up in the .ubulk'
    assert os.path.getsize(ob + '.ubulk') == 0


def test_bulk_template_puts_big_mips_in_ubulk_with_separate_file_flag():
    for rel in (False, True):
        tb, ob, img, chain = write('bulk', rel)
        o = parse_tex(ob); big = [m for m in o['mips'] if 'inline' not in m]
        assert len(big) >= 5 and all(m['flags'] & 0x100 for m in big) and os.path.getsize(ob + '.ubulk') == sum(m['count'] for m in big)
        assert (big[0]['off'] == -o['d']['bulk_start']) == rel, 'offset convention of the template was not kept'


def test_checker_catches_a_broken_texture():
    tb, ob, img, chain = write('bulk', False)
    ub = bytearray(open(ob + '.ubulk', 'rb').read()); ub[100] ^= 0xFF; open(ob + '.ubulk', 'wb').write(ub)       # flip a byte in the pixels
    assert texwrite.check_texture(ob, chain), 'a corrupted .ubulk went unnoticed'
    tb, ob, img, chain = write('bulk', False)
    open(ob + '.ubulk', 'ab').write(b'extra')
    assert texwrite.check_texture(ob, chain), 'a wrong-size .ubulk went unnoticed'


def test_bc3_alpha_median_matches_a_real_decoder():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]; rgba = np.zeros((n, n, 4), np.uint8); rgba[..., :3] = 128
    for alpha in (255, 0, 90, 17):
        rgba[..., 3] = alpha
        w, h, data = atlas.compress_chain(rgba, 'bc3')[0]
        dec = np.array(Image.open(io.BytesIO(dds(w, h, data, b'DXT5'))).convert('RGBA'))[..., 3]
        assert abs(texwrite.bc3_alpha_median(data) - int(np.median(dec))) <= 1, (alpha, texwrite.bc3_alpha_median(data), int(np.median(dec)))
    rgba[..., 3] = np.where(xx < 48, 200, 10)                                  # mostly 200
    w, h, data = atlas.compress_chain(rgba, 'bc3')[0]
    dec = np.array(Image.open(io.BytesIO(dds(w, h, data, b'DXT5'))).convert('RGBA'))[..., 3]
    assert abs(texwrite.bc3_alpha_median(data) - int(np.median(dec))) <= 2


def test_bc3_diffuse_keeps_alpha_through_the_writer():
    tb, ob, img, chain = write('bulk', False, kind='bc3')
    assert not texwrite.check_texture(ob, chain)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'passed')
