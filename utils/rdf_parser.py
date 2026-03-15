"""RDF parsing module supporting multiple semantic graph formats."""

import io
from typing import Optional
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DCTERMS, FOAF


FORMAT_MAP = {
    ".rdf": "xml",
    ".xml": "xml",
    ".owl": "xml",
    ".ttl": "turtle",
    ".n3": "n3",
    ".nt": "nt",
    ".nq": "nquads",
    ".jsonld": "json-ld",
    ".json": "json-ld",
    ".trig": "trig",
}

COMMON_NAMESPACES = {
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    "xsd": XSD,
    "skos": SKOS,
    "dcterms": DCTERMS,
    "foaf": FOAF,
}


def detect_format(filename: str) -> str:
    """Detect RDF format from file extension."""
    filename_lower = filename.lower()
    for ext, fmt in FORMAT_MAP.items():
        if filename_lower.endswith(ext):
            return fmt
    return "turtle"


def parse_rdf(data: bytes, filename: str, format_override: Optional[str] = None) -> Graph:
    """Parse RDF data from bytes into an rdflib Graph.

    Args:
        data: Raw file bytes.
        filename: Original filename (used to detect format).
        format_override: Explicitly set the RDF format.

    Returns:
        Parsed rdflib Graph.
    """
    g = Graph()
    fmt = format_override or detect_format(filename)
    g.parse(io.BytesIO(data), format=fmt)
    return g


def extract_namespaces(g: Graph) -> dict[str, str]:
    """Extract all namespace prefixes from the graph."""
    ns = {}
    for prefix, uri in g.namespaces():
        ns[str(prefix)] = str(uri)
    return ns


def extract_classes(g: Graph) -> list[dict]:
    """Extract OWL/RDFS classes and build hierarchy."""
    classes = set()
    # OWL classes
    for s in g.subjects(RDF.type, OWL.Class):
        if isinstance(s, URIRef):
            classes.add(s)
    # RDFS classes
    for s in g.subjects(RDF.type, RDFS.Class):
        if isinstance(s, URIRef):
            classes.add(s)
    # Classes mentioned as range/domain
    for s in g.objects(predicate=RDFS.range):
        if isinstance(s, URIRef):
            classes.add(s)
    for s in g.objects(predicate=RDFS.domain):
        if isinstance(s, URIRef):
            classes.add(s)

    hierarchy = []
    for cls in classes:
        label = _get_label(g, cls)
        parents = list(g.objects(cls, RDFS.subClassOf))
        parent_uris = [str(p) for p in parents if isinstance(p, URIRef)]
        hierarchy.append({
            "uri": str(cls),
            "label": label,
            "parents": parent_uris,
        })
    return hierarchy


def extract_properties(g: Graph) -> list[dict]:
    """Extract all properties from the graph."""
    props = set()
    for p in g.predicates():
        if isinstance(p, URIRef):
            props.add(p)
    result = []
    for p in props:
        label = _get_label(g, p)
        result.append({"uri": str(p), "label": label})
    return result


def _get_label(g: Graph, node) -> str:
    """Get a human-readable label for a node."""
    for label in g.objects(node, RDFS.label):
        return str(label)
    for label in g.objects(node, SKOS.prefLabel):
        return str(label)
    if isinstance(node, URIRef):
        uri = str(node)
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.rsplit("/", 1)[-1]
    return str(node)


def get_node_type(g: Graph, node) -> str:
    """Determine the type of a node: class, instance, literal, or blank."""
    if isinstance(node, Literal):
        return "literal"
    if isinstance(node, BNode):
        return "blank"
    types = list(g.objects(node, RDF.type))
    for t in types:
        if t in (OWL.Class, RDFS.Class):
            return "class"
        if t in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, RDF.Property):
            return "property"
    if types:
        return "instance"
    # Check if used as class
    if (None, RDF.type, node) in g:
        return "class"
    return "resource"


def get_node_details(g: Graph, node_uri: str) -> dict:
    """Get detailed info for a specific node."""
    node = URIRef(node_uri)
    label = _get_label(g, node)
    node_type = get_node_type(g, node)

    types = [str(t) for t in g.objects(node, RDF.type)]
    namespace = str(node).rsplit("#", 1)[0] + "#" if "#" in str(node) else str(node).rsplit("/", 1)[0] + "/"

    properties = {}
    for p, o in g.predicate_objects(node):
        pred_label = _get_label(g, p)
        if pred_label not in properties:
            properties[pred_label] = []
        if isinstance(o, Literal):
            properties[pred_label].append({"value": str(o), "type": "literal", "datatype": str(o.datatype) if o.datatype else None})
        elif isinstance(o, URIRef):
            properties[pred_label].append({"value": str(o), "type": "uri", "label": _get_label(g, o)})
        else:
            properties[pred_label].append({"value": str(o), "type": "blank"})

    incoming = []
    for s, p in g.subject_predicates(node):
        incoming.append({
            "subject": str(s),
            "subject_label": _get_label(g, s),
            "predicate": str(p),
            "predicate_label": _get_label(g, p),
        })

    return {
        "uri": node_uri,
        "label": label,
        "type": node_type,
        "types": types,
        "namespace": namespace,
        "properties": properties,
        "incoming": incoming,
    }
