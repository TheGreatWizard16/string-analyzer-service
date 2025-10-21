"""
Utility functions:
- String analysis logic
- SHA-256 hashing
- Natural language query parsing
"""

import hashlib
import re
from collections import Counter
from typing import Dict


def sha256_hex(s: str) -> str:
    """Return the SHA-256 hex digest of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def analyze_string(value: str) -> dict:
    """
    Analyze the given string and return computed properties.
    """
    if not isinstance(value, str):
        raise TypeError("value must be string")

    length = len(value)
    lowered = value.casefold()  # case-insensitive comparison
    is_palindrome = lowered == lowered[::-1]
    unique_characters = len(set(value))
    word_count = len(value.split())
    digest = sha256_hex(value)
    freq_map = dict(Counter(value))  # counts every character including spaces

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": digest,
        "character_frequency_map": freq_map,
    }


# -------- Natural Language Parser --------

VOWELS = ["a", "e", "i", "o", "u"]


def parse_nl_query(q: str) -> dict:
    """
    Interpret simple natural-language filter queries.

    Supported patterns:
    - "all single word palindromic strings"
    - "strings longer than 10 characters"
    - "strings containing the letter z"
    - "palindromic strings that contain the first vowel"
    """
    if not q or not isinstance(q, str):
        raise ValueError("query must be a non-empty string")

    original = q
    q = q.strip().lower()
    filters = {}

    # Detect single-word palindrome request
    if re.search(r"\b(single|one)[ -]?word\b", q) and "palindrom" in q:
        filters["word_count"] = 1
        filters["is_palindrome"] = True

    # "strings longer than N characters"
    m = re.search(r"longer than\s*(\d+)\s*characters?", q)
    if m:
        filters["min_length"] = int(m.group(1)) + 1

    # "strings containing the letter z"
    m = re.search(r"contain(?:ing)?\s+(?:the\s+letter\s+)?([a-z])\b", q)
    if m:
        filters["contains_character"] = m.group(1)

    # "palindromic strings that contain the first vowel"
    if "palindrom" in q and "first vowel" in q:
        filters["is_palindrome"] = True
        filters.setdefault("contains_character", VOWELS[0])  # default 'a'

    # If nothing matched, fail
    if not filters:
        raise ValueError("unable to parse query")

    # Example conflict check
    if "min_length" in filters and "max_length" in filters:
        if int(filters["min_length"]) > int(filters["max_length"]):
            raise RuntimeError("conflicting filters")

    return {"original": original, "parsed_filters": filters}
