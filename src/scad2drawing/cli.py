"""stdlib argparse front-end. Shells out to uv; never imports CAD libraries."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from scad2drawing import __version__
from scad2drawing.commands import (
    DefineError,
    default_env_root,
    draftwright_cmd,
    draw_env_dir,
    git_clone_cmd,
    mesh_fallback_lines,
    output_stem,
    parse_defines,
    scad2step_cmd,
    scad_env_dir,
    uv_sync_cmd,
)
from scad2drawing.pins import DRAFTWRIGHT, SCAD123D, samples_dir


def _run(cmd: list[str], *, log: Path | None = None) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if log is not None:
        log.write_text(proc.stdout + proc.stderr)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc


def _require(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"scad2drawing: {name} not found on PATH")


def cmd_bootstrap(args: argparse.Namespace) -> None:
    _require("git")
    _require("uv")
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    pairs = (
        (SCAD123D, root / "scad123d"),
        (DRAFTWRIGHT, root / "draftwright"),
    )
    for pin, dest in pairs:
        if dest.exists() and (dest / "pyproject.toml").exists():
            print(f"scad2drawing: using existing {dest}", file=sys.stderr)
        else:
            if dest.exists():
                shutil.rmtree(dest)
            for cmd in git_clone_cmd(pin.repo, dest, pin.rev):
                _run(cmd)
        _run(uv_sync_cmd(dest))
    print(f"scad2drawing: envs ready under {root}")


def _check_env(path: Path, tool: str) -> None:
    if not (path / "pyproject.toml").is_file():
        raise SystemExit(
            f"scad2drawing: {tool} env not found at {path}\n"
            f"  run: scad2drawing bootstrap --root {path.parent}"
        )


def cmd_convert(args: argparse.Namespace) -> None:
    _require("uv")
    if shutil.which("openscad") is None and not os_env_openscad():
        print(
            "scad2drawing: warning: `openscad` not on PATH "
            "(set SCAD123D_OPENSCAD if it lives elsewhere)",
            file=sys.stderr,
        )
    try:
        defines = parse_defines(args.defines or [])
    except DefineError as exc:
        raise SystemExit(f"scad2drawing: {exc}") from exc

    scad = Path(args.scad).resolve()
    if not scad.is_file():
        raise SystemExit(f"scad2drawing: no such file: {scad}")

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(scad, defines)
    step = out_dir / f"{stem}.step"
    prefix = out_dir / stem
    log = out_dir / f"{stem}.scad2step.log"

    scad_env = Path(args.scad_env).resolve() if args.scad_env else scad_env_dir()
    draw_env = Path(args.draw_env).resolve() if args.draw_env else draw_env_dir()

    if not args.skip_step:
        _check_env(scad_env, "scad123d")
        proc = _run(scad2step_cmd(scad_env, scad, step, defines, timeout=args.timeout), log=log)
        hits = mesh_fallback_lines(proc.stderr)
        if hits:
            print("scad2drawing: MESH FALLBACK — drawings may show faceted edges:", file=sys.stderr)
            for line in hits:
                print(f"  {line}", file=sys.stderr)
        if not step.is_file() or step.stat().st_size == 0:
            raise SystemExit(f"scad2drawing: STEP was not written: {step}")
        print(f"scad2drawing: wrote {step}")

    if args.skip_draw:
        return

    _check_env(draw_env, "draftwright")
    if not step.is_file():
        raise SystemExit(f"scad2drawing: missing STEP {step}")
    title = args.title or stem.replace("_", " ")
    _run(
        draftwright_cmd(
            draw_env,
            step,
            prefix,
            title=title,
            number=args.number,
            formats=args.formats,
        )
    )
    print(f"scad2drawing: drawing prefix {prefix}")


def os_env_openscad() -> bool:
    import os

    return bool(os.environ.get("SCAD123D_OPENSCAD"))


def cmd_smoke(args: argparse.Namespace) -> None:
    cube = samples_dir() / "cube.scad"
    ns = argparse.Namespace(
        scad=str(cube),
        out=args.out,
        defines=[],
        title="Smoke cube",
        number="SMOKE-001",
        formats=args.formats,
        timeout=args.timeout,
        skip_step=False,
        skip_draw=args.skip_draw,
        scad_env=args.scad_env,
        draw_env=args.draw_env,
    )
    cmd_convert(ns)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scad2drawing",
        description="Convert an OpenSCAD file to STEP and a dimensioned drawing "
        "using locked scad123d and draftwright environments (subprocess, not import).",
    )
    p.add_argument("--version", action="version", version=f"scad2drawing {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bootstrap", help="clone pinned upstream repos and uv sync")
    b.add_argument(
        "--root",
        default=str(default_env_root()),
        help="directory that will contain scad123d/ and draftwright/ clones",
    )
    b.set_defaults(func=cmd_bootstrap)

    c = sub.add_parser("convert", help="scad → step → pdf/svg")
    c.add_argument("scad", help="input .scad file")
    c.add_argument("-o", "--out", default="out", help="output directory")
    c.add_argument(
        "-D",
        dest="defines",
        action="append",
        default=[],
        metavar="name=value",
        help="OpenSCAD override (repeatable). Use part=frame not quoted values.",
    )
    c.add_argument("--title", default=None)
    c.add_argument("--number", default="DWG-001")
    c.add_argument("--formats", default="pdf,svg")
    c.add_argument("--timeout", type=float, default=600)
    c.add_argument("--skip-step", action="store_true")
    c.add_argument("--skip-draw", action="store_true")
    c.add_argument("--scad-env", default=None)
    c.add_argument("--draw-env", default=None)
    c.set_defaults(func=cmd_convert)

    s = sub.add_parser("smoke", help="convert samples/cube.scad")
    s.add_argument("-o", "--out", default="out")
    s.add_argument("--formats", default="pdf,svg")
    s.add_argument("--timeout", type=float, default=120)
    s.add_argument("--skip-draw", action="store_true")
    s.add_argument("--scad-env", default=None)
    s.add_argument("--draw-env", default=None)
    s.set_defaults(func=cmd_smoke)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
