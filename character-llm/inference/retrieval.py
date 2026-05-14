"""Local RAG retrieval with manual canon facts and weighted reranking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

try:
    from manual_facts import (
        ManualFactMatch,
        ManualFactStore,
        format_matches_for_context,
        normalize_text,
        tokenize,
    )
except ImportError:  # pragma: no cover - fallback for package-style imports
    from .manual_facts import (
        ManualFactMatch,
        ManualFactStore,
        format_matches_for_context,
        normalize_text,
        tokenize,
    )


REPO_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = REPO_ROOT / "character-llm" / "data" / "processed" / "chunks.json"
VECTORDB_PATH = REPO_ROOT / "character-llm" / "data" / "vectordb"
MANUAL_FACTS_PATH = REPO_ROOT / "data" / "manual_facts"

COLLECTION_NAME = "ayaka_chunks"
DEFAULT_CHARACTER_NAME = "Kamisato Ayaka"
MAX_VECTOR_DISTANCE = 1.5
MAX_MANUAL_FACTS = 5

SECTION_WEIGHTS = {
    "default": 1.0,
    "dialogue": 0.65,
    "profile": 1.15,
    "personality": 1.3,
    "history": 1.25,
    "family": 1.4,
}

QUERY_EXPANSION_RULES = {
    "gia dinh": ("family", "siblings", "parents", "brother", "sister"),
    "family": ("family", "siblings", "parents", "brother", "sister"),
    "anh trai": ("brother", "siblings", "family"),
    "chi gai": ("sister", "siblings", "family"),
    "em trai": ("brother", "siblings", "family"),
    "em gai": ("sister", "siblings", "family"),
    "bo me": ("parents", "mother", "father", "family"),
    "cha me": ("parents", "mother", "father", "family"),
    "parents": ("parents", "mother", "father", "family"),
    "siblings": ("siblings", "brother", "sister", "family"),
    "lich su": ("history", "background", "past", "clan history"),
    "tieu su": ("history", "background", "origin", "profile"),
    "qua khu": ("history", "past", "background"),
    "history": ("history", "background", "past"),
    "personality": ("personality", "temperament", "traits"),
    "tinh cach": ("personality", "temperament", "traits"),
    "ho so": ("profile", "introduction", "background"),
    "profile": ("profile", "introduction", "background"),
}

PROFILE_HINTS = {
    "introduction",
    "official introduction",
    "appearance",
    "daily life",
    "interests",
    "aliases and titles",
}
HISTORY_HINTS = {
    "history",
    "clan history",
    "character stories",
    "childhood",
    "background",
    "past",
    "change history",
    "the truth behind the order",
}
FAMILY_HINTS = {
    "family",
    "brother",
    "sister",
    "siblings",
    "mother",
    "father",
    "parents",
    "clan",
}
DIALOGUE_HINT_PREFIXES = (
    "chat",
    "about us",
    "good ",
    "when ",
    "receiving a gift",
    "feelings about ascension",
)


EMBED_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
chroma_client = chromadb.PersistentClient(path=str(VECTORDB_PATH))


@dataclass(slots=True)
class RetrievedChunk:
    """Vector-retrieved chunk plus rerank metadata."""

    chunk_id: str
    text: str
    section: str
    doc_id: str
    character: str
    distance: float
    matched_query: str
    section_bucket: str = "default"
    section_weight: float = 1.0
    lexical_overlap: float = 0.0
    rerank_score: float = 0.0


def embed(text: str) -> list[float]:
    """Convert text into an embedding vector for Chroma search."""
    vector = EMBED_MODEL.encode(text)
    return vector.tolist()


@lru_cache(maxsize=1)
def load_chunk_catalog() -> dict[str, dict[str, Any]]:
    """Load chunk metadata locally so reranking can use full chunk labels."""
    if not CHUNKS_PATH.exists():
        return {}

    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return {
        chunk["chunk_id"]: chunk
        for chunk in chunks
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


@lru_cache(maxsize=1)
def load_manual_fact_store() -> ManualFactStore:
    """Load runtime-only manual facts from ``data/manual_facts``."""
    return ManualFactStore.from_directory(MANUAL_FACTS_PATH)


def build_index(chunks_path: str | Path = CHUNKS_PATH) -> None:
    """Read ``chunks.json``, embed each chunk, and upsert into Chroma."""
    chunks_file = Path(chunks_path)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))

    print(f"Embedding {len(chunks)} chunks from {chunks_file} ...")

    for index, chunk in enumerate(chunks, start=1):
        collection.upsert(
            ids=[chunk["chunk_id"]],
            embeddings=[embed(chunk["text"])],
            documents=[chunk["text"]],
            metadatas=[
                {
                    "section": chunk.get("section", ""),
                    "doc_id": chunk.get("doc_id", ""),
                    "character": chunk.get("character", ""),
                }
            ],
        )

        if index % 10 == 0:
            print(f"  {index}/{len(chunks)} chunks indexed")

    print(f"Finished indexing {len(chunks)} chunks into Chroma.")
    print("Manual facts remain runtime-only and are not embedded into the vector DB.")


def expand_query(question: str) -> list[str]:
    """Expand multilingual queries with domain synonyms for recall."""
    normalized_question = normalize_text(question)
    expanded_queries = [question.strip()]
    seen = {normalized_question}

    for trigger, variants in QUERY_EXPANSION_RULES.items():
        if trigger not in normalized_question:
            continue

        for variant in variants:
            normalized_variant = normalize_text(variant)
            if normalized_variant and normalized_variant not in seen:
                expanded_queries.append(variant)
                seen.add(normalized_variant)

    return expanded_queries


def get_query_terms(values: list[str]) -> set[str]:
    """Collect normalized query tokens for lightweight lexical reranking."""
    terms: set[str] = set()
    for value in values:
        terms.update(token for token in tokenize(value) if len(token) >= 3)
    return terms


def classify_section_bucket(chunk: RetrievedChunk) -> str:
    """Map heterogeneous section names into a few weighted retrieval buckets."""
    section = normalize_text(chunk.section)
    doc_id = normalize_text(chunk.doc_id)
    text = normalize_text(chunk.text[:1200])

    if (
        section == "dialogue"
        or "voice overs" in doc_id
        or any(section.startswith(prefix) for prefix in DIALOGUE_HINT_PREFIXES)
    ):
        return "dialogue"

    if "personality" in section:
        return "personality"

    if section in HISTORY_HINTS or any(hint in section for hint in HISTORY_HINTS):
        return "history"

    if section in PROFILE_HINTS or ("profile" in doc_id and section in PROFILE_HINTS):
        return "profile"

    if any(hint in section for hint in FAMILY_HINTS) or any(hint in text for hint in FAMILY_HINTS):
        return "family"

    if "profile" in doc_id:
        return "profile"

    return "default"


def compute_lexical_overlap(text: str, query_terms: set[str]) -> float:
    """Small overlap bonus so query-specific chunks beat generic ones."""
    if not query_terms:
        return 0.0

    text_terms = {token for token in tokenize(text) if len(token) >= 3}
    if not text_terms:
        return 0.0

    overlap = len(query_terms.intersection(text_terms))
    if not overlap:
        return 0.0

    return overlap / max(len(query_terms), 1)


def query_vector_candidates(expanded_queries: list[str], top_k: int) -> list[RetrievedChunk]:
    """Run vector search for the original query plus expanded variants."""
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    chunk_catalog = load_chunk_catalog()
    candidate_pool = max(top_k * 4, 12)
    best_by_id: dict[str, RetrievedChunk] = {}

    for query in expanded_queries:
        results = collection.query(
            query_embeddings=[embed(query)],
            n_results=candidate_pool,
            include=["documents", "distances", "metadatas"],
        )

        chunk_ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or [{}] * len(chunk_ids)

        for chunk_id, document, distance, metadata in zip(
            chunk_ids,
            documents,
            distances,
            metadatas,
        ):
            if distance is None or distance >= MAX_VECTOR_DISTANCE:
                continue

            chunk_data = chunk_catalog.get(chunk_id, {})
            candidate = RetrievedChunk(
                chunk_id=chunk_id,
                text=chunk_data.get("text", document or ""),
                section=chunk_data.get("section", (metadata or {}).get("section", "")),
                doc_id=chunk_data.get("doc_id", (metadata or {}).get("doc_id", "")),
                character=chunk_data.get("character", (metadata or {}).get("character", "")),
                distance=float(distance),
                matched_query=query,
            )

            current_best = best_by_id.get(chunk_id)
            if current_best is None or candidate.distance < current_best.distance:
                best_by_id[chunk_id] = candidate

    return list(best_by_id.values())


def rerank_chunks(
    candidates: list[RetrievedChunk],
    query_terms: set[str],
    *,
    top_k: int,
    character_name: str | None = None,
) -> list[RetrievedChunk]:
    """Apply section weighting and a small lexical bonus after vector retrieval."""
    reranked: list[RetrievedChunk] = []
    normalized_character = normalize_text(character_name or "")

    for candidate in candidates:
        if normalized_character and candidate.character:
            if normalize_text(candidate.character) != normalized_character:
                related_text = normalize_text(candidate.text[:1200])
                if normalized_character not in related_text:
                    continue

        bucket = classify_section_bucket(candidate)
        weight = SECTION_WEIGHTS.get(bucket, SECTION_WEIGHTS["default"])
        lexical_overlap = compute_lexical_overlap(candidate.text, query_terms)
        semantic_score = 1.0 / (1.0 + candidate.distance)

        candidate.section_bucket = bucket
        candidate.section_weight = weight
        candidate.lexical_overlap = lexical_overlap
        candidate.rerank_score = (semantic_score * weight) + (lexical_overlap * 0.15)
        reranked.append(candidate)

    reranked.sort(key=lambda item: (-item.rerank_score, item.distance, item.chunk_id))
    return reranked[:top_k]


def format_vector_context(chunks: list[RetrievedChunk]) -> str:
    """Render reranked chunks into a prompt-ready lore block."""
    if not chunks:
        return ""

    lines = ["=== RETRIEVED LORE ==="]
    for chunk in chunks:
        label = chunk.section.strip() or chunk.section_bucket.title()
        lines.append(f"[{label}] {chunk.text.strip()}")
    return "\n\n".join(lines)


def assemble_context(
    manual_matches: list[ManualFactMatch],
    vector_chunks: list[RetrievedChunk],
) -> str:
    """Combine guaranteed canon facts with reranked vector lore."""
    blocks = [
        block
        for block in (
            format_matches_for_context(manual_matches),
            format_vector_context(vector_chunks),
        )
        if block
    ]
    return "\n\n".join(blocks)


def retrieve(
    question: str,
    top_k: int = 5,
    character_name: str | None = DEFAULT_CHARACTER_NAME,
) -> str:
    """Retrieve prompt context using manual facts first, then vector search."""
    expanded_queries = expand_query(question)
    query_terms = get_query_terms(expanded_queries)

    manual_matches = load_manual_fact_store().match(
        question,
        expanded_queries[1:],
        character_name=character_name,
        limit=MAX_MANUAL_FACTS,
    )

    vector_candidates = query_vector_candidates(expanded_queries, top_k)
    reranked_chunks = rerank_chunks(
        vector_candidates,
        query_terms,
        top_k=top_k,
        character_name=character_name,
    )

    return assemble_context(manual_matches, reranked_chunks)


if __name__ == "__main__":
    build_index(CHUNKS_PATH)
