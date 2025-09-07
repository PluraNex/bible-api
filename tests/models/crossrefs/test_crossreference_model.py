"""
Tests for CrossReference model.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import Book, CrossReference, Verse, Version


class CrossReferenceModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(name="Genesis", abbreviation="Gen", order=1, testament="OLD", chapter_count=50)
        self.version = Version.objects.create(name="King James Version", abbreviation="KJV", language="en")
        self.v1 = Verse.objects.create(
            book=self.book, version=self.version, chapter=1, number=1, text="In the beginning..."
        )
        self.v2 = Verse.objects.create(
            book=self.book, version=self.version, chapter=1, number=2, text="And the earth..."
        )

    def test_crossref_creation(self):
        cr = CrossReference.objects.create(
            from_verse=self.v1, to_verse=self.v2, relationship_type="parallel", source="manual"
        )
        self.assertIn("->", str(cr))
        self.assertEqual(cr.relationship_type, "parallel")

    def test_crossref_unique_from_to_source(self):
        CrossReference.objects.create(from_verse=self.v1, to_verse=self.v2, relationship_type="other", source="manual")
        with self.assertRaises(IntegrityError):
            CrossReference.objects.create(
                from_verse=self.v1, to_verse=self.v2, relationship_type="parallel", source="manual"
            )

    def test_crossref_no_self_reference(self):
        with self.assertRaises(IntegrityError):
            CrossReference.objects.create(
                from_verse=self.v1, to_verse=self.v1, relationship_type="other", source="manual"
            )
