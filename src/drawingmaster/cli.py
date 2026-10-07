"""CLI for the drawing checker. Separate from scad2drawing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from drawingmaster import __version__
from drawingmaster.check import PROFILES, check_facts, facts_from_doc
from drawingmaster.dxf import DxfError, parse_dxf


def cmd_check(args: argparse.Namespace) -> None:
    path = Path(args.dxf)
    if not path.is_file():
        raise SystemExit(f"drawingmaster: no such file: {path}")
    try:
        doc = parse_dxf(path.read_text(encoding="utf-8", errors="replace"))
    except DxfError as exc:
        raise SystemExit(f"drawingmaster: {exc}") from exc
    findings = check_facts(facts_from_doc(doc), args.profile)
    payload = [
        {"severity": f.severity, "rule": f.rule, "message": f.message} for f in findings
    ]
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"profile": args.profile, "file": str(path), "findings": payload}, indent=2) + "\n")
    counts = {name: sum(1 for f in findings if f.severity == name) for name in ("error", "warning", "info")}
    print(f"drawingmaster: {args.profile} {path}")
    for item in payload:
        print(f"  {item['severity']:7} {item['rule']:28} {item['message']}")
    print(
        f"drawingmaster: {len(findings)} finding(s) "
        f"({counts['error']} error, {counts['warning']} warning, {counts['info']} info)"
    )
    if counts["error"] or (args.strict and counts["warning"]):
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drawingmaster",
        description="Flag DXF sheet, unit, projection, scale, and GD&T-syntax problems. "
        "Does not approve the part.",
    )
    parser.add_argument("--version", action="version", version=f"drawingmaster {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check", help="check one ASCII DXF")
    check.add_argument("dxf")
    check.add_argument("--profile", default="asme-ca", choices=PROFILES)
    check.add_argument("--json", dest="json_out", help="write findings JSON")
    check.add_argument("--strict", action="store_true", help="warnings also exit 1")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)
