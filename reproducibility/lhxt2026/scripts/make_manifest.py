#!/usr/bin/env python
"""Write SHA-256 checksums for the public reproducibility package."""

from __future__ import annotations

import hashlib
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent.parent
MANIFEST = PACKAGE_DIR / "MANIFEST.sha256"
EXCLUDED = {MANIFEST.name}


def main() -> None:
    lines = []
    for path in sorted(PACKAGE_DIR.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or path.name in EXCLUDED or "__pycache__" in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(PACKAGE_DIR).as_posix()}")
    MANIFEST.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Manifiesto generado: {MANIFEST}")


if __name__ == "__main__":
    main()
