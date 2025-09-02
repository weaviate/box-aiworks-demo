import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.tenants import Tenant
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Weaviate Instance URL and API Key (replace with your own)
WEAVIATE_URL = os.getenv('WCD_URL')
WEAVIATE_API_KEY = os.getenv('WCD_API_KEY')

# authentication and connect to WCD

def init_clients(weaviate_url: str, weaviate_api_key: str):
    
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=AuthApiKey(WEAVIATE_API_KEY)
    )
    
    return weaviate_client

weaviate_client = init_clients(
    WEAVIATE_URL, WEAVIATE_API_KEY
)
print("Clients initialized successfully.")

multi_collection = weaviate_client.collections.get("Documents")

# Path to the parent folder that contains the 5 subfolders
parent_folder = "data"

# Iterate through each subfolder inside the parent folder
for subfolder in os.listdir(parent_folder):
    subfolder_path = os.path.join(parent_folder, subfolder)
    tenant_collcection = multi_collection.with_tenant(subfolder)

    if os.path.isdir(subfolder_path):  # only process folders
        print(f"\n=== Folder: {subfolder} ===")

        for item in os.listdir(subfolder_path):
            if item.endswith(".md"):  # only process Markdown files
                file_path = os.path.join(subfolder_path, item)

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                content = content.split()

                for i in range(0, len(content), 200):
                    chunk = " ".join(content[i:i + 200])
                    tenant_collcection.data.insert(
                        properties={
                            "content": chunk
                        }
                    )



