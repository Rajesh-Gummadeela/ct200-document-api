"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ── Document / Version ────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    document_id: int
    document_title: str
    version_id: int
    version_number: int
    nodes_created: int
    message: str


class DocumentOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    latest_version: int

    model_config = {"from_attributes": True}


# ── Doc Nodes ─────────────────────────────────────────────────────────────────

class DocNodeSummary(BaseModel):
    id: int
    heading: str
    level: int
    section_number: str
    path_key: str
    content_hash: str
    node_order: int
    version_id: int

    model_config = {"from_attributes": True}


class DocNodeDetail(DocNodeSummary):
    body_text: str
    tables: List[Any] = []
    figures: List[str] = []
    bullets: List[str] = []
    parent_id: Optional[int] = None
    children: List["DocNodeDetail"] = []

    model_config = {"from_attributes": True}


DocNodeDetail.model_rebuild()


class NodeDiff(BaseModel):
    node_id_v1: Optional[int]
    node_id_v2: Optional[int]
    path_key: str
    heading: str
    status: str  # "unchanged" | "modified" | "added" | "removed"
    hash_v1: Optional[str]
    hash_v2: Optional[str]
    diff_summary: Optional[str]


# ── Selections ────────────────────────────────────────────────────────────────

class SelectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    node_ids: List[int] = Field(..., min_length=1)


class SelectionItemOut(BaseModel):
    id: int
    node_id: int
    version_id: int
    snapshot_content_hash: str
    snapshot_heading: str
    snapshot_body_text: str

    model_config = {"from_attributes": True}


class SelectionOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    items: List[SelectionItemOut] = []

    model_config = {"from_attributes": True}


# ── LLM Generation ────────────────────────────────────────────────────────────

class GenerationRequest(BaseModel):
    selection_id: int
    force_regenerate: bool = False  # explicit policy: default do not regenerate


class TestCase(BaseModel):
    id: str
    title: str
    preconditions: List[str]
    steps: List[str]
    expected_result: str
    section_reference: str


class GenerationOut(BaseModel):
    generation_id: str
    selection_id: int
    node_ids: List[int]
    test_cases: List[TestCase]
    prompt_used: str
    raw_llm_response: str
    created_at: str
    is_cached: bool = False


# ── Retrieval + Staleness ─────────────────────────────────────────────────────

class StalenessInfo(BaseModel):
    node_id: int
    path_key: str
    heading: str
    snapshot_hash: str
    current_hash: Optional[str]
    is_stale: bool
    change_type: str   # "unchanged" | "content_changed" | "node_removed" | "not_in_latest"
    diff_note: Optional[str]


class TestCaseWithStaleness(BaseModel):
    generation_id: str
    selection_id: int
    test_cases: List[TestCase]
    created_at: str
    staleness: List[StalenessInfo]
    overall_stale: bool
