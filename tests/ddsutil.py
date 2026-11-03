import struct
def dds(w, h, data, fourcc):
    hdr = b'DDS ' + struct.pack('<7I', 124, 0x1007 | 0x80000, h, w, len(data), 0, 1) + b'\0' * 44
    hdr += struct.pack('<2I4s5I', 32, 4, fourcc, 0, 0, 0, 0, 0) + struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    assert len(hdr) == 128, len(hdr)
    return hdr + data
