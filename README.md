# scad2drawing

Glue an OpenSCAD `.scad` file into a dimensioned engineering drawing, intended to run in Google Colab.

This is **not** a fork-merge of two CAD codebases. The working design is:

```
.scad  →  scad2step / scad123d  →  .step  →  draftwright  →  PDF / SVG / DXF
```

**Feasibility: yes**, with isolated Python environments (the two PyPI stacks pin incompatible `build123d` versions on Colab's Python 3.12). Details, licenses, and the rejected FreeCAD path are in [FEASIBILITY.md](FEASIBILITY.md).

| Stage | Project | License |
|---|---|---|
| SCAD → STEP | [etjones/scad2step](https://github.com/etjones/scad2step) / [scad123d](https://github.com/etjones/scad123d) | MIT |
| STEP → drawing | [pzfreo/draftwright](https://github.com/pzfreo/draftwright) | AGPL-3.0 |

Nothing here is implemented yet. Next step is a Colab notebook that installs OpenSCAD, runs the two CLIs in separate envs, and lets you download the PDF.
