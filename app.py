
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.config import Configure
from weaviate.classes.generate import GenerativeConfig

from dotenv import load_dotenv
import os
from datetime import datetime
import logging


try:
    from weaviate.agents.query import QueryAgent
    from weaviate.agents.classes import QueryAgentCollectionConfig
except ImportError:
    from weaviate_agents.query import QueryAgent
    from weaviate_agents.classes import QueryAgentCollectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Weaviate Enterprise Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEAVIATE_URL = os.getenv('WCD_URL')
WEAVIATE_API_KEY = os.getenv('WCD_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_APIKEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

from connect_and_collection import weaviate_client

def get_anthropic_generative_config():
    return GenerativeConfig.anthropic(
        model="claude-3-opus-20240229",
        max_tokens=256,
        temperature=0.7,
    )

class SearchRequest(BaseModel):
    query: str
    tenant: str
    search_type: str = "hybrid"
    alpha: float = 0.5
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

@app.get("/")
async def root():
    return {"message": "Weaviate Enterprise Search API"}

@app.get("/tenants", response_model=List[TenantInfo])
async def get_tenants():
    client = None
    try:
        client = weaviate_client
        docs = client.collections.get("BoxDocuments")
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
    client = None
    try:
        client = weaviate_client
        docs = client.collections.get("BoxDocuments")
        tenant_collection = docs.with_tenant(tenant)
        
        result = tenant_collection.query.fetch_objects(limit=limit)
        
        documents = []
        for i, obj in enumerate(result.objects):
            properties = obj.properties or {}
            documents.append(DocumentResponse(
                id=str(obj.uuid),
                content=properties.get("content", "No content available"),
                file_name=f"Document_{i+1}",
                chunk_index=i,
                created_date="2024-01-01",
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
    client = None
    try:
        client = weaviate_client
        docs = client.collections.get("BoxDocuments")
        tenant_collection = docs.with_tenant(request.tenant)
        
        documents = []
        result = None
        
        if request.search_type == "keyword":
            result = tenant_collection.query.bm25(
                query=request.query,
                limit=request.limit
            )
            
        elif request.search_type == "vector":
            result = tenant_collection.query.near_text(
                query=request.query,
                limit=request.limit
            )
            
        elif request.search_type == "hybrid":
            result = tenant_collection.query.hybrid(
                query=request.query,
                alpha=request.alpha,
                limit=request.limit
            )
            
        elif request.search_type == "generative":
            gen_config = get_anthropic_generative_config()
            
            result = tenant_collection.generate.near_text(
                query=request.query,
                limit=request.limit,
                single_prompt=f"Based on the following context, answer the question: {request.query}",
                grouped_task="Summarize the key points from the search results",
                generative_provider=gen_config
            )
            
            if hasattr(result, 'generated') and result.generated:
                generated_text = result.generated
                documents = [DocumentResponse(
                    id="generated_response",
                    content=generated_text,
                    file_name="AI Generated Response",
                    chunk_index=0,
                    created_date=datetime.now().strftime("%Y-%m-%d"),
                    score=1.0
                )]
            else:
                documents = [DocumentResponse(
                    id="no_response",
                    content="No response generated",
                    file_name="No Response",
                    chunk_index=0,
                    created_date=datetime.now().strftime("%Y-%m-%d"),
                    score=0.0
                )]
            
            logger.info(f"Generative search completed: Generated response only")
            return SearchResponse(
                documents=documents,
                total_count=len(documents),
                search_type=request.search_type,
                query=request.query
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        for i, obj in enumerate(result.objects):
            properties = obj.properties or {}
            documents.append(DocumentResponse(
                id=str(obj.uuid),
                content=properties.get("content", "No content available"),
                file_name=f"Search_Result_{i+1}",
                chunk_index=i,
                created_date="2024-01-01",
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
    client = None
    try:
        client = weaviate_client

        collection_name = "Documents"

        agent = QueryAgent(client=client)

        
        cfg = QueryAgentCollectionConfig(
            name=collection_name,
            tenant=request.tenant,
            view_properties=["content", "file_name", "created_date"]
        )

        response = agent.run(
            request.query,
            collections=[cfg]
        )

        # Hydrate sources using existing props only
        hydrated_sources = []
        try:
            for src in response.sources[:10]:
                # QueryAgent can touch multiple collections; re-scope per source
                coll = client.collections.get(src.collection).with_tenant(request.tenant)
                obj = coll.query.fetch_object_by_id(src.object_id)
                props = obj.properties or {}
                hydrated_sources.append({
                    "collection": src.collection,
                    "id": src.object_id,
                    "content": (props.get("content") or "")[:500],
                    "file_name": props.get("file_name"),
                    "created_date": props.get("created_date"),
                    "chunk_index": props.get("chunk_index"),
                    "file_id": props.get("file_id"),
                })
        except Exception as hydrate_err:
            logger.warning(f"Source hydration failed: {hydrate_err}")

        result = {
            "query": request.query,
            "tenant": request.tenant,
            "answer": response.final_answer,
            "collections": getattr(response, "collection_names", None),
            "usage": {
                "requests": getattr(getattr(response, "usage", None), "requests", None),
                "request_tokens": getattr(getattr(response, "usage", None), "request_tokens", None),
                "response_tokens": getattr(getattr(response, "usage", None), "response_tokens", None),
                "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", None),
                "total_time_sec": getattr(response, "total_time", None),
            },
            "searches": [
                {"collection": q.collection, "queries": q.queries}
                for group in getattr(response, "searches", []) for q in group
            ],
            "aggregations": [
                {"collection": a.collection, "search_query": a.search_query}
                for group in getattr(response, "aggregations", []) for a in group
            ],
            "sources": hydrated_sources,
        }

        logger.info(f"Query Agent completed for: {request.query} (tenant={request.tenant})")
        return result

    except Exception as e:
        logger.error(f"Error in query_agent: {e}")
        raise HTTPException(status_code=500, detail=f"Query Agent error: {str(e)}")
    finally:
        if client:
            try:
                client.close()
            except:
                pass        
            
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)