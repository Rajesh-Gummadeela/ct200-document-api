"""
End-to-end demo script: demonstrates the full versioning + staleness flow.

Usage:
    python scripts/demo.py

This script:
1. Generates the CT-200 PDFs (v1 and v2)
2. Starts the API (or connects to a running one)
3. Ingests v1
4. Creates a selection of safety-critical nodes
5. Generates QA test cases from the selection
6. Ingests v2
7. Retrieves the generation and shows staleness status
8. Demonstrates the diff endpoint
"""
import subprocess
import sys
import os
import time
import json
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCRIPT_DIR = os.path.dirname(__file__)


def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_server():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def main():
    sep("Step 0: Generate CT-200 PDFs")
    generate_script = os.path.join(SCRIPT_DIR, "generate_pdfs.py")
    subprocess.run([sys.executable, generate_script], check=True)
    v1_path = os.path.abspath(os.path.join(DATA_DIR, "ct200_manual_v1.pdf"))
    v2_path = os.path.abspath(os.path.join(DATA_DIR, "ct200_manual_v2.pdf"))
    print(f"  v1: {v1_path}")
    print(f"  v2: {v2_path}")

    # ── Check server ──────────────────────────────────────────────────────────
    if not check_server():
        print("\n[!] API server not running. Start it with:")
        print("    cd ct200_api && python -m uvicorn app.main:app --reload")
        print("\nRun this script again after starting the server.")
        sys.exit(1)

    doc_title = "CT-200 CardioTrack Manual"

    # ── Ingest v1 ─────────────────────────────────────────────────────────────
    sep("Step 1: Ingest CT-200 v1")
    r = httpx.post(
        f"{BASE_URL}/ingest/path",
        params={"filepath": v1_path, "document_title": doc_title},
        timeout=60,
    )
    r.raise_for_status()
    ingest_v1 = r.json()
    print(json.dumps(ingest_v1, indent=2))
    doc_id = ingest_v1["document_id"]

    # ── Browse top-level nodes ────────────────────────────────────────────────
    sep("Step 2: List top-level sections (v1)")
    r = httpx.get(f"{BASE_URL}/documents/{doc_id}/nodes", timeout=10)
    r.raise_for_status()
    top_nodes = r.json()
    for n in top_nodes:
        print(f"  [{n['id']}] {n['heading']}  (hash: {n['content_hash'][:12]}...)")

    # ── Find safety-critical nodes ─────────────────────────────────────────────
    sep("Step 3: Select safety-critical nodes from top-level sections")
    # For demo purposes, we'll select nodes that have children with actual content
    # In a real scenario, users would browse and select via UI
    r = httpx.get(f"{BASE_URL}/documents/{doc_id}/nodes", timeout=10)
    r.raise_for_status()
    top_nodes = r.json()

    # Get all nodes to find ones with actual content
    all_nodes_with_content = []
    for node in top_nodes:
        r2 = httpx.get(f"{BASE_URL}/nodes/{node['id']}", timeout=10)
        r2.raise_for_status()
        node_detail = r2.json()
        all_nodes_with_content.append(node_detail)
        # Also get children
        for child in node_detail.get('children', []):
            all_nodes_with_content.append(child)

    # Select nodes that have actual body text (not just headings)
    content_nodes = [n for n in all_nodes_with_content if n.get('body_text') and len(n['body_text']) > 50]
    print(f"  Found {len(content_nodes)} nodes with substantial content")

    # Select 2 nodes with content
    selection_node_ids = [n['id'] for n in content_nodes[:2]]
    print(f"  Selected node IDs: {selection_node_ids}")
    for nid in selection_node_ids:
        node = next(n for n in content_nodes if n['id'] == nid)
        print(f"    [{nid}] {node['heading']}")

    # ── Create selection ───────────────────────────────────────────────────────
    sep("Step 4: Create version-pinned selection")
    r = httpx.post(
        f"{BASE_URL}/selections",
        json={"name": "Pressure Safety Nodes", "node_ids": selection_node_ids},
        timeout=10,
    )
    r.raise_for_status()
    selection = r.json()
    selection_id = selection["id"]
    print(json.dumps(selection, indent=2, default=str))

    # ── Generate test cases ────────────────────────────────────────────────────
    sep("Step 5: Generate QA test cases (LLM)")
    r = httpx.post(
        f"{BASE_URL}/generate",
        json={"selection_id": selection_id, "force_regenerate": False},
        timeout=120,
    )
    r.raise_for_status()
    generation = r.json()
    gen_id = generation["generation_id"]
    print(f"  Generation ID: {gen_id}")
    print(f"  Cached: {generation['is_cached']}")
    print(f"  Test cases generated: {len(generation['test_cases'])}")
    for tc in generation["test_cases"]:
        print(f"\n  [{tc['id']}] {tc['title']}")
        print(f"    Expected: {tc['expected_result'][:100]}...")

    # ── Ingest v2 (document re-versioning) ────────────────────────────────────
    sep("Step 6: Ingest CT-200 v2 (re-versioning)")
    r = httpx.post(
        f"{BASE_URL}/ingest/path",
        params={"filepath": v2_path, "document_title": doc_title},
        timeout=60,
    )
    r.raise_for_status()
    ingest_v2 = r.json()
    print(json.dumps(ingest_v2, indent=2))

    # ── Retrieve generation + staleness ───────────────────────────────────────
    sep("Step 7: Retrieve generation with staleness detection")
    r = httpx.get(f"{BASE_URL}/generations/{gen_id}", timeout=10)
    r.raise_for_status()
    retrieved = r.json()
    print(f"  Overall stale: {retrieved['overall_stale']}")
    print(f"\n  Staleness per node:")
    for s in retrieved["staleness"]:
        status_icon = "[STALE]" if s["is_stale"] else "[OK]"
        print(f"  {status_icon} [{s['node_id']}] {s['heading']} — {s['change_type']}")
        if s.get("diff_note"):
            print(f"    {s['diff_note'][:200]}")

    # ── Diff a specific node ───────────────────────────────────────────────────
    sep("Step 8: Diff node between versions")
    node_id_to_diff = selection_node_ids[0]
    r = httpx.get(f"{BASE_URL}/nodes/{node_id_to_diff}/diff", timeout=10)
    r.raise_for_status()
    diff = r.json()
    print(json.dumps(diff, indent=2))

    # ── Duplicate request test (cache policy) ─────────────────────────────────
    sep("Step 9: Submit same selection again (cache policy test)")
    r = httpx.post(
        f"{BASE_URL}/generate",
        json={"selection_id": selection_id, "force_regenerate": False},
        timeout=30,
    )
    r.raise_for_status()
    cached_gen = r.json()
    print(f"  is_cached: {cached_gen['is_cached']}  (expected: True)")
    assert cached_gen["is_cached"] is True, "Duplicate submit should return cached result"
    assert cached_gen["generation_id"] == gen_id, "Cached response must be the same generation"

    sep("Demo complete - all flows exercised successfully")


if __name__ == "__main__":
    main()
