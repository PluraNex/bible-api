"""
Tests for commentary models.
Tests Author, CommentarySource, CommentaryEntry, and VerseComment models.
"""
import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from bible.models import (
    Author,
    CanonicalBook,
    CommentaryEntry,
    CommentarySource,
    Language,
    Testament,
    Verse,
    VerseComment,
    Version,
)


@pytest.mark.models
class AuthorModelTest(TestCase):
    """Test Author model functionality."""

    def test_str_method_with_century(self):
        """Test __str__ method with century info."""
        author = Author.objects.create(name="John Chrysostom", century="4th century AD")
        expected = "John Chrysostom (4th century AD)"
        self.assertEqual(str(author), expected)

    def test_lifespan_with_both_dates(self):
        """Test lifespan property with birth and death years."""
        author = Author.objects.create(name="Augustine", birth_year=354, death_year=430)
        self.assertEqual(author.lifespan, "354-430")

    def test_lifespan_with_birth_only(self):
        """Test lifespan property with birth year only."""
        author = Author.objects.create(name="Jerome", birth_year=347)
        self.assertEqual(author.lifespan, "b. 347")

    def test_lifespan_with_death_only(self):
        """Test lifespan property with death year only."""
        author = Author.objects.create(name="Unknown Author", death_year=400)
        self.assertEqual(author.lifespan, "d. 400")

    def test_lifespan_with_century_fallback(self):
        """Test lifespan property falls back to century."""
        author = Author.objects.create(name="Origen", century="3rd century AD")
        self.assertEqual(author.lifespan, "3rd century AD")

    def test_lifespan_unknown_period(self):
        """Test lifespan property with no date info."""
        author = Author.objects.create(name="Unknown")
        self.assertEqual(author.lifespan, "Unknown period")


@pytest.mark.models
class CommentarySourceModelTest(TestCase):
    """Test CommentarySource model functionality."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.author = Author.objects.create(name="John Chrysostom", century="4th century AD")

    def test_str_method(self):
        """Test __str__ method."""
        source = CommentarySource.objects.create(name="Homilies on Genesis", short_code="CHRYSO_GEN")
        expected = "Homilies on Genesis (CHRYSO_GEN)"
        self.assertEqual(str(source), expected)

    def test_commentary_source_creation(self):
        """Test basic CommentarySource creation and fields."""
        language = Language.objects.create(name="English", code="en")

        source = CommentarySource.objects.create(
            name="Genesis Commentary",
            short_code="GEN_COMM",
            language=language,
            description="A comprehensive commentary on Genesis",
        )

        self.assertEqual(source.name, "Genesis Commentary")
        self.assertEqual(source.short_code, "GEN_COMM")
        self.assertEqual(source.language, language)
        self.assertTrue(source.is_active)  # default True


@pytest.mark.models
class CommentaryEntryModelTest(TestCase):
    """Test CommentaryEntry model functionality."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.author = Author.objects.create(name="Test Author")

        # Create test verse data
        testament = Testament.objects.create(name="Old Testament")
        book = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=testament, chapter_count=50)
        language = Language.objects.create(name="English", code="en")
        version = Version.objects.create(language=language, code="EN_KJV", name="King James Version")
        self.verse = Verse.objects.create(
            book=book, version=version, chapter=1, number=1, text="In the beginning God created..."
        )

        self.source = CommentarySource.objects.create(name="Test Commentary", short_code="TEST_COMM")

    def test_str_method(self):
        """Test __str__ method."""
        entry = CommentaryEntry.objects.create(
            source=self.source,
            book=self.verse.book,
            chapter=1,
            verse_start=1,
            verse_end=1,
            body_text="This is a test commentary entry.",
        )
        expected = f"TEST_COMM: {self.verse.book.osis_code} 1:1"
        self.assertEqual(str(entry), expected)

    def test_commentary_entry_verse_range(self):
        """Test commentary entry with verse range."""
        entry = CommentaryEntry.objects.create(
            source=self.source,
            book=self.verse.book,
            chapter=1,
            verse_start=1,
            verse_end=3,  # Range 1-3
            body_text="This commentary covers verses 1-3.",
        )

        # Verify the str method shows the range
        self.assertIn("1-3", str(entry))


@pytest.mark.models
class VerseCommentModelTest(TestCase):
    """Test VerseComment model functionality."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

        # Create test verse data
        testament = Testament.objects.create(name="Old Testament")
        book = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=testament, chapter_count=50)
        language = Language.objects.create(name="English", code="en")
        version = Version.objects.create(language=language, code="EN_KJV", name="King James Version")
        self.verse = Verse.objects.create(
            book=book, version=version, chapter=1, number=1, text="In the beginning God created..."
        )

    def test_str_method(self):
        """Test __str__ method."""
        comment = VerseComment.objects.create(
            verse=self.verse, user=self.user, comment="This is a user comment on Genesis 1:1"
        )
        expected = f"Comment by {self.user.username} on {self.verse}"
        self.assertEqual(str(comment), expected)

    def test_comment_flags(self):
        """Test comment boolean flags."""
        comment = VerseComment.objects.create(
            verse=self.verse,
            user=self.user,
            comment="This is a favorite public comment",
            is_public=True,
            is_favorite=True,
        )

        self.assertTrue(comment.is_public)
        self.assertTrue(comment.is_favorite)
