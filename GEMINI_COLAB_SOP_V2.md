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

DXF check: [GEMINI_COLAB_SOP_DRAWINGMASTER.md](GEMINI_COLAB_SOP_DRAWINGMASTER.md).

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
You are setting up and running scad2drawing V2 in Google Colab.

Obey the CAPABILITY_INDEX block in this file before you invent a command.
It is the full inventory: bootstrap, convert flags, worker, lint, drawingmaster.

Goal: .scad → STEP → dimensioned PDF/SVG, with unique drawing numbers,
SVG kept, and draftwright lint (needs-attention) printed.
If the user supplies an ASCII DXF, also run drawingmaster (see GEMINI_COLAB_SOP_DRAWINGMASTER.md). Do not approve the part.

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
| User hands you a DXF | `drawingmaster check FILE.dxf --profile asme-ca`. Obey CAPABILITY_INDEX. Exit 1 is a finding, not a crash. Do not approve the part. |
| `no_semantic_dimensions` | Draftwright DXF is exploded. Do not invent DIMENSION entities. Use `.draftwright.json` for lint. |

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
- [ ] CAPABILITY_INDEX block was left intact (do not summarize it away)
