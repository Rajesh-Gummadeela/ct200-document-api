"""
FastAPI main application — CT-200 Document API.

Endpoints:
  POST /ingest                  - Ingest a PDF (creates new version)
  GET  /documents               - List all documents
  GET  /documents/{id}/nodes    - List top-level nodes (version param)
  GET  /nodes/{id}              - Get node detail with children
  GET  /nodes/search            - Search nodes by heading/text
  GET  /nodes/{id}/diff         - Diff a node across versions
  POST /selections              - Create a named, version-pinned selection
  GET  /selections/{id}         - Get selection
  POST /generate                - Generate QA test cases for a selection
  GET  /generations/{id}        - Retrieve generation with staleness info
  GET  /selections/{id}/generations - All generations for a selection
  GET  /nodes/{id}/generations  - All generations for a node
"""
import os
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import create_tables, get_db
from app.models import (
    Document, DocumentVersion, DocNode,
    Selection, SelectionItem, Generation,
)
from app.schemas import (
    IngestResponse, DocumentOut, DocNodeSummary, DocNodeDetail, NodeDiff,
    SelectionCreate, SelectionOut, SelectionItemOut,
    GenerationRequest, GenerationOut, TestCaseWithStaleness, StalenessInfo,
)
from app.ingestion import ingest_pdf
from app.llm_service import generate_test_cases
from app.staleness import compute_staleness
from app.mongo_store import get_generation_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    # Warm up generation store
    get_generation_store()
    yield


app = FastAPI(
    title="CT-200 Document API",
    description=(
        "Hierarchical document ingestion, versioning, selection, and "
        "QA test-case generation for the CardioTrack CT-200 manual."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _node_to_detail(node: DocNode, db: Session, depth: int = 0) -> DocNodeDetail:
    children = (
        db.query(DocNode)
        .filter(DocNode.parent_id == node.id)
        .order_by(DocNode.node_order)
        .all()
    ) if depth < 5 else []

    return DocNodeDetail(
        id=node.id,
        heading=node.heading,
        level=node.level,
        section_number=node.section_number,
        path_key=node.path_key,
        content_hash=node.content_hash,
        node_order=node.node_order,
        version_id=node.version_id,
        body_text=node.body_text,
        tables=node.tables or [],
        figures=node.figures or [],
        bullets=node.bullets or [],
        parent_id=node.parent_id,
        children=[_node_to_detail(c, db, depth + 1) for c in children],
    )


def _get_version(document_id: int, version: Optional[int], db: Session) -> DocumentVersion:
    q = db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id)
    if version is not None:
        q = q.filter(DocumentVersion.version_number == version)
    else:
        q = q.filter(DocumentVersion.is_latest == True)
    result = q.first()
    if not result:
        raise HTTPException(404, f"Version not found for document {document_id}")
    return result


# ── Ingestion ─────────────────────────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_document(
    file: UploadFile = File(...),
    document_title: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF and ingest it as a new version of the named document.
    If the document doesn't exist, it is created.
    If it exists, a new version is appended (previous versions are preserved).
    """
    # Save uploaded file temporarily
    tmp_path = f"./tmp_upload_{file.filename}"
    try:
        with open(tmp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = ingest_pdf(
            filepath=tmp_path,
            document_title=document_title,
            db=db,
        )
        return IngestResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/ingest/path", response_model=IngestResponse, tags=["Ingestion"])
def ingest_by_path(
    filepath: str = Query(..., description="Absolute or relative path to PDF"),
    document_title: str = Query(...),
    db: Session = Depends(get_db),
):
    """Ingest a PDF from a server-side file path (useful for scripting)."""
    try:
        result = ingest_pdf(filepath=filepath, document_title=document_title, db=db)
        return IngestResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")


# ── Documents ─────────────────────────────────────────────────────────────────

@app.get("/documents", response_model=List[DocumentOut], tags=["Browse"])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    result = []
    for doc in docs:
        latest = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == doc.id, DocumentVersion.is_latest == True)
            .first()
        )
        result.append(DocumentOut(
            id=doc.id,
            title=doc.title,
            created_at=doc.created_at,
            latest_version=latest.version_number if latest else 0,
        ))
    return result


# ── Browse API ────────────────────────────────────────────────────────────────

@app.get("/documents/{document_id}/nodes", response_model=List[DocNodeSummary], tags=["Browse"])
def list_top_level_nodes(
    document_id: int,
    version: Optional[int] = Query(None, description="Version number; defaults to latest"),
    db: Session = Depends(get_db),
):
    """List top-level sections of a document (direct children of the root)."""
    ver = _get_version(document_id, version, db)
    nodes = (
        db.query(DocNode)
        .filter(DocNode.version_id == ver.id, DocNode.parent_id == None)
        .order_by(DocNode.node_order)
        .all()
    )
    return [DocNodeSummary(
        id=n.id,
        heading=n.heading,
        level=n.level,
        section_number=n.section_number,
        path_key=n.path_key,
        content_hash=n.content_hash,
        node_order=n.node_order,
        version_id=n.version_id,
    ) for n in nodes]


@app.get("/nodes/{node_id}", response_model=DocNodeDetail, tags=["Browse"])
def get_node(node_id: int, db: Session = Depends(get_db)):
    """Get full details of a node including children (up to 5 levels deep)."""
    node = db.query(DocNode).filter(DocNode.id == node_id).first()
    if not node:
        raise HTTPException(404, f"Node {node_id} not found")
    return _node_to_detail(node, db)


@app.get("/nodes/search", response_model=List[DocNodeSummary], tags=["Browse"])
def search_nodes(
    q: str = Query(..., min_length=1, description="Search term"),
    document_id: Optional[int] = Query(None),
    version: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Search nodes by heading or body text."""
    query = db.query(DocNode)

    if document_id is not None:
        ver = _get_version(document_id, version, db)
        query = query.filter(DocNode.version_id == ver.id)

    term = f"%{q}%"
    query = query.filter(
        DocNode.heading.ilike(term) | DocNode.body_text.ilike(term)
    )

    nodes = query.limit(50).all()
    return [DocNodeSummary(
        id=n.id,
        heading=n.heading,
        level=n.level,
        section_number=n.section_number,
        path_key=n.path_key,
        content_hash=n.content_hash,
        node_order=n.node_order,
        version_id=n.version_id,
    ) for n in nodes]


@app.get("/nodes/{node_id}/diff", response_model=NodeDiff, tags=["Browse"])
def diff_node(
    node_id: int,
    db: Session = Depends(get_db),
):
    """
    Given a node ID, compare it across all versions of its document.
    Returns whether the node changed between v1 and latest, with a diff summary.
    """
    node = db.query(DocNode).filter(DocNode.id == node_id).first()
    if not node:
        raise HTTPException(404, f"Node {node_id} not found")

    version = db.query(DocumentVersion).filter(DocumentVersion.id == node.version_id).first()
    document_id = version.document_id

    # Find the same path_key in the latest version
    latest_ver = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id, DocumentVersion.is_latest == True)
        .first()
    )

    if not latest_ver or latest_ver.id == node.version_id:
        return NodeDiff(
            node_id_v1=node.id,
            node_id_v2=None,
            path_key=node.path_key,
            heading=node.heading,
            status="unchanged",
            hash_v1=node.content_hash,
            hash_v2=None,
            diff_summary="This is the latest version or no other version exists.",
        )

    latest_node = (
        db.query(DocNode)
        .filter(DocNode.version_id == latest_ver.id, DocNode.path_key == node.path_key)
        .first()
    )

    if not latest_node:
        return NodeDiff(
            node_id_v1=node.id,
            node_id_v2=None,
            path_key=node.path_key,
            heading=node.heading,
            status="removed",
            hash_v1=node.content_hash,
            hash_v2=None,
            diff_summary=f"Node not found in latest version (v{latest_ver.version_number}).",
        )

    if node.content_hash == latest_node.content_hash:
        status = "unchanged"
        diff_summary = None
    else:
        status = "modified"
        old_words = set(node.body_text.split())
        new_words = set(latest_node.body_text.split())
        added = list(new_words - old_words)[:8]
        removed = list(old_words - new_words)[:8]
        diff_summary = (
            f"Content changed between v{version.version_number} and v{latest_ver.version_number}.\n"
            f"Words added: {added}\nWords removed: {removed}"
        )

    return NodeDiff(
        node_id_v1=node.id,
        node_id_v2=latest_node.id,
        path_key=node.path_key,
        heading=node.heading,
        status=status,
        hash_v1=node.content_hash,
        hash_v2=latest_node.content_hash,
        diff_summary=diff_summary,
    )


# ── Selections ────────────────────────────────────────────────────────────────

@app.post("/selections", response_model=SelectionOut, tags=["Selections"])
def create_selection(body: SelectionCreate, db: Session = Depends(get_db)):
    """
    Create a version-pinned selection.
    Each node_id is resolved to its current version at creation time.
    The snapshot of each node's content is stored for future staleness detection.
    """
    # Validate all node IDs
    nodes = []
    for nid in body.node_ids:
        node = db.query(DocNode).filter(DocNode.id == nid).first()
        if not node:
            raise HTTPException(404, f"Node {nid} not found")
        nodes.append(node)

    selection = Selection(name=body.name)
    db.add(selection)
    db.flush()

    items = []
    for node in nodes:
        item = SelectionItem(
            selection_id=selection.id,
            node_id=node.id,
            version_id=node.version_id,
            snapshot_content_hash=node.content_hash,
            snapshot_heading=node.heading,
            snapshot_body_text=node.body_text,
        )
        db.add(item)
        items.append(item)

    db.flush()
    db.commit()
    db.refresh(selection)

    return SelectionOut(
        id=selection.id,
        name=selection.name,
        created_at=selection.created_at,
        items=[
            SelectionItemOut(
                id=it.id,
                node_id=it.node_id,
                version_id=it.version_id,
                snapshot_content_hash=it.snapshot_content_hash,
                snapshot_heading=it.snapshot_heading or "",
                snapshot_body_text=it.snapshot_body_text or "",
            )
            for it in items
        ],
    )


@app.get("/selections/{selection_id}", response_model=SelectionOut, tags=["Selections"])
def get_selection(selection_id: int, db: Session = Depends(get_db)):
    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if not selection:
        raise HTTPException(404, f"Selection {selection_id} not found")
    return SelectionOut(
        id=selection.id,
        name=selection.name,
        created_at=selection.created_at,
        items=[
            SelectionItemOut(
                id=it.id,
                node_id=it.node_id,
                version_id=it.version_id,
                snapshot_content_hash=it.snapshot_content_hash,
                snapshot_heading=it.snapshot_heading or "",
                snapshot_body_text=it.snapshot_body_text or "",
            )
            for it in selection.items
        ],
    )


# ── Generation ────────────────────────────────────────────────────────────────

@app.post("/generate", response_model=GenerationOut, tags=["Generation"])
def generate(body: GenerationRequest, db: Session = Depends(get_db)):
    """
    Generate QA test cases for a selection.

    Duplicate policy: If the same selection_id is submitted again and
    force_regenerate=False, the existing generation is returned (cached).
    This is intentional — regenerating creates traceability ambiguity.
    Set force_regenerate=True to override.
    """
    store = get_generation_store()

    # Check for existing generation (duplicate policy)
    selection = db.query(Selection).filter(Selection.id == body.selection_id).first()
    if not selection:
        raise HTTPException(404, f"Selection {body.selection_id} not found")

    existing = store.find_by_selection(body.selection_id)
    if existing and not body.force_regenerate:
        g = existing[-1]  # most recent
        return GenerationOut(
            generation_id=g["_id"],
            selection_id=g["selection_id"],
            node_ids=g["node_ids"],
            test_cases=g["test_cases"],
            prompt_used=g.get("prompt_used", ""),
            raw_llm_response=g.get("raw_llm_response", ""),
            created_at=g["created_at"],
            is_cached=True,
        )

    # Build context text from selection items
    context_parts = []
    node_ids = []
    for item in selection.items:
        node = item.node
        if node:
            context_parts.append(
                f"### {node.heading}\n\n{node.body_text}\n"
                + ("\n".join(f"• {b}" for b in (node.bullets or [])))
            )
            node_ids.append(node.id)

    context_text = "\n\n---\n\n".join(context_parts)

    # Call LLM
    result = generate_test_cases(context_text, node_ids)

    # Serialize test cases for MongoDB
    test_cases_data = [tc.model_dump() for tc in result["test_cases"]]

    # Persist to MongoDB / JSON store
    doc = {
        "selection_id": body.selection_id,
        "node_ids": node_ids,
        "test_cases": test_cases_data,
        "prompt_used": result["prompt_used"],
        "raw_llm_response": result["raw_llm_response"],
        "parse_error": result.get("parse_error"),
        # Snapshot of node content hashes at generation time (for staleness)
        "node_content_hashes": {
            str(item.node_id): item.snapshot_content_hash
            for item in selection.items
        },
    }
    mongo_id = store.insert(doc)

    # Store reference in SQLite
    gen_ref = Generation(
        selection_id=body.selection_id,
        mongo_id=mongo_id,
    )
    db.add(gen_ref)
    db.commit()

    return GenerationOut(
        generation_id=mongo_id,
        selection_id=body.selection_id,
        node_ids=node_ids,
        test_cases=result["test_cases"],
        prompt_used=result["prompt_used"],
        raw_llm_response=result["raw_llm_response"],
        created_at=doc["created_at"],
        is_cached=False,
    )


# ── Retrieval + Staleness ─────────────────────────────────────────────────────

@app.get("/generations/{generation_id}", response_model=TestCaseWithStaleness, tags=["Retrieval"])
def get_generation(generation_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a generation with real-time staleness computation.
    Staleness is checked at retrieval time against the latest document version.
    """
    store = get_generation_store()
    g = store.get(generation_id)
    if not g:
        raise HTTPException(404, f"Generation {generation_id} not found")

    selection_id = g["selection_id"]
    staleness_list = compute_staleness(selection_id, db)
    overall_stale = any(s.is_stale for s in staleness_list)

    from app.schemas import TestCase
    test_cases = []
    for tc in g.get("test_cases", []):
        try:
            test_cases.append(TestCase(**tc))
        except Exception:
            pass

    return TestCaseWithStaleness(
        generation_id=generation_id,
        selection_id=selection_id,
        test_cases=test_cases,
        created_at=g.get("created_at", ""),
        staleness=staleness_list,
        overall_stale=overall_stale,
    )


@app.get("/selections/{selection_id}/generations", tags=["Retrieval"])
def list_generations_for_selection(selection_id: int, db: Session = Depends(get_db)):
    """List all generation IDs for a selection."""
    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if not selection:
        raise HTTPException(404, f"Selection {selection_id} not found")

    gens = db.query(Generation).filter(Generation.selection_id == selection_id).all()
    return {
        "selection_id": selection_id,
        "generations": [{"id": g.id, "mongo_id": g.mongo_id, "created_at": g.created_at} for g in gens],
    }


@app.get("/nodes/{node_id}/generations", tags=["Retrieval"])
def list_generations_for_node(node_id: int, db: Session = Depends(get_db)):
    """List all generations that include a specific node."""
    node = db.query(DocNode).filter(DocNode.id == node_id).first()
    if not node:
        raise HTTPException(404, f"Node {node_id} not found")

    store = get_generation_store()
    gens = store.find_by_node(node_id)
    return {
        "node_id": node_id,
        "heading": node.heading,
        "generations": [{"id": g["_id"], "created_at": g["created_at"]} for g in gens],
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "storage": {
            "sqlite": "connected",
            "generation_store": (
                "mongodb" if get_generation_store().using_mongo else "json_fallback"
            ),
        },
    }
