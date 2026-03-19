"""
Hybrid Search Module - Combinação de BM25 (lexical) + Vetorial (semântica)

Este módulo implementa busca híbrida usando:
- BM25 via PostgreSQL full-text search (tsvector/tsquery)
- Busca vetorial via pgvector (HNSW index)
- Fusão via Reciprocal Rank Fusion (RRF)
- Query Expansion via sinônimos teológicos (estático ou LLM dinâmico)

Referências:
- https://arxiv.org/abs/2210.11934 (Hybrid Search for Dense Retrieval)
- https://www.elastic.co/blog/improving-information-retrieval-elastic-stack-hybrid

Versão: 1.2.0
Data: Nov 2025
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

from django.db import connection

from .query_expansion import expand_query, expand_query_for_bm25, ExpandedQuery

if TYPE_CHECKING:
    from .agents.tools.nlp_query_tool import NLPQueryTool, NLPAnalysis

logger = logging.getLogger(__name__)

# === NLP Query Tool Integration ===
_nlp_tool: "NLPQueryTool | None" = None


def get_nlp_tool() -> "NLPQueryTool":
    """Get singleton NLP Query Tool instance (lazy loaded)."""
    global _nlp_tool
    if _nlp_tool is None:
        from .agents.tools.nlp_query_tool import NLPQueryTool
        _nlp_tool = NLPQueryTool(use_spacy=False, use_gazetteer=True)
        # Force gazetteer loading and count entities correctly
        gazetteer = _nlp_tool.gazetteer
        entity_count = 0
        namespace_count = 0
        if gazetteer:
            for namespace, items in gazetteer.items():
                # Skip metadata keys
                if namespace.startswith("_") or not isinstance(items, dict):
                    continue
                namespace_count += 1
                entity_count += len(items)
        logger.info(f"NLP Query Tool initialized: {entity_count} entities in {namespace_count} namespaces")
    return _nlp_tool


def analyze_query_nlp(query: str) -> "NLPAnalysis | None":
    """
    Analyze query using NLP Tool to get dynamic boost strategy.
    
    Returns:
        NLPAnalysis with semantic_type, entities, boost_strategy, and optimized tsquery
    """
    try:
        nlp_tool = get_nlp_tool()
        return nlp_tool.analyze(query)
    except Exception as e:
        logger.warning(f"NLP analysis failed for query '{query}': {e}")
        return None


@dataclass
class HybridResult:
    """Resultado de busca híbrida com scores de ambas as fontes."""
    
    verse_id: int
    book_id: int
    book_osis: str
    chapter: int
    verse: int
    text: str
    version_code: str
    
    # Scores
    bm25_rank: int | None = None
    bm25_score: float | None = None
    vector_rank: int | None = None
    vector_score: float | None = None
    rrf_score: float = 0.0
    final_score: float = 0.0


def normalize_query_for_tsquery(query: str, lang: str = "portuguese") -> str:
    """
    Normaliza query para formato tsquery do PostgreSQL.
    
    Exemplos:
        "amor de Deus" → "amor & deus"
        "perdão dos pecados" → "perdao & pecados"
    """
    # Remover caracteres especiais exceto letras e espaços
    clean = re.sub(r"[^\w\s]", " ", query.lower())
    
    # Remover stopwords comuns em português
    stopwords = {"de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "ou", 
                 "um", "uma", "uns", "umas", "em", "no", "na", "nos", "nas",
                 "por", "para", "com", "sem", "sob", "sobre", "entre", "que"}
    
    words = [w.strip() for w in clean.split() if w.strip() and w not in stopwords]
    
    if not words:
        return query.lower()
    
    # Juntar com & (AND) para busca mais precisa
    return " & ".join(words)


def bm25_search(
    query: str,
    *,
    top_k: int = 100,
    versions: list[str] | None = None,
    book_id: int | None = None,
    lang: str = "portuguese",
    use_raw_tsquery: bool = False,
    original_query: str | None = None,
    original_boost: float = 1.5,
) -> list[dict[str, Any]]:
    """
    Busca lexical usando PostgreSQL full-text search (BM25-like).
    
    O PostgreSQL usa ts_rank que é similar ao BM25 em comportamento.
    
    Args:
        query: Texto da busca (ou tsquery formatada se use_raw_tsquery=True)
        top_k: Número máximo de resultados
        versions: Lista de versões para filtrar
        book_id: Filtrar por livro específico
        lang: Idioma para stemming ('portuguese' ou 'english')
        use_raw_tsquery: Se True, usa query diretamente como tsquery (já formatada)
        original_query: Query original (antes da expansão) para dar boost
        original_boost: Multiplicador de score para textos que contêm a query original (default: 1.5)
    
    Returns:
        Lista de resultados com verse_id, score e metadados
    """
    start_time = time.time()
    
    # Determinar configuração de idioma
    config = "portuguese" if lang in ("pt", "pt-BR", "portuguese") else "english"
    
    # Usar tsquery raw ou plainto_tsquery
    if use_raw_tsquery:
        # Query já está formatada como tsquery (ex: "odio | ira | raiva")
        tsquery_func = f"to_tsquery('{config}', %s)"
        tsquery_param = query
    else:
        # Converter query normal para tsquery
        tsquery = normalize_query_for_tsquery(query, lang)
        tsquery_func = f"plainto_tsquery('{config}', %s)"
        tsquery_param = query
    
    # Boost para query original (se fornecida e diferente da query expandida)
    # Isso garante que textos com a frase exata tenham prioridade
    if original_query and original_query.lower() != query.lower():
        # Normalizar para busca case-insensitive
        boost_clause = f"CASE WHEN LOWER(v.text) LIKE LOWER(%s) THEN {original_boost} ELSE 1.0 END"
        score_expression = f"ts_rank_cd(to_tsvector('{config}', v.text), {tsquery_func}) * {boost_clause}"
    else:
        score_expression = f"ts_rank_cd(to_tsvector('{config}', v.text), {tsquery_func})"
        boost_clause = None
    
    sql_parts = [
        "SELECT",
        "  v.id as verse_id,",
        "  v.book_id,",
        "  cb.osis_code as book_osis,",
        "  v.chapter,",
        "  v.number as verse,",
        "  v.text,",
        "  ver.code as version_code,",
        f"  {score_expression} as bm25_score",
        "FROM verses v",
        "JOIN canonical_books cb ON cb.id = v.book_id",
        "JOIN versions ver ON ver.id = v.version_id",
        f"WHERE to_tsvector('{config}', v.text) @@ {tsquery_func}",
    ]
    
    # Parâmetros: tsquery (2x) + boost pattern (se houver)
    if boost_clause:
        params: list[Any] = [tsquery_param, f"%{original_query}%", tsquery_param]
    else:
        params: list[Any] = [tsquery_param, tsquery_param]
    
    if versions:
        sql_parts.append("AND ver.code = ANY(%s)")
        params.append(versions)
    
    if book_id is not None:
        sql_parts.append("AND v.book_id = %s")
        params.append(book_id)
    
    sql_parts.extend([
        "ORDER BY bm25_score DESC",
        "LIMIT %s",
    ])
    params.append(top_k)
    
    sql = "\n".join(sql_parts)
    
    results = []
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            for i, row in enumerate(rows):
                results.append({
                    "verse_id": row[0],
                    "book_id": row[1],
                    "book_osis": row[2],
                    "chapter": row[3],
                    "verse": row[4],
                    "text": row[5],
                    "version_code": row[6],
                    "bm25_score": float(row[7]) if row[7] else 0.0,
                    "bm25_rank": i + 1,
                })
    except Exception as e:
        logger.error(f"Erro na busca BM25: {e}")
        # Fallback para busca LIKE simples
        results = _fallback_like_search(query, top_k, versions, book_id)
    
    elapsed = (time.time() - start_time) * 1000
    logger.info(f"BM25 search: {len(results)} results in {elapsed:.1f}ms")
    
    return results


def _fallback_like_search(
    query: str,
    top_k: int,
    versions: list[str] | None,
    book_id: int | None,
) -> list[dict[str, Any]]:
    """Fallback para busca ILIKE quando full-text falha."""
    sql_parts = [
        "SELECT",
        "  v.id as verse_id,",
        "  v.book_id,",
        "  cb.osis_code as book_osis,",
        "  v.chapter,",
        "  v.number as verse,",
        "  v.text,",
        "  ver.code as version_code",
        "FROM verses v",
        "JOIN canonical_books cb ON cb.id = v.book_id",
        "JOIN versions ver ON ver.id = v.version_id",
        "WHERE v.text ILIKE %s",
    ]
    
    params: list[Any] = [f"%{query}%"]
    
    if versions:
        sql_parts.append("AND ver.code = ANY(%s)")
        params.append(versions)
    
    if book_id is not None:
        sql_parts.append("AND v.book_id = %s")
        params.append(book_id)
    
    sql_parts.append("LIMIT %s")
    params.append(top_k)
    
    sql = "\n".join(sql_parts)
    
    results = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        for i, row in enumerate(rows):
            results.append({
                "verse_id": row[0],
                "book_id": row[1],
                "book_osis": row[2],
                "chapter": row[3],
                "verse": row[4],
                "text": row[5],
                "version_code": row[6],
                "bm25_score": 1.0 / (i + 1),  # Score aproximado
                "bm25_rank": i + 1,
            })
    
    return results


def reciprocal_rank_fusion(
    bm25_results: list[dict[str, Any]],
    vector_results: list[dict[str, Any]],
    *,
    k: int = 60,
    alpha: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Combina resultados de BM25 e vetorial usando Reciprocal Rank Fusion.
    
    RRF Score = α * (1/(k + rank_bm25)) + (1-α) * (1/(k + rank_vector))
    
    Args:
        bm25_results: Resultados da busca BM25
        vector_results: Resultados da busca vetorial
        k: Constante de suavização (padrão 60, comum em IR)
        alpha: Peso do BM25 (0=só vetorial, 1=só BM25, 0.5=balanceado)
    
    Returns:
        Lista fusionada ordenada por RRF score
    """
    # Criar mapa de verse_id → resultado
    combined: dict[int, dict[str, Any]] = {}
    
    # Adicionar resultados BM25
    for result in bm25_results:
        vid = result["verse_id"]
        combined[vid] = {
            **result,
            "bm25_rank": result.get("bm25_rank"),
            "bm25_score": result.get("bm25_score"),
            "vector_rank": None,
            "vector_score": None,
        }
    
    # Adicionar/mesclar resultados vetoriais
    for result in vector_results:
        vid = result["verse_id"]
        if vid in combined:
            # Mesclar com existente
            combined[vid]["vector_rank"] = result.get("vector_rank")
            combined[vid]["vector_score"] = result.get("similarity", result.get("vector_score"))
        else:
            # Novo resultado
            combined[vid] = {
                **result,
                "bm25_rank": None,
                "bm25_score": None,
                "vector_rank": result.get("vector_rank"),
                "vector_score": result.get("similarity", result.get("vector_score")),
            }
    
    # Calcular RRF score
    for vid, result in combined.items():
        bm25_contrib = 0.0
        vector_contrib = 0.0
        
        if result["bm25_rank"] is not None:
            bm25_contrib = 1.0 / (k + result["bm25_rank"])
        
        if result["vector_rank"] is not None:
            vector_contrib = 1.0 / (k + result["vector_rank"])
        
        result["rrf_score"] = alpha * bm25_contrib + (1 - alpha) * vector_contrib

        # Score final: normalizado pelo máximo teórico (item rank=1 em ambos os sinais).
        # O máximo RRF ocorre quando bm25_rank=1 E vector_rank=1:
        #   max = alpha * 1/(k+1) + (1-alpha) * 1/(k+1) = 1/(k+1)
        # Nota: este valor é constante independente do alpha, pois rank=1 em ambos
        # dá a mesma contribuição ponderada. O alpha afeta items que NÃO são rank=1
        # em ambos os sinais, onde a contribuição relativa muda.
        max_possible = 1.0 / (k + 1)
        result["final_score"] = result["rrf_score"] / max_possible if max_possible > 0 else 0
        
        # Determinar origem do match
        has_bm25 = result["bm25_rank"] is not None
        has_vector = result["vector_rank"] is not None
        if has_bm25 and has_vector:
            result["match_source"] = "both"
        elif has_bm25:
            result["match_source"] = "bm25_only"
        else:
            result["match_source"] = "vector_only"
    
    # Ordenar por RRF score descendente
    sorted_results = sorted(combined.values(), key=lambda x: x["rrf_score"], reverse=True)
    
    return sorted_results


def _expand_query_with_mode(
    query: str,
    mode: Literal["static", "dynamic", "auto"],
    max_synonyms: int = 3,
) -> dict[str, Any]:
    """
    Expande query usando o modo especificado.
    
    Args:
        query: Query para expandir
        mode: 'static' (dicionário), 'dynamic' (LLM), 'auto' (tenta dynamic, fallback static)
        max_synonyms: Máximo de sinônimos por categoria
    
    Returns:
        Dict com expansões e metadados
    """
    result: dict[str, Any] = {
        "mode": mode,
        "from_cache": False,
        "model_used": None,
        "expanded_terms": [],
        "theological_synonyms": [],
        "morphological_variants": [],
        "related_concepts": [],
        "expansion_type": "none",
        "tsquery": query,
    }
    
    # Tenta expansão dinâmica (LLM + cache)
    if mode in ("dynamic", "auto"):
        try:
            from .expansion_services.query_expansion_service import expand_query_dynamic
            
            dynamic_result = expand_query_dynamic(
                query,
                use_cache=True,
                use_llm=True,  # Em 'auto' e 'dynamic', usa LLM (cache é verificado primeiro)
                use_static_fallback=False,  # Tratamos static separadamente
            )
            
            if dynamic_result.get_all_terms():
                result["mode"] = "dynamic" if not dynamic_result.from_cache else "cached"
                result["from_cache"] = dynamic_result.from_cache
                result["model_used"] = dynamic_result.model_used
                result["theological_synonyms"] = dynamic_result.theological_synonyms[:max_synonyms]
                result["morphological_variants"] = dynamic_result.morphological_variants[:max_synonyms]
                result["related_concepts"] = dynamic_result.related_concepts[:max_synonyms]
                result["expanded_terms"] = dynamic_result.get_all_terms()[:max_synonyms * 3]
                result["expansion_type"] = dynamic_result.expansion_type
                result["tsquery"] = dynamic_result.to_tsquery()
                
                return result
                
        except Exception as e:
            logger.warning(f"Dynamic expansion failed, falling back to static: {e}")
    
    # Fallback para expansão estática (dicionário)
    if mode in ("static", "auto"):
        try:
            expanded = expand_query(query, max_synonyms_per_term=max_synonyms)
            
            if expanded.synonyms_used:
                all_synonyms = []
                for syns in expanded.synonyms_used.values():
                    all_synonyms.extend(syns)
                
                result["mode"] = "static"
                result["from_cache"] = False
                result["theological_synonyms"] = all_synonyms[:max_synonyms]
                result["expanded_terms"] = expanded.expanded_terms[:max_synonyms * 3]
                result["expansion_type"] = expanded.expansion_type
                result["tsquery"] = expanded.to_tsquery()
                
                return result
                
        except Exception as e:
            logger.warning(f"Static expansion failed: {e}")
    
    return result


def hybrid_search(
    query: str,
    query_embedding: list[float],
    *,
    top_k: int = 20,
    pool_size: int = 100,
    versions: list[str] | None = None,
    book_id: int | None = None,
    alpha: float = 0.5,
    rrf_k: int = 60,
    expand_query_flag: bool = False,
    expand_mode: Literal["static", "dynamic", "auto"] = "auto",
    max_synonyms: int = 3,
    rerank_with_large: bool = False,
    mmr_lambda: float | None = None,
    deduplicate_versions: bool = False,
    embedding_source: Literal["verse", "unified"] = "verse",
    use_nlp_analysis: bool = True,
    bm25_original_boost: float = 1.5,
) -> dict[str, Any]:
    """
    Executa busca híbrida completa: BM25 + Vetorial + RRF Fusion.
    
    Pipeline completo:
    0. NLP Analysis (novo) - Analisa query para determinar boost strategy
       - Detecta entidades (Gazetteer), classifica tipo semântico
       - Calcula alpha dinâmico, boost de entidade, distância de palavras
    1. Query Expansion (opcional) - Expande com sinônimos teológicos
       - static: usa dicionário estático (rápido, offline)
       - dynamic: usa LLM GPT-4o com cache (mais preciso, primeira vez lento)
       - auto: tenta dynamic primeiro, fallback para static
    2. BM25 Search - Busca léxica com full-text search
    3. Vector Search - Busca semântica com embeddings
    4. RRF Fusion - Combina rankings com Reciprocal Rank Fusion
    5. Two-Stage Reranking (opcional) - Reordena com embedding large
    6. MMR Diversification (opcional) - Diversifica resultados com MMR
    
    Args:
        query: Texto da consulta
        query_embedding: Vetor embedding da query (small, dim=1536)
        top_k: Número final de resultados
        pool_size: Candidatos a buscar de cada fonte
        versions: Filtro de versões (ignorado se embedding_source='unified')
        book_id: Filtro de livro
        alpha: Peso BM25 vs Vetorial (0.5 = balanceado)
        rrf_k: Constante k do RRF
        expand_query_flag: Se True, expande query com sinônimos teológicos
        expand_mode: Modo de expansão ('static', 'dynamic', 'auto')
        max_synonyms: Máximo de sinônimos por termo na expansão
        rerank_with_large: Se True, reordena usando embedding large (3072 dim)
        mmr_lambda: Se fornecido (0.0-1.0), aplica MMR diversification
                   0.0 = máxima diversidade, 1.0 = máxima relevância
                   Recomendado: 0.5-0.7 para balanço
        deduplicate_versions: Se True, remove versículos duplicados de diferentes versões
        embedding_source: Fonte dos embeddings para busca vetorial:
            - 'verse': usa verse_embeddings (528K, por versão, PT+EN)
            - 'unified': usa unified_verse_embeddings (31K, canônico, só PT)
        use_nlp_analysis: Se True, usa NLP Tool para boost dinâmico (default: True)
    
    Returns:
        Dict com hits, timing e métricas
    """
    start_time = time.time()
    timings = {}
    expansion_info: dict[str, Any] = {}
    reranking_info: dict[str, Any] = {}
    mmr_info: dict[str, Any] = {}
    nlp_info: dict[str, Any] = {}
    
    # 0. NLP Analysis (novo) - Analisa query para estratégia de boost
    nlp_analysis = None
    entity_boost = 1.0
    optimized_tsquery = None
    
    if use_nlp_analysis:
        t0 = time.time()
        nlp_analysis = analyze_query_nlp(query)
        
        if nlp_analysis:
            boost_strategy = nlp_analysis.boost_strategy
            
            # Alpha dinâmico baseado no tipo semântico
            if "alpha" in boost_strategy:
                alpha = boost_strategy["alpha"]
            
            # Expansão desabilitada para entidades/frases
            if not boost_strategy.get("expand", True):
                expand_query_flag = False
            
            # Boost de entidade para BM25
            entity_boost = boost_strategy.get("entity_boost", 1.0)
            
            # TSQuery otimizado com distância dinâmica
            optimized_tsquery = nlp_analysis.to_tsquery()
            
            nlp_info = {
                "enabled": True,
                "semantic_type": nlp_analysis.semantic_type.value,
                "tokens": nlp_analysis.tokens_clean,
                "stopwords_removed": nlp_analysis.stopwords_removed,
                "entities": [
                    {"name": e.get("text", e.get("canonical_id", "?")), 
                     "type": e.get("type", "?"), 
                     "boost": e.get("boost", 1.0)}
                    for e in nlp_analysis.entities
                ],
                "boost_strategy": {
                    "method": boost_strategy.get("method"),
                    "alpha": alpha,
                    "entity_boost": entity_boost,
                    "expand": expand_query_flag,
                    "phrase_boost": boost_strategy.get("phrase_boost", 1.0),
                },
                "tsquery_optimized": optimized_tsquery,
                "from_cache": nlp_analysis.from_cache,
                "processing_time_ms": nlp_analysis.processing_time_ms,
            }
            
            cache_status = "CACHE HIT" if nlp_analysis.from_cache else "CACHE MISS"
            logger.info(
                f"NLP Analysis [{cache_status}]: type={nlp_analysis.semantic_type.value}, "
                f"entities={len(nlp_analysis.entities)}, "
                f"alpha={alpha:.2f}, entity_boost={entity_boost:.1f}, "
                f"expand={expand_query_flag}"
            )
        else:
            nlp_info = {"enabled": True, "failed": True}
        
        timings["nlp_ms"] = (time.time() - t0) * 1000
    else:
        nlp_info = {"enabled": False}
    
    # 0. Query Expansion (opcional)
    search_query = query
    if expand_query_flag:
        t0 = time.time()
        expansion_result = _expand_query_with_mode(query, expand_mode, max_synonyms)
        
        if expansion_result.get("expanded_terms"):
            # Usar query expandida para BM25
            search_query = expansion_result.get("tsquery", query)
            expansion_info = {
                "enabled": True,
                "original": query,
                "mode": expansion_result.get("mode", "static"),
                "from_cache": expansion_result.get("from_cache", False),
                "model_used": expansion_result.get("model_used"),
                "expanded_terms": expansion_result.get("expanded_terms", []),
                "theological_synonyms": expansion_result.get("theological_synonyms", []),
                "morphological_variants": expansion_result.get("morphological_variants", []),
                "related_concepts": expansion_result.get("related_concepts", []),
                "expansion_type": expansion_result.get("expansion_type", "none"),
            }
            logger.info(
                f"Query expanded ({expansion_result.get('mode', 'static')}): "
                f"'{query}' → '{search_query}' "
                f"(cache: {expansion_result.get('from_cache', False)})"
            )
        else:
            expansion_info = {"enabled": True, "original": query, "no_synonyms_found": True}
        timings["expansion_ms"] = (time.time() - t0) * 1000
    else:
        expansion_info = {"enabled": False}
    
    # 1. Busca BM25 (com query expandida se disponível)
    t0 = time.time()
    has_expansion = expand_query_flag and expansion_info.get("expanded_terms")
    
    # Determinar qual tsquery usar:
    # 1. Se tem expansão, usa tsquery da expansão
    # 2. Se tem NLP com tsquery otimizado, usa esse
    # 3. Senão, usa query original
    if has_expansion:
        bm25_query = search_query
        use_raw = True
    elif optimized_tsquery:
        bm25_query = optimized_tsquery
        use_raw = True
        logger.debug(f"Using NLP optimized tsquery: {optimized_tsquery}")
    else:
        bm25_query = query
        use_raw = False
    
    bm25_results = bm25_search(
        bm25_query,
        top_k=pool_size,
        versions=versions,
        book_id=book_id,
        use_raw_tsquery=use_raw,
        # Passar query original para boost quando há expansão
        original_query=query if has_expansion else None,
        original_boost=bm25_original_boost * entity_boost,  # Combinar boost configurável + entity boost
    )
    timings["bm25_ms"] = (time.time() - t0) * 1000
    
    # 2. Busca Vetorial (escolhe fonte baseado em embedding_source)
    t0 = time.time()
    embedding_info: dict[str, Any] = {"source": embedding_source}
    
    if embedding_source == "unified":
        # Usar unified_verse_embeddings (fusão de versões PT, 31K registros)
        # Nota: ignora filtro de versões pois embeddings são canônicos
        if versions:
            logger.info(
                f"embedding_source='unified' ignora filtro de versões {versions}. "
                "Embeddings são agnósticos de versão."
            )
        vector_results_raw = _vector_search_unified(
            query_embedding,
            top_k=pool_size,
            book_id=book_id,
        )
        # Enriquecer com dados reais do versículo
        preferred_version = versions[0] if versions else "NAA"
        vector_results = _enrich_unified_results(vector_results_raw, preferred_version)
        embedding_info.update({
            "table": "unified_verse_embeddings",
            "records": "31K (canônico)",
            "languages": ["pt"],
            "fusion_strategy": "weighted_average",
            "source_versions": ["NVI", "ARA", "NAA", "AS21", "ACF", "NTLH", "NVT", "ARC"],
        })
    else:
        # Usar verse_embeddings (por versão, 529K registros, PT+EN)
        vector_results = _vector_search(
            query_embedding,
            top_k=pool_size,
            versions=versions,
            book_id=book_id,
        )
        embedding_info.update({
            "table": "verse_embeddings",
            "records": "529K (por versão)",
            "languages": ["pt", "en"],
            "versions_filter": versions,
        })
    
    timings["vector_ms"] = (time.time() - t0) * 1000
    
    # 3. Fusão RRF
    t0 = time.time()
    fused_results = reciprocal_rank_fusion(
        bm25_results,
        vector_results,
        k=rrf_k,
        alpha=alpha,
    )
    timings["fusion_ms"] = (time.time() - t0) * 1000
    
    # 4. Preparar candidatos para reranking/MMR (ou top_k final)
    # Se reranking ou MMR habilitado, pegar mais candidatos
    if rerank_with_large or mmr_lambda is not None:
        candidates_for_rerank = fused_results[:pool_size]
    else:
        candidates_for_rerank = fused_results[:top_k]
    
    # Formatar para compatibilidade com API existente
    # Normalizar query para verificar se texto contém a palavra
    import unicodedata
    query_normalized = query.lower().strip()
    query_normalized = "".join(
        c for c in unicodedata.normalize("NFKD", query_normalized) 
        if not unicodedata.combining(c)
    )
    
    hits = []
    for result in candidates_for_rerank:
        # Verificar se o texto contém a query original
        text_normalized = result["text"].lower()
        text_normalized = "".join(
            c for c in unicodedata.normalize("NFKD", text_normalized)
            if not unicodedata.combining(c)
        )
        contains_query = query_normalized in text_normalized
        
        hits.append({
            "verse_id": result["verse_id"],
            "book_id": result["book_id"],
            "book_osis": result["book_osis"],
            "chapter": result["chapter"],
            "verse": result["verse"],
            "text": result["text"],
            "version": result["version_code"],
            "similarity": result["final_score"],
            "distance": 1.0 - result["final_score"],
            # Métricas extras
            "bm25_score": result.get("bm25_score"),
            "vector_score": result.get("vector_score"),
            "rrf_score": result["rrf_score"],
            # Flags de origem
            "match_source": result.get("match_source", "unknown"),
            "contains_query": contains_query,
        })
    
    # 5. Two-Stage Reranking com embedding large (se habilitado)
    if rerank_with_large and hits:
        from .reranking import rerank_with_large_embeddings, compare_rankings
        
        t0 = time.time()
        original_hits = hits.copy()
        rerank_result = rerank_with_large_embeddings(
            hits=hits,
            query=query,
            top_k=top_k,
        )
        hits = rerank_result.hits
        timings["rerank_ms"] = (time.time() - t0) * 1000
        
        # Análise de mudanças no ranking
        comparison = compare_rankings(original_hits[:top_k], hits)
        
        reranking_info = {
            "enabled": True,
            "model": "text-embedding-3-large",
            "dimension": 3072,
            "candidates_evaluated": rerank_result.metrics.candidates_count,
            "rank_changes": rerank_result.metrics.rank_changes,
            "avg_rank_shift": round(rerank_result.metrics.avg_rank_shift, 2),
            "top_k_preserved": round(rerank_result.metrics.top_k_preserved, 2),
            "kendall_tau": comparison["kendall_tau"],
            "timing_ms": round(rerank_result.metrics.total_time_ms, 2),
        }
    else:
        # Limitar ao top_k se não houver reranking nem MMR
        if mmr_lambda is None:
            hits = hits[:top_k]
        reranking_info = {"enabled": False}
    
    # 6. MMR Diversification (se habilitado)
    if mmr_lambda is not None and hits:
        from .mmr import mmr_diversify, deduplicate_by_version
        
        t0 = time.time()
        
        # Primeiro, opcionalmente deduplica versões
        pre_dedup_count = len(hits)
        if deduplicate_versions:
            hits = deduplicate_by_version(hits)
            dedup_removed = pre_dedup_count - len(hits)
        else:
            dedup_removed = 0
        
        # Agora aplica MMR
        pre_mmr_count = len(hits)
        
        # mmr_diversify retorna MMRResult
        mmr_result = mmr_diversify(
            hits=hits,
            top_k=top_k,
            lambda_param=mmr_lambda,
            use_embeddings=False,  # Por ora, usar deduplicação por ID canônico
        )
        hits = mmr_result.hits
        
        timings["mmr_ms"] = (time.time() - t0) * 1000
        
        # Análise de diversificação
        mmr_info = {
            "enabled": True,
            "lambda": mmr_lambda,
            "deduplicate_versions": deduplicate_versions,
            "duplicates_removed": mmr_result.duplicates_removed + dedup_removed,
            "candidates_processed": pre_mmr_count,
            "results_selected": len(hits),
            "diversity_score": round(mmr_result.diversity_score, 3),
            "timing_ms": round(timings["mmr_ms"], 2),
        }
        
        logger.info(
            f"MMR diversification: {pre_mmr_count} → {len(hits)} results "
            f"(λ={mmr_lambda}, diversity={mmr_result.diversity_score:.2f}) in {timings['mmr_ms']:.1f}ms"
        )
    else:
        mmr_info = {"enabled": False}
    
    total_time = (time.time() - start_time) * 1000
    
    expansion_log = ""
    if expand_query_flag and expansion_info.get("expanded_terms"):
        mode = expansion_info.get("mode", "static")
        term_count = len(expansion_info.get("expanded_terms", []))
        expansion_log = f" (expanded[{mode}]: {term_count} terms)"
    
    rerank_log = ""
    if rerank_with_large:
        rerank_log = f" (reranked: {reranking_info.get('rank_changes', 0)} changes)"
    
    mmr_log = ""
    if mmr_lambda is not None:
        mmr_log = f" (MMR λ={mmr_lambda}, dedup={mmr_info.get('duplicates_removed', 0)})"

    logger.info(
        f"Hybrid search: {len(hits)} results in {total_time:.1f}ms "
        f"(BM25: {timings['bm25_ms']:.1f}ms, Vector: {timings['vector_ms']:.1f}ms)"
        f"{expansion_log}{rerank_log}{mmr_log}"
    )
    
    result_dict: dict[str, Any] = {
        "hits": hits,
        "total": len(hits),
        "timing": {
            "total_ms": round(total_time, 2),
            "bm25_ms": round(timings["bm25_ms"], 2),
            "vector_ms": round(timings["vector_ms"], 2),
            "fusion_ms": round(timings["fusion_ms"], 2),
        },
        "config": {
            "alpha": alpha,
            "rrf_k": rrf_k,
            "pool_size": pool_size,
            "expand_query": expand_query_flag,
            "rerank_with_large": rerank_with_large,
            "mmr_lambda": mmr_lambda,
            "deduplicate_versions": deduplicate_versions,
            "embedding_source": embedding_source,
            "use_nlp_analysis": use_nlp_analysis,
        },
        "stats": {
            "bm25_candidates": len(bm25_results),
            "vector_candidates": len(vector_results),
            "unique_candidates": len(fused_results),
        },
        "embedding_source_info": embedding_info,
    }
    
    # Adicionar informações de análise NLP
    if use_nlp_analysis:
        result_dict["nlp_analysis"] = nlp_info
        if "nlp_ms" in timings:
            result_dict["timing"]["nlp_ms"] = round(timings["nlp_ms"], 2)
    
    # Adicionar informações de expansão se habilitada
    if expand_query_flag:
        result_dict["query_expansion"] = expansion_info
        if "expansion_ms" in timings:
            result_dict["timing"]["expansion_ms"] = round(timings["expansion_ms"], 2)
    
    # Adicionar informações de reranking se habilitado
    if rerank_with_large:
        result_dict["reranking"] = reranking_info
        if "rerank_ms" in timings:
            result_dict["timing"]["rerank_ms"] = round(timings["rerank_ms"], 2)
    
    # Adicionar informações de MMR se habilitado
    if mmr_lambda is not None:
        result_dict["mmr_diversification"] = mmr_info
        if "mmr_ms" in timings:
            result_dict["timing"]["mmr_ms"] = round(timings["mmr_ms"], 2)
    
    return result_dict


def _vector_search(
    embedding: list[float],
    *,
    top_k: int = 100,
    versions: list[str] | None = None,
    book_id: int | None = None,
) -> list[dict[str, Any]]:
    """Busca vetorial simples para uso interno."""
    dim = len(embedding)
    nums = ",".join(format(float(x), ".8g") for x in embedding)
    vec_sql = f"ARRAY[{nums}]::vector({dim})"
    
    sql_parts = [
        "SELECT",
        "  v.id as verse_id,",
        "  v.book_id,",
        "  cb.osis_code as book_osis,",
        "  v.chapter,",
        "  v.number as verse,",
        "  v.text,",
        "  ve.version_code,",
        f"  (ve.embedding_small <=> {vec_sql}) as distance",
        "FROM verse_embeddings ve",
        "JOIN verses v ON v.id = ve.verse_id",
        "JOIN canonical_books cb ON cb.id = v.book_id",
        "WHERE ve.embedding_small IS NOT NULL",
    ]
    
    params: list[Any] = []
    
    if versions:
        sql_parts.append("AND ve.version_code = ANY(%s)")
        params.append(versions)
    
    if book_id is not None:
        sql_parts.append("AND v.book_id = %s")
        params.append(book_id)
    
    sql_parts.extend([
        "ORDER BY distance ASC",
        "LIMIT %s",
    ])
    params.append(top_k)
    
    sql = "\n".join(sql_parts)
    
    results = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        for i, row in enumerate(rows):
            dist = float(row[7])
            results.append({
                "verse_id": row[0],
                "book_id": row[1],
                "book_osis": row[2],
                "chapter": row[3],
                "verse": row[4],
                "text": row[5],
                "version_code": row[6],
                "distance": dist,
                "similarity": 1.0 - dist,
                "vector_score": 1.0 - dist,
                "vector_rank": i + 1,
            })
    
    return results


def _vector_search_unified(
    embedding: list[float],
    *,
    top_k: int = 100,
    book_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Busca vetorial usando unified_verse_embeddings (fusão de versões PT).
    
    Esta tabela contém embeddings canônicos que combinam múltiplas traduções
    portuguesas (NVI, ARA, NAA, etc.) para melhor recall semântico.
    
    Args:
        embedding: Vetor da query (1536 dim para small)
        top_k: Número de resultados
        book_id: Filtro opcional por livro
        
    Returns:
        Lista de resultados com canonical_verse_id
        
    Nota: Não suporta filtro por versão (embeddings são agnósticos de versão).
          Para versões em inglês, use _vector_search() com verse_embeddings.
    """
    dim = len(embedding)
    nums = ",".join(format(float(x), ".8g") for x in embedding)
    vec_sql = f"ARRAY[{nums}]::vector({dim})"
    
    sql_parts = [
        "SELECT",
        "  uve.canonical_verse_id,",
        "  uve.source_versions,",
        "  uve.fusion_strategy,",
        "  uve.quality_score,",
        f"  (uve.unified_embedding_small <=> {vec_sql}) as distance",
        "FROM unified_verse_embeddings uve",
        "WHERE uve.unified_embedding_small IS NOT NULL",
    ]
    
    params: list[Any] = []
    
    # Filtro por livro usando prefixo do canonical_verse_id (ex: "Gen.1.1" → "Gen")
    if book_id is not None:
        # Precisamos fazer JOIN com canonical_books para filtrar
        sql_parts = [
            "SELECT",
            "  uve.canonical_verse_id,",
            "  uve.source_versions,",
            "  uve.fusion_strategy,",
            "  uve.quality_score,",
            f"  (uve.unified_embedding_small <=> {vec_sql}) as distance",
            "FROM unified_verse_embeddings uve",
            "JOIN canonical_books cb ON cb.osis_code = SPLIT_PART(uve.canonical_verse_id, '.', 1)",
            "WHERE uve.unified_embedding_small IS NOT NULL",
            "AND cb.id = %s",
        ]
        params.append(book_id)
    
    sql_parts.extend([
        "ORDER BY distance ASC",
        "LIMIT %s",
    ])
    params.append(top_k)
    
    sql = "\n".join(sql_parts)
    
    results = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        for i, row in enumerate(rows):
            canonical_id = row[0]  # Ex: "Gen.1.1"
            source_versions = row[1]  # Ex: ['NVI', 'ARA', 'NAA']
            dist = float(row[4])
            
            # Parse canonical_verse_id para extrair book, chapter, verse
            parts = canonical_id.split(".")
            book_osis = parts[0] if len(parts) >= 1 else ""
            chapter = int(parts[1]) if len(parts) >= 2 else 0
            verse = int(parts[2]) if len(parts) >= 3 else 0
            
            results.append({
                "canonical_verse_id": canonical_id,
                "book_osis": book_osis,
                "chapter": chapter,
                "verse": verse,
                "source_versions": source_versions,
                "fusion_strategy": row[2],
                "quality_score": row[3],
                "distance": dist,
                "similarity": 1.0 - dist,
                "vector_score": 1.0 - dist,
                "vector_rank": i + 1,
                # Campos para compatibilidade - serão preenchidos depois
                "verse_id": None,
                "book_id": None,
                "text": None,
                "version_code": source_versions[0] if source_versions else "NAA",
            })
    
    return results


def _enrich_unified_results(
    results: list[dict[str, Any]],
    preferred_version: str = "NAA",
) -> list[dict[str, Any]]:
    """
    Enriquece resultados da busca unified com dados reais dos versículos.
    
    Args:
        results: Resultados de _vector_search_unified
        preferred_version: Versão preferida para buscar o texto
        
    Returns:
        Resultados enriquecidos com verse_id, book_id e text
    """
    if not results:
        return results
    
    # Coletar canonical_verse_ids
    canonical_ids = [r["canonical_verse_id"] for r in results]
    
    # Buscar versículos reais - primeiro tenta a versão preferida
    sql = """
        SELECT 
            cb.osis_code || '.' || v.chapter || '.' || v.number as canonical_id,
            v.id as verse_id,
            v.book_id,
            v.text,
            bv.code as version_code
        FROM verses v
        JOIN canonical_books cb ON cb.id = v.book_id
        JOIN versions bv ON bv.id = v.version_id
        WHERE bv.code = %s
        AND (cb.osis_code || '.' || v.chapter || '.' || v.number) = ANY(%s)
    """
    
    verse_map = {}
    with connection.cursor() as cur:
        cur.execute(sql, [preferred_version, canonical_ids])
        for row in cur.fetchall():
            verse_map[row[0]] = {
                "verse_id": row[1],
                "book_id": row[2],
                "text": row[3],
                "version_code": row[4],
            }
    
    # Se algum não foi encontrado na versão preferida, tenta NVI
    missing = [cid for cid in canonical_ids if cid not in verse_map]
    if missing and preferred_version != "NVI":
        with connection.cursor() as cur:
            cur.execute(sql, ["NVI", missing])
            for row in cur.fetchall():
                if row[0] not in verse_map:
                    verse_map[row[0]] = {
                        "verse_id": row[1],
                        "book_id": row[2],
                        "text": row[3],
                        "version_code": row[4],
                    }
    
    # Enriquecer resultados
    enriched = []
    for r in results:
        cid = r["canonical_verse_id"]
        if cid in verse_map:
            r.update(verse_map[cid])
            enriched.append(r)
        else:
            # Versículo não encontrado - pode acontecer se versão não tem esse versículo
            logger.warning(f"Versículo {cid} não encontrado em {preferred_version} ou NVI")
    
    return enriched


# === Utilitários ===


def create_fulltext_index() -> str:
    """
    Gera SQL para criar índice GIN para full-text search.
    
    Execute este SQL manualmente ou via migração:
    ```sql
    CREATE INDEX CONCURRENTLY idx_verses_text_pt_gin 
    ON verses USING GIN (to_tsvector('portuguese', text));
    
    CREATE INDEX CONCURRENTLY idx_verses_text_en_gin 
    ON verses USING GIN (to_tsvector('english', text));
    ```
    """
    return """
-- Índice GIN para full-text search em português
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verses_text_pt_gin 
ON verses USING GIN (to_tsvector('portuguese', text));

-- Índice GIN para full-text search em inglês
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verses_text_en_gin 
ON verses USING GIN (to_tsvector('english', text));

-- Estatísticas para otimização
ANALYZE verses;
"""
