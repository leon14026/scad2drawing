# Gemini in Colab SOP — scad2drawing V1

Use this file as the **instruction pack** if you drive the conversion with Gemini in Google Colab (the Gemini side panel, “Help me code”, or paste into a Gemini chat that writes notebook cells).

**How to use it**

1. Open a Colab notebook (CPU runtime; GPU unused).
2. Upload this file, or paste the **Hard rules** plus **Cell sequence** into Gemini.
3. Tell Gemini: *Follow GEMINI_COLAB_SOP.md exactly. Do not invent a shorter install.*
4. After a runtime reset, start again at Cell 1.

Preferred path: open `notebooks/scad2drawing_template.ipynb`, fill the **CONFIG** cell, and only ask Gemini to **fill CONFIG and run cells**, not to rewrite setup.

---

## Paste into Gemini (system)

```text
You are setting up and running scad2drawing in Google Colab.

Goal: .scad → STEP → dimensioned PDF/SVG.

You MUST use two locked uv environments and subprocess CLIs:
  /content/envs/scad123d   →  uv run --directory … scad2step
  /content/envs/draftwright →  uv run --directory … draftwright
Work files live in /content/work. Never %cd into the git clones.

FORBIDDEN:
- uvx scad2step, uvx draftwright, uvx anything CAD
- pip install scad123d / draftwright / build123d / cadquery-ocp into Colab's system Python
- import scad123d or import draftwright in the notebook kernel
- mixing both tools in one venv
- nested quotes on -D (no part='"frame"'; use part=frame)
- copying or vendoring draftwright/scad123d source into a new cell as a rewrite
- FreeCAD, step2pdf, or Onshape API

If setup already exists (openscad on PATH, both envs have pyproject.toml), skip clone/sync.
If OpenSCAD is missing, apt-get install -y openscad.
If uv is missing, python -m pip install uv — that is the only pip CAD-adjacent install allowed.
Pins:
  scad123d  https://github.com/etjones/scad123d.git  @ 85811a1a9daa291fb9ebfdfd8339322a9ec5b52c
  draftwright https://github.com/pzfreo/draftwright.git @ v0.4.35
Always: git clone --depth 1, git fetch --depth 1 origin REV, git checkout FETCH_HEAD, uv sync --directory ENV.
Smoke a cube([10, 20, 30]) before the user's model.
Surface mesh-fallback warnings. Do not hide them.
Onshape mates/motion are out of scope. One STEP → one drawing. Use -D part=NAME per component.
```

---

## Hard rules (do not skip)

| Do | Do not |
|---|---|
| `uv sync --directory /content/envs/scad123d` | `uvx scad2step` (causes `OCP TopTools ImportError`) |
| `uv run --directory ENV tool …` | `pip install build123d` in the Colab kernel |
| Absolute paths under `/content/work` | `%cd /content/envs/scad123d` then `files.upload()` |
| `-D part=frame` | `-D part='"frame"'` |
| Smoke cube first | Jump straight to a huge assembly |
| Export components separately for motion/drawings | Draw a fused `union()` assembly as if it were one part |

draftwright is AGPL-3.0. Call the official CLI only. Do not paste its source into the notebook.

---

## Placeholders

| Placeholder | Replace with |
|---|---|
| `YOUR_MODEL.scad` | Uploaded source filename |
| `YOUR_PART` | Selector value (`frame`, `shaft`, …) or omit `-D` if none |
| `YOUR_TITLE` | Title block text |
| `DWG-001` | Drawing number |
| `PARAMETER` / `VALUE` | Extra OpenSCAD `-D` overrides |

---

## Cell sequence

Run in order. Separate code cells. After a Colab reset, rerun 1–5.

### Cell 1 — OpenSCAD

```python
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
sh(["openscad", "--version"])
```

PNG preview needs Xvfb. **CSG/STEP conversion does not.** Do not install a display unless the user asked for a PNG from OpenSCAD.

### Cell 2 — uv

```python
if shutil.which("uv") is None:
    sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
sh(["uv", "--version"])
```

### Cell 3 — BOSL2 only if the model `include`s it

```python
BOSL = Path("/root/.local/share/OpenSCAD/libraries/BOSL2")
if not (BOSL / "std.scad").is_file():
    BOSL.parent.mkdir(parents=True, exist_ok=True)
    sh(["git", "clone", "--depth", "1",
        "https://github.com/BelfrySCAD/BOSL2.git", str(BOSL)])
assert (BOSL / "std.scad").is_file()
```

Other libraries: clone into `/root/.local/share/OpenSCAD/libraries/<NameExpectedByInclude>`.

### Cell 4 — locked scad123d

```python
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
   stdout=subprocess.DEVNULL)
```

Continue only if `scad2step --help` exits 0.

### Cell 5 — locked draftwright

```python
DRAW_REPO = "https://github.com/pzfreo/draftwright.git"
DRAW_REV = "v0.4.35"
materialize(DRAW_REPO, DRAW_ENV, DRAW_REV)
sh(["uv", "run", "--directory", str(DRAW_ENV), "draftwright", "--help"],
   stdout=subprocess.DEVNULL)
```

First-run `uv sync` takes several minutes (OpenCASCADE wheels). Do not “simplify” to pip.

### Cell 6 — smoke cube

```python
smoke = WORK / "cube.scad"
smoke.write_text("cube([10, 20, 30]);\n")
step = WORK / "cube.step"
sh(["uv", "run", "--directory", str(SCAD_ENV), "scad2step",
    str(smoke), "-o", str(step), "--timeout", "120"])
assert step.stat().st_size > 0
print(step, step.stat().st_size)
```

If this fails, **stop**. Do not blame the user's model. Fix OpenSCAD / the scad123d env.

### Cell 7 — upload

```python
from google.colab import files
uploaded = files.upload()
for name, data in uploaded.items():
    (WORK / Path(name).name).write_bytes(data)
    print("saved", WORK / Path(name).name)
# zip:  !unzip -o /content/work/YOUR_PROJECT.zip -d /content/work/YOUR_PROJECT
```

### Cell 8 — convert selected part

```python
MODEL = WORK / "YOUR_MODEL.scad"
DEFINES = ["part=YOUR_PART"]   # or []
OUT_STEM = "YOUR_PART"

step_path = WORK / f"{OUT_STEM}.step"
cmd = ["uv", "run", "--directory", str(SCAD_ENV), "scad2step",
       str(MODEL), "-o", str(step_path), "--timeout", "600"]
for d in DEFINES:
    cmd += ["-D", d]
proc = subprocess.run(cmd, text=True, capture_output=True)
sys.stderr.write(proc.stderr)
if proc.returncode:
    raise SystemExit(proc.returncode)
(WORK / f"{OUT_STEM}.scad2step.log").write_text(proc.stderr)
if "mesh" in proc.stderr.lower() and "fallback" in proc.stderr.lower():
    print("WARNING: mesh fallback — inspect STEP; dimensions may be junk")
print(step_path, step_path.stat().st_size)
```

Extra overrides: `DEFINES = ["part=frame", "PARAMETER=VALUE"]`.

### Cell 9 — drawing

```python
prefix = WORK / OUT_STEM
sh(["uv", "run", "--directory", str(DRAW_ENV), "draftwright",
    str(step_path), "--out", str(prefix),
    "--format", "pdf,svg", "--title", "YOUR_TITLE", "--number", "DWG-001"])
for p in sorted(WORK.glob(OUT_STEM + ".*")):
    print(p.name, p.stat().st_size)
```

### Cell 10 — download

```python
from google.colab import files as colab_files
bundle = WORK / "drawings.zip"
payload = [p for p in WORK.glob(OUT_STEM + ".*") if p.suffix != ".scad"]
sh(["zip", "-j", str(bundle), *map(str, payload)])
colab_files.download(str(bundle))
```

---

## What Gemini should say when something fails

| Symptom | Response |
|---|---|
| `openscad: command not found` | Runtime was reset. Rerun Cell 1. |
| `Cannot open include file` | Clone that library next to BOSL2; do not rewrite the SCAD to drop the include unless the user asks. |
| `OCP` / `TopTools` / `HashCode` import error | You used `uvx` or system pip. Delete that approach. Use Cells 4–5 only. |
| OpenSCAD parse error after `-D` | Bare `part=frame`. |
| Cube works, real model fails | Geometry/library issue, not env. Export one module via `-D part=`. |
| `hull() has no BRep equivalent` | Expected mesh fallback. Warn the user; still write STEP. |
| One fused body | Expected for `part=assembly`. Draw `frame` / `shaft` separately. |
| User asks to `import draftwright` | Refuse for V1. Call the CLI in `DRAW_ENV`. |

---

## Out of scope (tell the user, don’t fake it)

- Onshape mates, gear relations, motion, balloons, BOM
- Shop-release GD&T that was never in the `.scad`
- FreeCAD TechDraw / step2pdf
- Restarting the Colab runtime after installing CAD packages into system site-packages

---

## Quality checklist

- [ ] `openscad --version` prints 2021.x (or newer AppImage if you installed one)
- [ ] `uv run --directory /content/envs/scad123d scad2step --help` works
- [ ] `uv run --directory /content/envs/draftwright draftwright --help` works
- [ ] Smoke cube STEP is nonzero
- [ ] Production STEP is nonzero
- [ ] Mesh-fallback notes copied to the user if present
- [ ] PDF/SVG downloaded
- [ ] No `uvx`, no kernel `import draftwright`
