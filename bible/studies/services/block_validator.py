"""
Block validation for study documents.

Each block has: {id, type, order, data, meta}
This module validates the `data` payload per block type.

Block categories:
- Narrative (author's voice): paragraph, heading, callout, divider
- Citation (API data inline): verse_cite, verse_compare, commentary_cite
- Embed (structured visuals): reference_table, crossref_network, entity_card,
  symbol_card, image_embed, connection_map, comparison_table, theme_progression
"""

VALID_BLOCK_TYPES = {
    # Narrative
    "paragraph",
    "heading",
    "callout",
    "divider",
    # Citation
    "verse_cite",
    "verse_compare",
    "commentary_cite",
    # Embed
    "reference_table",
    "crossref_network",
    "entity_card",
    "symbol_card",
    "image_embed",
    "connection_map",
    "comparison_table",
    "theme_progression",
}

# Required fields per block type (in the `data` dict)
REQUIRED_DATA_FIELDS = {
    "paragraph": ["html"],
    "heading": ["text", "level"],
    "callout": ["style", "html"],
    "divider": [],
    "verse_cite": ["ref", "version", "text"],
    "verse_compare": ["ref", "versions", "texts"],
    "commentary_cite": ["author_name", "verse_ref", "content"],
    "reference_table": ["refs"],
    "crossref_network": ["verse", "connections"],
    "entity_card": ["canonical_id", "name", "namespace"],
    "symbol_card": ["canonical_id", "name"],
    "image_embed": ["image_id", "url", "title"],
    "connection_map": ["content", "format"],
    "comparison_table": ["headers", "rows"],
    "theme_progression": ["theme_id", "label"],
}

VALID_HEADING_LEVELS = {1, 2, 3}
VALID_CALLOUT_STYLES = {"insight", "warning", "question", "patristic"}
VALID_DIVIDER_STYLES = {"line", "ornament", "space"}
VALID_MAP_FORMATS = {"ascii", "mermaid"}
VALID_NETWORK_LAYOUTS = {"table", "graph"}


def validate_block(block, index=0):
    """
    Validate a single block. Returns list of error strings (empty = valid).
    """
    errors = []
    prefix = f"blocks[{index}]"

    if not isinstance(block, dict):
        return [f"{prefix}: must be a dict"]

    # Required envelope fields
    block_type = block.get("type")
    if not block_type:
        errors.append(f"{prefix}: missing 'type'")
        return errors

    if block_type not in VALID_BLOCK_TYPES:
        errors.append(f"{prefix}: unknown type '{block_type}'")
        return errors

    if "id" not in block:
        errors.append(f"{prefix}: missing 'id'")

    data = block.get("data")
    if data is None:
        # Dividers can have empty data
        if block_type != "divider":
            errors.append(f"{prefix}: missing 'data'")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{prefix}.data: must be a dict")
        return errors

    # Required data fields
    required = REQUIRED_DATA_FIELDS.get(block_type, [])
    for field in required:
        if field not in data:
            errors.append(f"{prefix}.data: missing required field '{field}'")

    # Type-specific validation
    if block_type == "heading":
        level = data.get("level")
        if level is not None and level not in VALID_HEADING_LEVELS:
            errors.append(f"{prefix}.data.level: must be 1, 2, or 3")

    elif block_type == "callout":
        style = data.get("style")
        if style and style not in VALID_CALLOUT_STYLES:
            errors.append(
                f"{prefix}.data.style: must be one of {VALID_CALLOUT_STYLES}"
            )

    elif block_type == "divider":
        style = data.get("style")
        if style and style not in VALID_DIVIDER_STYLES:
            errors.append(
                f"{prefix}.data.style: must be one of {VALID_DIVIDER_STYLES}"
            )

    elif block_type == "verse_compare":
        versions = data.get("versions")
        texts = data.get("texts")
        if isinstance(versions, list) and isinstance(texts, list):
            if len(versions) != len(texts):
                errors.append(
                    f"{prefix}.data: versions and texts must have same length"
                )

    elif block_type == "reference_table":
        refs = data.get("refs")
        if isinstance(refs, list):
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    errors.append(f"{prefix}.data.refs[{i}]: must be a dict")
                elif "ref" not in ref:
                    errors.append(f"{prefix}.data.refs[{i}]: missing 'ref'")

    elif block_type == "crossref_network":
        layout = data.get("layout")
        if layout and layout not in VALID_NETWORK_LAYOUTS:
            errors.append(
                f"{prefix}.data.layout: must be one of {VALID_NETWORK_LAYOUTS}"
            )

    elif block_type == "connection_map":
        fmt = data.get("format")
        if fmt and fmt not in VALID_MAP_FORMATS:
            errors.append(
                f"{prefix}.data.format: must be one of {VALID_MAP_FORMATS}"
            )

    elif block_type == "comparison_table":
        headers = data.get("headers")
        rows = data.get("rows")
        if isinstance(headers, list) and isinstance(rows, list):
            col_count = len(headers)
            for i, row in enumerate(rows):
                if isinstance(row, list) and len(row) != col_count:
                    errors.append(
                        f"{prefix}.data.rows[{i}]: expected {col_count} columns"
                    )

    return errors


def validate_blocks(blocks):
    """
    Validate the full blocks array. Returns list of error strings.
    """
    if not isinstance(blocks, list):
        return ["blocks: must be a list"]

    errors = []
    seen_ids = set()

    for i, block in enumerate(blocks):
        block_errors = validate_block(block, i)
        errors.extend(block_errors)

        # Check for duplicate IDs
        block_id = block.get("id") if isinstance(block, dict) else None
        if block_id:
            if block_id in seen_ids:
                errors.append(f"blocks[{i}]: duplicate id '{block_id}'")
            seen_ids.add(block_id)

    return errors
