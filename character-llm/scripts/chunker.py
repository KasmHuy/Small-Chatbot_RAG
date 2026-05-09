"""
Chunk a structured document.json into smaller overlapping text segments.

Input  (document.json):
    List of documents, each with "doc_id", "source", "character", and "sections".

Output (chunks.json):
    List of chunk objects:
    {
        "chunk_id": "wiki_kamisato_ayaka_profile__introduction__0",
        "doc_id":   "wiki_kamisato_ayaka_profile",
        "source":   "https://...",
        "character": "Kamisato Ayaka",
        "section":  "Introduction",
        "chunk_index": 0,
        "text":     "..."
    }
"""

import json
import argparse
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Core chunking helpers
# ---------------------------------------------------------------------------

def chunk_words(words: List[str], chunk_size: int, overlap: int) -> List[str]:
    """Split a word list into overlapping string chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def chunk_section(section_text: str, chunk_size: int, overlap: int) -> List[str]:
    """Return word-level overlapping chunks for a single section's text."""
    words = section_text.split()
    if not words:
        return []
    return chunk_words(words, chunk_size, overlap)


# ---------------------------------------------------------------------------
# Document → chunks
# ---------------------------------------------------------------------------

def chunk_document(doc: dict, chunk_size: int, overlap: int) -> List[dict]:
    """Convert one document dict into a flat list of chunk dicts."""
    results: list[dict] = []
    doc_id    = doc.get("doc_id", "unknown")
    source    = doc.get("source", "")
    character = doc.get("character", "")

    for section in doc.get("sections", []):
        section_name = section.get("section", "Unnamed")
        content      = section.get("content", "")
        text_chunks  = chunk_section(content, chunk_size, overlap)

        for idx, text in enumerate(text_chunks):
            # Build a deterministic, human-readable chunk_id
            safe_section = section_name.lower().replace(" ", "_")[:40]
            chunk_id = f"{doc_id}__{safe_section}__{idx}"

            results.append({
                "chunk_id":    chunk_id,
                "doc_id":      doc_id,
                "source":      source,
                "character":   character,
                "section":     section_name,
                "chunk_index": idx,
                "text":        text,
                
            })

    return results


def chunk_documents(documents: List[dict], chunk_size: int, overlap: int) -> List[dict]:
    all_chunks: list[dict] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size, overlap))
    return all_chunks


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load_documents(path: str) -> List[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_chunks(chunks: List[dict], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chunk a document.json into overlapping text segments (chunks.json)."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="../data/raw/document.json",
        help="Path to document.json  (default: ../data/raw/document.json)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="../data/processed/chunks.json",
        help="Path for output chunks.json  (default: ../data/processed/chunks.json)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Max words per chunk (default: 200)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=40,
        help="Overlap words between consecutive chunks (default: 40)",
    )
    args = parser.parse_args()

    documents = load_documents(args.input)
    chunks    = chunk_documents(documents, args.chunk_size, args.overlap)
    save_chunks(chunks, args.output)

    total_sections = sum(len(d.get("sections", [])) for d in documents)
    print(
        f"Chunked {len(documents)} doc(s), {total_sections} section(s) "
        f"→ {len(chunks)} chunks  (size={args.chunk_size}, overlap={args.overlap})"
    )
    print(f"Saved → {args.output}")