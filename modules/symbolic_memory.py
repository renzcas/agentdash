import re


_WORD_PATTERN = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*", re.UNICODE)
_STOP_WORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "among",
    "and",
    "any",
    "are",
    "because",
    "been",
    "before",
    "being",
    "between",
    "both",
    "but",
    "can",
    "could",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "here",
    "hers",
    "him",
    "himself",
    "his",
    "how",
    "into",
    "itself",
    "just",
    "more",
    "most",
    "must",
    "not",
    "now",
    "once",
    "only",
    "other",
    "our",
    "ours",
    "out",
    "over",
    "own",
    "same",
    "should",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "until",
    "very",
    "was",
    "were",
    "what",
    "work",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "would",
    "your",
}


def extract_concepts(text: str, *, limit: int = 8) -> list[str]:
    """Extract stable keyword symbols without claiming semantic understanding."""
    if limit <= 0:
        return []
    concepts: list[str] = []
    seen: set[str] = set()
    for word in _WORD_PATTERN.findall(text):
        normalized = word.casefold()
        if len(normalized) < 3 or normalized in _STOP_WORDS or normalized in seen:
            continue
        seen.add(normalized)
        concepts.append(normalized)
        if len(concepts) == limit:
            break
    return concepts
