"""Generate placeholder solid-color PNG icons for the extension manifest.

Uses only the standard library (struct + zlib) so it needs no extra dependencies.
Replace these with real designed icons before shipping.
"""

import struct
import zlib
from pathlib import Path

SIZES = (16, 48, 128)
COLOR = (37, 99, 235, 255)  # blue-600
OUT_DIR = Path(__file__).resolve().parent.parent / "apps" / "chrome-extension" / "src" / "assets"


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def make_png(size: int, color: tuple[int, int, int, int]) -> bytes:
    row = bytes(color) * size
    raw = b"".join(b"\x00" + row for _ in range(size))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = OUT_DIR / f"icon-{size}.png"
        path.write_bytes(make_png(size, COLOR))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
