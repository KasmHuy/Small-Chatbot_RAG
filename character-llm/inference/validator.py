"""Post-generation validator with hard, soft, and style checks."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

try:
    from manual_facts import ManualFactMatch, ManualFactStore, normalize_text, tokenize
except ImportError:  # pragma: no cover - fallback for package-style imports
    from .manual_facts import ManualFactMatch, ManualFactStore, normalize_text, tokenize


REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL_FACTS_PATH = REPO_ROOT / "data" / "manual_facts"

HARD_FALLBACK = "Tôi không tiện nói về điều này."
SOFT_FALLBACK = "Chuyện ấy, tôi nghĩ mình không nên nói quá chắc khi bối cảnh chưa cho thấy rõ."
STYLE_FALLBACK = "Nếu bạn muốn, bạn có thể nói rõ hơn với tôi."

HARD_VALIDATION_AREAS = ("family", "titles", "organizations", "timeline", "death_state")
SOFT_VALIDATION_AREAS = ("hobbies", "feelings", "daily_life", "social_tone")
STYLE_VALIDATION_AREAS = ("no_wiki_dump", "no_metadata_dump", "no_omniscient_narration")

RELATION_PATTERNS = {
    "father": (
        "cha",
        "bo",
    ),
    "mother": (
        "me",
    ),
    "older_brother": (
        "anh trai",
        "nguoi anh trai",
    ),
    "younger_brother": (
        "em trai",
    ),
    "older_sister": (
        "chi gai",
        "nguoi chi gai",
    ),
    "younger_sister": (
        "em gai",
    ),
}

RELATION_LABELS_VI = {
    "father": "cha của",
    "mother": "mẹ của",
    "older_brother": "anh trai của",
    "younger_brother": "em trai của",
    "older_sister": "chị gái của",
    "younger_sister": "em gái của",
}

INVERSE_RELATIONS = {
    "older_brother": "younger_sister",
    "younger_sister": "older_brother",
    "older_sister": "younger_brother",
    "younger_brother": "older_sister",
}

DEFAULT_CANON_RELATIONS = {
    ("kamisato ayato", "kamisato ayaka"): "older_brother",
    ("kamisato ayaka", "kamisato ayato"): "younger_sister",
    ("kamisato kayo", "kamisato ayaka"): "mother",
}

FACT_RELATION_PATTERNS = {
    "father": (
        r"(?P<subject>[a-z' ]+?) is the father of (?P<object>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<subject>[a-z' ]+?), (?P<object>[a-z' ]+?)'s father(?:[.,]| is )",
    ),
    "mother": (
        r"(?P<subject>[a-z' ]+?) is the mother of (?P<object>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<subject>[a-z' ]+?), (?P<object>[a-z' ]+?)'s mother(?:[.,]| is )",
    ),
    "older_brother": (
        r"(?P<subject>[a-z' ]+?) is the older brother of (?P<object>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<subject>[a-z' ]+?) is the elder brother of (?P<object>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<object>[a-z' ]+?)'s older brother(?: is)? (?P<subject>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<object>[a-z' ]+?)'s elder brother(?: is)? (?P<subject>[a-z' ]+?)(?:[.,]|$)",
    ),
    "younger_brother": (
        r"(?P<subject>[a-z' ]+?) is the younger brother of (?P<object>[a-z' ]+?)(?:[.,]|$)",
    ),
    "older_sister": (
        r"(?P<subject>[a-z' ]+?) is the older sister of (?P<object>[a-z' ]+?)(?:[.,]|$)",
        r"(?P<object>[a-z' ]+?)'s older sister(?: is)? (?P<subject>[a-z' ]+?)(?:[.,]|$)",
    ),
    "younger_sister": (
        r"(?P<subject>[a-z' ]+?) is the younger sister of (?P<object>[a-z' ]+?)(?:[.,]|$)",
    ),
}

RELATION_QUERY_HINTS = (
    "gia dinh",
    "family",
    "relation",
    "quan he",
    "anh trai",
    "chi gai",
    "em trai",
    "em gai",
    "brother",
    "sister",
    "mother",
    "father",
    "me",
    "bo",
    "cha",
)

PREFERENCE_QUERY_HINTS = (
    "thich",
    "so thich",
    "hobby",
    "favorite",
    "food",
    "cuisine",
    "mon an",
    "khau vi",
    "prefer",
    "enjoy",
)

PREFERENCE_SENTENCE_HINTS = (
    " thich ",
    " yeu thich ",
    " ua ",
    " ghet ",
    " khong thich ",
    " quan tam den ",
    " ham mo ",
    " prefer ",
    " like ",
    " likes ",
    " enjoy ",
    " enjoys ",
    " interested in ",
)

POSITIVE_PREFERENCE_MARKERS = (
    "thich",
    "yeu thich",
    "ua",
    "quan tam den",
    "ham mo",
    "favorite",
    "prefer",
    "prefers",
    "like",
    "likes",
    "enjoy",
    "enjoys",
    "interested in",
    "interested",
)

NEGATIVE_PREFERENCE_MARKERS = (
    "khong thich",
    "ghet",
    "dislike",
    "dislikes",
    "difficult to accept",
    "hard to accept",
    "cannot accept",
)

PREFERENCE_HEDGE_MARKERS = (
    "co le",
    "hinh nhu",
    "toi nghi",
    "minh nghi",
    "phai chang",
    "doi khi",
    "it nhieu",
)

PREFERENCE_CATEGORIES = {
    "hobby",
    "food",
    "preference",
    "daily_life",
    "personality",
    "childhood",
    "philosophy",
    "skill",
}

PREFERENCE_STOPWORDS = {
    "toi",
    "ta",
    "minh",
    "ayaka",
    "kamisato",
    "la",
    "rat",
    "mot",
    "nhung",
    "cac",
    "va",
    "hay",
    "that",
    "this",
    "very",
    "favorite",
    "prefer",
    "prefers",
    "enjoy",
    "enjoys",
    "like",
    "likes",
    "interested",
    "thich",
    "yeu",
    "ua",
}

PREFERENCE_CONCEPT_ALIASES = {
    "ochazuke": {"ochazuke"},
    "foreign_cuisine": {
        "foreign cuisine",
        "foreign food",
        "cuisine from all over the world",
        "am thuc nuoc ngoai",
        "mon nuoc ngoai",
        "do an nuoc ngoai",
    },
    "gagaku_music": {"gagaku", "gagaku music", "nha nhac gagaku"},
    "poetry_art": {"poetry", "tho", "tho ca"},
    "game_of_go": {"the game of go", "game of go", "go game", "co vay", "ban co"},
    "dance_art": {"dance", "mua", "vu dao"},
    "animal_fats": {"animal fat", "animal fats", "mo dong vat", "chat beo dong vat"},
    "offal_food": {"offal", "noi tang", "long"},
    "wind_feeling": {"feeling the wind", "the wind", "gio"},
    "dance_fans": {"dance fan", "dance fans", "quat mua"},
    "tea_ceremony_fans": {"tea ceremony fan", "tea ceremony fans", "quat tra dao"},
    "temari_ball": {"temari", "tokomaru", "temari ball"},
}

SECOND_PERSON_TOKENS = ("ban", "anh", "chi", "ngai", "cau")
INNER_STATE_TERMS = (
    "buon",
    "dau",
    "met moi",
    "co don",
    "lo lang",
    "so hai",
    "that vong",
    "boi roi",
    "toi te",
    "khoc",
    "trong long",
    "sau tham tam",
    "noi long",
)
OMNISCIENT_PATTERNS = (
    r"\b(?:toi|ta)\s+(?:biet|hieu|nhin ra|cam thay)\s+r(?:a)?ng\s+(?:ban|anh|chi|ngai)\b",
    r"\b(?:toi|ta)\s+(?:biet|hieu|nhin ra|cam thay)\s+(?:trong long|noi long|sau tham tam)\s+(?:ban|anh|chi|ngai)\b",
    r"\b(?:trong long|sau tham tam|noi long)\s+(?:ban|anh|chi|ngai)\b",
    r"\b(?:ban|anh|chi|ngai)\s+(?:dang|han la|chac han)\s+(?:buon|dau|met moi|co don|lo lang|so hai|that vong|boi roi)\b",
)

METADATA_LABELS = (
    "quan he:",
    "gioi tinh:",
    "vai tro:",
    "chuc vu:",
    "organization:",
    "title:",
    "fact_id",
    "manual canon facts",
    "retrieved lore",
)

CAPITALIZED_NAME_PATTERN = re.compile(r"\b[A-Z][A-Za-z']+(?: [A-Z][A-Za-z']+){0,2}\b")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass(slots=True)
class ValidationIssue:
    """Single validator finding."""

    kind: str
    severity: str
    detail: str
    sentence: str
    rewrite_hint: str


@dataclass(slots=True)
class ValidationResult:
    """Validation output plus rewrite hints."""

    text: str
    issues: tuple[ValidationIssue, ...] = ()
    corrected_sentences: tuple[str, ...] = ()

    @property
    def hard_issues(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "hard")

    @property
    def soft_issues(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "soft")

    @property
    def style_issues(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "style")

    @property
    def should_regenerate(self) -> bool:
        return bool(self.issues)

    @property
    def issue_report(self) -> str:
        return build_issue_report(self.issues)


@dataclass(slots=True)
class RelationClaim:
    """Structured relation claim extracted from reply text."""

    subject: str
    object: str
    relation: str
    sentence: str


@dataclass(slots=True)
class EvidenceSentence:
    """Small canon evidence unit for soft validation."""

    text: str
    normalized_text: str
    category: str
    polarity: str


def literal_pattern(text: str) -> str:
    """Escape literal text while keeping whitespace flexible."""
    return re.escape(text).replace(r"\ ", r"\s+")


def split_sentences(text: str) -> list[str]:
    """Split reply into small validation units."""
    return [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(text or "") if part.strip()]


def normalize_name(value: str) -> str:
    """Normalize names but keep apostrophes for English facts."""
    return re.sub(r"[^\w\s']+", "", normalize_text(value)).strip()


def normalize_entity_fragment(value: str) -> str:
    """Trim noisy suffixes around captured entity text."""
    cleaned = normalize_name(value)
    cleaned = re.sub(r"\b(cua toi|cua minh|cua ta|toi|minh|ta)\b", "", cleaned).strip()
    cleaned = re.sub(r"\b(la|mot|nguoi)\b$", "", cleaned).strip()
    return " ".join(cleaned.split())


def relation_prompt_hint(question: str) -> bool:
    """Detect hard family questions."""
    normalized_question = f" {normalize_text(question)} "
    return any(f" {hint} " in normalized_question for hint in RELATION_QUERY_HINTS)


def preference_prompt_hint(question: str) -> bool:
    """Detect preference / hobby questions."""
    normalized_question = f" {normalize_text(question)} "
    return any(f" {hint} " in normalized_question for hint in PREFERENCE_QUERY_HINTS)


def preference_sentence_hint(sentence: str) -> bool:
    """Detect preference assertion in assistant reply."""
    normalized_sentence = f" {normalize_text(sentence)} "
    return any(marker in normalized_sentence for marker in PREFERENCE_SENTENCE_HINTS)


def get_preference_polarity(text: str) -> str:
    """Classify a preference sentence polarity."""
    normalized = normalize_text(text)
    if any(marker in normalized for marker in NEGATIVE_PREFERENCE_MARKERS):
        return "negative"
    if any(marker in normalized for marker in POSITIVE_PREFERENCE_MARKERS):
        return "positive"
    return "neutral"


def has_preference_hedge(text: str) -> bool:
    """Allow softer, non-committal wording to pass more easily."""
    normalized = normalize_text(text)
    return any(marker in normalized for marker in PREFERENCE_HEDGE_MARKERS)


def canonicalize_preference_text(text: str) -> str:
    """Map bilingual preference phrases to stable concept tokens."""
    normalized = normalize_text(text)
    enriched = normalized
    for concept, aliases in PREFERENCE_CONCEPT_ALIASES.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            enriched = f"{enriched} {concept}"
    return enriched


def distinctive_tokens(text: str) -> set[str]:
    """Extract content tokens that should be grounded in canon."""
    return {
        token
        for token in tokenize(canonicalize_preference_text(text))
        if len(token) >= 3 and token not in PREFERENCE_STOPWORDS
    }


@lru_cache(maxsize=1)
def load_manual_fact_store() -> ManualFactStore:
    """Load runtime facts without touching vector DB contents."""
    return ManualFactStore.from_directory(MANUAL_FACTS_PATH)


def iter_fact_texts(
    manual_matches: Iterable[ManualFactMatch] = (),
    vector_chunks: Iterable[Any] = (),
) -> Iterable[tuple[str, str]]:
    """Yield unique canon texts plus a light category label."""
    seen: set[tuple[str, str]] = set()

    for match in manual_matches:
        payload = (match.fact.text, match.fact.category)
        if payload not in seen and match.fact.text:
            seen.add(payload)
            yield payload

    for fact in load_manual_fact_store().facts:
        payload = (fact.text, fact.category)
        if payload not in seen and fact.text:
            seen.add(payload)
            yield payload

    for chunk in vector_chunks:
        text = getattr(chunk, "text", "") or ""
        category = getattr(chunk, "section_bucket", "") or getattr(chunk, "section", "") or "vector"
        payload = (text, category)
        if payload not in seen and text:
            seen.add(payload)
            yield payload


def extract_named_entities(text: str) -> set[str]:
    """Collect capitalized names from canon evidence."""
    return {match.group(0).strip() for match in CAPITALIZED_NAME_PATTERN.finditer(text or "")}


def _prefer_display_name(current: str | None, candidate: str) -> str:
    """Prefer fuller names over shorter aliases."""
    if not current:
        return candidate
    if len(candidate.split()) > len(current.split()):
        return candidate
    if len(candidate) > len(current):
        return candidate
    return current


def build_entity_registry(
    *,
    character_name: str | None = None,
    manual_matches: Iterable[ManualFactMatch] = (),
    vector_chunks: Iterable[Any] = (),
) -> tuple[dict[str, str], dict[str, str]]:
    """Build alias-to-canonical and canonical-to-display maps."""
    alias_to_canonical: dict[str, str] = {}
    display_names: dict[str, str] = {}

    def register(alias: str, canonical: str) -> None:
        normalized_alias = normalize_name(alias)
        normalized_canonical = normalize_name(canonical)
        if len(normalized_alias) < 2 or len(normalized_canonical) < 2:
            return

        current_canonical = alias_to_canonical.get(normalized_alias)
        current_display = display_names.get(current_canonical, "") if current_canonical else ""
        candidate_display = canonical.strip()

        if current_canonical and current_canonical != normalized_canonical:
            if len(candidate_display.split()) < len(current_display.split()):
                return
            if len(candidate_display) < len(current_display):
                return

        alias_to_canonical[normalized_alias] = normalized_canonical
        display_names[normalized_canonical] = _prefer_display_name(
            display_names.get(normalized_canonical),
            candidate_display,
        )

    if character_name:
        register(character_name, character_name)

    for fact in load_manual_fact_store().facts:
        if fact.character:
            register(fact.character, fact.character)
            register(fact.character.split()[-1], fact.character)

        for entity in extract_named_entities(fact.text):
            register(entity, entity)
            if " " in entity:
                register(entity.split()[-1], entity)

    for match in manual_matches:
        if match.fact.character:
            register(match.fact.character, match.fact.character)
        for entity in extract_named_entities(match.fact.text):
            register(entity, entity)
            if " " in entity:
                register(entity.split()[-1], entity)

    for chunk in vector_chunks:
        for entity in extract_named_entities(getattr(chunk, "text", "")):
            register(entity, entity)
            if " " in entity:
                register(entity.split()[-1], entity)

    if character_name:
        for alias in ("toi", "ta", "minh", "tui", "ta day"):
            register(alias, character_name)

    for canonical, display_name in list(display_names.items()):
        short_name = display_name.split()[-1]
        for prefix in ("anh", "chi", "em", "co", "me", "bo", "cha"):
            register(f"{prefix} {short_name}", display_name)

    return alias_to_canonical, display_names


def resolve_entity(value: str, alias_to_canonical: dict[str, str]) -> str | None:
    """Resolve a free-form entity string into canonical normalized form."""
    normalized_value = normalize_name(value)
    if not normalized_value:
        return None
    if normalized_value in alias_to_canonical:
        return alias_to_canonical[normalized_value]
    for alias, canonical in alias_to_canonical.items():
        if normalized_value.endswith(alias) or alias.endswith(normalized_value):
            return canonical
    return None


def build_canon_relation_map(
    *,
    character_name: str | None = None,
    manual_matches: Iterable[ManualFactMatch] = (),
    vector_chunks: Iterable[Any] = (),
) -> tuple[dict[tuple[str, str], str], dict[str, str]]:
    """Build canonical relation map from defaults, manual facts, and retrieval."""
    alias_to_canonical, display_names = build_entity_registry(
        character_name=character_name,
        manual_matches=manual_matches,
        vector_chunks=vector_chunks,
    )
    canon_relations = dict(DEFAULT_CANON_RELATIONS)

    for raw_text, _category in iter_fact_texts(
        manual_matches=manual_matches,
        vector_chunks=vector_chunks,
    ):
        normalized_text = normalize_text(raw_text)
        for relation, patterns in FACT_RELATION_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, normalized_text):
                    subject = resolve_entity(match.group("subject"), alias_to_canonical)
                    object_name = resolve_entity(match.group("object"), alias_to_canonical)
                    if not subject or not object_name or subject == object_name:
                        continue
                    canon_relations[(subject, object_name)] = relation
                    inverse = INVERSE_RELATIONS.get(relation)
                    if inverse and (object_name, subject) not in canon_relations:
                        canon_relations[(object_name, subject)] = inverse

    return canon_relations, display_names


def extract_relation_claims(
    text: str,
    alias_to_canonical: dict[str, str],
) -> list[RelationClaim]:
    """Extract Vietnamese relation claims, including sibling ordering."""
    claims: list[RelationClaim] = []
    seen: set[tuple[str, str, str, str]] = set()

    for sentence in split_sentences(text):
        normalized_sentence = normalize_text(sentence)
        for relation, phrases in RELATION_PATTERNS.items():
            for phrase in phrases:
                phrase_pattern = literal_pattern(phrase)
                patterns = (
                    rf"(?P<subject>[a-z0-9' ]+?)\s+la\s+{phrase_pattern}\s+cua\s+(?P<object>[a-z0-9' ]+?)(?:[.!?,]|$)",
                    rf"{phrase_pattern}\s+cua\s+(?P<object>[a-z0-9' ]+?)\s+la\s+(?P<subject>[a-z0-9' ]+?)(?:[.!?,]|$)",
                    rf"(?P<object>[a-z0-9' ]+?)\s+co\s+(?P<subject>[a-z0-9' ]+?)\s+la\s+{phrase_pattern}(?:[.!?,]|$)",
                    rf"(?P<subject>[a-z0-9' ]+?)\s+la\s+{phrase_pattern}\s+(?P<object_pronoun>toi|minh|ta)(?:[.!?,]|$)",
                    rf"{phrase_pattern}\s+(?P<object_pronoun>toi|minh|ta)\s+la\s+(?P<subject>[a-z0-9' ]+?)(?:[.!?,]|$)",
                )

                for pattern in patterns:
                    for match in re.finditer(pattern, normalized_sentence):
                        raw_subject = normalize_entity_fragment(match.group("subject"))
                        if match.groupdict().get("object_pronoun"):
                            raw_object = match.groupdict()["object_pronoun"]
                        else:
                            raw_object = normalize_entity_fragment(match.groupdict().get("object") or "")
                        if not raw_subject or not raw_object or raw_subject == raw_object:
                            continue

                        subject = resolve_entity(raw_subject, alias_to_canonical) or raw_subject
                        object_name = resolve_entity(raw_object, alias_to_canonical) or raw_object
                        key = (subject, object_name, relation, normalized_sentence)
                        if key in seen:
                            continue

                        seen.add(key)
                        claims.append(
                            RelationClaim(
                                subject=subject,
                                object=object_name,
                                relation=relation,
                                sentence=sentence,
                            )
                        )

    return claims


def build_relation_correction(
    claim: RelationClaim,
    canonical_relation: str,
    display_names: dict[str, str],
) -> str:
    """Render a deterministic canon relation correction."""
    subject = display_names.get(claim.subject, claim.subject.title())
    object_name = display_names.get(claim.object, claim.object.title())
    label = RELATION_LABELS_VI[canonical_relation]
    return f"{subject} là {label} {object_name}."


def build_preference_evidence(
    manual_matches: Iterable[ManualFactMatch] = (),
    vector_chunks: Iterable[Any] = (),
) -> list[EvidenceSentence]:
    """Collect canon evidence for soft preference validation."""
    evidence: list[EvidenceSentence] = []
    seen: set[str] = set()

    for match in manual_matches:
        if match.fact.category not in PREFERENCE_CATEGORIES:
            continue
        normalized_fact = normalize_text(match.fact.text)
        if normalized_fact and normalized_fact not in seen:
            seen.add(normalized_fact)
            evidence.append(
                EvidenceSentence(
                    text=match.fact.text,
                    normalized_text=normalized_fact,
                    category=match.fact.category,
                    polarity=get_preference_polarity(match.fact.text),
                )
            )

    for fact in load_manual_fact_store().facts:
        if fact.category not in PREFERENCE_CATEGORIES:
            continue
        normalized_fact = normalize_text(fact.text)
        if normalized_fact and normalized_fact not in seen:
            seen.add(normalized_fact)
            evidence.append(
                EvidenceSentence(
                    text=fact.text,
                    normalized_text=normalized_fact,
                    category=fact.category,
                    polarity=get_preference_polarity(fact.text),
                )
            )

    for chunk in vector_chunks:
        for sentence in split_sentences(getattr(chunk, "text", "")):
            normalized_chunk_sentence = normalize_text(sentence)
            if not normalized_chunk_sentence or normalized_chunk_sentence in seen:
                continue
            if not any(token in normalized_chunk_sentence for token in ("like", "likes", "enjoy", "prefer")):
                continue
            seen.add(normalized_chunk_sentence)
            evidence.append(
                EvidenceSentence(
                    text=sentence,
                    normalized_text=normalized_chunk_sentence,
                    category=getattr(chunk, "section_bucket", "") or getattr(chunk, "section", ""),
                    polarity=get_preference_polarity(sentence),
                )
            )

    return evidence


def cosine_similarity_against(query: str, candidates: list[str]) -> list[float]:
    """Use retrieval embed model if it is already loaded in-process."""
    if not candidates:
        return []

    try:
        retrieval_module = sys.modules.get("retrieval")
        if retrieval_module is None:
            retrieval_module = next(
                (
                    module
                    for name, module in sys.modules.items()
                    if name.endswith(".retrieval") and hasattr(module, "EMBED_MODEL")
                ),
                None,
            )
        if retrieval_module is None:
            return [0.0 for _ in candidates]

        embed_model = getattr(retrieval_module, "EMBED_MODEL", None)
        if embed_model is None:
            return [0.0 for _ in candidates]

        embeddings = embed_model.encode([query, *candidates], normalize_embeddings=True)
        query_vector = embeddings[0]
        return [float(query_vector @ candidate_vector) for candidate_vector in embeddings[1:]]
    except Exception:
        return [0.0 for _ in candidates]


def preference_sentence_supported(
    sentence: str,
    evidence_sentences: list[EvidenceSentence],
) -> bool:
    """Soft support check for personal preferences."""
    if not evidence_sentences:
        return False
    if has_preference_hedge(sentence):
        return True

    sentence_polarity = get_preference_polarity(sentence)
    content_tokens = distinctive_tokens(sentence)
    if not content_tokens:
        return True

    candidate_texts = [item.text for item in evidence_sentences]
    similarities = cosine_similarity_against(sentence, candidate_texts)
    best_same = 0.0
    best_opposite = 0.0

    for item, similarity in zip(evidence_sentences, similarities):
        same_polarity = (
            sentence_polarity == "neutral"
            or item.polarity == "neutral"
            or sentence_polarity == item.polarity
        )
        overlap = content_tokens.intersection(distinctive_tokens(item.text))
        concept_support = any(token == "ochazuke" or "_" in token for token in overlap)

        if same_polarity and (concept_support or len(overlap) >= 2):
            return True
        if not same_polarity and (concept_support or len(overlap) >= 2):
            best_opposite = max(best_opposite, 0.6)

        score = similarity + (0.05 if overlap else 0.0)
        if same_polarity:
            best_same = max(best_same, score)
        else:
            best_opposite = max(best_opposite, score)

    if best_same >= 0.52 and best_same >= best_opposite:
        return True
    if best_same >= 0.44 and len(content_tokens) <= 2 and best_opposite < 0.38:
        return True
    return False


def is_omniscient_user_narration(sentence: str) -> bool:
    """Detect narration that claims the user's hidden inner state."""
    normalized_sentence = normalize_text(sentence)
    if "?" in sentence or normalized_sentence.startswith("neu "):
        return False
    if "co le" in normalized_sentence or "duong nhu" in normalized_sentence:
        return False
    if not any(token in normalized_sentence for token in SECOND_PERSON_TOKENS):
        return False
    if not any(term in normalized_sentence for term in INNER_STATE_TERMS):
        return False
    return any(re.search(pattern, normalized_sentence) for pattern in OMNISCIENT_PATTERNS)


def is_metadata_dump(reply: str) -> bool:
    """Detect wiki / metadata style output."""
    lines = [line.strip() for line in (reply or "").splitlines() if line.strip()]
    bullet_lines = [
        line
        for line in lines
        if line.startswith("- ")
        or line.startswith("* ")
        or re.match(r"^\d+\.\s", line)
    ]
    normalized_reply = normalize_text(reply)
    if len(bullet_lines) >= 2:
        return True
    return any(label in normalized_reply for label in METADATA_LABELS)


def build_issue_report(issues: Iterable[ValidationIssue]) -> str:
    """Format validator findings into a concise rewrite brief."""
    items = list(issues)
    if not items:
        return ""

    lines = [
        "Rewrite the previous draft once.",
        "Keep Ayaka natural, gentle, and in-character.",
        "Do not add any unsupported lore.",
        "Fix these issues:",
    ]

    seen: set[tuple[str, str, str]] = set()
    for issue in items:
        key = (issue.severity, issue.kind, issue.rewrite_hint)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {issue.severity.upper()}: {issue.rewrite_hint}")

    lines.extend(
        [
            "Rules for the rewrite:",
            "- Preserve supported facts already present.",
            "- Hard facts must stay explicit and canon-grounded.",
            "- Soft facts may stay gentle or non-committal instead of overly blunt refusal.",
            "- Never narrate the user's hidden thoughts or feelings.",
            "- Return only the revised answer.",
        ]
    )
    return "\n".join(lines)


def remove_issue_sentences(text: str, issues: Iterable[ValidationIssue]) -> str:
    """Drop sentences flagged by style/soft issues and keep the rest."""
    offending = {normalize_text(issue.sentence) for issue in issues if issue.sentence}
    kept = [
        sentence
        for sentence in split_sentences(text)
        if normalize_text(sentence) not in offending
    ]
    return " ".join(kept).strip()


def merge_with_corrections(
    text: str,
    issues: Iterable[ValidationIssue],
    corrected_sentences: Iterable[str],
) -> str:
    """Remove offending hard-relation sentences and insert deterministic corrections."""
    kept = remove_issue_sentences(text, issues)
    corrections = [sentence.strip() for sentence in corrected_sentences if sentence.strip()]
    parts = [part for part in [kept, " ".join(corrections).strip()] if part]
    return " ".join(parts).strip()


def validation_penalty(result: ValidationResult) -> int:
    """Rank candidates so regenerated drafts can be compared with originals."""
    return (len(result.hard_issues) * 100) + (len(result.style_issues) * 10) + len(result.soft_issues)


def resolve_validation_outcome(
    result: ValidationResult,
    *,
    question: str,
    factual: bool = False,
) -> str:
    """Choose final output after at most one regeneration attempt."""
    if not result.issues:
        return result.text.strip() or HARD_FALLBACK

    if result.hard_issues:
        only_relation_mismatch = all(issue.kind == "relation_mismatch" for issue in result.hard_issues)
        if only_relation_mismatch and result.corrected_sentences:
            corrected = merge_with_corrections(result.text, result.hard_issues, result.corrected_sentences)
            if corrected:
                return corrected
        return HARD_FALLBACK

    if result.style_issues:
        if any(issue.kind == "metadata_dump" for issue in result.style_issues):
            return STYLE_FALLBACK
        sanitized = remove_issue_sentences(result.text, result.style_issues)
        if sanitized:
            return sanitized
        return STYLE_FALLBACK

    if result.soft_issues:
        sanitized = remove_issue_sentences(result.text, result.soft_issues)
        if sanitized:
            return sanitized
        if factual or preference_prompt_hint(question):
            return SOFT_FALLBACK

    return result.text.strip() or HARD_FALLBACK


def validate_generated_reply(
    question: str,
    reply: str,
    *,
    character_name: str | None = None,
    factual: bool = False,
    manual_matches: Iterable[ManualFactMatch] = (),
    vector_chunks: Iterable[Any] = (),
    context_text: str = "",
) -> ValidationResult:
    """Validate reply using hard, soft, and style checks."""
    stripped_reply = (reply or "").strip()
    if not stripped_reply:
        return ValidationResult(
            text=HARD_FALLBACK,
            issues=(
                ValidationIssue(
                    kind="empty_response",
                    severity="hard",
                    detail="Model returned an empty response.",
                    sentence="",
                    rewrite_hint="Return a complete reply instead of an empty draft.",
                ),
            ),
        )

    canon_relations, display_names = build_canon_relation_map(
        character_name=character_name,
        manual_matches=manual_matches,
        vector_chunks=vector_chunks,
    )
    alias_to_canonical, _ = build_entity_registry(
        character_name=character_name,
        manual_matches=manual_matches,
        vector_chunks=vector_chunks,
    )

    issues: list[ValidationIssue] = []
    corrected_sentences: list[str] = []
    seen_corrections: set[str] = set()

    relation_claims = extract_relation_claims(stripped_reply, alias_to_canonical)
    for claim in relation_claims:
        canonical_relation = canon_relations.get((claim.subject, claim.object))
        if canonical_relation is None:
            issues.append(
                ValidationIssue(
                    kind="unsupported_relation",
                    severity="hard",
                    detail="Generated a family relation without canon evidence.",
                    sentence=claim.sentence,
                    rewrite_hint=(
                        "Do not infer or invent family hierarchy. Only state a relation if it is explicit "
                        "in canon context."
                    ),
                )
            )
            continue

        if canonical_relation != claim.relation:
            correction = build_relation_correction(claim, canonical_relation, display_names)
            if correction not in seen_corrections:
                seen_corrections.add(correction)
                corrected_sentences.append(correction)
            issues.append(
                ValidationIssue(
                    kind="relation_mismatch",
                    severity="hard",
                    detail=(
                        f"Expected {canonical_relation} for {claim.subject} -> {claim.object}, "
                        f"but got {claim.relation}."
                    ),
                    sentence=claim.sentence,
                    rewrite_hint=(
                        "Use the canon-supported family relation and remove any inferred sibling ordering "
                        "or family nuance that is not explicit."
                    ),
                )
            )

    should_validate_preferences = preference_prompt_hint(question) or any(
        preference_sentence_hint(sentence) for sentence in split_sentences(stripped_reply)
    )
    if should_validate_preferences:
        preference_evidence = build_preference_evidence(
            manual_matches=manual_matches,
            vector_chunks=vector_chunks,
        )
        for sentence in split_sentences(stripped_reply):
            if not preference_sentence_hint(sentence):
                continue
            if has_preference_hedge(sentence):
                continue
            if not preference_sentence_supported(sentence, preference_evidence):
                issues.append(
                    ValidationIssue(
                        kind="unsupported_preference",
                        severity="soft",
                        detail="Generated a personal preference without canon support.",
                        sentence=sentence,
                        rewrite_hint=(
                            "Do not assert unsupported hobbies or personal tastes. Either keep only supported "
                            "preferences or answer more gently without sounding absolute."
                        ),
                    )
                )

    for sentence in split_sentences(stripped_reply):
        if is_omniscient_user_narration(sentence):
            issues.append(
                ValidationIssue(
                    kind="omniscient_user_state",
                    severity="style",
                    detail="Narrated the user's hidden inner state.",
                    sentence=sentence,
                    rewrite_hint=(
                        "Do not narrate the user's hidden thoughts or feelings. Stay with what Ayaka can "
                        "directly observe, or invite the user to share more."
                    ),
                )
            )

    if is_metadata_dump(stripped_reply):
        issues.append(
            ValidationIssue(
                kind="metadata_dump",
                severity="style",
                detail="Reply sounds like wiki or metadata output.",
                sentence=stripped_reply,
                rewrite_hint=(
                    "Rewrite as natural dialogue. No wiki dump, no metadata labels, and no bullet-style "
                    "character sheet."
                ),
            )
        )

    return ValidationResult(
        text=stripped_reply,
        issues=tuple(issues),
        corrected_sentences=tuple(corrected_sentences),
    )
