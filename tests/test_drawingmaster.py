import json
from pathlib import Path

import pytest

from drawingmaster.check import check_facts, facts_from_doc
from drawingmaster.cli import main
from drawingmaster.dxf import DxfError, parse_dxf

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "drawingmaster" / "metric_third_angle.dxf"


def _dxf(entities: list[str], *, insunits: str = "4", limmax: tuple[str, str] = ("210", "297")) -> str:
    lines = [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "9",
        "$INSUNITS",
        "70",
        insunits,
        "9",
        "$LIMMIN",
        "10",
        "0",
        "20",
        "0",
        "9",
        "$LIMMAX",
        "10",
        limmax[0],
        "20",
        limmax[1],
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
        *entities,
        "0",
        "ENDSEC",
        "0",
        "EOF",
    ]
    return "\n".join(lines) + "\n"


def _text(value: str, height: str = "3.5") -> list[str]:
    return ["0", "TEXT", "8", "0", "10", "0", "20", "0", "40", height, "1", value]


def _rules(text: str, profile: str = "asme-ca") -> list[str]:
    return [f.rule for f in check_facts(facts_from_doc(parse_dxf(text)), profile)]


def test_sample_metric_third_angle_is_clean():
    assert _rules(SAMPLE.read_text(encoding="utf-8")) == []


def _notes(projection: str = "THIRD ANGLE PROJECTION") -> list[str]:
    return [
        *_text(projection),
        *_text("SCALE 1:1"),
        *_text("UNITS mm"),
        *_text("DWG NO DWG-001 REV A"),
        *_text("UNLESS OTHERWISE SPECIFIED TOLERANCES ±0.5"),
        "0",
        "DIMENSION",
        "8",
        "DIM",
        "1",
        "10±0.1",
        "42",
        "10.0",
    ]


def test_first_angle_is_an_error_on_asme_ca():
    assert "projection_first_angle" in _rules(_dxf(_notes("FIRST ANGLE PROJECTION")))


def test_first_angle_is_allowed_on_iso_ca():
    assert "projection_first_angle" not in _rules(_dxf(_notes("FIRST ANGLE PROJECTION")), "iso-ca")


def test_inches_and_nonstandard_scale_and_small_text():
    entities = [
        *_text("THIRD ANGLE PROJECTION", "1.2"),
        *_text('SCALE 1:3  SIZE 1.5"'),
        *_text("DWG NO DWG-9 REV A"),
        *_text("UNLESS OTHERWISE SPECIFIED TOLERANCES ±0.5"),
    ]
    rules = _rules(_dxf(entities, insunits="4"))
    assert "inch_callout" in rules
    assert "scale_nonstandard" in rules
    assert "lettering_small" in rules
    assert "units_not_millimetres" in _rules(_dxf(entities, insunits="1"))


def test_inch_limits_are_converted_before_the_sheet_check():
    entities = [
        *_text("THIRD ANGLE PROJECTION"),
        *_text("SCALE 1:1"),
        *_text("DWG NO DWG-001 REV A"),
        *_text("UNLESS OTHERWISE SPECIFIED ±0.5"),
    ]
    rules = _rules(_dxf(entities, insunits="1", limmax=("11", "8.5")))
    assert "units_not_millimetres" in rules
    assert "sheet_not_iso" in rules
    assert "sheet_size" not in rules


def test_ansi_sheet_and_missing_projection():
    entities = [
        *_text("SCALE 1:1"),
        *_text("UNITS mm"),
        *_text("DWG NO DWG-001 REV A"),
        *_text("UNLESS OTHERWISE SPECIFIED ±0.2"),
    ]
    rules = _rules(_dxf(entities, limmax=("279.4", "431.8")))
    assert "sheet_not_iso" in rules
    assert "projection_missing" in rules


def test_exploded_dxf_skips_dimension_tolerance_check():
    entities = [
        *_text("THIRD ANGLE PROJECTION"),
        *_text("SCALE 1:1"),
        *_text("UNITS mm"),
        *_text("DWG NO DWG-001 REV A"),
    ]
    rules = _rules(_dxf(entities))
    assert "no_semantic_dimensions" in rules
    assert "untoleranced_dimension" not in rules


def test_bare_dimension_without_general_note():
    entities = [
        *_text("THIRD ANGLE PROJECTION"),
        *_text("SCALE 2:1"),
        *_text("UNITS mm"),
        *_text("DWG NO DWG-001 REV A"),
        "0",
        "DIMENSION",
        "8",
        "DIM",
        "1",
        "",
        "42",
        "20",
    ]
    assert "untoleranced_dimension" in _rules(_dxf(entities))


def test_position_frame_needs_a_datum_and_rejects_ioq():
    entities = _notes() + [
        "0",
        "TOLERANCE",
        "8",
        "GDT",
        "1",
        r"{\Fgdt;j}%%v{\Fgdt;n}0.2%%v%%v%%v%%v",
        "0",
        "TOLERANCE",
        "8",
        "GDT",
        "1",
        r"{\Fgdt;r}%%v0.08%%vI%%v%%v%%v",
        "0",
        "TOLERANCE",
        "8",
        "GDT",
        "1",
        "⏤%%v0.1%%vA%%v%%v%%v",
    ]
    rules = _rules(_dxf(entities))
    assert rules.count("gdt_datum_required") == 1
    assert "gdt_datum_letter" in rules
    assert "gdt_form_has_datum" in rules


def test_iso_note_on_asme_profile_and_the_reverse():
    entities = _notes() + _text("GENERAL TOL ISO 2768-mK")
    assert "standards_mixed" in _rules(_dxf(entities), "asme-ca")
    asme_note = _notes() + _text("INTERPRET PER ASME Y14.5")
    assert "standards_mixed" in _rules(_dxf(asme_note), "iso-ca")
    assert "standards_mixed" not in _rules(_dxf(asme_note), "asme-ca")


def test_binary_dxf_is_rejected():
    with pytest.raises(DxfError):
        parse_dxf("AutoCAD Binary DXF\x00\x00")


def test_cli_writes_json_and_fails_on_error(tmp_path, capsys):
    path = tmp_path / "bad.dxf"
    path.write_text(
        _dxf(
            [
                *_text("FIRST ANGLE PROJECTION"),
                *_text("SCALE 1:1"),
                *_text("UNITS mm"),
                *_text("DWG NO DWG-001 REV A"),
                *_text("UNLESS OTHERWISE SPECIFIED TOLERANCES ±0.5"),
            ]
        ),
        encoding="utf-8",
    )
    report = tmp_path / "out.json"
    with pytest.raises(SystemExit) as exc:
        main(["check", str(path), "--json", str(report)])
    assert exc.value.code == 1
    data = json.loads(report.read_text())
    assert data["profile"] == "asme-ca"
    assert any(item["rule"] == "projection_first_angle" for item in data["findings"])
    assert "projection_first_angle" in capsys.readouterr().out


def test_packages_stay_separate():
    root = ROOT / "src"
    for path in (root / "drawingmaster").glob("*.py"):
        text = path.read_text()
        assert "import scad2drawing" not in text
        assert "import draftwright" not in text
    for path in (root / "scad2drawing").glob("*.py"):
        assert "drawingmaster" not in path.read_text()
