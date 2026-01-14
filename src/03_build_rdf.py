#!/usr/bin/env python3

"""
Steps 5-6: Build RDF Knowledge Graph from parsed templates
Outputs: output/tolkien_kg.ttl
"""

import json
import re
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import FOAF, DCTERMS, XSD
from tqdm import tqdm
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config import *

# Define namespaces
TG = Namespace(RESOURCE_NS)
TGO = Namespace(ONTOLOGY_NS)
SCHEMA = Namespace(SCHEMA_ORG)
DBP = Namespace(DBPEDIA_RESOURCE)
DBO = Namespace(DBPEDIA_ONTOLOGY)

# Template to schema.org class mappings
TEMPLATE_TO_CLASS = {
    # Both orders supported (infobox character vs character)
    'infobox character': SCHEMA.Person,
    'character': SCHEMA.Person,
    
    'infobox location': SCHEMA.Place,
    'location infobox': SCHEMA.Place,  # ← FIX: Support reversed order
    'location': SCHEMA.Place,
    
    'infobox book': SCHEMA.Book,
    'book': SCHEMA.Book,
    
    'infobox event': SCHEMA.Event,
    'event': SCHEMA.Event,
    
    'infobox item': SCHEMA.Thing,
    'item': SCHEMA.Thing,
    
    'infobox language': SCHEMA.Language,
    'language': SCHEMA.Language,
    
    'infobox weapon': SCHEMA.Product,
    'weapon': SCHEMA.Product,
    
    'infobox organization': SCHEMA.Organization,
    'organization': SCHEMA.Organization
}

# Property mappings for character infoboxes
CHARACTER_PROPERTY_MAP = {
    'name': SCHEMA.name,
    'birth': SCHEMA.birthDate,
    'death': SCHEMA.deathDate,
    'culture': SCHEMA.nationality,
    'race': TGO.race,
    'realm': TGO.realm,
    'weapon': TGO.hasWeapon,
    'title': SCHEMA.jobTitle,
    'gender': SCHEMA.gender,
    'house': TGO.house,
    'parentage': TGO.parentage,
    'spouse': SCHEMA.spouse,
    'children': SCHEMA.children,
    'height': SCHEMA.height
}

# Property mappings for location infoboxes
LOCATION_PROPERTY_MAP = {
    'name': SCHEMA.name,
    'type': SCHEMA.additionalType,
    'location': SCHEMA.containedInPlace,
    'inhabitants': TGO.inhabitants,
    'founded': TGO.foundingDate,
    'destroyed': TGO.destructionDate,
    'capital': TGO.hasCapital
}

# Property mappings for book infoboxes
BOOK_PROPERTY_MAP = {
    'name': SCHEMA.name,
    'author': SCHEMA.author,
    'published': SCHEMA.datePublished,
    'publisher': SCHEMA.publisher,
    'isbn': SCHEMA.isbn,
    'language': SCHEMA.inLanguage,
    'pages': SCHEMA.numberOfPages
}

def create_entity_uri(page_title):
    """
    Create URI-safe entity identifier from page title
    Example: "Gandalf the Grey" -> http://tolkiengateway.net/kg/resource/Gandalf_the_Grey
    """
    # Remove special characters, replace spaces with underscores
    clean_title = re.sub(r'[^\w\s-]', '', page_title)
    clean_title = re.sub(r'\s+', '_', clean_title)
    return TG[clean_title]

def clean_wikitext_value(value):
    """
    Clean wikitext markup from values
    Examples:
        [[Gandalf]] -> Gandalf
        [[Gandalf|Gandalf the Grey]] -> Gandalf the Grey
        '''bold''' -> bold
    """
    # Remove wikilinks: [[target|text]] -> text or [[target]] -> target
    value = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', value)
    value = re.sub(r'\[\[([^\]]+)\]\]', r'\1', value)
    # Remove bold/italic markers
    value = re.sub(r"'''([^']+)'''", r'\1', value)
    value = re.sub(r"''([^']+)''", r'\1', value)
    # Remove HTML tags
    value = re.sub(r'<[^>]+>', '', value)
    # Remove templates (simplified)
    value = re.sub(r'\{\{[^\}]+\}\}', '', value)
    # Clean whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    return value

def extract_wikilink_target(value):
    """
    Extract target page from wikilink
    Example: [[Gandalf the Grey]] -> Gandalf the Grey
    """
    match = re.search(r'\[\[([^\]|]+)', value)
    if match:
        return match.group(1).strip()
    return None

def is_descriptive_value(value):
    """
    Check if value is a descriptive note rather than entity reference
    These are informative but cannot be used as relationship targets
    """
    descriptive_patterns = [
        'never married', 'unmarried', 'never',
        'none', 'unknown', 'n/a', '-',
        'no children', 'no spouse', 'childless',
        'none known', 'not applicable',
        'at least one', 'several', 'many', 'some',
        'disputed', 'unclear', 'possibly'
    ]
    
    value_lower = value.lower().strip()
    # Check exact matches
    if value_lower in descriptive_patterns:
        return True
    # Check if starts with descriptive phrases
    descriptive_prefixes = ['at least', 'possibly', 'unknown', 'none']
    for prefix in descriptive_prefixes:
        if value_lower.startswith(prefix):
            return True
    return False

def get_descriptive_property(param_name):
    """
    Map relationship properties to their descriptive equivalents
    """
    descriptive_map = {
        'spouse': TGO.maritalStatus,
        'children': TGO.childrenNote,
        'parentage': TGO.parentageNote,
        'siblings': TGO.siblingsNote,
        'house': TGO.houseNote,
        'affiliation': TGO.affiliationNote,
    }
    return descriptive_map.get(param_name, TGO[param_name + '_note'])

def map_infobox_to_rdf(page_title, infobox, graph):
    """
    Convert a single infobox to RDF triples
    
    Args:
        page_title: Page title (entity name)
        infobox: Dictionary with 'name' and 'params'
        graph: rdflib.Graph object to add triples to
    
    Returns:
        URIRef of created entity
    """
    entity_uri = create_entity_uri(page_title)
    template_type = infobox['name'].lower().strip()  # Normalize to lowercase
    
    # Map template to RDF class
    rdf_class = TEMPLATE_TO_CLASS.get(template_type, SCHEMA.Thing)
    graph.add((entity_uri, RDF.type, rdf_class))
    
    # Add rdfs:label
    graph.add((entity_uri, RDFS.label, Literal(page_title, lang='en')))
    
    # Select appropriate property map
    if 'character' in template_type:
        property_map = CHARACTER_PROPERTY_MAP
    elif 'location' in template_type:
        property_map = LOCATION_PROPERTY_MAP
    elif 'book' in template_type:
        property_map = BOOK_PROPERTY_MAP
    else:
        property_map = {}
    
    # Map parameters to properties
    for param_name, param_value in infobox['params'].items():
        param_name = param_name.lower().strip()
        
        # Skip empty values
        if not param_value or param_value.strip() == '':
            continue
        
        # Get RDF property for relationships
        rdf_property = property_map.get(param_name)
        
        if not rdf_property:
            # Use custom property in TGO namespace
            safe_param = re.sub(r'[^\w]', '_', param_name)
            rdf_property = TGO[safe_param]
        
        # Clean value
        clean_value = clean_wikitext_value(param_value)
        
        # Check if value is a wikilink (entity reference)
        target = extract_wikilink_target(param_value)
        
        if target:
            # It's a relationship to another entity - use relationship property
            target_uri = create_entity_uri(target)
            graph.add((entity_uri, rdf_property, target_uri))
        else:
            # It's a literal value - decide which property to use
            if is_descriptive_value(clean_value):
                # Use descriptive property (won't be inverted during reasoning)
                descriptive_property = get_descriptive_property(param_name)
                graph.add((entity_uri, descriptive_property, Literal(clean_value, lang='en')))
            else:
                # Use standard property for normal literal values
                graph.add((entity_uri, rdf_property, Literal(clean_value, lang='en')))
    
    # Add source information
    source_url = f"https://tolkiengateway.net/wiki/{page_title.replace(' ', '_')}"
    graph.add((entity_uri, DCTERMS.source, URIRef(source_url)))
    
    return entity_uri

def process_wikilinks(page_title, wikilinks, graph):
    """
    Add triples for page links (relationships between entities)
    """
    source_uri = create_entity_uri(page_title)
    
    for link in wikilinks:
        target_title = link['target']
        target_uri = create_entity_uri(target_title)
        # Add generic "links to" relationship
        graph.add((source_uri, SCHEMA.mentions, target_uri))

def build_knowledge_graph(pages_data):
    """
    Build complete RDF graph from all pages
    
    Returns:
        rdflib.Graph object
    """
    g = Graph()
    
    # Bind namespaces
    g.bind("tg", TG)
    g.bind("tgo", TGO)
    g.bind("schema", SCHEMA)
    g.bind("dbp", DBP)
    g.bind("dbo", DBO)
    g.bind("owl", OWL)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    
    print("\nBuilding RDF Knowledge Graph...")
    
    stats = {
        'total_pages': 0,
        'pages_with_infoboxes': 0,
        'total_triples': 0,
        'entities_created': 0
    }
    
    for page in tqdm(pages_data, desc="Converting to RDF"):
        stats['total_pages'] += 1
        
        # Process infoboxes
        if page['infoboxes']:
            stats['pages_with_infoboxes'] += 1
            
            for infobox in page['infoboxes']:
                entity_uri = map_infobox_to_rdf(page['title'], infobox, g)
                if entity_uri:
                    stats['entities_created'] += 1
        
        # Process wikilinks (sampling to avoid too many triples)
        if page['wikilinks']:
            # Only add links for pages with infoboxes
            if page['infoboxes']:
                process_wikilinks(page['title'], page['wikilinks'][:10], g)
    
    stats['total_triples'] = len(g)
    
    return g, stats

def main():
    """Main execution function"""
    print("="*60)
    print("Tolkien Gateway RDF Builder")
    print("="*60)
    
    # Load parsed templates
    print(f"\nLoading parsed templates from {PARSED_TEMPLATES_FILE}...")
    with open(PARSED_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages_data = data['pages']
    print(f"✓ Loaded {len(pages_data)} pages")
    
    # Build RDF graph
    graph, stats = build_knowledge_graph(pages_data)
    
    # Save to Turtle format
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"\n✓ Serializing to Turtle format...")
    graph.serialize(destination=RDF_OUTPUT_FILE, format='turtle')
    
    # Print statistics
    print("\n" + "="*60)
    print("Knowledge Graph Statistics")
    print("="*60)
    print(f"Total pages processed: {stats['total_pages']}")
    print(f"Pages with infoboxes: {stats['pages_with_infoboxes']}")
    print(f"Entities created: {stats['entities_created']}")
    print(f"Total triples: {stats['total_triples']:,}")
    print(f"\nOutput file: {RDF_OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(RDF_OUTPUT_FILE) / (1024*1024):.2f} MB")
    
    # Show sample triples
    print("\n" + "="*60)
    print("Sample Triples (first 10):")
    print("="*60)
    for i, (s, p, o) in enumerate(graph):
        if i >= 10:
            break
        print(f"{s}")
        print(f"  {p}")
        print(f"  {o}\n")

if __name__ == "__main__":
    main()
