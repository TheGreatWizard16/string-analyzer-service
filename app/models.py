"""
SQLModel database table definition for storing analyzed strings.
"""

from datetime import datetime
from typing import Dict
from sqlmodel import SQLModel, Field, Column, JSON


class StringRecord(SQLModel, table=True):
    """
    Represents one analyzed string record in the database.
    """
    id: str = Field(primary_key=True, index=True)  # SHA256 hash used as unique ID
    value: str = Field(index=True, unique=True)  # Original string value

    # Computed properties
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str

    # Frequency map stored as JSON
    character_frequency_map: Dict[str, int] = Field(sa_column=Column(JSON))

    # Auto-generated timestamp (UTC)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
