# Gemini in Colab SOP — scad2drawing V2

Use this file as the **instruction pack** in Google Colab (Gemini side panel, “Help me code”, or a chat that writes cells).

**Easiest path**

1. CPU runtime (GPU unused).
2. Open `notebooks/scad2drawing_v2.ipynb` (File → Upload if the GitHub repo is private).
3. Upload **this file** into Colab too, or clone the glue repo so it lands at `/content/scad2drawing/GEMINI_COLAB_SOP_V2.md`.
4. Tell Gemini: *Follow GEMINI_COLAB_SOP_V2.md exactly. Do not invent a shorter install.*
5. Edit only the **CONFIG** cell. Runtime → Run all.
6. After a runtime reset, start again at Cell 1.

Preferred: fill CONFIG and run cells. Do not let Gemini rewrite setup.

V1 SOP (raw `uv run draftwright` CLI): `GEMINI_COLAB_SOP.md`. This V2 file is the one to use now.

---

## Paste into Gemini (system)

```text
You are setting up and running scad2drawing V2 in Google Colab.

Goal: .scad → STEP → dimensioned PDF/SVG, with unique drawing numbers,
SVG kept, and draftwright lint (needs-attention) printed.

You MUST:
- Clone or upload the scad2drawing glue repo, then pip install -e that repo
  (stdlib glue only — not CAD wheels into Colab's system Python).
- Two locked uv environments via: scad2drawing bootstrap --root /content/envs
    /content/envs/scad123d     →  scad2step
    /content/envs/draftwright  →  V2 worker (import draftwright in THAT env only)
- Work files in /content/work. Never %cd into the git clones.
- Convert with the glue CLI, default --draw worker:
    scad2drawing convert MODEL.scad -o /content/work/out \
      --parts a,b --title "{part}" --number "DWG-{part}" --on-mesh warn
- Set SCAD2DRAWING_SCAD_ENV / SCAD2DRAWING_DRAW_ENV or pass --scad-env/--draw-env.

FORBIDDEN:
- uvx scad2step, uvx draftwright, uvx anything CAD
- pip install scad123d / draftwright / build123d / cadquery-ocp into Colab's system Python
- import scad123d or import draftwright in the notebook kernel
  (the worker may import draftwright only as uv run --directory DRAW_ENV python …/v2_draw_worker.py)
- mixing both CAD tools in one venv
- nested quotes on -D (no part='"frame"'; use part=frame)
- copying draftwright/scad123d source into a cell
- FreeCAD, step2pdf, or Onshape API

If setup already exists (openscad on PATH, both envs have pyproject.toml,
scad2drawing --version prints 0.2.x), skip clone/sync.
If OpenSCAD is missing, apt-get install -y openscad.
If uv is missing, python -m pip install uv — that is the only pip CAD-adjacent install allowed.
Smoke samples/cube.scad (or a cube([10,20,30])) before the user's model.
Surface mesh-fallback and lint needs-attention. Do not hide them.
Onshape mates/motion are out of scope. One STEP → one drawing. Use --parts a,b
(or -D part=NAME) per component, never a fused union() as the only sheet.
```

---

## Hard rules (do not skip)

| Do | Do not |
|---|---|
| `pip install -e /content/scad2drawing` (glue only) | `pip install draftwright` in the kernel |
| `scad2drawing bootstrap --root /content/envs` | `uvx scad2step` (`OCP TopTools ImportError`) |
| `scad2drawing convert … --parts a,b --title "{part}"` | Kernel `import draftwright` |
| `--on-mesh views-only` when scad123d mesh-fallbacks | Hide mesh warnings |
| Keep default `--formats pdf,svg` | PDF-only if the user wanted to edit dims |
| Absolute paths under `/content/work` | `%cd` into env clones then `files.upload()` |
| Bare `-D part=frame` | `-D part='"frame"'` |

draftwright is AGPL-3.0. V2 may `import draftwright` **only** inside the locked draw env via `scripts/v2_draw_worker.py`. `--draw cli` is the V1 official CLI if the user asks.

---

## Placeholders

| Placeholder | Replace with |
|---|---|
| `YOUR_MODEL.scad` | Uploaded source filename |
| `a,b,c` | `--parts` selector values (`drum_shaft,collar,…`) or empty for the whole file |
| `{part}` | Title/number substitution in batch |
| `warn` | `--on-mesh`: `warn` / `views-only` / `skip-draw` / `fail` |
| `PARAMETER=VALUE` | Extra OpenSCAD `-D` (repeatable) |

---

## Cell sequence

Run in order. Separate code cells. After a Colab reset, rerun 1–6.

### Cell 1 — OpenSCAD + paths

```python
import os, shutil, subprocess, sys, zipfile
from pathlib import Path

WORK = Path("/content/work")
ENV_ROOT = Path("/content/envs")
GLUE = Path("/content/scad2drawing")
WORK.mkdir(parents=True, exist_ok=True)
ENV_ROOT.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print("+", cmd if isinstance(cmd, str) else " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)

if shutil.which("openscad") is None:
    sh("apt-get update -qq", shell=True)
    sh("apt-get install -y -qq openscad", shell=True)
sh(["openscad", "--version"])
```

PNG preview needs Xvfb. **CSG/STEP conversion does not.**

### Cell 2 — uv

```python
if shutil.which("uv") is None:
    sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
sh(["uv", "--version"])
```

### Cell 3 — glue repo (V2 worker lives here)

Public repo:

```python
GLUE_REPO = "https://github.com/leon14026/scad2drawing.git"
GLUE_REF = "cursor/v2-draw-worker-a0df"  # use main after V2 is merged

if not (GLUE / "pyproject.toml").is_file():
    sh(["git", "clone", "--depth", "1", "--branch", GLUE_REF, GLUE_REPO, str(GLUE)])
sh([sys.executable, "-m", "pip", "install", "-q", "-e", str(GLUE)])
sh(["scad2drawing", "--version"])  # expect 0.2.x
print("SOP", GLUE / "GEMINI_COLAB_SOP_V2.md")
```

Private repo: upload a zip of the checkout, then:

```python
# sh(["unzip", "-o", "/content/scad2drawing.zip", "-d", "/content"])
# GLUE = Path("/content/scad2drawing")  # adjust if the zip has a prefix folder
```

Do **not** skip this cell. `scripts/v2_draw_worker.py` is resolved from the glue checkout.

### Cell 4 — show this SOP (so Gemini can read it in-notebook)

```python
sop = GLUE / "GEMINI_COLAB_SOP_V2.md"
assert sop.is_file(), "Upload GEMINI_COLAB_SOP_V2.md or clone the glue repo"
try:
    from IPython.display import Markdown, display
    display(Markdown(sop.read_text()))
except Exception:
    print(sop.read_text())
```

### Cell 5 — BOSL2 only if the model `include`s it

```python
BOSL = Path("/root/.local/share/OpenSCAD/libraries/BOSL2")
if not (BOSL / "std.scad").is_file():
    BOSL.parent.mkdir(parents=True, exist_ok=True)
    sh(["git", "clone", "--depth", "1",
        "https://github.com/BelfrySCAD/BOSL2.git", str(BOSL)])
assert (BOSL / "std.scad").is_file()
```

Skip if `NEED_BOSL2` is false.

### Cell 6 — bootstrap locked CAD envs

```python
sh(["scad2drawing", "bootstrap", "--root", str(ENV_ROOT)])
os.environ["SCAD2DRAWING_SCAD_ENV"] = str(ENV_ROOT / "scad123d")
os.environ["SCAD2DRAWING_DRAW_ENV"] = str(ENV_ROOT / "draftwright")
```

First-run `uv sync` takes several minutes. Do not “simplify” to pip.

### Cell 7 — smoke cube

```python
sh(["scad2drawing", "convert", str(GLUE / "samples" / "cube.scad"),
    "-o", str(WORK / "smoke"), "--title", "Smoke cube", "--number", "SMOKE-001",
    "--timeout", "120"])
```

If this fails, **stop**. Do not blame the user's model.

### Cell 8 — upload model

```python
from google.colab import files
uploaded = files.upload()
for name, data in uploaded.items():
    (WORK / Path(name).name).write_bytes(data)
    print("saved", WORK / Path(name).name)
```

### Cell 9 — convert (V2 CLI)

```python
MODEL = WORK / "YOUR_MODEL.scad"
cmd = [
    "scad2drawing", "convert", str(MODEL),
    "-o", str(WORK / "out"),
    "--parts", "a,b",                 # or omit for the whole file
    "--title", "{part}",
    "--number", "DWG-{part}",
    "--on-mesh", "warn",              # warn | views-only | skip-draw | fail
    "--formats", "pdf,svg",
    "--timeout", "600",
    # "-D", "holes=6",
]
sh(cmd)
for p in sorted((WORK / "out").glob("*")):
    print(p.name, p.stat().st_size)
```

Already have STEPs? Put them in `/content/work/out/` with the expected stem (`model_part.step`) and add `--skip-step`.

### Cell 10 — download

```python
from google.colab import files as colab_files
bundle = WORK / "drawings.zip"
payload = [p for p in (WORK / "out").iterdir() if p.is_file()]
sh(["zip", "-j", str(bundle), *map(str, payload)])
colab_files.download(str(bundle))
```

---

## What Gemini should say when something fails

| Symptom | Response |
|---|---|
| `openscad: command not found` | Runtime was reset. Rerun Cell 1. |
| `scad2drawing: command not found` or version `0.1.x` | Cell 3: clone V2 branch + `pip install -e` the glue. |
| `missing V2 worker` | Glue checkout incomplete. Clone/unzip the full repo, not only the `.ipynb`. |
| `Cannot open include file` | Clone that library next to BOSL2; do not drop the include unless the user asks. |
| `OCP` / `TopTools` / `HashCode` | You used `uvx` or system pip. Delete that approach. Use bootstrap only. |
| OpenSCAD parse error after `-D` | Bare `part=frame`. |
| Cube works, real model fails | Geometry/library issue. Use `--parts` for one module. |
| `hull() has no BRep equivalent` | Expected mesh fallback. Warn; use `--on-mesh views-only` if auto-dims are junk. |
| `lint … status=needs-attention` | Drawing still written. Tell the user to edit the SVG (missing notch/D-flat/gear data). Do not claim shop-release. |
| Every sheet is `DWG-001` | You ran one convert per file without `--number DWG-{part}` / `--parts`. |
| User asks to `import draftwright` in the kernel | Refuse. `scad2drawing convert --draw worker` only. |

---

## Out of scope (tell the user, don’t fake it)

- Onshape mates, gear relations, motion, balloons, BOM
- Shop-release GD&T that was never in the `.scad`
- FreeCAD TechDraw / step2pdf
- Mixing scad123d and draftwright in the Colab kernel
- Restarting the runtime after installing CAD packages into system site-packages

---

## Quality checklist

- [ ] `scad2drawing --version` is 0.2.x
- [ ] `GEMINI_COLAB_SOP_V2.md` is readable in the notebook (Cell 4)
- [ ] `openscad --version` prints 2021.x (or newer AppImage)
- [ ] Bootstrap envs have `pyproject.toml`
- [ ] Smoke cube PDF/SVG nonzero
- [ ] Production convert used `--parts` and `{part}` if the model has a selector
- [ ] Mesh-fallback and `needs-attention` lines copied to the user if present
- [ ] PDF **and** SVG downloaded
- [ ] No `uvx`, no kernel `import draftwright`
