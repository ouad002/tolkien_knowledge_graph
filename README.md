# Tolkien Gateway Knowledge Graph


## 📋 Overview

This project extracts structured information about J.R.R. Tolkien's literary universe from Tolkien Gateway's MediaWiki API, converts it into RDF triples, enriches it through semantic reasoning, and serves it as Linked Data with content negotiation support.

### Key Features

- **Data Extraction**: Fetches 60+ entities (characters, locations, events) from Tolkien Gateway
- **RDF Transformation**: Converts MediaWiki infobox templates to RDF using Schema.org and custom ontology
- **Semantic Reasoning**: Infers new relationships using RDFS/OWL reasoning rules
- **SHACL Validation**: Validates data quality against predefined constraints
- **Triple Store**: Stores and queries data using Apache Fuseki
- **Linked Data Interface**: Flask web application with content negotiation (HTML/Turtle)

## 🏗️ Architecture

```
Tolkien Gateway API
    ↓
01_fetch_pages.py → tolkien_pages.json
    ↓
02_parse_templates.py → parsed_templates.json
    ↓
03_build_rdf.py → tolkien_kg.ttl
    ↓
04_validate_shacl.py → validation reports
    ↓
06_apply_reasoning.py → tolkien_kg_reasoned.ttl
    ↓
05_load_fuseki.py → Apache Fuseki
    ↓
app.py (Flask) → Web Interface
```

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Apache Jena Fuseki (for triplestore)
- pip (Python package manager)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd tolkien-kg
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Download and run Apache Fuseki**
```bash
# Download from https://jena.apache.org/download/
# Extract and run:
./fuseki-server
```

The server will start on `http://localhost:3030`

## 📦 Dependencies

```
Core RDF and Semantic Web:
- rdflib (7.0.0) - RDF graph manipulation
- SPARQLWrapper (2.0.0) - SPARQL queries
- owlrl (6.0.2) - OWL reasoning
- pyshacl (0.25.0) - SHACL validation

MediaWiki:
- mwclient (0.10.1) - MediaWiki API client
- mwparserfromhell (0.6.6) - Wikitext parser

Web Framework:
- Flask (3.0.0) - Web application
- Flask-CORS (4.0.0) - Cross-origin support

Utilities:
- pandas (2.1.4) - Data processing
- requests (2.31.0) - HTTP requests
- tqdm (4.66.1) - Progress bars
```

## 🎯 Usage

### Step 1: Fetch Pages from Tolkien Gateway

```bash
python 01_fetch_pages.py
```

Fetches wikitext for 60+ entities including:
- Characters: Gandalf, Frodo, Aragorn, Legolas, etc.
- Locations: Rivendell, Minas Tirith, Mordor, etc.
- Regions: Gondor, Rohan, The Shire, etc.

**Output**: `data/tolkien_pages.json`

### Step 2: Parse Wikitext Templates

```bash
python 02_parse_templates.py
```

Extracts structured data from MediaWiki templates (infoboxes).

**Output**: `data/parsed_templates.json`

### Step 3: Build RDF Knowledge Graph

```bash
python 03_build_rdf.py
```

Converts parsed templates to RDF using:
- **Schema.org** for common types (Person, Place, Event)
- **Custom ontology** for Tolkien-specific concepts (Race, House, Artifact)

**Output**: `output/tolkien_kg.ttl`

### Step 4: Validate with SHACL (Optional)

```bash
python 04_validate_shacl.py
```

Validates RDF data against SHACL shapes for data quality.

**Output**: `output/shacl_validation_report.json`

### Step 5: Load into Fuseki

```bash
python 05_load_fuseki.py
```

Creates dataset and uploads RDF to Apache Fuseki triplestore.

### Step 6: Apply Reasoning

```bash
python 06_apply_reasoning.py
```

Enriches the knowledge graph with inferred relationships:
- Family relationships (siblings, parent-child)
- Inverse properties (memberOf ↔ hasMember)
- Fellowship membership
- Race-based groupings

**Output**: `output/tolkien_kg_reasoned.ttl`

### Step 7: Launch Web Interface

```bash
python app.py
```

Visit `http://localhost:5000` to explore the knowledge graph.

## 🌐 Web Interface

The Flask application provides:

- **Home Page**: Browse all entities
- **Search**: Find entities by name
- **Entity Pages**: Detailed information with linked relationships
- **Content Negotiation**: 
  - HTML for browsers
  - Turtle (text/turtle) for RDF clients

### Example URLs

```
http://localhost:5000/
http://localhost:5000/search?q=Gandalf
http://localhost:5000/resource/Frodo_Baggins
```

## 📊 Ontology

### Classes

| Class | Description | Schema |
|-------|-------------|--------|
| Person | Characters | schema:Person |
| Place | Locations | schema:Place |
| Event | Historical events | schema:Event |
| Organization | Groups, fellowships | schema:Organization |
| Race | Peoples (Elves, Hobbits, etc.) | tgo:Race |
| House | Noble houses | tgo:House |
| Artifact | Weapons, items | tgo:Artifact |
| Creature | Mounts, animals | tgo:Creature |

### Key Properties

**Relationships**:
- `schema:spouse`, `tgo:siblings`, `tgo:parentage`
- `schema:memberOf` ↔ `tgo:hasMember`
- `tgo:belongsToRace` ↔ `tgo:raceIncludes`
- `tgo:wields` ↔ `tgo:wieldedBy`

**Attributes**:
- `schema:name`, `schema:birthDate`, `schema:deathDate`
- `tgo:race`, `tgo:realm`, `tgo:house`

## 🔍 Example SPARQL Queries

### Find all members of the Fellowship

```sparql
PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
PREFIX schema: <http://schema.org/>

SELECT ?name WHERE {
  ?member tgo:memberOf <http://tolkiengateway.net/kg/resource/Fellowship_of_the_Ring> ;
          schema:name ?name .
}
```

### Find all Hobbits

```sparql
PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name WHERE {
  ?person tgo:belongsToRace <http://tolkiengateway.net/kg/resource/Hobbits> ;
          rdfs:label ?name .
}
```

### Find all wielders of artifacts

```sparql
PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>

SELECT ?person ?artifact WHERE {
  ?artifact tgo:wieldedBy ?person .
}
```

## 📁 Project Structure

```
tolkien-kg/
├── 01_fetch_pages.py       # MediaWiki data extraction
├── 02_parse_templates.py   # Wikitext template parser
├── 03_build_rdf.py          # RDF graph builder
├── 04_validate_shacl.py     # SHACL validator
├── 05_load_fuseki.py        # Fuseki loader
├── 06_apply_reasoning.py    # Semantic reasoning engine
├── app.py                   # Flask web application
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── data/
│   ├── tolkien_pages.json
│   └── parsed_templates.json
├── output/
│   ├── tolkien_kg.ttl
│   ├── tolkien_kg_reasoned.ttl
│   └── shacl_validation_report.json
├── shapes/
│   └── tolkien_shapes.ttl
└── templates/
    ├── base.html
    ├── index.html
    ├── search.html
    └── entity.html
```

## 🧪 Reasoning Rules

The reasoning engine applies:

1. **RDFS Entailment**: Subclass and subproperty inference
2. **Family Relationships**: Sibling inference from shared parents
3. **Inverse Properties**: Bidirectional relationships (e.g., memberOf ↔ hasMember)
4. **Fellowship Membership**: Automatic tagging of the nine companions
5. **Location Associations**: Birth/death location connections
6. **Symmetric Properties**: Spouse and sibling symmetry

## 📈 Statistics

After reasoning, the knowledge graph contains approximately:
- **1,500+** RDF triples
- **60+** entities
- **200+** relationships
- **15+** property types

## 🎓 Academic Context

This project was developed for **Mines Saint-Étienne** as a semantic web technologies demonstration, showcasing:
- RDF/RDFS/OWL standards
- Linked Data principles
- SPARQL queries
- Semantic reasoning
- Data integration from external sources

## 📝 Configuration

Edit `config.py` to customize:

```python
# MediaWiki API
WIKI_DOMAIN = "tolkiengateway.net"

# Namespaces
NAMESPACE_BASE = "http://tolkiengateway.net/kg/"

# Apache Fuseki
FUSEKI_HOST = "http://localhost:3030"
FUSEKI_DATASET = "tolkien"

# Flask Server
FLASK_PORT = 5000
```

## 🛠️ Troubleshooting

### Fuseki Connection Error
```bash
# Ensure Fuseki is running
./fuseki-server

# Check http://localhost:3030
```

### SHACL Validation Fails
This is informational - the knowledge graph will still work. Review `output/shacl_validation_details.txt` for specific issues.

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 🔗 Resources

- [Tolkien Gateway](https://tolkiengateway.net) - Data source
- [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/) - Triple store
- [RDFLib Documentation](https://rdflib.readthedocs.io/) - RDF library
- [Schema.org](https://schema.org/) - Vocabulary

