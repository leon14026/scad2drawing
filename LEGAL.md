# Legal notes (not legal advice)

Short version: **a glue repo that calls published open-source CLIs, with attribution and no copied engine source, is normal open-source practice.** A GitHub “copyright strike” is a DMCA takedown for *copied files*, not for “uses library X.” A lawsuit is always possible; this design is meant to stay on the boring side of that line.

## What this repo is

Original MIT-licensed wrapper + Colab notebook + samples. At runtime the user installs:

| Tool | License | How we use it |
|---|---|---|
| scad123d / scad2step | MIT | `uv run scad2step` from *their* clone/lockfile |
| draftwright | AGPL-3.0 | `uv run draftwright` from *their* clone/lockfile |
| OpenSCAD | GPL-2.0+ | system binary |
| BOSL2 (optional) | BSD-2-Clause | OpenSCAD library folder |

We do **not** vendor those sources or rebrand them. The `scad2drawing` package never imports CAD libraries.

**V2 worker:** `scripts/v2_draw_worker.py` is launched with `uv run --directory <draftwright clone> python …` and may `from draftwright import build_drawing` in that process only. That is not an import into Colab’s kernel or into this package. `--draw cli` keeps the V1 official-CLI-only path. If you modify draftwright or host a modified drawing service, AGPL obligations are yours.

## Realistic risks

**DMCA / copyright strike — low if we keep it glue.** Strikes happen when someone uploads another project’s source (or substantial copied code) without a license. Cloning GitHub repos the user already has a right to clone, or `uv sync` of a public lockfile, is how those projects expect to be used. Do not paste draftwright or scad123d source into this tree.

**AGPL — the one to treat carefully.** Calling the official `draftwright` CLI (`--draw cli`) is the conservative approach (same idea as calling `ffmpeg`). V2’s worker still runs as a **subprocess of the locked draftwright env**, not as a library import into this MIT package. Importing `draftwright` into `scad2drawing` itself, forking it, or shipping a modified drawing *service* is when copyleft and AGPL §13 get real. If you later host a public converter that *modifies* draftwright, you owe users corresponding source.

**Trademarks.** OpenSCAD, Onshape, Google Colab, GitHub are other people’s marks. Use them descriptively (“runs in Google Colab”), not as if this project is affiliated.

**Your `.scad` files.** Uploading models to Colab sends them to Google. That is a data/policy issue, not copyright of this repo. The SOP already flags org rules.

**step2pdf.** No license file. Do not copy it.

## Should the GitHub repo be private first?

**Optional hygiene, not a legal requirement.**

- **Private** is reasonable while V1 is messy: fewer random clones, fewer “is this affiliated with draftwright?” questions, and you can open it when NOTICE/LICENSE/README are settled. Colab can still run if you upload the notebook; cloning a private GitHub repo from Colab needs a token.
- **Public** is also fine for this design: MIT glue + “install these AGPL/MIT tools yourself” is how a lot of CLI wrappers ship. Public does *not* by itself create a DMCA issue.
- Private does **not** hide AGPL if you later run a modified drawing engine as a service for other people.

This environment cannot change GitHub visibility. If you want it private: repo **Settings → General → Danger zone → Change repository visibility**.

## What we will not do

- Copy draftwright, scad123d, or step2pdf source into this repository
- Strip license headers from anything we quote in docs (we quote as little as possible)
- Claim interoperability equals endorsement
