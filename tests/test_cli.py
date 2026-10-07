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


def test_convert_repeatable_defines():
    args = build_parser().parse_args(
        ["convert", "a.scad", "-D", "part=frame", "-D", "holes=6"]
    )
    assert args.defines == ["part=frame", "holes=6"]
