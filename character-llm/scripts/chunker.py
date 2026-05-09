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
def chunk_entries(entries: List[dict], max_words: int = 250, overlap_entries: int = 2) -> List[List[dict]]:
    """
    Chunk theo entry thay vì cắt text thô.
    Không bao giờ cắt giữa dialogue/action/text entry.
    """
    chunks = []

    current_chunk = []
    current_word_count = 0

    for entry in entries:
        entry_text = entry.get("text", "")
        entry_words = len(entry_text.split())

        if entry_words > max_words:
            print(f"[WARN] Large entry exceeds max_words: {entry_words}")
        # Nếu vượt giới hạn -> flush chunk hiện tại
        if (
            current_word_count + entry_words > max_words
            and current_chunk
        ):
            chunks.append(current_chunk)

            # overlap giữ lại vài entry cuối
            current_chunk = current_chunk[-overlap_entries:]

            current_word_count = sum(
                len(e.get("text", "").split())
                for e in current_chunk
            )

        current_chunk.append(entry)
        current_word_count += entry_words

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_document(doc: dict, chunk_size: int = 250, overlap_entries: int = 2) -> List[dict]:
    """
    Convert parsed document -> semantic chunks.
    Chunk theo entries thay vì raw text.
    """

    results: List[dict] = []

    doc_id = doc.get("doc_id", "unknown")
    source = doc.get("source", "")
    character = doc.get("character", "")

    for section in doc.get("sections", []):

        section_name = section.get("section", "Unnamed")

        # entries đã được parse từ parse_content()
        entries = section.get("entries", [])

        if not entries:
            continue

        entry_chunks = chunk_entries(
            entries,
            max_words=chunk_size,
            overlap_entries=overlap_entries
        )

        for idx, chunk_entries_list in enumerate(entry_chunks):

            safe_section = (
                section_name.lower()
                .replace(" ", "_")[:40]
            )

            chunk_id = f"{doc_id}__{safe_section}__{idx}"

            # convert entries -> text để embed/vectorize
            merged_text = "\n".join(
                entry.get("text", "")
                for entry in chunk_entries_list
            )

            results.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "source": source,
                "character": character,
                "section": section_name,
                "chunk_index": idx,

                # text thuần để embedding
                "text": merged_text,

                # giữ structured entries cho AI dùng
                "entries": chunk_entries_list,
            })

    return results


def chunk_documents(documents: List[dict], chunk_size: int, overlap_entries: int) -> List[dict]:
    all_chunks: list[dict] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size, overlap_entries))
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
        "--overlap-entries",
        type=int,
        default=2,
        help="Overlap words between consecutive chunks (default: 40)",
    )
    args = parser.parse_args()

    documents = load_documents(args.input)
    chunks    = chunk_documents(documents, args.chunk_size, args.overlap_entries)
    save_chunks(chunks, args.output)

    total_sections = sum(len(d.get("sections", [])) for d in documents)
    print(
        f"Chunked {len(documents)} doc(s), {total_sections} section(s) "
        f"→ {len(chunks)} chunks  (size={args.chunk_size}, overlap={args.overlap_entries})"
    )
    print(f"Saved → {args.output}")