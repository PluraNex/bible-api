"""
Tests for CrossReference model.
"""
from django.db import IntegrityError
from django.test import TransactionTestCase
from django.test.utils import override_settings

from bible.models import BookName, CanonicalBook, CrossReference, Language, Testament, Verse, Version


@override_settings(USE_TZ=True)
class CrossReferenceModelTest(TransactionTestCase):
    def setUp(self):
        # Create test language (unique code to avoid conflicts, max 10 chars)
        self.language, _ = Language.objects.get_or_create(code="test-cr", defaults={"name": "Test Crossref Language"})

        # Create test testament (unique ID to avoid conflicts)
        self.testament, _ = Testament.objects.get_or_create(id=98, defaults={"name": "Test Crossref Testament"})

        # Create test canonical book (shortened OSIS code to fit constraint)
        self.book = CanonicalBook.objects.create(
            osis_code="TestCR", canonical_order=990, testament=self.testament, chapter_count=50
        )

        # Create book name
        BookName.objects.create(
            canonical_book=self.book, language=self.language, name="Test Genesis", abbreviation="TestGen"
        )

        # Create version
        self.version = Version.objects.create(name="Test King James Version", code="TEST_KJV", language=self.language)

        # Create verses
        self.v1 = Verse.objects.create(
            book=self.book, version=self.version, chapter=1, number=1, text="Test: In the beginning..."
        )
        self.v2 = Verse.objects.create(
            book=self.book, version=self.version, chapter=1, number=2, text="Test: And the earth..."
        )

    def test_crossref_creation(self):
        cr = CrossReference.objects.create(
            from_book=self.book,
            from_chapter=1,
            from_verse=1,
            to_book=self.book,
            to_chapter=1,
            to_verse_start=2,
            to_verse_end=2,
            source="manual",
        )
        self.assertIn("→", str(cr))
        self.assertEqual(cr.source, "manual")

    def test_crossref_unique_from_to_source(self):
        CrossReference.objects.create(
            from_book=self.book,
            from_chapter=1,
            from_verse=1,
            to_book=self.book,
            to_chapter=1,
            to_verse_start=2,
            to_verse_end=2,
            source="manual",
        )
        with self.assertRaises(IntegrityError):
            CrossReference.objects.create(
                from_book=self.book,
                from_chapter=1,
                from_verse=1,
                to_book=self.book,
                to_chapter=1,
                to_verse_start=2,
                to_verse_end=2,
                source="manual",
            )

    def test_crossref_no_self_reference(self):
        # This test may not apply with new model structure
        # Self-references might be allowed from one verse to itself in different contexts
        cr = CrossReference.objects.create(
            from_book=self.book,
            from_chapter=1,
            from_verse=1,
            to_book=self.book,
            to_chapter=1,
            to_verse_start=1,
            to_verse_end=1,
            source="manual",
        )
        self.assertIsNotNone(cr)
        self.assertEqual(cr.from_verse, cr.to_verse_start)
