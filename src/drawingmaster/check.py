"""Pure checks against a parsed drawing. No file or CAD access."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from drawingmaster.dxf import DxfDoc, dxf_plain, header_number, header_pair_span
from drawingmaster.frames import Frame, illegal_datums, parse_frames, value_has_number

PROFILES = ("asme-ca", "iso-ca")

# ISO 216 / ASME Y14.1M trimmed sizes, millimetres.
ISO_SHEETS = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
    "A1": (594.0, 841.0),
    "A0": (841.0, 1189.0),
}

# ASME Y14.1 inch sheets, stored in millimetres for comparison.
ANSI_SHEETS_MM = {
    "ANSI-A": (215.9, 279.4),
    "ANSI-B": (279.4, 431.8),
    "ANSI-C": (431.8, 558.8),
    "ANSI-D": (558.8, 863.6),
    "ANSI-E": (863.6, 1117.6),
}

# ISO 5455 recommended scales, plus the x10 extensions shops actually use.
STANDARD_SCALES = {
    (1, 1),
    (1, 2),
    (1, 5),
    (1, 10),
    (1, 20),
    (1, 50),
    (1, 100),
    (1, 200),
    (1, 500),
    (1, 1000),
    (2, 1),
    (5, 1),
    (10, 1),
    (20, 1),
    (50, 1),
    (100, 1),
}

# Usual minimum for notes on a metric sheet (ISO 3098). Not a copy of the Y14.2 table.
MIN_LETTER_MM = 2.5

_SCALE = re.compile(r"(\d+)\s*:\s*(\d+)")
_INCH = re.compile(r"\d+(?:\.\d+)?\s*(?:\"|″)|(?:\bINCH(?:ES)?\b)", re.I)
_THIRD = re.compile(r"(THIRD|3RD)[\s\-]*ANGLE", re.I)
_FIRST = re.compile(r"(FIRST|1ST)[\s\-]*ANGLE", re.I)
_NTS = re.compile(r"\bN\.?T\.?S\.?\b|NOT\s+TO\s+SCALE", re.I)
_GENERAL_TOL = re.compile(
    r"UNLESS\s+OTHERWISE\s+SPECIFIED|GENERAL\s+TOL|ISO\s*2768|TOLERANCES?\s*[:.]?\s*±",
    re.I,
)
_TOL_ON_DIM = re.compile(r"±|\+/-|\+\s*\d|H[0-9]|h[0-9]|[A-Z][0-9]\b")
_ISO_MARK = re.compile(r"ISO\s*2768|ISO\s*8015|ISO\s*1101")
_ASME_MARK = re.compile(r"ASME\s*Y14|Y14\.5")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str


@dataclass
class DrawingFacts:
    insunits: int | None
    width_mm: float | None
    height_mm: float | None
    texts: list[str] = field(default_factory=list)
    text_heights: list[float] = field(default_factory=list)
    dimension_texts: list[str] = field(default_factory=list)
    frames: list[Frame] = field(default_factory=list)
    dimension_count: int = 0

    @property
    def blob(self) -> str:
        return "\n".join(self.texts)


def _entity_text(entity) -> str:
    chunks = entity.all(3) + entity.all(1)
    return dxf_plain("".join(chunks)).strip()


# $INSUNITS → millimetres. 1 inch, 4 mm, 5 cm, 6 m.
_TO_MM = {0: 1.0, 1: 25.4, 4: 1.0, 5: 10.0, 6: 1000.0}


def facts_from_doc(doc: DxfDoc) -> DrawingFacts:
    ins = header_number(doc, "$INSUNITS", 70)
    insunits = int(ins) if ins is not None else None
    span = header_pair_span(doc, "$LIMMIN", "$LIMMAX") or header_pair_span(doc, "$EXTMIN", "$EXTMAX")
    factor = _TO_MM.get(insunits, 1.0)
    facts = DrawingFacts(
        insunits=insunits,
        width_mm=span[0] * factor if span else None,
        height_mm=span[1] * factor if span else None,
    )
    for ent in doc.entities:
        if ent.type in ("TEXT", "MTEXT"):
            text = _entity_text(ent)
            if text:
                facts.texts.append(text)
            height = ent.first(40)
            if height:
                try:
                    facts.text_heights.append(float(height))
                except ValueError:
                    pass
        elif ent.type == "DIMENSION":
            facts.dimension_count += 1
            override = _entity_text(ent)
            if override:
                facts.dimension_texts.append(override)
                facts.texts.append(override)
            else:
                measured = ent.first(42)
                if measured:
                    facts.dimension_texts.append(measured)
        elif ent.type == "TOLERANCE":
            raw = "".join(ent.all(1) + ent.all(3))
            facts.frames.extend(parse_frames(raw))
            plain = dxf_plain(raw)
            if plain.strip():
                facts.texts.append(plain)
    for ent in doc.entities:
        if ent.type in ("TEXT", "MTEXT"):
            raw = "".join(ent.all(3) + ent.all(1))
            facts.frames.extend(parse_frames(raw))
    return facts


def _match_sheet(width: float, height: float, table: dict[str, tuple[float, float]]) -> str | None:
    a, b = sorted((width, height))
    for name, (sw, sh) in table.items():
        c, d = sorted((sw, sh))
        tol = max(8.0, 0.02 * d)
        if abs(a - c) <= tol and abs(b - d) <= tol:
            return name
    return None


def _dim_has_tolerance(text: str) -> bool:
    return bool(_TOL_ON_DIM.search(text))


def check_facts(facts: DrawingFacts, profile: str) -> list[Finding]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; use {', '.join(PROFILES)}")
    found: list[Finding] = []

    def add(severity: str, rule: str, message: str) -> None:
        found.append(Finding(rule, severity, message))

    blob = facts.blob

    if facts.insunits == 4:
        pass
    elif facts.insunits == 1:
        add("error", "units_not_millimetres", "DXF $INSUNITS is inches; Canada profiles expect millimetres")
    elif re.search(r"\bMM\b|MILLIMET", blob, re.I):
        add("warning", "units_header_blank", "notes say millimetres but $INSUNITS is not 4 (mm)")
    else:
        add("warning", "units_not_stated", "no millimetre units in $INSUNITS or in the notes")

    if _INCH.search(blob):
        add("error", "inch_callout", "an inch mark or the word INCH appears on a millimetre profile")

    if facts.width_mm is None or facts.height_mm is None:
        add("warning", "sheet_unknown", "no $LIMMIN/$LIMMAX or $EXTMIN/$EXTMAX; sheet size was not checked")
    else:
        iso = _match_sheet(facts.width_mm, facts.height_mm, ISO_SHEETS)
        ansi = _match_sheet(facts.width_mm, facts.height_mm, ANSI_SHEETS_MM)
        size = f"{facts.width_mm:.0f}×{facts.height_mm:.0f} mm"
        if iso:
            pass
        elif ansi:
            add(
                "warning",
                "sheet_not_iso",
                f"sheet matches {ansi} ({size}); Canada profiles expect an ISO A-series sheet",
            )
        else:
            add("warning", "sheet_size", f"sheet {size} is not an ISO A0–A4 size")

    scales = [(int(a), int(b)) for a, b in _SCALE.findall(blob)]
    odd = [f"{a}:{b}" for a, b in scales if (a, b) not in STANDARD_SCALES]
    if odd:
        add("warning", "scale_nonstandard", "scale not in the usual 1/2/5 series: " + ", ".join(odd))
    elif not scales and not _NTS.search(blob):
        add("warning", "scale_missing", "no scale (1:1, 2:1, …) and no NTS note")
    elif not scales and _NTS.search(blob):
        add("info", "scale_not_to_scale", "sheet is marked not-to-scale")

    third = bool(_THIRD.search(blob))
    first = bool(_FIRST.search(blob))
    if profile == "asme-ca":
        if first and not third:
            add("error", "projection_first_angle", "first-angle projection on asme-ca; Canada/ASME sheets are third-angle")
        elif not third and not first:
            add("warning", "projection_missing", "no third-angle (or first-angle) note")
        elif third and first:
            add("warning", "projection_both", "both first-angle and third-angle are mentioned")
    else:
        if not third and not first:
            add("warning", "projection_missing", "no first-angle or third-angle note")
        elif third and first:
            add("warning", "projection_both", "both first-angle and third-angle are mentioned")

    upper = blob.upper()
    if not re.search(r"\b(DWG|DRG|DRAWING)\b|\bNUMBER\b|\bNO\.\b", upper):
        add("warning", "title_number", "no drawing-number note (DWG, DRG, NUMBER)")
    if not re.search(r"\bREV\b|REVISION", upper):
        add("warning", "title_revision", "no revision note (REV)")

    general = bool(_GENERAL_TOL.search(blob))
    if facts.dimension_count == 0:
        add(
            "warning",
            "no_semantic_dimensions",
            "no DIMENSION entities; untoleranced sizes cannot be checked (exploded geometry)",
        )
    elif not general:
        bare = [t for t in facts.dimension_texts if t and not _dim_has_tolerance(t)]
        if bare:
            sample = ", ".join(bare[:3])
            add(
                "warning",
                "untoleranced_dimension",
                f"{len(bare)} dimension(s) have no tolerance and there is no general-tolerance note ({sample})",
            )

    if facts.insunits in (None, 4, 0):
        small = [h for h in facts.text_heights if 0 < h < MIN_LETTER_MM]
        if small:
            add(
                "warning",
                "lettering_small",
                f"{len(small)} text entity(s) under {MIN_LETTER_MM} mm",
            )

    if profile == "asme-ca" and _ISO_MARK.search(blob):
        add("warning", "standards_mixed", "ISO 2768 / 8015 / 1101 note on an asme-ca sheet")
    if profile == "iso-ca" and _ASME_MARK.search(blob):
        add("warning", "standards_mixed", "ASME Y14 note on an iso-ca sheet")

    seen: set[tuple[str, tuple[str, ...], str]] = set()
    for frame in facts.frames:
        key = (frame.symbol, frame.datums, frame.value)
        if key in seen:
            continue
        seen.add(key)
        bad = illegal_datums(frame)
        if bad:
            add(
                "error",
                "gdt_datum_letter",
                f"datum letter {', '.join(bad)} is I, O, or Q ({frame.symbol})",
            )
        if not value_has_number(frame):
            add("error", "gdt_missing_value", f"{frame.symbol} frame has no numeric tolerance")
        elif frame.policy == "datum" and not frame.datums:
            add("error", "gdt_datum_required", f"{frame.symbol} frame has no datum reference")
        elif frame.policy == "form" and frame.datums:
            add(
                "error",
                "gdt_form_has_datum",
                f"{frame.symbol} is a form control and should not reference a datum",
            )
        elif frame.policy == "unknown":
            add("info", "gdt_symbol_unclassified", f"geometric frame symbol {frame.symbol} was not classified")

    order = {"error": 0, "warning": 1, "info": 2}
    found.sort(key=lambda f: (order[f.severity], f.rule, f.message))
    return found
