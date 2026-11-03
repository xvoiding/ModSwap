"""Swapping a Sonic Frontiers character: DDS writer, .pac writer, model slot filling, installer, command line and the app's server functions.
Everything that needs the game's real files is skipped without them (set SONIC_CHARACTER_DIR to image\\x64\\raw\\character).   python tests/test_hedgehog_sonic.py"""
import os, sys, struct, json, time, tempfile, shutil, hashlib, io, contextlib, base64
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
cfg = tempfile.mkdtemp(prefix='ms_cfg_'); os.environ['XDG_CONFIG_HOME'] = cfg; os.environ['APPDATA'] = cfg
from modswap.hedgehog import pacx, pacwrite, innerwrite, dds, hemodel as H, hewrite as W, sonic, needle
from modswap.hedgehog.install import Installer
from humanoid_fixture import humanoid

CHAR_DIR = next((p for p in (os.environ.get('SONIC_CHARACTER_DIR'), '/tmp/s2x/whole/image/x64/raw/character') if p and os.path.isfile(os.path.join(p, 'sonic.pac'))), None)
SKIP = lambda: print('   (no real Sonic files: skipped)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def tiny_dds(kind='DXT1', w=64, h=64, mips=7, dx10=None):
    hdr = bytearray(128); hdr[:4] = b'DDS '; struct.pack_into('<7I', hdr, 4, 124, 0xA1007, h, w, 0, 0, mips); struct.pack_into('<I', hdr, 76, 32); struct.pack_into('<I', hdr, 80, 4)
    hdr[84:88] = (b'DX10' if dx10 else kind.encode()); body = b''
    if dx10: body = struct.pack('<5I', dx10, 3, 0, 1, 0)
    blk = {'DXT1': 8, 'DXT5': 16, 'ATI2': 16}.get(kind, 16)
    n = sum(((max(1, w >> i) + 3) // 4) * ((max(1, h >> i) + 3) // 4) * blk for i in range(mips)); return bytes(hdr) + body + b'\0' * n


# ------------------------------------------------------------------ small pieces (no game files)
def test_dds_same_length_for_every_format_and_exact_flat_colours():
    for kind, dx in (('DXT1', None), ('DXT5', None), ('ATI2', None), ('DX10', 98)):
        t = tiny_dds(kind if kind != 'DX10' else 'DX10', 64, 32, 6, dx); d = dds.Dds(t)
        pic = np.random.default_rng(1).integers(0, 255, (50, 70, 3), dtype=np.uint8)               # a different size: it is resized
        new = dds.write_like(d, pic); assert len(new) == len(t) and new[:d.data_at] == t[:d.data_at], kind
        flat = dds.Dds(dds.flat_like(d, (130, 126, 255, 255))).decode(0); assert abs(int(flat[0, 0, 0]) - 130) <= 2 and abs(int(flat[0, 0, 1]) - 126) <= 2, kind


def test_dds_rejects_wrong_sizes_and_unknown_formats():
    t = tiny_dds('DXT1')
    for bad in (t[:-5], b'NOPE' + t[4:]):
        try: dds.Dds(bad); raise AssertionError('should fail')
        except ValueError: pass


def test_tangent_frame_follows_u_and_minus_v():
    pos = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float); nrm = np.tile([0, 0, 1.0], (3, 1)); uv = np.array([[0, 0], [1, 0], [0, 1]], float)
    T, B = W.tangent_frame(pos, nrm, uv, np.array([[0, 1, 2]]))
    assert np.allclose(T, [[1, 0, 0]] * 3, atol=1e-9) and np.allclose(B, [[0, -1, 0]] * 3, atol=1e-9)
    u = np.random.default_rng(0).normal(size=(5, 3)); assert (np.abs((W._dec3n(u).astype(np.uint32) >> 30) - 3) == 0).all(), 'w bits are always 3'


def test_dec3n_roundtrip_through_the_reader():
    v = np.random.default_rng(3).normal(size=(200, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    back = H._decode_dec3n(W._dec3n(v).astype(np.uint32)); assert np.abs(back - v).max() < 0.004


def test_clean_skin_limits_bones_by_merging_into_parents_and_keeps_weights():
    parent = [-1, 0, 1, 2, 3, 4]; si = np.array([[5, 4, 0, 0], [3, 2, 0, 0], [1, 0, 0, 0]]); sw = np.array([[0.7, 0.3, 0, 0], [0.5, 0.5, 0, 0], [1, 0, 0, 0]])
    i2, w2 = W.clean_skin(si, sw, parent, 3)
    assert len(np.unique(i2[w2 > 0])) <= 3 and np.allclose(w2.sum(1), 1) and (i2[w2 > 0] <= 5).all()


def test_installer_backup_replace_uninstall_and_restore_are_exact():
    g = tempfile.mkdtemp(); cd = os.path.join(g, 'image', 'x64', 'raw', 'character'); os.makedirs(cd)
    rel = os.path.join('image', 'x64', 'raw', 'character', 'a.pac'); open(os.path.join(cd, 'a.pac'), 'wb').write(b'ORIGINAL-A'); open(os.path.join(cd, 'b.pac'), 'wb').write(b'ORIGINAL-B')
    I = Installer(g); I.install('m1', rel, b'MOD-ONE', 'one'); assert open(I.path(rel), 'rb').read() == b'MOD-ONE' and I.read_original(rel) == b'ORIGINAL-A'
    I.install('m2', rel, b'MOD-TWO', 'two'); assert [m['id'] for m in I.installed()] == ['m2'] and I.read_original(rel) == b'ORIGINAL-A', 'a second mod for the same file replaces the first, the original stays'
    relb = os.path.join('image', 'x64', 'raw', 'character', 'b.pac'); I.install('m3', relb, b'MOD-B', 'b'); I.uninstall('m2')
    assert open(I.path(rel), 'rb').read() == b'ORIGINAL-A' and open(I.path(relb), 'rb').read() == b'MOD-B'
    I.restore(); assert open(I.path(relb), 'rb').read() == b'ORIGINAL-B' and I.installed() == [] and not os.path.exists(I.bdir)
    try: Installer(tempfile.mkdtemp()); raise AssertionError('not a Sonic folder')
    except ValueError as e: assert 'Sonic' in str(e)


# ------------------------------------------------------------------ real files
def test_pac_rewrite_keeps_everything_but_the_changed_bytes():
    if CHAR_DIR is None: return SKIP()
    raw = open(os.path.join(CHAR_DIR, 'amy.pac'), 'rb').read(); p = pacx.Pacx(raw); name = p.split_names()[0]; sp = p.split(name)
    same = pacx.Pacx(pacwrite.rebuild(p, {name: sp.data})); assert same.split(name).data == sp.data and same.root.entries[0].uid == p.root.entries[0].uid
    e = next(x for x in sp.entries if x.ext == 'model'); b = bytearray(sp.data); b[e.offset + 4000] ^= 0xFF
    out = pacwrite.rebuild(p, {name: bytes(b)}); q = pacx.Pacx(out); assert q.split(name).data == bytes(b) and len(out) % 16 == 0
    assert sum(a != c for a, c in zip(q.root.data, p.root.data)) < 400, 'the root differs only in the split size / position fields'


def test_a_file_can_grow_inside_a_pac_and_nothing_else_changes():
    if CHAR_DIR is None: return SKIP()
    raw = open(os.path.join(CHAR_DIR, 'amy.pac'), 'rb').read(); p = pacx.Pacx(raw); name = p.split_names()[0]; sp = p.split(name)
    e = next(x for x in sp.entries if x.name == 'chr_amy_cloth_abd'); blob = bytes(np.random.default_rng(1).integers(0, 256, 349700, dtype=np.uint8))
    big = innerwrite.append_entries(sp, {e.index: blob}); sp2 = pacx.Inner(big, name)
    assert sp2.read(sp2.entries[e.index]) == blob and all(sp.read(a) == sp2.read(b) for a, b in zip(sp.entries, sp2.entries) if not a.is_proxy and a.index != e.index)
    assert [x.name for x in sp.entries] == [x.name for x in sp2.entries], 'names (the trees) are untouched'
    out = pacwrite.rebuild(p, {name: big}); q = pacx.Pacx(out); n_old, n_new = len(p.root.deps()[0][4]), len(q.root.deps()[0][4])
    assert n_new > n_old and q.split(name).data == big and [(x.uid, x.size) for x in q.root.entries] == [(x.uid, x.size) for x in p.root.entries], 'more chunks: the chunk table moved, everything reads back'


def test_streaming_stubs_become_full_textures_for_amy_knuckles_tails():
    if CHAR_DIR is None: return SKIP()
    for f, host in (('amy', 'chr_amy_cloth'), ('knuckles', 'chr_knuckles_cloth'), ('tails', 'chr_tails_cloth')):
        raw = open(os.path.join(CHAR_DIR, f + '.pac'), 'rb').read(); ch = sonic.Character(raw); assert ch.host == host and ch.texture_status() == (True, '')
        tpl, stub = ch.template(ch.textures()['abd']); assert stub and tpl.width >= 256
        new, rep = ch.build(ch.fit(humanoid(), up='+Y', forward='+Z', log=lambda *a: None), log=lambda *a: None)
        a, b = pacx.Pacx(raw), pacx.Pacx(new); sa, sb = a.split(a.split_names()[0]), b.split(b.split_names()[0])
        names = sorted(e.name for e, g in zip(sa.entries, sb.entries) if sa.read(e) != sb.read(g)); assert names == sorted(['chr_' + f, host + '_abd', host + '_nrm', host + '_prm']), names
        d = dds.Dds(sb.read(next(e for e in sb.entries if e.name == host + '_abd'))); assert d.width == tpl.width and d.mips == tpl.mips and d.kind == tpl.kind


def test_real_textures_have_exactly_the_size_the_dds_rule_predicts():
    if CHAR_DIR is None: return SKIP()
    p = pacx.Pacx.open(os.path.join(CHAR_DIR, 'sonic.pac')); s = p.split(p.split_names()[0]); n = 0
    for e in s.entries:
        if e.ext == 'dds' and e.name.startswith('chr_sonic_') and e.size > 1000: dds.Dds(s.read(e)); n += 1
    assert n >= 10, n


def test_whole_swap_changes_only_the_model_and_three_textures_and_textures_land_right():
    if CHAR_DIR is None: return SKIP()
    raw = open(os.path.join(CHAR_DIR, 'sonic.pac'), 'rb').read(); ch = sonic.Character(raw); assert ch.name == 'chr_sonic' and ch.host == 'chr_sonic_cloth' and ch.texture_status() == (True, '')
    h = humanoid(); f = ch.fit(h, up='+Y', forward='+Z', log=lambda *a: None); new, rep = ch.build(f, log=lambda *a: None)
    a, b = pacx.Pacx(raw), pacx.Pacx(new); sa, sb = a.split(a.split_names()[0]), b.split(b.split_names()[0])
    changed = sorted(e.name for e, g in zip(sa.entries, sb.entries) if sa.read(e) != sb.read(g)); assert changed == ['chr_sonic', 'chr_sonic_cloth_abd', 'chr_sonic_cloth_nrm', 'chr_sonic_cloth_prm'], changed
    assert [(e.uid, e.size) for e in a.root.entries] == [(e.uid, e.size) for e in b.root.entries]
    c2 = sonic.Character(new); cl = next(x for x in c2.model0.meshes() if x.material == 'chr_sonic_cloth'); U = cl.uvs()
    tex = dds.Dds(sb.read(next(e for e in sb.entries if e.name == 'chr_sonic_cloth_abd'))).decode(0); W_ = tex.shape[1]
    order = np.array(list(dict.fromkeys(int(i) for t in f['tris'] for i in t))); src = np.asarray(h.images[0].convert('RGB'))
    got = tex[np.clip((U[:, 1] * W_).astype(int), 0, W_ - 1), np.clip((U[:, 0] * W_).astype(int), 0, W_ - 1), :3]
    want = src[np.clip((h.uv[order, 1] * 256).astype(int), 0, 255), np.clip((h.uv[order, 0] * 256).astype(int), 0, 255)]
    assert (np.abs(got.astype(int) - want.astype(int)).max(1) <= 40).mean() > 0.98, 'textures must land on the right vertices'
    assert np.array_equal(order[cl.faces], np.asarray(f['tris'])) and len(rep['levels']) == len(ch.chunks)
    sk = cl.skin(); names = c2.model0.nodes()[0]; dom = [names[i] for i in sk[0][np.arange(len(U)), sk[1].argmax(1)]]
    assert any('Head' in n for n in dom) and any('Hand' in n or 'Arm' in n for n in dom) and any('Foot' in n or 'Leg' in n or 'Toe' in n for n in dom), 'skin lands on head, arm and leg bones'


def test_a_model_too_big_for_a_slot_is_reduced_not_refused():
    if CHAR_DIR is None: return SKIP()
    raw = open(os.path.join(CHAR_DIR, 'sonic.pac'), 'rb').read(); ch = sonic.Character(raw); f = ch.fit(humanoid(), up='+Y', forward='+Z', log=lambda *a: None)
    big = dict(f); n = len(f['pos']); rng = np.random.default_rng(0)
    reps = np.tile(np.arange(n), 8); jitter = rng.normal(scale=0.002, size=(len(reps), 3))                       # ~23,000 vertices: more than the cloth slot of the lowest level holds
    big['pos'] = f['pos'][reps] + jitter; big['nrm'] = f['nrm'][reps]; big['uv'] = f['uv'][reps]; big['skin_i'] = f['skin_i'][reps]; big['skin_w'] = f['skin_w'][reps]
    big['tris'] = np.concatenate([f['tris'] + n * k for k in range(8)])
    out, rep = W.fill_fitting(ch.chunks[1], big, log=lambda *a: None); assert len(out) == len(ch.chunks[1]) and rep['vertices'] <= 13137


def test_command_line_and_installer_on_a_fake_game_folder():
    if CHAR_DIR is None: return SKIP()
    g = tempfile.mkdtemp(); cd = os.path.join(g, 'image', 'x64', 'raw', 'character'); os.makedirs(cd)
    for f in ('sonic.pac', 'amy.pac'): shutil.copy(os.path.join(CHAR_DIR, f), cd)
    import modswap.modelio as MIO; MIO.load_model = lambda path, textures=None: humanoid()
    def run(*args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try: __import__('modswap.cli', fromlist=['main']).main(list(args))
            except SystemExit as e:
                if e.code not in (None, 0): return out.getvalue() + 'EXIT: %s' % e.code
        return out.getvalue()
    o = run('sonic', '--dir', g, 'characters'); assert 'Sonic' in o and 'Amy' in o and 'model only' not in o, o
    before = sha(os.path.join(cd, 'sonic.pac')); out = os.path.join(g, 'x.pac')
    assert 'nothing installed' in run('sonic', '--dir', g, 'install', '--character', 'sonic', '--model', 'x.fbx', '--forward', '+Z', '--dry-run', out) and sha(os.path.join(cd, 'sonic.pac')) == before
    o = run('sonic', '--dir', g, 'install', '--character', 'sonic', '--model', 'x.fbx', '--forward', '+Z', '--name', 'Test'); assert 'installed "Test"' in o, o
    assert sha(os.path.join(cd, 'sonic.pac')) != before and 'Test' in run('sonic', '--dir', g, 'list')
    o = run('sonic', '--dir', g, 'install', '--character', 'amy', '--model', 'x.fbx', '--forward', '+Z', '--dry-run', out); assert 'nothing installed' in o and pacx.Pacx.open(out).split_names(), o
    run('sonic', '--dir', g, 'restore'); assert sha(os.path.join(cd, 'sonic.pac')) == before and 'nothing installed' in run('sonic', '--dir', g, 'list')


def test_app_server_whole_flow_for_sonic():
    if CHAR_DIR is None: return SKIP()
    g = tempfile.mkdtemp(); cd = os.path.join(g, 'image', 'x64', 'raw', 'character'); os.makedirs(cd); shutil.copy(os.path.join(CHAR_DIR, 'sonic.pac'), cd); pac0 = sha(os.path.join(cd, 'sonic.pac'))
    os.makedirs(os.path.join(cfg, 'ModSwap'), exist_ok=True)
    json.dump({'games': [dict(id='sf', name='Sonic Frontiers', root=g, source='steam', engine='unknown')]}, open(os.path.join(cfg, 'ModSwap', 'games.json'), 'w'))
    from modswap import server
    server.UPLOADS = tempfile.mkdtemp(prefix='ms_up_'); d = os.path.join(server.UPLOADS, 'up1'); os.makedirs(d); h = humanoid(); h.images[0].save(os.path.join(d, 'tex.png'))
    with open(os.path.join(d, 'hero.obj'), 'w') as f:
        f.write('mtllib hero.mtl\nusemtl m\n'); [f.write('v %f %f %f\n' % tuple(p)) for p in h.pos]; [f.write('vt %f %f\n' % (u, 1 - v)) for u, v in h.uv]
        [f.write('vn %f %f %f\n' % tuple(n)) for n in h.nrm]; [f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % tuple(x for i in t for x in (i + 1, i + 1, i + 1))) for t in h.tris + 0]
    open(os.path.join(d, 'hero.mtl'), 'w').write('newmtl m\nKd 1 1 1\nmap_Kd tex.png\n')
    def wait(jid):
        for _ in range(900):
            j = server.JOBS[jid]
            if j['done']: break
            time.sleep(0.2)
        assert not j['error'], j['error']; return j['result']
    from modswap.games.library import Library
    gj = server._game_json(Library().games['sf']); assert gj['engine'] == 'hedgehog2' and gj['supported'] is True, gj
    ch = wait(server.api_characters('sf'))['characters']; assert [c['label'] for c in ch] == ['Sonic'] and ch[0]['rigged'], ch
    body = dict(game='sf', family=ch[0]['index'], upload='up1', up='+Y', forward='+Z', scale=1.0)
    f = server.api_fit(body); pos = np.frombuffer(base64.b64decode(f['new']['pos']), '<f4').reshape(-1, 3); opos = np.frombuffer(base64.b64decode(f['orig']['pos']), '<f4').reshape(-1, 3)
    assert len(pos) == f['new']['n'] and np.isfinite(pos).all() and 80 < f['height'] < 130, f['height']
    assert abs((pos[:, 2].max() - pos[:, 2].min()) - (opos[:, 2].max() - opos[:, 2].min())) < 12 and pos[:, 2].min() > -10, 'fitted to the character, standing on the floor'
    r = wait(server.api_apply(dict(body, name='Humanoid', install=True))); assert r.get('mod'), r
    assert sha(os.path.join(cd, 'sonic.pac')) != pac0 and [m['active'] for m in server.api_mods('sf')['mods']] == [True]
    wait(server.api_apply(dict(body, name='Humanoid 2', install=True))); mods = server.api_mods('sf'); assert sum(m['active'] for m in mods['mods']) == 1 and len(mods['mods']) == 2
    mid = next(m['id'] for m in mods['mods'] if m['active']); wait(server.api_mod_uninstall(dict(game='sf', id=mid))['job']); assert sha(os.path.join(cd, 'sonic.pac')) == pac0, 'uninstall gives the original file back byte for byte'
    wait(server.api_mod_install(dict(game='sf', id=mid, name='again'))['job']); assert sha(os.path.join(cd, 'sonic.pac')) != pac0
    server.api_restore('sf'); assert sha(os.path.join(cd, 'sonic.pac')) == pac0 and not os.path.exists(os.path.join(g, 'modswap_backup'))


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print('%d passed' % n)
