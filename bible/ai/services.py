"""
RAG Services - Camada de serviço para busca semântica

Este módulo fornece uma interface limpa para o sistema RAG,
enriquecendo os resultados com dados do banco e formatando
a resposta de acordo com os padrões da API.

Versão: 2.1.0 - Adicionado suporte a Hybrid Search (BM25 + Vetorial)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from django.core.cache import cache

from bible.models import Book, Version

from . import retrieval as rag_core
from .embedding_cache import embedding_cache

logger = logging.getLogger(__name__)

# Configuração via env
HYBRID_ENABLED = os.getenv("RAG_HYBRID", "0") == "1"
HYBRID_ALPHA = float(os.getenv("RAG_HYBRID_ALPHA", "0.7"))

# Cache TTL para dados de livros (1 hora)
BOOK_CACHE_TTL = 3600


@dataclass
class RagSearchResult:
    """Resultado estruturado de busca RAG."""

    hits: list[dict[str, Any]]
    total: int
    timing: dict[str, float]
    query: str
    top_k: int
    query_expansion: dict[str, Any] | None = None
    reranking: dict[str, Any] | None = None
    mmr_diversification: dict[str, Any] | None = None


def _get_book_data_cached() -> dict[int, dict[str, str]]:
    """
    Retorna um dicionário com dados dos livros, usando cache.
    
    Returns:
        Dict mapeando book_id para {osis_code, name}
    """
    cache_key = "rag_book_data"
    book_data = cache.get(cache_key)
    
    if book_data is None:
        book_data = {}
        for book in Book.objects.select_related("testament").prefetch_related("names__language").all():
            # Pegar o nome em português (ou primeiro disponível)
            name = book.osis_code  # fallback
            for book_name in book.names.all():
                lang_code = book_name.language.code if book_name.language else ""
                if lang_code in ("pt", "pt-BR"):
                    name = book_name.name
                    break
                elif not name or name == book.osis_code:
                    name = book_name.name
            
            book_data[book.id] = {
                "osis_code": book.osis_code,
                "name": name,
            }
        
        cache.set(cache_key, book_data, BOOK_CACHE_TTL)
    
    return book_data


def _get_version_data_cached() -> dict[str, dict[str, str]]:
    """
    Retorna um dicionário com dados das versões, usando cache.
    
    Returns:
        Dict mapeando version_code para {code, name, abbreviation}
    """
    cache_key = "rag_version_data"
    version_data = cache.get(cache_key)
    
    if version_data is None:
        version_data = {}
        for version in Version.objects.all():
            version_data[version.code] = {
                "code": version.code,
                "name": version.name,
                "abbreviation": version.abbreviation or version.code,
            }
        
        cache.set(cache_key, version_data, BOOK_CACHE_TTL)
    
    return version_data


def _format_reference(book_name: str, chapter: int, verse: int) -> str:
    """Formata uma referência bíblica legível."""
    return f"{book_name} {chapter}:{verse}"


def _enrich_hit(hit: dict[str, Any], book_data: dict, version_data: dict) -> dict[str, Any]:
    """
    Enriquece um hit RAG com dados adicionais do banco.
    
    O formato de saída é compatível com o frontend (RagSearchHit).
    """
    book_id = hit.get("book_id")
    book_info = book_data.get(book_id, {})
    version_code = hit.get("version", "")
    version_info = version_data.get(version_code, {})
    
    book_osis = hit.get("book_osis") or book_info.get("osis_code", "")
    book_name = book_info.get("name", book_osis)
    chapter = hit.get("chapter", 0)
    verse = hit.get("verse", 0)
    
    return {
        "id": hit.get("verse_id"),
        "verse_id": hit.get("verse_id"),  # Para compatibilidade
        "reference": _format_reference(book_name, chapter, verse),
        "text": hit.get("text", ""),
        "book_osis": book_osis,
        "book_name": book_name,
        "book_id": book_id,
        "chapter": chapter,
        "verse": verse,
        "version_code": version_code,
        "version_name": version_info.get("name", version_code),
        "score": round(hit.get("similarity", 0.0), 4),
        "distance": round(hit.get("distance", 0.0), 4),
    }


def search(
    query: str,
    *,
    top_k: int = 10,
    versions: list[str] | None = None,
    book_id: int | None = None,
    testament: str | None = None,
    min_score: float | None = None,
) -> RagSearchResult:
    """
    Executa busca semântica (RAG) e retorna resultados enriquecidos.
    
    Args:
        query: Texto da consulta
        top_k: Número máximo de resultados (default: 10, max: 50)
        versions: Lista de códigos de versão para filtrar
        book_id: ID do livro para filtrar
        testament: 'old' ou 'new' para filtrar por testamento
        min_score: Score mínimo de similaridade (0-1)
    
    Returns:
        RagSearchResult com hits enriquecidos
    
    Raises:
        ValueError: Se query estiver vazia ou top_k inválido
    """
    # Validação
    if not query or not query.strip():
        raise ValueError("Query não pode estar vazia")
    
    query = query.strip()
    top_k = max(1, min(top_k, 50))  # Limitar entre 1 e 50
    
    # Buscar dados auxiliares (cache)
    book_data = _get_book_data_cached()
    version_data = _get_version_data_cached()
    
    # Converter filtro de testamento para book_ids
    filtered_book_id = book_id
    if testament and not book_id:
        # Filtrar livros pelo testamento
        testament_books = [
            bid for bid, binfo in book_data.items()
            # Aqui precisaríamos ter o testament no cache
            # Por ora, deixar sem esse filtro no RAG
        ]
    
    # Executar busca RAG core
    try:
        result = rag_core.retrieve(
            query=query,
            vector=None,
            top_k=top_k * 2 if min_score else top_k,  # Buscar mais se vamos filtrar
            versions=versions,
            book_id=filtered_book_id,
        )
    except Exception as e:
        logger.error(f"Erro na busca RAG: {e}")
        raise
    
    # Enriquecer hits
    raw_hits = result.get("hits", [])
    enriched_hits = []
    
    for hit in raw_hits:
        enriched = _enrich_hit(hit, book_data, version_data)
        
        # Aplicar filtro de score mínimo
        if min_score is not None and enriched["score"] < min_score:
            continue
        
        enriched_hits.append(enriched)
        
        if len(enriched_hits) >= top_k:
            break
    
    return RagSearchResult(
        hits=enriched_hits,
        total=len(enriched_hits),
        timing=result.get("timing", {}),
        query=query,
        top_k=top_k,
    )


def search_hybrid(
    query: str,
    *,
    top_k: int = 10,
    versions: list[str] | None = None,
    book_id: int | None = None,
    alpha: float | None = None,
    min_score: float | None = None,
    expand_query: bool = False,
    expand_mode: str = "auto",
    max_synonyms: int = 3,
    rerank: bool = False,
    mmr_lambda: float | None = None,
    deduplicate_versions: bool = False,
    embedding_source: str = "verse",
    embedding_model: str = "large",
    reembed_after_expansion: bool = False,
) -> RagSearchResult:
    """
    Executa busca híbrida: BM25 (lexical) + Vetorial (semântica) com RRF fusion.
    
    A busca híbrida combina o melhor de dois mundos:
    - BM25: Excelente para termos exatos e palavras específicas
    - Vetorial: Excelente para conceitos e significado semântico
    
    Pipeline completo:
    1. Query Expansion (opcional) - Sinônimos teológicos
       - static: dicionário estático (offline, rápido)
       - dynamic: LLM GPT-4o com cache (mais preciso)
       - auto: tenta dynamic primeiro, fallback para static
    2. BM25 Search - Matches lexicais
    3. Vector Search - Similaridade semântica
    4. RRF Fusion - Combina rankings
    5. Two-Stage Reranking (opcional) - embedding-large (3072 dim)
    6. MMR Diversification (opcional) - Maximiza diversidade
    
    Args:
        query: Texto da consulta
        top_k: Número máximo de resultados (default: 10, max: 50)
        versions: Lista de códigos de versão para filtrar
        book_id: ID do livro para filtrar
        alpha: Peso do BM25 (0=só vetorial, 1=só BM25, 0.5=balanceado)
        min_score: Score mínimo de similaridade (0-1)
        expand_query: Se True, expande query com sinônimos teológicos
        expand_mode: Modo de expansão ('static', 'dynamic', 'auto')
        rerank: Se True, reordena com embedding large (3072 dim)
        mmr_lambda: Se fornecido (0-1), aplica MMR diversification
                   0=máxima diversidade, 1=máxima relevância
        deduplicate_versions: Se True, remove versículos duplicados de diferentes versões
        embedding_source: Fonte dos embeddings vetoriais:
            - 'verse': verse_embeddings (529K, por versão, PT+EN)
            - 'unified': unified_verse_embeddings (31K, canônico, só PT)
    
    Returns:
        RagSearchResult com hits enriquecidos
    """
    from .hybrid import hybrid_search
    
    if not query or not query.strip():
        raise ValueError("Query não pode estar vazia")
    
    query = query.strip()
    top_k = max(1, min(top_k, 50))
    alpha_user_provided = alpha is not None
    alpha = alpha if alpha is not None else HYBRID_ALPHA
    
    # Obter embedding da query (model depends on embedding_model param)
    embed_model_name = "text-embedding-3-large" if embedding_model == "large" else "text-embedding-3-small"
    query_embedding, _ = embedding_cache.get_embedding(query, model=embed_model_name)

    # Buscar dados auxiliares
    book_data = _get_book_data_cached()
    version_data = _get_version_data_cached()
    
    # Executar busca híbrida
    try:
        result = hybrid_search(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k * 2 if min_score else top_k,
            pool_size=300,
            versions=versions,
            book_id=book_id,
            alpha=alpha,
            alpha_user_provided=alpha_user_provided,
            expand_query_flag=expand_query,
            expand_mode=expand_mode,
            max_synonyms=max_synonyms,
            rerank_with_large=rerank,
            mmr_lambda=mmr_lambda,
            deduplicate_versions=deduplicate_versions,
            embedding_source=embedding_source,
            embedding_model=embedding_model,
            reembed_after_expansion=reembed_after_expansion,
            embed_model_name=embed_model_name,
        )
    except (ConnectionError, TimeoutError, OSError) as e:
        logger.warning(f"Busca híbrida falhou por conexão/timeout, fallback para vetorial: {e}")
        fallback_result = search(query, top_k=top_k, versions=versions, book_id=book_id, min_score=min_score)
        if isinstance(fallback_result, dict):
            fallback_result["fallback"] = True
            fallback_result["fallback_reason"] = str(e)
        return fallback_result
    except Exception as e:
        logger.exception(f"Erro inesperado na busca híbrida: {e}")
        raise
    
    # Enriquecer hits
    raw_hits = result.get("hits", [])
    enriched_hits = []
    
    for hit in raw_hits:
        enriched = _enrich_hit(hit, book_data, version_data)
        
        # Adicionar métricas extras do hybrid
        enriched["bm25_score"] = hit.get("bm25_score")
        enriched["vector_score"] = hit.get("vector_score")
        enriched["rrf_score"] = hit.get("rrf_score")
        
        # Flags de origem do match
        enriched["match_source"] = hit.get("match_source")
        enriched["contains_query"] = hit.get("contains_query")
        
        # Métricas de reranking (se disponíveis)
        if rerank:
            enriched["large_similarity"] = hit.get("large_similarity")
            enriched["original_rank"] = hit.get("original_rank")
            enriched["rank_shift"] = hit.get("rank_shift")
        
        if min_score is not None and enriched["score"] < min_score:
            continue
        
        enriched_hits.append(enriched)
        
        if len(enriched_hits) >= top_k:
            break
    
    timing = result.get("timing", {})
    timing["hybrid"] = True
    timing["alpha"] = alpha
    
    rag_result = RagSearchResult(
        hits=enriched_hits,
        total=len(enriched_hits),
        timing=timing,
        query=query,
        top_k=top_k,
    )
    
    # Adicionar info de query expansion se disponível
    if "query_expansion" in result:
        rag_result.query_expansion = result["query_expansion"]
    
    # Adicionar info de reranking se disponível
    if "reranking" in result:
        rag_result.reranking = result["reranking"]
    
    # Adicionar info de MMR se disponível
    if "mmr_diversification" in result:
        rag_result.mmr_diversification = result["mmr_diversification"]
    
    return rag_result


def get_similar_verses(
    verse_id: int,
    *,
    top_k: int = 5,
    exclude_same_chapter: bool = True,
) -> RagSearchResult:
    """
    Encontra versículos similares a um versículo específico.
    
    Útil para sugestões de referências cruzadas baseadas em semântica.
    
    Args:
        verse_id: ID do versículo de referência
        top_k: Número de resultados
        exclude_same_chapter: Se True, exclui versículos do mesmo capítulo
    
    Returns:
        RagSearchResult com versículos similares
    """
    from bible.models import Verse
    
    try:
        verse = Verse.objects.select_related("book").get(id=verse_id)
    except Verse.DoesNotExist:
        raise ValueError(f"Versículo {verse_id} não encontrado")
    
    # Usar o texto do versículo como query
    result = search(
        query=verse.text,
        top_k=top_k + 10,  # Buscar mais para compensar filtros
    )
    
    # Filtrar resultados
    filtered_hits = []
    for hit in result.hits:
        # Excluir o próprio versículo
        if hit["verse_id"] == verse_id:
            continue
        
        # Excluir mesmo capítulo se configurado
        if exclude_same_chapter:
            if hit["book_id"] == verse.book_id and hit["chapter"] == verse.chapter:
                continue
        
        filtered_hits.append(hit)
        
        if len(filtered_hits) >= top_k:
            break
    
    return RagSearchResult(
        hits=filtered_hits,
        total=len(filtered_hits),
        timing=result.timing,
        query=verse.text[:100],  # Truncar para log
        top_k=top_k,
    )


def get_cache_stats() -> dict[str, Any]:
    """Retorna estatísticas do cache de embeddings."""
    from .embedding_cache import embedding_cache
    
    return embedding_cache.get_cache_stats()


def health_check() -> dict[str, Any]:
    """
    Verifica a saúde do sistema RAG.
    
    Returns:
        Dict com status de cada componente
    """
    status = {
        "status": "healthy",
        "components": {},
    }
    
    # Verificar cache de embeddings
    try:
        cache_stats = get_cache_stats()
        status["components"]["embedding_cache"] = {
            "status": "healthy",
            "stats": cache_stats,
        }
    except Exception as e:
        status["components"]["embedding_cache"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        status["status"] = "degraded"
    
    # Verificar conexão com banco vetorial
    try:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT 1 FROM bible_verseembedding LIMIT 1")
            cur.fetchone()
        status["components"]["vector_db"] = {"status": "healthy"}
    except Exception as e:
        status["components"]["vector_db"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        status["status"] = "unhealthy"
    
    # Verificar dados de livros
    try:
        book_data = _get_book_data_cached()
        status["components"]["book_data"] = {
            "status": "healthy",
            "book_count": len(book_data),
        }
    except Exception as e:
        status["components"]["book_data"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        status["status"] = "degraded"
    
    return status
