"""Build argv for the two upstream CLIs. No CAD imports — stdlib only."""

from __future__ import annotations

import os
import re
from pathlib import Path

MESH_HINTS = (
    "mesh fallback",
    "MeshFallback",
    "falling back to mesh",
    "no BRep equivalent",
    "no closed form",
)

_NESTED_QUOTES = re.compile(r"""^["'].*|.*["']$""")


class DefineError(ValueError):
    pass


def parse_defines(items: list[str]) -> list[str]:
    """Validate OpenSCAD ``-D name=value`` tokens. Pass values bare (``part=frame``)."""
    out: list[str] = []
    for raw in items:
        if "=" not in raw:
            raise DefineError(f"-D expects name=value, got {raw!r}")
        name, _, value = raw.partition("=")
        name = name.strip()
        if not name:
            raise DefineError(f"-D expects name=value, got {raw!r}")
        if _NESTED_QUOTES.match(value.strip()):
            raise DefineError(
                f"refusing quoted -D value {raw!r}; use -D part=frame not nested quotes"
            )
        out.append(f"{name}={value}")
    return out


def part_from_defines(defines: list[str]) -> str | None:
    for item in defines:
        name, _, value = item.partition("=")
        if name == "part":
            return value
    return None


def output_stem(scad: Path, defines: list[str]) -> str:
    part = part_from_defines(defines)
    if part:
        return f"{scad.stem}_{part}"
    return scad.stem


def scad2step_cmd(
    env: Path,
    scad: Path,
    step: Path,
    defines: list[str],
    *,
    timeout: float = 600,
) -> list[str]:
    cmd = [
        "uv",
        "run",
        "--directory",
        str(env),
        "scad2step",
        str(scad),
        "-o",
        str(step),
        "--timeout",
        str(timeout),
    ]
    for item in defines:
        cmd.extend(["-D", item])
    return cmd


def draftwright_cmd(
    env: Path,
    step: Path,
    out_prefix: Path,
    *,
    title: str | None = None,
    number: str = "DWG-001",
    formats: str = "pdf,svg",
) -> list[str]:
    cmd = [
        "uv",
        "run",
        "--directory",
        str(env),
        "draftwright",
        str(step),
        "--out",
        str(out_prefix),
        "--format",
        formats,
        "--number",
        number,
    ]
    if title:
        cmd.extend(["--title", title])
    return cmd


def git_clone_cmd(repo: str, dest: Path, rev: str) -> list[list[str]]:
    """Clone *repo* then fetch/checkout *rev* (tag or SHA). Depth-1 to keep Colab light."""
    dest_s = str(dest)
    return [
        ["git", "clone", "--depth", "1", repo, dest_s],
        ["git", "-C", dest_s, "fetch", "--depth", "1", "origin", rev],
        ["git", "-C", dest_s, "checkout", "--quiet", "FETCH_HEAD"],
    ]


def uv_sync_cmd(env: Path) -> list[str]:
    return ["uv", "sync", "--directory", str(env)]


def parse_parts(raw: str | None) -> list[str]:
    """Comma-separated ``--parts frame,shaft`` list. Empty → []."""
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if any("=" in p or " " in p for p in parts):
        raise DefineError(f"--parts expects comma-separated names, got {raw!r}")
    return parts


def defines_for_part(base: list[str], part: str | None) -> list[str]:
    """Replace or add ``part=`` while keeping other -D flags."""
    rest = [d for d in base if not d.startswith("part=")]
    if part:
        rest.append(f"part={part}")
    return rest


def draw_worker_cmd(
    env: Path,
    worker: Path,
    step: Path,
    out_prefix: Path,
    *,
    title: str | None = None,
    number: str = "DWG-001",
    formats: str = "pdf,svg",
    auto_dims: bool = True,
    mesh_fallback: bool = False,
) -> list[str]:
    cmd = [
        "uv",
        "run",
        "--directory",
        str(env),
        "python",
        str(worker),
        "--step",
        str(step),
        "--out",
        str(out_prefix),
        "--format",
        formats,
        "--number",
        number,
    ]
    if title:
        cmd.extend(["--title", title])
    if auto_dims:
        cmd.append("--auto-dims")
    else:
        cmd.append("--no-auto-dims")
    if mesh_fallback:
        cmd.append("--mesh-fallback")
    return cmd


def worker_script() -> Path:
    from scad2drawing.pins import ROOT

    return ROOT / "scripts" / "v2_draw_worker.py"


def mesh_fallback_lines(stderr: str) -> list[str]:
    hits = []
    for line in stderr.splitlines():
        if any(h.lower() in line.lower() for h in MESH_HINTS):
            hits.append(line.strip())
    return hits


def default_env_root() -> Path:
    override = os.environ.get("SCAD2DRAWING_ENV_ROOT")
    if override:
        return Path(override)
    return Path.cwd() / "envs"


def scad_env_dir(root: Path | None = None) -> Path:
    override = os.environ.get("SCAD2DRAWING_SCAD_ENV")
    if override:
        return Path(override)
    return (root or default_env_root()) / "scad123d"


def draw_env_dir(root: Path | None = None) -> Path:
    override = os.environ.get("SCAD2DRAWING_DRAW_ENV")
    if override:
        return Path(override)
    return (root or default_env_root()) / "draftwright"
