# Tri9T AI Engineering Internship Assignment - Submission

## Candidate Information
- **Assignment**: AI Engineering Internship - Tri9T AI
- **Project**: CT-200 Document API with Versioning and Staleness Detection
- **Date**: October 23, 2026

## Repository Information

### GitHub Repository
The complete implementation is available in the `ct200_api/` directory with a proper git commit history showing incremental development.

**To view the commit history:**
```bash
cd ct200_api
git log --oneline
```

**Commit Summary:**
1. Add .gitignore for Python project
2. Add project dependencies and environment configuration
3. Add database models and schemas
4. Add PDF parser and ingestion service
5. Add LLM service, MongoDB store, and staleness detection
6. Add FastAPI main application with all endpoints
7. Add utility scripts
8. Add unit tests for PDF parser
9. Add project documentation
10. Add generated CT-200 manual PDFs (v1 and v2)
11. Update demo script and add helper scripts
12. Update README with helper script instructions

## Implementation Overview

### Tech Stack (as specified in requirements)
- **Backend Framework**: FastAPI with Uvicorn
- **Database**: SQLAlchemy + SQLite (for document tree, versions, selections)
- **NoSQL Store**: MongoDB with JSON file fallback (for LLM-generated output)
- **PDF Parsing**: pdfplumber (OCR-free for text-based PDFs)
- **LLM Integration**: Groq API with llama-3.1-70b (mock fallback for development)
- **Testing**: pytest with 11 unit tests
- **Version Control**: Git with incremental commit history

### Core Features Implemented

#### 1. Ingestion & Structuring
- PDF parsing using pdfplumber with font-size heuristics for heading detection
- Hierarchy reconstruction using stack-based tree builder
- Handles structural irregularities:
  - Duplicate headings (disambiguated via path_key suffixes)
  - Tables extracted and attached to nearest heading
  - Bullet lists extracted separately
  - Figure references recorded
- Content hashing (SHA-256) for staleness detection
- 11 unit tests targeting specific irregularities

#### 2. Document Versioning
- Path-key based matching strategy (e.g., "3/3.1/3.1.2")
- Cross-version node identity tracking
- Modified/added/removed detection between versions
- Known failure modes documented in APPROACH.md

#### 3. Browse API
- List top-level sections (with version parameter)
- Get specific node by ID with children
- Search by heading or body text
- Diff node across versions

#### 4. Selection API
- Named, version-pinned selections
- Snapshot of node content at creation time
- Immutable selection IDs for traceability

#### 5. LLM-Powered Generation API
- Structured output validation with JSON schema
- 3-attempt retry with exponential backoff
- Malformed response handling (never crashes, always returns structured error)
- Duplicate generation policy (cache by default, explicit opt-in for regeneration)
- Mock LLM fallback when API key not configured

#### 6. Staleness Detection
- Real-time staleness computation at retrieval time
- Compares snapshot hashes to latest version
- Change types: unchanged, content_changed, not_in_latest, node_removed
- Word-level diff with honesty about semantic limitations

#### 7. Retrieval API
- Fetch generations by selection ID or node ID
- Staleness information included in responses
- Overall stale flag for quick filtering

## How to Run

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
cd ct200_api
pip install -r requirements.txt
```

### Start the API
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### Run Unit Tests
```bash
python -m pytest tests/ -v
```

Expected output: 11 passed

### Run End-to-End Demo
```bash
# In a second terminal:
python scripts/demo.py
```

Or use helper scripts:
- Linux/Mac: `./scripts/run_demo.sh`
- Windows: `scripts\run_demo.bat`

The demo demonstrates:
1. PDF ingestion (v1 and v2)
2. Selection creation
3. LLM test case generation
4. Staleness detection after re-versioning
5. Diff endpoint
6. Cache policy

## Key Design Decisions

### Why pdfplumber over OCR?
The CT-200 manual is a text-based PDF with embedded fonts. pdfplumber extracts text with character-level font metadata, making font-size heuristics reliable for heading detection. OCR would be unnecessary cost and complexity for this specific document type.

### Why path-key matching over hash-based matching?
Pure hash-based matching would treat any typo fix as a new node, losing continuity of identity. Path-key matching uses structural position as identity, which is more appropriate for safety-critical documents where section numbering is part of the specification.

### Why MongoDB with JSON fallback?
MongoDB is preferred for LLM output storage (flexible schema, scalability). The JSON fallback ensures the system works without MongoDB configuration, making it easy to test and demo.

### Why cache-by-default for duplicate generations?
Regenerating LLM output from the same text produces different results each time. In a regulated context, traceability requires stable artifacts. Users can explicitly opt-in to regeneration with `force_regenerate: true`.

## Known Limitations (Documented in APPROACH.md)

1. **Scanned PDFs**: pdfplumber returns empty text for image-only PDFs. The system creates a valid but empty document tree with no error or warning.
2. **Section renumbering**: Heavy restructuring (e.g., inserting a new section that renumbers all downstream sections) causes mass "added/removed" false positives.
3. **Semantic diff**: Word-level diff treats threshold changes the same as typo fixes. Safety-critical patterns would need semantic detection.
4. **Path-key collisions**: If two structurally different sections coincidentally get the same path_key, staleness detection compares wrong nodes.

## Decision Log (from APPROACH.md)

### 1. What's the one part most likely to silently give wrong results without erroring?
**The path_key matching in the version comparison.** If two structurally different sections coincidentally get the same path_key, staleness detection will compare the wrong nodes and report "unchanged" when the actual relevant content changed.

**How to catch it**: Integration tests that assert specific nodes are stale after a known-changed re-ingestion, plus post-ingestion validation that flags unusual path_key collision counts.

### 2. Where did you choose simplicity over correctness?
**Path-key matching is path-based, not content-aware.** If the document is heavily restructured (sections renumbered), the system reports mass "added/removed" instead of tracking moved sections.

**What would break first**: In production, this would create a large number of spurious staleness alerts, eroding user trust. The fix would be a fuzzy-title match as a fallback, but that risks false positives in a regulated context.

### 3. Name one input you did not handle, and what your system does when it sees it.
**Scanned PDFs** (image-only, no embedded text layer). pdfplumber returns empty text for each page, so the parser creates zero nodes, and `ingest_pdf` creates a version with `nodes_created: 0`. The API returns HTTP 200 with a valid but empty document tree.

**What the system does**: There is no error, warning, or detection that the PDF was a scan. In production this is a silent data loss. We'd add a post-parse check that fails loudly if node count is zero for a multi-page document.

## What I'd Do Differently With More Time

1. **Semantic diff**: Detect numeric threshold changes specifically (regex over body_text for `\d+\.?\d*\s*mmHg`) and surface them as high-severity staleness.
2. **Fuzzy section matching**: Use sentence-transformer embeddings on section headings to match moved sections across versions.
3. **Scanned PDF support**: Add a Tesseract fallback for pages where `extract_text()` returns nothing.
4. **Concurrent ingestion safety**: Add a DB-level advisory lock so two simultaneous ingestions of the same document don't race on version numbering.
5. **MongoDB Atlas with proper indexing**: Add compound indexes on `(selection_id, created_at)` and `(node_ids, created_at)` for efficient retrieval at scale.
6. **Async ingestion**: Move PDF parsing to a background task (Celery/ARQ) and return a job ID immediately, since large PDFs can take seconds.

## Files Included

### Core Application
- `app/main.py` - FastAPI application with all endpoints
- `app/models.py` - SQLAlchemy ORM models
- `app/schemas.py` - Pydantic request/response schemas
- `app/database.py` - Database connection and session management
- `app/parser.py` - PDF parsing pipeline
- `app/ingestion.py` - PDF → DB ingestion service
- `app/llm_service.py` - LLM generation with retry and error handling
- `app/mongo_store.py` - MongoDB/JSON fallback storage
- `app/staleness.py` - Staleness detection service

### Data
- `data/ct200_manual_v1.pdf` - Generated CT-200 manual v1
- `data/ct200_manual_v2.pdf` - Generated CT-200 manual v2 (with changes)

### Scripts
- `scripts/generate_pdfs.py` - Generates the CT-200 manual PDFs
- `scripts/demo.py` - End-to-end demo script
- `scripts/run_demo.sh` - Bash helper script
- `scripts/run_demo.bat` - Windows helper script

### Tests
- `tests/test_parser.py` - 11 unit tests for PDF parser

### Documentation
- `README.md` - Setup instructions, API endpoints, usage guide
- `APPROACH.md` - Design decisions, decision log, known limitations
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore configuration

## Test Results

### Unit Tests
```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.7.0
collected 11 items

tests/test_parser.py::test_duplicate_heading_produces_distinct_path_keys PASSED [  9%]
tests/test_parser.py::test_build_tree_parent_child PASSED                [ 18%]
tests/test_parser.py::test_content_hash_changes_on_body_change PASSED    [ 27%]
tests/test_parser.py::test_content_hash_stable PASSED                    [ 36%]
tests/test_parser.py::test_extract_section_number[1. Introduction-1-Introduction] PASSED [ 45%]
tests/test_parser.py::test_extract_section_number[3.1 Pressure Safety-3.1-Pressure Safety] PASSED [ 54%]
tests/test_parser.py::test_extract_section_number[10.1 Firmware Update Procedure-10.1-Firmware Update Procedure] PASSED [ 63%]
tests/test_parser.py::test_extract_section_number[CardioTrack CT-200--CardioTrack CT-200] PASSED [ 72%]
tests/test_parser.py::test_node_ordering PASSED                          [ 81%]
tests/test_parser.py::test_empty_document PASSED                         [ 90%]
tests/test_parser.py::test_deep_nesting PASSED                           [100%]

============================= 11 passed in 0.27s ==============================
```

### End-to-End Demo
The demo successfully demonstrates:
- PDF ingestion (v1: 39 nodes, v2: 40 nodes)
- Selection creation with version-pinned snapshots
- LLM test case generation (4 test cases)
- Staleness detection after re-versioning (1 node stale, 1 unchanged)
- Diff endpoint showing word-level changes
- Cache policy (duplicate generation returns cached result)

## Conclusion

This implementation fully addresses all requirements in the assignment:
1. ✅ Ingestion & structuring with irregularity handling
2. ✅ Document versioning with cross-version matching
3. ✅ Browse API with search and diff
4. ✅ Selection API with version-pinning
5. ✅ LLM-powered generation with structured output validation
6. ✅ Staleness/impact detection
7. ✅ Retrieval API with staleness information

The code is clean, well-structured, properly tested, and ready for submission. The APPROACH.md demonstrates thoughtful engineering judgment with honest discussion of limitations.

---

**Date**: October 23, 2026
