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

# Define namespaces (DBpedia removed - schema.org only)
TG = Namespace(RESOURCE_NS)
TGO = Namespace(ONTOLOGY_NS)
SCHEMA = Namespace(SCHEMA_ORG)

# Template to schema.org class mappings
TEMPLATE_TO_CLASS = {
    # Both orders supported
    'infobox character': SCHEMA.Person,
    'character': SCHEMA.Person,
    'infobox location': SCHEMA.Place,
    'location infobox': SCHEMA.Place,
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

def extract_all_wikilinks(text):
    """
    Extract all wikilink targets from text
    Example: "[[Gandalf]] and [[Frodo]]" -> ["Gandalf", "Frodo"]
    """
    if not text:
        return []
    
    # Find all [[target]] or [[target|display]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches if m.strip()]

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

def create_or_get_entity(entity_name, entity_type, graph):
    """
    Create entity if it doesn't exist, or return existing URI
    
    Args:
        entity_name: Name of the entity
        entity_type: RDF type (SCHEMA.Event, SCHEMA.Organization, etc.)
        graph: RDF graph
    
    Returns:
        URIRef of the entity
    """
    entity_uri = create_entity_uri(entity_name)
    
    # Check if entity already exists
    if (entity_uri, RDF.type, None) not in graph:
        # Create new entity
        graph.add((entity_uri, RDF.type, entity_type))
        graph.add((entity_uri, RDFS.label, Literal(entity_name, lang='en')))
    
    return entity_uri

def extract_embedded_entities(entity_uri, params, graph):
    """
    Extract entities embedded in properties (events, organizations, races, weapons)
    and create them as standalone entities with relationships
    """
    # 1. EVENTS - from 'events' property (locations) or 'notablefor' (characters)
    if 'events' in params:
        event_names = extract_all_wikilinks(params['events'])
        for event_name in event_names:
            event_uri = create_or_get_entity(event_name, SCHEMA.Event, graph)
            graph.add((entity_uri, TGO.participatedIn, event_uri))
    
    if 'notablefor' in params:
        # Notable events/achievements
        notable_items = extract_all_wikilinks(params['notablefor'])
        for item_name in notable_items:
            # Could be event or action - create as Event
            item_uri = create_or_get_entity(item_name, SCHEMA.Event, graph)
            graph.add((entity_uri, TGO.notableFor, item_uri))
    
    # 2. ORGANIZATIONS - from 'affiliation' property
    if 'affiliation' in params:
        org_names = extract_all_wikilinks(params['affiliation'])
        for org_name in org_names:
            org_uri = create_or_get_entity(org_name, SCHEMA.Organization, graph)
            graph.add((entity_uri, SCHEMA.memberOf, org_uri))
    
    # 3. RACES/PEOPLES - from 'people' property
    if 'people' in params:
        race_names = extract_all_wikilinks(params['people'])
        for race_name in race_names:
            race_uri = create_or_get_entity(race_name, TGO.Race, graph)
            graph.add((entity_uri, TGO.belongsToRace, race_uri))
    
    # 4. WEAPONS/ARTIFACTS - from 'weapons' property
    if 'weapons' in params:
        weapon_names = extract_all_wikilinks(params['weapons'])
        for weapon_name in weapon_names:
            weapon_uri = create_or_get_entity(weapon_name, TGO.Artifact, graph)
            graph.add((entity_uri, TGO.wields, weapon_uri))
    
    # 5. HOUSES/DYNASTIES - from 'house' property
    if 'house' in params:
        house_names = extract_all_wikilinks(params['house'])
        for house_name in house_names:
            house_uri = create_or_get_entity(house_name, TGO.House, graph)
            graph.add((entity_uri, TGO.belongsToHouse, house_uri))
    
    # 6. LANGUAGES - from 'language' property
    if 'language' in params:
        lang_names = extract_all_wikilinks(params['language'])
        for lang_name in lang_names:
            lang_uri = create_or_get_entity(lang_name, SCHEMA.Language, graph)
            graph.add((entity_uri, TGO.speaks, lang_uri))
    
    # 7. STEEDS/MOUNTS - from 'steed' property
    if 'steed' in params:
        steed_names = extract_all_wikilinks(params['steed'])
        for steed_name in steed_names:
            steed_uri = create_or_get_entity(steed_name, TGO.Creature, graph)
            graph.add((entity_uri, TGO.rides, steed_uri))

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
    template_type = infobox['name'].lower().strip()
    
    # Map template to RDF class
    rdf_class = TEMPLATE_TO_CLASS.get(template_type, SCHEMA.Thing)
    
    # AUTO-DETECTION: If no template match but has location-indicating properties
    if rdf_class == SCHEMA.Thing:
        params = infobox['params']
        location_indicators = ['location', 'inhabitants', 'type', 'founded', 
                              'destroyed', 'capital', 'regions', 'settlements']
        
        if any(indicator in params for indicator in location_indicators):
            rdf_class = SCHEMA.Place
            print(f"  → Auto-detected as Place: {page_title}")
    
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
    
    # Extract embedded entities from properties
    extract_embedded_entities(entity_uri, infobox['params'], graph)
    
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
    
    # Bind namespaces (DBpedia removed)
    g.bind("tg", TG)
    g.bind("tgo", TGO)
    g.bind("schema", SCHEMA)
    g.bind("owl", OWL)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    
    print("\nBuilding RDF Knowledge Graph (schema.org only)...")
    
    stats = {
        'total_pages': 0,
        'pages_with_infoboxes': 0,
        'total_triples': 0,
        'entities_created': 0,
        'events_extracted': 0,
        'organizations_extracted': 0,
        'races_extracted': 0,
        'artifacts_extracted': 0
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
    
    # Count extracted entities
    stats['events_extracted'] = len(list(g.subjects(RDF.type, SCHEMA.Event)))
    stats['organizations_extracted'] = len(list(g.subjects(RDF.type, SCHEMA.Organization)))
    stats['races_extracted'] = len(list(g.subjects(RDF.type, TGO.Race)))
    stats['artifacts_extracted'] = len(list(g.subjects(RDF.type, TGO.Artifact)))
    
    return g, stats

def main():
    """Main execution function"""
    print("="*60)
    print("Tolkien Gateway RDF Builder (schema.org only)")
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
    print(f"\n📊 Extracted Entities:")
    print(f"   - Events: {stats['events_extracted']}")
    print(f"   - Organizations: {stats['organizations_extracted']}")
    print(f"   - Races: {stats['races_extracted']}")
    print(f"   - Artifacts: {stats['artifacts_extracted']}")
    print(f"\nTotal triples: {stats['total_triples']:,}")
    print(f"\nOutput file: {RDF_OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(RDF_OUTPUT_FILE) / (1024*1024):.2f} MB")
    

if __name__ == "__main__":
    main()
