"""Entry point for the make.fun news-image-20261123 competition.

The image is rendered by draw.py (Pillow, from figures.json and the
story table) and stored in this repository as entry.png. This program
simply delivers those exact bytes to the output directory the
competition expects, using only the standard library.

Output directory: the MAKEFUN_OUTPUT_DIR environment variable when
set, otherwise /output. The written file is verified byte-for-byte
against the repository copy before the program reports success.
"""

import hashlib
import os
import shutil
import sys

SOURCE = "entry.png"
TARGET = "entry.png"


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    target = os.path.join(out_dir, TARGET)

    with open(source, "rb") as handle:
        expected = hashlib.sha256(handle.read()).hexdigest()

    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(source, target)

    with open(target, "rb") as handle:
        actual = hashlib.sha256(handle.read()).hexdigest()
    if actual != expected:
        print(f"main.py: verification failed for {target}", file=sys.stderr)
        return 1

    size = os.path.getsize(target)
    print(f"main.py: wrote {target} ({size} bytes, sha256 {actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
