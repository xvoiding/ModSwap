"""Make a file inside an inner PACx archive BIGGER (or give it new bytes of any size) without moving anything else.

An inner archive is  header | trees | dependencies | data entries | strings | FILE DATA | offset table. The offset table lists the positions of the pointer fields, and every one of them
lies in the front part (checked on the real files), so appending new file data at the END of the file-data area only moves the offset table: the entry gets a new size and a new data
pointer, the old bytes stay behind as dead space, and the header's file size and file-data size grow. Nothing else changes."""
import struct
from . import pacx


def append_entries(inner, new, align=16):
    """inner: a pacx.Inner. new: {entry index: bytes}. -> the new archive bytes"""
    d = inner.data; h = list(pacx.V3.unpack_from(d, 0)); trees, deps, dents, strs, fdata, offt = h[4:10]
    fd_start = 0x30 + trees + deps + dents + strs; offt_at = fd_start + fdata
    if offt_at + offt != len(d): raise ValueError('inner archive layout does not add up (%d + %d != %d)' % (offt_at, offt, len(d)))
    body = bytearray(d[:offt_at]); tail = bytes(d[offt_at:])
    for idx, blob in sorted(new.items()):
        e = inner.ent0 + 0x30 * idx
        if inner.entries[idx].is_proxy: raise ValueError('entry %d is only a pointer to another archive' % idx)
        body += b'\0' * ((-len(body)) % align); pos = len(body); body += blob
        struct.pack_into('<I', body, e + 4, len(blob)); struct.pack_into('<Q', body, e + 16, pos)
    body += b'\0' * ((-len(body)) % 8)
    h[8] = len(body) - fd_start; h[3] = len(body) + len(tail); pacx.V3.pack_into(body, 0, *h)
    return bytes(body) + tail


def append_blob(data, blob, align=8):
    """append raw bytes at the end of an inner archive's file-data area (e.g. a longer chunk table). -> (new archive bytes, position of the blob)"""
    d = bytes(data); h = list(pacx.V3.unpack_from(d, 0)); trees, deps, dents, strs, fdata, offt = h[4:10]
    fd_start = 0x30 + trees + deps + dents + strs; offt_at = fd_start + fdata
    body = bytearray(d[:offt_at]); tail = d[offt_at:]; body += b'\0' * ((-len(body)) % align); pos = len(body); body += blob; body += b'\0' * ((-len(body)) % 8)
    h[8] = len(body) - fd_start; h[3] = len(body) + len(tail); pacx.V3.pack_into(body, 0, *h)
    return bytes(body) + tail, pos
