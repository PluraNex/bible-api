"""Create/Drop pgvector IVFFlat indexes with safe defaults.

Usage examples:
  python manage.py create_vector_indexes --create \
    --table=verse_embeddings --column=embedding_small \
    --opclass=vector_cosine_ops --lists=64 --dim=1536 --alter-dim

  python manage.py create_vector_indexes --drop \
    --index-name=idx_verse_embeddings_small_ivf

Notes:
- Uses CREATE INDEX CONCURRENTLY (requires autocommit).
- You can raise maintenance_work_mem only for this session via --maintenance-work-mem (e.g., 512MB).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import connection

SAFE_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class IndexSpec:
    table: str = "verse_embeddings"
    column: str = "embedding_small"
    opclass: str = "vector_cosine_ops"
    lists: int = 64
    dim: int | None = 1536
    index_name: str | None = None
    maintenance_work_mem: str | None = None  # e.g., '512MB'
    alter_dim: bool = False


class Command(BaseCommand):
    help = "Create or drop IVFFlat indexes for pgvector"

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group(required=True)
        g.add_argument("--create", action="store_true", help="Create index")
        g.add_argument("--drop", action="store_true", help="Drop index")

        parser.add_argument("--table", type=str, default="verse_embeddings")
        parser.add_argument("--column", type=str, default="embedding_small")
        parser.add_argument("--opclass", type=str, default="vector_cosine_ops")
        parser.add_argument("--lists", type=int, default=64)
        parser.add_argument("--dim", type=int, default=1536)
        parser.add_argument("--index-name", type=str, default=None)
        parser.add_argument("--maintenance-work-mem", type=str, default=None, help="e.g., 512MB, 1GB")
        parser.add_argument("--alter-dim", action="store_true", help="Alter column type to vector(dim) before index")

    def handle(self, *args, **opts):
        spec = IndexSpec(
            table=opts["table"],
            column=opts["column"],
            opclass=opts["opclass"],
            lists=opts["lists"],
            dim=opts["dim"],
            index_name=opts["index_name"] or f"idx_{opts['table']}_{opts['column']}_ivf",
            maintenance_work_mem=opts["maintenance_work_mem"],
            alter_dim=opts["alter_dim"],
        )

        self._validate_ident(spec.table)
        self._validate_ident(spec.column)
        self._validate_ident(spec.index_name)
        self._validate_ident(spec.opclass)

        # Ensure autocommit for CONCURRENTLY
        connection.ensure_connection()
        if not connection.get_autocommit():
            connection.set_autocommit(True)

        with connection.cursor() as cur:
            # Optional: raise maintenance_work_mem for this session
            if spec.maintenance_work_mem:
                cur.execute(f"SET maintenance_work_mem = '{spec.maintenance_work_mem}'")
                self.stdout.write(self.style.NOTICE(f"maintenance_work_mem set to {spec.maintenance_work_mem}"))

            if opts["drop"]:
                sql = f"DROP INDEX CONCURRENTLY IF EXISTS {spec.index_name}"
                cur.execute(sql)
                self.stdout.write(self.style.SUCCESS(f"Dropped index if exists: {spec.index_name}"))
                return

            # Create flow
            if spec.alter_dim and spec.dim:
                alter_sql = f"ALTER TABLE {spec.table} " f"ALTER COLUMN {spec.column} TYPE vector({spec.dim})"
                cur.execute(alter_sql)
                self.stdout.write(self.style.SUCCESS(f"Column {spec.table}.{spec.column} set to vector({spec.dim})"))

            sql = (
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {spec.index_name} "
                f"ON {spec.table} USING ivfflat ({spec.column} {spec.opclass}) "
                f"WITH (lists = {spec.lists})"
            )
            cur.execute(sql)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Index created: {spec.index_name} on {spec.table}({spec.column}) lists={spec.lists}"
                )
            )

    def _validate_ident(self, ident: str):
        if not SAFE_IDENT.match(ident):
            raise ValueError(f"Invalid identifier: {ident}")
