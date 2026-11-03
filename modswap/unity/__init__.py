"""Unity game support (UnityPy based)."""
import sys, types

# UnityPy imports an audio library (fmod_toolkit) and an ASTC texture codec (astc_encoder, which needs archspec) the moment it saves a
# texture. ModSwap never converts audio or writes ASTC, and the Windows runtime does not ship what they need, so give UnityPy stand-ins
# instead of failing with "No module named 'fmod_toolkit'" / "'archspec'". (They only raise if something actually tries to use them.)
for _name, _what in (('fmod_toolkit', 'audio conversion'), ('astc_encoder', 'ASTC textures')):
    try: __import__(_name)
    except Exception:
        _m = types.ModuleType(_name)
        def _missing(attr, _what=_what, _name=_name): raise RuntimeError('%s is not available in ModSwap (%s)' % (_what, _name))
        _m.__getattr__ = _missing
        sys.modules[_name] = _m
