import requests
import sys
import os

# Configuration
FUSEKI_URL = "http://localhost:3030"
DATASET_NAME = "tolkien"
RDF_FILE = "output/tolkien_kg_reasoned.ttl"  

def setup_fuseki():
    print(f"Checking Fuseki connection at {FUSEKI_URL}...")
    try:
        # 1. Create the dataset (TDB2 persistent storage)
        # dbType can be 'mem' for in-memory or 'tdb2' for persistent
        create_url = f"{FUSEKI_URL}/$/datasets"
        data = {'dbName': DATASET_NAME, 'dbType': 'tdb2'}
        
        response = requests.post(create_url, data=data)
        if response.status_code == 200:
            print(f"✓ Dataset '{DATASET_NAME}' created successfully.")
        elif response.status_code == 409:
            print(f"! Dataset '{DATASET_NAME}' already exists.")
        
        # 2. Upload the RDF data
        upload_url = f"{FUSEKI_URL}/{DATASET_NAME}/data"
        print(f"Uploading {RDF_FILE}...")
        
        with open(RDF_FILE, 'rb') as f:
            headers = {'Content-Type': 'text/turtle'}
            up_res = requests.post(upload_url, data=f, headers=headers)
            
        if up_res.status_code in [200, 201, 204]:
            print(f"✅ Successfully uploaded Knowledge Graph to Fuseki!")
        else:
            print(f"❌ Upload failed: {up_res.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Fuseki. Is the server running on port 3030?")

if __name__ == "__main__":
    setup_fuseki()
