"""V2 worker + convert_one fail-soft. No CAD imports."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from scad2drawing import cli
from scad2drawing.pins import ROOT

WORKER = ROOT / "scripts" / "v2_draw_worker.py"


def _load_worker():
    spec = importlib.util.spec_from_file_location("v2_draw_worker", WORKER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_package_never_imports_draftwright():
    src = Path(__file__).resolve().parents[1] / "src" / "scad2drawing"
    for path in src.glob("*.py"):
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            stripped = line.strip()
            assert not stripped.startswith("import draftwright"), f"{path}:{i}"
            assert not stripped.startswith("from draftwright"), f"{path}:{i}"


def test_worker_parse_formats():
    mod = _load_worker()
    assert mod.parse_formats("pdf,svg") == ("pdf", "svg")
    assert mod.parse_formats("all") == ("pdf", "svg", "dxf", "png")
    with pytest.raises(SystemExit):
        mod.parse_formats("igs")
    with pytest.raises(SystemExit):
        mod.parse_formats("")


def test_worker_main_uses_auto_dims(tmp_path, monkeypatch):
    step = tmp_path / "p.step"
    step.write_text("ISO-10303-21;")
    report = tmp_path / "p.draftwright.json"
    report.write_text("{}\n")

    fake_dwg = SimpleNamespace()
    calls: dict = {}

    def build_drawing(path, **kwargs):
        calls["step"] = path
        calls["kwargs"] = kwargs
        return fake_dwg

    def export(prefix, formats=None):
        calls["export"] = (prefix, formats)
        return {"pdf": str(tmp_path / "p.pdf")}

    def write_report(path):
        Path(path).write_text("{}\n")
        return str(path)

    fake_dwg.export = export
    fake_dwg.write_report = write_report

    fake_mod = ModuleType("draftwright")
    fake_mod.build_drawing = build_drawing
    monkeypatch.setitem(sys.modules, "draftwright", fake_mod)

    mod = _load_worker()
    mod.main(
        [
            "--step",
            str(step),
            "--out",
            str(tmp_path / "p"),
            "--title",
            "Hull",
            "--no-auto-dims",
            "--mesh-fallback",
            "--format",
            "pdf",
        ]
    )
    assert calls["kwargs"]["auto_dims"] is False
    assert calls["kwargs"]["title"] == "Hull"
    stamped = report.read_text()
    assert "mesh_fallback" in stamped


def _envs(tmp_path: Path) -> tuple[Path, Path]:
    scad_env = tmp_path / "scad123d"
    draw_env = tmp_path / "draftwright"
    scad_env.mkdir()
    draw_env.mkdir()
    (scad_env / "pyproject.toml").write_text("[project]\nname='s'\n")
    (draw_env / "pyproject.toml").write_text("[project]\nname='d'\n")
    return scad_env, draw_env


def test_convert_one_skip_draw_on_mesh(tmp_path, monkeypatch):
    scad = tmp_path / "hull.scad"
    scad.write_text("hull() { sphere(1); }\n")
    out = tmp_path / "out"
    out.mkdir()
    scad_env, draw_env = _envs(tmp_path)
    draw_cmds: list[list[str]] = []

    def fake_run(cmd, *, log=None, check=True):
        if "scad2step" in cmd:
            step = Path(cmd[cmd.index("-o") + 1])
            step.write_text("ISO-10303-21;")
            proc = SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="note: hull() has no BRep equivalent, using mesh fallback\n",
            )
            if log is not None:
                log.write_text(proc.stdout + proc.stderr)
            return proc
        draw_cmds.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "_run", fake_run)
    status = cli.convert_one(
        scad=scad,
        out_dir=out,
        defines=[],
        title=None,
        number="DWG-001",
        formats="pdf",
        timeout=30,
        skip_step=False,
        skip_draw=False,
        scad_env=scad_env,
        draw_env=draw_env,
        on_mesh="skip-draw",
        draw="worker",
        check=True,
    )
    assert status == "skipped-draw"
    assert not draw_cmds
    note = out / "hull.MESH_FALLBACK.txt"
    assert note.is_file()
    assert "mesh fallback" in note.read_text().lower()


def test_convert_one_views_only_passes_no_auto_dims(tmp_path, monkeypatch):
    scad = tmp_path / "hull.scad"
    scad.write_text("hull() { sphere(1); }\n")
    out = tmp_path / "out"
    out.mkdir()
    scad_env, draw_env = _envs(tmp_path)
    seen: list[list[str]] = []

    def fake_run(cmd, *, log=None, check=True):
        if "scad2step" in cmd:
            Path(cmd[cmd.index("-o") + 1]).write_text("ISO-10303-21;")
            proc = SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="MeshFallback: falling back to mesh\n",
            )
            if log is not None:
                log.write_text(proc.stderr)
            return proc
        seen.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "_run", fake_run)
    status = cli.convert_one(
        scad=scad,
        out_dir=out,
        defines=[],
        title="Hull",
        number="DWG-001",
        formats="pdf",
        timeout=30,
        skip_step=False,
        skip_draw=False,
        scad_env=scad_env,
        draw_env=draw_env,
        on_mesh="views-only",
        draw="worker",
        check=True,
    )
    assert status == "mesh-warned"
    assert seen and "--no-auto-dims" in seen[0]
    assert "--mesh-fallback" in seen[0]
    assert "python" in seen[0]
    assert "v2_draw_worker.py" in seen[0][-1] or any(
        "v2_draw_worker.py" in str(x) for x in seen[0]
    )


def test_convert_one_flags_lint_needs_attention(tmp_path, monkeypatch):
    scad = tmp_path / "wheel.scad"
    scad.write_text("cylinder(d=40, h=5);\n")
    out = tmp_path / "out"
    out.mkdir()
    scad_env, draw_env = _envs(tmp_path)

    def fake_run(cmd, *, log=None, check=True):
        if "scad2step" in cmd:
            Path(cmd[cmd.index("-o") + 1]).write_text("ISO-10303-21;")
            proc = SimpleNamespace(returncode=0, stdout="", stderr="")
            if log is not None:
                log.write_text("")
            return proc
        out.joinpath("wheel.draftwright.json").write_text(
            '{"status":"needs-attention","lint":{"errors":1,"warnings":0,'
            '"assessment":{"status":"needs-attention","summary":"incomplete"},'
            '"issues":[{"severity":"error","code":"overall_dim_withheld","message":"width"}]}}'
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "_run", fake_run)
    status = cli.convert_one(
        scad=scad,
        out_dir=out,
        defines=[],
        title="Wheel",
        number="DWG-001",
        formats="pdf,svg",
        timeout=30,
        skip_step=False,
        skip_draw=False,
        scad_env=scad_env,
        draw_env=draw_env,
        on_mesh="warn",
        draw="worker",
        check=True,
    )
    assert status == "needs-attention"


def test_cmd_convert_loops_parts(tmp_path, monkeypatch):
    scad = tmp_path / "selector.scad"
    scad.write_text("cube(1);\n")
    jobs: list[dict] = []

    def fake_one(**kwargs):
        jobs.append(kwargs)
        return "ok"

    monkeypatch.setattr(cli, "convert_one", fake_one)
    monkeypatch.setattr(cli, "_require", lambda _name: None)
    ns = argparse.Namespace(
        scad=str(scad),
        out=str(tmp_path / "out"),
        defines=[],
        parts="frame,shaft",
        title="Part {part}",
        number="DWG-{part}",
        formats="pdf",
        timeout=30,
        skip_step=False,
        skip_draw=True,
        scad_env=None,
        draw_env=None,
        on_mesh="warn",
        draw="worker",
        keep_going=False,
    )
    cli.cmd_convert(ns)
    assert [j["defines"] for j in jobs] == [["part=frame"], ["part=shaft"]]
    assert [j["title"] for j in jobs] == ["Part frame", "Part shaft"]
    assert [j["number"] for j in jobs] == ["DWG-frame", "DWG-shaft"]
    assert all(j["check"] is False for j in jobs)  # --parts implies keep-going


def test_cmd_convert_keep_going_exits_1_if_any_failed(tmp_path, monkeypatch):
    scad = tmp_path / "selector.scad"
    scad.write_text("cube(1);\n")
    results = ["failed", "ok"]

    def fake_one(**kwargs):
        return results.pop(0)

    monkeypatch.setattr(cli, "convert_one", fake_one)
    monkeypatch.setattr(cli, "_require", lambda _name: None)
    ns = argparse.Namespace(
        scad=str(scad),
        out=str(tmp_path / "out"),
        defines=[],
        parts="frame,shaft",
        title=None,
        number="DWG-001",
        formats="pdf",
        timeout=30,
        skip_step=True,
        skip_draw=True,
        scad_env=None,
        draw_env=None,
        on_mesh="warn",
        draw="worker",
        keep_going=True,
    )
    with pytest.raises(SystemExit) as exc:
        cli.cmd_convert(ns)
    assert exc.value.code == 1
