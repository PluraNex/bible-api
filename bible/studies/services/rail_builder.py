"""
Rail builder — builds compact preview payload for the study rail panel.

The rail view shows a condensed version of the study:
- Metadata (title, author, type, tags)
- First 3 content blocks as preview
- Block count and type summary
"""


def build_rail_preview(study):
    """
    Build a compact rail preview from a Study instance.

    Returns dict with metadata and preview blocks.
    """
    preview_blocks = []
    block_type_counts = {}

    for block in study.blocks or []:
        if not isinstance(block, dict):
            continue

        btype = block.get("type", "unknown")
        block_type_counts[btype] = block_type_counts.get(btype, 0) + 1

        # Collect first 3 meaningful blocks for preview
        if len(preview_blocks) < 3 and btype in (
            "paragraph",
            "heading",
            "verse_cite",
            "callout",
        ):
            preview_blocks.append(block)

    return {
        "slug": study.slug,
        "title": study.title,
        "subtitle": study.subtitle,
        "study_type": study.study_type,
        "difficulty": study.difficulty,
        "description": study.description,
        "tags": study.tags,
        "block_count": study.block_count,
        "block_summary": block_type_counts,
        "preview_blocks": preview_blocks,
    }
