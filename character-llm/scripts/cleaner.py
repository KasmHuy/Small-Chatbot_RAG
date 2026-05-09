"""
Clean a document.json produced by scraper.py.

What it does:
  1. Drop sections that are purely navigation / template noise
  2. Strip wikitext artifacts (*, **, &mdash;, |key = value lines, etc.)
  3. Drop sections whose content is empty after cleaning
  4. Write the result back as a clean document.json
"""

import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Sections to drop entirely (case-insensitive exact match or startswith)
# ---------------------------------------------------------------------------
BLOCKED_SECTIONS = {
    "navigation",
    "references",
    "see also",
    "gallery",
    "other languages",
    "in other languages",
    "poetry",       # thêm
    "etymology", 
}

BLOCKED_SECTION_PREFIXES = (
    "character title:",   # |ja_tl = ... template dumps
)


def _is_blocked_section(section_name: str) -> bool:
    name = section_name.strip().lower()
    if name in BLOCKED_SECTIONS:
        return True
    for prefix in BLOCKED_SECTION_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_content(text: str) -> str:
    text = text.replace("&mdash;", "—")
    text = text.replace("&ndash;", "–")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\|[\w_\s]+=", stripped):
            continue
        if stripped in ("}}", "{{", "|", ""):
            continue
        stripped = re.sub(r"^\*{1,3}\s*", "", stripped)
        stripped = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", stripped)
        stripped = re.sub(r"https?://\S+", "", stripped)
        stripped = re.sub(r"'{2,}", "", stripped)
        stripped = re.sub(r"[\u3000-\u9fff\ua000-\udfff\uf900-\uffef]+", "", stripped)
        stripped = re.sub(r"\(\s*\)", "", stripped)
        stripped = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stripped)
        stripped = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stripped)
        stripped = stripped.strip()
        # Chỉ giữ dòng có từ tiếng Anh và đủ 2 từ trở lên
        if re.search(r"[a-zA-Z]", stripped) and len(stripped.split()) >= 2:
            cleaned_lines.append(stripped)   # ← chỉ append string

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"'\s*$", "", text)        # trailing quote
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Document cleaning
# ---------------------------------------------------------------------------

def clean_document(doc: dict) -> dict:
    cleaned_sections = []

    for section in doc.get("sections", []):
        name    = section.get("section", "")
        content = section.get("content", "")

        if _is_blocked_section(name):
            continue

        content = clean_content(content)

        if not content:
            continue

        cleaned_sections.append({"section": name, "content": content})

    return {**doc, "sections": cleaned_sections}


def clean_documents(documents: list[dict]) -> list[dict]:
    return [clean_document(doc) for doc in documents]


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load_documents(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_documents(documents: list[dict], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean a document.json file.")
    parser.add_argument("input",  nargs="?", default="../data/raw/document.json")
    parser.add_argument("output", nargs="?", default="../data/processed/document_clean.json")
    args = parser.parse_args()

    documents = load_documents(args.input)
    cleaned   = clean_documents(documents)
    save_documents(cleaned, args.output)

    for original, result in zip(documents, cleaned):
        dropped = len(original["sections"]) - len(result["sections"])
        print(
            f"{result['doc_id']}: "
            f"{len(original['sections'])} sections → {len(result['sections'])} kept "
            f"({dropped} dropped)"
        )
    print(f"\nSaved → {args.output}")