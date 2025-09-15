"""
Performance tests for Bible API.
Tests query efficiency, response times, and scalability.
"""
import time

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from bible.models import APIKey, BookName, CanonicalBook, Language, Testament, Theme, Verse, VerseTheme, Version


class APIPerformanceTest(TestCase):
    """Test API performance and query efficiency."""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all performance tests."""
        super().setUpClass()

        # Create user and API key
        cls.user = User.objects.create_user(username="perf_user")
        cls.api_key = APIKey.objects.create(name="Performance Key", user=cls.user, scopes=["read"])

        # Create languages
        cls.english = Language.objects.create(code="en", name="English")

        # Create testaments
        cls.old_testament = Testament.objects.create(name="Old Testament")
        cls.new_testament = Testament.objects.create(name="New Testament")

        # Create multiple books for performance testing
        cls.books = []
        book_names = ["Genesis", "Exodus", "Matthew", "Mark", "Luke", "John"]

        for i, name in enumerate(book_names):
            testament = cls.old_testament if i < 2 else cls.new_testament
            canonical_book = CanonicalBook.objects.create(
                osis_code=name[:3], canonical_order=i + 1, testament=testament, chapter_count=50 if i < 2 else 28
            )

            BookName.objects.create(
                canonical_book=canonical_book, language=cls.english, name=name, abbreviation=name[:3]
            )

            cls.books.append(canonical_book)

        # Create version
        cls.version = Version.objects.create(name="Performance Test Version", code="PERF", language=cls.english)

        # Create many verses for performance testing
        cls.verses = []
        for book in cls.books[:2]:  # Just Genesis and Exodus for now
            for chapter in range(1, 6):  # 5 chapters each
                for verse_num in range(1, 21):  # 20 verses each
                    verse = Verse.objects.create(
                        book=book,
                        version=cls.version,
                        chapter=chapter,
                        number=verse_num,
                        text=f"Performance test verse {book.osis_code} {chapter}:{verse_num}",
                    )
                    cls.verses.append(verse)

        # Create themes and associate verses
        cls.themes = []
        theme_names = ["Faith", "Hope", "Love", "Peace", "Joy"]
        for theme_name in theme_names:
            theme = Theme.objects.create(name=theme_name, description=f"Verses about {theme_name.lower()}")
            cls.themes.append(theme)

            # Associate every 10th verse with this theme
            for i, verse in enumerate(cls.verses):
                if i % 10 == 0:
                    VerseTheme.objects.create(verse=verse, theme=theme)

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    def test_book_list_query_efficiency(self):
        """Test that book list endpoint is efficient."""
        with self.assertNumQueries(3):  # Should use minimal queries
            response = self.client.get("/api/v1/bible/books/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertGreater(len(data["results"]), 0)

    def test_verse_by_chapter_query_efficiency(self):
        """Test that verse-by-chapter endpoint avoids N+1 queries."""
        with self.assertNumQueries(4):  # Should be constant regardless of verse count
            response = self.client.get("/api/v1/bible/verses/by-chapter/Genesis/1/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data["results"]), 20)  # 20 verses in chapter 1

    def test_verse_detail_query_efficiency(self):
        """Test that verse detail endpoint is efficient."""
        verse = self.verses[0]

        with self.assertNumQueries(2):  # Should use select_related/prefetch_related
            response = self.client.get(f"/api/v1/bible/verses/{verse.id}/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("text", data)

    def test_theme_verses_query_efficiency(self):
        """Test that theme-verses endpoint handles many verses efficiently."""
        theme = self.themes[0]  # Should have many verses associated

        with self.assertNumQueries(4):  # Should be efficient regardless of verse count
            response = self.client.get(f"/api/v1/bible/verses/by-theme/{theme.id}/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertGreater(len(data["results"]), 0)

    def test_response_time_benchmarks(self):
        """Test that endpoints respond within acceptable time limits."""

        # Book list should be very fast
        start_time = time.time()
        response = self.client.get("/api/v1/bible/books/")
        elapsed = time.time() - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 0.5, "Book list took too long")  # Should be < 500ms

        # Verse chapter should be reasonably fast
        start_time = time.time()
        response = self.client.get("/api/v1/bible/verses/by-chapter/Genesis/1/")
        elapsed = time.time() - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 1.0, "Verse chapter took too long")  # Should be < 1s

        # Individual verse should be very fast
        verse = self.verses[0]
        start_time = time.time()
        response = self.client.get(f"/api/v1/bible/verses/{verse.id}/")
        elapsed = time.time() - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 0.3, "Verse detail took too long")  # Should be < 300ms

    def test_pagination_performance(self):
        """Test that pagination doesn't degrade performance significantly."""

        # Test first page
        start_time = time.time()
        response1 = self.client.get("/api/v1/bible/verses/by-chapter/Genesis/1/?page_size=10")
        elapsed1 = time.time() - start_time
        self.assertEqual(response1.status_code, 200)

        # Test second page
        start_time = time.time()
        response2 = self.client.get("/api/v1/bible/verses/by-chapter/Genesis/1/?page_size=10&page=2")
        elapsed2 = time.time() - start_time
        self.assertEqual(response2.status_code, 200)

        # Performance should be similar across pages
        self.assertAlmostEqual(elapsed1, elapsed2, delta=0.2)  # Within 200ms of each other

    def test_concurrent_request_simulation(self):
        """Test that multiple requests don't cause significant performance degradation."""
        import queue
        import threading

        results = queue.Queue()

        def make_request():
            start_time = time.time()
            response = self.client.get("/api/v1/bible/books/")
            elapsed = time.time() - start_time
            results.put((response.status_code, elapsed))

        # Simulate 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Collect results
        response_times = []
        while not results.empty():
            status_code, elapsed = results.get()
            self.assertEqual(status_code, 200)
            response_times.append(elapsed)

        # All requests should complete within reasonable time
        max_time = max(response_times)
        avg_time = sum(response_times) / len(response_times)

        self.assertLess(max_time, 2.0, "Concurrent requests took too long")
        self.assertLess(avg_time, 1.0, "Average response time too high")


@override_settings(DEBUG=False)  # Disable debug to get realistic performance
class APIScalabilityTest(TestCase):
    """Test API scalability with larger datasets."""

    @classmethod
    def setUpClass(cls):
        """Create larger dataset for scalability testing."""
        super().setUpClass()

        # Create user and API key
        cls.user = User.objects.create_user(username="scale_user")
        cls.api_key = APIKey.objects.create(name="Scale Key", user=cls.user, scopes=["read"])

        # Create test data
        cls.english = Language.objects.create(code="en", name="English")
        cls.testament = Testament.objects.create(name="Test Testament")

        # Create one book with many chapters and verses
        cls.large_book = CanonicalBook.objects.create(
            osis_code="LRG", canonical_order=1, testament=cls.testament, chapter_count=150  # Large book
        )

        BookName.objects.create(
            canonical_book=cls.large_book, language=cls.english, name="Large Book", abbreviation="LRG"
        )

        cls.version = Version.objects.create(name="Scale Test Version", code="SCALE", language=cls.english)

        # Create many verses (simulating a large book like Psalms)
        for chapter in range(1, 21):  # 20 chapters
            for verse_num in range(1, 31):  # 30 verses per chapter = 600 verses total
                Verse.objects.create(
                    book=cls.large_book,
                    version=cls.version,
                    chapter=chapter,
                    number=verse_num,
                    text=f"Scale test verse {chapter}:{verse_num} " + "x" * 100,  # Longer text
                )

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    def test_large_chapter_performance(self):
        """Test performance with large chapters (30 verses)."""
        with self.assertNumQueries(4):  # Should remain constant
            start_time = time.time()
            response = self.client.get("/api/v1/bible/verses/by-chapter/Large Book/1/")
            elapsed = time.time() - start_time

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data["results"]), 30)

            # Should complete within reasonable time even with 30 verses
            self.assertLess(elapsed, 1.5, f"Large chapter took {elapsed:.2f}s")

    def test_memory_usage_with_large_responses(self):
        """Test that large responses don't consume excessive memory."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Make request for large chapter
        response = self.client.get("/api/v1/bible/verses/by-chapter/Large Book/1/")
        self.assertEqual(response.status_code, 200)

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        # Memory increase should be reasonable (less than 50MB for this request)
        self.assertLess(memory_increase, 50, f"Memory usage increased by {memory_increase:.2f}MB")

    def test_pagination_with_large_datasets(self):
        """Test pagination performance with large datasets."""
        # Test that pagination works efficiently even with many pages

        # Get total count first
        response = self.client.get("/api/v1/bible/verses/by-chapter/Large Book/1/?page_size=10")
        self.assertEqual(response.status_code, 200)
        total_count = response.json()["count"]

        # Test a page near the end
        last_page = (total_count // 10) + (1 if total_count % 10 else 0)

        start_time = time.time()
        response = self.client.get(f"/api/v1/bible/verses/by-chapter/Large Book/1/?page_size=10&page={last_page}")
        elapsed = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        # Last page should be as fast as first page
        self.assertLess(elapsed, 1.0, "Last page pagination too slow")
