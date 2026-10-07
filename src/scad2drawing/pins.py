"""Upstream git pins. Keep in sync with /pins.toml at the repo root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS_TOML = ROOT / "pins.toml"


@dataclass(frozen=True)
class Pin:
    repo: str
    rev: str


SCAD123D = Pin(
    repo="https://github.com/etjones/scad123d.git",
    rev="85811a1a9daa291fb9ebfdfd8339322a9ec5b52c",
)
DRAFTWRIGHT = Pin(
    repo="https://github.com/pzfreo/draftwright.git",
    rev="v0.4.35",
)
BOSL2 = Pin(
    repo="https://github.com/BelfrySCAD/BOSL2.git",
    rev="master",
)

SCAD_DIRNAME = "scad123d"
DRAW_DIRNAME = "draftwright"


def samples_dir() -> Path:
    return ROOT / "samples"
