"""Validate JSONL files for training and evaluation."""

import json
from pathlib import Path


def validate_jsonl(path: str) -> bool:
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path_obj.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}")
            if not isinstance(record, dict) or "input" not in record or "output" not in record:
                raise ValueError(f"Invalid record format on line {line_number}: {record}")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate JSONL training data files.")
    parser.add_argument("path", help="Path to a JSONL file")
    args = parser.parse_args()

    valid = validate_jsonl(args.path)
    print(f"Validation passed: {valid}")
