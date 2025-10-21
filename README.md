# String Analyzer Service (FastAPI)

A small REST API that analyzes strings and stores their properties.

## Features
- **POST /strings** — analyze and store a string (409 on duplicate value)
- **GET /strings/{string_value}** — fetch a specific string
- **GET /strings** — list with filters (`is_palindrome`, `min_length`, `max_length`, `word_count`, `contains_character`)
- **GET /strings/filter-by-natural-language?query=...** — simple NL -> filters
- **DELETE /strings/{string_value}** — remove by exact value

## Tech
- FastAPI, SQLModel, SQLite (file: `strings.db`), Uvicorn

## Local Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Open docs: http://127.0.0.1:8000/docs