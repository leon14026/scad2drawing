"""Feature-control frames stored as DXF TOLERANCE text or gdt font codes.

AutoCAD gdt.shx letters confirmed from published TOLERANCE samples:
``j`` position, ``r`` concentricity, ``n`` diameter zone, ``m`` MMC, ``l`` LMC.
Other letters stay unclassified so a wrong guess cannot invent a failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# symbol → datum policy: "form" (no datum), "datum" (datum required), "optional"
_UNICODE = {
    "⏤": ("straightness", "form"),
    "⏥": ("flatness", "form"),
    "⌭": ("cylindricity", "form"),
    "⌒": ("profile_line", "optional"),
    "⌓": ("profile_surface", "optional"),
    "∠": ("angularity", "datum"),
    "⟂": ("perpendicularity", "datum"),
    "⊥": ("perpendicularity", "datum"),
    "∥": ("parallelism", "datum"),
    "⌖": ("position", "datum"),
    "◎": ("concentricity", "datum"),
    "⌯": ("symmetry", "datum"),
}

_GDT_LETTERS = {
    "j": ("position", "datum"),
    "r": ("concentricity", "datum"),
}

_MODIFIERS = {"n": "diameter", "m": "mmc", "l": "lmc"}

_FONT = re.compile(r"\\[Ff]gdt;([A-Za-z])")
_ILLEGAL_DATUMS = set("IOQ")


@dataclass(frozen=True)
class Frame:
    symbol: str
    policy: str
    value: str
    datums: tuple[str, ...]
    raw: str


def _letters(compartment: str) -> list[str]:
    cleaned = compartment
    cleaned = _FONT.sub("", cleaned)
    cleaned = cleaned.upper()
    cleaned = re.sub(r"[^A-Z]", "", cleaned)
    return list(cleaned)


def parse_frames(raw: str) -> list[Frame]:
    frames: list[Frame] = []
    for chunk in re.split(r"\\P", raw):
        if "Fgdt" not in chunk and not any(ch in chunk for ch in _UNICODE):
            continue
        parts = chunk.split("%%v")
        symbol = "unclassified"
        policy = "unknown"
        head = parts[0] if parts else ""
        for ch, (name, pol) in _UNICODE.items():
            if ch in head or ch in chunk:
                symbol, policy = name, pol
                break
        for code in _FONT.findall(head):
            key = code.lower()
            if key in _MODIFIERS:
                continue
            if key in _GDT_LETTERS:
                symbol, policy = _GDT_LETTERS[key]
            else:
                symbol, policy = f"gdt:{key}", "unknown"
            break
        value = parts[1] if len(parts) > 1 else ""
        datums: list[str] = []
        for comp in parts[2:]:
            datums.extend(_letters(comp))
        if symbol == "unclassified" and not datums and not re.search(r"\d", value):
            continue
        frames.append(Frame(symbol, policy, value, tuple(datums), chunk.strip()))
    return frames


def illegal_datums(frame: Frame) -> list[str]:
    return [d for d in frame.datums if d in _ILLEGAL_DATUMS]


def value_has_number(frame: Frame) -> bool:
    return bool(re.search(r"\d", frame.value))
