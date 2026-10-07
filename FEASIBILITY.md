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

## Lessons from the existing Colab SOP

The user already has a working *OpenSCAD → STEP → Onshape* notebook SOP. That is production evidence, not theory. It changes several earlier assumptions.

**1. `uvx scad2step` is the bug, not the install.** The public scad2step README's one-liner lets uv resolve a fresh, unlocked `build123d`/`cadquery-ocp` set. On Colab that failed as `OCP TopTools ImportError`. The fix that actually works:

```text
git clone etjones/scad123d → uv sync (lockfile) → uv run scad2step
```

Any notebook we ship must copy that pattern. A second lockfile (or `uv sync` of a draftwright clone) is required for the drawing hop. Mixing both into Colab's system `pip` is the same class of failure.

**2. This repo replaces SOP section 13 for parts, not the whole SOP.** Today drawings are made by hand in Onshape after STEP import (views, dimensions, title block, PDF). Mates, motion, gear relations, and assembly balloons stay in Onshape — STEP does not carry parameters or mechanisms. Auto-drawings from draftwright are a Colab replacement for *single-part* sheets. They are not a replacement for Onshape assemblies.

**3. `-D part=` is a first-class input.** Real models expose a selector (`part=frame|shaft|assembly|...`) and export components separately. A fused assembly STEP is for visualization / a static picture, not for motion or per-part documentation. The wrapper should loop that selector, not assume one `.scad` → one drawing.

**4. Operational details to encode, not rediscover.**

| SOP fact | Implication |
|---|---|
| Colab VMs are disposable | Setup cells rerun after reset; pin SHAs / lockfiles in this repo |
| `%cd /content/scad123d` then `files.upload()` | Files land in the clone. Keep a `/content/work` dir and use absolute paths |
| BOSL2 at `/root/.local/share/OpenSCAD/libraries/BOSL2` | That is the OpenSCAD library path on Colab; clone only what the model `include`s |
| Smoke `cube([10,20,30])` before the real file | Separates env breakage from geometry breakage |
| Nested `offset_2d` / `hull()` mesh fallback | Surface converter warnings; inspect those faces before trusting dims |
| `-D part=NAME` quoting | Nested quotes break OpenSCAD; pass the selector bare |
| Full assembly much slower than a part | Timeouts and RAM; export components first |

**5. Colors survive into STEP.** The SOP keeps appearances on for Onshape identification. scad123d already preserves `color()` as named bodies. Useful for inspection; draftwright still wants one solid per drawing.

---

## Colab install sketch (not yet implemented)

OpenSCAD CSG/STL export does **not** need a display. PNG preview does (Xvfb). For conversion only:

```bash
apt-get update
apt-get install -y openscad   # Ubuntu jammy: 2021.01 from universe
```

`openscad -o model.csg model.scad` is what scad123d needs. If a model requires a newer OpenSCAD language/library, download an official AppImage instead of the distro package.

Do **not** follow the public `uvx scad2step` one-liner in Colab. That unlocked resolver is what produced the `OCP TopTools ImportError` in the existing SOP. Use the cloned repo lockfile:

```bash
git clone https://github.com/etjones/scad123d.git
cd /content/scad123d
uv sync
uv run scad2step --help
```

Keep a **second** locked env for draftwright. Never `uv sync` both into one tree.

Libraries the SCAD `include`s must live where OpenSCAD looks, e.g. BOSL2:

```bash
mkdir -p /root/.local/share/OpenSCAD/libraries
git clone --depth 1 https://github.com/BelfrySCAD/BOSL2.git \
  /root/.local/share/OpenSCAD/libraries/BOSL2
```

Avoid `%cd` into the scad123d clone for the rest of the notebook. Uploads and outputs should stay in a dedicated project dir (`/content/work`) and pass absolute paths into `uv run --directory /content/scad123d scad2step ...`.

Then, conceptually:

```python
# env A — locked scad123d
subprocess.check_call([
    "uv", "run", "--directory", "/content/scad123d",
    "scad2step", "/content/work/part.scad", "-o", "/content/work/part.step",
    "-D", "part=frame",
])
# env B — locked draftwright
subprocess.check_call([
    "uv", "run", "--directory", "/content/draftwright",
    "draftwright", "/content/work/part.step",
    "--title", "Frame", "--format", "pdf,svg",
])
```

Notebook UX: upload `.scad` (+ libraries/zip) → smoke-test a cube → export selected parts via `-D part=` → download STEP + PDF/SVG.

Colab runtimes are ephemeral. Setup cells must be rerun after reset; pin git SHAs or publish a lockfile in *this* repo so `uv sync` is reproducible.

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
- Recreate mates, gear ratios, or animation — that remains the Onshape assembly SOP, from separately exported components

draftwright has a declarative `Sheet` API for tolerances, datums, and GD&T **if** you have live build123d objects. That path needs the version conflict solved (Python 3.13 single env, or skip STEP and pass objects). For Colab MVP, auto-from-STEP is the product.

---

## Risks

1. **Unlocked `uvx` / `pip` OCP mismatch.** Already hit in production as `OCP TopTools ImportError`. Mitigate: clone + `uv sync` + `uv run` only; never install CAD wheels into Colab's system Python.
2. **Mesh fallback → junk drawings.** Mitigate: surface scad123d warnings; optionally refuse to dimension mesh-fallback parts and export views only. `hull()` of 3+ spheres and nested `offset_2d` are the SOP's known geometry cliffs.
3. **Missing `include` libraries.** Mitigate: clone BOSL2 (and others) into `/root/.local/share/OpenSCAD/libraries`; fail the cell if `std.scad` is absent.
4. **Fused assembly STEP.** A default SCAD `union()` of moving parts becomes one body. Fine for a static picture, useless for mates, balloons, or per-part drawings. Mitigate: require a `part=` selector (or separate files) and draw components one at a time.
5. **OpenSCAD 2021.01 on Colab vs BOSL2 / newer language.** Mitigate: document AppImage install as an upgrade path.
6. **RAM / time.** Free Colab ~12 GB. Full assemblies take substantially longer than parts. Smoke-test a cube, then one component, then production.
7. **Native wheel pain.** OCP wheels must match Python and manylinux. The lockfile is the fix, not a newer unlocked resolve.
8. **Auto-dimension quality.** Heuristic. Always keep SVG/DXF so a human can fix the sheet. Assembly drawings, balloons, and BOM stay in Onshape.
9. **AGPL surprise.** Document it up front so the repo does not look like a silent relicense.
10. **`-D` quoting.** Nested quotes around selector values break OpenSCAD. Use `-D part=frame`, not `-D part='"frame"'`.

---

## Recommended MVP (when building)

1. Glue repo, not a fork merge. Encode the proven SOP as notebook cells, then add a second locked env for draftwright.
2. Two `uv` projects, STEP on disk, Colab notebook + small CLI. No `uvx`, no system-site OCP.
3. Inputs: `.scad` (+ optional `-D part=` / other parameters, sibling `.json` Customizer, OpenSCAD libraries).
4. Outputs: `.step`, `.pdf`, `.svg`, plus a log of scad123d mesh-fallback warnings.
5. Smoke-test a `cube([10,20,30])` before any real model, same as the SOP.
6. Samples: a cube+cylinder, a plate with holes, one BOSL2-ish part with a `part=` selector, one known mesh-fallback `hull()` of 3 spheres.
7. Skip FreeCAD / step2pdf for v1. Skip Onshape automation; leave mates/motion/assembly drawings as the existing Onshape SOP.
8. License this repo MIT; depend on draftwright via CLI; mention AGPL in README.

Out of scope for v1: GD&T authoring, Onshape API, mechanism mates, assembly balloons/BOM, a hosted SaaS.

V2 (shipped in this repo, see [docs/V2.md](docs/V2.md)): still two envs and STEP on disk. Drawing may `import draftwright` **only** inside the locked draftwright env via `scripts/v2_draw_worker.py`. Batch `--parts` and `--on-mesh` fail-soft. Do not mix CAD stacks in the Colab kernel.

---

## Sources checked (2026-10-07)

- https://github.com/etjones/scad2step and https://pypi.org/project/scad2step/ (0.1.3)
- https://github.com/etjones/scad123d and https://pypi.org/project/scad123d/ (0.8.0)
- https://github.com/pzfreo/draftwright and https://pypi.org/project/draftwright/ (0.4.35)
- https://github.com/maowiz/step2pdf (`src/drawing.py`, `src/main.py`)
- Colab runtime FAQ: Ubuntu 22.04 / Python 3.12.13
- Ubuntu jammy `openscad` = 2021.01-4build1
- OpenSCAD CSG/STL CLI does not need X; PNG does
- Existing Colab SOP: *General OpenSCAD to STEP to Onshape SOP* (user-supplied). Locked `uv sync` of scad123d; BOSL2 in `/root/.local/share/OpenSCAD/libraries`; drawings and mates currently done in Onshape after STEP import.
