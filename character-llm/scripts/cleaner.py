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

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
DEFAULT_RAW_DOCUMENT_PATH = DATA_ROOT / "raw" / "document.json"
DEFAULT_CLEAN_DOCUMENT_PATH = DATA_ROOT / "processed" / "document_clean.json"


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

def clean_content(text: str):
    # HTML entities
    text = (
        text.replace("&mdash;", "—")
            .replace("&ndash;", "–")
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )
    lines = text.splitlines()
    # Dialogue: "Name: Text" hoặc "Name (Emotion): Text"
    dialogue_pattern = re.compile(
        r"^([\w\s]+?)(?:\s*\((.*?)\))?\s*:\s*(.*)$"
    )
    # Action/context: "(Action)" hoặc ";(Action)"
    action_pattern = re.compile(
        r"^\s*[;:]?\s*\((.*)\)\s*$"
    )

    entries = []
    seen = set()

    for line in lines:
        stripped = line.strip()

        # ===== CLEAN =====

        # remove template dump
        if re.match(r"^\|[\w_\s]+=", stripped):
            continue

        if stripped in ("}}", "{{", "|", ""):
            continue

        # remove wiki formatting
        stripped = re.sub(r"^\*{1,3}\s*", "", stripped)

        # remove leading :
        stripped = re.sub(r"^:\s*", "", stripped)

        # remove commands
        stripped = re.sub(r"^[#;]+\s*", "", stripped)

        # normalize colons
        stripped = re.sub(r"[:]{2,}", ":", stripped)

        # remove links
        stripped = re.sub(
            r"\[https?://\S+\s+([^\]]+)\]",
            r"\1",
            stripped
        )
        stripped = re.sub(r"https?://\S+", "", stripped)

        # remove bold/italic wiki markup
        stripped = re.sub(r"'{2,}", "", stripped)

        # normalize spacing
        stripped = re.sub(r"\s{2,}", " ", stripped)
        stripped = stripped.strip()

        # filter tiny junk
        if len(stripped.split()) < 5:
            continue

        # must contain english
        if not re.search(r"[a-zA-Z]", stripped):
            continue

        # deduplicate
        if stripped in seen:
            continue

        seen.add(stripped)

        # ===== PARSE =====
        # 1. Dialogue
        diag_match = dialogue_pattern.match(stripped)
        if diag_match:
            speaker, emotion, content = diag_match.groups()

            entries.append({
                "type": "dialogue",
                "speaker": speaker.strip(),
                "emotion_hint": emotion.strip() if emotion else None,
                "text": content.strip()
            })
            continue

        # 2. Action / Context
        act_match = action_pattern.match(stripped)
        if act_match:
            entries.append({
                "type": "action",
                "text": act_match.group(1).strip()
            })
            continue

        # 3. Gameplay objectives -> skip
        if stripped.startswith((
            "#",
            "Goal:",
            "Objective:"
        )):
            continue

        # 4. Normal text/context
        entries.append({
            "type": "text",
            "text": stripped
        })

    return entries


# ---------------------------------------------------------------------------
# Document cleaning
# ---------------------------------------------------------------------------

def clean_entry_text(text: str) -> str:
    """
    Clean text của từng entry.
    """

    if not text:
        return ""

    text = (
        text.replace("&mdash;", "—")
            .replace("&ndash;", "–")
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )

    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)

    text = re.sub(r"'{2,}", "", text)

    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def clean_document(doc: dict) -> dict:
    cleaned_sections = []
    for section in doc.get("sections", []):
        section_name = section.get("section", "")
        if _is_blocked_section(section_name):
            continue
        entries = section.get("entries", [])
        cleaned_entries = []
        for entry in entries:

            cleaned_text = clean_entry_text(
                entry.get("text", "")
            )
            entry_type = entry.get("type", "text")

            # validate dialogue
            if entry_type == "dialogue":
                if not entry.get("speaker"):
                    continue
            # min words theo type
            MIN_WORDS = {
                "dialogue": 1,
                "action": 2,
                "text": 5
            }

            if len(cleaned_text.split()) < MIN_WORDS.get(entry_type, 3):
                continue

            cleaned_entry = {
                **entry,
                "text": cleaned_text
            }

            cleaned_entries.append(cleaned_entry)

        if not cleaned_entries:
            continue

        cleaned_sections.append({
            "section": section_name,
            "entries": cleaned_entries
        })

    return {
        **doc,
        "sections": cleaned_sections
    }

# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load_documents(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_documents(documents: list[dict], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")

def clean_documents(documents: list[dict]) -> list[dict]:
    return [clean_document(doc) for doc in documents]
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean a document.json file.")
    parser.add_argument("input", nargs="?", default=str(DEFAULT_RAW_DOCUMENT_PATH))
    parser.add_argument("output", nargs="?", default=str(DEFAULT_CLEAN_DOCUMENT_PATH))
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
