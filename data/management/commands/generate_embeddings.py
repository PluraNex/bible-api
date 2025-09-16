"""
Management command to generate verse embeddings (Fase 0) — versão PRO.

Exemplos:
  python manage.py generate_embeddings \
    --versions=PT_NAA,PT_ARA \
    --batch-size=128 --only-missing --sleep=0.1

  # Trocar modelos / pular um deles
  python manage.py generate_embeddings \
    --versions=EN_KJV --small-only --model-small=text-embedding-3-small

Modo dry-run (sem OPENAI_API_KEY): estima tokens e custo, e não grava.
"""
import hashlib
import os
import random
import time
from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import Verse, VerseEmbedding

# --------- Defaults / preços (ajuste se mudar no provedor) ----------
OPENAI_PRICING_PER_1M_TOKENS = {
    "text-embedding-3-small": 0.02,  # $ por 1M tokens
    "text-embedding-3-large": 0.13,
}

# fallback de dimensões (caso dry-run)
DEFAULT_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


# --------- Utilidades ----------
def norm_text(s: str) -> str:
    # normalização conservadora (mantém pontuação e espaços simples)
    return " ".join((s or "").split())


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def approx_token_count(texts: list[str]) -> int:
    # Aproximação rápida: ~4 chars por token (bom o suficiente p/ budget)
    # Para algo mais fiel, integre tiktoken se quiser.
    total_chars = sum(len(t) for t in texts)
    return max(1, total_chars // 4)


@dataclass
class EmbedBatchResult:
    vectors: list[list[float]]
    dim: int
    tokens: int


class Command(BaseCommand):
    help = "Generate embeddings for verses by version (robusto/observável)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--versions", type=str, required=True, help="Comma-separated version codes (e.g. PT_NAA,EN_KJV)"
        )
        parser.add_argument("--batch-size", type=int, default=128)
        parser.add_argument("--limit", type=int, default=0, help="Limit verses per version (0 = all)")
        parser.add_argument("--only-missing", action="store_true", help="Process only verses missing embeddings")
        parser.add_argument("--overwrite", action="store_true", help="Recompute even if embeddings exist")
        parser.add_argument(
            "--sleep",
            type=float,
            default=float(os.getenv("EMBEDDING_SLEEP", "0")),
            help="Sleep seconds between API calls (throttle)",
        )
        parser.add_argument("--max-retries", type=int, default=int(os.getenv("EMBEDDING_MAX_RETRIES", "5")))
        parser.add_argument("--timeout", type=float, default=float(os.getenv("EMBEDDING_TIMEOUT", "60")))
        parser.add_argument("--model-small", type=str, default="text-embedding-3-small")
        parser.add_argument("--model-large", type=str, default="text-embedding-3-large")
        parser.add_argument("--small-only", action="store_true", help="Generate only small embeddings")
        parser.add_argument("--large-only", action="store_true", help="Generate only large embeddings")
        parser.add_argument("--provider", type=str, default="openai")

    # ---------- OpenAI client (on-demand) ----------
    def _embed_openai(
        self, texts: list[str], model: str, timeout: float, max_retries: int, base_sleep: float
    ) -> EmbedBatchResult:
        """Chama a API de embeddings do OpenAI com backoff + jitter e devolve (vetores, dim, tokens)."""
        from openai import OpenAI

        client = OpenAI()

        last_exc = None
        # Repare: aumentamos o backoff exponencial + jitter
        for attempt in range(max_retries):
            try:
                start = time.time()
                resp = client.embeddings.create(model=model, input=texts, timeout=timeout)
                dur = time.time() - start
                vectors = [item.embedding for item in resp.data]
                dim = len(vectors[0]) if vectors else DEFAULT_DIMS.get(model, 1536)
                tokens = approx_token_count(texts)
                if base_sleep:
                    # throttle “gentil”: só dorme um tiquinho, mesmo quando sucesso
                    time.sleep(base_sleep)
                # log de sucesso
                self.stdout.write(
                    self.style.SUCCESS(f"[embed] model={model} n={len(texts)} dim={dim} dur_s={dur:.2f} tok≈{tokens}")
                )
                return EmbedBatchResult(vectors=vectors, dim=dim, tokens=tokens)
            except Exception as e:
                last_exc = e
                # backoff exponencial com jitter (0.5–1.5x)
                backoff = min(2**attempt, 10)
                backoff *= random.uniform(0.5, 1.5)
                self.stdout.write(self.style.WARNING(f"[embed] retry {attempt+1}/{max_retries} in {backoff:.1f}s: {e}"))
                time.sleep(backoff)

        raise last_exc

    def handle(self, *args, **opts):
        versions = [v.strip() for v in opts["versions"].split(",") if v.strip()]
        batch_size = opts["batch_size"]
        limit = opts["limit"]
        only_missing = opts["only_missing"]
        overwrite = opts["overwrite"]
        sleep = opts["sleep"]
        max_retries = opts["max_retries"]
        timeout = opts["timeout"]
        model_small = opts["model_small"]
        model_large = opts["model_large"]
        small_only = opts["small_only"]
        large_only = opts["large_only"]
        provider = opts["provider"]

        if only_missing and overwrite:
            self.stderr.write(self.style.ERROR("Flags conflitantes: use --only-missing OU --overwrite"))
            return
        if small_only and large_only:
            self.stderr.write(self.style.ERROR("Use apenas --small-only OU --large-only."))
            return

        api_key = os.getenv("OPENAI_API_KEY")
        dry_run = not api_key
        if dry_run:
            self.stdout.write(self.style.WARNING("OPENAI_API_KEY not set; running in DRY-RUN mode."))

        grand_total = 0
        grand_tokens: dict[str, int] = {}
        grand_cost: dict[str, float] = {}

        t0 = time.time()
        for code in versions:
            qs = Verse.objects.filter(version__code__iexact=code).order_by("book__canonical_order", "chapter", "number")
            if limit and limit > 0:
                qs = qs[:limit]
            total_verses = qs.count()
            self.stdout.write(self.style.NOTICE(f"Processing version={code} verses={total_verses}"))

            # mapa de versos já embutidos (quando only_missing)
            existing_ids = set()
            if only_missing and not overwrite:
                existing_ids = set(
                    VerseEmbedding.objects.filter(version_code__iexact=code, embedding_small__isnull=False).values_list(
                        "verse_id", flat=True
                    )
                )

            processed_version = 0
            version_tokens: dict[str, int] = {}
            version_cost: dict[str, float] = {}

            batch: list[Verse] = []
            # iterador em stream para reduzir memória
            for verse in qs.iterator(chunk_size=2048):
                if only_missing and not overwrite and verse.id in existing_ids:
                    continue
                batch.append(verse)
                if len(batch) >= batch_size:
                    n = self._process_batch(
                        verses=batch,
                        version_code=code,
                        provider=provider,
                        dry_run=dry_run,
                        model_small=model_small,
                        model_large=model_large,
                        small_only=small_only,
                        large_only=large_only,
                        overwrite=overwrite,
                        max_retries=max_retries,
                        sleep=sleep,
                        timeout=timeout,
                        tok_acc=version_tokens,
                        cost_acc=version_cost,
                    )
                    processed_version += n
                    batch = []
            if batch:
                n = self._process_batch(
                    verses=batch,
                    version_code=code,
                    provider=provider,
                    dry_run=dry_run,
                    model_small=model_small,
                    model_large=model_large,
                    small_only=small_only,
                    large_only=large_only,
                    overwrite=overwrite,
                    max_retries=max_retries,
                    sleep=sleep,
                    timeout=timeout,
                    tok_acc=version_tokens,
                    cost_acc=version_cost,
                )
                processed_version += n

            # somatórios por versão
            grand_total += processed_version
            for m, t in version_tokens.items():
                grand_tokens[m] = grand_tokens.get(m, 0) + t
            for m, c in version_cost.items():
                grand_cost[m] = grand_cost.get(m, 0.0) + c

            self.stdout.write(
                self.style.SUCCESS(
                    f"[version={code}] processed={processed_version} "
                    + " ".join(
                        [
                            f"{m}: tok≈{version_tokens.get(m,0)} cost≈${version_cost.get(m,0):.4f}"
                            for m in sorted(version_tokens.keys())
                        ]
                    )
                )
            )

        dur = time.time() - t0
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. versions={len(versions)} verses={grand_total} time={dur:.2f}s "
                + " ".join(
                    [
                        f"{m}: tok≈{grand_tokens.get(m,0)} cost≈${grand_cost.get(m,0):.2f}"
                        for m in sorted(grand_tokens.keys())
                    ]
                )
            )
        )

    @transaction.atomic
    def _process_batch(
        self,
        verses: list[Verse],
        version_code: str,
        provider: str,
        dry_run: bool,
        model_small: str,
        model_large: str,
        small_only: bool,
        large_only: bool,
        overwrite: bool,
        max_retries: int,
        sleep: float,
        timeout: float,
        tok_acc: dict[str, int],
        cost_acc: dict[str, float],
    ) -> int:
        # prepara textos e hashes
        texts = [norm_text(v.text) for v in verses]
        hashes = [sha256_hex(t) for t in texts]

        # carrega/instancia registros de embeddings
        # (get_or_create por item para manter simplicidade transacional)
        vec_small: list[list[float]] = []
        vec_large: list[list[float]] = []
        dim_small = DEFAULT_DIMS.get(model_small, 1536)
        dim_large = DEFAULT_DIMS.get(model_large, 3072)

        # Decide o que precisa re-embedar (por idempotência)
        # Regra: se overwrite=True → re-embeda tudo desse batch.
        # Senão: re-embeda apenas se não existe OU text_hash mudou OU modelo mudou.
        needs_small = []
        needs_large = []
        existing_rows: list[VerseEmbedding] = []

        # Pré-carrega objetos VerseEmbedding (ou cria)
        for i, verse in enumerate(verses):
            ve, _created = VerseEmbedding.objects.get_or_create(
                verse=verse,
                defaults={
                    "version_code": version_code,
                    "provider": provider,
                    "model_name_small": model_small if not small_only else None,
                    "model_name_large": model_large if not large_only else None,
                    "text_hash": hashes[i],
                },
            )
            existing_rows.append(ve)

        # Checa quem precisa Small
        if not large_only:
            for i, ve in enumerate(existing_rows):
                if overwrite:
                    needs_small.append(i)
                else:
                    # re-embeda se não existe, mudou o texto, ou modelo mudou
                    if not ve.embedding_small or ve.model_name_small != model_small or ve.text_hash != hashes[i]:
                        needs_small.append(i)

        # Checa quem precisa Large
        if not small_only:
            for i, ve in enumerate(existing_rows):
                if overwrite:
                    needs_large.append(i)
                else:
                    if not ve.embedding_large or ve.model_name_large != model_large or ve.text_hash != hashes[i]:
                        needs_large.append(i)

        # --- Embedding para quem precisa (em lote no provedor) ---
        # Small
        if not dry_run and needs_small:
            need_texts = [texts[i] for i in needs_small]
            res = self._embed_openai(need_texts, model_small, timeout, max_retries, sleep)
            vec_small = [None] * len(verses)
            for j, idx in enumerate(needs_small):
                vec_small[idx] = res.vectors[j]
            dim_small = res.dim
            tok_acc[model_small] = tok_acc.get(model_small, 0) + res.tokens
            cost_acc[model_small] = cost_acc.get(model_small, 0.0) + (
                res.tokens / 1_000_000
            ) * OPENAI_PRICING_PER_1M_TOKENS.get(model_small, 0.0)
        elif dry_run and needs_small:
            # estima tokens/custo
            tokens = approx_token_count([texts[i] for i in needs_small])
            tok_acc[model_small] = tok_acc.get(model_small, 0) + tokens
            cost_acc[model_small] = cost_acc.get(model_small, 0.0) + (
                tokens / 1_000_000
            ) * OPENAI_PRICING_PER_1M_TOKENS.get(model_small, 0.0)

        # Large
        if not dry_run and needs_large:
            need_texts = [texts[i] for i in needs_large]
            res = self._embed_openai(need_texts, model_large, timeout, max_retries, sleep)
            vec_large = [None] * len(verses)
            for j, idx in enumerate(needs_large):
                vec_large[idx] = res.vectors[j]
            dim_large = res.dim
            tok_acc[model_large] = tok_acc.get(model_large, 0) + res.tokens
            cost_acc[model_large] = cost_acc.get(model_large, 0.0) + (
                res.tokens / 1_000_000
            ) * OPENAI_PRICING_PER_1M_TOKENS.get(model_large, 0.0)
        elif dry_run and needs_large:
            tokens = approx_token_count([texts[i] for i in needs_large])
            tok_acc[model_large] = tok_acc.get(model_large, 0) + tokens
            cost_acc[model_large] = cost_acc.get(model_large, 0.0) + (
                tokens / 1_000_000
            ) * OPENAI_PRICING_PER_1M_TOKENS.get(model_large, 0.0)

        # --- Persistência (idempotente) ---
        updated = 0
        for i, ve in enumerate(existing_rows):
            update_fields = []
            # sempre mantém provider e text_hash em sincronia
            if ve.provider != provider:
                ve.provider = provider
                update_fields.append("provider")
            if ve.text_hash != hashes[i]:
                ve.text_hash = hashes[i]
                update_fields.append("text_hash")

            # small
            if not large_only:
                if ve.model_name_small != model_small:
                    ve.model_name_small = model_small
                    update_fields.append("model_name_small")
                if ve.dim_small != dim_small:
                    ve.dim_small = dim_small
                    update_fields.append("dim_small")
                # grava embedding se foi recém computado
                if not dry_run and vec_small:
                    new_vec = vec_small[i]
                    if new_vec is not None:
                        ve.embedding_small = new_vec
                        update_fields.append("embedding_small")

            # large
            if not small_only:
                if ve.model_name_large != model_large:
                    ve.model_name_large = model_large
                    update_fields.append("model_name_large")
                if ve.dim_large != dim_large:
                    ve.dim_large = dim_large
                    update_fields.append("dim_large")
                if not dry_run and vec_large:
                    new_vec = vec_large[i]
                    if new_vec is not None:
                        ve.embedding_large = new_vec
                        update_fields.append("embedding_large")

            if update_fields:
                ve.save(update_fields=sorted(set(update_fields)))
                updated += 1

        self.stdout.write(
            self.style.NOTICE(
                f"[batch] version={version_code} size={len(verses)} updated={updated} "
                f"need_small={len(needs_small)} need_large={len(needs_large)}"
            )
        )
        return len(verses)
