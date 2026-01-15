# Tolkien Knowledge Graph

A semantic web application that automatically builds a comprehensive knowledge graph from Tolkien Gateway wiki pages, featuring advanced reasoning algorithms and a web interface for exploring J.R.R. Tolkien's Middle-earth universe.

## Overview

This project extracts structured data from [Tolkien Gateway](https://tolkiengateway.net), constructs an RDF knowledge graph using semantic web standards (RDF, RDFS, OWL), applies sophisticated reasoning algorithms to infer new relationships, validates the data using SHACL constraints, and serves it through a Flask web interface with SPARQL query capabilities.

### Key Features

- **Automated data extraction** from MediaWiki API
- **Template parsing** to extract structured information
- **RDF knowledge graph construction** using Schema.org and custom ontologies
- **Advanced reasoning engine** with multiple inference algorithms
- **SHACL validation** for data quality assurance
- **Apache Fuseki integration** for RDF storage and SPARQL querying
- **Web interface** with content negotiation (HTML/Turtle)
- **Interactive exploration** of characters, locations, events, and relationships

## Architecture

The project follows a pipeline architecture with six main stages:

```
1. Fetch Pages      →  2. Parse Templates  →  3. Build RDF
       ↓                      ↓                     ↓
   JSON data          Structured data         Base graph
       
4. Validate SHACL   →  5. Load Fuseki     →  6. Apply Reasoning
       ↓                      ↓                     ↓
   Quality check        Triple store         Enhanced graph
```

### Technology Stack

- **RDF/Semantic Web**: RDFLib, SPARQL, OWL-RL, PySHACL
- **MediaWiki**: mwclient, mwparserfromhell
- **Web Framework**: Flask, Flask-CORS
- **Triple Store**: Apache Fuseki
- **Data Processing**: pandas, requests
- **Standards**: Schema.org, RDFS, OWL, SHACL

## Enhanced Reasoning Algorithms

The reasoning engine (`06_apply_reasoning.py`) implements multiple sophisticated inference algorithms to enrich the knowledge graph:

### 1. Ontology Definition
- **Class Hierarchies**: Defines taxonomies for races (Elves → Noldor, Sindar), peoples (FreePeoples, EvilCreatures), and divine beings (Ainur → Maiar → Wizards)
- **Property Hierarchies**: Establishes relationships between properties (e.g., `tgo:parentage` → `schema:parent`)
- **Symmetric Properties**: Declares bidirectional relationships (`schema:spouse`, `tgo:siblings`)
- **Inverse Properties**: Defines 9 inverse relationship types for bidirectional navigation

### 2. Family Relationship Inference
- **Sibling Discovery**: Infers sibling relationships from shared parentage
- **Inverse Parentage**: Generates child → parent relationships from parent → child
- **Spouse Symmetry**: Ensures bidirectional marriage relationships

### 3. Fellowship Membership
- Automatically tags the nine members of the Fellowship of the Ring
- Creates organizational structure linking characters to groups

### 4. Inverse Relationship Inference ⭐ *Enhanced Feature*
This powerful algorithm creates navigable inverse relationships, enabling queries from both directions:

- **Organization Membership**: `X memberOf Y` → `Y hasMember X`
- **Race Inclusion**: `X belongsToRace R` → `R raceIncludes X`
- **House Affiliation**: `X belongsToHouse H` → `H houseIncludes X`
- **Artifact Wielding**: `X wields A` → `A wieldedBy X`
- **Event Participation**: `X participatedIn E` → `E hasParticipant X`
- **Mount Riding**: `X rides C` → `C riddenBy X`
- **Language Speaking**: `X speaks L` → `L spokenBy X`

**Example Impact**: When Aragorn wields Andúril, the reasoner automatically infers that Andúril is wielded by Aragorn, allowing queries like "Show all artifacts and their wielders" to work seamlessly.

### 5. Race-Based Group Membership
- Maps specific races to broader cultural groups
- Example: Gondorians → Númenórean descendants

### 6. RDFS Entailment
- **Transitive Subclass Inference**: If `Noldor subClassOf Elves` and `Galadriel type Noldor`, infers `Galadriel type Elves`
- **Subproperty Propagation**: Propagates values through property hierarchies
- **Iterative Convergence**: Runs until no new inferences possible (typically 3-5 iterations)

### 7. Location Associations
- Infers connections between characters and places based on birth/death locations
- Creates `hasConnectionTo` relationships for geographical context

### Reasoning Impact

The reasoning engine typically enriches the graph by **15-25%**, adding thousands of inferred triples:

```
Initial triples:   ~8,000
Final triples:     ~10,000
New inferred:      ~2,000 (+25%)
```

This dramatically improves query capabilities, allowing users to discover:
- All members of a race or house (via inverse relationships)
- Extended family networks (via sibling inference)
- Cultural groupings (via class hierarchies)
- Comprehensive character affiliations (via multiple inference paths)

## Project Structure

```
tolkien_knowledge_graph/
├── config.py                      # Central configuration
├── requirements.txt               # Python dependencies
├── data/                          # Raw and processed data
│   ├── tolkien_pages.json        # Fetched wiki pages
│   └── parsed_templates.json     # Extracted templates
├── output/                        # Generated RDF files
│   ├── tolkien_kg.ttl            # Base knowledge graph
│   ├── tolkien_kg_reasoned.ttl   # Graph with inferred triples
│   ├── shacl_validation_report.json
│   └── shacl_validation_details.txt
├── shapes/                        # SHACL constraint definitions
│   └── tolkien_shapes.ttl
├── src/                           # Pipeline scripts
│   ├── 01_fetch_pages.py         # Download wiki pages via API
│   ├── 02_parse_templates.py     # Extract structured data
│   ├── 03_build_rdf.py           # Generate RDF triples
│   ├── 04_validate_shacl.py      # Quality validation
│   ├── 05_load_fuseki.py         # Load to triple store
│   ├── 06_apply_reasoning.py     # Run inference algorithms
│   └── inspect_data.py           # Data exploration utilities
└── web/                           # Flask application
    ├── app.py                     # Web server
    ├── templates/                 # HTML templates
    │   ├── index.html            # Homepage
    │   ├── entity.html           # Entity detail view
    │   ├── search.html           # Search interface
    │   └── base.html             # Base template
    └── static/
        └── style.css             # Styling
```

## Installation

### Prerequisites

- Python 3.8+
- Apache Jena Fuseki (for SPARQL endpoint)
- Git (optional)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd tolkien_knowledge_graph
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download and Start Apache Fuseki

```bash
# Download from https://jena.apache.org/download/
# Extract and run:
cd apache-jena-fuseki-x.x.x
./fuseki-server
# Or on Windows:
fuseki-server.bat
```

Fuseki will start on `http://localhost:3030`

## Usage

### Running the Complete Pipeline

Execute the scripts in order:

#### 1. Fetch Pages from Tolkien Gateway
```bash
python src/01_fetch_pages.py
```
Downloads wiki pages for ~50 major Tolkien entities via MediaWiki API. Output: `data/tolkien_pages.json`

#### 2. Parse Templates
```bash
python src/02_parse_templates.py
```
Extracts infoboxes and structured data from wikitext. Output: `data/parsed_templates.json`

#### 3. Build RDF Knowledge Graph
```bash
python src/03_build_rdf.py
```
Converts parsed data to RDF triples using Schema.org vocabulary. Output: `output/tolkien_kg.ttl`

#### 4. Validate with SHACL (Optional)
```bash
python src/04_validate_shacl.py
```
Validates data quality against SHACL constraints. Output: `output/shacl_validation_report.json`

#### 5. Apply Reasoning ⭐
```bash
python src/06_apply_reasoning.py
```
Runs all inference algorithms to enrich the graph. Output: `output/tolkien_kg_reasoned.ttl`

**This is the key step for the enhanced reasoning features!**

#### 6. Load into Fuseki
```bash
python src/05_load_fuseki.py
```
Uploads the reasoned graph to Apache Fuseki triple store.

### Launching the Web Interface

```bash
cd web
python app.py
```

Access at `http://localhost:5000`

Features:
- Browse all entities (characters, locations, events, organizations)
- Search by name
- View detailed entity information with all properties
- Explore inverse relationships (e.g., "Members of House of Elrond")
- Content negotiation: add `Accept: text/turtle` header for RDF

### Example SPARQL Queries

Access Fuseki's query interface at `http://localhost:3030/tolkien/sparql` or use the web app.

#### Find all members of the Fellowship
```sparql
PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
PREFIX tg: <http://tolkiengateway.net/kg/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?member ?name WHERE {
  ?member tgo:memberOf tg:Fellowship_of_the_Ring ;
          rdfs:label ?name .
}
```

#### Find all wielders of artifacts (using inverse inference)
```sparql
PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artifact ?artifactName ?wielder ?wielderName WHERE {
  ?artifact tgo:wieldedBy ?wielder ;
            rdfs:label ?artifactName .
  ?wielder rdfs:label ?wielderName .
}
```

#### Find all Elves and their subclasses (using RDFS inference)
```sparql
PREFIX tg: <http://tolkiengateway.net/kg/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?elf ?name WHERE {
  ?elf rdf:type tg:Elves ;
       rdfs:label ?name .
}
```

## Configuration

Edit `config.py` to customize:

- **Data limits**: `MAX_PAGES` (set to `None` for all pages)
- **API settings**: User agent, request delays
- **Fuseki endpoints**: Host, port, dataset name
- **Flask settings**: Host, port, debug mode
- **Namespace URIs**: Base URIs for resources and ontologies

## Development

### Adding New Reasoning Rules

Edit [src/06_apply_reasoning.py](src/06_apply_reasoning.py):

```python
def infer_custom_rule(self):
    """Your custom inference logic"""
    inferred = 0
    
    for s, p, o in self.graph.triples((None, YOUR_PROPERTY, None)):
        # Inference logic here
        self.graph.add((s, NEW_PROPERTY, o))
        inferred += 1
    
    return inferred

# Add to main() function
reasoner.infer_custom_rule()
```

### Extending Entity Types

Add new template mappings in [src/03_build_rdf.py](src/03_build_rdf.py):

```python
TEMPLATE_TO_CLASS = {
    'infobox your_type': SCHEMA.YourType,
    # ...
}
```

## Data Quality

- **SHACL Validation**: Ensures required properties, data types, and constraints
- **Automated Testing**: Template parsing validates against known patterns
- **Inference Verification**: Reasoning statistics track triple growth
- **Manual Review**: Output files are human-readable Turtle format

## Performance

- **Pages Processed**: ~50 entities (configurable)
- **Triples Generated**: ~8,000 base + ~2,000 inferred
- **Reasoning Time**: ~2-3 seconds
- **Query Response**: <100ms for typical SPARQL queries

## Troubleshooting

### Fuseki Connection Error
```
Error: Could not connect to Fuseki
```
**Solution**: Ensure Fuseki is running on port 3030: `./fuseki-server`

### Missing Data Files
```
Error: Input file not found
```
**Solution**: Run pipeline scripts in order (01 → 02 → 03 → 06 → 05)

### Import Errors
```
ModuleNotFoundError: No module named 'rdflib'
```
**Solution**: Activate virtual environment and reinstall: `pip install -r requirements.txt`

### Web App 404 Errors
**Solution**: Ensure Fuseki is loaded with data: `python src/05_load_fuseki.py`

## Future Enhancements

- [ ] Entity resolution and owl:sameAs linking to DBpedia
- [ ] Temporal reasoning (timeline inference)
- [ ] Geospatial reasoning (location hierarchies)
- [ ] Multi-language support
- [ ] REST API with OpenAPI documentation
- [ ] Graph visualization dashboard
- [ ] Incremental updates from Tolkien Gateway

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new reasoning rules
4. Submit a pull request

## License

This project is for educational purposes. Tolkien Gateway content is used under their terms of service.

## Acknowledgments

- **Tolkien Gateway** for comprehensive Middle-earth knowledge
- **Schema.org** for semantic vocabulary standards
- **Apache Jena** for SPARQL infrastructure
- **RDFLib** for Python RDF processing

## Contact

For questions or collaboration:
- Project: Mines Saint-Étienne University
- Purpose: Semantic Web & Knowledge Graph Research

---

**Built with semantic web technologies to preserve and explore the legendarium of J.R.R. Tolkien** 🧙‍♂️
