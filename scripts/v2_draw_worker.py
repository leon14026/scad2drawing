#!/usr/bin/env python3
"""V2 drawing worker — run *inside* the locked draftwright env.

    uv run --directory envs/draftwright python scripts/v2_draw_worker.py \\
        --step part.step --out out/part --title "Part" --format pdf,svg

This file imports draftwright / build123d. Do not run it with Colab's
system Python. The scad2drawing CLI never imports those packages; it only
executes this script via `uv run --directory`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_formats(value: str) -> tuple[str, ...]:
    allowed = {"pdf", "svg", "dxf", "png"}
    out: list[str] = []
    for raw in value.split(","):
        tok = raw.strip().lower()
        if not tok:
            continue
        names = allowed if tok == "all" else (tok,)
        for name in names:
            if name not in allowed:
                raise SystemExit(f"v2_draw_worker: unknown format {tok!r}")
            if name not in out:
                out.append(name)
    if not out:
        raise SystemExit("v2_draw_worker: no output format")
    return tuple(out)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Import draftwright in the draw env and export a sheet.")
    p.add_argument("--step", required=True, help="input STEP")
    p.add_argument("--out", required=True, help="output prefix (no suffix)")
    p.add_argument("--title", default=None)
    p.add_argument("--number", default="DWG-001")
    p.add_argument("--format", dest="formats", default="pdf,svg")
    p.add_argument(
        "--auto-dims",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="False = views + title block only (mesh fail-soft)",
    )
    p.add_argument("--mesh-fallback", action="store_true", help="stamp the JSON report")
    args = p.parse_args(argv)

    step = Path(args.step)
    if not step.is_file():
        raise SystemExit(f"v2_draw_worker: missing STEP {step}")

    # Imported only inside the draftwright uv env.
    from draftwright import build_drawing

    formats = parse_formats(args.formats)
    title = args.title or step.stem
    dwg = build_drawing(
        step,
        title=title,
        number=args.number,
        auto_dims=args.auto_dims,
    )
    prefix = str(Path(args.out))
    paths = dwg.export(prefix, formats=formats)
    report_path = Path(prefix + ".draftwright.json")
    try:
        written = dwg.write_report(str(report_path))
        report_path = Path(written)
    except Exception as exc:  # noqa: BLE001 — worker must still emit files
        print(f"v2_draw_worker: report skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        report_path = None
    if args.mesh_fallback and report_path and report_path.is_file():
        try:
            data = json.loads(report_path.read_text())
        except json.JSONDecodeError:
            data = {}
        data.setdefault("scad2drawing", {})["mesh_fallback"] = True
        report_path.write_text(json.dumps(data, indent=2) + "\n")
    for fmt, path in (paths.items() if isinstance(paths, dict) else []):
        print(path)
    if isinstance(paths, dict):
        return
    # Older export tuple
    if isinstance(paths, (tuple, list)):
        for path in paths:
            print(path)


if __name__ == "__main__":
    main()
