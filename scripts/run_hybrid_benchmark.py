#!/usr/bin/env python3
"""
Runner reproduzivel para benchmark da busca hibrida.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests import HTTPError

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api/v1")
API_KEY = os.getenv("API_KEY", "")
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
DEFAULT_QUERYSET = _PROJECT_ROOT / "data" / "experiments" / "hybrid_search" / "pilot_queries_v1.json"
DEFAULT_OUTPUT_ROOT = _PROJECT_ROOT / "data" / "experiments" / "hybrid_search" / "runs"
HYBRID_ENDPOINT_PATH = os.getenv("HYBRID_ENDPOINT_PATH", "/ai/rag/hybrid/")

EXPERIMENTS = [
    {
        "id": "baseline_hybrid",
        "description": "Controle hibrido balanceado",
        "alpha": 0.5,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "alpha_lexical",
        "description": "Controle textual forte",
        "alpha": 1.0,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "alpha_semantic",
        "description": "Controle semantico forte",
        "alpha": 0.0,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "expand_on",
        "description": "Com expansao de consulta",
        "alpha": 0.5,
        "expand": True,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "rerank_on",
        "description": "Com reranking de segundo estagio",
        "alpha": 0.5,
        "expand": False,
        "rerank": True,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "mmr_relevance",
        "description": "MMR priorizando relevancia",
        "alpha": 0.5,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": 0.8,
    },
    {
        "id": "mmr_balanced",
        "description": "MMR balanceado",
        "alpha": 0.5,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": 0.5,
    },
    {
        "id": "mmr_diversity",
        "description": "MMR priorizando diversidade",
        "alpha": 0.5,
        "expand": False,
        "rerank": False,
        "embedding_source": "verse",
        "mmr_lambda": 0.2,
    },
    {
        "id": "embedding_unified",
        "description": "Busca vetorial em unified embeddings",
        "alpha": 0.5,
        "expand": False,
        "rerank": False,
        "embedding_source": "unified",
        "mmr_lambda": None,
    },
    {
        "id": "full_pipeline",
        "description": "Pipeline completo: hybrid + expansion + rerank + diversificacao",
        "alpha": 0.5,
        "expand": True,
        "rerank": True,
        "embedding_source": "verse",
        "mmr_lambda": 0.5,
    },
    {
        "id": "expand_rerank",
        "description": "Expansion + reranking sem diversificacao",
        "alpha": 0.5,
        "expand": True,
        "rerank": True,
        "embedding_source": "verse",
        "mmr_lambda": None,
    },
    {
        "id": "unified_rerank",
        "description": "Unified embeddings com reranking de precisao",
        "alpha": 0.5,
        "expand": False,
        "rerank": True,
        "embedding_source": "unified",
        "mmr_lambda": None,
    },
]


def load_queries(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Arquivo de queries deve conter uma lista")
    return data


def select_queries(queries: list[dict[str, Any]], query_ids: list[str]) -> list[dict[str, Any]]:
    if not query_ids:
        return queries
    selected = [query for query in queries if query.get("id") in query_ids]
    missing = sorted(set(query_ids) - {query.get("id") for query in selected})
    if missing:
        raise ValueError(f"Query ids nao encontrados: {', '.join(missing)}")
    return selected


def select_experiments(experiment_ids: list[str]) -> list[dict[str, Any]]:
    if not experiment_ids:
        return EXPERIMENTS
    selected = [experiment for experiment in EXPERIMENTS if experiment["id"] in experiment_ids]
    missing = sorted(set(experiment_ids) - {experiment["id"] for experiment in selected})
    if missing:
        raise ValueError(f"Experimentos nao encontrados: {', '.join(missing)}")
    return selected


def build_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Api-Key {API_KEY}"
    return headers


def build_params(experiment: dict[str, Any], query: dict[str, Any], top_k: int, version: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query["query"],
        "top_k": top_k,
        "alpha": experiment["alpha"],
        "expand": str(experiment["expand"]).lower(),
        "rerank": str(experiment["rerank"]).lower(),
        "embedding_source": experiment["embedding_source"],
    }
    if experiment["mmr_lambda"] is not None:
        params["mmr_lambda"] = experiment["mmr_lambda"]
    if version:
        params["version"] = version
    return params


def to_reference(hit: dict[str, Any]) -> str:
    if hit.get("reference"):
        return str(hit["reference"])
    return f"{hit.get('book_osis', '')} {hit.get('chapter', 0)}:{hit.get('verse', 0)}".strip()


def average_precision(binary_relevance: list[int]) -> float | None:
    if not binary_relevance or sum(binary_relevance) == 0:
        return None
    precisions = []
    hits = 0
    for index, is_relevant in enumerate(binary_relevance, start=1):
        if is_relevant:
            hits += 1
            precisions.append(hits / index)
    return sum(precisions) / max(1, sum(binary_relevance))


def ndcg_at_k(gains: list[float]) -> float | None:
    if not gains:
        return None
    dcg = sum(gain / (1 if idx == 0 else math.log2(idx + 2)) for idx, gain in enumerate(gains))
    ideal = sorted(gains, reverse=True)
    idcg = sum(gain / (1 if idx == 0 else math.log2(idx + 2)) for idx, gain in enumerate(ideal))
    if idcg == 0:
        return None
    return dcg / idcg


def contains_query_token(query_text: str, hit: dict[str, Any]) -> bool:
    if "contains_query" in hit:
        return bool(hit["contains_query"])
    text = (hit.get("text") or "").lower()
    query_words = [word for word in query_text.lower().split() if len(word) > 2]
    return any(word in text for word in query_words)


def book_matches_expected(reference: str, hit: dict[str, Any], expected_books: list[str]) -> bool:
    haystack = " ".join(
        [
            reference.lower(),
            str(hit.get("book_name", "")).lower(),
            str(hit.get("book_osis", "")).lower(),
        ]
    )
    return any(book.lower() in haystack for book in expected_books)


def compute_metrics(query: dict[str, Any], hits: list[dict[str, Any]], top_k: int, response_data: dict[str, Any]) -> dict[str, Any]:
    limited_hits = hits[:top_k]
    references = [to_reference(hit) for hit in limited_hits]
    unique_books = {
        hit.get("book_osis") or hit.get("book_name")
        for hit in limited_hits
        if hit.get("book_osis") or hit.get("book_name")
    }
    expected_books = query.get("seed_signals", {}).get("expected_books", [])
    gold_references = query.get("gold_references", [])
    relevance_judgments = query.get("relevance_judgments", {})

    contains_query_count = sum(1 for hit in limited_hits if contains_query_token(query["query"], hit))
    expected_book_hits = sum(
        1
        for hit, reference in zip(limited_hits, references)
        if book_matches_expected(reference, hit, expected_books)
    )

    binary_relevance: list[int] = []
    gains: list[float] = []
    if gold_references:
        gold_set = {ref.lower() for ref in gold_references}
        binary_relevance = [1 if reference.lower() in gold_set else 0 for reference in references]
        gains = [
            float(relevance_judgments.get(reference, 1 if reference.lower() in gold_set else 0))
            for reference in references
        ]
    elif relevance_judgments:
        gains = [float(relevance_judgments.get(reference, 0)) for reference in references]
        binary_relevance = [1 if gain > 0 else 0 for gain in gains]

    precision_at_k = sum(binary_relevance) / top_k if binary_relevance else None
    recall_at_k = sum(binary_relevance) / len(gold_references) if binary_relevance and gold_references else None
    ap = average_precision(binary_relevance)
    ndcg = ndcg_at_k(gains)

    timing = response_data.get("timing", {})
    total_ms = timing.get("total_ms") or timing.get("total") or timing.get("search_ms")

    return {
        "top_k": top_k,
        "hit_count": len(limited_hits),
        "latency_ms": total_ms,
        "contains_query_rate": contains_query_count / max(1, len(limited_hits)),
        "expected_books_hit_rate": expected_book_hits / max(1, len(limited_hits)),
        "unique_books_at_k": len(unique_books),
        "diversity_unique_books_rate": len(unique_books) / max(1, len(limited_hits)),
        "unique_references_at_k": len(set(references)),
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "map": ap,
        "ndcg": ndcg,
        "judged": bool(gold_references or relevance_judgments),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["experiment_id"], []).append(row)

    aggregates = []
    for experiment_id, experiment_rows in grouped.items():
        aggregate: dict[str, Any] = {
            "experiment_id": experiment_id,
            "queries": len(experiment_rows),
        }
        for field in [
            "latency_ms",
            "contains_query_rate",
            "expected_books_hit_rate",
            "diversity_unique_books_rate",
            "precision_at_k",
            "recall_at_k",
            "map",
            "ndcg",
        ]:
            values = [row[field] for row in experiment_rows if row.get(field) is not None]
            aggregate[f"avg_{field}"] = round(sum(values) / len(values), 6) if values else None
        aggregates.append(aggregate)

    return sorted(aggregates, key=lambda row: row["experiment_id"])


def resolve_output_dir(output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_ROOT / timestamp


def build_hybrid_url() -> str:
    return f"{API_BASE.rstrip('/')}{HYBRID_ENDPOINT_PATH}"


def run_benchmark(
    queries: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    top_k: int,
    version: str | None,
    query_file: Path,
    output_dir: Path,
    dry_run: bool,
) -> None:
    plan = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "query_file": str(query_file),
        "top_k": top_k,
        "version": version,
        "dry_run": dry_run,
        "experiments": experiments,
        "queries": [
            {
                "id": query["id"],
                "query": query["query"],
                "query_type": query.get("query_type"),
            }
            for query in queries
        ],
    }
    write_json(output_dir / "plan.json", plan)

    if dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    session = requests.Session()
    session.headers.update(build_headers())

    summary_rows: list[dict[str, Any]] = []
    summary_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "results": [],
    }

    for experiment in experiments:
        for query in queries:
            params = build_params(experiment, query, top_k, version)
            try:
                response = session.get(
                    build_hybrid_url(),
                    params=params,
                    timeout=120,
                )
                response.raise_for_status()
            except HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else "?"
                url = exc.response.url if exc.response is not None else build_hybrid_url()
                raise RuntimeError(
                    "Falha chamando o endpoint híbrido. "
                    f"status={status_code} url={url}. "
                    "Verifique se a API correta está no ar e se `API_BASE` / "
                    "`HYBRID_ENDPOINT_PATH` apontam para a rota certa."
                ) from exc
            except requests.RequestException as exc:
                raise RuntimeError(
                    "Não foi possível conectar à API da busca híbrida. "
                    f"url={build_hybrid_url()}. Verifique API, Docker e porta 8000."
                ) from exc
            response_data = response.json()
            hits = response_data.get("hits", [])
            metrics = compute_metrics(query, hits, top_k, response_data)

            raw_payload = {
                "experiment": experiment,
                "query": query,
                "request": params,
                "response": response_data,
                "metrics": metrics,
            }
            raw_path = output_dir / "raw" / experiment["id"] / f"{query['id']}.json"
            write_json(raw_path, raw_payload)

            summary_row = {
                "experiment_id": experiment["id"],
                "query_id": query["id"],
                "query": query["query"],
                "query_type": query.get("query_type"),
                **metrics,
            }
            summary_rows.append(summary_row)
            summary_payload["results"].append(summary_row)

            print(
                f"[ok] {experiment['id']} :: {query['id']} "
                f"latency={metrics['latency_ms']} hit_count={metrics['hit_count']}"
            )

    write_json(output_dir / "summary.json", summary_payload)
    write_csv(output_dir / "summary.csv", summary_rows)
    write_csv(output_dir / "aggregate.csv", aggregate_rows(summary_rows))


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark reproduzivel da busca hibrida")
    parser.add_argument("--queries", default=str(DEFAULT_QUERYSET), help="Arquivo JSON com queries")
    parser.add_argument("--query-id", action="append", default=[], help="Filtrar por query id")
    parser.add_argument("--experiment", action="append", default=[], help="Filtrar por experimento")
    parser.add_argument("--top-k", type=int, default=10, help="Top K para avaliacao")
    parser.add_argument("--version", default=None, help="Versao biblica opcional")
    parser.add_argument("--output-dir", default=None, help="Diretorio de saida")
    parser.add_argument("--dry-run", action="store_true", help="Nao chama a API; apenas gera o plano")
    parser.add_argument("--list-experiments", action="store_true", help="Lista os experimentos disponiveis")
    args = parser.parse_args()

    if args.list_experiments:
        print(json.dumps(EXPERIMENTS, ensure_ascii=False, indent=2))
        return 0

    query_file = Path(args.queries)
    queries = select_queries(load_queries(query_file), args.query_id)
    experiments = select_experiments(args.experiment)
    output_dir = resolve_output_dir(args.output_dir)

    run_benchmark(
        queries=queries,
        experiments=experiments,
        top_k=args.top_k,
        version=args.version,
        query_file=query_file,
        output_dir=output_dir,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
