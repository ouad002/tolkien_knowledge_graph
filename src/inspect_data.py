#!/usr/bin/env python3
"""
Inspect fetched data to understand content structure
"""

import json
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config import *

def main():
    # Load parsed templates
    with open(PARSED_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data['pages']
    
    print("="*60)
    print("Data Inspection Report")
    print("="*60)
    
    # Show all page titles
    print(f"\nFetched {len(pages)} pages:")
    for i, page in enumerate(pages, 1):
        print(f"{i:3}. {page['title']:<40} ({page['template_count']} templates)")
    
    # Find pages with most templates
    print("\n" + "="*60)
    print("Pages with most templates:")
    print("="*60)
    sorted_pages = sorted(pages, key=lambda p: p['template_count'], reverse=True)
    for page in sorted_pages[:10]:
        print(f"\n{page['title']} ({page['template_count']} templates):")
        for template in page['all_templates'][:5]:
            print(f"  - {template['name']}")
            if template['params']:
                print(f"    Params: {list(template['params'].keys())[:5]}")
    
    # Load raw pages to check content
    print("\n" + "="*60)
    print("Sample page content (checking for infoboxes):")
    print("="*60)
    
    with open(RAW_PAGES_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    raw_pages = raw_data['pages']
    
    # Check first few pages for infobox patterns
    for page in raw_pages[:5]:
        print(f"\n{page['title']}:")
        text = page['text'][:500]  # First 500 chars
        
        # Check for common infobox patterns
        if 'infobox' in text.lower():
            print("  ✓ Contains 'infobox'")
        elif '{{' in text:
            # Find first template
            start = text.find('{{')
            end = text.find('}}', start)
            if end > start:
                template = text[start:end+2]
                print(f"  First template: {template[:100]}")
        else:
            print("  ✗ No templates found")
        
        print(f"  First 200 chars: {text[:200]}")

if __name__ == "__main__":
    main()
