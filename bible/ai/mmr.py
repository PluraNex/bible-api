"""
MMR (Maximal Marginal Relevance) Module - Diversificação de Resultados

Este módulo implementa MMR para evitar resultados redundantes na busca RAG.
O problema principal: mesma passagem bíblica retornada em múltiplas versões.

Fundamentação Teórica:
- Carbonell & Goldstein (1998) "The Use of MMR, Diversity-Based Reranking"
- MMR balanceia relevância (query match) com diversidade (novidade)

Fórmula:
    MMR(d) = λ * Sim(d, Q) - (1-λ) * max[Sim(d, S)]
    
    Onde:
    - Sim(d, Q) = similaridade do documento d com a query Q
    - Sim(d, S) = similaridade de d com documentos já selecionados S
    - λ = trade-off (0.7 recomendado para bíblia)

Aplicação Bíblica:
- Evita retornar 1 João 4:16 em 5 versões diferentes
- Promove diversidade de passagens sobre o mesmo tema
- Mantém relevância enquanto expande cobertura temática

Referências:
- https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf
- https://arxiv.org/abs/2005.11401 (Dense Passage Retrieval)

Versão: 1.0.0
Data: Nov 2025
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MMRConfig:
    """Configuração do algoritmo MMR."""
    
    lambda_param: float = 0.7  # Trade-off relevância vs diversidade
    similarity_threshold: float = 0.85  # Threshold para considerar "duplicata"
    use_canonical_id: bool = True  # Usar ID canônico para detectar mesmo versículo
    
    def __post_init__(self):
        if not 0 <= self.lambda_param <= 1:
            raise ValueError("lambda_param deve estar entre 0 e 1")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold deve estar entre 0 e 1")


@dataclass
class MMRResult:
    """Resultado do processo MMR."""
    
    hits: list[dict[str, Any]]
    original_count: int
    deduplicated_count: int
    duplicates_removed: int
    diversity_score: float  # 0-1, quanto maior mais diverso
    config: MMRConfig = field(default_factory=MMRConfig)
    
    @property
    def dedup_ratio(self) -> float:
        """Proporção de resultados mantidos após deduplicação."""
        if self.original_count == 0:
            return 1.0
        return self.deduplicated_count / self.original_count


def cosine_similarity_vectors(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calcula similaridade cosseno entre dois vetores."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def get_canonical_verse_id(hit: dict[str, Any]) -> str:
    """
    Gera ID canônico para um versículo (independente de versão).
    
    Formato: "{book_osis}:{chapter}:{verse}"
    Exemplo: "1John:4:16"
    """
    book = hit.get("book_osis", "")
    if not book:
        book_field = hit.get("book")
        if isinstance(book_field, dict):
            book = book_field.get("osis_code", "")
        elif isinstance(book_field, str):
            book = book_field
    chapter = hit.get("chapter", 0)
    verse = hit.get("verse", 0) or hit.get("number", 0)
    return f"{book}:{chapter}:{verse}"


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calcula similaridade entre dois textos usando Jaccard.
    
    Útil quando não temos embeddings disponíveis.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def mmr_diversify(
    hits: list[dict[str, Any]],
    *,
    top_k: int | None = None,
    lambda_param: float = 0.7,
    use_embeddings: bool = False,
    embeddings: dict[int, np.ndarray] | None = None,
) -> MMRResult:
    """
    Aplica MMR para diversificar resultados.
    
    Estratégia:
    1. Se use_embeddings=True, usa similaridade de embeddings
    2. Senão, usa ID canônico para detectar duplicatas exatas
    3. Para duplicatas, mantém apenas a de maior score
    
    Args:
        hits: Lista de resultados ordenados por relevância
        top_k: Número máximo de resultados (None = todos)
        lambda_param: Trade-off relevância/diversidade (0.7 recomendado)
        use_embeddings: Se True, usa embeddings para calcular similaridade
        embeddings: Dict mapeando verse_id → embedding (se use_embeddings=True)
    
    Returns:
        MMRResult com hits diversificados
    """
    if not hits:
        return MMRResult(
            hits=[],
            original_count=0,
            deduplicated_count=0,
            duplicates_removed=0,
            diversity_score=1.0,
        )
    
    config = MMRConfig(lambda_param=lambda_param)
    original_count = len(hits)
    
    if use_embeddings and embeddings:
        # MMR completo com embeddings
        selected = _mmr_with_embeddings(hits, embeddings, top_k, lambda_param)
    else:
        # MMR simplificado: deduplicação por ID canônico
        selected = _mmr_by_canonical_id(hits, top_k)
    
    # Calcular score de diversidade
    diversity_score = _calculate_diversity_score(selected)
    
    duplicates_removed = original_count - len(selected)
    
    logger.info(
        f"MMR: {original_count} → {len(selected)} hits "
        f"({duplicates_removed} duplicates removed, "
        f"diversity: {diversity_score:.2f})"
    )
    
    return MMRResult(
        hits=selected,
        original_count=original_count,
        deduplicated_count=len(selected),
        duplicates_removed=duplicates_removed,
        diversity_score=diversity_score,
        config=config,
    )


def _mmr_by_canonical_id(
    hits: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    MMR simplificado: mantém apenas uma versão de cada versículo.
    
    Estratégia: para cada versículo canônico, manter o de maior score.
    """
    seen_canonical: dict[str, dict[str, Any]] = {}
    
    for hit in hits:
        canonical_id = get_canonical_verse_id(hit)
        score = hit.get("similarity") or hit.get("score") or hit.get("rrf_score", 0)
        
        if canonical_id not in seen_canonical:
            # Primeiro encontro deste versículo
            hit_copy = hit.copy()
            hit_copy["canonical_id"] = canonical_id
            hit_copy["is_primary"] = True
            seen_canonical[canonical_id] = hit_copy
        else:
            # Já vimos este versículo - manter o de maior score
            existing_score = (
                seen_canonical[canonical_id].get("similarity") or 
                seen_canonical[canonical_id].get("score") or 
                seen_canonical[canonical_id].get("rrf_score", 0)
            )
            if score > existing_score:
                hit_copy = hit.copy()
                hit_copy["canonical_id"] = canonical_id
                hit_copy["is_primary"] = True
                seen_canonical[canonical_id] = hit_copy
    
    # Ordenar por score original
    result = sorted(
        seen_canonical.values(),
        key=lambda x: x.get("similarity") or x.get("score") or x.get("rrf_score", 0),
        reverse=True
    )
    
    if top_k:
        result = result[:top_k]
    
    return result


def _mmr_with_embeddings(
    hits: list[dict[str, Any]],
    embeddings: dict[int, np.ndarray],
    top_k: int | None = None,
    lambda_param: float = 0.7,
) -> list[dict[str, Any]]:
    """
    MMR completo usando embeddings para calcular similaridade.
    
    Algoritmo:
    1. Selecionar documento mais relevante
    2. Para cada documento restante, calcular:
       MMR = λ * relevance - (1-λ) * max_similarity_to_selected
    3. Selecionar documento com maior MMR
    4. Repetir até top_k
    """
    if not hits:
        return []
    
    top_k = top_k or len(hits)
    remaining = list(range(len(hits)))
    selected_indices: list[int] = []
    selected_embeddings: list[np.ndarray] = []
    
    # Primeiro: selecionar o mais relevante
    first_idx = remaining.pop(0)
    selected_indices.append(first_idx)
    
    verse_id = hits[first_idx].get("verse_id")
    if verse_id in embeddings:
        selected_embeddings.append(embeddings[verse_id])
    
    # Iterar até top_k
    while len(selected_indices) < top_k and remaining:
        best_idx = None
        best_mmr = float("-inf")
        
        for idx in remaining:
            hit = hits[idx]
            relevance = hit.get("similarity") or hit.get("score") or hit.get("rrf_score", 0)
            
            # Calcular máxima similaridade com selecionados
            max_sim = 0.0
            verse_id = hit.get("verse_id")
            
            if verse_id in embeddings and selected_embeddings:
                hit_emb = embeddings[verse_id]
                for sel_emb in selected_embeddings:
                    sim = cosine_similarity_vectors(hit_emb, sel_emb)
                    max_sim = max(max_sim, sim)
            
            # Calcular MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
            
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = idx
        
        if best_idx is not None:
            remaining.remove(best_idx)
            selected_indices.append(best_idx)
            
            verse_id = hits[best_idx].get("verse_id")
            if verse_id in embeddings:
                selected_embeddings.append(embeddings[verse_id])
    
    # Construir lista de resultados
    result = []
    for i, idx in enumerate(selected_indices):
        hit_copy = hits[idx].copy()
        hit_copy["mmr_rank"] = i
        hit_copy["canonical_id"] = get_canonical_verse_id(hits[idx])
        result.append(hit_copy)
    
    return result


def _calculate_diversity_score(hits: list[dict[str, Any]]) -> float:
    """
    Calcula score de diversidade dos resultados.
    
    Baseado na proporção de versículos canônicos únicos.
    1.0 = todos únicos, 0.0 = todos iguais
    """
    if not hits:
        return 1.0
    
    canonical_ids = set()
    for hit in hits:
        canonical_id = get_canonical_verse_id(hit)
        canonical_ids.add(canonical_id)
    
    return len(canonical_ids) / len(hits)


def deduplicate_by_version(
    hits: list[dict[str, Any]],
    preferred_versions: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Remove duplicatas mantendo versão preferida.
    
    Args:
        hits: Lista de resultados
        preferred_versions: Lista ordenada de preferência (ex: ["NVI", "ARA", "ACF"])
    
    Returns:
        Lista sem duplicatas, com versão preferida quando disponível
    """
    if not preferred_versions:
        preferred_versions = ["NVI", "NAA", "ARA", "ACF", "AS21"]  # Default PT
    
    version_priority = {v: i for i, v in enumerate(preferred_versions)}
    
    # Agrupar por versículo canônico
    by_canonical: dict[str, list[dict[str, Any]]] = {}
    
    for hit in hits:
        canonical_id = get_canonical_verse_id(hit)
        if canonical_id not in by_canonical:
            by_canonical[canonical_id] = []
        by_canonical[canonical_id].append(hit)
    
    # Para cada grupo, selecionar o melhor
    result = []
    for canonical_id, group in by_canonical.items():
        # Ordenar por: versão preferida, depois por score
        def sort_key(h):
            version = h.get("version") or h.get("version_code", "")
            priority = version_priority.get(version, 999)
            score = h.get("similarity") or h.get("score") or 0
            return (priority, -score)
        
        group.sort(key=sort_key)
        
        best = group[0].copy()
        best["canonical_id"] = canonical_id
        best["versions_available"] = [
            h.get("version") or h.get("version_code") 
            for h in group
        ]
        result.append(best)
    
    # Ordenar resultado final por score
    result.sort(
        key=lambda x: x.get("similarity") or x.get("score") or 0,
        reverse=True
    )
    
    return result
