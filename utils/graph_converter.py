"""Convert rdflib Graph triples into Cytoscape.js-compatible node/edge structures."""

from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL
from utils.rdf_parser import _get_label, get_node_type


# Color palettes
CLASS_COLORS = [
    "#6366f1", "#8b5cf6", "#a78bfa", "#7c3aed", "#5b21b6",
    "#4f46e5", "#4338ca", "#3730a3", "#312e81", "#818cf8",
]
INSTANCE_COLORS = [
    "#06b6d4", "#0891b2", "#0e7490", "#22d3ee", "#67e8f9",
    "#14b8a6", "#0d9488", "#0f766e", "#2dd4bf", "#5eead4",
]
LITERAL_COLOR = "#f59e0b"
BLANK_COLOR = "#94a3b8"
PROPERTY_COLOR = "#10b981"

SUBCLASS_EDGE_COLOR = "#8b5cf6"
OBJECT_PROP_EDGE_COLOR = "#06b6d4"
DATATYPE_PROP_EDGE_COLOR = "#f59e0b"
DEFAULT_EDGE_COLOR = "#64748b"


def _get_namespace(uri: str) -> str:
    if "#" in uri:
        return uri.rsplit("#", 1)[0] + "#"
    return uri.rsplit("/", 1)[0] + "/"


def _node_id(node) -> str:
    return str(node)


def convert_graph(g: Graph, max_nodes: int = 2000) -> dict:
    """Convert an rdflib Graph to Cytoscape.js elements.

    Returns dict with 'nodes' and 'edges' lists in Cytoscape.js format.
    """
    nodes_dict = {}
    edges_list = []

    # Track class assignments for coloring
    class_color_map = {}
    class_idx = 0

    def _get_class_color(cls_uri: str) -> str:
        nonlocal class_idx
        if cls_uri not in class_color_map:
            class_color_map[cls_uri] = CLASS_COLORS[class_idx % len(CLASS_COLORS)]
            class_idx += 1
        return class_color_map[cls_uri]

    def _add_node(node, force_type=None):
        nid = _node_id(node)
        if nid in nodes_dict:
            return nid

        if isinstance(node, Literal):
            val = str(node)
            display = val[:60] + "..." if len(val) > 60 else val
            nodes_dict[nid] = {
                "data": {
                    "id": nid,
                    "label": display,
                    "node_type": "literal",
                    "color": LITERAL_COLOR,
                    "shape": "rectangle",
                    "namespace": "",
                    "classes": [],
                    "size": 20,
                }
            }
            return nid

        if isinstance(node, BNode):
            nodes_dict[nid] = {
                "data": {
                    "id": nid,
                    "label": f"_:{node}",
                    "node_type": "blank",
                    "color": BLANK_COLOR,
                    "shape": "diamond",
                    "namespace": "",
                    "classes": [],
                    "size": 20,
                }
            }
            return nid

        ntype = force_type or get_node_type(g, node)
        label = _get_label(g, node)
        ns = _get_namespace(str(node))

        # Get classes for instances
        type_uris = [str(t) for t in g.objects(node, RDF.type)]

        if ntype == "class":
            color = _get_class_color(str(node))
            shape = "roundrectangle"
            size = 40
        elif ntype == "instance":
            # Color by first class
            if type_uris:
                color = INSTANCE_COLORS[hash(type_uris[0]) % len(INSTANCE_COLORS)]
            else:
                color = INSTANCE_COLORS[0]
            shape = "ellipse"
            size = 30
        elif ntype == "property":
            color = PROPERTY_COLOR
            shape = "triangle"
            size = 25
        else:
            color = "#64748b"
            shape = "ellipse"
            size = 25

        nodes_dict[nid] = {
            "data": {
                "id": nid,
                "label": label,
                "node_type": ntype,
                "color": color,
                "shape": shape,
                "namespace": ns,
                "classes": type_uris,
                "size": size,
            }
        }
        return nid

    # Process all triples
    triple_count = 0
    for s, p, o in g:
        triple_count += 1
        if len(nodes_dict) >= max_nodes:
            break

        src_id = _add_node(s)
        tgt_id = _add_node(o)

        # Edge type & color
        pred_uri = str(p)
        pred_label = _get_label(g, p)

        if p == RDFS.subClassOf:
            edge_type = "subclass"
            edge_color = SUBCLASS_EDGE_COLOR
            line_style = "solid"
        elif p == RDF.type:
            edge_type = "type"
            edge_color = "#ec4899"
            line_style = "dashed"
        elif isinstance(o, Literal):
            edge_type = "datatype_property"
            edge_color = DATATYPE_PROP_EDGE_COLOR
            line_style = "dotted"
        elif p in (OWL.imports, OWL.versionIRI):
            edge_type = "owl_meta"
            edge_color = "#94a3b8"
            line_style = "dashed"
        else:
            edge_type = "object_property"
            edge_color = OBJECT_PROP_EDGE_COLOR
            line_style = "solid"

        edges_list.append({
            "data": {
                "id": f"{src_id}-{pred_uri}-{tgt_id}",
                "source": src_id,
                "target": tgt_id,
                "label": pred_label,
                "predicate": pred_uri,
                "edge_type": edge_type,
                "color": edge_color,
                "line_style": line_style,
            }
        })

    return {
        "nodes": list(nodes_dict.values()),
        "edges": edges_list,
        "stats": {
            "total_triples": len(g),
            "displayed_triples": triple_count,
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges_list),
            "truncated": len(nodes_dict) >= max_nodes,
        }
    }


def get_neighbors(g: Graph, node_uri: str, depth: int = 1) -> dict:
    """Get neighboring nodes up to a certain depth for expand/collapse."""
    node = URIRef(node_uri)
    visited = set()
    nodes_dict = {}
    edges_list = []
    frontier = {node}

    for _ in range(depth):
        next_frontier = set()
        for n in frontier:
            if n in visited:
                continue
            visited.add(n)
            # Outgoing
            for p, o in g.predicate_objects(n):
                nid_s = _node_id(n)
                nid_o = _node_id(o)
                edges_list.append({
                    "data": {
                        "id": f"{nid_s}-{str(p)}-{nid_o}",
                        "source": nid_s,
                        "target": nid_o,
                        "label": _get_label(g, p),
                        "predicate": str(p),
                    }
                })
                if isinstance(o, (URIRef, BNode)) and o not in visited:
                    next_frontier.add(o)
            # Incoming
            for s, p in g.subject_predicates(n):
                nid_s = _node_id(s)
                nid_n = _node_id(n)
                edges_list.append({
                    "data": {
                        "id": f"{nid_s}-{str(p)}-{nid_n}",
                        "source": nid_s,
                        "target": nid_n,
                        "label": _get_label(g, p),
                        "predicate": str(p),
                    }
                })
                if isinstance(s, (URIRef, BNode)) and s not in visited:
                    next_frontier.add(s)
        frontier = next_frontier

    return {"nodes": list(nodes_dict.values()), "edges": edges_list}


def filter_elements(elements: dict, class_filter: list = None,
                    predicate_filter: list = None,
                    namespace_filter: list = None) -> dict:
    """Filter graph elements by class, predicate, or namespace."""
    nodes = elements["nodes"]
    edges = elements["edges"]

    if class_filter:
        class_set = set(class_filter)
        nodes = [n for n in nodes if (
            n["data"].get("node_type") in ("literal", "blank") or
            any(c in class_set for c in n["data"].get("classes", [])) or
            n["data"]["id"] in class_set
        )]

    if namespace_filter:
        ns_set = set(namespace_filter)
        node_ids_before = {n["data"]["id"] for n in nodes}
        nodes = [n for n in nodes if (
            n["data"].get("namespace", "") in ns_set or
            n["data"].get("node_type") == "literal"
        )]

    if predicate_filter:
        pred_set = set(predicate_filter)
        edges = [e for e in edges if e["data"].get("predicate") in pred_set]

    # Keep only edges whose source and target are still in nodes
    node_ids = {n["data"]["id"] for n in nodes}
    edges = [e for e in edges if e["data"]["source"] in node_ids and e["data"]["target"] in node_ids]

    return {"nodes": nodes, "edges": edges}
