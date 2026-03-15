"""Graph statistics computation."""

from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL
from utils.rdf_parser import extract_namespaces


def compute_stats(g: Graph) -> dict:
    """Compute comprehensive statistics for the graph."""
    total_triples = len(g)

    subjects = set()
    predicates = set()
    objects_set = set()
    classes = set()
    instances = set()
    literals = set()
    bnodes = set()

    for s, p, o in g:
        subjects.add(s)
        predicates.add(p)
        objects_set.add(o)

        if isinstance(o, Literal):
            literals.add(o)
        if isinstance(s, BNode):
            bnodes.add(s)
        if isinstance(o, BNode):
            bnodes.add(o)

    all_nodes = subjects | objects_set

    # Classes
    for s in g.subjects(RDF.type, OWL.Class):
        if isinstance(s, URIRef):
            classes.add(s)
    for s in g.subjects(RDF.type, RDFS.Class):
        if isinstance(s, URIRef):
            classes.add(s)

    # Instances
    for s, _, o in g.triples((None, RDF.type, None)):
        if isinstance(o, URIRef) and o not in (OWL.Class, RDFS.Class, OWL.ObjectProperty,
                                                 OWL.DatatypeProperty, OWL.AnnotationProperty,
                                                 OWL.Ontology, OWL.Restriction):
            if isinstance(s, URIRef):
                instances.add(s)

    # Object properties
    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    data_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))

    namespaces = extract_namespaces(g)

    return {
        "total_triples": total_triples,
        "total_nodes": len(all_nodes),
        "total_uris": len([n for n in all_nodes if isinstance(n, URIRef)]),
        "total_literals": len(literals),
        "total_bnodes": len(bnodes),
        "total_subjects": len(subjects),
        "total_predicates": len(predicates),
        "total_objects": len(objects_set),
        "classes_count": len(classes),
        "instances_count": len(instances),
        "object_properties_count": len(obj_props),
        "datatype_properties_count": len(data_props),
        "namespaces_count": len(namespaces),
        "namespaces": namespaces,
    }
