# scad2drawing

Glue an OpenSCAD `.scad` file into a STEP file and a dimensioned drawing. Built to run in **Google Colab** the same way the existing conversion SOP does: locked `uv` environments, subprocess CLIs, STEP on disk.

```
.scad  →  uv run scad2step  →  .step  →  uv run draftwright  →  PDF / SVG
```

This repository is **original MIT glue**. It does not vendor [scad123d](https://github.com/etjones/scad123d) or [draftwright](https://github.com/pzfreo/draftwright). You clone those projects at pinned revisions and run **their** lockfiles. See [NOTICE](NOTICE) and [LEGAL.md](LEGAL.md).

Want the GitHub repo private while this is WIP? That is optional hygiene, not required for license compliance. Settings → Change visibility. This repo cannot flip that for you.

## V1

- Colab **template** (V1.2): [notebooks/scad2drawing_template.ipynb](notebooks/scad2drawing_template.ipynb) — copy it, edit the CONFIG cell, Run all
- Walkthrough notebook: [notebooks/scad2drawing.ipynb](notebooks/scad2drawing.ipynb)
- Local CLI: `scad2drawing bootstrap` then `scad2drawing convert file.scad -D part=frame`
- Samples under `samples/` (cube smoke, plate, `part=` selector, known mesh-fallback hull)
- **Not** Onshape mates, assembly balloons, or `import draftwright` in the notebook kernel

## Colab

Open `notebooks/scad2drawing_template.ipynb` in Colab (File → Upload if the GitHub repo is private). Edit **CONFIG** (`MODEL_NAME`, `PARTS`, `NEED_BOSL2`), then Runtime → Run all. Rerun setup after a runtime reset.

Using **Gemini in Colab** (side panel / “Help me code”): give it [GEMINI_COLAB_SOP.md](GEMINI_COLAB_SOP.md) and tell it to follow that file exactly. The SOP forbids `uvx` and kernel `import` of the CAD stacks — Gemini will otherwise invent a pip one-liner and hit `OCP TopTools ImportError`.

Do **not** `uvx scad2step`. That unlocked resolve is what produced `OCP TopTools ImportError`. The notebook clones pins from `pins.toml` and runs `uv sync`.

## Local

```bash
# system: git, uv, OpenSCAD on PATH
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

scad2drawing bootstrap --root envs
scad2drawing smoke --skip-draw          # needs OpenSCAD + scad123d env
scad2drawing convert samples/plate.scad -o out --title "Plate"
scad2drawing convert samples/selector.scad -o out -D part=frame --title Frame
```

Environment variables: `SCAD2DRAWING_SCAD_ENV`, `SCAD2DRAWING_DRAW_ENV`, `SCAD123D_OPENSCAD`.

## License

- This repo: MIT
- Drawing engine you install: draftwright **AGPL-3.0** (official CLI only in V1)
- Converter you install: scad123d **MIT**
