from typing import List, Optional, Tuple, Union
import os
from pathlib import Path
import pymupdf4llm
import pypandoc
import re
import spacy
from opensearchpy import OpenSearch


# Load spaCy English model
lemmatizer = spacy.load("en_core_web_sm")

def get_opensearch_client(opensearch_host):
    """Create OpenSearch client"""
    return OpenSearch(hosts=[opensearch_host])


def get_files(root: Union[Path, str], extension: str = '') -> List[Path]:
    """Get all files with given extension"""
    files = sorted([file for file in Path(root).rglob(f'*{extension}') if file.is_file()])
    return files

def load_text(file: Path) -> Optional[str]:
    """Read and convert file content to text"""
    try:
        if file.suffix == '.pdf':
            text = pymupdf4llm.to_markdown(file).strip()
        elif file.suffix in ['.txt', '.text']:
            text = file.read_text(encoding='utf-8').strip()
        elif file.suffix == '.docx':
            text = pypandoc.convert_file(str(file), 'md').strip()
        else:
            text = None
    except Exception as e:
        print(f"Error loading {file.name}: {e}")
        return None
    return text

def remove_stopwords(text) -> str:
    """Remove stopwords from text"""
    doc = lemmatizer(text)
    return " ".join([str(token) for token in doc if not token.is_stop])

def lemmatize(text) -> str:
    """Lemmatize text and remove stopwords."""
    doc = lemmatizer(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop and token.lemma_ != "-PRON-"])

def get_title_and_author(text) -> Tuple[str, str]:
    """Get title and author from first paragraphs."""
    clean = lambda line: line.replace("**", "").replace("_", "").strip()
    text = text.split("\n\n")
    title = clean(text[1]).replace('*', '')
    author = clean(text[2]).split(' and ') if re.fullmatch("\*\*.*\*\*", text[2]) else []
    return title, author

def parse_filename(file) -> Tuple[str, str, str, str]:
    """Extract metadata from filename"""
    number = lambda string: int(string[-2:])
    name = str(file.stem).split("-")
    volume = f"Volume {number(name[0])}"
    order = int(name[1])
    section = f"Section {number(name[2])}"
    if name[-1] == 'Intro':
        chapter = 'Introduction'
    elif name[-1] == 'References':
        chapter = 'References'
    else:
        chapter = f"Chapter {number(name[-1])}"
    return volume, order, section, chapter

def extract_headers(text):
    #TO DO: Placeholder for future header extraction
    return []

def get_aggs(client, index):
    aggs = client.search(index=index, body={
    "size": 0,
    "aggs": {
        "volumes": {
            "terms": {
                "field": "volume",  
                "size": 100
            }
        },
        "authors": {
            "terms": {
                "field": "author",
                "size": 100
            }
        }
    }
    })["aggregations"]
    all_volumes = sorted([b["key"] for b in aggs["volumes"]["buckets"]])
    all_authors = sorted([b["key"] for b in aggs["authors"]["buckets"]])
    return all_volumes, all_authors

def format_download_link(b64data, filename, title):
    """Return an HTML download link for base64-encoded PDF data."""
    href = f'<a href="data:application/pdf;base64,{b64data}" download="{filename}">{title}</a>'
    return href

def format_metadata(author, volume, section, chapter):
    """Format author and document metadata into a readable string."""
    metadata = [volume]
    if section:
        metadata.append(section)
    if chapter:
        metadata.append(chapter)
    metadata = ", ".join(metadata)
    if author:
        author = ', '.join(author)
        metadata = f'**{author}** | *{metadata}*'
    return metadata

def format_hit(hit):
    """Format a search hit into title, metadata, HTML flag, and highlights."""
    src = hit["_source"]
    title = src.get("title", "")
    author = src.get("author", "")
    volume = src.get("volume", "")
    section = src.get("section", "")
    chapter = src.get("chapter", "")
    path = os.path.basename(src["path"])
    unsafe_allow_html = False

    """Convert title to clickable PDF link if base64 PDF is available."""
    if "pdf" in src:
        b64 = src["pdf"]
        title = format_download_link(b64, path, title)
        unsafe_allow_html = True

    """Generate metadata and highlight snippets for display."""
    metadata = format_metadata(author, volume, section, chapter)
    snippets = hit.get("highlight", {}).get("content", [])

    return title, metadata, unsafe_allow_html, snippets


