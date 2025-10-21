## Quick orientation

This is a small FastAPI service that analyzes strings and stores the results in SQLite using SQLModel.

- App entry: `app/main.py` (FastAPI app, endpoints)
- Data models: `app/models.py` (SQLModel `StringRecord`)
- Schemas / API shapes: `app/schemas.py` (Pydantic models used in responses)
- DB wiring: `app/db.py` (`init_db`, `get_session`, respect `DATABASE_URL`)
- Utilities: `app/utils.py` (string analysis + a conservative natural-language parser `parse_nl_query`)
- Tests: `tests/test_api.py` — small integration-style tests that exercise the public HTTP API via `TestClient`

Read these files first to understand the project's decisions (computed fields stored on the model, JSON column for frequency map, heuristic NL parser).

## Big-picture architecture & intent

- Purpose: analyze incoming strings (compute length, palindrome, character frequencies, word count, sha256) and persist them.
- Storage: SQLite by default (`strings.db`). The model intentionally stores computed properties redundantly (for simpler, faster filters on Stage 1).
- Filtering: the list endpoint loads records and applies filters in Python (in-memory) rather than complex SQL. This is deliberate for small datasets in Stage 1 — avoid converting to heavy SQL unless adding pagination or working with large datasets.
- Natural language: `app/utils.py::parse_nl_query` turns simple NL queries into the same filter set used by the list API.

## Developer workflows (commands & env)

Recommended local flow (macOS / zsh):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# (optional) install pytest for running tests
pip install pytest
uvicorn app.main:app --reload
```

Running tests (keep DB isolated):

```bash
# use a separate DB so tests don't clobber your dev DB
export DATABASE_URL="sqlite:///./test.db"
pytest -q
```

You can set `DATABASE_URL` to point to another SQLite file (or another SQL DB) — `app/db.py` reads that env var.

## API surface & behavior (concrete examples)

- POST /strings — body { "value": "..." } — returns 201 and a `StringOut`. Duplicate `value` returns 409 (see `tests/test_api.py::test_conflict_on_duplicate`).
- GET /strings — supports filters: `is_palindrome`, `min_length`, `max_length`, `word_count`, `contains_character`. Filtering is implemented in `app/main.py` in Python.
- GET /strings/{string_value} — returns a single string record.
- GET /strings/filter-by-natural-language?query=... — uses `parse_nl_query` in `app/utils.py`. Tests show the expected parsing: e.g. `"all single word palindromic strings"` -> parsed_filters includes `word_count=1` and `is_palindrome=True`.
- DELETE /strings/{string_value} — returns 204 on success, 404 if not found.

## Project-specific conventions & patterns (for AI edits)

- Primary key: `id` is a sha256 hex digest (also stored as `sha256_hash` on the model). When creating or modifying records, preserve this convention.
- Computed fields (length, is_palindrome, unique_characters, word_count, character_frequency_map) are stored on the model. When adding features that affect these, update both the model (if needed) and where those values are computed (likely in `app/main.py` or helper functions in `app/utils.py`).
- `character_frequency_map` is stored as JSON (`Column(JSON)` in `models.py`). When serializing, follow `schemas.py::Properties` shape.
- Small dataset assumption: list endpoint performs in-memory filtering. If you change to database-side filters or add pagination, update tests accordingly.

## Editing guidance for AI agents

- Preserve public API shapes declared in `app/schemas.py`.
- Keep HTTP error codes consistent: existing endpoints use 201, 204, 404, 409, 400, 422. Mirror these codes for similar behaviors.
- If you add a new filter or field, update:
  - `app/models.py` (if persisted),
  - `app/schemas.py` (response model),
  - `app/main.py` (endpoint behavior + validation), and
  - `tests/test_api.py` (add a test exercising the change).
- When touching DB behavior, prefer using `DATABASE_URL` for testability and avoid hardcoding file paths.

## Where to look for examples

- Example tests exercising API patterns: `tests/test_api.py`
- NL parsing heuristics and edge-cases: `app/utils.py::parse_nl_query` (contains regex-driven heuristics and explicit conflict checks)
- SQLModel usage and DB helpers: `app/db.py` and `app/models.py`

If anything here is unclear or you'd like more detail in a particular area (e.g., expected JSON response formats, test isolation strategy, or migrating filters to SQL), tell me what to expand and I'll iterate.
