"""
Main FastAPI application with all endpoints:
- POST /strings
- GET /strings/{value}
- GET /strings
- GET /strings/filter-by-natural-language
- DELETE /strings/{value}
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session
from typing import Optional
from datetime import timezone

from .db import init_db, get_session
from .models import StringRecord
from .schemas import StringCreate, StringOut, Properties, StringsListOut, NaturalLanguageOut
from .utils import analyze_string, parse_nl_query

# -----------------------------------------------------
# App initialization
# -----------------------------------------------------
app = FastAPI(title="String Analyzer Service", version="1.0.0")

@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "ok",
        "service": "String Analyzer Service",
        "docs": "/docs",
        "endpoints": ["/strings", "/strings/{string_value}", "/strings/filter-by-natural-language"]
    }

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}


# Allow all origins for simplicity (you can restrict this later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    init_db()


# -----------------------------------------------------
# Helper function: convert DB record -> API output model
# -----------------------------------------------------
def to_out(rec: StringRecord) -> StringOut:
    return StringOut(
        id=rec.id,
        value=rec.value,
        properties=Properties(
            length=rec.length,
            is_palindrome=rec.is_palindrome,
            unique_characters=rec.unique_characters,
            word_count=rec.word_count,
            sha256_hash=rec.sha256_hash,
            character_frequency_map=rec.character_frequency_map,
        ),
        created_at=rec.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
    )


# -----------------------------------------------------
# 1. POST /strings - analyze & store new string
# -----------------------------------------------------
@app.post("/strings", response_model=StringOut, status_code=201)
def create_string(payload: StringCreate, session: Session = Depends(get_session)):
    if payload is None or payload.value is None:
        raise HTTPException(status_code=400, detail='Invalid request body or missing "value" field')
    if not isinstance(payload.value, str):
        raise HTTPException(status_code=422, detail='Invalid data type for "value" (must be string)')

    value = payload.value
    props = analyze_string(value)

    # Prevent duplicates
    existing = session.exec(select(StringRecord).where(StringRecord.value == value)).first()
    if existing:
        raise HTTPException(status_code=409, detail="String already exists in the system")

    rec = StringRecord(
        id=props["sha256_hash"],
        value=value,
        length=props["length"],
        is_palindrome=props["is_palindrome"],
        unique_characters=props["unique_characters"],
        word_count=props["word_count"],
        sha256_hash=props["sha256_hash"],
        character_frequency_map=props["character_frequency_map"],
    )

    session.add(rec)
    session.commit()
    session.refresh(rec)
    return to_out(rec)


# -----------------------------------------------------
# 2. GET /strings/{string_value}
# -----------------------------------------------------
@app.get("/strings/{string_value}", response_model=StringOut)
def get_string(string_value: str = Path(...), session: Session = Depends(get_session)):
    rec = session.exec(select(StringRecord).where(StringRecord.value == string_value)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    return to_out(rec)


# -----------------------------------------------------
# 3. GET /strings - list with filters
# -----------------------------------------------------
@app.get("/strings", response_model=StringsListOut)
def list_strings(
    is_palindrome: Optional[bool] = Query(default=None),
    min_length: Optional[int] = Query(default=None, ge=0),
    max_length: Optional[int] = Query(default=None, ge=0),
    word_count: Optional[int] = Query(default=None, ge=0),
    contains_character: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    # Validate query params
    if contains_character is not None:
        if not isinstance(contains_character, str) or len(contains_character) != 1:
            raise HTTPException(status_code=400, detail='contains_character must be a single character')
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(status_code=400, detail='min_length cannot be greater than max_length')

    # Get all records and filter in memory (Stage 1 = small dataset)
    recs = session.exec(select(StringRecord)).all()

    def matches(r: StringRecord) -> bool:
        if is_palindrome is not None and r.is_palindrome != is_palindrome:
            return False
        if min_length is not None and r.length < min_length:
            return False
        if max_length is not None and r.length > max_length:
            return False
        if word_count is not None and r.word_count != word_count:
            return False
        if contains_character is not None and contains_character not in r.value:
            return False
        return True

    filtered = [to_out(r) for r in recs if matches(r)]

    filters_applied = {
        k: v
        for k, v in dict(
            is_palindrome=is_palindrome,
            min_length=min_length,
            max_length=max_length,
            word_count=word_count,
            contains_character=contains_character,
        ).items()
        if v is not None
    }

    return {"data": filtered, "count": len(filtered), "filters_applied": filters_applied}


# -----------------------------------------------------
# 4. GET /strings/filter-by-natural-language
# -----------------------------------------------------
@app.get("/strings/filter-by-natural-language", response_model=NaturalLanguageOut)
def filter_by_natural_language(query: str = Query(...), session: Session = Depends(get_session)):
    try:
        interpreted = parse_nl_query(query)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")
    except RuntimeError:
        raise HTTPException(status_code=422, detail="Query parsed but resulted in conflicting filters")

    pf = interpreted["parsed_filters"]
    result = list_strings(
        is_palindrome=pf.get("is_palindrome"),
        min_length=pf.get("min_length"),
        max_length=pf.get("max_length"),
        word_count=pf.get("word_count"),
        contains_character=pf.get("contains_character"),
        session=session,
    )

    return {**result, "interpreted_query": interpreted}


# -----------------------------------------------------
# 5. DELETE /strings/{string_value}
# -----------------------------------------------------
@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str = Path(...), session: Session = Depends(get_session)):
    rec = session.exec(select(StringRecord).where(StringRecord.value == string_value)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    session.delete(rec)
    session.commit()
    return None
