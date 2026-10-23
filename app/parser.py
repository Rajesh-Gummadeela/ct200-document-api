"""
PDF parsing pipeline for the CT-200 CardioTrack manual.
Reconstructs the document hierarchy from PDF text using pdfplumber.

Design decisions:
- We use font-size heuristics (via pdfplumber character-level data) to identify
  headings vs. body text, since the CT-200 manual uses explicit heading styles.
- Heading levels are inferred from font size: title > H1 > H2 > H3.
- Duplicate headings (the 3.3 case) are handled by appending a disambiguating
  suffix ('a', 'b') to the path_key so they get distinct node IDs.
- Tables are extracted via pdfplumber's extract_tables(); figures are recorded
  if a page has image objects.
- Content hash = SHA-256(heading.strip() + "||" + body_text.strip())
"""
import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional, List

import pdfplumber


# ── Heading detection thresholds (tuned for the CT-200 PDF) ──────────────────
FONT_SIZE_TITLE = 16.0   # DocTitle / cover title
FONT_SIZE_H1 = 12.0      # Section headings (e.g. "1. Introduction")
FONT_SIZE_H2 = 10.5      # Subsection headings (e.g. "1.1 Intended Use")
FONT_SIZE_H3 = 10.0      # Sub-subsection headings
FONT_SIZE_BODY = 9.9     # Body text threshold (anything ≤ this)

HEADING_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)*)\.?\s+(.+)$"  # "3.1 Pressure Safety" or "1. Introduction" style
)
TITLE_PATTERN = re.compile(
    r"^(CardioTrack|User\s*&\s*Technical|Document\s*ID)", re.IGNORECASE
)


@dataclass
class RawNode:
    heading: str
    level: int          # 0=title, 1=H1, 2=H2, 3=H3
    section_number: str
    body_lines: List[str] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)

    @property
    def body_text(self) -> str:
        return "\n".join(self.body_lines).strip()

    @property
    def content_hash(self) -> str:
        raw = f"{self.heading.strip()}||{self.body_text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _classify_level(size: float) -> Optional[int]:
    """Return heading level (0-3) or None for body text."""
    if size >= FONT_SIZE_TITLE:
        return 0
    if size >= FONT_SIZE_H1:
        return 1
    if size >= FONT_SIZE_H2:
        return 2
    if size >= FONT_SIZE_H3:
        return 3
    return None


def _dominant_fontsize(chars: list) -> float:
    """Return the most frequent font size among a list of pdfplumber chars."""
    if not chars:
        return 0.0
    freq: dict[float, int] = {}
    for c in chars:
        s = round(float(c.get("size", 0)), 1)
        freq[s] = freq.get(s, 0) + 1
    return max(freq, key=freq.get)


def _is_bold(chars: list) -> bool:
    for c in chars:
        if "Bold" in (c.get("fontname") or ""):
            return True
    return False


def _extract_section_number(heading: str):
    m = HEADING_PATTERN.match(heading.strip())
    if m:
        return m.group(1), m.group(2)
    return "", heading.strip()


def _make_path_key(parent_path: str, section_number: str, heading: str) -> str:
    """Build a deterministic path key for cross-version matching."""
    slug = section_number if section_number else re.sub(r"\W+", "_", heading[:40]).strip("_")
    if parent_path:
        return f"{parent_path}/{slug}"
    return slug


def _resolve_path_key_duplicate(path_key: str, seen: set) -> str:
    """If path_key already used, append 'b', 'c', ... to disambiguate."""
    if path_key not in seen:
        return path_key
    for suffix in "bcdefghij":
        candidate = f"{path_key}_{suffix}"
        if candidate not in seen:
            return candidate
    return path_key + "_dup"


def parse_pdf(filepath: str) -> List[RawNode]:
    """
    Parse a CT-200 manual PDF into a flat list of RawNodes with hierarchy info.
    The caller is responsible for building the parent-child tree.
    """
    nodes: List[RawNode] = []
    current_node: Optional[RawNode] = None
    seen_paths: set = set()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract tables first so we can attach them to nodes
            raw_tables = page.extract_tables() or []

            # Get words with font info
            words = page.extract_words(
                extra_attrs=["fontname", "size"],
                use_text_flow=True,
                keep_blank_chars=False,
            ) or []

            # Group words into lines by approximate y-coordinate
            lines_dict: dict[float, list] = {}
            for w in words:
                y = round(float(w.get("top", 0)), 0)
                lines_dict.setdefault(y, []).append(w)

            sorted_ys = sorted(lines_dict.keys())

            for y in sorted_ys:
                line_words = lines_dict[y]
                line_text = " ".join(w["text"] for w in line_words).strip()
                if not line_text:
                    continue

                chars_approx = line_words  # use word-level size as proxy
                dom_size = _dominant_fontsize(chars_approx)
                is_bold = _is_bold(chars_approx)

                level = _classify_level(dom_size)

                # Heuristic: bold body-sized text is treated as H2 if it matches section pattern
                if level is None and is_bold and dom_size >= 9.0:
                    if HEADING_PATTERN.match(line_text) or TITLE_PATTERN.match(line_text):
                        level = 2

                if level is not None and (HEADING_PATTERN.match(line_text) or level == 0):
                    # Start a new node
                    section_number, heading_text = _extract_section_number(line_text)
                    if section_number:
                        full_heading = line_text
                    else:
                        full_heading = heading_text

                    # Determine parent path for path_key
                    parent_path = ""
                    if nodes:
                        for prev in reversed(nodes):
                            if prev.level < level:
                                # find its path key — we'll store it in _path_keys list
                                break

                    # Build path key via section number
                    path_key = _make_path_key(
                        _get_parent_path(nodes, level, seen_paths),
                        section_number,
                        heading_text
                    )
                    path_key = _resolve_path_key_duplicate(path_key, seen_paths)
                    seen_paths.add(path_key)

                    node = RawNode(
                        heading=full_heading,
                        level=level,
                        section_number=section_number,
                    )
                    # Attach tables that appear on this page to the most recent heading
                    # (crude but workable for single-heading-per-page cases)
                    if raw_tables and level <= 2:
                        node.tables = [
                            [[cell or "" for cell in row] for row in tbl]
                            for tbl in raw_tables
                        ]
                        raw_tables = []  # consume

                    # Stash path_key on node for tree building
                    node._path_key = path_key  # type: ignore[attr-defined]
                    nodes.append(node)
                    current_node = node
                else:
                    # Body text
                    if current_node is not None:
                        # Detect bullet lines
                        stripped = line_text.lstrip("•●◦▸-– \t")
                        if line_text.startswith(("•", "●", "◦", "▸", "-", "–")) and stripped:
                            current_node.bullets.append(stripped)
                        current_node.body_lines.append(line_text)

            # Any remaining tables on this page go to current node
            if raw_tables and current_node:
                current_node.tables.extend(
                    [[cell or "" for cell in row] for row in raw_tables]
                    for raw_tables in raw_tables
                )

            # Detect figure references
            images = getattr(page, "images", []) or []
            if images and current_node:
                for img in images:
                    current_node.figures.append(f"Figure on page {page_num+1}")

    return nodes


def _get_parent_path(nodes: list, level: int, seen: set) -> str:
    """Walk backward through nodes to find the closest ancestor's path_key."""
    for node in reversed(nodes):
        if node.level < level:
            return getattr(node, "_path_key", "")
    return ""


def build_tree(flat_nodes: List[RawNode]) -> List[dict]:
    """
    Convert flat RawNode list to a nested tree dict suitable for DB insertion.
    Returns a list of root-level dicts with 'children' lists.
    Handles duplicate headings at the same level (e.g., two "3.3" sections).
    """
    # Stack-based tree builder
    stack: List[dict] = []   # [(level, dict)]
    roots: List[dict] = []

    for rn in flat_nodes:
        node_dict = {
            "heading": rn.heading,
            "level": rn.level,
            "section_number": rn.section_number,
            "body_text": rn.body_text,
            "content_hash": rn.content_hash,
            "path_key": getattr(rn, "_path_key", rn.heading[:40]),
            "tables": rn.tables,
            "figures": rn.figures,
            "bullets": rn.bullets,
            "children": [],
            "node_order": 0,
        }

        # Pop stack until we find a parent
        while stack and stack[-1]["level"] >= rn.level:
            stack.pop()

        if stack:
            parent = stack[-1]
            node_dict["node_order"] = len(parent["children"])
            parent["children"].append(node_dict)
        else:
            node_dict["node_order"] = len(roots)
            roots.append(node_dict)

        stack.append(node_dict)

    return roots
