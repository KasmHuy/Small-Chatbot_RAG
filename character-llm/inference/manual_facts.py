"""Manual fact loading and alias-based matching for runtime context injection."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def normalize_text(value: str) -> str:
    """Lowercase, remove accents, and normalize separators for matching."""
    normalized = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.replace("_", " ").replace("-", " ")
    return " ".join(stripped.lower().split())


def tokenize(value: str) -> set[str]:
    """Extract simple normalized tokens for lightweight lexical matching."""
    return set(TOKEN_PATTERN.findall(normalize_text(value)))


@dataclass(slots=True)
class ManualFact:
    """Runtime-only canon fact that must not be embedded into the vector store."""

    fact_id: str
    character: str
    category: str
    priority: int
    aliases: tuple[str, ...]
    text: str
    normalized_aliases: tuple[str, ...] = field(init=False, repr=False)
    alias_token_sets: tuple[frozenset[str], ...] = field(init=False, repr=False)
    normalized_character: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        fallback_aliases = self.aliases or (self.category,)
        normalized_aliases = tuple(
            alias for alias in (normalize_text(alias) for alias in fallback_aliases) if alias
        )
        self.normalized_aliases = normalized_aliases
        self.alias_token_sets = tuple(frozenset(tokenize(alias)) for alias in normalized_aliases)
        self.normalized_character = normalize_text(self.character)

    @classmethod
    def from_payload(cls, payload: dict) -> "ManualFact":
        fact_id = str(payload.get("fact_id", "")).strip()
        text = str(payload.get("text", "")).strip()
        if not fact_id:
            raise ValueError("missing required field: fact_id")
        if not text:
            raise ValueError("missing required field: text")

        aliases = payload.get("aliases", [])
        if aliases is None:
            aliases = []
        if not isinstance(aliases, list):
            raise ValueError("aliases must be a list of strings")

        return cls(
            fact_id=fact_id,
            character=str(payload.get("character", "")).strip(),
            category=str(payload.get("category", "general")).strip() or "general",
            priority=int(payload.get("priority", 0)),
            aliases=tuple(str(alias).strip() for alias in aliases if str(alias).strip()),
            text=text,
        )


@dataclass(slots=True)
class ManualFactMatch:
    """Matched fact plus its lightweight alias score for sorting/debugging."""

    fact: ManualFact
    match_score: int
    alias_hits: tuple[str, ...]


class ManualFactStore:
    """Small in-memory fact store loaded from ``data/manual_facts``."""

    def __init__(self, facts: Iterable[ManualFact]):
        self.facts = list(facts)

    @classmethod
    def from_directory(cls, directory: Path) -> "ManualFactStore":
        if not directory.exists():
            return cls([])

        facts: list[ManualFact] = []
        for path in sorted(directory.rglob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"[WARN] Skipping invalid manual fact file {path}: {exc}")
                continue

            raw_facts = payload if isinstance(payload, list) else [payload]
            for index, raw_fact in enumerate(raw_facts):
                if not isinstance(raw_fact, dict):
                    print(
                        f"[WARN] Skipping invalid manual fact entry {path}#{index}: "
                        "expected a JSON object."
                    )
                    continue

                try:
                    facts.append(ManualFact.from_payload(raw_fact))
                except ValueError as exc:
                    print(f"[WARN] Skipping invalid manual fact entry {path}#{index}: {exc}")

        return cls(facts)

    def match(
        self,
        query: str,
        expanded_terms: Iterable[str] = (),
        *,
        character_name: str | None = None,
        limit: int | None = None,
    ) -> list[ManualFactMatch]:
        normalized_query = normalize_text(query)
        search_strings = {normalized_query}
        query_terms = {token for token in tokenize(query) if len(token) >= 3}

        for term in expanded_terms:
            normalized_term = normalize_text(term)
            if not normalized_term:
                continue
            search_strings.add(normalized_term)
            query_terms.update(token for token in tokenize(term) if len(token) >= 3)

        normalized_character = normalize_text(character_name or "")
        matches: list[ManualFactMatch] = []

        for fact in self.facts:
            if normalized_character and fact.normalized_character:
                if fact.normalized_character != normalized_character:
                    continue

            match_score = 0
            alias_hits: list[str] = []

            for alias, normalized_alias, alias_tokens in zip(
                fact.aliases or (fact.category,),
                fact.normalized_aliases,
                fact.alias_token_sets,
            ):
                if not normalized_alias:
                    continue

                if any(normalized_alias in value for value in search_strings):
                    match_score += 3 if " " in normalized_alias else 2
                    alias_hits.append(alias)
                    continue

                if alias_tokens and alias_tokens.issubset(query_terms):
                    match_score += 2
                    alias_hits.append(alias)
                    continue

                if alias_tokens and alias_tokens.intersection(query_terms):
                    match_score += 1
                    alias_hits.append(alias)

            if match_score:
                matches.append(
                    ManualFactMatch(
                        fact=fact,
                        match_score=match_score,
                        alias_hits=tuple(dict.fromkeys(alias_hits)),
                    )
                )

        matches.sort(
            key=lambda item: (
                -item.fact.priority,
                -item.match_score,
                item.fact.fact_id,
            )
        )

        if limit is not None:
            return matches[:limit]
        return matches


def format_matches_for_context(matches: Iterable[ManualFactMatch]) -> str:
    """Render matched facts into a prompt-ready canon block."""
    items = list(matches)
    if not items:
        return ""

    lines = ["=== MANUAL CANON FACTS ==="]
    for match in items:
        label = match.fact.category.strip() or "canon"
        lines.append(f"- [{label}] {match.fact.text}")
    return "\n".join(lines)
