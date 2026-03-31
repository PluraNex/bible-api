"""
API tests for Person hub endpoints.

Tests cover:
- Authentication (§5): all endpoints require API key
- List: pagination, filtering by person_type, search
- Detail: full profile with author_profile and biblical_profile links
- Author integration: person_id and person_slug in author responses
- Response structure (§4): contract compliance
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.commentaries.models import Author, CommentaryEntry, CommentarySource
from bible.models import APIKey, CanonicalBook, Language, Testament
from bible.people.models import Person, PersonType


class PersonTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="people_user")
        self.api_key = APIKey.objects.create(name="People Key", user=self.user, scopes=["read"])

        # Base data for commentary entries
        self.lang_en = Language.objects.create(name="English", code="en")
        self.testament_nt = Testament.objects.create(name="NEW", description="New Testament")
        self.book_rom = CanonicalBook.objects.create(
            osis_code="Rom", canonical_order=45, testament=self.testament_nt, chapter_count=16
        )

        # Persons
        self.person_aug = Person.objects.create(
            canonical_name="Augustine of Hippo",
            slug="augustine-of-hippo",
            person_type=PersonType.AUTHOR,
            birth_year="354",
            death_year="430",
            description="Most influential theologian of Western Christianity.",
            portrait_image="https://example.com/augustine.jpg",
            wikipedia_url="https://en.wikipedia.org/wiki/Augustine_of_Hippo",
        )
        self.person_david = Person.objects.create(
            canonical_name="King David",
            slug="king-david",
            person_type=PersonType.BIBLICAL,
            birth_year="~1040 BC",
            death_year="~970 BC",
            description="Second king of Israel, author of Psalms.",
        )
        self.person_paul = Person.objects.create(
            canonical_name="Paul the Apostle",
            slug="paul-the-apostle",
            person_type=PersonType.MIXED,
            birth_year="~5 AD",
            death_year="~67 AD",
            description="Apostle and major NT author.",
        )

        # Author linked to person_aug
        self.author_aug = Author.objects.create(
            name="Augustine of Hippo",
            short_name="Augustine",
            author_type="church_father",
            tradition="Western Catholic",
            primary_hermeneutic="mixed_alexandrian",
            orthodoxy_status="orthodox",
            is_doctor_of_church=True,
            person=self.person_aug,
        )

        # Source + entry for testing cross-domain
        self.source = CommentarySource.objects.create(
            name="Catena Bible", short_code="CATENA", source_type="catena", is_active=True,
        )
        self.entry = CommentaryEntry.objects.create(
            source=self.source, author=self.author_aug, book=self.book_rom,
            chapter=12, verse_start=1, verse_end=1,
            body_text="If the body is a sacrifice when used correctly...",
            original_language="en", word_count=30, is_complete=True,
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class PersonListTest(PersonTestBase):
    """Tests for GET /people/"""

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v1/bible/people/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_all_persons(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 3)

    def test_list_compact_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/")
        person = resp.json()["results"][0]
        for field in ("id", "canonical_name", "slug", "person_type", "portrait_image", "has_author_profile", "has_biblical_profile"):
            self.assertIn(field, person, f"Missing field: {field}")
        # Should NOT have detail-only fields
        for field in ("birth_year", "death_year", "description", "author_profile", "biblical_profile"):
            self.assertNotIn(field, person, f"List should not have: {field}")

    def test_filter_by_person_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?person_type=author")
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["canonical_name"], "Augustine of Hippo")

    def test_filter_biblical(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?person_type=biblical")
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["canonical_name"], "King David")

    def test_filter_mixed(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?person_type=mixed")
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_search_by_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?search=Augustine")
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_search_by_description(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?search=Psalms")
        self.assertEqual(resp.json()["pagination"]["count"], 1)
        self.assertEqual(resp.json()["results"][0]["canonical_name"], "King David")

    def test_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/?page_size=2")
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["pagination"]["next"])


class PersonDetailTest(PersonTestBase):
    """Tests for GET /people/<slug>/"""

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v1/bible/people/augustine-of-hippo/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_by_slug(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/augustine-of-hippo/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["canonical_name"], "Augustine of Hippo")
        self.assertEqual(data["birth_year"], "354")
        self.assertEqual(data["death_year"], "430")
        self.assertIn("description", data)

    def test_detail_includes_author_profile(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/augustine-of-hippo/")
        data = resp.json()
        self.assertTrue(data["has_author_profile"])
        self.assertIsNotNone(data["author_profile"])
        ap = data["author_profile"]
        self.assertEqual(ap["author_type"], "church_father")
        self.assertEqual(ap["tradition"], "Western Catholic")
        self.assertEqual(ap["primary_hermeneutic"], "mixed_alexandrian")
        self.assertTrue(ap["is_doctor_of_church"])
        self.assertIn("entry_count", ap)

    def test_detail_biblical_no_author_profile(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/king-david/")
        data = resp.json()
        self.assertFalse(data["has_author_profile"])
        self.assertIsNone(data["author_profile"])
        self.assertEqual(data["person_type"], "biblical")

    def test_detail_mixed_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/paul-the-apostle/")
        data = resp.json()
        self.assertEqual(data["person_type"], "mixed")

    def test_detail_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/nonexistent-person/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_has_portrait_and_wikipedia(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/augustine-of-hippo/")
        data = resp.json()
        self.assertIn("portrait_image", data)
        self.assertIn("wikipedia_url", data)
        self.assertTrue(data["portrait_image"].startswith("https://"))
        self.assertTrue(data["wikipedia_url"].startswith("https://"))


class AuthorPersonIntegrationTest(PersonTestBase):
    """Tests that Author endpoints include person_id and person_slug."""

    def test_author_list_has_person_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/comments/authors/")
        author = resp.json()["results"][0]
        self.assertIn("person_id", author)
        self.assertIn("person_slug", author)
        self.assertEqual(author["person_id"], self.person_aug.id)
        self.assertEqual(author["person_slug"], "augustine-of-hippo")

    def test_commentary_entry_author_has_person(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/comments/entries/{self.entry.id}/")
        author = resp.json()["author"]
        self.assertIn("person_id", author)
        self.assertIn("person_slug", author)

    def test_response_content_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/people/")
        self.assertEqual(resp["Content-Type"], "application/json")
