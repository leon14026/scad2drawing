"""Minimal ASCII DXF reader. Enough for sheet headers and annotation entities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


class DxfError(ValueError):
    pass


@dataclass
class Entity:
    type: str
    values: dict[int, list[str]] = field(default_factory=dict)

    def first(self, code: int, default: str | None = None) -> str | None:
        got = self.values.get(code)
        if not got:
            return default
        return got[0]

    def all(self, code: int) -> list[str]:
        return list(self.values.get(code, []))


@dataclass
class DxfDoc:
    header: dict[str, list[tuple[int, str]]]
    entities: list[Entity]


_UNICODE = re.compile(r"\\U\+([0-9A-Fa-f]{4,6})")
_MTEXT_CTRL = re.compile(r"\\[A-Za-z][^;\\]*;")


def dxf_plain(raw: str) -> str:
    """Strip MTEXT / %% controls to readable text. Drops font switches, including gdt."""
    text = raw.replace("\\P", "\n").replace("\\~", " ")
    text = text.replace("%%c", "Ø").replace("%%C", "Ø")
    text = text.replace("%%d", "°").replace("%%D", "°")
    text = text.replace("%%p", "±").replace("%%P", "±")
    text = text.replace("%%%", "%")
    text = _UNICODE.sub(lambda m: chr(int(m.group(1), 16)), text)
    text = _MTEXT_CTRL.sub("", text)
    return text.replace("{", "").replace("}", "")


def _pairs(text: str) -> list[tuple[int, str]]:
    if text.startswith("AutoCAD Binary DXF"):
        raise DxfError("binary DXF is not supported; export ASCII DXF")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) % 2 != 0:
        raise DxfError("DXF group codes are not in code/value pairs")
    out: list[tuple[int, str]] = []
    for i in range(0, len(lines), 2):
        raw = lines[i].strip()
        try:
            code = int(raw)
        except ValueError as exc:
            raise DxfError(f"bad DXF group code {raw!r}") from exc
        out.append((code, lines[i + 1].strip()))
    return out


def _take_entity(pairs: list[tuple[int, str]], start: int) -> tuple[Entity, int]:
    etype = pairs[start][1]
    values: dict[int, list[str]] = {}
    i = start + 1
    while i < len(pairs) and pairs[i][0] != 0:
        code, value = pairs[i]
        values.setdefault(code, []).append(value)
        i += 1
    return Entity(etype, values), i


def parse_dxf(text: str) -> DxfDoc:
    pairs = _pairs(text)
    header: dict[str, list[tuple[int, str]]] = {}
    entities: list[Entity] = []
    i = 0
    section: str | None = None
    while i < len(pairs):
        code, value = pairs[i]
        if code == 0 and value == "SECTION" and i + 1 < len(pairs) and pairs[i + 1][0] == 2:
            section = pairs[i + 1][1]
            i += 2
            continue
        if code == 0 and value == "ENDSEC":
            section = None
            i += 1
            continue
        if section == "HEADER" and code == 9:
            name = value
            i += 1
            body: list[tuple[int, str]] = []
            while i < len(pairs) and pairs[i][0] not in (0, 9):
                body.append(pairs[i])
                i += 1
            header[name] = body
            continue
        if section in ("ENTITIES", "BLOCKS") and code == 0 and value not in ("ENDSEC", "SECTION", "EOF"):
            if value in ("TEXT", "MTEXT", "DIMENSION", "TOLERANCE"):
                ent, i = _take_entity(pairs, i)
                entities.append(ent)
                continue
            i += 1
            continue
        i += 1
    return DxfDoc(header, entities)


def header_number(doc: DxfDoc, name: str, code: int) -> float | None:
    for group, value in doc.header.get(name, []):
        if group == code:
            try:
                return float(value)
            except ValueError:
                return None
    return None


def header_pair_span(doc: DxfDoc, min_name: str, max_name: str) -> tuple[float, float] | None:
    def xy(name: str) -> tuple[float, float] | None:
        x = header_number(doc, name, 10)
        y = header_number(doc, name, 20)
        if x is None or y is None:
            return None
        return x, y

    lo = xy(min_name)
    hi = xy(max_name)
    if lo is None or hi is None:
        return None
    return abs(hi[0] - lo[0]), abs(hi[1] - lo[1])
