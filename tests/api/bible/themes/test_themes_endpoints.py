"""
API tests for themes endpoints (enriched theme model).

Tests cover:
- Authentication (§5): all endpoints require API key
- List endpoint: default (product) and ?detail=full (research)
- Detail endpoint: verses returned, both modes
- Search endpoint: Portuguese/English, limit, missing query
- Response structure (§4): contract compliance for both modes
- Verse linking: themes return their linked verses correctly
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import (
    APIKey,
    CanonicalBook,
    Language,
    Testament,
    Verse,
    Version,
)
from bible.themes.models import Theme, ThemeVerseLink


class ThemesEnrichedApiTest(TestCase):
    """Tests for enriched themes endpoints with ?detail=full param."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="themes_user")
        self.api_key = APIKey.objects.create(name="Themes Key", user=self.user, scopes=["read"])

        # Base data
        self.lang_en = Language.objects.create(name="English", code="en")
        self.lang_pt = Language.objects.create(name="Portuguese", code="pt-BR")
        self.testament_old = Testament.objects.create(name="OLD", description="Old Testament")
        self.testament_new = Testament.objects.create(name="NEW", description="New Testament")

        self.book_gen = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.testament_old, chapter_count=50
        )
        self.book_heb = CanonicalBook.objects.create(
            osis_code="Heb", canonical_order=58, testament=self.testament_new, chapter_count=13
        )

        self.version = Version.objects.create(language=self.lang_pt, code="PT_NAA", name="NAA")

        # Verses
        self.v_gen_1_1 = Verse.objects.create(
            book=self.book_gen, version=self.version, chapter=1, number=1,
            text="No princípio, Deus criou os céus e a terra.",
        )
        self.v_gen_1_27 = Verse.objects.create(
            book=self.book_gen, version=self.version, chapter=1, number=27,
            text="Criou Deus o homem à sua imagem; à imagem de Deus o criou; homem e mulher os criou.",
        )
        self.v_heb_11_1 = Verse.objects.create(
            book=self.book_heb, version=self.version, chapter=11, number=1,
            text="Ora, a fé é a certeza daquilo que esperamos e a prova das coisas que não vemos.",
        )
        self.v_heb_11_6 = Verse.objects.create(
            book=self.book_heb, version=self.version, chapter=11, number=6,
            text="Sem fé é impossível agradar a Deus.",
        )

        # Enriched themes
        self.theme_faith = Theme.objects.create(
            slug="importancia-da-fe",
            name_pt="A importância da fé",
            name_en="the importance of faith",
            label_normalized="importancia-da-fe",
            evidence_score=0.947,
            verse_count=2,
            status="approved",
        )
        self.theme_creation = Theme.objects.create(
            slug="criacao",
            name_pt="Criação",
            name_en="creation",
            label_normalized="criacao",
            evidence_score=0.950,
            verse_count=2,
            status="approved",
        )

        # Verse links with grades
        ThemeVerseLink.objects.create(
            theme=self.theme_faith, verse=self.v_heb_11_1,
            grade=3, relevance_score=1.0, is_primary_theme=True, source="imported",
        )
        ThemeVerseLink.objects.create(
            theme=self.theme_faith, verse=self.v_heb_11_6,
            grade=2, relevance_score=0.67, is_primary_theme=False, source="imported",
        )
        ThemeVerseLink.objects.create(
            theme=self.theme_creation, verse=self.v_gen_1_1,
            grade=3, relevance_score=1.0, is_primary_theme=True, source="imported",
        )
        ThemeVerseLink.objects.create(
            theme=self.theme_creation, verse=self.v_gen_1_27,
            grade=2, relevance_score=0.67, is_primary_theme=False, source="imported",
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    # ─── Authentication ───────────────────────────────────────

    def test_unauthenticated_request_returns_401(self):
        endpoints = [
            "/api/v1/bible/themes/",
            f"/api/v1/bible/themes/{self.theme_faith.id}/detail/",
            "/api/v1/bible/themes/search/?q=fé",
        ]
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                f"{endpoint} should require auth",
            )

    # ─── List Endpoint ────────────────────────────────────────

    def test_list_returns_200_with_themes(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["pagination"]["count"], 2)

    def test_list_product_mode_has_clean_fields(self):
        """Default mode returns only product-relevant fields."""
        self._auth()
        response = self.client.get("/api/v1/bible/themes/")
        theme = response.json()["results"][0]

        # Must have
        for field in ("id", "slug", "name", "name_en", "verse_count"):
            self.assertIn(field, theme, f"Missing field: {field}")

        # Must NOT have research fields
        for field in ("evidence_score", "grade_distribution", "priority", "status"):
            self.assertNotIn(field, theme, f"Should not have research field: {field}")

    def test_list_full_mode_has_research_fields(self):
        """?detail=full returns research metadata."""
        self._auth()
        response = self.client.get("/api/v1/bible/themes/?detail=full")
        theme = response.json()["results"][0]

        for field in ("evidence_score", "grade_distribution", "priority", "status"):
            self.assertIn(field, theme, f"Missing research field: {field}")

        # Check grade_distribution structure
        gd = theme["grade_distribution"]
        self.assertIn("grade_3", gd)
        self.assertIn("grade_2", gd)
        self.assertIn("grade_1", gd)

    def test_list_ordered_by_evidence_score_desc(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/?detail=full")
        results = response.json()["results"]
        scores = [r["evidence_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    # ─── Detail Endpoint ──────────────────────────────────────

    def test_detail_returns_theme_with_verses(self):
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["slug"], "importancia-da-fe")
        self.assertEqual(data["name"], "A importância da fé")
        self.assertIn("verses", data)
        self.assertEqual(len(data["verses"]), 2)

    def test_detail_verses_product_mode_is_clean(self):
        """Product mode verses have only ref, book, chapter, verse, text."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/")
        verse = response.json()["verses"][0]

        for field in ("ref", "book", "chapter", "verse", "text"):
            self.assertIn(field, verse, f"Missing verse field: {field}")

        for field in ("grade", "relevance_score", "is_primary_theme", "source"):
            self.assertNotIn(field, verse, f"Should not have research field: {field}")

    def test_detail_verses_full_mode_has_grades(self):
        """Full mode includes grade, relevance_score, source per verse."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/?detail=full")
        data = response.json()
        verse = data["verses"][0]

        for field in ("grade", "relevance_score", "is_primary_theme", "source"):
            self.assertIn(field, verse, f"Missing research field: {field}")

        # Check grade_distribution on theme level
        self.assertIn("grade_distribution", data)
        self.assertEqual(data["evidence_score"], 0.947)

    def test_detail_verse_ref_format(self):
        """Verse ref should be OSIS format: Book.Chapter.Verse."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/")
        verse = response.json()["verses"][0]
        ref = verse["ref"]
        parts = ref.split(".")
        self.assertEqual(len(parts), 3, f"Ref should be Book.Ch.Vs, got: {ref}")

    def test_detail_not_found_returns_404(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/99999/detail/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_includes_anchor_verses(self):
        """Themes with anchor_verses should return them."""
        self.theme_faith.anchor_verses = ["HEB.11.1", "HEB.11.6"]
        self.theme_faith.save()

        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/")
        data = response.json()
        self.assertEqual(data["anchor_verses"], ["HEB.11.1", "HEB.11.6"])

    # ─── Search Endpoint ──────────────────────────────────────

    def test_search_by_portuguese_name(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/?q=fé")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertGreater(len(results), 0)
        names = [r["name"] for r in results]
        self.assertTrue(any("fé" in n.lower() for n in names))

    def test_search_by_english_name(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/?q=creation")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertGreater(len(results), 0)

    def test_search_with_limit(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/?q=a&limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.json()), 1)

    def test_search_missing_query_returns_400(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_no_results_returns_empty_list(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/?q=xyznonexistent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_search_full_mode_has_research_fields(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/search/?q=fé&detail=full")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if response.json():
            theme = response.json()[0]
            self.assertIn("evidence_score", theme)
            self.assertIn("grade_distribution", theme)

    # ─── Response Structure Contract ──────────────────────────

    def test_list_response_pagination_structure(self):
        """List endpoint wraps results in standard pagination."""
        self._auth()
        response = self.client.get("/api/v1/bible/themes/")
        data = response.json()
        for field in ("count", "num_pages", "current_page", "page_size", "next", "previous"):
            self.assertIn(field, data["pagination"], f"Missing pagination field: {field}")

    def test_response_content_type_is_json(self):
        self._auth()
        response = self.client.get("/api/v1/bible/themes/")
        self.assertEqual(response["Content-Type"], "application/json")

    # ─── Verse Linking ────────────────────────────────────────

    def test_theme_returns_correct_verse_count(self):
        """verse_count field matches actual linked verses."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/")
        data = response.json()
        self.assertEqual(data["verse_count"], len(data["verses"]))

    def test_verses_contain_text(self):
        """Every verse in the response must have non-empty text."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_creation.id}/detail/")
        for verse in response.json()["verses"]:
            self.assertTrue(len(verse["text"]) > 0, f"Verse {verse['ref']} has empty text")

    def test_grade_3_verses_are_primary_in_full_mode(self):
        """Grade 3 verses should have is_primary_theme=True."""
        self._auth()
        response = self.client.get(f"/api/v1/bible/themes/{self.theme_faith.id}/detail/?detail=full")
        for verse in response.json()["verses"]:
            if verse["grade"] == 3:
                self.assertTrue(verse["is_primary_theme"], f"Grade 3 verse {verse['ref']} should be primary")
