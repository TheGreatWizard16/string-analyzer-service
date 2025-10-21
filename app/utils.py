"""
Utility functions:
- String analysis logic
- SHA-256 hashing
- Natural language query parsing (robust)
"""

import hashlib
import re
from collections import Counter
from typing import Dict


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def analyze_string(value: str) -> dict:
    if not isinstance(value, str):
        raise TypeError("value must be string")

    length = len(value)
    lowered = value.casefold()
    is_palindrome = lowered == lowered[::-1]
    unique_characters = len(set(value))
    word_count = len(value.split())
    digest = sha256_hex(value)
    freq_map = dict(Counter(value))  # counts spaces/punctuations too

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": digest,
        "character_frequency_map": freq_map,
    }


VOWELS = ["a", "e", "i", "o", "u"]


def parse_nl_query(q: str) -> dict:
    """
    Robust heuristic parser for basic NL filters expected by the task.

    Examples handled:
      - "all single word palindromic strings"
      - "strings longer than 10 characters"
      - "strings more than 10 characters"
      - "strings at least 10 characters"
      - "strings fewer than 10 characters" / "less than 10"
      - "strings exactly 10 characters"
      - "strings containing the letter z" / "contain letter 'z'"
      - "palindromic strings that contain the first vowel"
      - "palindrome" / "palindromic" keywords
    """
    if not q or not isinstance(q, str):
        raise ValueError("query must be a non-empty string")

    original = q
    q = q.strip().lower()
    filters: Dict[str, object] = {}

    # palindromic keyword (palindrome / palindromic)
    if re.search(r"\bpalindrom(e|ic)?\b", q):
        filters["is_palindrome"] = True

    # single / one word
    if re.search(r"\b(single|one)[ -]?word\b", q):
        filters["word_count"] = 1

    # longer than / more than N characters
    m = re.search(r"(longer|more)\s+than\s+(\d+)\s*chars?|characters?", q)
    if m:
        filters["min_length"] = int(m.group(2)) + 1

    # at least N characters
    m = re.search(r"at\s+least\s+(\d+)\s*chars?|characters?", q)
    if m:
        filters["min_length"] = max(int(m.group(1)), int(filters.get("min_length", 0)))

    # fewer/less than N characters
    m = re.search(r"(fewer|less)\s+than\s+(\d+)\s*chars?|characters?", q)
    if m:
        filters["max_length"] = int(m.group(2)) - 1

    # exactly N characters
    m = re.search(r"exactly\s+(\d+)\s*chars?|characters?", q)
    if m:
        n = int(m.group(1))
        filters["min_length"] = n
        filters["max_length"] = n

    # containing the letter X (quotes optional)
    m = re.search(r"contain(?:ing)?\s+(?:the\s+letter\s+)?'?(?P<ch>[a-z])'?", q)
    if m:
        filters["contains_character"] = m.group("ch")

    # first vowel heuristic
    if "first vowel" in q:
        filters.setdefault("contains_character", VOWELS[0])

    if not filters:
        raise ValueError("unable to parse query")

    # basic conflict check
    if "min_length" in filters and "max_length" in filters:
        if int(filters["min_length"]) > int(filters["max_length"]):
            raise RuntimeError("conflicting filters")

    return {"original": original, "parsed_filters": filters}
