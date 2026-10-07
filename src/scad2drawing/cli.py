"""stdlib argparse front-end. Shells out to uv; never imports CAD libraries."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scad2drawing import __version__
from scad2drawing.commands import (
    DefineError,
    default_env_root,
    defines_for_part,
    draftwright_cmd,
    draw_env_dir,
    draw_worker_cmd,
    git_clone_cmd,
    mesh_fallback_lines,
    output_stem,
    parse_defines,
    parse_parts,
    scad2step_cmd,
    scad_env_dir,
    uv_sync_cmd,
    worker_script,
)
from scad2drawing.pins import DRAFTWRIGHT, SCAD123D, samples_dir


def _run(
    cmd: list[str], *, log: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if log is not None:
        log.write_text(proc.stdout + proc.stderr)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if check and proc.returncode != 0:
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


def os_env_openscad() -> bool:
    return bool(os.environ.get("SCAD123D_OPENSCAD"))


def convert_one(
    *,
    scad: Path,
    out_dir: Path,
    defines: list[str],
    title: str | None,
    number: str,
    formats: str,
    timeout: float,
    skip_step: bool,
    skip_draw: bool,
    scad_env: Path,
    draw_env: Path,
    on_mesh: str,
    draw: str,
    check: bool,
) -> str:
    """Run one SCAD → STEP → drawing. Returns status: ok, mesh-warned, skipped-draw, failed."""
    stem = output_stem(scad, defines)
    step = out_dir / f"{stem}.step"
    prefix = out_dir / stem
    log = out_dir / f"{stem}.scad2step.log"
    mesh_note = out_dir / f"{stem}.MESH_FALLBACK.txt"
    hits: list[str] = []

    if not skip_step:
        _check_env(scad_env, "scad123d")
        proc = _run(
            scad2step_cmd(scad_env, scad, step, defines, timeout=timeout),
            log=log,
            check=False,
        )
        hits = mesh_fallback_lines(proc.stderr)
        if proc.returncode != 0:
            print(f"scad2drawing: convert failed for {stem}", file=sys.stderr)
            if check:
                raise SystemExit(proc.returncode)
            return "failed"
        if hits:
            mesh_note.write_text("\n".join(hits) + "\n")
            print("scad2drawing: MESH FALLBACK — drawings may show faceted edges:", file=sys.stderr)
            for line in hits:
                print(f"  {line}", file=sys.stderr)
            if on_mesh == "fail":
                if check:
                    raise SystemExit(2)
                return "failed"
        if not step.is_file() or step.stat().st_size == 0:
            msg = f"scad2drawing: STEP was not written: {step}"
            if check:
                raise SystemExit(msg)
            print(msg, file=sys.stderr)
            return "failed"
        print(f"scad2drawing: wrote {step}")

    skip_this_draw = skip_draw or (hits and on_mesh == "skip-draw")
    if skip_this_draw:
        if hits and on_mesh == "skip-draw":
            print(f"scad2drawing: skipping drawing for {stem} (--on-mesh skip-draw)", file=sys.stderr)
        return "skipped-draw" if hits else "ok"

    _check_env(draw_env, "draftwright")
    if not step.is_file():
        msg = f"scad2drawing: missing STEP {step}"
        if check:
            raise SystemExit(msg)
        print(msg, file=sys.stderr)
        return "failed"

    label = title or stem.replace("_", " ")
    auto_dims = not (hits and on_mesh == "views-only")
    if not auto_dims:
        print(f"scad2drawing: views-only drawing for {stem} (mesh fallback)", file=sys.stderr)

    if draw == "cli":
        proc = _run(
            draftwright_cmd(
                draw_env, step, prefix, title=label, number=number, formats=formats
            ),
            check=False,
        )
    else:
        worker = worker_script()
        if not worker.is_file():
            raise SystemExit(f"scad2drawing: missing V2 worker {worker}")
        proc = _run(
            draw_worker_cmd(
                draw_env,
                worker,
                step,
                prefix,
                title=label,
                number=number,
                formats=formats,
                auto_dims=auto_dims,
                mesh_fallback=bool(hits),
            ),
            check=False,
        )
    if proc.returncode != 0:
        if check:
            raise SystemExit(proc.returncode)
        return "failed"
    print(f"scad2drawing: drawing prefix {prefix}")
    return "mesh-warned" if hits else "ok"


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
        parts = parse_parts(getattr(args, "parts", None))
    except DefineError as exc:
        raise SystemExit(f"scad2drawing: {exc}") from exc

    scad = Path(args.scad).resolve()
    if not scad.is_file():
        raise SystemExit(f"scad2drawing: no such file: {scad}")

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scad_env = Path(args.scad_env).resolve() if args.scad_env else scad_env_dir()
    draw_env = Path(args.draw_env).resolve() if args.draw_env else draw_env_dir()
    keep_going = bool(getattr(args, "keep_going", False) or parts)
    jobs = parts or [None]
    statuses: list[str] = []

    for i, part in enumerate(jobs, start=1):
        job_defines = defines_for_part(defines, part) if part else defines
        stem_hint = part or output_stem(scad, job_defines)
        title = args.title
        if title and part and "{part}" in title:
            title = title.replace("{part}", part)
        elif title is None and part:
            title = part
        number = args.number
        if parts:
            if "{part}" in number:
                number = number.replace("{part}", part or "")
            elif number == "DWG-001":
                number = f"DWG-{i:03d}"
        print(f"scad2drawing: job {i}/{len(jobs)} {stem_hint}", file=sys.stderr)
        statuses.append(
            convert_one(
                scad=scad,
                out_dir=out_dir,
                defines=job_defines,
                title=title,
                number=number,
                formats=args.formats,
                timeout=args.timeout,
                skip_step=args.skip_step,
                skip_draw=args.skip_draw,
                scad_env=scad_env,
                draw_env=draw_env,
                on_mesh=getattr(args, "on_mesh", "warn"),
                draw=getattr(args, "draw", "worker"),
                check=not keep_going,
            )
        )

    failed = sum(1 for s in statuses if s == "failed")
    print(f"scad2drawing: done {len(statuses)} job(s), {failed} failed ({', '.join(statuses)})")
    if failed:
        raise SystemExit(1)


def cmd_smoke(args: argparse.Namespace) -> None:
    cube = samples_dir() / "cube.scad"
    ns = argparse.Namespace(
        scad=str(cube),
        out=args.out,
        defines=[],
        parts=None,
        title="Smoke cube",
        number="SMOKE-001",
        formats=args.formats,
        timeout=args.timeout,
        skip_step=False,
        skip_draw=args.skip_draw,
        scad_env=args.scad_env,
        draw_env=args.draw_env,
        on_mesh="warn",
        draw=getattr(args, "draw", "worker"),
        keep_going=False,
    )
    cmd_convert(ns)


def add_convert_flags(c: argparse.ArgumentParser) -> None:
    c.add_argument("-o", "--out", default="out", help="output directory")
    c.add_argument(
        "-D",
        dest="defines",
        action="append",
        default=[],
        metavar="name=value",
        help="OpenSCAD override (repeatable). Use part=frame not quoted values.",
    )
    c.add_argument(
        "--parts",
        default=None,
        help="comma-separated selector values (V2). Loops -D part=NAME for each.",
    )
    c.add_argument("--title", default=None, help="title block; use {part} in batch")
    c.add_argument("--number", default="DWG-001", help="drawing number; {part} or DWG-001,002…")
    c.add_argument("--formats", default="pdf,svg")
    c.add_argument("--timeout", type=float, default=600)
    c.add_argument("--skip-step", action="store_true")
    c.add_argument("--skip-draw", action="store_true")
    c.add_argument("--scad-env", default=None)
    c.add_argument("--draw-env", default=None)
    c.add_argument(
        "--on-mesh",
        choices=("warn", "views-only", "skip-draw", "fail"),
        default="warn",
        help="V2 fail-soft when scad123d mesh-fallbacks (default: warn and still draw)",
    )
    c.add_argument(
        "--draw",
        choices=("worker", "cli"),
        default="worker",
        help="worker = import draftwright in the draw env (V2); cli = draftwright CLI (V1)",
    )
    c.add_argument(
        "--keep-going",
        action="store_true",
        help="do not stop the batch on the first failure (implied by --parts)",
    )


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
    add_convert_flags(c)
    c.set_defaults(func=cmd_convert)

    s = sub.add_parser("smoke", help="convert samples/cube.scad")
    s.add_argument("-o", "--out", default="out")
    s.add_argument("--formats", default="pdf,svg")
    s.add_argument("--timeout", type=float, default=120)
    s.add_argument("--skip-draw", action="store_true")
    s.add_argument("--scad-env", default=None)
    s.add_argument("--draw-env", default=None)
    s.add_argument("--draw", choices=("worker", "cli"), default="worker")
    s.set_defaults(func=cmd_smoke)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
