"""
Unit tests for AI utility functions (helper functions).

Tests helper functions from bible.ai.retrieval module:
- _vector_array_sql(): Vector to SQL array conversion
- _normalize_query(): Text normalization for cache
- _cosine(): Cosine similarity calculation

Following best practices §2: Unit tests for isolated logic.
"""

import pytest

from bible.ai import retrieval


@pytest.mark.unit
class TestVectorArraySQL:
    """Tests for _vector_array_sql() helper function."""

    def test_valid_vector_conversion(self):
        """Testa conversão válida de vetor Python para formato SQL ARRAY."""
        vec = [0.1, 0.2, 0.3]
        result = retrieval._vector_array_sql(vec, 3)

        assert "ARRAY[" in result
        assert "0.1" in result
        assert "0.2" in result
        assert "0.3" in result
        assert "::vector(3)" in result

    def test_empty_vector_raises_error(self):
        """Testa que vetor vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Vector vazio"):
            retrieval._vector_array_sql([], 0)

    def test_wrong_dimension_smaller_raises_error(self):
        """Testa que vetor menor que dimensão esperada levanta ValueError."""
        with pytest.raises(ValueError, match="Dimensão incorreta"):
            retrieval._vector_array_sql([0.1, 0.2], 3)

    def test_truncates_larger_dimension(self):
        """Testa que vetor maior que dimensão esperada é truncado."""
        vec = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = retrieval._vector_array_sql(vec, 3)

        # Deve truncar para 3 elementos (2 vírgulas)
        assert result.count(",") == 2
        assert "0.1" in result
        assert "0.2" in result
        assert "0.3" in result
        assert "0.4" not in result

    def test_handles_float_precision(self):
        """Testa que lida corretamente com precisão de floats."""
        vec = [0.123456789, 0.987654321]
        result = retrieval._vector_array_sql(vec, 2)

        # Python trunca floats para precisão padrão
        assert "0.1234" in result
        assert "0.9876" in result


@pytest.mark.unit
class TestNormalizeQuery:
    """Tests for _normalize_query() helper function."""

    def test_lowercase_conversion(self):
        """Testa conversão para lowercase."""
        assert retrieval._normalize_query("AMOR DE DEUS") == "amor de deus"
        assert retrieval._normalize_query("João 3:16") == "joão 3:16"

    def test_strip_whitespace(self):
        """Testa remoção de espaços extras."""
        assert retrieval._normalize_query("  amor  de  deus  ") == "amor de deus"
        assert retrieval._normalize_query("\n\t amor \t\n") == "amor"

    def test_preserves_special_characters(self):
        """Testa que preserva caracteres especiais."""
        assert retrieval._normalize_query("João 3:16") == "joão 3:16"
        assert retrieval._normalize_query("amor ♥ αγάπη") == "amor ♥ αγάπη"

    def test_empty_string(self):
        """Testa string vazia."""
        assert retrieval._normalize_query("") == ""
        assert retrieval._normalize_query("   ") == ""

    def test_unicode_handling(self):
        """Testa tratamento correto de unicode."""
        assert retrieval._normalize_query("Αγάπη Θεού") == "αγάπη θεού"
        assert retrieval._normalize_query("Café") == "café"


@pytest.mark.unit
class TestCosineSimilarity:
    """Tests for _cosine() helper function."""

    def test_identical_vectors(self):
        """Testa que vetores idênticos têm similaridade 1.0."""
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert abs(retrieval._cosine(a, b) - 1.0) < 0.001

    def test_orthogonal_vectors(self):
        """Testa que vetores ortogonais têm similaridade 0.0."""
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(retrieval._cosine(a, b) - 0.0) < 0.001

    def test_opposite_vectors(self):
        """Testa que vetores opostos têm similaridade -1.0."""
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(retrieval._cosine(a, b) - (-1.0)) < 0.001

    def test_empty_vectors(self):
        """Testa que vetores vazios retornam 0.0."""
        assert retrieval._cosine([], []) == 0.0

    def test_zero_vectors(self):
        """Testa que vetores de zeros retornam 0.0."""
        a = [0.0, 0.0, 0.0]
        b = [0.0, 0.0, 0.0]
        assert retrieval._cosine(a, b) == 0.0

    def test_normalized_vectors(self):
        """Testa similaridade com vetores normalizados."""
        import math

        # Vetores unitários em 45 graus
        a = [1 / math.sqrt(2), 1 / math.sqrt(2)]
        b = [1.0, 0.0]
        similarity = retrieval._cosine(a, b)
        # cos(45°) = 1/sqrt(2) ≈ 0.707
        assert abs(similarity - 1 / math.sqrt(2)) < 0.001

    def test_high_dimensional_vectors(self):
        """Testa com vetores de alta dimensionalidade (simula embeddings)."""
        import random

        random.seed(42)

        # Simular embeddings de 1536 dimensões
        a = [random.random() for _ in range(1536)]
        b = [random.random() for _ in range(1536)]

        similarity = retrieval._cosine(a, b)

        # Deve estar entre -1 e 1
        assert -1.0 <= similarity <= 1.0
