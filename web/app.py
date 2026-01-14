#!/usr/bin/env python3

"""
Linked Data interface for Tolkien Knowledge Graph
Serves entities in Turtle and HTML formats (content negotiation)
"""

from flask import Flask, render_template, request, Response, redirect, url_for, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
import re

app = Flask(__name__)

# Configuration
FUSEKI_ENDPOINT = "http://localhost:3030/tolkien/sparql"
BASE_URI = "http://tolkiengateway.net/kg/resource/"

def query_sparql(query):
    """Execute SPARQL query against Fuseki"""
    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"SPARQL Error: {e}")
        return None

def get_entity_description(entity_uri):
    """Get all triples about an entity"""
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX schema: <http://schema.org/>
    PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    
    SELECT ?property ?value ?valueLabel
    WHERE {{
        <{entity_uri}> ?property ?value .
        OPTIONAL {{ ?value rdfs:label ?valueLabel }}
    }}
    ORDER BY ?property
    """
    return query_sparql(query)

def get_all_entities():
    """Get all entities in the KG (ENHANCED - all types)"""
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>
    PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
    
    SELECT DISTINCT ?entity ?label ?type
    WHERE {
        ?entity rdfs:label ?label .
        ?entity a ?type .
        FILTER(?type IN (
            schema:Person, schema:Place, schema:Event,
            schema:Organization, schema:Book, schema:Language,
            tgo:Artifact, tgo:Race, tgo:House, tgo:Creature,
            schema:Thing
        ))
    }
    ORDER BY ?label
    LIMIT 100
    """
    return query_sparql(query)

def search_entities(query_text):
    """Search for entities by name (ENHANCED - all types)"""
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>
    PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
    
    SELECT DISTINCT ?entity ?label ?type
    WHERE {{
        ?entity rdfs:label ?label ;
                a ?type .
        FILTER(CONTAINS(LCASE(?label), LCASE("{query_text}")))
        FILTER(?type IN (
            schema:Person, schema:Place, schema:Event,
            schema:Organization, schema:Book, schema:Language,
            tgo:Artifact, tgo:Race, tgo:House, tgo:Creature,
            schema:Thing
        ))
    }}
    ORDER BY ?label
    LIMIT 20
    """
    return query_sparql(query)

def format_property_name(uri):
    """Convert property URI to readable name with custom mappings (ENHANCED)"""
    
    # Custom mappings for better readability
    custom_names = {
        'hasMember': 'Members',
        'raceIncludes': 'Members of this race',
        'houseIncludes': 'Members of this house',
        'wieldedBy': 'Wielded by',
        'hasParticipant': 'Participants',
        'riddenBy': 'Ridden by',
        'spokenBy': 'Spoken by',
        'memberOf': 'Member of',
        'belongsToRace': 'Race',
        'belongsToHouse': 'House',
        'wields': 'Wields',
        'participatedIn': 'Participated in',
        'notableFor': 'Notable for',
        'rides': 'Rides',
        'speaks': 'Speaks',
        'parentage': 'Parents',
        'siblings': 'Siblings',
        'spouse': 'Spouse',
        'children': 'Children',
        'birthlocation': 'Birth location',
        'deathlocation': 'Death location',
        'affiliation': 'Affiliation',
        'people': 'People/Race',
        'weapons': 'Weapons',
        'house': 'House',
        'language': 'Language',
        'steed': 'Steed'
    }
    
    # Extract property name
    if '#' in uri:
        name = uri.split('#')[-1]
    else:
        name = uri.split('/')[-1]
    
    # Check custom mapping first
    if name in custom_names:
        return custom_names[name]
    
    # Otherwise convert camelCase to Title Case
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    return name.replace('_', ' ').title()

def format_type_name(type_uri):
    """Convert type URI to readable name (ENHANCED)"""
    type_map = {
        'http://schema.org/Person': 'Person',
        'http://schema.org/Place': 'Place',
        'http://schema.org/Event': 'Event',
        'http://schema.org/Organization': 'Organization',
        'http://schema.org/Book': 'Book',
        'http://schema.org/Language': 'Language',
        'http://schema.org/Thing': 'Thing',
        'http://tolkiengateway.net/kg/ontology/Artifact': 'Artifact',
        'http://tolkiengateway.net/kg/ontology/Race': 'Race',
        'http://tolkiengateway.net/kg/ontology/House': 'House',
        'http://tolkiengateway.net/kg/ontology/Creature': 'Creature'
    }
    return type_map.get(type_uri, 'Unknown')

def is_uri(value):
    """Check if value is a URI"""
    return value.startswith('http://') or value.startswith('https://')

@app.route('/')
def index():
    """Homepage with entity list"""
    results = get_all_entities()
    entities = []
    
    if results:
        for binding in results['results']['bindings']:
            entity = {
                'uri': binding['entity']['value'],
                'label': binding['label']['value'],
                'type': format_type_name(binding['type']['value']),
                'local_name': binding['entity']['value'].split('/')[-1]
            }
            entities.append(entity)
    
    return render_template('index.html', entities=entities)

@app.route('/search')
def search():
    """Search endpoint"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    results = search_entities(query)
    entities = []
    
    if results:
        for binding in results['results']['bindings']:
            entity = {
                'uri': binding['entity']['value'],
                'label': binding['label']['value'],
                'type': format_type_name(binding['type']['value']),
                'local_name': binding['entity']['value'].split('/')[-1]
            }
            entities.append(entity)
    
    return render_template('search.html', query=query, entities=entities)

@app.route('/resource/<entity_name>')
def entity(entity_name):
    """Entity page with content negotiation"""
    entity_uri = BASE_URI + entity_name
    
    # Content negotiation
    accept_header = request.headers.get('Accept', '')
    
    # If requesting Turtle/RDF
    if 'text/turtle' in accept_header or 'application/rdf+xml' in accept_header:
        return serve_turtle(entity_uri)
    
    # Otherwise serve HTML
    return serve_html(entity_uri, entity_name)

def serve_turtle(entity_uri):
    """Serve entity as Turtle (RDF format)"""
    query = f"""
    CONSTRUCT {{
        <{entity_uri}> ?p ?o .
    }}
    WHERE {{
        <{entity_uri}> ?p ?o .
    }}
    """
    
    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query)
    
    try:
        # Get Turtle format from Fuseki
        sparql.setReturnFormat('turtle')
        results = sparql.query().convert()
        return Response(results, mimetype='text/turtle')
    except Exception as e:
        return Response(f"Error: {e}", status=500)

def serve_html(entity_uri, entity_name):
    """Serve entity as HTML"""
    results = get_entity_description(entity_uri)
    
    if not results or not results['results']['bindings']:
        return render_template('entity.html',
                             entity_name=entity_name,
                             entity_uri=entity_uri,
                             error="Entity not found"), 404
    
    # Parse results into structured data
    properties = {}
    entity_label = entity_name.replace('_', ' ')
    entity_type = None
    
    for binding in results['results']['bindings']:
        prop_uri = binding['property']['value']
        prop_name = format_property_name(prop_uri)
        value = binding['value']['value']
        value_label = binding.get('valueLabel', {}).get('value', None)
        
        # Track type
        if 'type' in prop_uri:
            entity_type = format_type_name(value)
        
        # Track label
        if 'label' in prop_uri:
            entity_label = value
        
        # Build property structure
        if prop_name not in properties:
            properties[prop_name] = []
        
        properties[prop_name].append({
            'value': value,
            'label': value_label or value,
            'is_uri': is_uri(value),
            'local_name': value.split('/')[-1] if is_uri(value) else None
        })
    
    return render_template('entity.html',
                         entity_name=entity_name,
                         entity_uri=entity_uri,
                         entity_label=entity_label,
                         entity_type=entity_type,
                         properties=properties)

@app.route('/api/stats')
def stats():
    """API endpoint for KG statistics (ENHANCED)"""
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX tgo: <http://tolkiengateway.net/kg/ontology/>
    
    SELECT
        (COUNT(DISTINCT ?s) AS ?triples)
        (COUNT(DISTINCT ?person) AS ?persons)
        (COUNT(DISTINCT ?place) AS ?places)
        (COUNT(DISTINCT ?event) AS ?events)
        (COUNT(DISTINCT ?org) AS ?organizations)
        (COUNT(DISTINCT ?artifact) AS ?artifacts)
        (COUNT(DISTINCT ?race) AS ?races)
    WHERE {
        ?s ?p ?o .
        OPTIONAL { ?person a schema:Person }
        OPTIONAL { ?place a schema:Place }
        OPTIONAL { ?event a schema:Event }
        OPTIONAL { ?org a schema:Organization }
        OPTIONAL { ?artifact a tgo:Artifact }
        OPTIONAL { ?race a tgo:Race }
    }
    """
    
    results = query_sparql(query)
    if results and results['results']['bindings']:
        binding = results['results']['bindings'][0]
        return jsonify({
            'triples': int(binding['triples']['value']),
            'persons': int(binding.get('persons', {}).get('value', 0)),
            'places': int(binding.get('places', {}).get('value', 0)),
            'events': int(binding.get('events', {}).get('value', 0)),
            'organizations': int(binding.get('organizations', {}).get('value', 0)),
            'artifacts': int(binding.get('artifacts', {}).get('value', 0)),
            'races': int(binding.get('races', {}).get('value', 0))
        })
    
    return jsonify({'error': 'Could not retrieve stats'}), 500

if __name__ == '__main__':
    print("="*60)
    print("Tolkien Knowledge Graph - Linked Data Interface (Enhanced)")
    print("="*60)
    print("\n✓ Starting web server...")
    print("  → Visit: http://localhost:5000")
    print("  → Fuseki endpoint: " + FUSEKI_ENDPOINT)
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)
