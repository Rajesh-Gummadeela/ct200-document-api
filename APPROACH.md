# Approach Document — CT-200 Document API

## Data Model

### SQLite (Relational — tree, versions, selections)

```
Document (1) ──< DocumentVersion (N) ──< DocNode (N)
Selection (1) ──< SelectionItem (N) >── DocNode
Selection (1) ──< Generation (N)
```

**DocNode** is the central entity. Key fields:
- `path_key`: `"3/3.1"` — used for cross-version matching
- `content_hash`: SHA-256 of `heading || body_text` — used for staleness detection
- `node_order`: preserves sibling order from the source document

**SelectionItem** stores a **snapshot** of each node's content hash, heading, and body text at selection-creation time. This is what makes staleness detection possible after re-versioning.

**Generation** (in SQLite) stores only the MongoDB document ID and the selection FK. The full LLM output lives in MongoDB.

### MongoDB / JSON fallback (Document store — LLM output)

Each generation document contains:
- `selection_id`, `node_ids`, `created_at`
- `test_cases` (array of TestCase objects)
- `prompt_used`, `raw_llm_response`
- `node_content_hashes` (map of node_id → hash at generation time)
- `parse_error` (null on success)

The JSON fallback is a single file (`generation_store.json`) keyed by a timestamp-based ID. It is adequate for development and single-process deployments.

---

## Tree Parsing Decisions

### OCR / parsing approach

We use **pdfplumber** (not a cloud OCR service) because:
1. The CT-200 manual is a text-based PDF (no scanned images), so pdfplumber extracts text with character-level font metadata.
2. Font size is a reliable proxy for heading level in a document generated with consistent styles.
3. No external API dependency or cost.

Trade-off: if the manual were a scanned PDF, pdfplumber would return empty text, and we'd need Tesseract/AWS Textract. The current approach would fail silently for scans.

### Heading detection

```
font_size ≥ 16.0   → level 0 (document title)
font_size ≥ 12.0   → level 1 (H1, e.g. "1. Introduction")
font_size ≥ 10.5   → level 2 (H2, e.g. "1.1 Intended Use")
font_size ≥ 10.0   → level 3 (H3)
font_size <  10.0  → body text
```

Bold body-sized text matching the section-number regex (`^\d+(\.\d+)*\s+.+`) is also treated as a heading. This handles edge cases where the PDF renderer slightly undersizes a heading.

### Hierarchy reconstruction

Stack-based tree builder (`build_tree` in `parser.py`):
- Iterate flat nodes; maintain a stack.
- Pop the stack until the top is a shallower level than the current node.
- If stack is empty, node is a root; otherwise it's a child of the stack top.
- This correctly handles the `H1 > H2 > H2 > H1 > H2` pattern.

### Structural irregularities handled

| Irregularity | How handled |
|---|---|
| **Duplicate "3.3" heading** | `_resolve_path_key_duplicate()` appends `_b`, `_c`, etc. Two nodes with same path prefix get `3/3.3` and `3/3.3_b`. Both have distinct node IDs in the DB. |
| **Tables** | Extracted via `pdfplumber.extract_tables()` and attached as JSON to the nearest heading-level node on the same page. |
| **Bullet lists** | Lines starting with `•`, `-`, `–` are extracted as `bullets` list in addition to being included in `body_text`. |
| **Figure references** | Pages with image objects are recorded as figure stubs. |
| **Inconsistent font sizes** | Thresholds have 0.5 pt tolerance bands; bold override catches bold body text that was mis-sized. |

### What the initial implementation failed to handle

- **Paragraph merging**: words extracted per-line were treated as separate body chunks. Fixed by grouping words by y-coordinate bucket.
- **Table text re-inclusion**: pdfplumber's `extract_text()` includes table cell text inline with body text, causing duplication. Fixed by extracting tables separately and stripping from the main text stream.
- **Duplicate headings**: first pass produced identical path_keys → DB unique constraint violation. Fixed with `_resolve_path_key_duplicate`.

---

## Version Matching Strategy

**Strategy: path-key matching** (e.g. `"3/3.1"`)

On re-ingestion:
- New nodes whose `path_key` exists in the previous version with an **identical** `content_hash` are considered "semantically unchanged."
- New nodes whose `path_key` exists but `content_hash` differs are "modified."
- New nodes with no matching `path_key` are "added."
- Old nodes with no corresponding new `path_key` are "removed."

### Why path-based (not pure hash-based or fuzzy-title)

- **Pure hash**: would mark any typo fix as a new node (no continuity of identity).
- **Fuzzy title**: would incorrectly merge "3.1 Pressure Safety" with any similarly named section in a different document.
- **Path-based**: uses the section's structural position as its identity. A section moved from 3.1 to 4.1 would be treated as removed+added, which is the correct conservative behaviour for a safety-critical document.

### Known failure modes

1. If a heading is renamed (e.g. "3.1 Pressure Safety" → "3.1 Cuff Pressure Limits"), path-key matching still works, but the node will be flagged as "modified" (correct). If the section number also changes, it will be flagged as removed+added (false negative for continuity, conservative for safety).
2. If an entire section is renumbered (e.g. after inserting a new section 2.5, old 2.5 becomes 2.6), all downstream nodes get new path_keys. Their content is unchanged but they appear as added, while old nodes appear as removed. This is a known limitation we'd address with fuzzy title fallback given more time.

---

## LLM Prompt Design + Structured Output Strategy

### Prompt

See `llm_service.py` — `SYSTEM_PROMPT`. Key design choices:
- **Persona**: "QA engineer for a medical device" — grounds the model in the right register.
- **Constraints**: "specific enough that a different engineer could execute it" — prevents vague test cases.
- **Output format**: strict JSON schema specified in the prompt, reinforced by `response_format: {"type": "json_object"}` in the Groq API call.
- **Section reference**: required field — ensures traceability back to source text.

### Retry strategy

3 attempts, exponential backoff (1.5s → 3s → 6s). On all failures:
- Empty `test_cases` list is returned.
- `parse_error` field explains what failed.
- HTTP 200 is still returned (not 500) — the caller can inspect `parse_error` and decide what to do.

### Malformed response handling

After receiving a response:
1. Strip markdown fences (some models wrap JSON in ` ```json ``` `).
2. `json.loads()` — JSONDecodeError → parse_error, empty test_cases.
3. Pydantic `TestCase` validation on each item — field-level errors caught individually.
4. If `test_cases` is present but empty → parse_error.

"It usually works" is not a design. Our design is: always return a structured response; never crash; always expose parse errors to the caller.

### Duplicate generation policy

**Default**: if the same `selection_id` is submitted again, return the cached generation (`is_cached: true`).

**Rationale**: Regenerating LLM output from the same text produces different results each time. For traceability in a regulated context, each "official" generation should be a single, stable artifact. Callers can set `force_regenerate: true` if they explicitly want a fresh run (e.g. after fixing a prompt issue), but they must opt in.

---

## Staleness Detection

At retrieval time, for each `SelectionItem`:

1. Look up the node's `path_key`.
2. Find the matching node in the **latest** document version by path_key.
3. Compare `SelectionItem.snapshot_content_hash` with the current node's `content_hash`.

Result codes:
- `unchanged` — hash matches.
- `content_changed` — hash differs. Lightweight word-diff included.
- `not_in_latest` — path_key not found in latest version (section removed/renamed).
- `node_removed` — node record doesn't exist at all in the DB.

**Honest limitation**: our diff is word-level, not semantic. A safety-critical threshold change (`295 mmHg` → `290 mmHg`) appears the same severity as a comma correction. The `diff_note` field includes an explicit warning about this. In a production system we'd add a list of safety-critical patterns (pressure values, timing thresholds) and surface them separately.

---

## Decision Log

### 1. What's the one part most likely to silently give wrong results without erroring? How would you catch it?

**The path_key matching in the version comparison.** If two structurally different sections coincidentally get the same path_key (e.g. a duplicate section number that was silently de-duplicated differently in v2), staleness detection will compare the wrong nodes and report "unchanged" when the actual relevant content changed. You'd catch this with integration tests that assert specific nodes are stale after a known-changed re-ingestion (exactly what `demo.py` does for the pressure threshold change), plus a post-ingestion validation step that flags any version where the number of path_key collisions is higher than expected.

### 2. Where did you choose simplicity over correctness, and what would break first?

Path-key matching is path-based, not content-aware. If the document is heavily restructured (sections renumbered), the system reports mass "added/removed" instead of tracking moved sections. In production this would create a large number of spurious staleness alerts, eroding user trust. The fix would be a fuzzy-title match as a fallback when path_keys don't align — but that risks false positives in a regulated context, so it needs human confirmation, which was out of scope here.

### 3. Name one input you did not handle, and what your system does when it sees it.

**Scanned PDFs** (image-only, no embedded text layer). pdfplumber returns empty text for each page, so the parser creates zero nodes, and `ingest_pdf` creates a version with `nodes_created: 0`. The API returns HTTP 200 with a valid but empty document tree. There is no error, warning, or detection that the PDF was a scan. In production this is a silent data loss — we'd add a post-parse check that fails loudly if node count is zero for a multi-page document.

---

## What I'd Do Differently With More Time

1. **Semantic diff**: detect numeric threshold changes specifically (regex over body_text for `\d+\.?\d*\s*mmHg`) and surface them as high-severity staleness.
2. **Fuzzy section matching**: use sentence-transformer embeddings on section headings to match moved sections across versions.
3. **Scanned PDF support**: add a Tesseract fallback for pages where `extract_text()` returns nothing.
4. **Concurrent ingestion safety**: add a DB-level advisory lock so two simultaneous ingestions of the same document don't race on version numbering.
5. **MongoDB Atlas with proper indexing**: add compound indexes on `(selection_id, created_at)` and `(node_ids, created_at)` for efficient retrieval at scale.
6. **Async ingestion**: move PDF parsing to a background task (Celery/ARQ) and return a job ID immediately, since large PDFs can take seconds.
