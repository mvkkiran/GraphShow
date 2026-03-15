"""Streamlit component to embed the Cytoscape.js graph visualization."""

import json
import os
import streamlit.components.v1 as components

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "cytoscape_template.html")


def render_graph(elements: dict, height: int = 700, style_overrides: dict = None):
    """Render the Cytoscape.js graph inside Streamlit.

    Args:
        elements: Dict with 'nodes' and 'edges' in Cytoscape.js format.
        height: Pixel height of the graph canvas.
        style_overrides: Optional style overrides dict.
    """
    with open(TEMPLATE_PATH, "r") as f:
        html_template = f.read()

    elements_json = json.dumps(
        elements.get("nodes", []) + elements.get("edges", []),
        default=str,
    )
    style_json = json.dumps(style_overrides or {})

    html = html_template.replace("__ELEMENTS__", elements_json)
    html = html_template.replace("__ELEMENTS__", elements_json).replace("__STYLE_OVERRIDES__", style_json)

    components.html(html, height=height, scrolling=False)
