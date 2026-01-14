"""
Configuration file for Tolkien Gateway Knowledge Graph project
"""

# MediaWiki API Settings
WIKI_DOMAIN = "tolkiengateway.net"
WIKI_PATH = "/wiki/"  
USER_AGENT = "TolkienKGBuilder/1.0 (university-project-mines-saint-etienne; python-mwclient)"  # More descriptive

# Namespace URIs
NAMESPACE_BASE = "http://tolkiengateway.net/kg/"
RESOURCE_NS = f"{NAMESPACE_BASE}resource/"
ONTOLOGY_NS = f"{NAMESPACE_BASE}ontology/"
VOCAB_NS = f"{NAMESPACE_BASE}vocab/"

# External Ontologies
SCHEMA_ORG = "http://schema.org/"
DBPEDIA_RESOURCE = "http://dbpedia.org/resource/"
DBPEDIA_ONTOLOGY = "http://dbpedia.org/ontology/"

# File Paths
DATA_DIR = "data"
OUTPUT_DIR = "output"
EXTERNAL_DATA_DIR = f"{DATA_DIR}/external"

# File names
RAW_PAGES_FILE = f"{DATA_DIR}/tolkien_pages.json"
PARSED_TEMPLATES_FILE = f"{DATA_DIR}/parsed_templates.json"
RDF_OUTPUT_FILE = f"{OUTPUT_DIR}/tolkien_kg.ttl"
SHACL_SHAPES_FILE = f"{OUTPUT_DIR}/shacl_shapes.ttl"
REASONING_OUTPUT_FILE = f"{OUTPUT_DIR}/tolkien_kg_reasoned.ttl"

# Apache Fuseki Settings
FUSEKI_HOST = "http://localhost:3030"
FUSEKI_DATASET = "tolkien"
FUSEKI_ENDPOINT = f"{FUSEKI_HOST}/{FUSEKI_DATASET}"
FUSEKI_QUERY_ENDPOINT = f"{FUSEKI_HOST}/{FUSEKI_DATASET}/sparql"
FUSEKI_UPDATE_ENDPOINT = f"{FUSEKI_HOST}/{FUSEKI_DATASET}/update"
FUSEKI_DATA_ENDPOINT = f"{FUSEKI_HOST}/{FUSEKI_DATASET}/data"

# Flask Server Settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Processing Settings
BATCH_SIZE = 100
MAX_PAGES = 50  # Set to None for all pages, or a number for testing
REQUEST_DELAY = 0.5  # Seconds between requests

# Template to RDF Class Mappings
TEMPLATE_MAPPINGS = {
    'infobox character': 'Person',
    'infobox location': 'Place',
    'infobox book': 'Book',
    'infobox event': 'Event',
    'infobox item': 'Thing',
    'infobox language': 'Language'
}

# External Data Files
MULTILINGUAL_CSV = f"{EXTERNAL_DATA_DIR}/lotr_multilingual.csv"
METW_CARDS_JSON = f"{EXTERNAL_DATA_DIR}/metw_cards.json"
