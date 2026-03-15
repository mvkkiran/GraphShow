"""
Knowledge Graph Visualization Dashboard
========================================
A professional Knowledge Graph Explorer for RDF/OWL data,
powered by Streamlit + Cytoscape.js. Optimized for Databricks Apps.
"""

import json
import os
import streamlit as st
from rdflib import Graph

from utils.rdf_parser import (
    parse_rdf, extract_namespaces, extract_classes,
    extract_properties, get_node_details, FORMAT_MAP,
)
from utils.graph_converter import convert_graph, filter_elements
from utils.sparql_engine import run_sparql, EXAMPLE_QUERIES
from utils.stats import compute_stats
from components.cytoscape_component import render_graph

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Knowledge Graph Explorer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid #334155;
    }
    .block-container { padding-top: 1rem; }

    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    /* Node detail card */
    .node-card {
        background: linear-gradient(135deg, #1e293b, #1e1b4b);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .node-card h4 {
        color: #e2e8f0;
        margin-bottom: 8px;
    }
    .node-uri {
        font-size: 11px;
        color: #64748b;
        word-break: break-all;
        margin-bottom: 8px;
    }
    .node-type-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        color: white;
        margin-bottom: 8px;
    }
    .prop-table {
        width: 100%;
        font-size: 12px;
    }
    .prop-table td {
        padding: 4px 8px;
        border-bottom: 1px solid #334155;
    }
    .prop-key { color: #94a3b8; width: 35%; }
    .prop-val { color: #e2e8f0; }

    /* Class tree */
    .class-tree-item {
        padding: 4px 8px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        transition: background 0.2s;
        margin: 2px 0;
    }
    .class-tree-item:hover {
        background: rgba(99, 102, 241, 0.2);
    }

    /* Logo area */
    .logo-area {
        text-align: center;
        padding: 16px 0;
        margin-bottom: 16px;
        border-bottom: 1px solid #334155;
    }
    .logo-area h1 {
        font-size: 22px;
        background: linear-gradient(135deg, #6366f1, #06b6d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .logo-area p {
        color: #64748b;
        font-size: 11px;
        margin: 4px 0 0 0;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 8px 8px 0 0;
        border: 1px solid #334155;
        padding: 8px 16px;
    }

    /* SPARQL output */
    .sparql-results {
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "rdf_graph" not in st.session_state:
    st.session_state.rdf_graph = None
if "elements" not in st.session_state:
    st.session_state.elements = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "classes" not in st.session_state:
    st.session_state.classes = []
if "selected_node" not in st.session_state:
    st.session_state.selected_node = None
if "max_nodes" not in st.session_state:
    st.session_state.max_nodes = 1000
if "style_overrides" not in st.session_state:
    st.session_state.style_overrides = {}
if "graph_height" not in st.session_state:
    st.session_state.graph_height = 650

# ---------------------------------------------------------------------------
# Helper: load example graph
# ---------------------------------------------------------------------------
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "examples", "example_ontology.ttl")

def load_example():
    """Load the bundled example ontology."""
    if os.path.exists(EXAMPLE_PATH):
        with open(EXAMPLE_PATH, "rb") as f:
            data = f.read()
        _process_graph(data, "example_ontology.ttl")
        st.success("Example ontology loaded!")
    else:
        st.error("Example file not found.")


def _process_graph(data: bytes, filename: str):
    """Parse uploaded data and populate session state."""
    g = parse_rdf(data, filename)
    st.session_state.rdf_graph = g
    st.session_state.stats = compute_stats(g)
    st.session_state.classes = extract_classes(g)
    st.session_state.elements = convert_graph(g, max_nodes=st.session_state.max_nodes)
    st.session_state.selected_node = None


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="logo-area">
        <h1>🔗 GraphShow</h1>
        <p>Knowledge Graph Explorer</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Upload section ----
    st.markdown("#### 📂 Load Graph")
    uploaded_file = st.file_uploader(
        "Upload RDF / OWL file",
        type=["rdf", "xml", "owl", "ttl", "n3", "nt", "jsonld", "json", "trig", "nq"],
        help="Supported: RDF/XML, Turtle, N3, OWL, JSON-LD, N-Triples, TriG",
    )
    if uploaded_file is not None:
        data = uploaded_file.read()
        with st.spinner("Parsing graph..."):
            try:
                _process_graph(data, uploaded_file.name)
                st.success(f"Loaded **{uploaded_file.name}** — {st.session_state.stats['total_triples']} triples")
            except Exception as e:
                st.error(f"Parse error: {e}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 Example", use_container_width=True, help="Load example ontology"):
            load_example()
    with col2:
        if st.button("🔄 Reset", use_container_width=True, help="Clear graph"):
            for key in ["rdf_graph", "elements", "stats", "classes", "selected_node"]:
                st.session_state[key] = None
            st.rerun()

    st.divider()

    # ---- Display settings ----
    st.markdown("#### ⚙️ Display Settings")
    st.session_state.max_nodes = st.slider(
        "Max nodes to render", 50, 5000, st.session_state.max_nodes, 50,
        help="Limit nodes for performance on large graphs",
    )
    st.session_state.graph_height = st.slider(
        "Graph canvas height (px)", 400, 1000, st.session_state.graph_height, 50,
    )

    if st.session_state.rdf_graph is not None and st.button("Apply node limit", use_container_width=True):
        st.session_state.elements = convert_graph(
            st.session_state.rdf_graph, max_nodes=st.session_state.max_nodes
        )
        st.rerun()

    st.divider()

    # ---- Class Explorer ----
    if st.session_state.classes:
        st.markdown("#### 🏗️ Ontology Classes")

        # Build class tree
        classes = st.session_state.classes
        class_uris = {c["uri"] for c in classes}

        # Top-level classes (no parent in class set)
        roots = [c for c in classes if not any(p in class_uris for p in c["parents"])]
        children_map = {}
        for c in classes:
            for p in c["parents"]:
                if p in class_uris:
                    children_map.setdefault(p, []).append(c)

        def render_tree(cls_list, indent=0):
            for c in sorted(cls_list, key=lambda x: x["label"]):
                prefix = "│  " * indent + ("├─ " if indent > 0 else "")
                label = f"{prefix}**{c['label']}**"
                if st.button(label, key=f"cls_{c['uri']}", use_container_width=True):
                    st.session_state.selected_node = c["uri"]
                kids = children_map.get(c["uri"], [])
                if kids:
                    render_tree(kids, indent + 1)

        render_tree(roots)

    st.divider()

    # ---- Filtering ----
    if st.session_state.elements:
        st.markdown("#### 🔍 Filters")

        # Namespace filter
        if st.session_state.stats:
            all_ns = list(st.session_state.stats["namespaces"].values())
            if all_ns:
                selected_ns = st.multiselect("Namespaces", all_ns, default=all_ns, key="ns_filter")
            else:
                selected_ns = None
        else:
            selected_ns = None

        # Predicate filter
        edges = st.session_state.elements.get("edges", [])
        all_predicates = sorted({e["data"]["predicate"] for e in edges})
        if all_predicates:
            selected_preds = st.multiselect(
                "Predicates", all_predicates,
                default=all_predicates, key="pred_filter",
                format_func=lambda p: p.split("#")[-1] if "#" in p else p.split("/")[-1],
            )
        else:
            selected_preds = None

        if st.button("Apply Filters", use_container_width=True, key="apply_filters"):
            filtered = filter_elements(
                st.session_state.elements,
                namespace_filter=selected_ns,
                predicate_filter=selected_preds,
            )
            st.session_state.elements = {
                **st.session_state.elements,
                "nodes": filtered["nodes"],
                "edges": filtered["edges"],
            }
            st.rerun()

    # ---- Style Editor ----
    if st.session_state.elements:
        st.divider()
        st.markdown("#### 🎨 Style Editor")
        with st.expander("Node & Edge Styles"):
            class_color = st.color_picker("Class node color", "#6366f1", key="cls_color")
            instance_color = st.color_picker("Instance node color", "#06b6d4", key="inst_color")
            literal_color = st.color_picker("Literal node color", "#f59e0b", key="lit_color")
            edge_width = st.slider("Edge width", 0.5, 5.0, 1.5, 0.5, key="edge_w")
            node_scale = st.slider("Node size scale", 0.5, 3.0, 1.0, 0.1, key="node_s")

            if st.button("Apply Styles", key="apply_style"):
                # Recolor nodes
                for node in st.session_state.elements["nodes"]:
                    nt = node["data"].get("node_type")
                    if nt == "class":
                        node["data"]["color"] = class_color
                    elif nt == "instance":
                        node["data"]["color"] = instance_color
                    elif nt == "literal":
                        node["data"]["color"] = literal_color
                    node["data"]["size"] = int(node["data"]["size"] * node_scale)
                for edge in st.session_state.elements["edges"]:
                    edge["data"]["width"] = edge_width
                st.rerun()


# ---------------------------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------------------------
if st.session_state.elements is None:
    # Landing page
    st.markdown("""
    <div style="text-align:center; padding:80px 20px;">
        <h1 style="font-size:48px; background: linear-gradient(135deg, #6366f1, #06b6d4, #10b981);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🔗 GraphShow
        </h1>
        <p style="font-size:18px; color:#94a3b8; max-width:600px; margin:16px auto;">
            Upload an RDF, OWL, Turtle, or JSON-LD file to explore your Knowledge Graph
            with interactive visualization powered by Cytoscape.js.
        </p>
        <p style="color:#64748b; font-size:13px; margin-top:24px;">
            Supported formats: RDF/XML • Turtle • N3 • OWL • JSON-LD • N-Triples • TriG
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# Stats bar
# ---------------------------------------------------------------------------
stats = st.session_state.stats
if stats:
    cols = st.columns(6)
    stat_items = [
        ("Triples", stats["total_triples"]),
        ("Nodes", stats["total_nodes"]),
        ("Classes", stats["classes_count"]),
        ("Instances", stats["instances_count"]),
        ("Properties", stats["total_predicates"]),
        ("Namespaces", stats["namespaces_count"]),
    ]
    for col, (label, value) in zip(cols, stat_items):
        col.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{value:,}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")  # spacing

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_graph, tab_sparql, tab_details, tab_stats = st.tabs([
    "📊 Graph Visualization",
    "🔎 SPARQL Query",
    "📋 Node Inspector",
    "📈 Statistics",
])

# ---- Graph tab ----
with tab_graph:
    elements = st.session_state.elements
    if elements.get("stats", {}).get("truncated"):
        st.warning(f"Graph truncated to {st.session_state.max_nodes} nodes. Adjust the limit in settings.")

    render_graph(elements, height=st.session_state.graph_height, style_overrides=st.session_state.style_overrides)

    # Search bar under graph
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search nodes by URI, label, or type", key="node_search",
                                     placeholder="Type to search...")
    with search_col2:
        st.markdown("")
        st.markdown("")
        if search_query:
            q = search_query.lower()
            matches = [
                n for n in elements["nodes"]
                if q in n["data"].get("label", "").lower()
                or q in n["data"].get("id", "").lower()
                or q in n["data"].get("node_type", "").lower()
            ]
            st.info(f"Found {len(matches)} matching node(s)")

    if search_query:
        q = search_query.lower()
        matches = [
            n for n in elements["nodes"]
            if q in n["data"].get("label", "").lower()
            or q in n["data"].get("id", "").lower()
        ]
        if matches:
            st.markdown("**Search Results:**")
            for m in matches[:20]:
                d = m["data"]
                badge_color = {
                    "class": "#6366f1", "instance": "#06b6d4",
                    "literal": "#f59e0b", "property": "#10b981",
                }.get(d.get("node_type"), "#64748b")
                st.markdown(
                    f'<span style="background:{badge_color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:10px;margin-right:8px;">'
                    f'{d.get("node_type", "?")}</span> **{d["label"]}** '
                    f'<span style="color:#64748b;font-size:11px;">— {d["id"]}</span>',
                    unsafe_allow_html=True,
                )

# ---- SPARQL tab ----
with tab_sparql:
    if st.session_state.rdf_graph is None:
        st.info("Load a graph first.")
    else:
        st.markdown("#### SPARQL Query Interface")
        col_q1, col_q2 = st.columns([3, 1])
        with col_q2:
            st.markdown("**Example Queries**")
            for eq in EXAMPLE_QUERIES:
                if st.button(eq["name"], key=f"eq_{eq['name']}", use_container_width=True):
                    st.session_state["sparql_query"] = eq["query"]
                    st.rerun()

        with col_q1:
            query_text = st.text_area(
                "SPARQL Query",
                value=st.session_state.get("sparql_query", EXAMPLE_QUERIES[0]["query"]),
                height=180,
                key="sparql_input",
            )
            if st.button("▶ Execute Query", type="primary", key="run_sparql"):
                with st.spinner("Running query..."):
                    result = run_sparql(st.session_state.rdf_graph, query_text)

                if result["error"]:
                    st.error(result["error"])
                elif result["type"] == "SELECT":
                    st.success(f"Returned {len(result['rows'])} row(s)")
                    if result["rows"]:
                        import pandas as pd
                        df = pd.DataFrame(result["rows"], columns=result["columns"])
                        st.dataframe(df, use_container_width=True, height=300)
                elif result["type"] == "ASK":
                    st.info(f"Result: **{result['result']}**")
                elif result["type"] == "CONSTRUCT":
                    st.success(f"Constructed {len(result['triples'])} triple(s)")
                    for t in result["triples"][:50]:
                        st.text(f"{t['subject']}  →  {t['predicate']}  →  {t['object']}")

# ---- Node Inspector tab ----
with tab_details:
    if st.session_state.rdf_graph is None:
        st.info("Load a graph first.")
    else:
        # Node selector
        all_nodes = [n["data"]["id"] for n in st.session_state.elements["nodes"]
                     if n["data"].get("node_type") != "literal"]
        node_labels = {n["data"]["id"]: n["data"]["label"] for n in st.session_state.elements["nodes"]}

        selected = st.selectbox(
            "Select a node to inspect",
            all_nodes,
            format_func=lambda x: f"{node_labels.get(x, x)} ({x.split('#')[-1] if '#' in x else x.split('/')[-1]})",
            key="inspect_node",
        )

        if selected:
            details = get_node_details(st.session_state.rdf_graph, selected)

            type_color = {
                "class": "#6366f1", "instance": "#06b6d4",
                "literal": "#f59e0b", "property": "#10b981",
                "blank": "#94a3b8", "resource": "#64748b",
            }.get(details["type"], "#64748b")

            st.markdown(f"""
            <div class="node-card">
                <h4>{details['label']}</h4>
                <div class="node-type-badge" style="background:{type_color}">{details['type']}</div>
                <div class="node-uri">{details['uri']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Types
            if details["types"]:
                st.markdown("**Types:**")
                for t in details["types"]:
                    short = t.split("#")[-1] if "#" in t else t.split("/")[-1]
                    st.markdown(f"- `{short}` — <span style='color:#64748b;font-size:11px;'>{t}</span>",
                                unsafe_allow_html=True)

            # Properties
            if details["properties"]:
                st.markdown("**Properties:**")
                for pred, vals in details["properties"].items():
                    for v in vals:
                        if v["type"] == "uri":
                            st.markdown(f"- **{pred}** → [{v['label']}]({v['value']})" if v['value'].startswith('http') else f"- **{pred}** → {v['label']}")
                        else:
                            st.markdown(f"- **{pred}** = `{v['value']}`")

            # Incoming
            if details["incoming"]:
                st.markdown("**Incoming relationships:**")
                for inc in details["incoming"][:30]:
                    st.markdown(f"- ← **{inc['predicate_label']}** from *{inc['subject_label']}*")

# ---- Statistics tab ----
with tab_stats:
    if st.session_state.stats is None:
        st.info("Load a graph first.")
    else:
        s = st.session_state.stats

        st.markdown("#### 📊 Graph Statistics")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
            <div class="node-card">
                <h4>Triple Composition</h4>
            </div>
            """, unsafe_allow_html=True)
            metrics = {
                "Total Triples": s["total_triples"],
                "Total Nodes": s["total_nodes"],
                "URI Nodes": s["total_uris"],
                "Literal Nodes": s["total_literals"],
                "Blank Nodes": s["total_bnodes"],
                "Unique Subjects": s["total_subjects"],
                "Unique Predicates": s["total_predicates"],
                "Unique Objects": s["total_objects"],
            }
            for k, v in metrics.items():
                st.markdown(f"**{k}:** {v:,}")

        with col_b:
            st.markdown("""
            <div class="node-card">
                <h4>Ontology Statistics</h4>
            </div>
            """, unsafe_allow_html=True)
            onto_metrics = {
                "Classes": s["classes_count"],
                "Instances": s["instances_count"],
                "Object Properties": s["object_properties_count"],
                "Datatype Properties": s["datatype_properties_count"],
                "Namespaces": s["namespaces_count"],
            }
            for k, v in onto_metrics.items():
                st.markdown(f"**{k}:** {v:,}")

        # Namespace table
        st.markdown("#### 🌐 Namespaces")
        if s["namespaces"]:
            import pandas as pd
            ns_df = pd.DataFrame(
                [(prefix, uri) for prefix, uri in s["namespaces"].items()],
                columns=["Prefix", "URI"],
            )
            st.dataframe(ns_df, use_container_width=True, hide_index=True)
