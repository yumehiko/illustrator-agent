"""Explicitly regenerate the checked-in product-swatch PNG fixture."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

from examples import BUILD_ROOT

DEFAULT_OUTPUT = BUILD_ROOT / "fixtures" / "product-swatch.png"


def product_swatch_png(*, width: int = 320, height: int = 220) -> bytes:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            distance = ((x - width * 0.52) ** 2 + (y - height * 0.48) ** 2) ** 0.5
            glow = max(0.0, 1.0 - distance / (width * 0.62))
            rows.extend(
                (
                    int(32 + 150 * glow),
                    int(55 + 105 * glow + 28 * x / width),
                    int(82 + 130 * (1 - y / height)),
                )
            )

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(bytes(rows), level=9)),
            chunk(b"IEND", b""),
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if not args.output.resolve().is_relative_to(BUILD_ROOT.resolve()):
        raise ValueError(f"fixture output must be under {BUILD_ROOT}")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing fixture: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(product_swatch_png())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
