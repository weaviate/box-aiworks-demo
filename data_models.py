from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentResponse:
    def __init__(self, id: str, content: str, file_name: str, 
                 chunk_index: int, created_date: str, score: Optional[float] = None):
        self.id = id
        self.content = content
        self.file_name = file_name
        self.chunk_index = chunk_index
        self.created_date = created_date
        self.score = score

class TenantInfo:
    def __init__(self, name: str, document_count: int):
        self.name = name
        self.document_count = document_count

class SearchResponse:
    def __init__(self, documents: List[Dict], total_count: int, 
                 search_type: str, query: str):
        self.documents = documents
        self.total_count = total_count
        self.search_type = search_type
        self.query = query
