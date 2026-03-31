"""
API tests for Biblical Symbols domain.

Tests cover:
- Authentication: all endpoints require API key
- Symbol: list, detail by canonical_id, search, namespaces, by-context
- By-verse: returns empty list (occurrences not populated)
- Filters: namespace, search, ordering
- Response structure: nested meanings
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, CanonicalBook, Language, Testament
from bible.symbols.models import BiblicalSymbol, SymbolMeaning, SymbolNamespace, SymbolStatus


class SymbolTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="symbol_user")
        self.api_key = APIKey.objects.create(name="Symbol Key", user=self.user, scopes=["read"])

        self.lang = Language.objects.create(name="English", code="en")
        self.ot = Testament.objects.create(name="OLD", description="Old Testament")
        self.book_gen = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=self.ot, chapter_count=50)

        # Symbols
        self.water = BiblicalSymbol.objects.create(
            canonical_id="NAT:agua", namespace=SymbolNamespace.NATURAL,
            primary_name="Água", primary_name_pt="Água",
            literal_meaning="H2O", aliases=["water", "chuva"],
            priority=90, boost=3.5, status=SymbolStatus.APPROVED,
        )
        self.fire = BiblicalSymbol.objects.create(
            canonical_id="NAT:fogo", namespace=SymbolNamespace.NATURAL,
            primary_name="Fogo", primary_name_pt="Fogo",
            literal_meaning="Combustão", aliases=["fire", "chama"],
            priority=80, boost=3.0, status=SymbolStatus.APPROVED,
        )
        self.crown = BiblicalSymbol.objects.create(
            canonical_id="OBJ:coroa", namespace=SymbolNamespace.OBJECT,
            primary_name="Coroa", primary_name_pt="Coroa",
            literal_meaning="Adorno para a cabeça", aliases=["crown"],
            priority=70, boost=2.5, status=SymbolStatus.APPROVED,
        )

        # Meanings
        self.meaning_purification = SymbolMeaning.objects.create(
            symbol=self.water, meaning="Purification", meaning_pt="Purificação",
            theological_context="salvific", valence="positive",
            is_primary_meaning=True, frequency=10,
        )
        self.meaning_judgment = SymbolMeaning.objects.create(
            symbol=self.water, meaning="Judgment", meaning_pt="Juízo",
            theological_context="judgment", valence="negative",
            is_primary_meaning=False, frequency=5,
        )
        self.meaning_fire = SymbolMeaning.objects.create(
            symbol=self.fire, meaning="Divine Presence", meaning_pt="Presença Divina",
            theological_context="christological", valence="positive",
            is_primary_meaning=True, frequency=8,
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class SymbolListEndpointTest(SymbolTestBase):

    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get("/api/v1/bible/symbols/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_symbols(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 3)

    def test_list_compact_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/")
        sym = resp.json()["results"][0]
        for field in ("canonical_id", "namespace", "primary_name", "literal_meaning", "priority"):
            self.assertIn(field, sym)

    def test_list_has_meaning_count(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/")
        results = resp.json()["results"]
        water = next(r for r in results if r["canonical_id"] == "NAT:agua")
        self.assertEqual(water["meaning_count"], 2)

    def test_list_has_primary_meaning(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/")
        results = resp.json()["results"]
        water = next(r for r in results if r["canonical_id"] == "NAT:agua")
        self.assertEqual(water["primary_meaning"], "Purification")

    def test_filter_by_namespace(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/?namespace=NATURAL")
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    def test_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/?page_size=2")
        self.assertEqual(len(resp.json()["results"]), 2)


class SymbolDetailEndpointTest(SymbolTestBase):

    def test_detail_by_canonical_id(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/NAT:agua/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["canonical_id"], "NAT:agua")
        self.assertEqual(data["primary_name"], "Água")

    def test_detail_has_meanings(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/NAT:agua/")
        meanings = resp.json()["meanings"]
        self.assertEqual(len(meanings), 2)
        meaning_texts = [m["meaning"] for m in meanings]
        self.assertIn("Purification", meaning_texts)
        self.assertIn("Judgment", meaning_texts)

    def test_detail_has_aliases(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/NAT:agua/")
        self.assertIn("water", resp.json()["aliases"])

    def test_detail_has_full_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/NAT:agua/")
        data = resp.json()
        for field in ("meanings", "associated_concepts", "literal_meaning", "aliases"):
            self.assertIn(field, data)

    def test_detail_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/NAT:nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class SymbolSearchEndpointTest(SymbolTestBase):

    def test_search_by_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/search/?q=Fogo")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_search_by_meaning(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/search/?q=Purification")
        self.assertGreater(len(resp.json()), 0)

    def test_search_missing_query(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/search/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/search/?q=xyznonexistent")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_search_with_namespace_filter(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/search/?q=a&namespace=OBJECT")
        for sym in resp.json():
            self.assertEqual(sym["namespace"], "OBJECT")


class SymbolByVerseEndpointTest(SymbolTestBase):

    def test_by_verse_returns_empty(self):
        """SymbolOccurrence not populated — returns empty list."""
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/by-verse/Gen/1/1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_by_verse_invalid_book(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/by-verse/Xyz/1/1/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class SymbolNamespacesEndpointTest(SymbolTestBase):

    def test_namespaces(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/namespaces/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        namespaces = {d["namespace"] for d in data}
        self.assertIn("NATURAL", namespaces)
        self.assertIn("OBJECT", namespaces)
        total = sum(d["count"] for d in data)
        self.assertEqual(total, 3)


class SymbolByContextEndpointTest(SymbolTestBase):

    def test_by_context_christological(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/by-context/christological/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["canonical_id"], "NAT:fogo")

    def test_by_context_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/by-context/eschatological/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_content_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/symbols/")
        self.assertEqual(resp["Content-Type"], "application/json")
