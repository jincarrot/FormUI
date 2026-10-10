"""Generate the demo's exact, white square outline as a transparent RGBA PNG.

Uses only the Python standard library. Run from any directory:
    python tools/generate_square_texture.py
The two runtime images share this texture and use native UI color tinting.
"""
from pathlib import Path
import struct
import zlib


def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack(
        '>I', zlib.crc32(kind + payload) & 0xffffffff)


def make_square(size=256, stroke=4):
    rows = []
    for y in range(size):
        row = bytearray([0])  # PNG scanline filter: none
        for x in range(size):
            edge = min(x, y, size - 1 - x, size - 1 - y) < stroke
            row.extend((255, 255, 255, 255 if edge else 0))
        rows.append(bytes(row))
    header = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) +
            chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[1] / 'resource/textures/ui/square.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_square())
    print(path)
