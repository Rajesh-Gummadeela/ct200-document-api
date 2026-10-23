"""
Staleness detection service.

Design:
- A generation is considered "stale" if any node whose content was captured in
  the selection snapshot has had its content_hash change in the latest version.
- We compare snapshot_content_hash (stored in SelectionItem) with the current
  content_hash of the matching node (matched by path_key in the latest version).
- Known limitation: a one-word change in a non-critical field is treated the
  same as a changed safety threshold. We report this honestly via change_type.
- If the node no longer exists in the latest version (removed section), we
  report "node_removed".
- We do not auto-flag what *kind* of change occurred — that would require
  semantic diff, which is out of scope.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import DocNode, DocumentVersion, Document, SelectionItem, Selection
from app.schemas import StalenessInfo


def _get_latest_version(document_id: int, db: Session) -> Optional[DocumentVersion]:
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id, DocumentVersion.is_latest == True)
        .first()
    )


def _get_any_document(db: Session) -> Optional[Document]:
    """We assume a single document (CT-200). For multi-doc systems, pass doc_id."""
    return db.query(Document).first()


def compute_staleness(selection_id: int, db: Session) -> List[StalenessInfo]:
    """
    For each SelectionItem in a selection, determine whether the captured
    content still matches the current latest version.
    """
    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if not selection:
        return []

    # Find the document by looking at any node in the selection
    doc = _get_any_document(db)
    if not doc:
        return []

    latest_version = _get_latest_version(doc.id, db)

    results: List[StalenessInfo] = []

    for item in selection.items:
        node = item.node
        if node is None:
            results.append(StalenessInfo(
                node_id=item.node_id,
                path_key="(unknown)",
                heading="(node deleted)",
                snapshot_hash=item.snapshot_content_hash,
                current_hash=None,
                is_stale=True,
                change_type="node_removed",
                diff_note="The node record no longer exists in the database.",
            ))
            continue

        # Find node in latest version by path_key
        if latest_version:
            current_node = (
                db.query(DocNode)
                .filter(
                    DocNode.version_id == latest_version.id,
                    DocNode.path_key == node.path_key,
                )
                .first()
            )
        else:
            current_node = None

        if current_node is None:
            change_type = "not_in_latest"
            is_stale = True
            diff_note = (
                f"Node with path_key='{node.path_key}' not found in latest version "
                f"(v{latest_version.version_number if latest_version else 'N/A'}). "
                "The section may have been removed or renamed."
            )
            current_hash = None
        elif current_node.content_hash == item.snapshot_content_hash:
            change_type = "unchanged"
            is_stale = False
            diff_note = None
            current_hash = current_node.content_hash
        else:
            change_type = "content_changed"
            is_stale = True
            current_hash = current_node.content_hash
            # Build a lightweight diff note
            diff_note = _build_diff_note(
                item.snapshot_heading or node.heading,
                item.snapshot_body_text or node.body_text,
                current_node.body_text,
            )

        results.append(StalenessInfo(
            node_id=item.node_id,
            path_key=node.path_key,
            heading=node.heading,
            snapshot_hash=item.snapshot_content_hash,
            current_hash=current_hash,
            is_stale=is_stale,
            change_type=change_type,
            diff_note=diff_note,
        ))

    return results


def _build_diff_note(heading: str, old_text: str, new_text: str) -> str:
    """
    Produce a short, human-readable diff summary.
    Limitation: this is word-level, not semantic. A threshold change from
    '295 mmHg' to '290 mmHg' looks the same as a typo fix.
    """
    old_words = set(old_text.split())
    new_words = set(new_text.split())
    added = new_words - old_words
    removed = old_words - new_words

    parts = []
    if removed:
        sample = list(removed)[:5]
        parts.append(f"Removed words: {', '.join(sample)}" +
                     (" ..." if len(removed) > 5 else ""))
    if added:
        sample = list(added)[:5]
        parts.append(f"Added words: {', '.join(sample)}" +
                     (" ..." if len(added) > 5 else ""))

    if not parts:
        return "Content hash changed but word sets are identical (possible whitespace/encoding change)."

    return f"Section '{heading}' changed. " + " | ".join(parts) + (
        "\n\nNote: This is a word-level diff. A safety-critical threshold change "
        "(e.g. '295 mmHg' -> '290 mmHg') appears identical in severity to a "
        "minor wording edit. Manual review is required for safety-critical sections."
    )
