# CT-200 Document API

A FastAPI backend that ingests the CardioTrack CT-200 medical device manual PDF into a browsable, versioned document tree and generates QA test cases from selected sections — with real-time staleness detection as the document evolves.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env — set GROQ_API_KEY for real LLM calls, MONGO_URL for MongoDB
# All values are optional; defaults use SQLite + JSON file store + mock LLM
```

### 3. Start the API

```bash
# From the ct200_api/ directory:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 4. Run the end-to-end demo (v1 → v2 re-ingestion + staleness)

```bash
# In a second terminal (while server is running):
python scripts/demo.py
```

Or use the helper scripts (Linux/Mac):
```bash
chmod +x scripts/run_demo.sh
./scripts/run_demo.sh
```

Or (Windows):
```cmd
scripts\run_demo.bat
```

This will:
- Generate the CT-200 v1 and v2 PDFs
- Ingest v1, create a selection, generate test cases
- Ingest v2 (re-versioning)
- Retrieve the generation and show which nodes became stale

### 5. Run unit tests

```bash
python -m pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ct200.db` | SQLAlchemy DB URL |
| `MONGO_URL` | *(empty)* | MongoDB connection string; leave blank for JSON fallback |
| `MONGO_DB_NAME` | `ct200` | MongoDB database name |
| `JSON_STORE_PATH` | `./generation_store.json` | JSON file fallback path |
| `GROQ_API_KEY` | *(empty)* | Groq API key; leave blank for mock LLM |
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | Groq model name |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload a PDF file and ingest as new version |
| `POST` | `/ingest/path` | Ingest by server-side file path (for scripting) |
| `GET` | `/documents` | List all documents |
| `GET` | `/documents/{id}/nodes` | List top-level sections (`?version=N`) |
| `GET` | `/nodes/{id}` | Full node detail with children |
| `GET` | `/nodes/search` | Search by heading/text |
| `GET` | `/nodes/{id}/diff` | Diff node across versions |
| `POST` | `/selections` | Create a named, version-pinned selection |
| `GET` | `/selections/{id}` | Get selection |
| `POST` | `/generate` | Generate QA test cases for a selection |
| `GET` | `/generations/{id}` | Retrieve generation + staleness status |
| `GET` | `/selections/{id}/generations` | All generation IDs for a selection |
| `GET` | `/nodes/{id}/generations` | All generations that include a node |
| `GET` | `/health` | Health check |

---

## v1 → v2 Re-ingestion Flow

```bash
# Ingest v1
curl -X POST "http://localhost:8000/ingest/path?filepath=data/ct200_manual_v1.pdf&document_title=CT-200+CardioTrack+Manual"

# Create selection of pressure safety nodes (use node IDs from browse)
curl -X POST "http://localhost:8000/selections" \
  -H "Content-Type: application/json" \
  -d '{"name": "Pressure Safety", "node_ids": [5, 6]}'

# Generate test cases
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"selection_id": 1, "force_regenerate": false}'

# Ingest v2 (same document_title — creates version 2)
curl -X POST "http://localhost:8000/ingest/path?filepath=data/ct200_manual_v2.pdf&document_title=CT-200+CardioTrack+Manual"

# Retrieve generation with staleness
curl "http://localhost:8000/generations/{generation_id}"
```

### What changes between v1 and v2

| Section | v1 | v2 |
|---|---|---|
| 3.1 Pressure threshold | 295 mmHg | **290 mmHg** |
| 3.1 Auto-deflate window | 2 seconds | **1.5 seconds** |
| 3.4 Alarm list | E1–E6 | **E1–E7** (E7 added) |
| 5.1 Error table | E3 @ 295 mmHg, 2 s | **E3 @ 290 mmHg, 1.5 s** |
| 6.1 Memory capacity | 60 readings | **90 readings** |
| 8. Spec table | 280 mmHg range, 300 battery | **285 mmHg range, 350 battery** |
| 10.1 | *(absent)* | **New: Firmware Update Procedure** |

---

## Project Structure

```
ct200_api/
├── app/
│   ├── main.py          # FastAPI application + all endpoints
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── database.py      # DB connection + session
│   ├── parser.py        # PDF parsing pipeline
│   ├── ingestion.py     # PDF → DB ingestion service
│   ├── llm_service.py   # LLM generation with retry + error handling
│   ├── mongo_store.py   # MongoDB / JSON fallback store
│   └── staleness.py     # Staleness detection service
├── data/                # Generated PDFs (ct200_manual_v1.pdf, v2.pdf)
├── scripts/
│   ├── generate_pdfs.py # Generates the CT-200 manual PDFs
│   └── demo.py          # End-to-end demo script
├── tests/
│   └── test_parser.py   # Unit tests (8 tests)
├── requirements.txt
├── .env.example
├── APPROACH.md          # Design decisions and decision log
└── README.md
```
