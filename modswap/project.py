"""One game = one Project: scan it, plan a swap, build the override files, pack and install them (and undo it again)."""
import os, re, json, shutil, time
from .games import library, detect
from .pakio import Repak
from .ue4 import scan as uescan, autoprofile, aes as uaes, iostore
from .ue4.format import detect_sk_format
from .build import run_profile

PAK_VERSIONS = {3: 'V3', 4: 'V4', 5: 'V5', 6: 'V6', 7: 'V7', 8: 'V8B', 9: 'V9', 10: 'V10', 11: 'V11'}


def _slug(s): return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:40] or 'mod'


def _scan_ok(path):
    """a cached scan from an older ModSwap may have missed meshes (e.g. ones not named SK_...): rescan"""
    try: return json.load(open(path)).get('ver', 1) >= uescan.SCAN_VERSION
    except Exception: return False


class Project:
    def __init__(self, game, backend=None, cache_root=None):
        self.game = game
        self.backend = backend or Repak(aes=uaes.key_for(game.id))
        self.dir = os.path.join(cache_root or os.path.join(library.config_dir(), 'cache'), game.id)
        self.orig = os.path.join(self.dir, 'orig'); self.out = os.path.join(self.dir, 'out')
        os.makedirs(self.orig, exist_ok=True)
        if game.engine != 'unreal': raise NotImplementedError('%s games are not supported yet (only Unreal)' % game.engine)

    def _live_paks(self):
        """The game's own pak files that exist right now. The saved list can be stale (a pak deleted since) and can even contain paks ModSwap
        installed itself, so re-check it every time and fall back to a fresh scan of the folder."""
        ours = {os.path.normcase(os.path.abspath(x)) for x in self._manifest().get('installed', {})}
        def ok(x): return os.path.isfile(x) and os.path.normcase(os.path.abspath(x)) not in ours and not os.path.basename(x).lower().startswith('zz_modswap_')
        paks = [x for x in (self.game.paks or []) if ok(x)]
        if not paks or len(paks) != len(self.game.paks or []):
            fresh = [x for x in detect.find_paks(self.game.root) if ok(x)]
            if fresh: paks = fresh; self.game.paks = fresh
        return paks

    def _main_pak(self):
        paks = self._live_paks()
        if not paks: raise RuntimeError('no .pak files found under %s (IoStore/loose-file cooks are not supported yet)' % self.game.root)
        return max(paks, key=os.path.getsize)

    # ------------------------------------------------------------ scanning
    def scan(self, force=False, log=print):
        cache = os.path.join(self.dir, 'scan.json'); fm = os.path.join(self.dir, 'files.json')
        if not force and os.path.exists(cache) and os.path.exists(fm) and _scan_ok(cache):
            self.files = json.load(open(fm)); return uescan.load_scan(cache)
        paks = self._live_paks()
        if not paks: raise RuntimeError('no .pak files found under %s (IoStore/loose-file cooks are not supported yet)' % self.game.root)
        self._check_keys(paks, log)
        files = uescan.list_assets(paks, self.backend, log)
        if not files and any(os.path.splitext(f)[1].lower() == '.utoc' for d, _, fs in os.walk(os.path.dirname(paks[0])) for f in fs):
            raise RuntimeError('this game keeps its characters in IoStore containers (.utoc/.ucas); its .pak files only hold audio, video and configs. ModSwap can not read IoStore yet')
        sk_c, sm_c = uescan.candidates(files)
        log('%d character candidates, %d item candidates' % (len(sk_c), len(sm_c)))
        sk = uescan.verify_skeletal(sk_c, self.backend, self.dir, log)
        res = dict(characters=uescan.families(sk), items=sm_c, total_files=len(files))
        uescan.save_scan(res, cache)
        self.files = {k: v[0] for k, v in files.items()}; json.dump(self.files, open(fm, 'w'))
        return res

    def _check_keys(self, paks, log):
        """paks with an encrypted file list need the game's AES key: say so plainly instead of letting repak fail with a vague error"""
        key = uaes.key_for(self.game.id); enc = [p for p in paks if (uaes.footer(p) or {}).get('encrypted')]
        if not enc: return
        probe = max(enc, key=lambda p: (uaes.footer(p) or {}).get('index_size', 0))
        if not key: raise RuntimeError('the file lists inside this game\'s paks are encrypted and ModSwap has no AES key for it (%d of %d paks)' % (len(enc), len(paks)))
        if not uaes.key_works(probe, key): raise RuntimeError('the saved AES key for this game does not decrypt its paks (checked %s), so it is the wrong key' % os.path.basename(probe))
        log('AES key accepted: it decrypts the file list of %s' % os.path.basename(probe))

    # ------------------------------------------------------------ extraction
    def extract(self, bases, exts=('.uasset', '.uexp', '.ubulk')):
        """Make sure the given asset bases (pak path without extension) are unpacked under orig/."""
        if not hasattr(self, 'files'): self.files = json.load(open(os.path.join(self.dir, 'files.json')))
        by_pak = {}
        for b in dict.fromkeys(x for x in bases if x):                # ignore paths that aren't in this game's own paks
            pk = self.files.get(b)
            if pk is None: continue
            need = [b + e for e in exts if not os.path.exists(os.path.join(self.orig, b + e))]
            if need: by_pak.setdefault(pk, []).extend(need)
        for pk, inc in by_pak.items(): self.backend.unpack(pk, self.orig, inc)

    # ------------------------------------------------------------ planning
    def plan(self, family):
        return autoprofile.suggest_plan(family.assets)

    def make_profile(self, family, plan, log=print):
        assets = family.assets
        content_prefix = re.match(r'(.*?/Content)/', assets[0].path).group(1)
        self.extract([a.path for a in assets if a.path in plan['targets']], exts=('.uasset', '.uexp'))
        fmt = None; probe = [a.path for a in assets if a.path in plan['targets']] + [a.path for a in assets if a.path not in plan['targets']][:6]
        self.extract(probe, exts=('.uasset', '.uexp'))
        for rel in probe:                                               # first mesh in this family whose layout we can read
            t0 = os.path.join(self.orig, rel)
            if not (os.path.exists(t0 + '.uasset') and os.path.exists(t0 + '.uexp')): continue
            try: fmt = detect_sk_format(open(t0 + '.uasset', 'rb').read(), open(t0 + '.uexp', 'rb').read())
            except Exception: fmt = None
            if fmt: break
        if not fmt:
            t0 = os.path.join(self.orig, plan['targets'][0]); rep = os.path.join(self.dir, 'layout_report.txt')
            rep_note = ''
            try:
                from .ue4.format import diagnose_layout
                open(rep, 'w', encoding='utf-8').write(diagnose_layout(open(t0 + '.uasset', 'rb').read(), open(t0 + '.uexp', 'rb').read(), plan['targets'][0]))
                log('wrote a layout report to %s' % rep); rep_note = ' | report: ' + rep
            except Exception as e: log('could not write the layout report: %r' % (e,))
            raise RuntimeError('could not understand the mesh layout of %s (unsupported cook?)%s' % (plan['targets'][0], rep_note))
        log('mesh layout: %s' % fmt)
        prof = autoprofile.make_profile(self.game.name, content_prefix, fmt, assets, plan, self.orig, self.extract, log)
        try: pk = self._main_pak()
        except RuntimeError: pk = ''
        v = detect.pak_version(pk) if pk else None
        prof['pak_version'] = PAK_VERSIONS.get(v, 'V11')
        return prof

    # ------------------------------------------------------------ build + install
    def build(self, profile, model, name='mod', forward=None, up=None, scale=1.0, adjust=None, edits=None, log=print):
        out = os.path.join(self.out, _slug(name)); shutil.rmtree(out, ignore_errors=True)
        paths = [t['mesh'] for t in profile['targets']] + list(profile.get('hide', []))
        self.extract(paths, exts=('.uasset', '.uexp'))
        for t in profile['targets']: self.extract([x['path'] for x in t['textures']], exts=('.uasset', '.uexp', '.ubulk'))
        run_profile(profile, self.orig, model, out, up=up, forward=forward, scale=scale, adjust=adjust, edits=edits, log=log)
        pak = out + '.pak'
        info = self.backend.info(self._main_pak())
        seed = re.search(r'path hash seed: Some\(([0-9A-Fa-f]+)\)', info)
        self.backend.pack(out, pak, version=profile.get('pak_version') or 'V11', seed=int(seed.group(1), 16) if seed else 0,
                          mount=(re.search(r'mount point: (\S+)', info) or [0, '../../../'])[1])
        return pak

    def _paks_dir(self):
        base = self._main_pak(); return os.path.dirname(base), os.path.splitext(os.path.basename(base))[0]

    def install(self, pak, name='mod', mod_id=''):
        """add a mod. Mods stack: each one is its own patch pak (the game loads every *_P.pak). Nothing already installed is touched."""
        d, stem = self._paks_dir(); man = self._manifest()
        mine = lambda p: man['installed'].get(p, {}).get('mod') == mod_id and bool(mod_id)
        cands = [os.path.join(d, stem + '_P.pak'), os.path.join(d, 'zz_ModSwap_%s_P.pak' % _slug(name)), os.path.join(d, 'zz_ModSwap_%s_%s_P.pak' % (_slug(name), _slug(mod_id or str(int(time.time())))))]
        dest = next((c for c in cands if mine(c) or not os.path.exists(c)), cands[-1])
        shutil.copy2(pak, dest); man['installed'][dest] = dict(name=name, mod=mod_id, time=time.time()); self._save(man)
        return dest

    def installed(self): return self._manifest()['installed']

    def active_ids(self):
        return list(dict.fromkeys(v['mod'] for v in self._manifest()['installed'].values() if v.get('mod')))

    def uninstall_mod(self, mid, log=print):
        man = self._manifest(); gone = []
        for p, v in list(man['installed'].items()):
            if v.get('mod') != mid: continue
            try:
                if os.path.exists(p): os.remove(p)
                gone.append(p); del man['installed'][p]
            except OSError as e: raise RuntimeError('could not remove %s (is the game running?): %s' % (os.path.basename(p), e))
        self._save(man); return gone

    def restore(self):
        man = self._manifest(); gone = []
        for p in list(man['installed']):
            try:
                if os.path.exists(p): os.remove(p)
                gone.append(p); del man['installed'][p]
            except OSError as e: raise RuntimeError('could not remove %s (is the game running?): %s' % (p, e))
        self._save(man); return gone

    def _manifest(self):
        p = os.path.join(self.dir, 'installed.json')
        return json.load(open(p)) if os.path.exists(p) else dict(installed={})

    def _save(self, man): json.dump(man, open(os.path.join(self.dir, 'installed.json'), 'w'), indent=1)


# ====================================================================================================== IoStore games (Unreal 5)
class _NoPak:
    """stand-in for repak: IoStore games are read and written by retoc, so no .pak tool is needed (or downloaded)"""
    def __getattr__(self, n): raise RuntimeError('this game keeps its assets in IoStore containers, which are handled by retoc, not repak')


def is_iostore(game):
    """True when the game's assets live in .utoc/.ucas containers and its .pak files hold no .uasset (so Project can not see them)."""
    paks_dir = None
    for root in [game.root]:
        for d, _, fs in os.walk(root):
            if os.path.basename(d).lower() == 'paks' and any(f.lower().endswith('.utoc') for f in fs): paks_dir = d; break
            if d.count(os.sep) - root.count(os.sep) > 5: _[:] = []
        if paks_dir: break
    if not paks_dir: return False
    mark = os.path.join(library.config_dir(), 'cache', game.id, 'mode.txt')
    try:
        v = open(mark).read().strip()
        if v: return v == 'iostore'
    except OSError: pass
    paks = glob_paks(paks_dir)
    legacy = False
    try:
        rp = Repak(aes=uaes.key_for(game.id))
        for p in paks:
            try:
                if any(n.lower().endswith('.uasset') for n in rp.list(p)): legacy = True; break
            except Exception: continue
    except Exception: legacy = False
    os.makedirs(os.path.dirname(mark), exist_ok=True); open(mark, 'w').write('pak' if legacy else 'iostore')
    return not legacy


class IoStoreProject(Project):
    """Same flow as Project (scan -> plan -> profile -> build -> install) for games whose characters sit in IoStore containers.
    Extraction goes through `retoc to-legacy`, the finished swap is packed by `retoc to-zen` and installed as a .utoc/.ucas/.pak set in Paks/~mods."""
    MODS = '~mods'

    def __init__(self, game, backend=None, cache_root=None):
        super().__init__(game, backend or _NoPak(), cache_root)
        ver = (game.engine_version or '').strip()
        self.retoc = iostore.Retoc(aes=uaes.key_for(game.id), version=iostore.ue_version_flag(ver) or ('UE5_1' if not ver else None))
        self.notes = []

    # ---- where things are
    def _live_paks(self):
        ps = super()._live_paks()
        return [p for p in ps if self.MODS not in p.replace('\\', '/').lower()]

    def _paks_dir(self):
        for d, _, fs in os.walk(self.game.root):
            if os.path.basename(d).lower() == 'paks' and any(f.lower().endswith('.utoc') for f in fs): return d, 'pakchunk0-Windows'
            if d.count(os.sep) - self.game.root.count(os.sep) > 5: _[:] = []
        raise RuntimeError('could not find the game\'s Paks folder under %s' % self.game.root)

    def _main_pak(self): return os.path.join(self._paks_dir()[0], 'pakchunk0-Windows.pak')

    # ---- scanning
    CHAR = re.compile(r'^SK_(\d{4})((?:_\d{2}){1,3})_(?!Skeleton)(.+)$')

    def scan(self, force=False, log=print):
        cache = os.path.join(self.dir, 'scan.json')
        if not force and os.path.exists(cache) and _scan_ok(cache): return self._relabel(uescan.load_scan(cache))
        d = self._paks_dir()[0]; utocs = iostore.containers(d)
        if not utocs: raise RuntimeError('no .utoc containers found in %s' % d)
        paks = [p for p in glob_paks(d)]
        if paks: self._check_keys(paks, log)
        seen = {}
        for u in utocs:
            log('listing %s' % os.path.basename(u))
            for cont, base in self.retoc.list_packages(u, keep=r'^SK_\d{4}_'):
                seen[base] = cont
        log('%d character mesh packages' % len(seen))
        parts, base_meshes = {}, {}
        for base in sorted(seen):
            name = base.rsplit('/', 1)[-1]; m = self.CHAR.match(name)
            if not m: continue
            gid, groups, rest = m.group(1), re.findall(r'_(\d{2})', m.group(2)), m.group(3)
            if re.match(r'^BASE(_\d+)?$', rest) and len(groups) == 1: base_meshes.setdefault((gid, groups[0]), []).append(base); continue
            if len(groups) < 2: continue
            parts.setdefault((gid, groups[0], groups[1]), []).append(base)
        sk = []
        for (gid, form, look), bases in sorted(parts.items()):
            if not any(autoprofile.part_code(b.rsplit('/', 1)[-1]) == 'BDY' for b in bases): continue      # no whole-body mesh: not something we can swap
            skel = 'SKEL_%s_%s_%s' % (gid, form, look)
            for b in bases + base_meshes.get((gid, form), []):
                a = uescan.Asset(b, 'skeletal', b.rsplit('/', 1)[-1], os.path.dirname(uescan._content_rel(b)), seen[b], skeleton=skel, verified=True); sk.append(a)
        if not sk: raise RuntimeError('found %d containers but no character meshes named like SK_<id>_<form>_<look>_BDY_00' % len(utocs))
        res = dict(characters=uescan.families(sk), items=[], total_files=len(seen))
        uescan.save_scan(res, cache); self.files = {a.path: 'iostore' for a in sk}
        return self._relabel(res)

    def _relabel(self, res):
        names = self._names(); looks = {}
        for f in res['characters']:
            m = re.search(r'SKEL_(\d{4})_(\d{2})_(\d{2})', f.key or '')
            if m: looks[m.group(1) + '_' + m.group(2)] = looks.get(m.group(1) + '_' + m.group(2), 0) + 1
        for f in res['characters']:
            m = re.search(r'SKEL_(\d{4})_(\d{2})_(\d{2})', f.key or '')
            if not m: continue
            gid, form, look = m.groups(); nm = names.get('%s_%s' % (gid, form)) or names.get(gid)
            if nm: f.label = nm + ('' if looks.get(gid + '_' + form, 1) < 2 else '  \u00b7  outfit %s' % look)
            else: f.label = 'Character %s  \u00b7  form %s  \u00b7  look %s' % (gid, form, look)
        res['characters'].sort(key=lambda f: (re.sub(r'^Character ', '~', f.label)))
        return res

    def _names(self):
        """{'0000_10': 'Goku (Z - Mid)', ...} read from the game's own English text (Localization/Data/en/Data.locres); {} when not found"""
        p = os.path.join(self.dir, 'names.json')
        try: return json.load(open(p))
        except Exception: pass
        names = {}
        try: names = self._read_names()
        except Exception as e: print('could not read character names: %r' % (e,))
        if names: json.dump(names, open(p, 'w'), ensure_ascii=False)
        return names

    def _read_names(self):
        from .ue4 import locres
        rp = Repak(aes=uaes.key_for(self.game.id)); d = self._paks_dir()[0]; hits = []
        for pk in glob_paks(d):
            try: lst = rp.list(pk)
            except Exception: continue
            for n in lst:
                m = re.search(r'/Localization/Data/([A-Za-z0-9-]+)/Data\.locres$', n, re.I)
                if m: hits.append((0 if m.group(1).lower() == 'en' else 1, pk, n))
        if not hits: return {}
        _, pk, n = min(hits); tmp = os.path.join(self.dir, 'loc'); shutil.rmtree(tmp, ignore_errors=True)
        rp.unpack(pk, tmp, [n])
        data = locres.parse(open(os.path.join(tmp, *n.split('/')), 'rb').read()); shutil.rmtree(tmp, ignore_errors=True)
        out = {}
        for ns in ('ST_CHR_NAME', 'ST_CHR_NAME_FULL'):                      # the FULL one says 'Goku (Z - Mid), Super Saiyan'
            for k, v in (data.get(ns) or {}).items():
                m = re.match(r'^%s_(\d{4})_(\d{2})$' % ns, k)
                if m and v.strip(): out['%s_%s' % m.groups()] = v.strip()
        return out

    # ---- extraction
    def extract(self, bases, exts=('.uasset', '.uexp', '.ubulk')):
        need = [b for b in dict.fromkeys(x for x in bases if x) if not os.path.exists(os.path.join(self.orig, b + '.uasset'))]
        if not need: return
        self.retoc.to_legacy(self._paks_dir()[0], self.orig, [b.rsplit('/', 1)[-1] for b in need])

    # ---- build + install
    def build(self, profile, model, name='mod', forward=None, up=None, scale=1.0, adjust=None, edits=None, log=print):
        out = os.path.join(self.out, _slug(name)); shutil.rmtree(out, ignore_errors=True)
        paths = [t['mesh'] for t in profile['targets']] + list(profile.get('hide', []))
        self.extract(paths, exts=('.uasset', '.uexp'))
        for t in profile['targets']: self.extract([x['path'] for x in t['textures']], exts=('.uasset', '.uexp', '.ubulk'))
        run_profile(profile, self.orig, model, out, up=up, forward=forward, scale=scale, adjust=adjust, edits=edits, log=log)
        so = os.path.join(self.orig, 'scriptobjects.bin')
        if not os.path.exists(so): self.retoc.to_legacy(self._paks_dir()[0], self.orig, [paths[0].rsplit('/', 1)[-1]])
        shutil.copy2(so, os.path.join(out, 'scriptobjects.bin'))
        log('packing the swap into an IoStore container (retoc)...')
        stem = 'ModSwap_%s_P' % _slug(name)
        files = self.retoc.to_zen(out, os.path.join(self.out, stem + '.utoc'))
        shutil.rmtree(out, ignore_errors=True)
        return files[0]

    def install(self, pak, name='mod', mod_id=''):
        d, _ = self._paks_dir(); man = self._manifest(); dest_dir = os.path.join(d, self.MODS); os.makedirs(dest_dir, exist_ok=True)
        stem = 'ModSwap_%s_P' % _slug(name); src = os.path.splitext(pak)[0]; dests = []
        other = man['installed'].get(os.path.join(dest_dir, stem + '.utoc'), {}).get('mod')
        if other and other != mod_id: stem = 'ModSwap_%s_%s_P' % (_slug(name), _slug(mod_id))         # same name as a mod that stays installed: keep both
        for e in ('.pak', '.utoc', '.ucas'):
            dest = os.path.join(dest_dir, stem + e); shutil.copy2(src + e, dest); dests.append(dest)
            man['installed'][dest] = dict(name=name, mod=mod_id, time=time.time())
        self._save(man)
        root = os.path.dirname(os.path.dirname(os.path.dirname(d)))         # .../<Game>/Content/Paks -> <Game>
        self.notes = []
        if not os.path.exists(os.path.join(root, 'Binaries', 'Win64', 'dsound.dll')):
            self.notes.append('heads up: this game checks container signatures. Without the "UTOC Signature Bypass" patch (dsound.dll in %s) it will ignore or reject this mod. Get it from the game\'s page on Nexus Mods, then it works with ModSwap mods too.' % os.path.join(root, 'Binaries', 'Win64'))
        return dests[1]


def glob_paks(d):
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith('.pak') and not f.lower().startswith(('zz_modswap_', 'modswap_'))]
