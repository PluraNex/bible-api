"""
API tests for Biblical Entities domain.

Tests cover:
- Authentication: all endpoints require API key
- Entity: list, detail by canonical_id, search, namespaces, relationships
- By-verse: returns empty list (verse links not populated)
- Filters: namespace, search, ordering
- Response structure: contract compliance
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.entities.models import (
    CanonicalEntity,
    EntityAlias,
    EntityNamespace,
    EntityRelationship,
    EntityStatus,
    RelationshipType,
)
from bible.models import APIKey, CanonicalBook, Language, Testament


class EntityTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="entity_user")
        self.api_key = APIKey.objects.create(name="Entity Key", user=self.user, scopes=["read"])

        self.lang = Language.objects.create(name="English", code="en")
        self.ot = Testament.objects.create(name="OLD", description="Old Testament")
        self.nt = Testament.objects.create(name="NEW", description="New Testament")
        self.book_gen = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=self.ot, chapter_count=50)

        # Entities
        self.moses = CanonicalEntity.objects.create(
            canonical_id="PER:moises", namespace=EntityNamespace.PERSON,
            primary_name="Moisés", description="Legislador de Israel",
            categories=["PERSON", "LEADER"], priority=90, boost=3.5,
            status=EntityStatus.APPROVED,
        )
        self.david = CanonicalEntity.objects.create(
            canonical_id="PER:david", namespace=EntityNamespace.PERSON,
            primary_name="David", description="Rei de Israel",
            categories=["PERSON", "KING"], priority=85, boost=3.8,
            is_type_of_christ=True, status=EntityStatus.APPROVED,
        )
        self.jerusalem = CanonicalEntity.objects.create(
            canonical_id="PLC:jerusalem", namespace=EntityNamespace.PLACE,
            primary_name="Jerusalém", description="Cidade santa",
            categories=["PLACE", "CITY"], priority=95, boost=4.0,
            status=EntityStatus.APPROVED,
        )
        self.agua_symbol = CanonicalEntity.objects.create(
            canonical_id="NAT:agua", namespace=EntityNamespace.CONCEPT,
            primary_name="Água", description="Símbolo de purificação",
            priority=60, boost=2.5, status=EntityStatus.APPROVED,
        )

        # Aliases
        EntityAlias.objects.create(entity=self.moses, name="Moses", language_code="en")
        EntityAlias.objects.create(entity=self.moses, name="Moisés", language_code="pt")
        EntityAlias.objects.create(entity=self.david, name="Davi", language_code="pt")

        # Relationships
        self.rel = EntityRelationship.objects.create(
            source=self.moses, target=self.david,
            relationship_type=RelationshipType.PREDECESSOR_OF,
            description="Moisés precede Davi na história de Israel",
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class EntityListEndpointTest(EntityTestBase):

    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get("/api/v1/bible/entities/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_entities(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 4)

    def test_list_compact_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/")
        entity = resp.json()["results"][0]
        for field in ("canonical_id", "namespace", "primary_name", "description", "priority", "boost"):
            self.assertIn(field, entity)

    def test_filter_by_namespace(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/?namespace=PERSON")
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    def test_search_filter(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/?search=Moisés")
        self.assertGreaterEqual(resp.json()["pagination"]["count"], 1)

    def test_ordering_by_priority(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/?ordering=-priority")
        results = resp.json()["results"]
        self.assertEqual(results[0]["canonical_id"], "PLC:jerusalem")  # priority=95

    def test_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/?page_size=2")
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertIsNotNone(resp.json()["pagination"]["next"])


class EntityDetailEndpointTest(EntityTestBase):

    def test_detail_by_canonical_id(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:moises/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["canonical_id"], "PER:moises")
        self.assertEqual(data["primary_name"], "Moisés")

    def test_detail_has_aliases(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:moises/")
        aliases = resp.json()["aliases"]
        self.assertEqual(len(aliases), 2)
        alias_names = [a["name"] for a in aliases]
        self.assertIn("Moses", alias_names)

    def test_detail_has_full_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:david/")
        data = resp.json()
        self.assertTrue(data["is_type_of_christ"])
        self.assertIn("aliases", data)
        self.assertIn("roles", data)
        self.assertIn("wikipedia_url", data)

    def test_detail_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class EntityRelationshipsEndpointTest(EntityTestBase):

    def test_relationships_all(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:moises/relationships/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["relationship_type"], "predecessor_of")
        self.assertEqual(data[0]["direction"], "outgoing")

    def test_relationships_incoming(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PER:david/relationships/?direction=incoming")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["direction"], "incoming")

    def test_relationships_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/PLC:jerusalem/relationships/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)


class EntitySearchEndpointTest(EntityTestBase):

    def test_search_by_name(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/?q=David")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_search_by_alias(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/?q=Moses")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [e["primary_name"] for e in resp.json()]
        self.assertIn("Moisés", names)

    def test_search_by_canonical_id(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/?q=PER:moises")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_search_with_namespace_filter(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/?q=a&namespace=PLACE")
        for entity in resp.json():
            self.assertEqual(entity["namespace"], "PLACE")

    def test_search_missing_query(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/search/?q=xyznonexistent")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)


class EntityByVerseEndpointTest(EntityTestBase):

    def test_by_verse_returns_empty(self):
        """EntityVerseLink not populated — returns empty list."""
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/by-verse/Gen/1/1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_by_verse_invalid_book(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/by-verse/Xyz/1/1/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class EntityNamespacesEndpointTest(EntityTestBase):

    def test_namespaces(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/namespaces/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        namespaces = {d["namespace"] for d in data}
        self.assertIn("PERSON", namespaces)
        self.assertIn("PLACE", namespaces)
        total = sum(d["count"] for d in data)
        self.assertEqual(total, 4)

    def test_content_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/entities/")
        self.assertEqual(resp["Content-Type"], "application/json")
