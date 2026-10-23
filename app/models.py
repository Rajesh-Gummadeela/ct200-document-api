"""
Database models using SQLAlchemy + SQLite.
Stores document tree, versions, selections.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Boolean, UniqueConstraint, Float, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Logical document identity (one row per unique document title)."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """A specific ingested version of a document."""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)  # 1, 2, 3...
    source_filename = Column(String(512))
    ingested_at = Column(DateTime, default=datetime.utcnow)
    is_latest = Column(Boolean, default=True)

    document = relationship("Document", back_populates="versions")
    nodes = relationship("DocNode", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("document_id", "version_number"),)


class DocNode(Base):
    """
    A single node in the document hierarchy tree.
    Each node has a heading, level, body text, and content hash.
    """
    __tablename__ = "doc_nodes"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("doc_nodes.id"), nullable=True)

    # Structural info
    heading = Column(String(512), nullable=False)
    level = Column(Integer, nullable=False)  # 0=document title, 1=H1, 2=H2, 3=H3
    body_text = Column(Text, default="")
    section_number = Column(String(64), default="")  # e.g. "3.1", "3.3a"
    node_order = Column(Integer, default=0)           # position among siblings

    # Logical identity: path-based key for cross-version matching
    path_key = Column(String(1024), nullable=False)   # e.g. "3/3.1/3.1.2"

    # Content hash (SHA-256 of heading + body_text)
    content_hash = Column(String(64), nullable=False)

    # Parsed metadata (tables, figures, bullet lists as JSON blobs)
    tables = Column(JSON, default=list)
    figures = Column(JSON, default=list)
    bullets = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    version = relationship("DocumentVersion", back_populates="nodes")
    children = relationship(
        "DocNode",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )
    parent = relationship(
        "DocNode",
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side="DocNode.id",
    )
    selection_items = relationship("SelectionItem", back_populates="node")

    __table_args__ = (
        UniqueConstraint("version_id", "path_key", name="uq_version_path"),
    )


class Selection(Base):
    """A named, version-pinned selection of document nodes."""
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("SelectionItem", back_populates="selection", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="selection")


class SelectionItem(Base):
    """A single node+version pair within a selection."""
    __tablename__ = "selection_items"

    id = Column(Integer, primary_key=True)
    selection_id = Column(Integer, ForeignKey("selections.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("doc_nodes.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)

    # Snapshot of node content at time of selection (for staleness detection)
    snapshot_content_hash = Column(String(64), nullable=False)
    snapshot_heading = Column(String(512))
    snapshot_body_text = Column(Text)

    selection = relationship("Selection", back_populates="items")
    node = relationship("DocNode", back_populates="selection_items")


class Generation(Base):
    """
    Metadata record linking a Selection to a MongoDB generation document.
    Stored in SQLite so we can do relational queries; the full LLM output
    lives in MongoDB.
    """
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True)
    selection_id = Column(Integer, ForeignKey("selections.id"), nullable=False)
    mongo_id = Column(String(64), nullable=False)  # MongoDB ObjectId as string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Staleness info at retrieval time is computed dynamically, not stored
    selection = relationship("Selection", back_populates="generations")
