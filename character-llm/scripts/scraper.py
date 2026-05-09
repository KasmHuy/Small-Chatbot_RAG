import json
import re
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import requests


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", text.lower().strip()).strip("_")


def scrape_character_wiki(url: str, character_name: str) -> dict:
    """
    Dùng MediaWiki API thay vì scrape HTML → không bị 403.
    URL input vẫn dạng: https://genshin-impact.fandom.com/wiki/Kamisato_Ayaka/Profile
    """
    # Tách base + page title từ URL
    # vd: https://genshin-impact.fandom.com/wiki/Kamisato_Ayaka/Profile
    #  → api_base = https://genshin-impact.fandom.com/api.php
    #  → page_title = Kamisato_Ayaka/Profile
    match = re.match(r"(https?://[^/]+)/wiki/(.+)", url.rstrip("/"))
    if not match:
        raise ValueError(f"Không parse được URL: {url}")

    api_base   = match.group(1) + "/api.php"
    page_title = match.group(2)

    params = {
        "action":  "parse",
        "page":    page_title,
        "prop":    "sections|wikitext",
        "format":  "json",
    }
    headers = {"User-Agent": "CharacterLLM-Scraper/1.0 (educational project)"}

    resp = requests.get(api_base, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"MediaWiki API error: {data['error']}")

    raw_wikitext: str = data["parse"]["wikitext"]["*"]
    api_sections: list = data["parse"]["sections"]  # [{index, line, ...}, ...]

    sections = _parse_wikitext_sections(raw_wikitext, api_sections)

    page_path = url.rstrip("/").split("/wiki/")[-1]
    doc_id = f"wiki_{slugify(page_path)}"

    return {
        "doc_id":    doc_id,
        "source":    url,
        "character": character_name,
        "sections":  sections,
    }


def _clean_wikitext(text: str) -> str:
    """Bỏ wiki markup cơ bản, giữ lại plain text."""
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)  # [[link|label]] → label
    text = re.sub(r"\{\{[^}]+\}\}", "", text)                        # {{template}} → bỏ
    text = re.sub(r"'{2,}", "", text)                                 # bold/italic
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)      # <ref>
    text = re.sub(r"<[^>]+>", "", text)                               # HTML tags
    text = re.sub(r"={2,}[^=]+=+", "", text)                         # section headers
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_wikitext_sections(wikitext: str, api_sections: list) -> list[dict]:
    """
    Dùng section list từ API để split wikitext thành từng phần,
    trả về [{"section": "...", "content": "..."}, ...]
    """
    # Tạo list anchor heading để split
    heading_pattern = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
    matches = list(heading_pattern.finditer(wikitext))

    sections = []

    # Phần trước heading đầu tiên = Introduction
    intro_end = matches[0].start() if matches else len(wikitext)
    intro_text = _clean_wikitext(wikitext[:intro_end])
    if intro_text:
        sections.append({"section": "Introduction", "content": intro_text})

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        content_start = m.end()
        content_end   = matches[i + 1].start() if i + 1 < len(matches) else len(wikitext)
        content = _clean_wikitext(wikitext[content_start:content_end])
        if content:
            sections.append({"section": heading, "content": content})

    return sections

def scrape_voiceover_wiki(url: str, character_name: str) -> dict:
    """
    Dành riêng cho trang Voice-Overs — content nằm trong HTML table.
    Dùng action=parse&prop=text để lấy rendered HTML thay vì wikitext.
    """
    match = re.match(r"(https?://[^/]+)/wiki/(.+)", url.rstrip("/"))
    if not match:
        raise ValueError(f"Không parse được URL: {url}")

    api_base   = match.group(1) + "/api.php"
    page_title = match.group(2)

    params = {
        "action": "parse",
        "page":   page_title,
        "prop":   "text",       # rendered HTML
        "format": "json",
    }
    headers = {"User-Agent": "CharacterLLM-Scraper/1.0 (educational project)"}

    resp = requests.get(api_base, params=params, headers=headers, timeout=15)
    resp.raise_for_status()

    html = resp.json()["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "html.parser")

    sections = _parse_voiceover_tables(soup)

    page_path = url.rstrip("/").split("/wiki/")[-1]
    doc_id = f"wiki_{slugify(page_path)}"

    return {
        "doc_id":    doc_id,
        "source":    url,
        "character": character_name,
        "sections":  sections,
    }


def _parse_voiceover_tables(soup) -> list[dict]:
    sections = []
    SKIP_HEADERS = {"title and requirements", "title", "details"}
    SKIP_TITLES = {"opening treasure chest", "character idles"}
    

    for table in soup.find_all("table")[:2]:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            if cells[0].get("class") != ["hidden"]:
                continue
            
            # ── Clean title ──────────────────────────────
            title = cells[0].get_text(strip=True)
            title = re.sub(r"Friendship Lv\.\s*\d+", "", title)
            title = re.sub(r"Ascension Phase\s*\d+", "", title)
            title = re.sub(r"Stillness,.*", "", title)
            title = re.sub(r"\(Note:.*?\)", "", title)
            title = re.sub(r"\(For English.*?\)", "", title)
            title = re.sub(r"Omnipresence Over Mortals", "", title)
            title = re.sub(r"The Whispers of the Crane and the White Rabbit", "", title)
            title = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", title)  # "AboutThoma" → "About Thoma"
            title = re.sub(r"(?<=\w)(?=the[A-Z])", " ", title)  # "About theVision" → "About the Vision"
            title = re.sub(r":(?=[A-Z])", ": ", title)  # "Ayaka:Yashiro" → "Ayaka: Yashiro"
            title = re.sub(r"\s{2,}", " ", title).strip()
            # ─────────────────────────────────────────────

            if title.lower() in SKIP_HEADERS or not title:
                continue
            if title.lower() in SKIP_TITLES:
                continue

            cell = cells[1]
            for tag in cell.find_all("span", class_=lambda c: c and (
                "audio-button" in c or "hidden" in c or "mobile-only" in c
            )):
                tag.decompose()

            text = cell.get_text(separator=" ", strip=True)
            text = re.sub(r"https?://\S+", "", text)
            text = re.sub(r"Media:VO_\S+", "", text)
            text = re.sub(r"\s{2,}", " ", text).strip()

            # Drop sections quá ngắn (combat lines)
            if title and text and len(text.split()) >= 8:
                sections.append({"section": title, "content": text})

    return sections

def save_document(doc: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        existing = [d for d in existing if d.get("doc_id") != doc["doc_id"]]
        existing.append(doc)
        documents = existing
    else:
        documents = [doc]
    path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {doc['doc_id']} → {output_path}  ({len(doc['sections'])} sections)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", default="../data/raw/document.json")
    parser.add_argument("--character-name", default="Character")
    args = parser.parse_args()
    doc = scrape_character_wiki(args.url, args.character_name)
    save_document(doc, args.output)