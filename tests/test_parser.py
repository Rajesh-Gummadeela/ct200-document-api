"""
Unit tests for the CT-200 document parser.
Tests target the structural irregularities explicitly mentioned in the assignment.

Run with: python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import hashlib
import pytest

from app.parser import (
    _extract_section_number,
    _make_path_key,
    _resolve_path_key_duplicate,
    build_tree,
    RawNode,
)


# ── Test 1: Duplicate heading produces two distinct path_keys ─────────────────

def test_duplicate_heading_produces_distinct_path_keys():
    """
    The CT-200 manual has two subsections both labelled '3.3'.
    After path_key disambiguation, they must be distinct so they get
    separate DB node IDs with correct parents.
    """
    seen = set()

    # First "3.3 Electromagnetic Compatibility"
    pk1 = _make_path_key("3", "3.3", "Electromagnetic Compatibility")
    pk1 = _resolve_path_key_duplicate(pk1, seen)
    seen.add(pk1)

    # Second "3.3 Battery and Charging Safety"
    pk2 = _make_path_key("3", "3.3", "Battery and Charging Safety")
    pk2 = _resolve_path_key_duplicate(pk2, seen)
    seen.add(pk2)

    assert pk1 != pk2, f"Duplicate headings must produce distinct path_keys, got {pk1!r} and {pk2!r}"
    assert len(seen) == 2


# ── Test 2: Parent-child hierarchy preserved in build_tree ────────────────────

def _make_raw_node(heading, level, sec_num="", body="", path_key=None):
    n = RawNode(heading=heading, level=level, section_number=sec_num, body_lines=[body])
    n._path_key = path_key or _make_path_key("", sec_num, heading)
    return n


def test_build_tree_parent_child():
    """
    Given a flat list [H1, H2, H2, H1, H2], the resulting tree must have
    2 root nodes with 2 and 1 children respectively.
    """
    flat = [
        _make_raw_node("1. Introduction", 1, "1", path_key="1"),
        _make_raw_node("1.1 Intended Use", 2, "1.1", path_key="1/1.1"),
        _make_raw_node("1.2 Contraindications", 2, "1.2", path_key="1/1.2"),
        _make_raw_node("2. Device Description", 1, "2", path_key="2"),
        _make_raw_node("2.1 Hardware", 2, "2.1", path_key="2/2.1"),
    ]

    tree = build_tree(flat)

    assert len(tree) == 2, f"Expected 2 root nodes, got {len(tree)}"
    assert len(tree[0]["children"]) == 2, "Section 1 should have 2 children"
    assert len(tree[1]["children"]) == 1, "Section 2 should have 1 child"
    assert tree[0]["children"][0]["heading"] == "1.1 Intended Use"
    assert tree[1]["children"][0]["path_key"] == "2/2.1"


# ── Test 3: Content hash changes when body text changes ───────────────────────

def test_content_hash_changes_on_body_change():
    """
    Nodes with same heading but different body text must produce different
    content hashes (essential for v1 vs v2 staleness detection).
    """
    n1 = RawNode(heading="3.1 Pressure Safety", level=2, section_number="3.1",
                 body_lines=["If cuff pressure exceeds 295 mmHg during inflation, the firmware shall:"])
    n2 = RawNode(heading="3.1 Pressure Safety", level=2, section_number="3.1",
                 body_lines=["If cuff pressure exceeds 290 mmHg during inflation, the firmware shall:"])

    assert n1.content_hash != n2.content_hash, (
        "Changing '295' to '290' must produce a different content hash"
    )


# ── Test 4: Content hash is stable (same input -> same hash) ──────────────────

def test_content_hash_stable():
    n = RawNode(heading="3.1 Pressure Safety", level=2, section_number="3.1",
                body_lines=["Some body text"])
    h1 = n.content_hash
    h2 = n.content_hash
    assert h1 == h2


# ── Test 5: Section number extraction ─────────────────────────────────────────

@pytest.mark.parametrize("heading, expected_sec, expected_text", [
    ("1. Introduction", "1", "Introduction"),
    ("3.1 Pressure Safety", "3.1", "Pressure Safety"),
    ("10.1 Firmware Update Procedure", "10.1", "Firmware Update Procedure"),
    ("CardioTrack CT-200", "", "CardioTrack CT-200"),  # no section number
])
def test_extract_section_number(heading, expected_sec, expected_text):
    sec, text = _extract_section_number(heading)
    assert sec == expected_sec, f"For '{heading}': expected sec={expected_sec!r}, got {sec!r}"
    assert text == expected_text, f"For '{heading}': expected text={expected_text!r}, got {text!r}"


# ── Test 6: Node ordering preserved ───────────────────────────────────────────

def test_node_ordering():
    """Children must preserve the order they appeared in the flat list."""
    flat = [
        _make_raw_node("1. Introduction", 1, "1", path_key="1"),
        _make_raw_node("1.3 Symbols", 2, "1.3", path_key="1/1.3"),
        _make_raw_node("1.1 Intended Use", 2, "1.1", path_key="1/1.1"),
        _make_raw_node("1.2 Contraindications", 2, "1.2", path_key="1/1.2"),
    ]
    tree = build_tree(flat)
    children = tree[0]["children"]
    assert children[0]["section_number"] == "1.3"
    assert children[1]["section_number"] == "1.1"
    assert children[2]["section_number"] == "1.2"
    assert children[0]["node_order"] == 0
    assert children[2]["node_order"] == 2


# ── Test 7: Empty document parses cleanly ─────────────────────────────────────

def test_empty_document():
    tree = build_tree([])
    assert tree == []


# ── Test 8: Deep nesting (H3 under H2 under H1) ───────────────────────────────

def test_deep_nesting():
    flat = [
        _make_raw_node("1. Introduction", 1, "1", path_key="1"),
        _make_raw_node("1.1 Overview", 2, "1.1", path_key="1/1.1"),
        _make_raw_node("1.1.1 Background", 3, "1.1.1", path_key="1/1.1/1.1.1"),
    ]
    tree = build_tree(flat)
    assert len(tree) == 1
    h2 = tree[0]["children"][0]
    h3 = h2["children"][0]
    assert h3["heading"] == "1.1.1 Background"
    assert h3["level"] == 3
