#!/usr/bin/env python3
"""
SHACL Validation for Tolkien Knowledge Graph
Validates RDF data against SHACL shapes
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config import *

from rdflib import Graph
from pyshacl import validate
from pathlib import Path
import json
from datetime import datetime

class SHACLValidator:
    def __init__(self, data_graph_path, shapes_graph_path):
        """
        Initialize validator with data and shapes graphs
        
        Args:
            data_graph_path: Path to the RDF data to validate
            shapes_graph_path: Path to the SHACL shapes file
        """
        self.data_graph_path = data_graph_path
        self.shapes_graph_path = shapes_graph_path
        
        print("Loading graphs...")
        self.data_graph = Graph()
        self.data_graph.parse(data_graph_path, format='turtle')
        print(f"  ✓ Data graph: {len(self.data_graph)} triples")
        
        self.shapes_graph = Graph()
        self.shapes_graph.parse(shapes_graph_path, format='turtle')
        print(f"  ✓ Shapes graph: {len(self.shapes_graph)} triples")
    
    def validate(self, inference='rdfs'):
        """
        Run SHACL validation
        
        Args:
            inference: Type of inference to apply ('rdfs', 'owlrl', 'both', 'none')
        
        Returns:
            Tuple of (conforms, results_graph, results_text)
        """
        print(f"\nRunning SHACL validation with {inference} inference...")
        
        conforms, results_graph, results_text = validate(
            self.data_graph,
            shacl_graph=self.shapes_graph,
            inference=inference,
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            js=False
        )
        
        return conforms, results_graph, results_text
    
    def analyze_results(self, conforms, results_graph, results_text):
        """
        Parse and analyze validation results
        
        Returns:
            Dictionary with analysis statistics
        """
        if conforms:
            return {
                'conforms': True,
                'violations': 0,
                'warnings': 0,
                'infos': 0,
                'total_issues': 0
            }
        
        # Parse results text to count issues by severity
        lines = results_text.split('\n')
        
        violations = []
        warnings = []
        infos = []
        
        current_issue = None
        
        for line in lines:
            if line.strip().startswith('Constraint Violation'):
                current_issue = {'type': 'violation', 'details': []}
                violations.append(current_issue)
            elif line.strip().startswith('Constraint Warning'):
                current_issue = {'type': 'warning', 'details': []}
                warnings.append(current_issue)
            elif line.strip().startswith('Constraint Info'):
                current_issue = {'type': 'info', 'details': []}
                infos.append(current_issue)
            elif current_issue and line.strip():
                current_issue['details'].append(line.strip())
        
        return {
            'conforms': False,
            'violations': len(violations),
            'warnings': len(warnings),
            'infos': len(infos),
            'total_issues': len(violations) + len(warnings) + len(infos),
            'violation_details': violations[:10],  # First 10
            'warning_details': warnings[:10]
        }
    
    def generate_report(self, analysis, output_dir='output'):
        """
        Generate validation report
        """
        os.makedirs(output_dir, exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_file': str(self.data_graph_path),
            'shapes_file': str(self.shapes_graph_path),
            'data_triples': len(self.data_graph),
            'shapes_triples': len(self.shapes_graph),
            'validation': analysis
        }
        
        # Save JSON report
        report_path = Path(output_dir) / 'shacl_validation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report_path

def print_summary(analysis):
    """Print human-readable summary"""
    print("\n" + "="*60)
    print("SHACL VALIDATION SUMMARY")
    print("="*60)
    
    if analysis['conforms']:
        print("\n✅ VALIDATION PASSED - All constraints satisfied!")
    else:
        print("\n⚠️  VALIDATION FAILED")
        print(f"\n  Violations (must fix):  {analysis['violations']}")
        print(f"  Warnings (should fix):  {analysis['warnings']}")
        print(f"  Info (optional):        {analysis['infos']}")
        print(f"  Total issues:           {analysis['total_issues']}")
        
        if analysis.get('violation_details'):
            print("\n" + "-"*60)
            print("Sample Violations (first 5):")
            print("-"*60)
            for i, violation in enumerate(analysis['violation_details'][:5], 1):
                print(f"\n{i}. ", end='')
                for line in violation['details'][:3]:  # First 3 lines per violation
                    print(f"   {line}")
        
        if analysis.get('warning_details'):
            print("\n" + "-"*60)
            print("Sample Warnings (first 3):")
            print("-"*60)
            for i, warning in enumerate(analysis['warning_details'][:3], 1):
                print(f"\n{i}. ", end='')
                for line in warning['details'][:3]:
                    print(f"   {line}")

def main():
    print("="*60)
    print("Tolkien Knowledge Graph - SHACL Validation")
    print("="*60)
    
    # Paths
    data_path = RDF_OUTPUT_FILE
    shapes_path = Path('shapes/tolkien_shapes.ttl')
    
    # Check if files exist
    if not os.path.exists(data_path):
        print(f"\n❌ Error: Data file not found: {data_path}")
        print("   Run 03_build_rdf.py first!")
        sys.exit(1)
    
    if not os.path.exists(shapes_path):
        print(f"\n❌ Error: Shapes file not found: {shapes_path}")
        print("   Create the shapes file first!")
        sys.exit(1)
    
    # Initialize validator
    validator = SHACLValidator(data_path, shapes_path)
    
    # Run validation
    conforms, results_graph, results_text = validator.validate(inference='rdfs')
    
    # Analyze results
    analysis = validator.analyze_results(conforms, results_graph, results_text)
    
    # Generate report
    report_path = validator.generate_report(analysis)
    print(f"\n✓ Detailed report saved to: {report_path}")
    
    # Print summary
    print_summary(analysis)
    
    # Save detailed results
    if not conforms:
        results_path = Path('output/shacl_validation_details.txt')
        with open(results_path, 'w', encoding='utf-8') as f:
            f.write(results_text)
        print(f"\n✓ Full validation details saved to: {results_path}")
    
    print("\n" + "="*60)
    
    # Exit code
    sys.exit(0 if conforms else 1)

if __name__ == "__main__":
    main()
