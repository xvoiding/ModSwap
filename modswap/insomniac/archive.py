"""Spider-Man Remastered's archive files (asset_archive/g00s000 ...). Two kinds:

  'DSAR' archives   [b'DSAR' + header][block table from byte 32 to the u32 stored at byte 12][compressed blocks].
                    Each 32-byte table entry is  u64 position in the DECOMPRESSED stream, u64 position of the compressed block in the file,
                    u32 decompressed size (262,144 for a full block), u32 compressed size, u32 flags, u32 filler.
                    Blocks are LZ4 block-compressed. The toc's asset offsets are positions in the decompressed stream (so they can be larger than the
                    file on disk).
  plain files       anything else (for example the 'mods/...' archives ModSwap writes): the offset is a plain file position.
Nothing here writes to the game.
"""
import os
import numpy as np

DSAR = b'DSAR'


class Archive:
    def __init__(self, path):
        self.path = path; self.f = open(path, 'rb'); head = self.f.read(32)
        self.dsar = head[:4] == DSAR
        if self.dsar:
            import struct
            end = struct.unpack_from('<I', head, 12)[0]
            if end < 64 or (end - 32) % 32: raise ValueError('%s: odd DSAR block table end %d' % (os.path.basename(path), end))
            self.f.seek(32); t = np.frombuffer(self.f.read(end - 32), '<u4').reshape(-1, 8)
            self.n = len(t)
            self.real_off = t[:, 0].astype(np.uint64) | (t[:, 1].astype(np.uint64) << np.uint64(32))
            self.comp_off = t[:, 2].astype(np.uint64) | (t[:, 3].astype(np.uint64) << np.uint64(32))
            self.real_size = t[:, 4].astype(np.int64); self.comp_size = t[:, 5].astype(np.int64); self.flags = t[:, 6]
            self.length = int(self.real_off[-1]) + int(self.real_size[-1]) if self.n else 0

    def close(self): self.f.close()

    def _block(self, k):
        self.f.seek(int(self.comp_off[k])); comp = self.f.read(int(self.comp_size[k])); rs = int(self.real_size[k])
        if len(comp) != int(self.comp_size[k]): raise ValueError('%s: block %d is cut short' % (os.path.basename(self.path), k))
        if len(comp) == rs: return comp                                     # stored without compression
        import lz4.block
        try: out = lz4.block.decompress(comp, uncompressed_size=rs)
        except Exception as e: raise ValueError('%s: block %d (flags 0x%08X) would not decompress: %s' % (os.path.basename(self.path), k, int(self.flags[k]), e))
        return out

    def read(self, offset, size):
        """`size` bytes at `offset` of the (decompressed) stream"""
        if not self.dsar:
            self.f.seek(offset); data = self.f.read(size)
            if len(data) != size: raise ValueError('%s is shorter than the toc says' % os.path.basename(self.path))
            return data
        if size == 0: return b''
        if offset + size > self.length: raise ValueError('%s: bytes %d..%d are past the end of the archive (%d)' % (os.path.basename(self.path), offset, offset + size, self.length))
        k = int(np.searchsorted(self.real_off, np.uint64(offset), side='right')) - 1; out = bytearray(); end = offset + size
        while len(out) < size:
            blk = self._block(k); start = int(self.real_off[k]); a = max(offset, start) - start; b = min(end, start + len(blk)) - start
            out += blk[a:b]; k += 1
            if k >= self.n and len(out) < size: raise ValueError('ran out of blocks')
        return bytes(out)
