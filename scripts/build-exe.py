#!/usr/bin/env python3
"""Build a standalone parliament CLI executable using PyInstaller.

Usage:
    python scripts/build-exe.py

Produces:
    dist/parliament          (Linux / macOS)
    dist/parliament.exe      (Windows)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    spec_file = root / "parliament.spec"

    if not spec_file.exists():
        print(f"Error: spec file not found at {spec_file}", file=sys.stderr)
        sys.exit(1)

    print("Building parliament CLI executable …")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file),
        ],
        cwd=str(root),
    )

    if result.returncode != 0:
        print("Build failed.", file=sys.stderr)
        sys.exit(result.returncode)

    # Report output
    dist = root / "dist"
    for name in ("parliament.exe", "parliament"):
        exe_path = dist / name
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nBuild complete: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
            return

    print("Build completed but executable not found in dist/", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
