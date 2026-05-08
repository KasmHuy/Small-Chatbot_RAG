"""Scrape character knowledge from fandom wiki pages."""

import requests
from bs4 import BeautifulSoup


def scrape_character_wiki(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text_blocks = [p.get_text(strip=True) for p in soup.find_all("p")]
    return "\n\n".join(text_blocks)


def save_raw_text(output_path: str, text: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape a fandom wiki page and save raw text.")
    parser.add_argument("url", help="Fandom wiki page URL")
    parser.add_argument("output", default="../data/raw/character_wiki.txt", help="Output raw text file path")
    args = parser.parse_args()

    raw_text = scrape_character_wiki(args.url)
    save_raw_text(args.output, raw_text)
