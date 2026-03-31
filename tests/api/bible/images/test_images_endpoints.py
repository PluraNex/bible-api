"""
API tests for Biblical Images domain: Artists, Images, Tags, Verse Links.

Tests cover:
- Authentication: all endpoints require API key
- Artist: list, detail, search, images action
- Image: list, detail (tagged/untagged), filters, search, by-verse
- Response structure: contract compliance
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.images.models import Artist, BiblicalImage, ImageTag, ImageVerseLink
from bible.models import APIKey, CanonicalBook, Language, Testament


class ImageTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="images_user")
        self.api_key = APIKey.objects.create(name="Images Key", user=self.user, scopes=["read"])

        self.lang = Language.objects.create(name="English", code="en")
        self.nt = Testament.objects.create(name="NEW", description="New Testament")
        self.ot = Testament.objects.create(name="OLD", description="Old Testament")
        self.book_rev = CanonicalBook.objects.create(osis_code="Rev", canonical_order=66, testament=self.nt, chapter_count=22)
        self.book_gen = CanonicalBook.objects.create(osis_code="Gen", canonical_order=1, testament=self.ot, chapter_count=50)

        # Artists
        self.dore = Artist.objects.create(
            name="Gustave Doré", slug="gustave-dore",
            birth_date="1832-01-06", death_date="1883-01-23",
            nations=["French"], movements=["Romanticism"],
            image_count=2, source="wikiart",
        )
        self.rubens = Artist.objects.create(
            name="Peter Paul Rubens", slug="peter-paul-rubens",
            nations=["Flemish"], movements=["Baroque"],
            image_count=1, source="wikiart",
        )

        # Images
        self.img_tagged = BiblicalImage.objects.create(
            key="0001001", title="The Last Judgment", artist=self.dore,
            completion_year=1866, styles=["Romanticism"], genres=["religious painting"],
            image_url="https://example.com/lastjudgment.jpg",
            is_tagged=True, source="wikiart",
        )
        self.img_untagged = BiblicalImage.objects.create(
            key="0001002", title="Daniel in the Lions' Den", artist=self.dore,
            completion_year=1868, styles=["Romanticism"], genres=["religious painting"],
            image_url="https://example.com/daniel.jpg",
            is_tagged=False, source="wikiart",
        )
        self.img_rubens = BiblicalImage.objects.create(
            key="0002001", title="The Descent from the Cross", artist=self.rubens,
            completion_year=1614, styles=["Baroque"], genres=["religious painting"],
            image_url="https://example.com/descent.jpg",
            is_tagged=False, source="wikiart",
        )

        # Tag for img_tagged
        self.tag = ImageTag.objects.create(
            image=self.img_tagged,
            characters=[{"name": "Christ", "type": "DEITY"}, {"name": "Angel", "type": "ANGEL"}],
            event="The Last Judgment",
            tag_list=["judgment", "apocalypse", "eschatology"],
            symbols=["throne — divine authority", "scales — justice"],
            description="A dramatic scene of the Last Judgment...",
            theological_description="This image depicts the eschatological...",
            scripture_refs=[
                {"ref": "REV.20.12", "relevance": "primary", "reason": "The dead were judged"},
                {"ref": "MAT.25.31", "relevance": "typological", "reason": "Son of Man on throne"},
            ],
            scene_type="narrative",
            moods=["awe", "terror"],
            period="Apocalyptic",
            tagging_model="gemini-2.5-flash",
        )

        # Verse links
        self.link1 = ImageVerseLink.objects.create(
            image=self.img_tagged, book=self.book_rev,
            chapter=20, verse_start=12, verse_end=12,
            relevance_type="primary", reason="The dead were judged",
        )
        self.link2 = ImageVerseLink.objects.create(
            image=self.img_tagged, book=self.book_rev,
            chapter=12, verse_start=7, verse_end=12,
            relevance_type="typological", reason="War in heaven",
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class ArtistEndpointTest(ImageTestBase):

    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get("/api/v1/bible/images/artists/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_artists(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 2)

    def test_list_ordered_by_image_count(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/")
        names = [a["name"] for a in resp.json()["results"]]
        self.assertEqual(names[0], "Gustave Doré")  # 2 images

    def test_detail_by_slug(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/gustave-dore/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["name"], "Gustave Doré")
        self.assertEqual(data["image_count"], 2)
        self.assertIn("French", data["nations"])

    def test_detail_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_artist_images_action(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/gustave-dore/images/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)

    def test_search_artist(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/artists/?search=Rubens")
        self.assertEqual(resp.json()["pagination"]["count"], 1)


class ImageListEndpointTest(ImageTestBase):

    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get("/api/v1/bible/images/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_all(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["pagination"]["count"], 3)

    def test_list_compact_fields(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/")
        img = resp.json()["results"][0]
        for field in ("id", "key", "title", "artist_name", "image_url", "is_tagged", "styles", "genres"):
            self.assertIn(field, img)

    def test_filter_by_is_tagged(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/?is_tagged=true")
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_filter_by_artist_slug(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/?artist=peter-paul-rubens")
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_filter_by_style(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/?style=Baroque")
        self.assertEqual(resp.json()["pagination"]["count"], 1)

    def test_search_by_title(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/?search=Judgment")
        self.assertGreaterEqual(resp.json()["pagination"]["count"], 1)

    def test_pagination(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/?page_size=2")
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertIsNotNone(resp.json()["pagination"]["next"])


class ImageDetailEndpointTest(ImageTestBase):

    def test_detail_tagged_image(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/images/{self.img_tagged.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["title"], "The Last Judgment")
        self.assertIsNotNone(data["tag"])
        self.assertEqual(data["tag"]["event"], "The Last Judgment")
        self.assertEqual(len(data["tag"]["characters"]), 2)
        self.assertGreater(len(data["verse_links"]), 0)

    def test_detail_untagged_image(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/images/{self.img_untagged.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsNone(data["tag"])
        self.assertEqual(len(data["verse_links"]), 0)

    def test_detail_has_nested_artist(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/images/{self.img_tagged.id}/")
        artist = resp.json()["artist"]
        self.assertEqual(artist["name"], "Gustave Doré")
        self.assertIn("birth_date", artist)

    def test_detail_not_found(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ImageByVerseEndpointTest(ImageTestBase):

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v1/bible/images/by-verse/Rev/20/12/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_by_verse_returns_images(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/by-verse/Rev/20/12/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["title"], "The Last Judgment")
        self.assertEqual(data[0]["relevance_type"], "primary")

    def test_by_verse_range_match(self):
        """Link with verse_start=7, verse_end=12 should match verse 10."""
        self._auth()
        resp = self.client.get("/api/v1/bible/images/by-verse/Rev/12/10/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_by_verse_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/by-verse/Gen/50/26/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_by_verse_invalid_book(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/by-verse/Xyz/1/1/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_by_verse_includes_description(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/by-verse/Rev/20/12/")
        data = resp.json()
        if data:
            self.assertIn("description", data[0])
            self.assertIn("characters", data[0])


class ImageSearchEndpointTest(ImageTestBase):

    def test_search_by_title(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/search/?q=Last+Judgment")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_search_by_artist(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/search/?q=Rubens")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.json()), 0)

    def test_search_missing_query(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/search/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_no_results(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/search/?q=xyznonexistent")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_content_type(self):
        self._auth()
        resp = self.client.get("/api/v1/bible/images/")
        self.assertEqual(resp["Content-Type"], "application/json")
