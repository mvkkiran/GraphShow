"""SPARQL query engine for the uploaded graph."""

from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery
import traceback


def run_sparql(g: Graph, query_str: str) -> dict:
    """Execute a SPARQL query against the graph.

    Returns dict with 'columns', 'rows', 'type' (SELECT/CONSTRUCT/ASK), and 'error'.
    """
    try:
        query_str = query_str.strip()
        result = g.query(query_str)

        if result.type == "SELECT":
            columns = [str(v) for v in result.vars]
            rows = []
            for row in result:
                rows.append([str(cell) if cell is not None else "" for cell in row])
            return {"type": "SELECT", "columns": columns, "rows": rows, "error": None}

        elif result.type == "CONSTRUCT":
            triples = []
            for s, p, o in result:
                triples.append({"subject": str(s), "predicate": str(p), "object": str(o)})
            return {"type": "CONSTRUCT", "triples": triples, "error": None}

        elif result.type == "ASK":
            return {"type": "ASK", "result": bool(result), "error": None}

        else:
            return {"type": str(result.type), "error": "Unsupported query type"}

    except Exception as e:
        return {"type": "ERROR", "error": f"{type(e).__name__}: {str(e)}"}


EXAMPLE_QUERIES = [
    {
        "name": "All Classes",
        "query": """SELECT DISTINCT ?class ?label WHERE {
    { ?class a owl:Class . }
    UNION
    { ?class a rdfs:Class . }
    OPTIONAL { ?class rdfs:label ?label . }
}
ORDER BY ?class"""
    },
    {
        "name": "All Properties",
        "query": """SELECT DISTINCT ?prop ?label ?domain ?range WHERE {
    { ?prop a owl:ObjectProperty . }
    UNION
    { ?prop a owl:DatatypeProperty . }
    UNION
    { ?prop a rdf:Property . }
    OPTIONAL { ?prop rdfs:label ?label . }
    OPTIONAL { ?prop rdfs:domain ?domain . }
    OPTIONAL { ?prop rdfs:range ?range . }
}
ORDER BY ?prop"""
    },
    {
        "name": "Class Hierarchy",
        "query": """SELECT ?child ?parent WHERE {
    ?child rdfs:subClassOf ?parent .
    FILTER(isURI(?child) && isURI(?parent))
}
ORDER BY ?parent ?child"""
    },
    {
        "name": "Instance Count by Class",
        "query": """SELECT ?class (COUNT(?instance) AS ?count) WHERE {
    ?instance a ?class .
    FILTER(isURI(?class))
}
GROUP BY ?class
ORDER BY DESC(?count)"""
    },
    {
        "name": "All Triples (limit 100)",
        "query": """SELECT ?subject ?predicate ?object WHERE {
    ?subject ?predicate ?object .
}
LIMIT 100"""
    },
]
