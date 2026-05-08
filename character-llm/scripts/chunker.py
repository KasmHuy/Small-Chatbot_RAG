"""Split long character text into smaller chunks for embedding and training."""

import json
from pathlib import Path
from typing import List


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def load_raw_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def save_chunks(chunks: List[str], path: str):
    Path(path).write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chunk raw character wiki text into smaller segments.")
    parser.add_argument("input", default="../data/raw/character_wiki.txt", help="Raw text input path")
    parser.add_argument("output", default="../data/processed/chunks.json", help="Output chunks JSON path")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=200)
    args = parser.parse_args()

    text = load_raw_text(args.input)
    chunks = chunk_text(text, args.chunk_size, args.overlap)
    save_chunks(chunks, args.output)
