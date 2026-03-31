"""
API tests for commentary endpoints: Authors, Sources, Entries.

Tests cover:
- Authentication (§5): all endpoints require API key
- Author endpoints: list, detail, filters (type, tradition, hermeneutic, orthodoxy, doctor), search, entries action
- Source endpoints: list, detail
- Entry endpoints: list, detail, filters (book, chapter, verse, author, source), search, ordering, pagination
- Response structure (§4): contract compliance for all endpoints
- Nested serialization: author/source/book in entry responses
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.commentaries.models import Author, CommentaryEntry, CommentarySource
from bible.models import (
    APIKey,
    CanonicalBook,
    Language,
    Testament,
)


class CommentaryTestBase(TestCase):
    """Shared setUp for all commentary tests."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="comments_user")
        self.api_key = APIKey.objects.create(name="Comments Key", user=self.user, scopes=["read"])

        # Base data
        self.lang_en = Language.objects.create(name="English", code="en")
        self.testament_ot = Testament.objects.create(name="OLD", description="Old Testament")
        self.testament_nt = Testament.objects.create(name="NEW", description="New Testament")

        self.book_rom = CanonicalBook.objects.create(
            osis_code="Rom", canonical_order=45, testament=self.testament_nt, chapter_count=16
        )
        self.book_eph = CanonicalBook.objects.create(
            osis_code="Eph", canonical_order=49, testament=self.testament_nt, chapter_count=6
        )
        self.book_gen = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.testament_ot, chapter_count=50
        )

        # Source
        self.catena = CommentarySource.objects.create(
            name="Catena Bible Commentary",
            short_code="CATENA",
            source_type="catena",
            description="Church Fathers commentaries",
            is_active=True,
            is_featured=True,
            entry_count=0,
        )

        # Authors with rich theological data
        self.chrysostom = Author.objects.create(
            name="John Chrysostom",
            short_name="Chrysostom",
            author_type="church_father",
            birth_year=347,
            death_year=407,
            birthplace="Antioch, Syria",
            death_location="Comana, Pontus",
            tradition="Eastern Orthodox / Catholic",
            theological_school="Antiochene",
            era="nicene",
            primary_hermeneutic="mixed_antiochene",
            orthodoxy_status="orthodox",
            recognized_by=["catholic", "orthodox", "anglican"],
            councils=[],
            is_saint=True,
            is_doctor_of_church=True,
            major_works=["Homilies on Matthew", "Homilies on Romans"],
            biography_summary="Greatest preacher of the early Church.",
            theological_contributions="Established homiletical exegesis applying Antiochene literal-historical interpretation.",
            portrait_image="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Johnchrysostom.jpg/200px-Johnchrysostom.jpg",
            wikipedia_url="https://en.wikipedia.org/wiki/John_Chrysostom",
        )
        self.augustine = Author.objects.create(
            name="Augustine of Hippo",
            short_name="Augustine",
            author_type="church_father",
            birth_year=354,
            death_year=430,
            birthplace="Thagaste, Numidia",
            tradition="Western Catholic",
            theological_school="Western/Latin",
            era="nicene",
            primary_hermeneutic="mixed_alexandrian",
            orthodoxy_status="orthodox",
            recognized_by=["catholic", "orthodox", "protestant", "anglican"],
            is_saint=True,
            is_doctor_of_church=True,
            biography_summary="Most influential theologian of Western Christianity.",
            portrait_image="https://upload.wikimedia.org/example/augustine.jpg",
        )
        self.tertullian = Author.objects.create(
            name="Tertullian",
            short_name="Tertullian",
            author_type="church_father",
            birth_year=155,
            death_year=220,
            tradition="Western (later Montanist)",
            era="ante_nicene",
            primary_hermeneutic="literal_historical",
            orthodoxy_status="controversial",
            recognized_by=[],
            is_saint=False,
            is_doctor_of_church=False,
            biography_summary="Father of Latin Christianity, later joined Montanist movement.",
        )
        self.aquinas = Author.objects.create(
            name="Thomas Aquinas",
            short_name="Aquinas",
            author_type="medieval",
            birth_year=1225,
            death_year=1274,
            tradition="Roman Catholic (Dominican)",
            era="medieval",
            primary_hermeneutic="scholastic",
            orthodoxy_status="orthodox",
            recognized_by=["catholic", "anglican"],
            is_saint=True,
            is_doctor_of_church=True,
        )

        # Commentary entries
        self.entry1 = CommentaryEntry.objects.create(
            source=self.catena, author=self.chrysostom, book=self.book_rom,
            chapter=12, verse_start=1, verse_end=1,
            original_reference="ROM 12:1",
            body_text="Here he goes on to alarm them also by the figure he uses...",
            original_language="en", word_count=45, is_complete=True, confidence_score=0.9,
        )
        self.entry2 = CommentaryEntry.objects.create(
            source=self.catena, author=self.augustine, book=self.book_rom,
            chapter=12, verse_start=1, verse_end=1,
            original_reference="ROM 12:1",
            body_text="If the body, which is less than the soul, is a sacrifice when used correctly...",
            original_language="en", word_count=52, is_complete=True, confidence_score=0.9,
        )
        self.entry3 = CommentaryEntry.objects.create(
            source=self.catena, author=self.chrysostom, book=self.book_eph,
            chapter=6, verse_start=12, verse_end=12,
            original_reference="EPH 6:12",
            body_text="For we wrestle not against flesh and blood, but against principalities...",
            original_language="en", word_count=38, is_complete=True, confidence_score=0.9,
        )
        self.entry4 = CommentaryEntry.objects.create(
            source=self.catena, author=self.augustine, book=self.book_gen,
            chapter=3, verse_start=15, verse_end=15,
            original_reference="GEN 3:15",
            body_text="The seed of the woman shall crush the head of the serpent...",
            original_language="en", word_count=30, is_complete=True, confidence_score=0.85,
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


# ─── Author Tests ─────────────────────────────────────────────

class AuthorEndpointsTest(CommentaryTestBase):
    """Tests for /comments/authors/ endpoints."""

    # Authentication
    def test_unauthenticated_returns_401(self):
        endpoints = [
            "/api/v1/bible/comments/authors/",
            f"/api/v1/bible/comments/authors/{self.chrysostom.id}/",
        ]
        for ep in endpoints:
            self.assertEqual(self.client.get(ep).status_code, status.HTTP_401_UNAUTHORIZED, ep)

    # List
    def test_list_returns_all_authors(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 4)

    def test_list_response_has_compact_fields(self):
        """List should return compact fields: id, name, short_name, author_type, tradition, portrait_image."""
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/")
        author = resp.json()["results"][0]
        for field in ("id", "name", "short_name", "author_type", "tradition", "portrait_image"):
            self.assertIn(field, author, f"Missing field: {field}")
        # Should NOT have detail-only fields
        for field in ("biography_summary", "theological_contributions", "recognized_by", "entry_count"):
            self.assertNotIn(field, author, f"List should not have: {field}")

    # Detail
    def test_detail_returns_full_profile(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/authors/{self.chrysostom.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        self.assertEqual(data["name"], "John Chrysostom")
        self.assertEqual(data["lifespan"], "347-407")
        self.assertEqual(data["primary_hermeneutic"], "mixed_antiochene")
        self.assertEqual(data["orthodoxy_status"], "orthodox")
        self.assertIn("catholic", data["recognized_by"])
        self.assertIn("orthodox", data["recognized_by"])
        self.assertTrue(data["is_doctor_of_church"])
        self.assertTrue(data["is_saint"])
        self.assertIn("Homilies on Matthew", data["major_works"])
        self.assertIn("portrait_image", data)
        self.assertIn("wikipedia_url", data)
        self.assertIn("entry_count", data)
        self.assertEqual(data["entry_count"], 2)

    def test_detail_not_found_returns_404(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # Filters
    def test_filter_by_author_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?author_type=church_father")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["pagination"]["count"], 3)  # Chrysostom, Augustine, Tertullian
        for a in data["results"]:
            self.assertEqual(a["author_type"], "church_father")

    def test_filter_by_tradition(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?tradition=Western+Catholic")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for a in resp.json()["results"]:
            self.assertEqual(a["tradition"], "Western Catholic")

    def test_filter_by_hermeneutic(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?primary_hermeneutic=scholastic")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "Thomas Aquinas")

    def test_filter_by_orthodoxy_status(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?orthodoxy_status=controversial")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "Tertullian")

    def test_filter_by_doctor_of_church(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?is_doctor_of_church=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [a["name"] for a in resp.json()["results"]]
        self.assertIn("John Chrysostom", names)
        self.assertIn("Augustine of Hippo", names)
        self.assertIn("Thomas Aquinas", names)
        self.assertNotIn("Tertullian", names)

    def test_filter_by_era(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?era=nicene")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 2)  # Chrysostom, Augustine

    def test_filter_by_is_saint(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?is_saint=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 3)  # Not Tertullian

    # Search
    def test_search_by_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?search=Chrysostom")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_search_by_biography(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/?search=Montanist")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "Tertullian")

    # Entries action
    def test_author_entries_action(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/authors/{self.chrysostom.id}/entries/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), 2)
        for entry in data:
            self.assertEqual(entry["author"]["name"], "John Chrysostom")

    # Response structure
    def test_list_has_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/")
        data = resp.json()
        for field in ("count", "num_pages", "current_page", "page_size"):
            self.assertIn(field, data["pagination"])

    def test_response_content_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/")
        self.assertEqual(resp["Content-Type"], "application/json")


# ─── Source Tests ─────────────────────────────────────────────

class SourceEndpointsTest(CommentaryTestBase):
    """Tests for /comments/sources/ endpoints."""

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v1/bible/comments/sources/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_sources(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/sources/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["pagination"]["count"], 1)
        source = data["results"][0]
        self.assertEqual(source["short_code"], "CATENA")
        self.assertTrue(source["is_featured"])

    def test_source_detail(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/sources/{self.catena.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["name"], "Catena Bible Commentary")
        self.assertIn("entry_count", data)

    def test_source_response_fields(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/sources/{self.catena.id}/")
        data = resp.json()
        for field in ("id", "name", "short_code", "source_type", "description", "is_featured", "entry_count"):
            self.assertIn(field, data, f"Missing field: {field}")


# ─── Entry Tests ──────────────────────────────────────────────

class EntryEndpointsTest(CommentaryTestBase):
    """Tests for /comments/entries/ endpoints."""

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v1/bible/comments/entries/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_all_entries(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 4)

    # Filters
    def test_filter_by_book(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?book__osis_code=Rom")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["pagination"]["count"], 2)
        for r in data["results"]:
            self.assertEqual(r["book"]["osis_code"], "Rom")

    def test_filter_by_chapter(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?book__osis_code=Rom&chapter=12")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    def test_filter_by_verse(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?book__osis_code=Eph&chapter=6&verse=12")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertIn("principalities", resp.json()["results"][0]["body_text"])

    def test_filter_by_author_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?author__name=Augustine+of+Hippo")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    def test_filter_by_source(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?source__short_code=CATENA")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 4)

    def test_combined_filters(self):
        self._auth()
        resp = self.client.get(
            "/api/v1/bible/comments/entries/?book__osis_code=Rom&chapter=12&author__name=John+Chrysostom"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    # Search
    def test_search_in_body_text(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?search=sacrifice")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.json()["pagination"]["count"], 1)

    def test_search_by_author_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?search=Chrysostom")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    # Detail
    def test_entry_detail(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["chapter"], 12)
        self.assertEqual(data["verse_start"], 1)
        self.assertIn("body_text", data)

    def test_entry_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # Nested serialization
    def test_entry_has_nested_author(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry1.id}/")
        author = resp.json()["author"]
        self.assertEqual(author["name"], "John Chrysostom")
        self.assertEqual(author["author_type"], "church_father")
        self.assertIn("portrait_image", author)

    def test_entry_has_nested_source(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry1.id}/")
        source = resp.json()["source"]
        self.assertEqual(source["short_code"], "CATENA")

    def test_entry_has_nested_book(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry1.id}/")
        book = resp.json()["book"]
        self.assertEqual(book["osis_code"], "Rom")

    # Ordering
    def test_default_ordering_by_book_chapter_verse(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/")
        results = resp.json()["results"]
        # Gen (order 1) should come before Eph (49) and Rom (45)
        books = [r["book"]["osis_code"] for r in results]
        gen_idx = books.index("Gen")
        rom_idx = books.index("Rom")
        self.assertLess(gen_idx, rom_idx)

    # Pagination
    def test_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/?page_size=2")
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["pagination"]["next"])

    # Response structure
    def test_entry_response_fields(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry1.id}/")
        data = resp.json()
        required = [
            "id", "source", "author", "book", "chapter", "verse_start", "verse_end",
            "body_text", "original_language", "word_count", "is_complete",
            "confidence_score", "created_at",
        ]
        for field in required:
            self.assertIn(field, data, f"Missing field: {field}")

    def test_content_type_is_json(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/entries/")
        self.assertEqual(resp["Content-Type"], "application/json")
