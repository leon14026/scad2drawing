# drawingmaster

Separate checker. It reads an **ASCII DXF** and flags broken mechanical-drawing rules for a Canada shop profile. It does not look at the solid, and it does not approve a drawing.

```bash
pip install -e .
drawingmaster check samples/drawingmaster/metric_third_angle.dxf --profile asme-ca
drawingmaster check part.dxf --profile iso-ca --json out/part.flags.json
drawingmaster check part.dxf --strict   # warnings also exit 1
```

`scad2drawing` never imports this package. This package never imports `scad2drawing` or draftwright.

## Profiles

| Profile | Expects |
|---|---|
| `asme-ca` (default) | Millimetres, ISO A-series sheet, **third-angle**, no ISO 2768 / 8015 / 1101 note |
| `iso-ca` | Millimetres, ISO A-series sheet, first-angle **or** third-angle stated, no ASME Y14.5 note |

Withdrawn CSA B78.1 / B78.2 are not implemented. Current Canadian practice is ASME Y14.5 (this profile) or ISO GPS, plus millimetres.

## What is flagged

| Rule | Severity | Meaning |
|---|---|---|
| `units_not_millimetres` | error | `$INSUNITS` is inches |
| `inch_callout` | error | Inch mark or the word INCH |
| `projection_first_angle` | error | First-angle on `asme-ca` |
| `gdt_datum_letter` | error | Datum letter I, O, or Q |
| `gdt_datum_required` | error | Position / concentricity frame with no datum |
| `gdt_form_has_datum` | error | Form control (flatness, straightness, cylindricity) references a datum |
| `gdt_missing_value` | error | Frame has no numeric tolerance |
| `sheet_not_iso` / `sheet_size` / `sheet_unknown` | warning | Not an A0–A4 sheet, or size missing |
| `scale_missing` / `scale_nonstandard` | warning | No scale, or not a 1/2/5 series scale |
| `projection_missing` | warning | Projection method not stated |
| `title_number` / `title_revision` | warning | No DWG number or REV note |
| `untoleranced_dimension` | warning | DIMENSION entity with no tolerance and no general-tolerance note |
| `no_semantic_dimensions` | warning | No DIMENSION entities (exploded DXF). Size rules were skipped |
| `lettering_small` | warning | TEXT under 2.5 mm |
| `standards_mixed` | warning | The other profile’s standard is named on the sheet |
| `units_not_stated` / `units_header_blank` | warning | Units missing from the header |

Feature-control frames are read from DXF `TOLERANCE` text (`%%v` compartments, `{\Fgdt;j}` position, `{\Fgdt;r}` concentricity) and from a few Unicode symbols. Other gdt.shx letters are reported as `gdt_symbol_unclassified` and still checked for a number and for letters I/O/Q.

## What this will not catch

A missing V-notch, a bad datum scheme, a tolerance stack, or a gear that has no tooth data. Those need the model and design intent. Binary DXF is rejected; export ASCII.

Draftwright’s DXF writer (the one `scad2drawing` calls) currently emits lines and splines, not `TEXT` or `DIMENSION` entities. On those files the checker still reads sheet size and `$INSUNITS`, then warns `no_semantic_dimensions` and skips callout rules. Use a CAD DXF that keeps dimensions as entities when you want the tolerance and GD&T checks. Sheets produced here already carry a `.draftwright.json` lint sidecar; that remains the annotation signal for this pipeline.

Exit status is 1 when any finding is an error. `--strict` does the same for warnings.
