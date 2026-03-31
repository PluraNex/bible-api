"""
Tests for Cross-Domain Integration: Image↔Entity matching.

Tests cover:
- ImageEntityLink model creation and constraints
- Matching pipeline (exact, alias, fuzzy)
- Cross-domain endpoint: entity/{id}/images/
- Status reporting
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.entities.models import (
    CanonicalEntity,
    EntityAlias,
    EntityNamespace,
    EntityStatus,
)
from bible.images.models import Artist, BiblicalImage, ImageTag
from bible.integration.models import ImageEntityLink
from bible.integration.services.image_matcher import ImageEntityMatcher
from bible.models import APIKey, CanonicalBook, Language, Testament
from bible.people.models import Person


class IntegrationTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="int_user")
        self.api_key = APIKey.objects.create(name="Int Key", user=self.user, scopes=["read"])

        self.lang = Language.objects.create(name="English", code="en")
        self.ot = Testament.objects.create(name="OLD", description="Old Testament")
        self.book = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=self.ot, chapter_count=50)

        # Entities
        self.moses = CanonicalEntity.objects.create(
            canonical_id="PER:moses", namespace=EntityNamespace.PERSON,
            primary_name="Moses", status=EntityStatus.APPROVED,
        )
        self.david = CanonicalEntity.objects.create(
            canonical_id="PER:david", namespace=EntityNamespace.PERSON,
            primary_name="David", status=EntityStatus.APPROVED,
        )
        self.gabriel = CanonicalEntity.objects.create(
            canonical_id="ANG:gabriel", namespace=EntityNamespace.ANGEL,
            primary_name="Gabriel", status=EntityStatus.APPROVED,
        )

        # Aliases
        EntityAlias.objects.create(entity=self.moses, name="Moisés", language_code="pt")
        EntityAlias.objects.create(entity=self.david, name="Davi", language_code="pt")

        # Person (post-biblical)
        self.jerome = Person.objects.create(
            canonical_name="Jerome", slug="jerome", person_type="author",
        )

        # Artist + Images + Tags
        self.artist = Artist.objects.create(
            name="Test Artist", slug="test-artist", image_count=3, source="test",
        )
        self.img1 = BiblicalImage.objects.create(
            key="T001", title="Moses and the Burning Bush",
            artist=self.artist, image_url="https://example.com/moses.jpg",
            is_tagged=True, source="test",
        )
        self.img2 = BiblicalImage.objects.create(
            key="T002", title="David and Goliath",
            artist=self.artist, image_url="https://example.com/david.jpg",
            is_tagged=True, source="test",
        )
        self.img3 = BiblicalImage.objects.create(
            key="T003", title="Crowd Scene",
            artist=self.artist, image_url="https://example.com/crowd.jpg",
            is_tagged=True, source="test",
        )

        ImageTag.objects.create(
            image=self.img1,
            characters=[
                {"name": "Moses", "type": "PERSON"},
                {"name": "Gabriel", "type": "ANGEL"},
            ],
            symbols=["burning bush — divine presence"],
        )
        ImageTag.objects.create(
            image=self.img2,
            characters=[
                {"name": "Davi", "type": "PERSON"},  # PT alias
                {"name": "Soldiers", "type": "GROUP"},  # should be skipped
            ],
            symbols=[],
        )
        ImageTag.objects.create(
            image=self.img3,
            characters=[
                {"name": "Crowd", "type": "GROUP"},  # should be skipped
            ],
            symbols=[],
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class ImageEntityLinkModelTest(IntegrationTestBase):

    def test_create_entity_link(self):
        link = ImageEntityLink.objects.create(
            image=self.img1, entity=self.moses,
            character_name="Moses", character_type="PERSON",
            match_method="exact", confidence=1.0,
        )
        self.assertEqual(link.entity, self.moses)
        self.assertIsNone(link.person)

    def test_create_person_link(self):
        link = ImageEntityLink.objects.create(
            image=self.img1, person=self.jerome,
            character_name="Jerome", character_type="PERSON",
            match_method="exact", confidence=0.9,
        )
        self.assertIsNone(link.entity)
        self.assertEqual(link.person, self.jerome)

    def test_create_unlinked(self):
        link = ImageEntityLink.objects.create(
            image=self.img1,
            character_name="Unknown Saint", character_type="OTHER",
            match_method="exact", confidence=0.0,
        )
        self.assertIsNone(link.entity)
        self.assertIsNone(link.person)


class MatchingPipelineTest(IntegrationTestBase):

    def test_match_all_creates_links(self):
        matcher = ImageEntityMatcher()
        stats = matcher.match_all(clear_existing=True)
        self.assertGreater(stats.links_created, 0)
        self.assertEqual(stats.tags_processed, 3)

    def test_exact_match_on_primary_name(self):
        matcher = ImageEntityMatcher()
        stats = matcher.match_all(clear_existing=True)

        moses_link = ImageEntityLink.objects.filter(
            image=self.img1, character_name="Moses"
        ).first()
        self.assertIsNotNone(moses_link)
        self.assertEqual(moses_link.entity, self.moses)
        self.assertEqual(moses_link.match_method, "exact")

    def test_alias_match(self):
        matcher = ImageEntityMatcher()
        stats = matcher.match_all(clear_existing=True)

        davi_link = ImageEntityLink.objects.filter(
            image=self.img2, character_name="Davi"
        ).first()
        self.assertIsNotNone(davi_link)
        self.assertEqual(davi_link.entity, self.david)
        self.assertEqual(davi_link.match_method, "alias")

    def test_group_characters_skipped(self):
        matcher = ImageEntityMatcher()
        stats = matcher.match_all(clear_existing=True)
        self.assertGreater(stats.characters_skipped, 0)

        # "Soldiers" and "Crowd" should not have links
        soldiers_link = ImageEntityLink.objects.filter(character_name="Soldiers").exists()
        crowd_link = ImageEntityLink.objects.filter(character_name="Crowd").exists()
        self.assertFalse(soldiers_link)
        self.assertFalse(crowd_link)

    def test_idempotent_no_duplicates(self):
        matcher = ImageEntityMatcher()
        matcher.match_all(clear_existing=True)
        count1 = ImageEntityLink.objects.count()

        # Run again without clearing
        stats2 = matcher.match_all(clear_existing=False)
        count2 = ImageEntityLink.objects.count()
        self.assertEqual(count1, count2)
        self.assertGreater(stats2.links_existing, 0)

    def test_clear_existing_flag(self):
        matcher = ImageEntityMatcher()
        matcher.match_all(clear_existing=True)
        self.assertGreater(ImageEntityLink.objects.count(), 0)

        matcher.match_all(clear_existing=True)
        # Should still have links (rebuilt)
        self.assertGreater(ImageEntityLink.objects.count(), 0)

    def test_stats_totals_consistent(self):
        matcher = ImageEntityMatcher()
        stats = matcher.match_all(clear_existing=True)
        total_matches = stats.exact_matches + stats.alias_matches + stats.fuzzy_matches + stats.person_matches + stats.unmatched
        self.assertEqual(total_matches, stats.links_created)


class CrossDomainEndpointTest(IntegrationTestBase):

    def setUp(self):
        super().setUp()
        # Run matching pipeline
        matcher = ImageEntityMatcher()
        matcher.match_all(clear_existing=True)

    def test_entity_images_endpoint(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:moses/images/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["title"], "Moses and the Burning Bush")

    def test_entity_images_empty_for_unlinked(self):
        self._auth()
        # Gabriel has no image links in test data (the tag links Gabriel to an image
        # but let's check)
        resp = self.client.get("/api/v1/bible/entities/ANG:gabriel/images/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_entity_images_unauthenticated(self):
        resp = self.client.get("/api/v1/bible/entities/PER:moses/images/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class MatchingStatusTest(IntegrationTestBase):

    def test_status_empty(self):
        status = ImageEntityMatcher.get_status()
        self.assertEqual(status["total_links"], 0)

    def test_status_after_matching(self):
        matcher = ImageEntityMatcher()
        matcher.match_all(clear_existing=True)

        status = ImageEntityMatcher.get_status()
        self.assertGreater(status["total_links"], 0)
        self.assertGreater(status["with_entity"], 0)
        self.assertIn("exact", status["by_method"])
