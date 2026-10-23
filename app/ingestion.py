"""
Ingestion service: parses a PDF and persists it as a versioned document tree.
"""
import os
from sqlalchemy.orm import Session

from app import parser as doc_parser
from app.models import Document, DocumentVersion, DocNode
from app.database import get_db


def _insert_nodes(
    db: Session,
    nodes: list,
    version_id: int,
    parent_db_id: int | None = None,
) -> int:
    """Recursively insert tree nodes; returns count of nodes inserted."""
    count = 0
    for node_dict in nodes:
        db_node = DocNode(
            version_id=version_id,
            parent_id=parent_db_id,
            heading=node_dict["heading"],
            level=node_dict["level"],
            body_text=node_dict.get("body_text", ""),
            section_number=node_dict.get("section_number", ""),
            node_order=node_dict.get("node_order", 0),
            path_key=node_dict["path_key"],
            content_hash=node_dict["content_hash"],
            tables=node_dict.get("tables", []),
            figures=node_dict.get("figures", []),
            bullets=node_dict.get("bullets", []),
        )
        db.add(db_node)
        db.flush()  # get db_node.id

        count += 1
        children = node_dict.get("children", [])
        if children:
            count += _insert_nodes(db, children, version_id, db_node.id)

    return count


def ingest_pdf(
    filepath: str,
    document_title: str,
    db: Session,
) -> dict:
    """
    Parse the PDF, determine the next version number, persist tree to SQLite.
    Returns a summary dict.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDF not found: {filepath}")

    # 1. Parse PDF
    flat_nodes = doc_parser.parse_pdf(filepath)
    tree = doc_parser.build_tree(flat_nodes)

    # 2. Find or create Document record
    doc = db.query(Document).filter(Document.title == document_title).first()
    if not doc:
        doc = Document(title=document_title)
        db.add(doc)
        db.flush()

    # 3. Determine next version number
    existing_versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc.id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )
    next_version = (existing_versions[0].version_number + 1) if existing_versions else 1

    # 4. Mark all previous versions as not latest
    for v in existing_versions:
        v.is_latest = False

    # 5. Create new version
    source_filename = os.path.basename(filepath)
    version = DocumentVersion(
        document_id=doc.id,
        version_number=next_version,
        source_filename=source_filename,
        is_latest=True,
    )
    db.add(version)
    db.flush()

    # 6. Insert tree
    nodes_created = _insert_nodes(db, tree, version.id, None)

    db.commit()

    return {
        "document_id": doc.id,
        "document_title": doc.title,
        "version_id": version.id,
        "version_number": next_version,
        "nodes_created": nodes_created,
        "message": f"Ingested '{document_title}' as version {next_version} ({nodes_created} nodes).",
    }
