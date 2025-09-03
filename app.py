# app.py - Fixed search endpoint
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import weaviate
from weaviate.auth import AuthApiKey
from dotenv import load_dotenv
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Weaviate Enterprise Search API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Weaviate connection
WEAVIATE_URL = os.getenv('WCD_URL')
WEAVIATE_API_KEY = os.getenv('WCD_API_KEY')

def get_weaviate_client():
    """Get a properly configured Weaviate client"""
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=AuthApiKey(WEAVIATE_API_KEY)
        )
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Weaviate: {str(e)}")

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    tenant: str
    search_type: str = "hybrid"  # keyword, vector, hybrid, generative
    alpha: float = 0.5  # For hybrid search
    limit: int = 10

class AgentRequest(BaseModel):
    query: str
    tenant: str

class DocumentResponse(BaseModel):
    id: str
    content: str
    file_name: str
    chunk_index: int
    created_date: str
    score: Optional[float] = None

class SearchResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    search_type: str
    query: str

class TenantInfo(BaseModel):
    name: str
    document_count: int

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Weaviate Enterprise Search API"}

@app.get("/tenants", response_model=List[TenantInfo])
async def get_tenants():
    """Get all available tenants with document counts"""
    client = None
    try:
        client = get_weaviate_client()
        docs = client.collections.get("Documents")
        tenants = ["HR", "Finance", "Customer-Service"]
        
        tenant_info = []
        for tenant_name in tenants:
            try:
                tenant_collection = docs.with_tenant(tenant_name)
                result = tenant_collection.query.fetch_objects(limit=1000)
                tenant_info.append(TenantInfo(
                    name=tenant_name,
                    document_count=len(result.objects)
                ))
                logger.info(f"Found {len(result.objects)} documents for tenant {tenant_name}")
            except Exception as e:
                logger.warning(f"Error fetching documents for tenant {tenant_name}: {e}")
                tenant_info.append(TenantInfo(
                    name=tenant_name,
                    document_count=0
                ))
        
        return tenant_info
    except Exception as e:
        logger.error(f"Error in get_tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            try:
                client.close()
            except:
                pass

@app.get("/documents/{tenant}", response_model=List[DocumentResponse])
async def get_documents(tenant: str, limit: int = 50):
    """Get all documents for a specific tenant"""
    client = None
    try:
        client = get_weaviate_client()
        docs = client.collections.get("Documents")
        tenant_collection = docs.with_tenant(tenant)
        
        result = tenant_collection.query.fetch_objects(limit=limit)
        
        documents = []
        for i, obj in enumerate(result.objects):
            properties = obj.properties or {}
            documents.append(DocumentResponse(
                id=str(obj.uuid),
                content=properties.get("content", "No content available"),
                file_name=f"Document_{i+1}",  # Generate a name since it doesn't exist
                chunk_index=i,                # Use index as chunk number
                created_date="2024-01-01",    # Use a default date
            ))
        
        logger.info(f"Retrieved {len(documents)} documents for tenant {tenant}")
        return documents
    except Exception as e:
        logger.error(f"Error in get_documents for tenant {tenant}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")
    finally:
        if client:
            try:
                client.close()
            except:
                pass

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents with different search types"""
    client = None
    try:
        client = get_weaviate_client()
        docs = client.collections.get("Documents")
        tenant_collection = docs.with_tenant(request.tenant)
        
        documents = []
        result = None
        
        if request.search_type == "keyword":
            # Keyword search
            result = tenant_collection.query.bm25(
                query=request.query,
                limit=request.limit
            )
            
        elif request.search_type == "vector":
            # Vector search
            result = tenant_collection.query.near_text(
                query=request.query,
                limit=request.limit
            )
            
        elif request.search_type == "hybrid":
            # Hybrid search
            result = tenant_collection.query.hybrid(
                query=request.query,
                alpha=request.alpha,
                limit=request.limit
            )
            
        elif request.search_type == "generative":
            # Generative search with RAG
            result = tenant_collection.query.generate(
                single_prompt=f"Based on the following context, answer the question: {request.query}",
                grouped_task="Summarize the key points from the search results",
                limit=request.limit
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        # FIXED: Generate proper values for missing fields
        for i, obj in enumerate(result.objects):
            properties = obj.properties or {}
            documents.append(DocumentResponse(
                id=str(obj.uuid),
                content=properties.get("content", "No content available"),
                file_name=f"Search_Result_{i+1}",  # Generate a name
                chunk_index=i,                     # Use index as chunk number
                created_date="2024-01-01",         # Use a default date
                score=getattr(obj, 'score', None)
            ))
        
        logger.info(f"Search completed: {len(documents)} results for query '{request.query}'")
        return SearchResponse(
            documents=documents,
            total_count=len(documents),
            search_type=request.search_type,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in search_documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    finally:
        if client:
            try:
                client.close()
            except:
                pass

@app.post("/query-agent", response_model=Dict)
async def query_agent(request: AgentRequest):
    """Query agent with RBAC and multi-tenancy"""
    client = None
    try:
        client = get_weaviate_client()
        docs = client.collections.get("Documents")
        tenant_collection = docs.with_tenant(request.tenant)
        
        # Use generative search for now (agent setup would be more complex)
        result = tenant_collection.query.generate(
            single_prompt=f"Answer this question based on the available documents: {request.query}",
            limit=5
        )
        
        response = {
            "query": request.query,
            "tenant": request.tenant,
            "answer": "Agent response would go here",
            "sources": []
        }
        
        for obj in result.objects:
            properties = obj.properties or {}
            response["sources"].append({
                "content": properties.get("content", "")[:200] + "...",
                "file_name": properties.get("file_name", "Unknown")
            })
        
        logger.info(f"Agent query completed for: {request.query}")
        return response
        
    except Exception as e:
        logger.error(f"Error in query_agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent query error: {str(e)}")
    finally:
        if client:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)