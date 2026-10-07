import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "GEMINI_COLAB_SOP_V2.md"
NOTEBOOK = ROOT / "notebooks" / "scad2drawing_v2.ipynb"


def _source(nb) -> str:
    return "\n".join("".join(c.get("source", [])) for c in nb["cells"])


def test_v2_sop_exists_and_forbids_uvx():
    text = SOP.read_text()
    assert "scad2drawing convert" in text
    assert "--parts" in text
    assert "--on-mesh" in text
    assert "needs-attention" in text
    assert "v2_draw_worker.py" in text
    assert "GEMINI_COLAB_SOP_V2.md" in text
    assert "uvx" in text.lower()
    assert "import draftwright in the notebook kernel" in text.lower() or (
        "import draftwright" in text and "kernel" in text
    )


def test_every_gemini_sop_embeds_the_same_capability_index():
    index = (ROOT / "GEMINI_CAPACITY_INDEX.txt").read_text().strip()
    assert index.startswith("<<<CAPABILITY_INDEX")
    assert index.endswith("<<<END_CAPABILITY_INDEX>>>")
    assert "drawingmaster.check" in index
    assert "scad2drawing.convert" in index
    assert "forbidden=" in index
    for name in (
        "GEMINI_COLAB_SOP.md",
        "GEMINI_COLAB_SOP_V2.md",
        "GEMINI_COLAB_SOP_DRAWINGMASTER.md",
    ):
        text = (ROOT / name).read_text()
        assert text.count(index) == 1, name


def test_v2_notebook_is_convert_not_raw_cli():
    nb = json.loads(NOTEBOOK.read_text())
    text = _source(nb)
    assert ">>> EDIT THIS CELL ONLY <<<" in text
    assert "MODEL_NAME" in text
    assert "PARTS" in text
    assert "ON_MESH" in text
    assert "NEED_BOSL2" in text
    assert "scad2drawing" in text and "convert" in text
    assert "--parts" in text
    assert "bootstrap" in text
    assert "pip" in text and "-e" in text
    assert "GEMINI_COLAB_SOP_V2.md" in text
    assert "GEMINI_COLAB_SOP_DRAWINGMASTER.md" in text
    assert "GEMINI_CAPACITY_INDEX.txt" in text
    assert "CAPABILITY_INDEX" in text
    assert "Never uvx" in text or "never uvx" in text.lower()
    # Drawing path is the glue CLI, not a kernel import
    assert "from draftwright" not in text
    assert "import draftwright" in text.lower()  # mentioned as forbidden / worker-only


def test_v2_notebook_keeps_svg_and_lint_docs():
    text = _source(json.loads(NOTEBOOK.read_text()))
    assert "pdf,svg" in text
    assert "needs-attention" in text
    assert "DWG-{part}" in text
