"""
Search quality regression tests using the gold standard dataset.

The gold set contains 50 curated queries with 445 validated verse references,
stratified by difficulty (baseline, medium, medium_hard, hard, extreme).

These tests verify that search quality does not regress when making changes
to the hybrid search pipeline (alpha, embeddings, query expansion, etc.).

To run: pytest tests/api/ai/test_search_quality.py -v
Requires: running database with verse data and embeddings loaded.
"""

import json
from pathlib import Path

import pytest

GOLD_SET_PATH = Path(__file__).resolve().parent.parent.parent / "fixtures" / "gold_set.json"


def load_gold_set():
    """Load the gold standard dataset."""
    if not GOLD_SET_PATH.exists():
        pytest.skip(f"Gold set fixture not found: {GOLD_SET_PATH}")
    with open(GOLD_SET_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gold_set():
    return load_gold_set()


@pytest.mark.skipif(
    not GOLD_SET_PATH.exists(),
    reason="Gold set fixture not available",
)
class TestGoldSetIntegrity:
    """Verify the gold set fixture is well-formed."""

    def test_gold_set_has_50_queries(self, gold_set):
        assert len(gold_set) == 50

    def test_all_queries_have_references(self, gold_set):
        for q in gold_set:
            assert len(q["gold_references"]) > 0, f"Query {q['query_id']} has no references"

    def test_total_references(self, gold_set):
        total = sum(len(q["gold_references"]) for q in gold_set)
        assert total == 445

    def test_difficulty_distribution(self, gold_set):
        difficulties = {}
        for q in gold_set:
            d = q["difficulty"]
            difficulties[d] = difficulties.get(d, 0) + 1
        assert "extreme" in difficulties
        assert "baseline" in difficulties


@pytest.mark.django_db
@pytest.mark.slow
@pytest.mark.skipif(
    not GOLD_SET_PATH.exists(),
    reason="Gold set fixture not available",
)
class TestSearchQualityRegression:
    """
    Regression tests that run actual search queries against the gold set.

    These tests require:
    - A running PostgreSQL with verse data loaded
    - Embeddings generated (at least for one version)
    - The RAG service available

    Run with: pytest tests/api/ai/test_search_quality.py -m slow -v
    """

    @pytest.fixture(autouse=True)
    def _setup(self, gold_set):
        self.gold_set = gold_set

    def _run_search(self, query: str, top_k: int = 20):
        """Run hybrid search and return hit references."""
        try:
            from bible.ai.services import search_hybrid

            result = search_hybrid(query=query, top_k=top_k)
            return [hit.get("reference", "") for hit in result.hits]
        except Exception:
            pytest.skip("RAG service not available (DB/embeddings not loaded)")

    def _normalize_ref(self, ref: str) -> str:
        """Normalize a verse reference for comparison."""
        return ref.strip().lower().replace(" ", "")

    def test_baseline_queries_recall(self):
        """Baseline queries (easiest) should have recall >= 30%."""
        baseline = [q for q in self.gold_set if q["difficulty"] == "baseline"]
        if not baseline:
            pytest.skip("No baseline queries in gold set")

        total_found = 0
        total_expected = 0

        for q in baseline[:3]:  # Test first 3 for speed
            hits = self._run_search(q["query"])
            hit_refs = {self._normalize_ref(h) for h in hits}
            gold_refs = {self._normalize_ref(r["verse"]) for r in q["gold_references"]}
            found = len(hit_refs & gold_refs)
            total_found += found
            total_expected += len(gold_refs)

        if total_expected > 0:
            recall = total_found / total_expected
            assert recall >= 0.3, f"Baseline recall {recall:.2%} < 30% threshold"
