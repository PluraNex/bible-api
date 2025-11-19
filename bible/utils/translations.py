"""Translation utilities for bible domain."""

# Mapeamento de traduções de testamentos
TESTAMENT_TRANSLATIONS = {
    "pt-BR": {"Old Testament": "Antigo Testamento", "New Testament": "Novo Testamento"},
    "pt": {"Old Testament": "Antigo Testamento", "New Testament": "Novo Testamento"},
    "es": {"Old Testament": "Antiguo Testamento", "New Testament": "Nuevo Testamento"},
    "en": {"Old Testament": "Old Testament", "New Testament": "New Testament"},
    "fr": {"Old Testament": "Ancien Testament", "New Testament": "Nouveau Testament"},
    "de": {"Old Testament": "Altes Testament", "New Testament": "Neues Testament"},
    "it": {"Old Testament": "Antico Testamento", "New Testament": "Nuovo Testamento"},
}


def get_testament_translation(testament_name: str, lang_code: str) -> str:
    """
    Retorna a tradução do nome do testamento no idioma especificado.

    Args:
        testament_name: Nome original do testamento (e.g., "Old Testament")
        lang_code: Código do idioma (e.g., "pt-BR", "en")

    Returns:
        Nome traduzido do testamento ou o nome original se tradução não existir

    Examples:
        >>> get_testament_translation("Old Testament", "pt-BR")
        "Antigo Testamento"
        >>> get_testament_translation("New Testament", "es")
        "Nuevo Testamento"
    """
    return TESTAMENT_TRANSLATIONS.get(lang_code, {}).get(testament_name, testament_name)
