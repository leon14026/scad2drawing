from pathlib import Path

from scad2drawing.cli import build_parser


def test_help_lists_subcommands():
    parser = build_parser()
    names = {a.dest for a in parser._subparsers._group_actions}
    # argparse stores subparsers oddly; parse --help via the names we set
    text = parser.format_help()
    assert "bootstrap" in text
    assert "convert" in text
    assert "smoke" in text


def test_convert_defaults():
    args = build_parser().parse_args(["convert", "a.scad"])
    assert args.out == "out"
    assert args.defines == []
    assert args.formats == "pdf,svg"
    assert args.draw == "worker"
    assert args.on_mesh == "warn"
    assert args.parts is None


def test_convert_repeatable_defines():
    args = build_parser().parse_args(
        ["convert", "a.scad", "-D", "part=frame", "-D", "holes=6"]
    )
    assert args.defines == ["part=frame", "holes=6"]


def test_v2_convert_flags():
    args = build_parser().parse_args(
        [
            "convert",
            "a.scad",
            "--parts",
            "frame,shaft",
            "--on-mesh",
            "views-only",
            "--draw",
            "worker",
            "--title",
            "Part {part}",
            "--keep-going",
        ]
    )
    assert args.parts == "frame,shaft"
    assert args.on_mesh == "views-only"
    assert args.draw == "worker"
    assert args.title == "Part {part}"
    assert args.keep_going is True


def test_v1_cli_draw_still_available():
    args = build_parser().parse_args(["convert", "a.scad", "--draw", "cli"])
    assert args.draw == "cli"


def test_smoke_defaults_to_worker():
    args = build_parser().parse_args(["smoke", "-o", "out"])
    assert args.draw == "worker"
    assert Path(args.out).name == "out"
