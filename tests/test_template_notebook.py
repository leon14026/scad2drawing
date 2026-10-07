import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "notebooks" / "scad2drawing_template.ipynb"


def _source(nb) -> str:
    return "\n".join("".join(c.get("source", [])) for c in nb["cells"])


def test_template_notebook_exists_and_has_config():
    nb = json.loads(TEMPLATE.read_text())
    text = _source(nb)
    assert ">>> EDIT THIS CELL ONLY <<<" in text
    assert "MODEL_NAME" in text
    assert "PARTS" in text
    assert "NEED_BOSL2" in text
    assert '"uv"' in text and '"run"' in text
    assert "--directory" in text


def test_template_forbids_uvx_and_kernel_imports():
    text = _source(json.loads(TEMPLATE.read_text()))
    assert "Never uvx" in text or "never uvx" in text.lower() or "Do **not** use `uvx`" in text
    assert "import draftwright" in text.lower()
    # Must not tell the user to run uvx as the installer
    assert "uvx scad2step" not in text or "Never uvx" in text or "not" in text.lower()
