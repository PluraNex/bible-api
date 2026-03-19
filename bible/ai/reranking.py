"""
Two-Stage Reranking Module - Reordenação com Embedding Large

Este módulo implementa reranking em dois estágios:
1. Stage 1: Retrieval rápido com embedding-small (1536 dim)
2. Stage 2: Reranking preciso com embedding-large (3072 dim)

Fundamentação Teórica:
- Two-Stage Retrieval é uma técnica consolidada em Information Retrieval
- Primeiro estágio prioriza recall (encontrar candidatos relevantes)
- Segundo estágio prioriza precision (ordenar por relevância)

Referências:
- Nogueira & Cho (2019) "Passage Re-ranking with BERT"
- Karpukhin et al. (2020) "Dense Passage Retrieval for Open-Domain QA"
- OpenAI Embeddings: text-embedding-3-large tem maior precisão semântica

Métricas de Avaliação:
- MRR (Mean Reciprocal Rank): posição média do primeiro resultado relevante
- NDCG (Normalized Discounted Cumulative Gain): qualidade do ranking
- Precision@K: proporção de resultados relevantes nos top-K

Versão: 1.0.0
Data: Nov 2025
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from django.db import connection

logger = logging.getLogger(__name__)


@dataclass
class RerankingMetrics:
    """Métricas de performance do reranking."""
    
    candidates_count: int
    reranked_count: int
    large_embedding_time_ms: float
    similarity_calc_time_ms: float
    total_time_ms: float
    
    # Métricas de qualidade (opcionais)
    rank_changes: int = 0
    avg_rank_shift: float = 0.0
    top_k_preserved: float = 0.0  # % do top-k original mantido


@dataclass
class RerankingResult:
    """Resultado do reranking com métricas."""
    
    hits: list[dict[str, Any]]
    metrics: RerankingMetrics
    config: dict[str, Any] = field(default_factory=dict)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcula similaridade cosseno entre dois vetores.
    
    Fórmula: cos(θ) = (A·B) / (||A|| × ||B||)
    
    Args:
        vec1: Primeiro vetor
        vec2: Segundo vetor
    
    Returns:
        Similaridade entre -1 e 1 (1 = idênticos)
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def get_large_embeddings_batch(verse_ids: list[int]) -> dict[int, np.ndarray]:
    """
    Busca embeddings large para um batch de verse_ids.
    
    Otimização: busca em batch para reduzir round-trips ao banco.
    
    Args:
        verse_ids: Lista de IDs de versículos
    
    Returns:
        Dict mapeando verse_id → embedding (numpy array)
    """
    if not verse_ids:
        return {}
    
    # Query otimizada com IN clause
    placeholders = ",".join(["%s"] * len(verse_ids))
    sql = f"""
        SELECT verse_id, embedding_large
        FROM verse_embeddings
        WHERE verse_id IN ({placeholders})
        AND embedding_large IS NOT NULL
    """
    
    embeddings = {}
    with connection.cursor() as cur:
        cur.execute(sql, verse_ids)
        for row in cur.fetchall():
            verse_id = row[0]
            # pgvector retorna como string ou lista
            embedding_raw = row[1]
            if embedding_raw:
                try:
                    if isinstance(embedding_raw, str):
                        # Parse string format: "[0.1, 0.2, ...]" (tolerant to whitespace)
                        cleaned = embedding_raw.strip("[] ")
                        embedding = np.array([float(x.strip()) for x in cleaned.split(",") if x.strip()])
                    elif isinstance(embedding_raw, (list, tuple)):
                        embedding = np.array(embedding_raw, dtype=np.float64)
                    else:
                        embedding = np.array(embedding_raw)
                    embeddings[verse_id] = embedding
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse embedding for verse_id={verse_id}: {e}")
    
    return embeddings


def get_query_embedding_large(query: str) -> tuple[np.ndarray, float]:
    """
    Obtém embedding large para a query.
    
    Usa cache se disponível para reduzir chamadas à API.
    
    Args:
        query: Texto da query
    
    Returns:
        Tuple (embedding, latency_ms)
    """
    from .embedding_cache import embedding_cache
    
    t0 = time.time()
    embedding, latency = embedding_cache.get_embedding(
        query, 
        model="text-embedding-3-large"
    )
    total_ms = (time.time() - t0) * 1000
    
    return np.array(embedding), total_ms


def rerank_with_large_embeddings(
    hits: list[dict[str, Any]],
    query: str,
    *,
    top_k: int = 10,
    use_cached_query_embedding: np.ndarray | None = None,
) -> RerankingResult:
    """
    Reordena candidatos usando embedding large (3072 dim).
    
    Pipeline:
    1. Obtém embedding large da query
    2. Busca embeddings large dos candidatos (batch)
    3. Calcula similaridade cosseno
    4. Reordena por nova similaridade
    
    Args:
        hits: Lista de candidatos do primeiro estágio
        query: Query original
        top_k: Número de resultados finais
        use_cached_query_embedding: Embedding large da query (se já disponível)
    
    Returns:
        RerankingResult com hits reordenados e métricas
    """
    start_time = time.time()
    
    if not hits:
        return RerankingResult(
            hits=[],
            metrics=RerankingMetrics(
                candidates_count=0,
                reranked_count=0,
                large_embedding_time_ms=0,
                similarity_calc_time_ms=0,
                total_time_ms=0,
            ),
        )
    
    # 1. Obter embedding large da query
    if use_cached_query_embedding is not None:
        query_embedding = use_cached_query_embedding
        query_embedding_time = 0.0
    else:
        query_embedding, query_embedding_time = get_query_embedding_large(query)
    
    # 2. Buscar embeddings large dos candidatos
    t0 = time.time()
    verse_ids = [hit["verse_id"] for hit in hits]
    candidate_embeddings = get_large_embeddings_batch(verse_ids)
    batch_fetch_time = (time.time() - t0) * 1000
    
    # 3. Calcular novas similaridades
    t0 = time.time()
    scored_hits = []
    
    for hit in hits:
        verse_id = hit["verse_id"]
        
        if verse_id in candidate_embeddings:
            # Calcular similaridade com embedding large
            large_similarity = cosine_similarity(
                query_embedding, 
                candidate_embeddings[verse_id]
            )
            
            # Armazenar scores para análise
            hit_with_scores = hit.copy()
            hit_with_scores["large_similarity"] = large_similarity
            hit_with_scores["small_similarity"] = hit.get("similarity", 0)
            hit_with_scores["reranked"] = True
            
            scored_hits.append((large_similarity, hit_with_scores))
        else:
            # Manter score original se embedding large não disponível
            hit_copy = hit.copy()
            hit_copy["reranked"] = False
            scored_hits.append((hit.get("similarity", 0), hit_copy))
    
    similarity_calc_time = (time.time() - t0) * 1000
    
    # 4. Ordenar por nova similaridade (descendente)
    scored_hits.sort(key=lambda x: x[0], reverse=True)
    
    # 5. Calcular métricas de mudança de ranking
    original_order = {hit["verse_id"]: i for i, hit in enumerate(hits)}
    rank_changes = 0
    total_shift = 0
    
    reranked_hits = []
    for new_rank, (score, hit) in enumerate(scored_hits[:top_k]):
        original_rank = original_order.get(hit["verse_id"], new_rank)
        shift = abs(new_rank - original_rank)
        
        if shift > 0:
            rank_changes += 1
            total_shift += shift
        
        hit["similarity"] = score  # Atualizar score final
        hit["original_rank"] = original_rank
        hit["new_rank"] = new_rank
        hit["rank_shift"] = original_rank - new_rank  # Positivo = subiu
        
        reranked_hits.append(hit)
    
    # 6. Calcular preservação do top-k original
    original_top_k = set(hit["verse_id"] for hit in hits[:top_k])
    reranked_top_k = set(hit["verse_id"] for hit in reranked_hits)
    preserved = len(original_top_k & reranked_top_k) / len(original_top_k) if original_top_k else 0
    
    total_time = (time.time() - start_time) * 1000
    
    metrics = RerankingMetrics(
        candidates_count=len(hits),
        reranked_count=len(reranked_hits),
        large_embedding_time_ms=query_embedding_time + batch_fetch_time,
        similarity_calc_time_ms=similarity_calc_time,
        total_time_ms=total_time,
        rank_changes=rank_changes,
        avg_rank_shift=total_shift / len(reranked_hits) if reranked_hits else 0,
        top_k_preserved=preserved,
    )
    
    logger.info(
        f"Reranking: {len(hits)} → {len(reranked_hits)} hits, "
        f"{rank_changes} rank changes, "
        f"{metrics.avg_rank_shift:.1f} avg shift, "
        f"{preserved*100:.0f}% preserved, "
        f"{total_time:.1f}ms"
    )
    
    return RerankingResult(
        hits=reranked_hits,
        metrics=metrics,
        config={
            "model": "text-embedding-3-large",
            "dimension": 3072,
            "top_k": top_k,
            "candidates": len(hits),
        },
    )


def compare_rankings(
    original_hits: list[dict],
    reranked_hits: list[dict],
) -> dict[str, Any]:
    """
    Compara rankings original e rerankeado para análise.
    
    Útil para validação e debugging do reranking.
    
    Args:
        original_hits: Hits do primeiro estágio
        reranked_hits: Hits após reranking
    
    Returns:
        Dict com métricas de comparação
    """
    original_ids = [h["verse_id"] for h in original_hits]
    reranked_ids = [h["verse_id"] for h in reranked_hits]
    
    # Kendall Tau - correlação de rankings
    # +1 = idênticos, -1 = completamente invertidos
    concordant = 0
    discordant = 0
    
    for i in range(len(reranked_ids)):
        for j in range(i + 1, len(reranked_ids)):
            if reranked_ids[i] in original_ids and reranked_ids[j] in original_ids:
                orig_i = original_ids.index(reranked_ids[i])
                orig_j = original_ids.index(reranked_ids[j])
                
                if (orig_i < orig_j and i < j) or (orig_i > orig_j and i > j):
                    concordant += 1
                else:
                    discordant += 1
    
    n = len(reranked_ids)
    total_pairs = n * (n - 1) / 2 if n > 1 else 1
    kendall_tau = (concordant - discordant) / total_pairs if total_pairs > 0 else 0
    
    # Overlap@K
    overlap = len(set(original_ids) & set(reranked_ids)) / len(reranked_ids) if reranked_ids else 0
    
    # Análise de movimentos
    movements = {
        "promoted": [],  # Subiram de posição
        "demoted": [],   # Desceram de posição
        "unchanged": [], # Mantiveram posição
        "new": [],       # Entraram no top-k
        "removed": [],   # Saíram do top-k
    }
    
    original_set = set(original_ids[:len(reranked_ids)])
    reranked_set = set(reranked_ids)
    
    movements["new"] = list(reranked_set - original_set)
    movements["removed"] = list(original_set - reranked_set)
    
    for hit in reranked_hits:
        if "rank_shift" in hit:
            shift = hit["rank_shift"]
            vid = hit["verse_id"]
            if shift > 0:
                movements["promoted"].append({"verse_id": vid, "shift": shift})
            elif shift < 0:
                movements["demoted"].append({"verse_id": vid, "shift": shift})
            else:
                movements["unchanged"].append(vid)
    
    return {
        "kendall_tau": round(kendall_tau, 3),
        "overlap_at_k": round(overlap, 3),
        "movements": movements,
        "analysis": {
            "promoted_count": len(movements["promoted"]),
            "demoted_count": len(movements["demoted"]),
            "unchanged_count": len(movements["unchanged"]),
            "new_entries": len(movements["new"]),
            "removed_entries": len(movements["removed"]),
        },
    }
