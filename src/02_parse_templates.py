#!/usr/bin/env python3
"""
Step 4: Parse wikitext templates using mwparserfromhell
Outputs: data/parsed_templates.json
"""

import json
import mwparserfromhell
from collections import Counter
from tqdm import tqdm
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config import *

def load_pages(filepath):
    """Load pages from JSON file"""
    print(f"Loading pages from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded {data['metadata']['total_pages']} pages")
    return data['pages']

def extract_templates(page_text):
    """
    Extract all templates from wikitext
    
    Returns:
        List of dictionaries with template data
    """
    try:
        wikicode = mwparserfromhell.parse(page_text)
        templates_data = []
        
        for template in wikicode.filter_templates():
            template_name = str(template.name).strip().lower()
            
            # Extract all parameters
            params = {}
            for param in template.params:
                param_name = str(param.name).strip()
                param_value = str(param.value).strip()
                
                # Skip empty values
                if param_value:
                    params[param_name] = param_value
            
            templates_data.append({
                'name': template_name,
                'params': params
            })
        
        return templates_data
    
    except Exception as e:
        print(f"Error parsing wikitext: {e}")
        return []

def extract_infoboxes(templates):
    """
    Filter for structured data templates (infoboxes and similar)
    Tolkien Gateway uses various template names, not just 'infobox'
    """
    # Known structured data templates on Tolkien Gateway
    STRUCTURED_TEMPLATES = [
        'infobox', 'character', 'location', 'book', 'person',
        'events', 'scene', 'song', 'item', 'language',
        'organization', 'weapon', 'race', 'game'
    ]
    
    structured = []
    for template in templates:
        template_name = template['name'].lower().strip()
        
        # Check if it's a structured data template
        for known_type in STRUCTURED_TEMPLATES:
            if known_type in template_name or template_name.startswith(known_type):
                structured.append(template)
                break
    
    return structured


def extract_wikilinks(page_text):
    """Extract all [[wikilinks]] from text"""
    try:
        wikicode = mwparserfromhell.parse(page_text)
        links = []
        
        for wikilink in wikicode.filter_wikilinks():
            title = str(wikilink.title).strip()
            text = str(wikilink.text).strip() if wikilink.text else title
            links.append({
                'target': title,
                'display_text': text
            })
        
        return links
    except Exception as e:
        return []

def process_all_pages(pages):
    """Process all pages and extract template data"""
    processed_data = []
    template_counter = Counter()
    
    print("\nParsing wikitext templates...")
    
    for page in tqdm(pages, desc="Processing pages"):
        # Extract templates
        templates = extract_templates(page['text'])
        infoboxes = extract_infoboxes(templates)
        wikilinks = extract_wikilinks(page['text'])
        
        # Count template types
        for template in templates:
            template_counter[template['name']] += 1
        
        page_data = {
            'title': page['title'],
            'pageid': page['pageid'],
            'all_templates': templates,
            'infoboxes': infoboxes,
            'wikilinks': wikilinks,
            'template_count': len(templates),
            'infobox_count': len(infoboxes),
            'link_count': len(wikilinks)
        }
        
        processed_data.append(page_data)
    
    return processed_data, template_counter

def analyze_templates(template_counter):
    """Print analysis of template usage"""
    print("\n" + "="*60)
    print("Template Analysis")
    print("="*60)
    
    print(f"\nTotal unique templates: {len(template_counter)}")
    print(f"Total template uses: {sum(template_counter.values())}")
    
    print("\nTop 20 most used templates:")
    for template, count in template_counter.most_common(20):
        print(f"  {template:<40} {count:>6} uses")
    
    # Infobox templates specifically
    infobox_templates = {k: v for k, v in template_counter.items() if k.startswith('infobox')}
    print(f"\nInfobox templates found: {len(infobox_templates)}")
    print("\nAll infobox types:")
    for template, count in sorted(infobox_templates.items(), key=lambda x: -x[1]):
        print(f"  {template:<40} {count:>6} uses")

def main():
    """Main execution function"""
    print("="*60)
    print("Tolkien Gateway Template Parser")
    print("="*60)
    
    # Load pages
    pages = load_pages(RAW_PAGES_FILE)
    
    # Process pages
    processed_data, template_counter = process_all_pages(pages)
    
    # Save results
    output_data = {
        'metadata': {
            'total_pages': len(processed_data),
            'pages_with_infoboxes': sum(1 for p in processed_data if p['infoboxes']),
            'total_templates': sum(p['template_count'] for p in processed_data),
            'total_infoboxes': sum(p['infobox_count'] for p in processed_data)
        },
        'pages': processed_data
    }
    
    with open(PARSED_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved parsed templates to {PARSED_TEMPLATES_FILE}")
    
    # Analysis
    analyze_templates(template_counter)
    
    # Show examples
    print("\n" + "="*60)
    print("Example: Pages with infoboxes")
    print("="*60)
    for page in processed_data[:10]:
        if page['infoboxes']:
            print(f"\n{page['title']}:")
            for infobox in page['infoboxes']:
                print(f"  Type: {infobox['name']}")
                print(f"  Parameters: {len(infobox['params'])}")
                # Show first 3 parameters
                for i, (k, v) in enumerate(list(infobox['params'].items())[:3]):
                    print(f"    {k}: {v[:50]}...")
                if len(infobox['params']) > 3:
                    print(f"    ... and {len(infobox['params']) - 3} more")

if __name__ == "__main__":
    main()
