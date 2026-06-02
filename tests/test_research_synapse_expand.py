from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_research_synapse_has_expand_control_and_dialog():
    js = _read("static/js/researchSynapse.js")

    assert "class=\"rs-expand-btn\"" in js
    assert "aria-label=\"Expand research visualization\"" in js
    assert "research-synapse-overlay" in js
    assert "role', 'dialog'" in js
    assert "Deep Research Map" in js
    assert "research-synapse-close" in js


def test_research_synapse_restores_original_position_on_close():
    js = _read("static/js/researchSynapse.js")

    assert "originalParent = wrap.parentNode" in js
    assert "originalNextSibling = wrap.nextSibling" in js
    assert "research-synapse-placeholder" in js
    assert "placeholder.parentNode.insertBefore(wrap, placeholder)" in js
    assert "document.removeEventListener('keydown', _onExpandedKeydown)" in js
    assert "if (e.key === 'Escape') _closeExpanded()" in js


def test_research_synapse_public_api_reports_expanded_state():
    js = _read("static/js/researchSynapse.js")

    assert "isExpanded()" in js
    assert "return expanded;" in js
    assert "destroy() {" in js
    assert "_closeExpanded();" in js


def test_research_panel_does_not_remount_expanded_synapse():
    panel_js = _read("static/js/research/panel.js")

    assert "entry.synapse.isExpanded" in panel_js
    assert "!entry.synapse.isExpanded()" in panel_js
    assert "host.appendChild(entry.synapse.element)" in panel_js


def test_research_synapse_expand_styles_exist():
    css = _read("static/style.css")

    assert ".research-synapse .rs-toolbar" in css
    assert ".research-synapse .rs-expand-btn" in css
    assert ".research-synapse-overlay" in css
    assert ".research-synapse-shell" in css
    assert ".research-synapse.research-synapse-expanded .rs-stage" in css
    assert "@media (max-width: 700px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
