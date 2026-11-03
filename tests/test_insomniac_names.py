"""Listing more Spider-Man characters (suits + other characters) and re-skinning suits that have no plain material."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modswap.insomniac import install as I, materials as MT, project as PR, names as N
from test_insomniac_toc import build_toc
from modswap.insomniac.toc import Toc, path_id


def _toc(paths):
    import tempfile
    d = tempfile.mkdtemp(); open(os.path.join(d, 'toc'), 'wb').write(build_toc([(path_id(p), 0, 16 * k, 16) for k, p in enumerate(paths)], ['g00s000'])); return Toc.open(os.path.join(d, 'toc'))


def test_suits_and_other_characters_are_found_by_path_and_only_real_ones_listed():
    t = _toc([I.suit_model_path(x) for x in ('classic', 'mk4', '2099', 'npc_kingpin', 'npc_mrnegative', 'npc_rhino')] + ['characters/npc/npc_nothing_i_listed/x.model'])
    assert I.find_suits(t) == ['classic', 'mk4', '2099', 'npc_kingpin', 'npc_mrnegative', 'npc_rhino'], I.find_suits(t)
    assert I.find_suits(t, npcs=False) == ['classic', 'mk4', '2099']
    assert I.suit_model_path('npc_kingpin') == 'characters/npc/npc_kingpin/npc_kingpin.model' and I.suit_model_path('noir') == 'characters/hero/hero_spiderman_noir/hero_spiderman_noir.model'
    assert PR._title('npc_mrnegative') == 'Mr. Negative' and PR._title('mk4') == 'Spider-Armor MK IV Suit' and PR._title('punk') == 'Spider-Punk Suit' and PR._title('npc_foo_bar') == 'Foo Bar'
    assert len(N.SUITS) > 100 and len(N.NPCS) > 500


def row(slot, shader, tex, tris): return dict(slot=slot, shader=shader, textures=tex, triangles=tris, material=slot)


def test_picker_prefers_the_plain_material_but_no_longer_gives_up():
    f = 'characters/hero/hero_spiderman_punk/textures/hero_spiderman_punk_%s.texture'
    plain = row(0, 'materialtemplates/legacy/legacy_hero_spiderman_basic_normal_gloss.materialgraph', [f % 'jacket_c', f % 'jacket_n', f % 'jacket_g'], 9000)
    detail = row(1, 'materialtemplates/legacy/legacy_hero_spiderman_detail_windy.materialgraph', [f % 'body_c', f % 'body_n', f % 'body_g', f % 'body_mask'], 20000)
    eyes = row(2, 'materialgraph/characters/hero/hero_Spiderman_Eye_Base/x.materialgraph', ['characters/hero/hero_spiderman/textures/hero_spiderman_eye_c.texture'], 100)
    assert MT.pick_single_texture_slot([plain, detail, eyes], 'punk') == 0                       # plain kind first
    assert MT.pick_single_texture_slot([detail, eyes], 'punk') == 1                              # no plain one: the most-used material with its own colour texture (it used to be refused)
    assert MT.pick_single_texture_slot([eyes], 'punk') is None                                   # only shared textures: never re-skin those
    k = 'characters/npc/npc_kingpin/textures/npc_kingpin_%s.texture'
    assert MT.pick_single_texture_slot([row(0, 'x/legacy_char_basic_normal_gloss.mg', [k % 'suit_c', k % 'suit_n', k % 'suit_g'], 5000)], 'npc_kingpin') == 0


def test_material_ids_from_the_models_own_path_strings_match_the_record_scan():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_insomniac_cli import SAMPLES
    from modswap.insomniac import model as M
    f = os.path.join(SAMPLES, 'BF45D48B5314EC76.bin'); tf = os.path.join(SAMPLES, '..', 'toc_current')
    if not (os.path.isfile(f) and os.path.isfile(tf)): print('   (no real samples: skipped)'); return
    t = Toc(open(tf, 'rb').read()); m = M.Model(open(f, 'rb').read())
    assert MT.material_ids(m, t) == MT._scan_ids(m, t) and len(MT.material_ids(m, t)) == 11 and MT._path_strings(m)[3].endswith('hero_spiderman_classic_rubber.material')


def test_accessory_words_are_whole_words():
    assert MT._accessory('webshooters_c.texture') and MT._accessory('shoe_n.texture') and MT._accessory('fearitself_eyesframe_c') and not MT._accessory('white_damagemask_g.texture') and not MT._accessory('body_c.texture')


def test_only_the_suits_own_matching_textures_are_replaced_never_shared_or_layered_ones():
    f = 'characters/hero/hero_spiderman_noir/textures/hero_spiderman_noir_%s.texture'
    r = row(12, 'x/legacy_hero_spiderman_basic_normal_gloss.mg', ['textures/default_pink_shader/default_pink_shader_g.texture', 'characters/shared/textures/detail/hero_spiderman_damage_c.texture', 'textures/default_pink_shader/default_pink_shader_c.texture',
                                                                f % 'vest_g', 'x/detail_softleather_01_n.texture', f % 'vest_n', f % 'vest_c', f % 'vest_damagemask_g'], 5)
    t = MT.slot_textures(r, 'hero_spiderman_noir')
    assert t == dict(c=f % 'vest_c', n=f % 'vest_n', g=f % 'vest_g'), t                     # (it used to take the first '_c' in the list: the shared, layered damage texture)
    assert MT.pick_single_texture_slot([r], 'noir') == 12 and MT.slot_textures(row(0, 'x', ['characters/shared/textures/detail/hero_spiderman_damage_c.texture'], 1), 'hero_spiderman_noir') is None
