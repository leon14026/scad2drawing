# Gemini in Colab SOP — scad2drawing V1

Use this file as the **instruction pack** if you drive the conversion with Gemini in Google Colab (the Gemini side panel, “Help me code”, or paste into a Gemini chat that writes notebook cells).

**How to use it**

1. Open a Colab notebook (CPU runtime; GPU unused).
2. Upload this file, or paste the **Hard rules** plus **Cell sequence** into Gemini.
3. Tell Gemini: *Follow GEMINI_COLAB_SOP.md exactly. Do not invent a shorter install.*
4. After a runtime reset, start again at Cell 1.

Preferred path: open `notebooks/scad2drawing_template.ipynb`, fill the **CONFIG** cell, and only ask Gemini to **fill CONFIG and run cells**, not to rewrite setup.

**V2:** use [GEMINI_COLAB_SOP_V2.md](GEMINI_COLAB_SOP_V2.md) and `notebooks/scad2drawing_v2.ipynb` instead of this file.

Checker: [GEMINI_COLAB_SOP_DRAWINGMASTER.md](GEMINI_COLAB_SOP_DRAWINGMASTER.md).

## CAPABILITY_INDEX

Machine-readable inventory of every command in this repo. Same text in `GEMINI_CAPACITY_INDEX.txt`, `GEMINI_COLAB_SOP.md`, `GEMINI_COLAB_SOP_V2.md`, and `GEMINI_COLAB_SOP_DRAWINGMASTER.md`. Obey this block. Do not treat it as prose.

```text
<<<CAPABILITY_INDEX schema=scad2drawing.capability_index schema_version=1>>>
repo=leon14026/scad2drawing
glue_pkg=scad2drawing glue_version=0.2.0
checker_pkg=drawingmaster checker_version=0.1.0
branch=cursor/v2-draw-worker-a0df
sops=GEMINI_COLAB_SOP.md,GEMINI_COLAB_SOP_V2.md,GEMINI_COLAB_SOP_DRAWINGMASTER.md
notebooks=notebooks/scad2drawing_template.ipynb,notebooks/scad2drawing.ipynb,notebooks/scad2drawing_v2.ipynb
preferred=GEMINI_COLAB_SOP_V2.md + notebooks/scad2drawing_v2.ipynb
colab_paths glue=/content/scad2drawing work=/content/work env_root=/content/envs scad_env=/content/envs/scad123d draw_env=/content/envs/draftwright
pins scad123d=https://github.com/etjones/scad123d.git@85811a1a9daa291fb9ebfdfd8339322a9ec5b52c draftwright=https://github.com/pzfreo/draftwright.git@v0.4.35 bosl2=https://github.com/BelfrySCAD/BOSL2.git@master
install_glue=python -m pip install -e /content/scad2drawing
install_uv_only=python -m pip install uv
install_openscad=apt-get install -y openscad
bootstrap=scad2drawing bootstrap --root /content/envs
env SCAD2DRAWING_ENV_ROOT SCAD2DRAWING_SCAD_ENV SCAD2DRAWING_DRAW_ENV SCAD123D_OPENSCAD
forbidden=uvx;pip_install_scad123d;pip_install_draftwright;pip_install_build123d;pip_install_cadquery-ocp;kernel_import_scad123d;kernel_import_draftwright;kernel_import_build123d;mix_cad_venvs;nested_quotes_on_-D;vendor_engine_source;freecad;step2pdf;onshape_api;binary_dxf
kernel_import_draftwright_allowed_only_as=uv run --directory DRAW_ENV python scripts/v2_draw_worker.py
-D_form=name=value bare example part=frame reject part='"frame"'

command scad2drawing.bootstrap argv="scad2drawing bootstrap --root DIR" effect=clone_pins_and_uv_sync
command scad2drawing.convert argv="scad2drawing convert FILE.scad -o DIR" pipeline=".scad -> uv run scad2step -> .step -> draw -> pdf,svg"
command scad2drawing.convert.draw default=worker choices=worker,cli worker=scripts/v2_draw_worker.py imports draftwright.build_drawing inside draw env only cli=official draftwright CLI no auto_dims
command scad2drawing.convert.parts argv="--parts a,b" effect=loop -D part=NAME implies --keep-going title_sub={part} number_sub={part} default_number_sequence=DWG-001,DWG-002
command scad2drawing.convert.on-mesh default=warn choices=warn,views-only,skip-draw,fail views-only=worker --no-auto-dims skip-draw=STEP plus MESH_FALLBACK.txt no drawing fail=exit 2
command scad2drawing.convert.formats default=pdf,svg also=dxf,png,all
command scad2drawing.convert.flags=-D --title --number --timeout --skip-step --skip-draw --keep-going --scad-env --draw-env --strict_not_a_convert_flag
command scad2drawing.convert.lint reads={stem}.draftwright.json prints status,errors,warnings tally=needs-attention does_not_fail_process statuses=ok,mesh-warned,skipped-draw,needs-attention,failed mesh_stamp=scad2drawing.mesh_fallback
command scad2drawing.convert.outputs={stem}.step {stem}.pdf {stem}.svg {stem}.dxf {stem}.png {stem}.draftwright.json {stem}.scad2step.log {stem}.MESH_FALLBACK.txt
command scad2drawing.smoke argv="scad2drawing smoke" sample=samples/cube.scad draw=worker
worker_script=scripts/v2_draw_worker.py args=--step --out --title --number --format --auto-dims/--no-auto-dims --mesh-fallback formats_all_order=pdf,svg,dxf,png

command drawingmaster.check argv="drawingmaster check FILE.dxf --profile asme-ca|iso-ca [--json PATH] [--strict]" input=ASCII_DXF_only rejects=binary_DXF does_not_read_solid=true does_not_approve_part=true not_called_by_scad2drawing_convert=true
drawingmaster.profile asme-ca default=true expects=millimetres,ISO_A0-A4,third_angle rejects_note=ISO_2768,ISO_8015,ISO_1101 error_if=first_angle
drawingmaster.profile iso-ca expects=millimetres,ISO_A0-A4,first_or_third_stated rejects_note=ASME_Y14.5,Y14.5
drawingmaster.canada_withdrawn=CAN3-B78.1,CAN/CSA-B78.2 do_not_implement
drawingmaster.canada_practice=ASME_Y14.5_or_ISO_GPS plus millimetres third_angle_for_asme-ca
drawingmaster.exit=1 if any error; 1 if --strict and any warning; else 0
drawingmaster.error_rules=units_not_millimetres,inch_callout,projection_first_angle,gdt_datum_letter,gdt_datum_required,gdt_form_has_datum,gdt_missing_value
drawingmaster.warning_rules=units_header_blank,units_not_stated,sheet_unknown,sheet_not_iso,sheet_size,scale_nonstandard,scale_missing,projection_missing,projection_both,title_number,title_revision,no_semantic_dimensions,untoleranced_dimension,lettering_small,standards_mixed
drawingmaster.info_rules=scale_not_to_scale,gdt_symbol_unclassified
drawingmaster.gdt_letters j=position policy=datum_required r=concentricity policy=datum_required n=diameter_modifier m=mmc l=lmc other_Fgdt_letters=unclassified_still_check_value_and_IOQ
drawingmaster.gdt_unicode form_no_datum=straightness,flatness,cylindricity datum_required=angularity,perpendicularity,parallelism,position,concentricity,symmetry optional_datum=profile_line,profile_surface
drawingmaster.illegal_datum_letters=I,O,Q
drawingmaster.lettering_min_mm=2.5
drawingmaster.sheets_mm=A4:210x297,A3:297x420,A2:420x594,A1:594x841,A0:841x1189 ansi_inch_sheets_flagged_sheet_not_iso
drawingmaster.scales=1:1,1:2,1:5,1:10,1:20,1:50,1:100,1:200,1:500,1:1000,2:1,5:1,10:1,20:1,50:1,100:1 NTS=info
drawingmaster.draftwright_dxf=exploded LINE/SPLINE/ARC no TEXT no DIMENSION expect warning no_semantic_dimensions do_not_invent_DIMENSION_entities use_.draftwright.json_for_pipeline_lint

out_of_scope=onshape_mates,gear_relations,motion,balloons,BOM,shop_release_gdt_absent_from_scad,datum_scheme_correctness,tolerance_stack,missing_notch_or_D_flat_or_gear_module,mix_cad_stacks_one_colab_kernel,hosted_saas
do_not_hide=mesh_fallback,needs-attention,drawingmaster_errors
smoke_before_user_model=samples/cube.scad cube([10,20,30])
<<<END_CAPABILITY_INDEX>>>
```


---

## Paste into Gemini (system)

```text
You are setting up and running scad2drawing in Google Colab.

Obey the CAPABILITY_INDEX block in this file. It lists every command (convert, worker, drawingmaster). This V1 file is the raw CLI path. Prefer GEMINI_COLAB_SOP_V2.md unless the user asked for --draw cli.

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

draftwright is AGPL-3.0. Call it via `scad2drawing convert` or `uv run --directory DRAW_ENV …`. Do not paste its source into the notebook. Do not `import draftwright` in the Colab kernel. V2’s worker import is allowed **only** as that subprocess (`--draw worker`, the CLI default).

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
| User asks to `import draftwright` in the kernel | Refuse. Use `scad2drawing convert` (`--draw worker` runs the import inside `DRAW_ENV` only). |

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

---

## V2 addendum

Superseded by [GEMINI_COLAB_SOP_V2.md](GEMINI_COLAB_SOP_V2.md) and `notebooks/scad2drawing_v2.ipynb`. If you stay on this V1 file by mistake, still allowed:

```text
scad2drawing convert /content/work/MODEL.scad -o /content/work/out --parts frame,shaft --title "{part}"
```

Still forbidden: `import draftwright` in a notebook cell.
