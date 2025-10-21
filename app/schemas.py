"""
Pydantic schemas for request and response validation.
These control how data is received and returned by the API.
"""

from typing import Dict, List
from pydantic import BaseModel


class StringCreate(BaseModel):
    """Schema for POST /strings request."""
    value: str


class Properties(BaseModel):
    """Holds computed string properties."""
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]


class StringOut(BaseModel):
    """Response model for a single analyzed string."""
    id: str
    value: str
    properties: Properties
    created_at: str


class StringsListOut(BaseModel):
    """Response model for GET /strings (list with filters)."""
    data: List[StringOut]
    count: int
    filters_applied: dict


class NaturalLanguageOut(BaseModel):
    """Response model for GET /strings/filter-by-natural-language."""
    data: List[StringOut]
    count: int
    interpreted_query: dict
