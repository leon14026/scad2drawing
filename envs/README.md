# Isolated CAD environments

Clones of scad123d and draftwright **do not belong in git**. Run:

```bash
scad2drawing bootstrap --root envs
```

That checks out the revisions in `pins.toml` and runs `uv sync` in each tree so OCP/`build123d` come from **their lockfiles**, not an unlocked `uvx`.

```
envs/scad123d/      # MIT, uv-managed
envs/draftwright/   # AGPL-3.0, uv-managed
```

Set `SCAD2DRAWING_SCAD_ENV` / `SCAD2DRAWING_DRAW_ENV` if they live elsewhere.
