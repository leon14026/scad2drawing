# Feasibility: OpenSCAD → engineering drawings (Colab)

**Verdict: feasible.** Do not merge the two codebases. Glue them at STEP, isolate their Python stacks, and ship a Colab notebook as the front end.

Target pipeline:

```
.scad  →  OpenSCAD (CSG)  →  scad123d / scad2step  →  .step  →  draftwright  →  PDF / SVG / DXF
```

A same-process `import scad123d` then `import draftwright` path is **not** viable on current Google Colab (Python 3.12). The two packages pin incompatible `build123d` versions on that interpreter. STEP as the handshake is the right architecture anyway; draftwright documents that pattern as isolated execution.

---

## What exists

### 1. SCAD → STEP: use this

| | |
|---|---|
| CLI | [etjones/scad2step](https://github.com/etjones/scad2step) — PyPI `scad2step` 0.1.3, MIT, 4 stars |
| Engine | [etjones/scad123d](https://github.com/etjones/scad123d) — PyPI `scad123d` 0.8.0, MIT, 8 stars |

This is the repo you remembered. It is real, packaged, and the correct first hop.

How it works: it shells out to the **real OpenSCAD binary** so `include`/`use`, BOSL2, MCAD, and Customizer `-D` overrides all work, then rebuilds the flattened CSG on [build123d](https://github.com/gumyr/build123d) / OpenCASCADE. Cubes, cylinders, spheres, and the common `minkowski()`-with-sphere rounding stay exact B-Rep (circles stay circles). OpenSCAD's own STL export cannot do that.

Requirements: Python ≥ 3.10, `build123d>=0.11.1`, OpenSCAD on `PATH` (or `$SCAD123D_OPENSCAD`).

Known mesh fallbacks (warnings, never a hard refusal):

- `hull()` of 3+ spheres
- `minkowski()` where neither operand is a sphere
- `projection()`, `surface()`, mesh `import()`, `linear_extrude(twist=...)`

Mesh fallbacks still produce a STEP, but the drawing stage then sees faceted edges and auto-dimensioning gets noisy. That is the main quality risk for "any .scad file."

### 2. STEP → drawings: use draftwright, not step2pdf

Two GitHub projects actually turn STEP into dimensioned drawings. They are not equivalent.

#### Recommended: [pzfreo/draftwright](https://github.com/pzfreo/draftwright)

- PyPI `draftwright` 0.4.35, **AGPL-3.0**, 71 stars, docs at https://draftwright.io
- Input: build123d solid **or** a STEP file
- Output: PDF, SVG, DXF; optional JSON sidecar
- Headless. No GUI. `pip install draftwright` then `draftwright part.step --format pdf,svg,dxf`
- Auto: 3 orthographic views, ISO scale/page, envelope dims, hole callouts, section A–A when blind/stepped holes would be hidden, ISO 7200 title block
- Built on the same OpenCASCADE / build123d kernel as scad123d

This is the drawing half that matches the SCAD converter. Same solid kernel, STEP already supported, Colab-shaped (CLI, no Qt).

#### Not recommended as the Colab core: [maowiz/step2pdf](https://github.com/maowiz/step2pdf)

- 3 stars, **no license file**
- FreeCAD TechDraw batch job aimed at piping parts (straight / elbow / tee / flange)
- Dimensions are family recipes: overall bbox + cylinder diameters
- README: PDF export **requires the GUI FreeCAD executable** (`TechDrawGui.exportPageAsPdf` needs the Qt graphics scene). Headless path is listed as future work
- Colab would need a full FreeCAD GUI + Xvfb. Heavy, fragile, and still weaker at general parts than draftwright

Useful as a reference for ISO 5455 scale picking and first-angle layout. Not the engine to wrap.

### 3. Nearby tools (not the merge)

| Project | Why it is not the merge |
|---|---|
| [DraftSCAD](https://github.com/CameronBrooks11/DraftSCAD) | OpenSCAD library: you **author** dimensions on the XY plane. Not automatic from a 3D solid. |
| [ohmframe-drawer](https://github.com/dawarazhar11/ohmframe-drawer) | Desktop (Tauri/Rust) + Claude API. Not a Colab library. |
| OpenSCAD `projection()` + DXF/PDF | Outlines only. No auto dimensions, no title block, no sections. |

---

## Do not fork-merge the source trees

scad2step is a thin CLI over scad123d. draftwright is a large part-drawing compiler (feature recognition → IR → layout → export). Copying both into one repo would:

- Fight AGPL vs MIT
- Duplicate two fast-moving dependency stacks
- Gain nothing over calling both as installed tools

**This repo should be a glue project:** a Python wrapper, a Colab notebook, sample `.scad` files, and docs. Depend on PyPI packages. Keep STEP on disk so either stage can be debugged alone.

Preferred runtime shape (matches draftwright's own [isolated execution](https://github.com/pzfreo/draftwright/blob/main/docs/reference/isolated-execution.md) guide):

```
[scad env]  scad123d 0.8 + build123d ≥ 0.11.1  →  part.step
[draw env]  draftwright 0.4.x + its pinned build123d              →  part.pdf
```

---

## The hard compatibility fact (Colab)

Google Colab default runtime (2026.07): Ubuntu 22.04, **Python 3.12.13**.

Published pins:

| Package | On Python 3.12 | On Python ≥ 3.13 |
|---|---|---|
| scad123d 0.8.0 | `build123d>=0.11.1` | same |
| draftwright 0.4.35 | `build123d>=0.9,<0.11` | `build123d>=0.11,<0.12` |

On Colab's 3.12 they **cannot share one pip environment**. On 3.13 they can (`0.11.x`).

Colab options, in order:

1. **Two environments, STEP in the middle** — most robust. `venv` or `uv` for draftwright; notebook kernel can own scad123d, or both run as subprocesses. This is the recommended MVP.
2. **Micromamba / deadsnakes Python 3.13 in Colab** — then a single env might resolve. Extra setup, extra breakage surface.
3. **Same-process imports on 3.12** — do not plan on this.

Also: `build123d` upgrades IPython past what Colab's kernel bootstrap accepts. Known workaround: after install, `pip install --no-deps ipython==7.34.0` and **do not restart the runtime**. Safer: never install CAD packages into Colab's system site-packages; use venvs and subprocess.

OpenCASCADE wheels (`cadquery-ocp` / `cadquery-ocp-novtk`) are large. First-cell install will take minutes. GPU is unused; a CPU Colab runtime is correct.

---

## Colab install sketch (not yet implemented)

OpenSCAD CSG/STL export does **not** need a display. PNG preview does (Xvfb). For conversion only:

```bash
apt-get update
apt-get install -y openscad   # Ubuntu jammy: 2021.01 from universe
```

`openscad -o model.csg model.scad` is what scad123d needs. If a model requires a newer OpenSCAD language/library, download an official AppImage instead of the distro package.

Then, conceptually:

```python
# env A
subprocess.check_call(["scad2step", "part.scad", "-o", "part.step"])
# env B
subprocess.check_call(["draftwright", "part.step", "--title", "Part", "--format", "pdf,svg"])
```

Notebook UX: upload `.scad` → run one cell → download PDF/SVG (and keep the STEP).

---

## License

| Piece | License | Effect on this repo |
|---|---|---|
| scad2step / scad123d | MIT | Fine to wrap, fork, or vendor |
| build123d | Apache-2.0 | Fine |
| draftwright | **AGPL-3.0** | The drawing engine. Dual-licensed commercially by the author; contributions require their CLA |
| step2pdf | none published | Do not copy code until the author licenses it |
| OpenSCAD | GPL-2.0+ | System binary, not linked |

Practical policy for `scad2drawing`:

- **Call `draftwright` as a CLI subprocess** and keep this repo's own code MIT (or Apache-2.0). Treat it like calling `ffmpeg`.
- **Do not import `draftwright` as a library** unless you are willing to license this project AGPL-3.0 as well. Combined-work rules are the conservative reading.
- Ship `NOTICE` / README that the drawing step is AGPL software the user installs from PyPI.
- A hosted web service that modifies draftwright would owe users corresponding source (AGPL §13). A public Colab notebook that `pip install`s the official PyPI wheel is a much milder case, but do not fork-and-hide draftwright.

---

## What "engineering drawing" will actually mean

Honest output of the auto path, for a typical prismatic part with holes:

- Front / top / right views, auto scale, title block
- Overall sizes
- Hole diameters / depths / patterns when recognition fires
- Section A–A when the engine decides hidden internals need it

It will **not**, without extra authoring:

- Be shop-release ASME Y14.5 / ISO 1101 by default
- Invent threads, fits, or GD&T that were never in the `.scad` (OpenSCAD has no PMI)
- Stay clean if scad123d fell back to a mesh (fake edges everywhere)
- Treat a multi-body colored assembly as a proper drawing set (both tools are part-oriented)

draftwright has a declarative `Sheet` API for tolerances, datums, and GD&T **if** you have live build123d objects. That path needs the version conflict solved (Python 3.13 single env, or skip STEP and pass objects). For Colab MVP, auto-from-STEP is the product.

---

## Risks

1. **Mesh fallback → junk drawings.** Mitigate: surface scad123d warnings in the notebook; optionally refuse to dimension mesh-fallback parts and export views only.
2. **OpenSCAD 2021.01 on Colab vs BOSL2 / newer language.** Mitigate: document AppImage install as an upgrade path.
3. **RAM / time.** Free Colab ~12 GB. OpenCASCADE + OpenSCAD on a dense CSG can OOM. Timeouts already exist in scad2step.
4. **Native wheel pain.** OCP wheels must match Python and manylinux. Colab is a normal Linux x86_64; this usually works, but it is the first thing to smoke-test.
5. **Auto-dimension quality.** Heuristic. Always keep SVG/DXF so a human can fix the sheet.
6. **AGPL surprise.** Document it up front so the repo does not look like a silent relicense.

---

## Recommended MVP (when building)

1. Glue repo, not a fork merge.
2. Two subprocesses, STEP on disk, Colab notebook + small CLI.
3. Inputs: `.scad` (+ optional `-D` parameters and sibling `.json` Customizer).
4. Outputs: `.step`, `.pdf`, `.svg`, plus a log of scad123d mesh-fallback warnings.
5. Samples: a cube+cylinder, a plate with holes, one BOSL2-ish part, one known mesh-fallback `hull()` of 3 spheres (to show the quality cliff).
6. Skip FreeCAD / step2pdf for v1.
7. License this repo MIT; depend on draftwright via CLI; mention AGPL in README.

Out of scope for v1: GD&T authoring, assemblies, DXF-into-SolidWorks roundtrip guarantees, a hosted SaaS.

---

## Sources checked (2026-10-07)

- https://github.com/etjones/scad2step and https://pypi.org/project/scad2step/ (0.1.3)
- https://github.com/etjones/scad123d and https://pypi.org/project/scad123d/ (0.8.0)
- https://github.com/pzfreo/draftwright and https://pypi.org/project/draftwright/ (0.4.35)
- https://github.com/maowiz/step2pdf (`src/drawing.py`, `src/main.py`)
- Colab runtime FAQ: Ubuntu 22.04 / Python 3.12.13
- Ubuntu jammy `openscad` = 2021.01-4build1
- OpenSCAD CSG/STL CLI does not need X; PNG does
