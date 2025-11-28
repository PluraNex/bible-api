"""
API tests for comments endpoints.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import (
    APIKey,
    Author,
    Book,
    BookName,
    CanonicalBook,
    CommentaryEntry,
    CommentarySource,
    Language,
    License,
    Testament,
    Version,
)


class CommentariesApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="comments_user")
        self.api_key = APIKey.objects.create(name="Comments Key", user=self.user, scopes=["read"])

        # Create languages
        self.english = Language.objects.create(name="English", code="en-US")
        self.portuguese = Language.objects.create(name="Portuguese (Brazil)", code="pt-BR")

        # Create testament and canonical books
        self.new_testament = Testament.objects.create(name="New Testament")

        # Create Acts book
        self.acts_canonical = CanonicalBook.objects.create(
            osis_code="Acts",
            canonical_order=44,
            testament=self.new_testament,
            chapter_count=28,
        )

        # Create John book
        self.john_canonical = CanonicalBook.objects.create(
            osis_code="John",
            canonical_order=43,
            testament=self.new_testament,
            chapter_count=21,
        )

        # Create book names
        BookName.objects.create(
            canonical_book=self.acts_canonical,
            language=self.english,
            name="Acts",
            abbreviation="Acts",
        )
        BookName.objects.create(
            canonical_book=self.john_canonical,
            language=self.english,
            name="John",
            abbreviation="Joh",
        )

        # Create version
        self.version = Version.objects.create(
            name="King James Version", code="EN_KJV", language=self.english
        )

        # Create license
        self.license = License.objects.create(
            code="public-domain", name="Public Domain"
        )

        # Create commentary source
        self.source = CommentarySource.objects.create(
            name="Church Fathers Commentary",
            short_code="CF",
            publication_year=2024,
            author_type="church_father",
            description="Patristic commentaries",
            language=self.english,
            license=self.license,
            is_featured=True,
        )

        # Create authors
        self.author1 = Author.objects.create(
            name="John Chrysostom",
            author_type="church_father",
            period="347-407 AD",
            century="4th",
            tradition="Eastern Orthodox",
        )
        self.author2 = Author.objects.create(
            name="Augustine of Hippo",
            author_type="church_father",
            period="354-430 AD",
            century="4th-5th",
            tradition="Western Christian",
        )

        # Create commentary entries
        self.commentary1 = CommentaryEntry.objects.create(
            source=self.source,
            author=self.author1,
            book=self.acts_canonical,
            chapter=1,
            verse_start=1,
            verse_end=1,
            title="On Acts 1:1",
            body_text="The opening of the Acts of the Apostles... " * 50,  # ~450 words
            original_language="Greek",
            word_count=450,
            is_complete=True,
            confidence_score=0.95,
            ai_summary={"summary": "Commentary on Acts 1:1"},
            theological_analysis={"analysis": "Key theological themes"},
            spiritual_insight={"insight": "Spiritual lessons"},
        )

        self.commentary2 = CommentaryEntry.objects.create(
            source=self.source,
            author=self.author1,
            book=self.acts_canonical,
            chapter=1,
            verse_start=8,
            verse_end=8,
            title="On Acts 1:8",
            body_text="You will receive power... " * 30,  # ~150 words
            original_language="Greek",
            word_count=150,
            is_complete=True,
            confidence_score=0.88,
            ai_summary={"summary": "Commentary on Acts 1:8"},
        )

        self.commentary3 = CommentaryEntry.objects.create(
            source=self.source,
            author=self.author2,
            book=self.john_canonical,
            chapter=1,
            verse_start=1,
            verse_end=1,
            title="On John 1:1",
            body_text="In the beginning was the Word... " * 60,  # ~600 words
            original_language="Greek",
            word_count=600,
            is_complete=True,
            confidence_score=0.92,
        )

    def test_requires_auth(self):
        """Test that comments endpoint requires authentication."""
        resp = self.client.get("/api/v1/bible/comments/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_all_commentaries(self):
        """Test listing all commentaries."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 3)

    def test_filter_by_book(self):
        """Test filtering commentaries by book OSIS code."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?book__osis_code=Acts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        for result in data["results"]:
            self.assertEqual(result["book"]["osis_code"], "Acts")

    def test_filter_by_chapter(self):
        """Test filtering commentaries by chapter."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?book__osis_code=Acts&chapter=1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        for result in data["results"]:
            self.assertEqual(result["chapter"], 1)

    def test_filter_by_author(self):
        """Test filtering commentaries by author name."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?author__name=John+Chrysostom")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        for result in data["results"]:
            self.assertEqual(result["author"]["name"], "John Chrysostom")

    def test_filter_by_source(self):
        """Test filtering commentaries by source short code."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?source__short_code=CF")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 3)

    def test_search_by_title(self):
        """Test searching commentaries by title."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?search=On+John")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreaterEqual(len(data["results"]), 1)
        # Verify that the searched title is in results
        titles = [r["title"] for r in data["results"]]
        self.assertIn("On John 1:1", titles)

    def test_search_by_author_name(self):
        """Test searching commentaries by author name."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?search=Augustine")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["author"]["name"], "Augustine of Hippo")

    def test_ordering_by_book_chapter_verse(self):
        """Test default ordering by book, chapter, verse."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        results = data["results"]

        # John should come before Acts (John has canonical_order=43, Acts=44)
        john_results = [r for r in results if r["book"]["osis_code"] == "John"]
        acts_results = [r for r in results if r["book"]["osis_code"] == "Acts"]

        if john_results and acts_results:
            john_order = results.index(john_results[0])
            acts_order = results.index(acts_results[0])
            self.assertLess(john_order, acts_order)

    def test_nested_serialization(self):
        """Test that nested objects (author, source, book) are properly serialized."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/comments/{self.commentary1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        # Check author
        self.assertIn("author", data)
        self.assertEqual(data["author"]["name"], "John Chrysostom")
        self.assertEqual(data["author"]["author_type"], "church_father")

        # Check source
        self.assertIn("source", data)
        self.assertEqual(data["source"]["short_code"], "CF")
        self.assertEqual(data["source"]["is_featured"], True)

        # Check book
        self.assertIn("book", data)
        self.assertEqual(data["book"]["osis_code"], "Acts")

    def test_enrichment_fields_in_response(self):
        """Test that enrichment fields are included in the response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/comments/{self.commentary1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        # Check enrichment fields
        self.assertIn("ai_summary", data)
        self.assertIn("theological_analysis", data)
        self.assertIn("spiritual_insight", data)
        self.assertIn("word_count", data)
        self.assertIn("confidence_score", data)
        self.assertIn("is_complete", data)
        self.assertIn("original_language", data)

        # Verify values
        self.assertEqual(data["word_count"], 450)
        self.assertEqual(data["confidence_score"], 0.95)
        self.assertEqual(data["is_complete"], True)
        self.assertEqual(data["original_language"], "Greek")

    def test_length_category_property(self):
        """Test the length_category computed property."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Brief (< 100 words)
        resp = self.client.get(f"/api/v1/bible/comments/{self.commentary2.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["length_category"], "medium")  # 150 words

        # Detailed (500-2000 words)
        resp = self.client.get(f"/api/v1/bible/comments/{self.commentary3.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["length_category"], "detailed")  # 600 words

    def test_pagination(self):
        """Test pagination of results."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/comments/?page=1&page_size=2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)

    def test_combined_filters(self):
        """Test combining multiple filters."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(
            "/api/v1/bible/comments/?book__osis_code=Acts&chapter=1&author__name=John+Chrysostom"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data["results"]), 2)
        for result in data["results"]:
            self.assertEqual(result["book"]["osis_code"], "Acts")
            self.assertEqual(result["chapter"], 1)
            self.assertEqual(result["author"]["name"], "John Chrysostom")

    def test_reference_field(self):
        """Test that reference field is properly formatted."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/comments/{self.commentary1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("reference", data)
        self.assertIsNotNone(data["reference"])
