"""Generate training pairs from processed chunks using an LLM API."""

import os
from pathlib import Path
from typing import List


def generate_prompt_for_chunk(chunk: str, character_name: str) -> str:
    return f"Generate a conversation snippet where {character_name} explains the following information: {chunk}"


def generate_training_pairs(chunks: List[str], character_name: str) -> List[dict]:
    pairs = []
    for chunk in chunks:
        prompt = generate_prompt_for_chunk(chunk, character_name)
        pairs.append({"input": prompt, "output": "<MODEL_RESPONSE>"})
    return pairs


def load_chunks(path: str) -> List[str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_jsonl(records: List[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate training pairs from processed chunks.")
    parser.add_argument("chunks", default="../data/processed/chunks.json", help="Chunks JSON path")
    parser.add_argument("train-output", default="../data/training/train.jsonl", help="Training output JSONL")
    parser.add_argument("eval-output", default="../data/training/eval.jsonl", help="Evaluation output JSONL")
    parser.add_argument("--character-name", default=os.getenv("CHARACTER_NAME", "Character"), help="Character name")
    args = parser.parse_args()

    chunks = load_chunks(args.chunks)
    pairs = generate_training_pairs(chunks, args.character_name)
    save_jsonl(pairs, args.train_output)
    save_jsonl(pairs[: max(1, len(pairs) // 10)], args.eval_output)
