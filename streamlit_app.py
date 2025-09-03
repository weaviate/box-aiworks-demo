# streamlit_app.py - Fixed search logic for both methods
import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time

# Page configuration
st.set_page_config(
    page_title="Weaviate Enterprise Search",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = "http://localhost:8000"

# Fixed CSS with white headers and dark document text
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tenant-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s;
        margin: 1rem 0;
    }
    .tenant-card:hover {
        transform: translateY(-5px);
    }
    .search-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
    }
    .document-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        color: #000000 !important;
    }
    .document-card h4 {
        color: #1a1a1a !important;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .document-card p {
        color: #2d2d2d !important;
        line-height: 1.6;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    .document-card small {
        color: #4a4a4a !important;
        font-size: 0.9rem;
    }
    .document-card strong {
        color: #1a1a1a !important;
        font-weight: bold;
    }
    .search-type-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.25rem;
    }
    .keyword { background: #e3f2fd; color: #1976d2; }
    .vector { background: #f3e5f5; color: #7b1fa2; }
    .hybrid { background: #e8f5e8; color: #388e3c; }
    .generative { background: #fff3e0; color: #f57c00; }
    
    /* Force all text in document cards to be dark */
    .document-card * {
        color: #2d2d2d !important;
    }
    
    /* Make Streamlit headers white */
    .stApp h1, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: white !important;
    }
    
    /* Make sidebar headers white */
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6 {
        color: white !important;
    }
    
    /* Override any Streamlit default colors for headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: white !important;
    }
    
    /* Keep document card text dark */
    .document-card h1, .document-card h2, .document-card h3, .document-card h4, .document-card h5, .document-card h6 {
        color: #1a1a1a !important;
    }
    
    /* Ensure markdown content in document cards is dark */
    .stMarkdown p {
        color: #2d2d2d !important;
    }
</style>
""", unsafe_allow_html=True)

def fetch_tenants() -> List[Dict]:
    """Fetch all tenants from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/tenants")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def fetch_documents(tenant: str) -> List[Dict]:
    """Fetch documents for a specific tenant"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{tenant}")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def search_documents(query: str, tenant: str, search_type: str, alpha: float = 0.5) -> Dict:
    """Search documents using different search types"""
    try:
        payload = {
            "query": query,
            "tenant": tenant,
            "search_type": search_type,
            "alpha": alpha,
            "limit": 20
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload)
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return {}

def filter_documents_locally(documents: List[Dict], filter_text: str) -> List[Dict]:
    """Filter documents locally based on content"""
    if not filter_text:
        return documents
    
    filter_text = filter_text.lower()
    filtered = []
    
    for doc in documents:
        # Search in content, file_name, and other fields
        content = doc.get('content', '').lower()
        file_name = doc.get('file_name', '').lower()
        
        if filter_text in content or filter_text in file_name:
            filtered.append(doc)
    
    return filtered

def query_agent(query: str, tenant: str) -> Dict:
    """Query the agent"""
    try:
        payload = {"query": query, "tenant": tenant}
        response = requests.post(f"{API_BASE_URL}/query-agent", json=payload)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🔍 Weaviate Enterprise Search</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Advanced Search & AI-Powered Document Discovery</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_tenant' not in st.session_state:
        st.session_state.selected_tenant = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'all_documents' not in st.session_state:
        st.session_state.all_documents = []
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "documents"  # "documents", "search", "agent"
    
    # Sidebar for search controls
    with st.sidebar:
        st.header(" Search Controls")
        
        # Search type selection
        search_type = st.selectbox(
            "Search Type",
            ["hybrid", "keyword", "vector", "generative"],
            help="Choose the type of search to perform"
        )
        
        # Alpha parameter for hybrid search
        if search_type == "hybrid":
            alpha = st.slider(
                "Alpha Parameter",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="0.0 = pure keyword search, 1.0 = pure vector search"
            )
        else:
            alpha = 0.5
        
        # Search query
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            help="Type your search query here"
        )
        
        # Search button
        if st.button("🔍 Search", type="primary"):
            if search_query and st.session_state.selected_tenant:
                with st.spinner("Searching..."):
                    results = search_documents(
                        search_query, 
                        st.session_state.selected_tenant, 
                        search_type, 
                        alpha
                    )
                    if results and results.get('documents'):
                        st.session_state.search_results = results
                        st.session_state.current_view = "search"
                        st.success(f"Found {len(results['documents'])} results!")
                    else:
                        st.warning("No results found. Try a different query.")
            else:
                st.warning("Please select a department and enter a search query.")
        
        # Clear search button
        if st.button("🗑️ Clear Search"):
            st.session_state.search_results = None
            st.session_state.current_view = "documents"
            st.rerun()
        
        # Agent query section
        st.header(" AI Agent")
        agent_query = st.text_input(
            "Agent Query",
            placeholder="Ask a complex question...",
            help="Use the AI agent for complex queries"
        )
        
        if st.button("🤖 Query Agent"):
            if agent_query and st.session_state.selected_tenant:
                with st.spinner("Agent is thinking..."):
                    agent_response = query_agent(agent_query, st.session_state.selected_tenant)
                    if agent_response:
                        st.session_state.agent_response = agent_response
                        st.session_state.current_view = "agent"
                        st.success("Agent response generated!")
                    else:
                        st.error("Agent query failed. Please try again.")
            else:
                st.warning("Please select a department and enter a query.")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tenant selection
        st.header("📁 Select Department")
        
        tenants = fetch_tenants()
        if tenants:
            cols = st.columns(len(tenants))
            for i, tenant in enumerate(tenants):
                with cols[i]:
                    if st.button(
                        f"**{tenant['name']}**\n\n📄 {tenant['document_count']} documents",
                        key=f"tenant_{tenant['name']}",
                        help=f"Click to view {tenant['name']} documents"
                    ):
                        st.session_state.selected_tenant = tenant['name']
                        st.session_state.search_results = None
                        st.session_state.current_view = "documents"
                        st.session_state.all_documents = fetch_documents(tenant['name'])
                        st.rerun()
        else:
            st.error("Unable to fetch tenants. Please check your API connection.")
    
    with col2:
        # Current selection info
        if st.session_state.selected_tenant:
            st.success(f"✅ Selected: **{st.session_state.selected_tenant}**")
            
            # Show documents count
            documents = st.session_state.all_documents
            st.metric("Total Documents", len(documents))
            
            # Show current view
            view_icons = {
                "documents": "📄",
                "search": "🔍", 
                "agent": "🤖"
            }
            st.info(f"{view_icons.get(st.session_state.current_view, '📄')} Viewing: {st.session_state.current_view.title()}")
        else:
            st.info("👈 Select a department to get started")
    
    # Display content based on current view
    if st.session_state.selected_tenant:
        # Search results view
        if st.session_state.current_view == "search" and st.session_state.search_results:
            st.header("🔍 Search Results")
            
            # Search type badge
            search_type_badge = f'<span class="search-type-badge {st.session_state.search_results["search_type"]}">{st.session_state.search_results["search_type"].upper()}</span>'
            st.markdown(f"Search Type: {search_type_badge}", unsafe_allow_html=True)
            st.markdown(f"Query: **{st.session_state.search_results['query']}**")
            st.markdown(f"Found: **{st.session_state.search_results['total_count']}** results")
            
            # Display results
            for doc in st.session_state.search_results['documents']:
                with st.container():
                    st.markdown(f"""
                    <div class="document-card">
                        <h4> {doc['file_name']} (Chunk {doc['chunk_index']})</h4>
                        <p><strong>Content:</strong> {doc['content'][:300]}...</p>
                        <small>ID: {doc['id'][:8]}... | Date: {doc['created_date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Agent response view
        elif st.session_state.current_view == "agent" and hasattr(st.session_state, 'agent_response') and st.session_state.agent_response:
            st.header("🤖 Agent Response")
            agent_resp = st.session_state.agent_response
            
            st.markdown(f"**Query:** {agent_resp['query']}")
            st.markdown(f"**Answer:** {agent_resp.get('answer', 'No answer available')}")
            
            if agent_resp.get('sources'):
                st.subheader("📚 Sources")
                for source in agent_resp['sources']:
                    st.markdown(f"**{source['file_name']}:** {source['content']}")
        
        # Default document view with filtering
        else:
            st.header(f"📄 {st.session_state.selected_tenant} Documents")
            
            # Add a filter input
            filter_text = st.text_input(
                "🔍 Filter Documents",
                placeholder="Type to filter documents by content...",
                help="Filter documents by typing keywords"
            )
            
            documents = st.session_state.all_documents
            if documents:
                # Apply local filtering
                filtered_documents = filter_documents_locally(documents, filter_text)
                
                # Show filter results
                if filter_text:
                    st.info(f"Showing {len(filtered_documents)} of {len(documents)} documents matching '{filter_text}'")
                
                # Display filtered documents
                for doc in filtered_documents[:10]:  # Show first 10 documents
                    with st.container():
                        st.markdown(f"""
                        <div class="document-card">
                            <h4> {doc['file_name']} (Chunk {doc['chunk_index']})</h4>
                            <p><strong>Content:</strong> {doc['content'][:300]}...</p>
                            <small>ID: {doc['id'][:8]}... | Date: {doc['created_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                if len(filtered_documents) > 10:
                    st.info(f"Showing first 10 of {len(filtered_documents)} filtered documents.")
            else:
                st.warning("No documents found for this tenant.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p> Powered by <strong>Weaviate</strong> | Built with <strong>FastAPI</strong> & <strong>Streamlit</strong></p>
        <p>Features: Keyword Search | Vector Search | Hybrid Search | Generative AI | Query Agent</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
