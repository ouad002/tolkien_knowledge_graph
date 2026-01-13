#!/usr/bin/env python3
"""
Step 6: Apply reasoning rules to the Tolkien Knowledge Graph
Infers new relationships using RDFS/OWL semantics and custom rules
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config import *

from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from pathlib import Path
import time

# Namespaces
TG = Namespace("http://tolkiengateway.net/kg/resource/")
TGO = Namespace("http://tolkiengateway.net/kg/ontology/")
SCHEMA = Namespace("http://schema.org/")

class TolkienReasoner:
    def __init__(self, input_file):
        """Load the base knowledge graph"""
        print("Loading Knowledge Graph...")
        self.graph = Graph()
        self.graph.parse(input_file, format='turtle')
        
        # Bind namespaces
        self.graph.bind('tg', TG)
        self.graph.bind('tgo', TGO)
        self.graph.bind('schema', SCHEMA)
        self.graph.bind('owl', OWL)
        
        self.initial_triples = len(self.graph)
        print(f"  ✓ Loaded {self.initial_triples:,} triples\n")
    
    def define_ontology(self):
        """Define class hierarchies and property relationships"""
        print("Defining ontology axioms...")
        
        # ============================================================
        # RACE/SPECIES HIERARCHY
        # ============================================================
        print("  → Defining race hierarchy...")
        
        # Elven races
        self.graph.add((TG.Noldor, RDFS.subClassOf, TG.Elves))
        self.graph.add((TG.Sindar, RDFS.subClassOf, TG.Elves))
        self.graph.add((TG.Silvan_Elves, RDFS.subClassOf, TG.Elves))
        self.graph.add((TG.Half_elven, RDFS.subClassOf, TG.Elves))
        
        # Free Peoples
        self.graph.add((TG.Elves, RDFS.subClassOf, TG.FreePeoples))
        self.graph.add((TG.Hobbits, RDFS.subClassOf, TG.FreePeoples))
        self.graph.add((TG.Dwarves, RDFS.subClassOf, TG.FreePeoples))
        self.graph.add((TG.Men, RDFS.subClassOf, TG.FreePeoples))
        
        # Human cultures
        self.graph.add((TG.Gondorians, RDFS.subClassOf, TG.Men))
        self.graph.add((TG.Rohirrim, RDFS.subClassOf, TG.Men))
        
        # Divine beings
        self.graph.add((TG.Maiar, RDFS.subClassOf, TG.Ainur))
        self.graph.add((TG.Wizards, RDFS.subClassOf, TG.Maiar))
        
        # Evil creatures
        self.graph.add((TG.Orcs, RDFS.subClassOf, TG.EvilCreatures))
        self.graph.add((TG.Spiders, RDFS.subClassOf, TG.EvilCreatures))
        
        # ============================================================
        # PROPERTY HIERARCHIES
        # ============================================================
        print("  → Defining property hierarchies...")
        
        # Family relationships
        self.graph.add((TGO.parentage, RDFS.subPropertyOf, SCHEMA.parent))
        self.graph.add((SCHEMA.children, RDFS.subPropertyOf, SCHEMA.relatedTo))
        self.graph.add((SCHEMA.spouse, RDFS.subPropertyOf, SCHEMA.relatedTo))
        self.graph.add((TGO.siblings, RDFS.subPropertyOf, SCHEMA.relatedTo))
        
        # Symmetric properties
        self.graph.add((SCHEMA.spouse, RDF.type, OWL.SymmetricProperty))
        self.graph.add((TGO.siblings, RDF.type, OWL.SymmetricProperty))
        
        # Location relationships
        self.graph.add((TGO.location, RDFS.subPropertyOf, SCHEMA.location))
        self.graph.add((TGO.birthlocation, RDFS.subPropertyOf, TGO.location))
        self.graph.add((TGO.deathlocation, RDFS.subPropertyOf, TGO.location))
        
        print(f"  ✓ Added ontology axioms\n")
    
    def infer_family_relationships(self):
        """Infer sibling and parent-child relationships"""
        print("Inferring family relationships...")
        inferred = 0
        
        # Rule 1: Shared parentage → siblings
        parent_children = {}
        for s, p, o in self.graph.triples((None, TGO.parentage, None)):
            if o not in parent_children:
                parent_children[o] = []
            parent_children[o].append(s)
        
        for parent, children in parent_children.items():
            if len(children) > 1:
                for i, child1 in enumerate(children):
                    for child2 in children[i+1:]:
                        if (child1, TGO.siblings, child2) not in self.graph:
                            self.graph.add((child1, TGO.siblings, child2))
                            self.graph.add((child2, TGO.siblings, child1))
                            inferred += 2
        
        # Rule 2: Inverse parentage (parent → child)
        for s, p, o in list(self.graph.triples((None, TGO.parentage, None))):
            if (o, SCHEMA.children, s) not in self.graph:
                self.graph.add((o, SCHEMA.children, s))
                inferred += 1
        
        # Rule 3: Spouse symmetry
        for s, p, o in list(self.graph.triples((None, SCHEMA.spouse, None))):
            if (o, SCHEMA.spouse, s) not in self.graph:
                self.graph.add((o, SCHEMA.spouse, s))
                inferred += 1
        
        print(f"  ✓ Inferred {inferred} family relationships\n")
        return inferred
    
    def infer_fellowship_membership(self):
        """Tag Fellowship members"""
        print("Inferring Fellowship membership...")
        inferred = 0
        
        fellowship_members = [
            TG.Frodo_Baggins, TG.Samwise_Gamgee, TG.Gandalf,
            TG.Aragorn_II, TG.Legolas, TG.Gimli, TG.Boromir,
            TG.Meriadoc_Brandybuck, TG.Peregrin_Took
        ]
        
        for member in fellowship_members:
            if (member, RDF.type, SCHEMA.Person) in self.graph:
                if (member, TGO.memberOf, TG.Fellowship_of_the_Ring) not in self.graph:
                    self.graph.add((member, TGO.memberOf, TG.Fellowship_of_the_Ring))
                    inferred += 1
        
        # Define Fellowship as an organization
        self.graph.add((TG.Fellowship_of_the_Ring, RDF.type, SCHEMA.Organization))
        self.graph.add((TG.Fellowship_of_the_Ring, RDFS.label, Literal("Fellowship of the Ring", lang='en')))
        
        print(f"  ✓ Inferred {inferred} Fellowship memberships\n")
        return inferred
    
    def infer_race_based_groups(self):
        """Infer group memberships based on race"""
        print("Inferring race-based group memberships...")
        inferred = 0
        
        # Map races to broader groups
        race_to_group = {
            TG.Hobbits: (TG.HobbitKind, "Hobbit-kind"),
            TG.Dwarves: (TG.DwarfKind, "Dwarf-kind"),
            TG.Gondorians: (TG.Númenóreans, "Númenórean descendants"),
            TG.Rohirrim: (TG.Northmen, "Northmen"),
            TG.Maiar: (TG.Ainur, "Ainur"),
            TG.Orcs: (TG.ServantsOfMordor, "Servants of Mordor"),
        }
        
        for char, _, race in self.graph.triples((None, TGO.people, None)):
            if race in race_to_group:
                group_uri, group_label = race_to_group[race]
                if (char, TGO.belongsTo, group_uri) not in self.graph:
                    self.graph.add((char, TGO.belongsTo, group_uri))
                    inferred += 1
                
                # Add group label if not exists
                if (group_uri, RDFS.label, None) not in self.graph:
                    self.graph.add((group_uri, RDFS.label, Literal(group_label, lang='en')))
        
        print(f"  ✓ Inferred {inferred} group memberships\n")
        return inferred
    
    def apply_rdfs_entailment(self):
        """Apply RDFS reasoning (subclass and subproperty inference)"""
        print("Applying RDFS entailment...")
        inferred = 0
        max_iterations = 10
        
        for iteration in range(max_iterations):
            new_triples = 0
            
            # SubClassOf transitivity: if X subClassOf Y and a rdf:type X, then a rdf:type Y
            for subclass, _, superclass in list(self.graph.triples((None, RDFS.subClassOf, None))):
                for instance, _, _ in list(self.graph.triples((None, RDF.type, subclass))):
                    if (instance, RDF.type, superclass) not in self.graph:
                        self.graph.add((instance, RDF.type, superclass))
                        new_triples += 1
            
            # SubPropertyOf: if p1 subPropertyOf p2 and (a, p1, b), then (a, p2, b)
            for subprop, _, superprop in list(self.graph.triples((None, RDFS.subPropertyOf, None))):
                for s, _, o in list(self.graph.triples((None, subprop, None))):
                    if (s, superprop, o) not in self.graph:
                        self.graph.add((s, superprop, o))
                        new_triples += 1
            
            inferred += new_triples
            if new_triples == 0:
                break
        
        print(f"  ✓ Inferred {inferred} triples via RDFS reasoning (converged in {iteration+1} iterations)\n")
        return inferred
    
    def infer_locations_from_birth_death(self):
        """If character born/died somewhere, they have connection to that location"""
        print("Inferring location associations...")
        inferred = 0
        
        # Birth locations
        for char, _, loc in list(self.graph.triples((None, TGO.birthlocation, None))):
            if (char, TGO.hasConnectionTo, loc) not in self.graph:
                self.graph.add((char, TGO.hasConnectionTo, loc))
                inferred += 1
        
        # Death locations
        for char, _, loc in list(self.graph.triples((None, TGO.deathlocation, None))):
            if (char, TGO.hasConnectionTo, loc) not in self.graph:
                self.graph.add((char, TGO.hasConnectionTo, loc))
                inferred += 1
        
        print(f"  ✓ Inferred {inferred} location associations\n")
        return inferred
    
    def export_reasoned_graph(self, output_file):
        """Save the enriched graph"""
        print(f"Exporting reasoned graph to {output_file}...")
        self.graph.serialize(destination=output_file, format='turtle')
        
        final_triples = len(self.graph)
        new_triples = final_triples - self.initial_triples
        
        print(f"\n{'='*60}")
        print("REASONING SUMMARY")
        print('='*60)
        print(f"Initial triples:     {self.initial_triples:,}")
        print(f"Final triples:       {final_triples:,}")
        print(f"New inferred:        {new_triples:,} (+{100*new_triples/self.initial_triples:.1f}%)")
        print(f"\n✓ Saved to: {output_file}")
        
    def generate_statistics(self):
        """Generate statistics about the reasoned graph"""
        print(f"\n{'='*60}")
        print("KNOWLEDGE GRAPH STATISTICS")
        print('='*60)
        
        # Count entities by type
        persons = len(list(self.graph.subjects(RDF.type, SCHEMA.Person)))
        locations = len(set(self.graph.subjects(RDF.type, SCHEMA.Thing)))
        
        print(f"\nEntity Counts:")
        print(f"  Characters:          {persons}")
        print(f"  Locations/Things:    {locations}")
        
        # Count relationships
        stats = {
            'Family relationships': [
                (TGO.parentage, 'Parentage'),
                (TGO.siblings, 'Siblings'),
                (SCHEMA.spouse, 'Marriages'),
                (SCHEMA.children, 'Children'),
            ],
            'Affiliations': [
                (TGO.affiliation, 'Direct affiliations'),
                (TGO.memberOf, 'Group memberships'),
                (TGO.belongsTo, 'Belongs to'),
            ],
            'Locations': [
                (TGO.location, 'Lives in'),
                (TGO.birthlocation, 'Born in'),
                (TGO.deathlocation, 'Died in'),
                (TGO.hasConnectionTo, 'Connected to'),
            ]
        }
        
        for category, props in stats.items():
            print(f"\n{category}:")
            for prop, label in props:
                count = len(list(self.graph.triples((None, prop, None))))
                print(f"  {label:25} {count:4}")

def main():
    print('='*60)
    print("Tolkien Knowledge Graph - Reasoning Engine")
    print('='*60 + '\n')
    
    input_file = RDF_OUTPUT_FILE
    output_file = Path('output/tolkien_kg_reasoned.ttl')
    
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found: {input_file}")
        print("   Run 03_build_rdf.py first!")
        sys.exit(1)
    
    # Initialize reasoner
    reasoner = TolkienReasoner(input_file)
    
    # Apply reasoning steps
    reasoner.define_ontology()
    reasoner.infer_family_relationships()
    reasoner.infer_fellowship_membership()
    reasoner.infer_race_based_groups()
    reasoner.infer_locations_from_birth_death()
    reasoner.apply_rdfs_entailment()
    
    # Export and report
    reasoner.export_reasoned_graph(output_file)
    reasoner.generate_statistics()
    
    print(f"\n{'='*60}\n")
    print("✅ Reasoning complete!")
    print(f"\nNext steps:")
    print(f"  1. Reload into Fuseki: python src/05_load_fuseki.py")
    print(f"  2. Test SPARQL queries with inferred facts")
    print(f"  3. Build web interface (Steps 8-9)")

if __name__ == "__main__":
    main()
