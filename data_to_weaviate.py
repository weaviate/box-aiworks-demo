import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.tenants import Tenant
from dotenv import load_dotenv
import os
import re
from pathlib import Path

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

multi_collection = weaviate_client.collections.get("BoxDocuments")

# Path to the parent folder that contains the 5 subfolders
parent_folder = "data"


def clean_md(md: str) -> str:
    md = md.replace("\r\n", "\n").replace("\r", "\n").strip()
    # remove **bold**
    md = re.sub(r"\*\*(.*?)\*\*", r"\1", md)
    # remove ONE leading H1 title line and any blank lines immediately after
    md = re.sub(r"^\s*#\s+.*?\n(\s*\n)*", "", md, flags=re.MULTILINE)
    # normalize whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    return md

# match only '## ...' headers
H2_RE = re.compile(r"(^##\s+.+$)", flags=re.MULTILINE)

def split_h2_sections(md: str):
    """Yield only (header, body) for sections that start with '## '."""
    parts = H2_RE.split(md)  # ['', '## H2', 'body', '## H2b', 'bodyb', ...]
    # iterate pairs: header -> body
    it = iter(parts)
    first = next(it, "")
    # ignore any preface before first '##' (by design)
    for header in it:
        body = next(it, "")
        yield header.strip(), body.strip()

def chunk_h2_section(header: str, body: str, max_chars: int = 1400):
    """Chunk only within this H2 section; each chunk starts with the same header."""
    prefix = header + "\n\n"
    space = max_chars - len(prefix)
    blocks = re.split(r"\n\s*\n", body) if body else [""]
    acc, acc_len = [], 0

    def emit(lines):
        text = "\n\n".join(lines).strip()
        return (prefix + text).strip()

    for b in blocks:
        b = b.strip()
        if not b:
            continue
        fit = acc_len + (2 if acc else 0) + len(b)
        if fit <= space:
            acc.append(b); acc_len = fit
        else:
            if acc: yield emit(acc); acc, acc_len = [], 0
            if len(b) <= space:
                acc, acc_len = [b], len(b)
            else:
                # sentence fallback
                for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", b):
                    s = s.strip()
                    if not s: continue
                    if (acc_len + (1 if acc else 0) + len(s)) <= space:
                        acc.append(s); acc_len += (1 if acc else 0) + len(s)
                    else:
                        if acc: yield emit(acc)
                        acc, acc_len = [s], len(s)
    if acc: yield emit(acc)

# ---------------- Ingestion ----------------
for subfolder in os.listdir(parent_folder):
    subfolder_path = os.path.join(parent_folder, subfolder)
    if not os.path.isdir(subfolder_path): continue

    print(f"\n=== Folder: {subfolder} ===")
    tenant_collection = multi_collection.with_tenant(subfolder)

    for item in os.listdir(subfolder_path):
        if not item.lower().endswith(".md"): continue
        file_path = os.path.join(subfolder_path, item)

        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()

        cleaned = clean_md(raw)

        # ONLY process `##` sections; H1 and any preface are dropped
        for header, body in split_h2_sections(cleaned):
            for chunk in chunk_h2_section(header, body, max_chars=1400):
                tenant_collection.data.insert(properties={"content": chunk})
