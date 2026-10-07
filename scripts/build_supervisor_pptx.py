#!/usr/bin/env python3
"""Build a supervisor-facing PowerPoint for scad2drawing V1."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import nsmap, qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "scad2drawing_v1_supervisor.pptx"
PLATE = ROOT / "docs" / "assets" / "plate-drawing.png"

NAVY = RGBColor(0x1B, 0x36, 0x5D)
STEEL = RGBColor(0x2E, 0x5A, 0x88)
ACCENT = RGBColor(0xC4, 0x5C, 0x26)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5A, 0x5A, 0x5A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF4, 0xF6, 0xF8)
RULE = RGBColor(0xD0, 0xD7, 0xDE)


def _set_run(run, text, *, size=18, bold=False, color=DARK, font="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def _add_textbox(slide, left, top, width, height, text, **kw):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    _set_run(p.add_run() if p.runs else p.runs[0] if False else _ensure_run(p), text, **kw)
    return box


def _ensure_run(p):
    if p.runs:
        return p.runs[0]
    return p.add_run()


def add_title_bar(slide, prs, title: str, subtitle: str | None = None):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, Inches(1.05)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.18), Inches(12.3), Inches(0.5))
    p = box.text_frame.paragraphs[0]
    r = p.add_run()
    _set_run(r, title, size=26, bold=True, color=WHITE)
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.5), Inches(0.64), Inches(12.3), Inches(0.32))
        sp = sub.text_frame.paragraphs[0]
        sr = sp.add_run()
        _set_run(sr, subtitle, size=13, color=RGBColor(0xC5, 0xD4, 0xE8))
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.05), prs.slide_width, Inches(0.06)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = ACCENT
    accent.line.fill.background()


def add_footer(slide, prs, page: int, total: int):
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(7.15), Inches(12.3), Inches(0.015)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = RULE
    line.line.fill.background()
    left = slide.shapes.add_textbox(Inches(0.5), Inches(7.2), Inches(9), Inches(0.25))
    p = left.text_frame.paragraphs[0]
    r = p.add_run()
    _set_run(r, "scad2drawing  ·  V1 briefing", size=11, color=MUTED)
    right = slide.shapes.add_textbox(Inches(10.5), Inches(7.2), Inches(2.3), Inches(0.25))
    rp = right.text_frame.paragraphs[0]
    rp.alignment = PP_ALIGN.RIGHT
    rr = rp.add_run()
    _set_run(rr, f"{page}  /  {total}", size=11, color=MUTED)


def bullets(slide, items, left=0.5, top=1.35, width=12.3, height=5.5, size=18):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(10)
        r = p.add_run()
        _set_run(r, item, size=size, color=DARK)
    return box


def two_col_bullets(slide, left_items, right_items, *, top=1.4, size=16):
    bullets(slide, left_items, left=0.5, top=top, width=6.0, height=5.4, size=size)
    bullets(slide, right_items, left=6.8, top=top, width=6.0, height=5.4, size=size)


def new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank


def add_card(slide, left, top, width, height, heading, body):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = LIGHT
    shape.line.color.rgb = RULE
    shape.adjustments[0] = 0.08
    h = slide.shapes.add_textbox(
        Inches(left + 0.18), Inches(top + 0.12), Inches(width - 0.36), Inches(0.4)
    )
    hp = h.text_frame.paragraphs[0]
    hr = hp.add_run()
    _set_run(hr, heading, size=16, bold=True, color=NAVY)
    b = slide.shapes.add_textbox(
        Inches(left + 0.18), Inches(top + 0.5), Inches(width - 0.36), Inches(height - 0.65)
    )
    b.text_frame.word_wrap = True
    bp = b.text_frame.paragraphs[0]
    br = bp.add_run()
    _set_run(br, body, size=13, color=DARK)


def pipeline_boxes(slide):
    labels = [
        (0.4, "OpenSCAD\n.scad"),
        (3.15, "scad2step\n(scad123d)"),
        (5.9, "STEP\nsolid file"),
        (8.65, "draftwright"),
        (11.15, "PDF / SVG\ndrawing"),
    ]
    y = 2.0
    for i, (x, label) in enumerate(labels):
        box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(2.15), Inches(1.15)
        )
        box.fill.solid()
        box.fill.fore_color.rgb = NAVY if i in (1, 3, 4) else STEEL
        if i == 2:
            box.fill.fore_color.rgb = ACCENT
        box.line.fill.background()
        box.adjustments[0] = 0.12
        tb = slide.shapes.add_textbox(Inches(x), Inches(y + 0.22), Inches(2.15), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        _set_run(r, label, size=14, bold=True, color=WHITE)
        if i < len(labels) - 1:
            arr = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                Inches(x + 2.18),
                Inches(y + 0.42),
                Inches(0.32),
                Inches(0.28),
            )
            arr.fill.solid()
            arr.fill.fore_color.rgb = ACCENT
            arr.line.fill.background()


def build() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slides = []

    # 1 title
    s = new_slide(prs)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    stripe = s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(5.85), prs.slide_width, Inches(1.65)
    )
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = RGBColor(0x14, 0x28, 0x48)
    stripe.line.fill.background()
    t = s.shapes.add_textbox(Inches(0.7), Inches(2.0), Inches(12), Inches(1.2))
    p = t.text_frame.paragraphs[0]
    r = p.add_run()
    _set_run(r, "From OpenSCAD models\nto engineering drawings", size=40, bold=True, color=WHITE)
    st = s.shapes.add_textbox(Inches(0.7), Inches(4.35), Inches(12), Inches(0.8))
    sp = st.text_frame.paragraphs[0]
    sr = sp.add_run()
    _set_run(
        sr,
        "scad2drawing V1  ·  a Colab pipeline that turns a .scad file into a STEP solid and a dimensioned PDF",
        size=18,
        color=RGBColor(0xD5, 0xE2, 0xF2),
    )
    ft = s.shapes.add_textbox(Inches(0.7), Inches(6.2), Inches(12), Inches(0.8))
    fp = ft.text_frame.paragraphs[0]
    fr = fp.add_run()
    _set_run(
        fr,
        "Supervisor briefing  ·  what each piece of software is, what we built, and what we did not",
        size=16,
        color=RGBColor(0xB8, 0xC9, 0xDE),
    )
    slides.append(s)

    # 2 problem
    s = new_slide(prs)
    add_title_bar(s, prs, "The problem", "Code CAD is easy. Shop drawings are not.")
    bullets(
        s,
        [
            "We already design parts in OpenSCAD — text files that describe 3D geometry in code.",
            "OpenSCAD is excellent for parametric models and 3D printing. Its native export is STL: a triangle mesh.",
            "Manufacturing, inspection, and CAD handoff want something else: a 2D engineering drawing (views, dimensions, title block) and often a STEP solid that Fusion, SolidWorks, or Onshape can edit.",
            "Until now the path was: convert SCAD → STEP in Colab, then import into Onshape and draft the sheet by hand.",
            "V1 automates the drawing for a single part, in the same Colab workflow, without rewriting the OpenSCAD models.",
        ],
        size=17,
    )
    slides.append(s)

    # 3 pipeline
    s = new_slide(prs)
    add_title_bar(s, prs, "V1 in one picture", "Two existing open-source tools, glued. We did not merge their source.")
    pipeline_boxes(s)
    bullets(
        s,
        [
            "Left to right: the user’s .scad file is evaluated by real OpenSCAD, rebuilt as exact solid geometry, written as STEP, then auto-drafted.",
            "Google Colab is the place this runs (browser, no local CAD install). CPU runtime is enough; GPU is unused.",
            "This repository is glue: a notebook, a small command-line wrapper, samples, and an SOP. The CAD engines stay in their own projects.",
        ],
        top=3.5,
        size=16,
    )
    slides.append(s)

    # 4 openscad
    s = new_slide(prs)
    add_title_bar(s, prs, "OpenSCAD", "The modelling language we start from")
    bullets(
        s,
        [
            "What it is: a free, script-based 3D CAD program (openscad.org). You write a .scad file; it renders a solid. Very common in 3D-printing and parametric hardware.",
            "Why we use it: existing parts, libraries (BOSL2, MCAD), and Customizer parameters (-D part=frame) already live here.",
            "What it is not: a 2D drafting package. It has no first-class engineering-drawing, GD&T, or PMI. Export is typically STL (triangles).",
            "In Colab we install the Linux package (currently OpenSCAD 2021.01). Conversion uses the command line, not the GUI. A display is only needed for PNG previews.",
            "License: GPL-2.0-or-later. We run the official binary; we do not ship OpenSCAD source in this repo.",
        ],
        size=16,
    )
    slides.append(s)

    # 5 step vs stl
    s = new_slide(prs)
    add_title_bar(s, prs, "STL vs STEP", "Why we bother converting before we draw")
    add_card(
        s,
        0.5,
        1.4,
        5.9,
        5.3,
        "STL (what OpenSCAD exports)",
        "A mesh of flat triangles. A cylinder becomes dozens of flat sides. Fine for a printer. Poor for CAD: you cannot fillet a real cylinder, dimensions land on fake edges, and Onshape/SolidWorks treat it as a dumb body.",
    )
    add_card(
        s,
        6.9,
        1.4,
        5.9,
        5.3,
        "STEP / ISO 10303 (what we want)",
        "A B-Rep solid: cylinders stay cylinders, holes stay round. Fusion 360, SolidWorks, FreeCAD, and Onshape import it as real geometry. That is also what an auto-dimensioner needs — otherwise every mesh facet looks like an edge to measure.",
    )
    slides.append(s)

    # 6 scad123d
    s = new_slide(prs)
    add_title_bar(
        s, prs, "scad123d and scad2step", "Open-source converter: OpenSCAD → STEP"
    )
    bullets(
        s,
        [
            "Repos: github.com/etjones/scad123d (engine) and github.com/etjones/scad2step (one-line CLI). MIT license. PyPI packages.",
            "How it works: it runs the real OpenSCAD program so every language feature and library still works, then rebuilds the result on build123d / OpenCASCADE (the same class of solid kernel used in FreeCAD and many CAD tools).",
            "Result: a STEP file with exact curves where the converter understands the operation (cubes, cylinders, spheres, common rounding). Circles stay circles.",
            "Honest limit: some OpenSCAD tricks (hull of many spheres, some minkowski, mesh import) fall back to a triangle mesh. The STEP still writes; drawings of those regions look faceted. V1 prints a warning when that happens.",
            "We call it as a command: uv run scad2step model.scad -o part.step -D part=frame. We do not copy its source into our repo.",
        ],
        size=15,
    )
    slides.append(s)

    # 7 draftwright
    s = new_slide(prs)
    add_title_bar(s, prs, "draftwright", "Open-source engine: STEP → dimensioned drawing")
    bullets(
        s,
        [
            "Repo: github.com/pzfreo/draftwright  ·  PyPI: draftwright  ·  License: AGPL-3.0 (the author also offers a commercial license).",
            "What it does: reads a solid or a STEP file and produces a multi-view engineering drawing — front/top/side, isometric, automatic scale, hole callouts, section when internals would be hidden, ISO title block. Exports PDF, SVG, DXF.",
            "Same solid kernel family as scad123d (build123d / OpenCASCADE), which is why the two tools chain cleanly at STEP.",
            "What it is not: a replacement for a checker or a full ASME Y14.5 pack. Auto-dimensions are heuristic. Threads, fits, and GD&T that were never in the .scad cannot be invented.",
            "V1 calls the official CLI only (like calling ffmpeg). We do not import it into our Python package, and we do not vendor its source. That keeps our glue MIT and respects AGPL.",
        ],
        size=15,
    )
    slides.append(s)

    # 8 supporting
    s = new_slide(prs)
    add_title_bar(s, prs, "The rest of the stack", "Names you will see in the notebook")
    add_card(
        s, 0.45, 1.35, 4.05, 2.55, "Google Colab",
        "Free browser notebooks on a temporary Linux VM. No local CAD install. Runtime resets wipe the machine — setup cells must be rerun. CPU is enough.",
    )
    add_card(
        s, 4.65, 1.35, 4.05, 2.55, "uv (Astral)",
        "Python package manager. We use uv sync on each cloned repo so OpenCASCADE wheels come from that project’s lockfile. uvx (unlocked) is forbidden — it caused the OCP crash.",
    )
    add_card(
        s, 8.85, 1.35, 4.05, 2.55, "build123d / OpenCASCADE",
        "The 3D kernel both converters sit on. Apache-2.0 (build123d). Not something the user edits. Native wheels are large; first Colab setup takes minutes.",
    )
    add_card(
        s, 0.45, 4.1, 4.05, 2.55, "BOSL2",
        "Popular OpenSCAD parts library (BSD-2-Clause). Only cloned if the model include()s it, into OpenSCAD’s library folder. Not a Python package.",
    )
    add_card(
        s, 4.65, 4.1, 4.05, 2.55, "Onshape",
        "Browser CAD we already use after STEP import. Still the place for mates, motion, balloons, and assembly drawings. V1 does not call the Onshape API.",
    )
    add_card(
        s, 8.85, 4.1, 4.05, 2.55, "Gemini in Colab (optional)",
        "Google’s assistant in the notebook. Give it GEMINI_COLAB_SOP.md so it does not invent pip install / uvx. Fill CONFIG; do not let it rewrite setup.",
    )
    slides.append(s)

    # 9 this repo
    s = new_slide(prs)
    add_title_bar(s, prs, "What our repo actually contains", "scad2drawing is glue, not a fork of CAD engines")
    bullets(
        s,
        [
            "A Colab template (edit one CONFIG cell, Run all) and a walkthrough notebook.",
            "A small CLI: scad2drawing bootstrap | convert | smoke — same two subprocesses as Colab.",
            "Sample models: a cube (environment test), a plate with holes, a part= selector, and a known mesh-fallback hull.",
            "Pins (exact git revisions of scad123d and draftwright), NOTICE / licenses, and a Gemini SOP.",
            "It does not contain copies of scad123d or draftwright source. At runtime we clone those GitHub repos at pinned commits and run their CLIs.",
            "Why that matters: we get their bug-fixes by bumping a pin; we do not take ownership of two CAD codebases; AGPL stays on the drawing engine.",
        ],
        size=16,
    )
    slides.append(s)

    # 10 two envs
    s = new_slide(prs)
    add_title_bar(s, prs, "Why two locked environments", "The lesson from the earlier Colab SOP")
    bullets(
        s,
        [
            "Both tools depend on build123d and OpenCASCADE (OCP) native libraries. Those versions do not always agree, especially on Colab’s Python 3.12.",
            "An unlocked one-liner (uvx scad2step) previously failed with OCP TopTools ImportError — uv picked an incompatible wheel.",
            "The working pattern: clone each project, uv sync its own lockfile, uv run the command from that folder. STEP files sit in /content/work between the two.",
            "V1 never import scad123d and import draftwright in the same notebook kernel. That is a later optimisation (V2), not required to ship drawings.",
            "Rule for anyone helping in Colab (including Gemini): pip install uv is allowed; pip install of CAD wheels into Colab’s system Python is not.",
        ],
        size=16,
    )
    slides.append(s)

    # 11 demo
    s = new_slide(prs)
    add_title_bar(
        s, prs, "What a V1 drawing looks like",
        "samples/plate.scad  →  STEP  →  this PDF (generated on our test machine)",
    )
    if PLATE.is_file():
        # image is ~1684x1191 ~ 1.41 aspect
        s.shapes.add_picture(str(PLATE), Inches(1.6), Inches(1.25), Inches(10.1), Inches(5.7))
    slides.append(s)

    # 12 how to run
    s = new_slide(prs)
    add_title_bar(s, prs, "How someone runs V1", "Colab is the intended UI")
    bullets(
        s,
        [
            "Open notebooks/scad2drawing_template.ipynb in Google Colab (CPU). Edit CONFIG: filename, whether BOSL2 is needed, list of parts, title/drawing number.",
            "Runtime → Run all. First time: install OpenSCAD, clone the two pinned repos, uv sync (several minutes). After a runtime reset, setup must be rerun.",
            "Upload the .scad (and a zip of local includes if any). Use bare OpenSCAD flags: -D part=frame, not nested quotes.",
            "Download a zip of .step, .pdf, .svg, and converter logs. Mesh-fallback warnings are shown, not hidden.",
            "Local equivalent: scad2drawing bootstrap then scad2drawing convert file.scad -D part=frame. Same engines, no Colab.",
            "If using Gemini in Colab: attach GEMINI_COLAB_SOP.md and tell it to fill CONFIG only — not to invent a shorter install.",
        ],
        size=16,
    )
    slides.append(s)

    # 13 not in v1
    s = new_slide(prs)
    add_title_bar(s, prs, "What V1 does not do", "So we do not over-claim to manufacturing")
    bullets(
        s,
        [
            "Does not recreate mates, gear ratios, or motion. A fused assembly STEP is a picture. Moving parts still need separate exports and Onshape mates (existing SOP).",
            "Does not produce shop-release ASME/ISO GD&T from a .scad that has none. Review the PDF; SVG/DXF remain editable.",
            "Does not replace Onshape assembly drawings, balloons, or BOM.",
            "Does not use FreeCAD TechDraw (that other STEP→PDF project needs a GUI and has no published license — we did not use it).",
            "Does not host a public web service. Colab is user-driven. Uploading a .scad to Colab sends it to Google — same as the previous conversion SOP.",
        ],
        size=16,
    )
    slides.append(s)

    # 14 table of software
    s = new_slide(prs)
    add_title_bar(s, prs, "Software and repos at a glance", "Everything V1 touches")
    rows = [
        ("Piece", "What it is", "Where", "License", "Our use"),
        ("OpenSCAD", "Script 3D CAD", "openscad.org", "GPL-2.0+", "System binary in Colab"),
        ("scad123d / scad2step", "SCAD → STEP", "github.com/etjones/…", "MIT", "Official CLI, pinned clone"),
        ("draftwright", "STEP → drawing", "github.com/pzfreo/…", "AGPL-3.0", "Official CLI, pinned clone"),
        ("build123d", "Python CAD kernel", "github.com/gumyr/…", "Apache-2.0", "Transitive, inside those envs"),
        ("BOSL2", "OpenSCAD library", "github.com/BelfrySCAD/…", "BSD-2-Clause", "Optional OpenSCAD include"),
        ("Google Colab", "Hosted notebook", "colab.research.google.com", "Google ToS", "Where the job runs"),
        ("Onshape", "Browser CAD / PDM", "onshape.com", "Commercial", "Mates & assemblies, unchanged"),
        ("scad2drawing", "This glue project", "our GitHub repo", "MIT", "Notebook, CLI, SOP, samples"),
    ]
    table = s.shapes.add_table(len(rows), 5, Inches(0.4), Inches(1.28), Inches(12.5), Inches(5.7)).table
    widths = [1.9, 2.2, 3.15, 1.55, 3.7]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = val
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(11 if r else 12)
                    run.font.bold = r == 0
                    run.font.name = "Calibri"
                    run.font.color.rgb = WHITE if r == 0 else DARK
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (LIGHT if r % 2 else WHITE)
    slides.append(s)

    # 15 status
    s = new_slide(prs)
    add_title_bar(s, prs, "Status and what “done” means", "V1 is implemented and proven on the converter")
    bullets(
        s,
        [
            "Done: glue CLI, Colab template (one CONFIG cell), Gemini SOP, samples, license notices. Unit tests pass.",
            "Proven here: OpenSCAD 2021.01 + pinned engines converted a plate with four holes into a dimensioned PDF (previous slide). A hull-of-spheres sample correctly warned mesh fallback.",
            "Remaining check: first run of the template on a real Colab account with a production .scad (setup time, library includes).",
            "V2 (not started): richer drawings inside the draftwright environment only; still no mixing CAD stacks in one Colab kernel until pins allow it.",
            "Ask of you: treat V1 as a single-part drawing assistant on top of the existing SCAD→STEP→Onshape SOP — not as a full drawing office or a mechanism tool.",
        ],
        size=16,
    )
    slides.append(s)

    total = len(prs.slides)
    for i, slide in enumerate(prs.slides):
        if i == 0:
            continue
        add_footer(slide, prs, i + 1, total)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print("wrote", path, path.stat().st_size)
