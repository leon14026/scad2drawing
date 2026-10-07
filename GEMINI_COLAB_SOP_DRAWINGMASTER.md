# Gemini in Colab SOP — drawingmaster

Checker only. It does not convert `.scad`. For conversion follow [GEMINI_COLAB_SOP_V2.md](GEMINI_COLAB_SOP_V2.md).

1. CPU runtime.
2. Glue repo installed (`pip install -e /content/scad2drawing`) so `drawingmaster` is on `PATH`. Same checkout as V2. Do not pip-install CAD.
3. Upload an **ASCII DXF**, or pass a DXF already under `/content/work`.
4. Tell Gemini: *Follow GEMINI_COLAB_SOP_DRAWINGMASTER.md and the CAPABILITY_INDEX block. Do not approve the part.*

Draftwright DXF from `scad2drawing` is exploded lines. Expect `no_semantic_dimensions`. Do not invent `DIMENSION` entities. Use `.draftwright.json` for pipeline lint.

---

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
You check ASCII DXF files with drawingmaster. You do not approve drawings.

Command:
  drawingmaster check /content/work/FILE.dxf --profile asme-ca --json /content/work/FILE.flags.json
  --profile iso-ca when the user says ISO. Default asme-ca (Canada / ASME, third-angle, mm).
  --strict only if the user asks warnings to fail the cell.

Read the CAPABILITY_INDEX block in this file before choosing flags. Obey error_rules vs warning_rules.
Exit 1 means at least one error. Say the rule ids. Do not say the part is correct.

FORBIDDEN:
- uvx, kernel import of draftwright/scad123d/build123d, pip install of those packages
- binary DXF (tell the user to export ASCII)
- claiming shop-release, datum-scheme correctness, or a tolerance stack
- rewriting the DXF to hide findings

If the DXF came from scad2drawing/draftwright, warn no_semantic_dimensions and stop. Do not "fix" the export.
```

---

## Cell 1 — checker

```python
import shutil, subprocess, sys
from pathlib import Path

WORK = Path("/content/work") if Path("/content").is_dir() else Path("work")
GLUE = Path("/content/scad2drawing") if Path("/content").is_dir() else Path(".")
WORK.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print("+", " ".join(map(str, cmd)))
    return subprocess.run(cmd, check=False, text=True, **kw)

if shutil.which("drawingmaster") is None:
    root = GLUE if (GLUE / "pyproject.toml").is_file() else Path.cwd()
    sh([sys.executable, "-m", "pip", "install", "-q", "-e", str(root)])
sh(["drawingmaster", "--version"])
```

## Cell 2 — show this SOP and the capability index

```python
root = GLUE if (GLUE / "GEMINI_COLAB_SOP_DRAWINGMASTER.md").is_file() else Path.cwd()
for name in ("GEMINI_CAPACITY_INDEX.txt", "GEMINI_COLAB_SOP_DRAWINGMASTER.md", "GEMINI_COLAB_SOP_V2.md", "GEMINI_COLAB_SOP.md"):
    path = root / name
    print("SOP", path, "exists" if path.is_file() else "MISSING")
    if path.is_file():
        try:
            from IPython.display import Markdown, display
            display(Markdown(path.read_text()))
        except Exception:
            print(path.read_text())
```

## Cell 3 — upload DXF and check

```python
PROFILE = "asme-ca"   # or "iso-ca"
DXF_NAME = "YOUR_PART.dxf"

try:
    from google.colab import files
    uploaded = files.upload()
    for name, data in uploaded.items():
        (WORK / Path(name).name).write_bytes(data)
        print("saved", WORK / Path(name).name)
except ImportError:
    print("Not Colab — put the DXF in", WORK)

dxf = WORK / DXF_NAME
assert dxf.is_file(), dxf
report = WORK / (dxf.stem + ".flags.json")
proc = sh(["drawingmaster", "check", str(dxf), "--profile", PROFILE, "--json", str(report)])
print(report.read_text() if report.is_file() else "no json")
if proc.returncode not in (0, 1):
    raise SystemExit(proc.returncode)
print("exit", proc.returncode, "(1 = errors found, not a crash)")
```

## Cell 4 — download

```python
try:
    from google.colab import files as colab_files
    colab_files.download(str(report))
except ImportError:
    print(report)
```

---

## What to tell the user

| Result | Say |
|---|---|
| exit 0, zero findings | No rule in this profile failed. This is not part approval. |
| exit 1 | List `error` rule ids. Do not repair the DXF unless asked. |
| `no_semantic_dimensions` | Exported geometry has no DIMENSION entities. Callout rules were skipped. |
| `needs-attention` from scad2drawing | Different tool. That is draftwright JSON lint, not this checker. |
| User wants mates / GD&T authoring | Out of scope. Onshape or a human edit of the SVG. |
