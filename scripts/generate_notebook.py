#!/usr/bin/env python3
"""Write notebooks/scad2drawing.ipynb (stdlib json; no nbformat required)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "scad2drawing.ipynb"

MD = "markdown"
CODE = "code"


def cell(kind: str, source: str) -> dict:
    lines = source.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return {
        "cell_type": kind,
        "metadata": {},
        "source": lines,
        **(
            {
                "execution_count": None,
                "outputs": [],
            }
            if kind == CODE
            else {}
        ),
    }


CELLS = [
    cell(
        MD,
        """# scad2drawing (Colab V1)

OpenSCAD `.scad` → STEP (`scad2step`) → dimensioned PDF/SVG (`draftwright`).

This notebook **calls** those tools in two locked `uv` environments. It does not `pip install` CAD wheels into Colab's system Python and does not `import draftwright`.

Pins live in the `scad2drawing` repo (`pins.toml`). Upstream licenses: scad123d MIT, draftwright AGPL-3.0. See `LEGAL.md`.

After a runtime reset, rerun from cell 1.""",
    ),
    cell(
        CODE,
        r"""# Cell 1 — OpenSCAD (CSG export does not need a display)
import os, shutil, subprocess, sys
from pathlib import Path

WORK = Path("/content/work")
ENV_ROOT = Path("/content/envs")
SCAD_ENV = ENV_ROOT / "scad123d"
DRAW_ENV = ENV_ROOT / "draftwright"
WORK.mkdir(parents=True, exist_ok=True)
ENV_ROOT.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print("+", cmd if isinstance(cmd, str) else " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)

if shutil.which("openscad") is None:
    sh("apt-get update -qq", shell=True)
    sh("apt-get install -y -qq openscad", shell=True)
sh(["openscad", "--version"])""",
    ),
    cell(
        CODE,
        r"""# Cell 2 — uv (not uvx for CAD stacks)
if shutil.which("uv") is None:
    sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
sh(["uv", "--version"])""",
    ),
    cell(
        CODE,
        r"""# Cell 3 — optional BOSL2 (skip if your model does not include it)
BOSL = Path("/root/.local/share/OpenSCAD/libraries/BOSL2")
if not (BOSL / "std.scad").is_file():
    BOSL.parent.mkdir(parents=True, exist_ok=True)
    sh(["git", "clone", "--depth", "1",
        "https://github.com/BelfrySCAD/BOSL2.git", str(BOSL)])
print("BOSL2", "ok" if (BOSL / "std.scad").is_file() else "MISSING")""",
    ),
    cell(
        CODE,
        r"""# Cell 4 — locked scad123d (their uv.lock). Never uvx scad2step.
SCAD123D_REPO = "https://github.com/etjones/scad123d.git"
SCAD123D_REV = "85811a1a9daa291fb9ebfdfd8339322a9ec5b52c"

def materialize(repo, dest: Path, rev: str):
    if not (dest / ".git").exists():
        if dest.exists():
            shutil.rmtree(dest)
        sh(["git", "clone", "--depth", "1", repo, str(dest)])
    sh(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", rev])
    sh(["git", "-C", str(dest), "checkout", "--quiet", "FETCH_HEAD"])
    sh(["uv", "sync", "--directory", str(dest)])

materialize(SCAD123D_REPO, SCAD_ENV, SCAD123D_REV)
sh(["uv", "run", "--directory", str(SCAD_ENV), "scad2step", "--help"],
   stdout=subprocess.DEVNULL)""",
    ),
    cell(
        CODE,
        r"""# Cell 5 — locked draftwright (AGPL-3.0, official CLI only)
DRAW_REPO = "https://github.com/pzfreo/draftwright.git"
DRAW_REV = "v0.4.35"
materialize(DRAW_REPO, DRAW_ENV, DRAW_REV)
sh(["uv", "run", "--directory", str(DRAW_ENV), "draftwright", "--help"],
   stdout=subprocess.DEVNULL)""",
    ),
    cell(
        CODE,
        r"""# Cell 6 — smoke cube (separates env failures from model failures)
smoke = WORK / "cube.scad"
smoke.write_text("cube([10, 20, 30]);\n")
step = WORK / "cube.step"
sh(["uv", "run", "--directory", str(SCAD_ENV), "scad2step",
    str(smoke), "-o", str(step), "--timeout", "120"])
print(step, step.stat().st_size, "bytes")
assert step.stat().st_size > 0""",
    ),
    cell(
        CODE,
        r"""# Cell 7 — upload your project into /content/work (not into the git clones)
from google.colab import files
print("Upload .scad / zip / local libraries, then run the next cell.")
uploaded = files.upload()
for name in uploaded:
    target = WORK / Path(name).name
    target.write_bytes(uploaded[name])
    print("saved", target)
# If you uploaded a zip:
# !unzip -o /content/work/YOUR_PROJECT.zip -d /content/work/YOUR_PROJECT""",
    ),
    cell(
        CODE,
        r"""# Cell 8 — convert a selected part to STEP
# Use bare -D values: part=frame  (not part='"frame"')
MODEL = WORK / "YOUR_MODEL.scad"   # change me
DEFINES = ["part=YOUR_PART"]       # or [] if the file has no selector
OUT_STEM = "YOUR_PART"

step_path = WORK / f"{OUT_STEM}.step"
cmd = ["uv", "run", "--directory", str(SCAD_ENV), "scad2step",
       str(MODEL), "-o", str(step_path), "--timeout", "600"]
for d in DEFINES:
    cmd.extend(["-D", d])
proc = subprocess.run(cmd, text=True, capture_output=True)
sys.stderr.write(proc.stderr)
if proc.returncode:
    raise SystemExit(proc.returncode)
log = WORK / f"{OUT_STEM}.scad2step.log"
log.write_text(proc.stderr)
if "mesh" in proc.stderr.lower() and "fallback" in proc.stderr.lower():
    print("WARNING: mesh fallback — inspect this STEP before trusting dimensions")
print(step_path, step_path.stat().st_size, "bytes")""",
    ),
    cell(
        CODE,
        r"""# Cell 9 — drawing (draftwright CLI in its own env)
prefix = WORK / OUT_STEM
sh(["uv", "run", "--directory", str(DRAW_ENV), "draftwright",
    str(step_path), "--out", str(prefix),
    "--format", "pdf,svg", "--title", OUT_STEM, "--number", "DWG-001"])
for p in sorted(WORK.glob(OUT_STEM + ".*")):
    print(p.name, p.stat().st_size)""",
    ),
    cell(
        CODE,
        r"""# Cell 10 — download
from google.colab import files as colab_files
bundle = WORK / "drawings.zip"
payload = [p for p in WORK.glob(OUT_STEM + ".*") if p.suffix != ".scad"]
sh(["zip", "-j", str(bundle), *map(str, payload)])
colab_files.download(str(bundle))""",
    ),
    cell(
        MD,
        """## Troubleshooting

| Symptom | Fix |
|---|---|
| `openscad: command not found` | Runtime reset; rerun cell 1 |
| `Cannot open include file` | Clone the library into `/root/.local/share/OpenSCAD/libraries` |
| `OCP TopTools ImportError` | You used `uvx` or system pip. Use cells 4–5 (`uv sync` in the clone) |
| OpenSCAD parse error after `-D` | `part=frame`, not nested quotes |
| One fused body | Export with `-D part=…` per component; don't draw the unioned assembly |
| Mesh fallback / `hull()` | Warning is expected on `hull_fallback.scad`; inspect faces |
| Drawing hides vs Part Studio | That was Onshape. This notebook only makes a sheet from one STEP |

Onshape remains the place for mates, motion, and assembly balloons. This notebook replaces the *manual drawing tab* for a single part.
""",
    ),
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": CELLS,
    }
    OUT.write_text(json.dumps(nb, indent=1) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
