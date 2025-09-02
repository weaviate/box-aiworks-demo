import weaviate
from weaviate.auth import AuthApiKey
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Weaviate Instance URL and API Key (replace with your own)
WEAVIATE_URL = os.getenv('WCD_URL')
WEAVIATE_API_KEY = os.getenv('WCD_API_KEY')

# authentication and connect to WCD

def init_clients( weaviate_url: str, weaviate_api_key: str):
    
    # Initialize Weaviate Client with Cohere for vectorization
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=AuthApiKey(WEAVIATE_API_KEY)
    )
    
    return weaviate_client

weaviate_client = init_clients(
    WEAVIATE_URL, WEAVIATE_API_KEY
)
print("Clients initialized successfully.")

# create collection

from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.tenants import Tenant

if not weaviate_client.collections.exists("Documents"):
    weaviate_client.collections.create(
        name="Documents",
        multi_tenancy_config=Configure.multi_tenancy(enabled=True),
        
        generative_config=Configure.Generative.cohere(),
        properties=[
            Property(name="file_id", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="file_name", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="chunk_index", data_type=DataType.INT, skip_vectorization=True),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="created_date", data_type=DataType.TEXT, skip_vectorization=True),
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_weaviate()
    )
    print("Schema 'Documents' created successfully.")
else:
    print("Schema 'Documents' already exists.")

docs = weaviate_client.collections.get("Documents")

docs.tenants.create([
    Tenant(name="HR"),
    Tenant(name="Finance"),
    Tenant(name="Customer-Service")
])

print("Tenants created successfully.")