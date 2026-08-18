#!/usr/bin/env python3
"""Extract ```mermaid fences from a 设计 Markdown and optionally render PNG.

    python extract_mermaid.py report.md -o /tmp/sdd_ota
    python extract_mermaid.py report.md -o /tmp/sdd_ota --render
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_markdown import dump_mermaid_files, extract_mermaid_blocks, lint_mermaid


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract mermaid blocks from Markdown 详设")
    ap.add_argument("markdown")
    ap.add_argument("-o", "--out-dir", required=True)
    ap.add_argument("--prefix", default="fig")
    ap.add_argument("--render", action="store_true", help="run mmdc if available")
    args = ap.parse_args()

    md = Path(args.markdown)
    if not md.is_file():
        print(f"not found: {md}", file=sys.stderr)
        return 1

    blocks = extract_mermaid_blocks(md)
    if not blocks:
        print("no mermaid fences found", file=sys.stderr)
        return 2

    failed = 0
    for i, src in enumerate(blocks, 1):
        for issue in lint_mermaid(src):
            print(f"fig_{i:02d}: {issue}", file=sys.stderr)
            failed += 1
    if failed:
        return 3

    written = dump_mermaid_files(md, args.out_dir, prefix=args.prefix)
    for p in written:
        print(p)

    if args.render:
        mmdc = shutil.which("mmdc")
        if not mmdc:
            print("mmdc not found; skip PNG render", file=sys.stderr)
            return 0
        for p in written:
            png = p.with_suffix(".png")
            subprocess.check_call(
                [mmdc, "-i", str(p), "-o", str(png), "-b", "white", "-s", "2"]
            )
            print(png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
