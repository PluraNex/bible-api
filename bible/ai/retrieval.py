"""RAG Retrieval service helpers."""
from __future__ import annotations

import os
import time
from collections.abc import Sequence
from typing import Any

from django.core.cache import cache
from django.db import connection


def _vector_array_sql(vec: Sequence[float], dim: int) -> str:
    if not vec:
        raise ValueError("Vector vazio")
    if len(vec) != dim:
        # Aceita vetores maiores cortando; se menor, falha
        if len(vec) > dim:
            vec = vec[:dim]
        else:
            raise ValueError(f"Dimensão incorreta: esperado {dim}, recebido {len(vec)}")
    # Monta ARRAY[...]::vector(dim)
    nums = ",".join(format(float(x), ".8g") for x in vec)
    return f"ARRAY[{nums}]::vector({dim})"


def _normalize_query(text: str) -> str:
    return " ".join((text or "").strip().split()).lower()


def _embed_query(text: str, model: str = "text-embedding-3-small", timeout: float = 30.0) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não definido; envie 'vector' no request ou configure a chave.")
    from openai import OpenAI

    client = OpenAI()
    resp = client.embeddings.create(model=model, input=[text], timeout=timeout)
    return resp.data[0].embedding


def _embed_query_cached(text: str, model: str, timeout: float) -> list[float]:
    ttl = int(os.getenv("RAG_QEMB_CACHE_TTL", "900"))
    key = f"qemb:{model}:{hash(_normalize_query(text))}"
    vec = cache.get(key)
    if vec:
        return vec
    vec = _embed_query(text, model=model, timeout=timeout)
    cache.set(key, vec, ttl)
    return vec


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    import math

    if not a or not b:
        return 0.0
    s = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b, strict=True):
        s += x * y
        na += x * x
        nb += y * y
    denom = (math.sqrt(na) * math.sqrt(nb)) or 1e-12
    return float(s / denom)


def retrieve(
    *,
    query: str | None = None,
    vector: Sequence[float] | None = None,
    top_k: int = 10,
    versions: Sequence[str] | None = None,
    book_id: int | None = None,
    chapter: int | None = None,
    chapter_end: int | None = None,
    lang: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Execute vector retrieve with optional filters.

    Returns dict with hits and timing info.
    """
    if vector is None and (query is None or not query.strip()):
        raise ValueError("Informe 'query' ou 'vector'.")

    # Embedding da query (ou usar o vetor fornecido)
    if vector is None:
        query_vec = _embed_query(query.strip(), timeout=timeout)
    else:
        query_vec = list(map(float, vector))

    dim = 1536  # small
    vec_sql = _vector_array_sql(query_vec, dim)

    # Se não vier filtro de versões, aplicar RAG_ALLOWED_VERSIONS (CSV do env), se definido
    if not versions:
        env_allowed = os.getenv("RAG_ALLOWED_VERSIONS", "").strip()
        if env_allowed:
            versions = [v.strip() for v in env_allowed.split(",") if v.strip()]

    # SQL base
    sql = [
        "SELECT v.id, v.book_id, v.chapter, v.number, v.text, ve.version_code, cb.osis_code,",
        f"       (ve.embedding_small <=> {vec_sql}) AS score",
        "FROM verse_embeddings ve",
        "JOIN verses v ON v.id = ve.verse_id",
        "JOIN canonical_books cb ON cb.id = v.book_id",
    ]
    where = ["ve.embedding_small IS NOT NULL"]
    params: list[Any] = []

    if versions:
        where.append("ve.version_code = ANY(%s)")
        params.append(list(versions))
    if book_id is not None:
        where.append("v.book_id = %s")
        params.append(int(book_id))
    if chapter is not None and chapter_end is not None:
        where.append("v.chapter BETWEEN %s AND %s")
        params.extend([int(chapter), int(chapter_end)])
    elif chapter is not None:
        where.append("v.chapter = %s")
        params.append(int(chapter))
    # lang opcional: filtrar por language via versions seria caro; usar version_code por agora.

    if where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY score ASC")
    # Fetch mais que top_k para permitir dedupe por referência
    env_pool = int(os.getenv("RAG_RERANK_CANDIDATES", "0") or 0)
    fetch_limit = env_pool if env_pool > 0 else max(int(top_k) * 3, int(top_k) + 10)
    sql.append("LIMIT %s")
    params.append(fetch_limit)

    full_sql = "\n".join(sql)

    start = time.time()
    with connection.cursor() as cur:
        cur.execute(full_sql, params)
        rows = cur.fetchall()
    dur = time.time() - start

    # Rows: id, book_id, chapter, number, text, version_code, osis_code, score
    raw_hits = []
    for r in rows:
        verse_id, b_id, ch, num, text, ver, osis, dist = r
        dist = float(dist)
        sim = 1.0 / (1.0 + max(dist, 0.0))
        ref = f"{osis} {ch}:{num}"
        raw_hits.append(
            {
                "verse_id": verse_id,
                "book_id": b_id,
                "chapter": ch,
                "number": num,
                "text": text,
                "version": ver,
                "osis": osis,
                "ref": ref,
                "score": dist,
                "similarity": sim,
            }
        )

    # Dedupe por referência (book_id, chapter, number), mantendo melhor distância
    # Em empate, preferir versão por prioridade definida em env
    priority_csv = os.getenv("RAG_VERSION_PRIORITY", "PT_NAA,PT_ARA,PT_NTLH,EN_KJV")
    version_priority = {code.strip(): i for i, code in enumerate(priority_csv.split(",")) if code.strip()}

    deduped: dict[tuple[int, int, int], dict[str, Any]] = {}
    for h in raw_hits:
        key = (h["book_id"], h["chapter"], h["number"])
        current = deduped.get(key)
        if current is None:
            deduped[key] = h
            continue
        # Escolher por menor score (distância)
        if h["score"] < current["score"]:
            deduped[key] = h
        elif abs(h["score"] - current["score"]) < 1e-9:
            # Empate: escolher por prioridade de versão
            cur_rank = version_priority.get(current.get("version", ""), 9999)
            new_rank = version_priority.get(h.get("version", ""), 9999)
            if new_rank < cur_rank:
                deduped[key] = h

    candidates = list(deduped.values())

    # Rerank leve usando embedding_large (opt-in via env RAG_RERANK_LARGE)
    t_rerank = 0.0
    try:
        use_rerank = os.getenv("RAG_RERANK_LARGE", "0").lower() in ("1", "true", "yes", "on")
        if use_rerank and candidates:
            import time as _time

            # Query embedding (large): usar vetor fornecido se plausível, senão embedar
            q_vec_large: list[float] | None = None
            if vector is not None and isinstance(vector, list | tuple) and len(vector) >= 1024:
                # Se o cliente já mandou um vetor grande (>=1024), use como aproximação
                q_vec_large = list(map(float, vector))[:3072]
            elif query:
                t0 = _time.time()
                q_vec_large = _embed_query_cached(query, model="text-embedding-3-large", timeout=timeout)
                t_rerank += _time.time() - t0

            if q_vec_large:
                # Buscar embedding_large dos candidatos
                ids = [c["verse_id"] for c in candidates]
                verse2large: dict[int, Sequence[float] | None] = {}
                t1 = _time.time()
                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT verse_id, embedding_large FROM verse_embeddings WHERE verse_id = ANY(%s)",
                        (ids,),
                    )
                    for vid, emb in cur.fetchall():
                        verse2large[int(vid)] = emb

                # Calcular similaridade grande
                ranked: list[dict[str, Any]] = []
                for c in candidates:
                    emb = verse2large.get(int(c["verse_id"]))
                    sim_large = _cosine(q_vec_large, emb) if emb is not None else 0.0
                    item = dict(c)
                    item["similarity_large"] = sim_large
                    ranked.append(item)
                # Ordenar por sim_large desc (fallback: distância pequena)
                ranked.sort(key=lambda x: (-(x.get("similarity_large") or 0.0), x["score"]))

                # MMR opcional
                use_mmr = os.getenv("RAG_MMR", "0").lower() in ("1", "true", "yes", "on")
                mmr_lambda = float(os.getenv("RAG_MMR_LAMBDA", "0.7"))
                if use_mmr and ranked:
                    selected: list[dict[str, Any]] = []
                    pool = ranked[:]
                    # Precompute candidate vectors for pairwise sims
                    cand_vecs: dict[int, Sequence[float] | None] = {
                        int(c["verse_id"]): verse2large.get(int(c["verse_id"])) for c in pool
                    }
                    while pool and len(selected) < int(top_k):
                        best, best_val = None, -1e9
                        for c in pool:
                            sim_q = float(c.get("similarity_large") or 0.0)
                            max_sim_s = 0.0
                            if selected:
                                for s in selected:
                                    v_c = cand_vecs.get(int(c["verse_id"]))
                                    v_s = cand_vecs.get(int(s["verse_id"]))
                                    if v_c is not None and v_s is not None:
                                        cs = _cosine(v_c, v_s)
                                        if cs > max_sim_s:
                                            max_sim_s = cs
                            val = mmr_lambda * sim_q - (1.0 - mmr_lambda) * max_sim_s
                            if val > best_val:
                                best, best_val = c, val
                        selected.append(best)
                        pool.remove(best)
                    hits = selected
                else:
                    hits = ranked[: int(top_k)]
                t_rerank += _time.time() - t1
            else:
                hits = sorted(candidates, key=lambda x: x["score"])[: int(top_k)]
        else:
            hits = sorted(candidates, key=lambda x: x["score"])[: int(top_k)]
    except Exception:
        # Fallback silencioso: mantém ordenação por distância
        hits = sorted(candidates, key=lambda x: x["score"])[: int(top_k)]

    # Optional: Hybrid lexical + vector (opt-in via RAG_HYBRID)
    t_hybrid = 0.0
    try:
        use_hybrid = os.getenv("RAG_HYBRID", "0").lower() in ("1", "true", "yes", "on")
        alpha = float(os.getenv("RAG_HYBRID_ALPHA", "0.7"))  # weight for vector similarity
        if use_hybrid and query and candidates:
            import time as _time

            t0 = _time.time()
            # Lexical query using simple configuration (safe/no stemming). Limit similar to fetch_limit
            lex_sql = [
                "SELECT v.id, v.book_id, v.chapter, v.number, v.text, cb.osis_code,",
                "       ts_rank(to_tsvector('simple', v.text), plainto_tsquery('simple', %s)) AS lex_rank",
                "FROM verses v",
                "JOIN canonical_books cb ON cb.id = v.book_id",
            ]
            lex_where = ["v.text IS NOT NULL"]
            lex_params: list[Any] = [query]
            if versions:
                # Need to map version codes to ids; rely on version_code in embeddings to avoid an extra join
                # Efficient approach: limit to verses that have embeddings for given versions
                lex_sql.append("JOIN verse_embeddings ve ON ve.verse_id = v.id")
                lex_where.append("ve.version_code = ANY(%s)")
                lex_params.append(list(versions))
            if book_id is not None:
                lex_where.append("v.book_id = %s")
                lex_params.append(int(book_id))
            if chapter is not None and chapter_end is not None:
                lex_where.append("v.chapter BETWEEN %s AND %s")
                lex_params.extend([int(chapter), int(chapter_end)])
            elif chapter is not None:
                lex_where.append("v.chapter = %s")
                lex_params.append(int(chapter))

            if lex_where:
                lex_sql.append("WHERE " + " AND ".join(lex_where))
            lex_sql.append("ORDER BY lex_rank DESC")
            lex_sql.append("LIMIT %s")
            lex_params.append(fetch_limit)

            with connection.cursor() as cur:
                cur.execute("\n".join(lex_sql), lex_params)
                lex_rows = cur.fetchall()
            t_hybrid += _time.time() - t0

            # Build lex map keyed by (book_id, chapter, number) with max lex_rank
            lex_map: dict[tuple[int, int, int], float] = {}
            max_lex = 0.0
            for _vid, b_id, ch, num, _txt, _osis, lrank in lex_rows:
                key = (int(b_id), int(ch), int(num))
                val = float(lrank or 0.0)
                if val > lex_map.get(key, 0.0):
                    lex_map[key] = val
                if val > max_lex:
                    max_lex = val

            # Combine scores
            if lex_map and max_lex > 0:
                for item in candidates:
                    key = (item["book_id"], item["chapter"], item["number"])
                    lex_norm = (lex_map.get(key, 0.0) / max_lex) if max_lex > 0 else 0.0
                    item["lex_rank"] = lex_map.get(key, 0.0)
                    item["lex_norm"] = lex_norm
                    item["final"] = alpha * float(item.get("similarity", 0.0)) + (1.0 - alpha) * lex_norm
                # Sort by final desc; fallback to distance
                hits = sorted(candidates, key=lambda x: (-(x.get("final") or 0.0), x["score"]))[: int(top_k)]
                return {"hits": hits, "timing": {"db": dur, "rerank": t_rerank, "hybrid": t_hybrid}}
    except Exception:
        # Ignore hybrid failures silently
        pass

    return {"hits": hits, "timing": {"db": dur, "rerank": t_rerank}}
