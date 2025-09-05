
import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time
import os
from dotenv import load_dotenv


import streamlit as st
from search_functions import (
    fetch_tenants, fetch_documents, search_documents, 
    query_agent, filter_documents_locally
)
from connect_and_collection import weaviate_client
from config import APP_TITLE, APP_ICON

import base64
from pathlib import Path

def _b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

# Load environment variables from .env file
load_dotenv()

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API URL from environment variable or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.markdown("""
<style>
  :root{
    --brand-1:#667eea;
    --brand-2:#764ba2;
    --ink:#111827;
    --sub:#6b7280;
    --card:#ffffff;
    --card-border:#e5e7eb;
    --chip:#eef2ff;
  }

  /* App background */
  [data-testid="stAppViewContainer"] {
      background-image: url("https://images.unsplash.com/photo-1554629947-334ff61d85dc?q=80&w=1336&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3Dd");
      background-size: cover;
      background-repeat: no-repeat;
      background-position: center;
  }
            
/* Make the Streamlit header bar transparent */
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0) !important;
}


/* Logos in the existing white band at the top (no background) */
.top-logos {
  position: fixed;
  top: 8px;                   /* vertical offset */
  left: 0;                    /* span full width */
  width: 100%;                /* take the whole width */
  display: flex;
  justify-content: center;    /* center horizontally */
  align-items: center;
  gap: 36px;
  z-index: 1000;
  background: transparent;
}

/* Sidebar logos */
[data-testid="stSidebar"] .sidebar-logos{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:20px;
  padding:12px 0 18px;
}

[data-testid="stSidebar"] .sidebar-logos img{
  height:32px;     /* adjust size */
  display:block;
}


.top-logos img {
  height: 36px;  
}


  /* Sidebar */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #9dbce2 0%, #5a7ebd 50%, #344e8a 100%) !important;
    color: #f1f5f9 !important;
}
            
    /* Sidebar headings (st.header, st.subheader, etc.) */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: #f8fafc !important;  /* near-white */
    }

    /* Sidebar labels (for selectboxes, text inputs, sliders, etc.) */
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;  /* light gray */
        font-weight: 600;
    }
    
/* Sidebar buttons with sunset pink gradient */
[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #f8b6c1, #f18ca9, #e16385) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    cursor: pointer;
    transition: opacity 0.2s ease-in-out;
}

/* Hover effect */
[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    opacity: 0.9 !important;
}

/* Disabled state */
[data-testid="stSidebar"] div[data-testid="stButton"] > button:disabled {
    background: #f8b6c1 !important;
    color: #ffffff !important;
    cursor: not-allowed;
}   

  /* Main title */
  .main-header{
    font-size:3rem;
    font-weight:800;
    line-height:1.1;
    text-align:center;
    margin:0 0 .5rem 0;
    color:var(--ink) !important;
    background:none !important;
    -webkit-background-clip:unset !important;
    -webkit-text-fill-color:initial !important;
  }

  /* Subheading */
  .subheader{
    text-align:center;
    font-size:1.125rem;
    color:var(--sub);
    margin-bottom:1.25rem;
  }

  /* Tenant cards */
  .tenant-card,
  .tenant-btn{
    display:block;
    width:100%;
    text-align:center;
    padding:1rem;
    border-radius:14px;
    border:1px solid var(--card-border);
    background:linear-gradient(135deg, var(--brand-1) 0%, var(--brand-2) 100%);
    color:white;
    box-shadow:0 2px 8px rgba(0,0,0,.04);
    cursor:pointer;
  }
  .tenant-card:hover,
  .tenant-btn:hover{
    transform:translateY(-3px);
    transition:transform .15s ease;
  }

  /* Document card */
  .document-card{
    background:var(--card);
    padding:1.25rem;
    border-radius:12px;
    border:1px solid var(--card-border);
    box-shadow:0 2px 8px rgba(0,0,0,.04);
    margin:.75rem 0;
  }
  .document-card h4{margin:0 0 .5rem;font-size:1.05rem;color:var(--ink)}
  .document-card p{margin:.25rem 0;color:#1f2937}
  .document-card small{color:#6b7280}
  .document-card strong{color:var(--ink)}

  /* Search type badge (chips) */
  .search-type-badge{
    display:inline-block;
    padding:.25rem .6rem;
    border-radius:999px;
    font-size:.8rem;
    font-weight:600;
    margin:.1rem 0;
  }
  .keyword { background:#e3f2fd; color:#1976d2; }
  .vector { background:#f3e5f5; color:#7b1fa2; }
  .hybrid { background:#e8f5e8; color:#388e3c; }
  .generative { background:#fff3e0; color:#f57c00; }
            
    /* Tenant and section headers */
    h2 {
        color: #ffffff !important; 
        font-weight: 500 !important;
    }
            
    /* Make only text input labels white */
div.stTextInput label {
    color: #ffffff !important;
    font-weight: 600;
}


</style>
""", unsafe_allow_html=True)


def main():

    left, right = st.columns([0.25, 0.75])
    with left:
        st.image("images/logo.png", use_container_width=False, output_format="PNG", caption="", width=400)
        # st.markdown('<img src="images/logo.png" class="logo-img">', unsafe_allow_html=True)
    with right:
        st.markdown('<h1 class="main-header">Summit Sports</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Advanced Search & AI-Powered Document Discovery</p>', unsafe_allow_html=True)
    
    if 'selected_tenant' not in st.session_state:
        st.session_state.selected_tenant = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'all_documents' not in st.session_state:
        st.session_state.all_documents = []
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "documents"
    
    with st.sidebar:
        weaviate_b64 = _b64("images/weaviate-logo.png")
        box_b64 = _b64("images/box-logo.png")

        # top logos row (centered in the white strip)
        st.markdown(
            f"""
            <div class="sidebar-logos">
                <img src="data:image/png;base64,{weaviate_b64}" alt="Weaviate" />
                <img src="data:image/png;base64,{box_b64}" alt="Box" />
            </div>
            """,
            unsafe_allow_html=True
        )


        st.header(" Search Controls")
        
        search_type = st.selectbox(
            "Search Type",
            ["hybrid", "keyword", "vector", "generative"],
            help="Choose the type of search to perform"
        )
        
        if search_type == "hybrid":
            alpha = st.slider(
                "Alpha Parameter",
                min_value=0.0,
                max_value=1.0,
                value=0.75,
                step=0.1,
                help="0.0 = pure keyword search, 1.0 = pure vector search"
            )
        else:
            alpha = 0.5
        
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            help="Type your search query here"
        )
        
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
        
        if st.button("🗑️ Clear Search"):
            st.session_state.search_results = None
            st.session_state.current_view = "documents"
            st.rerun()
        
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
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📁 Select Department")
        
        tenants = fetch_tenants()
        if tenants:
            for tenant in tenants:
                if st.button(
                    f"**{tenant['name']}**\n\n📄 {tenant['document_count']} documents",
                    key=f"tenant_{tenant['name']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_tenant = tenant['name']
                    st.session_state.search_results = None
                    st.session_state.current_view = "documents"
                    st.session_state.all_documents = fetch_documents(tenant['name'])
                    st.rerun()

        # if tenants:
        #     cols = st.columns(len(tenants))
        #     for i, tenant in enumerate(tenants):
        #         with cols[i]:
        #             if st.button(
        #                 f"**{tenant['name']}**\n\n📄 {tenant['document_count']} documents",
        #                 key=f"tenant_{tenant['name']}",
        #                 help=f"Click to view {tenant['name']} documents"
        #             ):
        #                 st.session_state.selected_tenant = tenant['name']
        #                 st.session_state.search_results = None
        #                 st.session_state.current_view = "documents"
        #                 st.session_state.all_documents = fetch_documents(tenant['name'])
        #                 st.rerun()
        else:
            st.error("Unable to fetch tenants. Please check your API connection.")
    
    with col2:
        if st.session_state.selected_tenant:
            st.success(f"✅ Selected: **{st.session_state.selected_tenant}**")
            
            documents = st.session_state.all_documents
            st.metric("Total Documents", len(documents))
            
            view_icons = {
                "documents": "📄",
                "search": "🔍", 
                "agent": "🤖"
            }
            st.info(f"{view_icons.get(st.session_state.current_view, '📄')} Viewing: {st.session_state.current_view.title()}")
        # else:
        #     st.info("👈 Select a department to get started")
    
    if st.session_state.selected_tenant:
        if st.session_state.current_view == "search" and st.session_state.search_results:
            st.header("🔍 Search Results")
            
            search_type_badge = f'<span class="search-type-badge {st.session_state.search_results["search_type"]}">{st.session_state.search_results["search_type"].upper()}</span>'
            st.markdown(f"Search Type: {search_type_badge}", unsafe_allow_html=True)
            st.markdown(f"Query: **{st.session_state.search_results['query']}**")
            st.markdown(f"Found: **{st.session_state.search_results['total_count']}** results")
            
            for doc in st.session_state.search_results['documents']:
                with st.container():
                    # Check if this is a generated response
                    is_generated = doc.get('file_name') == 'AI Generated Response'
                    
                    if is_generated:
                        # Show full content for generated responses
                        st.markdown(f"""
                        <div class="document-card">
                            <h4>🤖 {doc['file_name']}</h4>
                            <p><strong>Generated Answer:</strong></p>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
                                {doc['content']}
                            </div>
                            <small>Date: {doc['created_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Truncate regular documents
                        st.markdown(f"""
                        <div class="document-card">
                            <h4> {doc['file_name']} (Chunk {doc['chunk_index']})</h4>
                            <p><strong>Content:</strong> {doc['content']}</p>
                            <small>ID: {doc['id'][:8]}... | Date: {doc['created_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        elif st.session_state.current_view == "agent" and hasattr(st.session_state, 'agent_response') and st.session_state.agent_response:
            st.header("🤖 Agent Response")
            agent_resp = st.session_state.agent_response
            
            st.markdown(f"**Query:** {agent_resp['query']}")
            st.markdown(f"**Answer:** {agent_resp.get('answer', 'No answer available')}")
        
        else:
            st.header(f"📄 {st.session_state.selected_tenant} Documents")
            
            filter_text = st.text_input(
                "🔍 Filter Documents",
                placeholder="Type to filter documents by content...",
                help="Filter documents by typing keywords"
            )
            
            documents = st.session_state.all_documents
            if documents:
                filtered_documents = filter_documents_locally(documents, filter_text)
                
                if filter_text:
                    st.info(f"Showing {len(filtered_documents)} of {len(documents)} documents matching '{filter_text}'")
                
                for doc in filtered_documents[:10]:
                    with st.container():
                        st.markdown(f"""
                        <div class="document-card">
                            <h4>{doc['file_name']} (Chunk {doc['chunk_index']})</h4>
                            <p><strong>Content:</strong></p>
                            <div style="list-style: none; margin-left: 0; padding-left: 0;">
                                {doc['content']}
                            </div>
                            <small>ID: {doc['id'][:8]}... | Date: {doc['created_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        # st.markdown(f"""
                        # <div class="document-card">
                        #     <h4> {doc['file_name']} (Chunk {doc['chunk_index']})</h4>
                        #     <p><strong>Content:</strong> {doc['content']}...</p>
                        #     <small>ID: {doc['id'][:8]}... | Date: {doc['created_date']}</small>
                        # </div>
                        # """, unsafe_allow_html=True)
                
                if len(filtered_documents) > 10:
                    st.info(f"Showing first 10 of {len(filtered_documents)} filtered documents.")
            else:
                st.warning("No documents found for this tenant.")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #ffffff; padding: 2rem;">
        <p> Powered by <strong>Box and Weaviate</strong> | Built with <strong>Streamlit</strong></p>
        <p>Features: Keyword Search | Vector Search | Hybrid Search | Generative AI | Query Agent</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()