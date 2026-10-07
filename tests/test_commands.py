from pathlib import Path

import pytest

from scad2drawing.commands import (
    DefineError,
    draftwright_cmd,
    git_clone_cmd,
    mesh_fallback_lines,
    output_stem,
    parse_defines,
    part_from_defines,
    scad2step_cmd,
    uv_sync_cmd,
)
from scad2drawing.pins import DRAFTWRIGHT, SCAD123D


def test_parse_defines_bare_selector():
    assert parse_defines(["part=frame", "holes=6"]) == ["part=frame", "holes=6"]


def test_parse_defines_rejects_missing_equals():
    with pytest.raises(DefineError):
        parse_defines(["frame"])


def test_parse_defines_rejects_nested_quotes():
    with pytest.raises(DefineError):
        parse_defines(['part="frame"'])
    with pytest.raises(DefineError):
        parse_defines(["part='frame'"])


def test_output_stem_includes_part():
    scad = Path("models/widget.scad")
    assert output_stem(scad, ["part=frame"]) == "widget_frame"
    assert output_stem(scad, []) == "widget"
    assert part_from_defines(["part=shaft"]) == "shaft"


def test_scad2step_argv_uses_uv_directory_not_uvx():
    env = Path("/content/scad123d")
    scad = Path("/content/work/a.scad")
    step = Path("/content/work/a_frame.step")
    cmd = scad2step_cmd(env, scad, step, ["part=frame"], timeout=90)
    assert cmd[:4] == ["uv", "run", "--directory", "/content/scad123d"]
    assert "uvx" not in cmd
    assert cmd[4] == "scad2step"
    assert "-D" in cmd and "part=frame" in cmd
    assert "--timeout" in cmd


def test_draftwright_argv():
    env = Path("/content/draftwright")
    step = Path("/tmp/part.step")
    cmd = draftwright_cmd(env, step, Path("/tmp/part"), title="Frame", formats="pdf,svg")
    assert cmd[:4] == ["uv", "run", "--directory", "/content/draftwright"]
    assert cmd[4] == "draftwright"
    assert "--format" in cmd
    assert "pdf,svg" in cmd
    assert "--title" in cmd


def test_bootstrap_fetch_pin_not_unlocked_resolve():
    dest = Path("envs/scad123d")
    cmds = git_clone_cmd(SCAD123D.repo, dest, SCAD123D.rev)
    assert cmds[0][0:3] == ["git", "clone", "--depth"]
    assert any("fetch" in c for c in cmds)
    assert uv_sync_cmd(dest) == ["uv", "sync", "--directory", str(dest)]
    assert DRAFTWRIGHT.rev.startswith("v")


def test_mesh_fallback_detection():
    log = "note: hull() has no BRep equivalent, using mesh fallback\nOK\n"
    hits = mesh_fallback_lines(log)
    assert hits and "mesh fallback" in hits[0].lower()
