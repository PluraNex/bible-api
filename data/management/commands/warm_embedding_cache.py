"""
Management command to warm the embedding cache before benchmark runs.

Usage:
    python manage.py warm_embedding_cache
    python manage.py warm_embedding_cache --queries path/to/queries.json
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Warm the embedding cache with common theological queries and benchmark queries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--queries",
            type=str,
            default=None,
            help="Path to JSON file with queries to pre-cache (e.g., pilot_queries_v2.json)",
        )

    def handle(self, *args, **options):
        from bible.ai.embedding_cache import embedding_cache

        self.stdout.write("Warming embedding cache...")

        # Warm common theological queries (built-in list)
        count = embedding_cache._warmup_common_embeddings()
        self.stdout.write(f"  Warmed {count} common queries")

        # Warm benchmark queries if provided
        queries_path = options.get("queries")
        if queries_path:
            import json
            from pathlib import Path

            path = Path(queries_path)
            if not path.exists():
                self.stderr.write(f"  File not found: {path}")
                return

            with open(path, encoding="utf-8") as f:
                queries = json.load(f)

            benchmark_count = 0
            for q in queries:
                query_text = q.get("query", "")
                if query_text:
                    embedding_cache.get_embedding(query_text, model="text-embedding-3-small")
                    benchmark_count += 1

            self.stdout.write(f"  Warmed {benchmark_count} benchmark queries from {path.name}")

        stats = embedding_cache.get_stats()
        self.stdout.write(
            f"  Cache stats: {stats.get('total_requests', 0)} requests, "
            f"{stats.get('hit_rate', 0):.0%} hit rate"
        )
        self.stdout.write(self.style.SUCCESS("Cache warm-up complete"))
