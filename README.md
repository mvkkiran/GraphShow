# GraphShow — Knowledge Graph Visualization Dashboard

A professional Knowledge Graph Explorer for RDF/OWL data, powered by **Streamlit** + **Cytoscape.js**. Designed to run inside **Databricks Apps**.

---

## Features

- **Multi-format RDF parsing**: RDF/XML, Turtle, N3, OWL, JSON-LD, N-Triples, TriG
- **Interactive graph visualization** with Cytoscape.js (zoom, pan, drag, click-to-expand)
- **Class hierarchy explorer** (sidebar ontology tree)
- **Node inspector** with full property/relationship details
- **SPARQL query interface** with example queries and tabular results
- **Graph statistics dashboard** (triples, nodes, classes, namespaces)
- **Search** nodes by URI, label, or type
- **Style editor** — customize node/edge colors and sizes
- **Multiple layouts**: force-directed, hierarchical, circular, grid
- **Export**: PNG, SVG, JSON
- **Dark/light theme toggle**
- **Performance controls**: adjustable node rendering limit

---

## Project Structure

```
GraphShow/
├── app.py                          # Main Streamlit application
├── app.yaml                        # Databricks Apps deployment config
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit theme config
├── utils/
│   ├── __init__.py
│   ├── rdf_parser.py               # RDF parsing (rdflib)
│   ├── graph_converter.py          # Triple → Cytoscape.js elements
│   ├── sparql_engine.py            # SPARQL query execution
│   └── stats.py                    # Graph statistics
├── components/
│   ├── __init__.py
│   └── cytoscape_component.py      # Cytoscape.js Streamlit wrapper
├── static/
│   └── cytoscape_template.html     # Cytoscape.js interactive template
└── examples/
    └── example_ontology.ttl        # Pharma knowledge graph example
```

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deploying to Databricks Apps

### Option 1: Databricks CLI

```bash
# From the GraphShow directory
databricks apps create graphshow --source-code-path /Workspace/Users/<your-email>/GraphShow

# Or deploy an update
databricks apps deploy graphshow --source-code-path /Workspace/Users/<your-email>/GraphShow
```

### Option 2: Manual Upload

1. Upload the entire `GraphShow/` folder to your Databricks Workspace (e.g., via Repos or Files).
2. Go to **Compute → Apps → Create App**.
3. Set the **source path** to the uploaded folder.
4. The `app.yaml` file defines the start command automatically.
5. Click **Deploy**.

### Option 3: Databricks Git Integration

1. Push this repo to a Git provider (GitHub, Azure DevOps, etc.).
2. In Databricks, go to **Repos → Add Repo** and connect.
3. Create a Databricks App pointing to the repo folder.

---

## Usage

1. Open the Databricks App URL (or `localhost:8501` locally).
2. **Upload** an RDF/OWL/TTL/JSON-LD file via the sidebar, or click **Example** to load the bundled pharma ontology.
3. The graph renders interactively in the main canvas.
4. Use the **sidebar** to explore the class hierarchy, filter by namespace/predicate, and customize styles.
5. Switch to the **SPARQL Query** tab to run queries against the loaded graph.
6. Use the **Node Inspector** tab for detailed property inspection.
7. Use the **Statistics** tab for graph metrics.
8. **Export** the graph as PNG, SVG, or JSON from the graph toolbar.

---

## Example Dataset

The included `examples/example_ontology.ttl` models a **pharmaceutical knowledge graph** with:

- Drugs (Nivolumab, Dabrafenib, Adalimumab, Erlotinib, Ruxolitinib)
- Diseases (Melanoma, Lung Cancer, Rheumatoid Arthritis, etc.)
- Proteins & Genes (BRAF, EGFR, PD-1, TNF-alpha, JAK2)
- Clinical Trials with phases, sponsors, investigators, and sites
- Mechanisms of Action, Adverse Events, Biomarkers, Pathways
- Organizations (pharma companies, hospitals, research institutions)
- Publications

---

## Technology Stack

| Layer               | Technology         |
|--------------------|--------------------|
| UI Framework       | Streamlit          |
| Graph Visualization| Cytoscape.js       |
| RDF Parsing        | rdflib             |
| Query Engine       | rdflib SPARQL      |
| Deployment         | Databricks Apps    |
