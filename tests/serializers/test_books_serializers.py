"""
Unit tests for books serializers.
Tests serialization, validation, and method fields.
"""
import pytest
from django.test import TestCase

from bible.books.serializers import BookNameSerializer, BookSerializer, CanonicalBookSerializer, LanguageSerializer
from bible.models import BookName, CanonicalBook, Language, Testament


@pytest.mark.unit
class BookSerializersTest(TestCase):
    """Test book domain serializers."""

    def setUp(self):
        """Set up test data."""
        # Create languages
        self.english = Language.objects.create(code="en", name="English")
        self.portuguese = Language.objects.create(code="pt", name="Portuguese")

        # Create testaments
        self.old_testament = Testament.objects.create(name="Old Testament")
        self.new_testament = Testament.objects.create(name="New Testament")

        # Create canonical book
        self.genesis = CanonicalBook.objects.create(
            osis_code="Gen",
            canonical_order=1,
            testament=self.old_testament,
            chapter_count=50,
            is_deuterocanonical=False,
        )

        # Create book names
        self.genesis_en = BookName.objects.create(
            canonical_book=self.genesis, language=self.english, name="Genesis", abbreviation="Gen"
        )

        self.genesis_pt = BookName.objects.create(
            canonical_book=self.genesis, language=self.portuguese, name="Gênesis", abbreviation="Gn"
        )

    def test_book_serializer_structure(self):
        """Test BookSerializer structure and method fields."""
        serializer = BookSerializer(self.genesis)
        data = serializer.data

        # Verify all expected fields are present
        expected_fields = ["id", "name", "abbreviation", "order", "testament", "chapter_count"]
        for field in expected_fields:
            self.assertIn(field, data)

        # Verify field values
        self.assertEqual(data["name"], "Genesis")
        self.assertEqual(data["abbreviation"], "Gen")
        self.assertEqual(data["order"], 1)
        self.assertEqual(data["testament"], "Old Testament")
        self.assertEqual(data["chapter_count"], 50)

    def test_book_serializer_get_name_method(self):
        """Test get_name method returns English name by default."""
        serializer = BookSerializer(self.genesis)
        name = serializer.get_name(self.genesis)
        self.assertEqual(name, "Genesis")

    def test_book_serializer_get_name_fallback(self):
        """Test get_name fallback to OSIS code when no English name exists."""
        # Create book without English name
        book_no_en = CanonicalBook.objects.create(
            osis_code="Test", canonical_order=100, testament=self.old_testament, chapter_count=1
        )

        serializer = BookSerializer(book_no_en)
        name = serializer.get_name(book_no_en)
        self.assertEqual(name, "Test")

    def test_book_serializer_get_abbreviation_method(self):
        """Test get_abbreviation method returns English abbreviation by default."""
        serializer = BookSerializer(self.genesis)
        abbr = serializer.get_abbreviation(self.genesis)
        self.assertEqual(abbr, "Gen")

    def test_book_serializer_get_abbreviation_fallback(self):
        """Test get_abbreviation fallback to OSIS code prefix when no English name exists."""
        book_no_en = CanonicalBook.objects.create(
            osis_code="TestBook", canonical_order=100, testament=self.old_testament, chapter_count=1
        )

        serializer = BookSerializer(book_no_en)
        abbr = serializer.get_abbreviation(book_no_en)
        self.assertEqual(abbr, "Tes")  # First 3 chars of OSIS code

    def test_canonical_book_serializer_structure(self):
        """Test CanonicalBookSerializer structure."""
        serializer = CanonicalBookSerializer(self.genesis)
        data = serializer.data

        # Verify all expected fields are present
        expected_fields = [
            "id",
            "osis_code",
            "canonical_order",
            "testament",
            "testament_name",
            "is_deuterocanonical",
            "chapter_count",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

        # Verify specific values
        self.assertEqual(data["osis_code"], "Gen")
        self.assertEqual(data["canonical_order"], 1)
        self.assertEqual(data["testament_name"], "Old Testament")
        self.assertEqual(data["is_deuterocanonical"], False)

    def test_book_name_serializer_structure(self):
        """Test BookNameSerializer structure and related fields."""
        serializer = BookNameSerializer(self.genesis_en)
        data = serializer.data

        # Verify all expected fields are present
        expected_fields = [
            "id",
            "name",
            "abbreviation",
            "canonical_book",
            "canonical_book_osis",
            "language",
            "language_code",
            "language_name",
            "version",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

        # Verify field values
        self.assertEqual(data["name"], "Genesis")
        self.assertEqual(data["abbreviation"], "Gen")
        self.assertEqual(data["canonical_book_osis"], "Gen")
        self.assertEqual(data["language_code"], "en")
        self.assertEqual(data["language_name"], "English")
        self.assertIsNone(data["version"])  # No version assigned

        # version_code should only be present if version is not None
        if data["version"]:
            self.assertIn("version_code", data)
        else:
            # version_code may or may not be present when version is None
            pass

    def test_language_serializer_structure(self):
        """Test LanguageSerializer structure."""
        serializer = LanguageSerializer(self.english)
        data = serializer.data

        # Verify all expected fields are present
        expected_fields = ["id", "name", "code", "created_at", "updated_at"]
        for field in expected_fields:
            self.assertIn(field, data)

        # Verify field values
        self.assertEqual(data["name"], "English")
        self.assertEqual(data["code"], "en")

    def test_book_serializer_many_objects(self):
        """Test BookSerializer with multiple objects."""
        # Create another book
        exodus = CanonicalBook.objects.create(
            osis_code="Exo", canonical_order=2, testament=self.old_testament, chapter_count=40
        )

        BookName.objects.create(canonical_book=exodus, language=self.english, name="Exodus", abbreviation="Exo")

        books = CanonicalBook.objects.all().order_by("canonical_order")
        serializer = BookSerializer(books, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Genesis")
        self.assertEqual(data[1]["name"], "Exodus")

    def test_serializer_performance_with_select_related(self):
        """Test that serializers work efficiently with select_related."""
        # This would be tested in integration tests, but we can verify structure
        queryset = CanonicalBook.objects.select_related("testament")
        serializer = BookSerializer(queryset, many=True)

        # Should not raise any errors and return data
        data = serializer.data
        self.assertIsInstance(data, list)

    def test_book_name_serializer_validation(self):
        """Test BookNameSerializer validation."""
        valid_data = {
            "name": "Test Book",
            "abbreviation": "TB",
            "canonical_book": self.genesis.id,
            "language": self.english.id,
        }

        serializer = BookNameSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_book_name_serializer_invalid_data(self):
        """Test BookNameSerializer with invalid data."""
        invalid_data = {
            "name": "",  # Empty name
            "canonical_book": self.genesis.id,
            "language": self.english.id,
        }

        serializer = BookNameSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_canonical_book_serializer_read_only_fields(self):
        """Test that read-only fields in CanonicalBookSerializer work correctly."""
        data = {
            "osis_code": "TEST",
            "canonical_order": 999,
            "testament": self.old_testament.id,
            "chapter_count": 5,
            "testament_name": "Should be ignored",  # Read-only field
        }

        serializer = CanonicalBookSerializer(data=data)
        if serializer.is_valid():
            # testament_name should be populated from the relationship, not the input
            instance = serializer.save()
            self.assertEqual(instance.testament.name, "Old Testament")
        else:
            # If invalid, check why
            self.fail(f"Serializer validation failed: {serializer.errors}")

    def test_language_serializer_validation(self):
        """Test LanguageSerializer validation."""
        valid_data = {
            "name": "Spanish",
            "code": "es",
        }

        serializer = LanguageSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_language_serializer_duplicate_code(self):
        """Test LanguageSerializer prevents duplicate codes."""
        duplicate_data = {
            "name": "Another English",
            "code": "en",  # Already exists
        }

        serializer = LanguageSerializer(data=duplicate_data)
        # This should fail due to unique constraint
        self.assertFalse(serializer.is_valid())
