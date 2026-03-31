"""
Scaffold builder — converts study plan data into a study document skeleton.

When the user clicks "Create Study" from a plan, the frontend sends the
collected plan items (verses, commentaries, cross-refs, entities, symbols).
This service converts them into an ordered blocks array with placeholders
for the author's narrative.
"""

import uuid


def _block(block_type, data, meta=None):
    """Create a block with a generated UUID."""
    return {
        "id": str(uuid.uuid4()),
        "type": block_type,
        "data": data,
        "meta": meta or {},
    }


def _placeholder(text="Escreva aqui sua reflexao..."):
    """Create a placeholder paragraph block."""
    return _block("paragraph", {"html": f'<p class="placeholder">{text}</p>'})


def build_scaffold(plan_data):
    """
    Build a study document skeleton from plan data.

    Args:
        plan_data: dict with optional keys:
            - title: str
            - verses: list of {ref, version, text, book_osis, score?}
            - commentaries: list of {author_name, tradition, century, is_saint?,
                                     verse_ref, content, source}
            - crossrefs: list of {verse, connections: [{to_ref, votes, score?, strength?}]}
            - entities: list of {canonical_id, name, namespace, description}
            - symbols: list of {canonical_id, name, meanings?, progressions?}
            - themes: list of {theme_id, label, books?}
            - images: list of {image_id, url, title, artist?, verse_ref?}

    Returns:
        list of blocks (ready for Study.blocks)
    """
    blocks = []

    title = plan_data.get("title", "Novo Estudo")
    blocks.append(_block("heading", {"text": title, "level": 1}))
    blocks.append(_placeholder("Escreva aqui sua introducao..."))

    # Verses (sorted by score descending if available)
    verses = plan_data.get("verses", [])
    if verses:
        blocks.append(_block("divider", {"style": "ornament"}))
        blocks.append(_block("heading", {"text": "Referencias Principais", "level": 2}))

        # Sort by score (highest first), then by order
        sorted_verses = sorted(verses, key=lambda v: v.get("score", 0), reverse=True)

        for verse in sorted_verses:
            blocks.append(
                _block("verse_cite", {
                    "ref": verse.get("ref", ""),
                    "version": verse.get("version", "ARA"),
                    "text": verse.get("text", ""),
                    "book_osis": verse.get("book_osis", ""),
                })
            )
            blocks.append(_placeholder("Sua analise deste verso..."))

    # Commentaries
    commentaries = plan_data.get("commentaries", [])
    if commentaries:
        blocks.append(_block("divider", {"style": "ornament"}))
        blocks.append(_block("heading", {"text": "Vozes da Tradicao", "level": 2}))

        for comm in commentaries:
            blocks.append(
                _block("commentary_cite", {
                    "author_name": comm.get("author_name", ""),
                    "tradition": comm.get("tradition", ""),
                    "century": comm.get("century", ""),
                    "is_saint": comm.get("is_saint", False),
                    "verse_ref": comm.get("verse_ref", ""),
                    "content": comm.get("content", ""),
                    "source": comm.get("source", ""),
                })
            )

    # Cross-references
    crossrefs = plan_data.get("crossrefs", [])
    if crossrefs:
        blocks.append(_block("divider", {"style": "ornament"}))
        blocks.append(_block("heading", {"text": "Conexoes", "level": 2}))

        for xref in crossrefs:
            blocks.append(
                _block("crossref_network", {
                    "verse": xref.get("verse", ""),
                    "connections": xref.get("connections", []),
                    "layout": "table",
                })
            )

    # Entities
    entities = plan_data.get("entities", [])
    if entities:
        blocks.append(_block("divider", {"style": "ornament"}))
        blocks.append(_block("heading", {"text": "Entidades", "level": 2}))

        for entity in entities:
            blocks.append(
                _block("entity_card", {
                    "canonical_id": entity.get("canonical_id", ""),
                    "name": entity.get("name", ""),
                    "namespace": entity.get("namespace", ""),
                    "description": entity.get("description", ""),
                })
            )

    # Symbols
    symbols = plan_data.get("symbols", [])
    if symbols:
        blocks.append(_block("divider", {"style": "ornament"}))
        blocks.append(_block("heading", {"text": "Simbolos", "level": 2}))

        for symbol in symbols:
            blocks.append(
                _block("symbol_card", {
                    "canonical_id": symbol.get("canonical_id", ""),
                    "name": symbol.get("name", ""),
                    "meanings": symbol.get("meanings", []),
                    "progressions": symbol.get("progressions", []),
                })
            )

    # Themes
    themes = plan_data.get("themes", [])
    if themes:
        for theme in themes:
            blocks.append(
                _block("theme_progression", {
                    "theme_id": theme.get("theme_id", ""),
                    "label": theme.get("label", ""),
                    "books": theme.get("books", []),
                })
            )

    # Images
    images = plan_data.get("images", [])
    if images:
        for img in images:
            blocks.append(
                _block("image_embed", {
                    "image_id": img.get("image_id", ""),
                    "url": img.get("url", ""),
                    "title": img.get("title", ""),
                    "artist": img.get("artist", ""),
                    "verse_ref": img.get("verse_ref", ""),
                })
            )

    # Conclusion placeholder
    blocks.append(_block("divider", {"style": "line"}))
    blocks.append(_placeholder("Escreva aqui sua conclusao..."))

    return blocks
