"""Swap a Sonic Frontiers character: one call that takes the character's .pac and a user's model and returns the new .pac.

    pac = Pacx(bytes);  char = Character(pac)                 # which split holds the model, its host material and the three textures
    fitted = char.fit(user_model, ...);  new_pac_bytes, report = char.build(fitted)

The model is filled in place for every level of detail (hewrite), the host material's three textures (diffuse 'abd', normal 'nrm', params 'prm') are replaced by DDS files of exactly
the same size and format, and the .pac is written again (pacwrite). Nothing moves inside the split, so nothing else has to be patched.
"""
import re, struct
import numpy as np
from . import pacx, pacwrite, needle, innerwrite, hemodel as H, hewrite as W, dds

NEUTRAL = {'nrm': (130, 126, 255, 255), 'prm': (27, 83, 21, 212)}       # flat normal map (BC5 keeps R,G), neutral params (the average of the original)
ROLES = ('abd', 'nrm', 'prm')


class NotSupported(ValueError): pass


class Character:
    def __init__(self, pac, stem=None):
        self.pac = pac if isinstance(pac, pacx.Pacx) else pacx.Pacx(pac)
        names = self.pac.split_names()
        if not names: raise NotSupported('this .pac has no embedded split with a model')
        self.split_name = names[0]; self.split = self.pac.split(self.split_name)
        models = [e for e in self.split.entries if e.ext == 'model' and not e.is_proxy and e.name.startswith('chr_')]
        if not models: raise NotSupported('no character model (chr_*) in this .pac')
        self.entry = min(models, key=lambda e: (len(e.name), e.name))              # the main model has the shortest name: chr_sonic, not chr_sonic_aura
        self.name = self.entry.name; self.blob = self.split.read(self.entry); self.chunks = needle.model_chunks(self.blob)
        self.model0 = H.HeModel(self.chunks[0]); self.host = W._host(self.model0.meshes()).material
        self.by_name = {(e.ext, e.name): e for e in self.split.entries if not e.is_proxy}

    # ------------------------------------------------------------ materials / textures
    def textures(self):
        """{role: texture name} of the host material (read from the material file)"""
        e = self.by_name.get(('material', self.host))
        if e is None: raise NotSupported('the material %s is not in this .pac' % self.host)
        raw = self.split.read(e); out = {}
        for m in re.finditer(rb'chr_[a-z0-9_]+?_(abd|nrm|prm)(?![a-z0-9_])', raw): out.setdefault(m.group(1).decode(), m.group().decode())
        return out

    def template(self, name):
        """-> (Dds template, is_stub). A texture is either a full DDS file or a small 'NTSI' streaming stub (header only; the pixels live in texture_streaming\\*.ntsp)."""
        e = self.by_name.get(('dds', name))
        if e is None: raise NotSupported('texture %s is not in this .pac' % name)
        raw = self.split.read(e)
        if raw[:4] == b'DDS ': return dds.Dds(raw), False
        if raw[:4] == b'NTSI':
            i = raw.find(b'DDS ')
            if i < 0: raise NotSupported('texture %s is a streaming stub without a header' % name)
            return dds.blank_from_header(raw[i:]), True
        raise NotSupported('texture %s has an unknown format' % name)

    def texture_status(self):
        """-> (ok, message): the three textures of the host material must be readable as DDS files or streaming stubs"""
        t = self.textures()
        for r in ROLES:
            if r not in t: return False, 'the material %s has no %s texture' % (self.host, r)
            try: self.template(t[r])
            except (NotSupported, ValueError) as ex: return False, str(ex)
        return True, ''

    # ------------------------------------------------------------ fit / build
    def reference_model(self): return self.model0

    def fit(self, user, up='+Y', forward=None, scale=1.0, adjust=None, edits=None, atlas_size=1024, log=print):
        return W.fit(self.model0, user, up=up, forward=forward, scale=scale, adjust=adjust, edits=edits, atlas_size=atlas_size, log=log)

    def build(self, fitted, textures=True, log=print):
        """-> (new .pac bytes, report)"""
        ok, why = self.texture_status()
        if textures and not ok: raise NotSupported(why)
        new_chunks = []; reports = []
        for k, ch in enumerate(self.chunks):
            out, rep = W.fill_fitting(ch, fitted, log=lambda *a, k=k: log('level of detail %d: %s' % (k, a[0]))); new_chunks.append(out); reports.append(rep)
        arch = bytearray(self.split.data); put = lambda e, data: arch.__setitem__(slice(e.offset, e.offset + e.size), data); grown = {}
        if bytes(self.blob[:8]) == needle.SIG_ARCHIVE:
            _, es = needle.parse(self.blob); it = iter(new_chunks)
            model_bytes = needle.build([(e.sig, e.name, next(it) if e.sig == needle.SIG_MODEL else e.data(self.blob)) for e in es])
        else: model_bytes = new_chunks[0]
        if len(model_bytes) != self.entry.size: raise ValueError('internal: the model changed size (%d -> %d)' % (self.entry.size, len(model_bytes)))
        put(self.entry, model_bytes)
        if textures:
            tex = self.textures(); atlas = np.asarray(fitted['atlas'], np.uint8)
            for r in ROLES:
                e = self.by_name[('dds', tex[r])]; tpl, stub = self.template(tex[r])
                data = dds.write_like(tpl, atlas) if r == 'abd' else dds.flat_like(tpl, NEUTRAL[r])
                if len(data) == e.size: put(e, data)
                else: grown[e.index] = data                                      # a streaming stub (a few hundred bytes) becomes a full texture: it needs new room at the end of the file data
            if grown: log('textures are streamed for this character: the full textures are written into the .pac instead')
            log('textures: %s replaced by your picture, %s flat, %s neutral' % (tex['abd'], tex['nrm'], tex['prm']))
        split_bytes = bytes(arch)
        if grown: split_bytes = innerwrite.append_entries(pacx.Inner(split_bytes, self.split_name), grown)
        return pacwrite.rebuild(self.pac, {self.split_name: split_bytes}), dict(levels=reports, host=self.host)
