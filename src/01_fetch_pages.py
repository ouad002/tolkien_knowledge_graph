#!/usr/bin/env python3
"""
Step 1-3: Fetch all pages from Tolkien Gateway using MediaWiki API
Outputs: data/tolkien_pages.json
"""

import requests
import json
import time
from tqdm import tqdm
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import *

# MAIN TOLKIEN ENTITIES - These definitely have character/location templates
MAIN_ENTITIES = [
    # Major characters from books
    'Gandalf', 'Frodo Baggins', 'Aragorn II', 'Legolas', 'Gimli',
    'Bilbo Baggins', 'Samwise Gamgee', 'Meriadoc Brandybuck', 'Peregrin Took',
    'Boromir', 'Faramir', 'Galadriel', 'Elrond', 'Arwen',
    'Sauron', 'Saruman', 'Gollum', 'Théoden', 'Éowyn', 'Éomer',
    
    # More characters
    'Thorin', 'Denethor II', 'Celeborn', 'Haldir', 'Treebeard',
    'Tom Bombadil', 'Goldberry', 'Glorfindel', 'Beregond',
    
    # Villains/creatures  
    'Witch-king', 'Shelob', 'Gothmog', 'Lurtz', 'Azog',
    
    # Major locations
    'Rivendell', 'Lothlórien', 'Minas Tirith', 'Edoras', 'Isengard',
    'Mordor', 'Mount Doom', 'The Shire', 'Bag End', 'Moria',
    'Helm''s Deep', 'Fangorn', 'Weathertop', 'Mirkwood', 'Erebor',
    
    # Realms/regions
    'Gondor', 'Rohan', 'Arnor', 'Eriador', 'Rhovanion',
    
    # More locations
    'Bree', 'Orthanc', 'Barad-dûr', 'Osgiliath', 'Pelennor Fields',
    'Argonath', 'Cirith Ungol', 'Dead Marshes', 'Emyn Muil'
]

class TolkienAPI:
    def __init__(self):
        self.base_url = "https://tolkiengateway.net/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TolkienKG-Academic/1.0 (Mines-Saint-Etienne)',
        })
    
    def parse_page(self, title):
        """Parse a page using action=parse"""
        params = {
            'action': 'parse',
            'page': title,
            'prop': 'wikitext|categories|links',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'parse' not in data:
                return None
            
            parse_data = data['parse']
            wikitext = parse_data.get('wikitext', {}).get('*', '')
            
            categories = []
            if 'categories' in parse_data:
                categories = [cat['*'] for cat in parse_data['categories']]
            
            links = []
            if 'links' in parse_data:
                links = [link['*'] for link in parse_data['links'] if link.get('ns') == 0]
            
            images = []
            if 'images' in parse_data:
                images = parse_data['images']
            
            return {
                'title': parse_data.get('title', title),
                'pageid': parse_data.get('pageid', 0),
                'text': wikitext,
                'categories': categories,
                'links': links[:100],
                'images': images[:20],
                'length': len(wikitext),
                'namespace': 0
            }
            
        except Exception as e:
            print(f"\nError fetching {title}: {e}")
            return None

def main():
    print("="*60)
    print("Tolkien Main Entities Fetcher")
    print("="*60)
    print(f"\nFetching {len(MAIN_ENTITIES)} main character/location pages...")
    
    api = TolkienAPI()
    
    pages_data = []
    failed = []
    
    for title in tqdm(MAIN_ENTITIES, desc="Downloading"):
        page = api.parse_page(title)
        
        if page and page['length'] > 100:  # Skip redirects/empty pages
            pages_data.append(page)
        else:
            failed.append(title)
        
        time.sleep(0.5)  # Be respectful
    
    print(f"\n✓ Successfully fetched {len(pages_data)} pages")
    
    if failed:
        print(f"⚠ Failed/redirected ({len(failed)} pages):")
        for title in failed[:10]:
            print(f"  - {title}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    
    output_data = {
        'metadata': {
            'source': 'Main entities from tolkiengateway.net',
            'total_pages': len(pages_data),
            'method': 'action=parse',
            'target': 'Characters and Locations'
        },
        'pages': pages_data
    }
    
    with open(RAW_PAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to {RAW_PAGES_FILE}")
    
    # Quick analysis
    with_infobox = sum(1 for p in pages_data if 
                       '{{infobox' in p['text'].lower() or 
                       '{{character' in p['text'].lower() or
                       '{{location' in p['text'].lower())
    
    print(f"\nQuick check:")
    print(f"  Pages with infobox-like templates: {with_infobox}")
    print(f"  Average page length: {sum(p['length'] for p in pages_data) // len(pages_data):,} chars")
    
    # Show first template from sample pages
    print(f"\nSample templates found:")
    for page in pages_data[:5]:
        text = page['text'][:300]
        if '{{' in text:
            template_start = text.find('{{')
            template_end = text.find('}}', template_start)
            if template_end > template_start:
                template = text[template_start:template_end+2]
                print(f"  {page['title'][:30]:<30} → {template[:60]}...")

if __name__ == "__main__":
    main()
