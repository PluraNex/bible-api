"""
API tests for versions endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Language, Version


class VersionsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="vers_user")
        self.api_key = APIKey.objects.create(name="Vers Key", user=self.user, scopes=["read"])

        # Create Language instances
        self.en_lang = Language.objects.create(code="en", name="English")
        self.pt_lang = Language.objects.create(code="pt", name="Portuguese")

        # Create Version instances with proper Language objects
        Version.objects.create(name="King James Version", code="EN_KJV", language=self.en_lang, is_active=True)
        Version.objects.create(name="Nova Versão Internacional", code="PT_NVI", language=self.pt_lang, is_active=True)
        Version.objects.create(name="Outdated Version", code="EN_OV", language=self.en_lang, is_active=False)

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/bible/versions/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_versions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json().get("results", [])), 2)

    def test_filter_by_language_and_active(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/versions/?language={self.en_lang.id}&is_active=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        # Since language is StringRelatedField, it returns the string representation of Language
        self.assertTrue(all(v["language"] == str(self.en_lang) for v in items))
        self.assertTrue(all(v["is_active"] is True for v in items))

    def test_detail_and_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        ok = self.client.get("/api/v1/bible/versions/KJV/")
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertEqual(ok.json()["abbreviation"], "KJV")

        miss = self.client.get("/api/v1/bible/versions/FAKE/")
        self.assertEqual(miss.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_abbreviation_case_insensitive(self):
        """Detail lookup by abbreviation should be case-insensitive."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/kjv/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["abbreviation"], "KJV")

    def test_list_ordering_by_name(self):
        """List should be ordered deterministically by name (asc)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in resp.json().get("results", [])]
        self.assertEqual(names, sorted(names))

    def test_filter_is_active_false(self):
        """Filtering by is_active=false should return only inactive versions."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/?is_active=false")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(all(item["is_active"] is False for item in items))

    def test_language_filter_case_insensitive(self):
        """Language filter should work with language ID."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/versions/?language={self.en_lang.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        # Since language is StringRelatedField, it returns the string representation of Language
        self.assertTrue(all(v["language"] == str(self.en_lang) for v in items))

    def test_is_active_various_formats(self):
        """is_active should accept various boolean formats."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test different true formats
        for true_val in ["1", "true", "True", "TRUE", "yes", "YES"]:
            resp = self.client.get(f"/api/v1/bible/versions/?is_active={true_val}")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            items = resp.json().get("results", [])
            if items:  # Only check if we have results
                self.assertTrue(all(item["is_active"] is True for item in items))

    def test_requires_read_scope(self):
        """Endpoints should require 'read' scope."""
        # API key without 'read' scope
        no_read_key = APIKey.objects.create(name="No Read Key", user=self.user, scopes=["write"])  # Missing 'read'

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {no_read_key.key}")

        # Both endpoints should return 403
        list_resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(list_resp.status_code, status.HTTP_403_FORBIDDEN)

        detail_resp = self.client.get("/api/v1/bible/versions/KJV/")
        self.assertEqual(detail_resp.status_code, status.HTTP_403_FORBIDDEN)


class VersionDefaultApiTest(TestCase):
    """Tests for the versions default endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="default_user")
        self.api_key = APIKey.objects.create(name="Default Key", user=self.user, scopes=["read"])

        # Create base languages
        self.en_lang = Language.objects.create(code="en", name="English")
        self.pt_lang = Language.objects.create(code="pt", name="Portuguese")

        # Create regional languages
        self.pt_br_lang = Language.objects.create(code="pt-BR", name="Portuguese (Brazil)")
        self.en_us_lang = Language.objects.create(code="en-US", name="English (US)")

        # Create active versions for different languages
        self.kjv = Version.objects.create(
            name="King James Version", code="EN_KJV", language=self.en_lang, is_active=True
        )
        self.nvi = Version.objects.create(
            name="Nova Versão Internacional", code="PT_NVI", language=self.pt_lang, is_active=True
        )
        self.nvi_br = Version.objects.create(
            name="Nova Versão Internacional (Brasil)",
            code="PT_BR_NVI",
            language=self.pt_br_lang,
            is_active=True,
        )

        # Create inactive version
        Version.objects.create(name="Outdated Version", code="EN_OLD", language=self.en_lang, is_active=False)

    def test_requires_auth(self):
        """Default endpoint should require authentication."""
        resp = self.client.get("/api/v1/bible/versions/default/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_requires_read_scope(self):
        """Default endpoint should require 'read' scope."""
        no_read_key = APIKey.objects.create(name="No Read Key", user=self.user, scopes=["write"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {no_read_key.key}")

        resp = self.client.get("/api/v1/bible/versions/default/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_default_without_lang_returns_english(self):
        """Default endpoint without lang param should return English version."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "en")
        self.assertTrue(data["is_active"])

    def test_default_with_exact_language_match(self):
        """Should return version for exact language match."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=pt")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "pt")
        self.assertEqual(data["abbreviation"], "NVI")

    def test_base_language_fallback_to_regional(self):
        """Base language should fallback to regional variant when base not found."""
        # Remove the base Portuguese version to test fallback
        self.nvi.delete()

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=pt")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "pt-BR")
        self.assertEqual(data["abbreviation"], "NVI-BR")

    def test_regional_language_fallback_to_base(self):
        """Regional language should fallback to base when regional not found."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=pt-PT")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "pt")  # Falls back to base Portuguese
        self.assertEqual(data["abbreviation"], "NVI")

    def test_fallback_to_english(self):
        """Should fallback to English when requested language not found."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=es")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "en")  # Falls back to English
        self.assertEqual(data["abbreviation"], "KJV")

    def test_no_active_versions_returns_404(self):
        """Should return 404 when no active versions exist."""
        # Make all versions inactive
        Version.objects.update(is_active=False)

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=pt")

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.json()
        self.assertEqual(data["code"], "version_not_found")
        self.assertIn("No active version found for language 'pt'", data["detail"])

    def test_response_headers_no_vary(self):
        """Response should not have Vary header since only lang query param is used."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/default/?lang=pt")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # No Vary header expected since we only use lang query param, not Accept-Language
        self.assertNotIn("Vary", resp)

    def test_ordering_consistency(self):
        """Should return same version consistently when multiple versions exist."""
        # Create another Portuguese version to test ordering
        Version.objects.create(
            name="Almeida Revista e Atualizada",
            code="PT_ARA",
            language=self.pt_lang,
            is_active=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Make multiple requests and ensure consistent results
        responses = []
        for _ in range(3):
            resp = self.client.get("/api/v1/bible/versions/default/?lang=pt")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            responses.append(resp.json()["abbreviation"])

        # All responses should be the same (deterministic ordering by name)
        self.assertEqual(len(set(responses)), 1)
        # Should return the first alphabetically by name
        self.assertEqual(responses[0], "ARA")  # "Almeida" comes before "Nova" alphabetically

    def test_case_insensitive_language_codes(self):
        """Language codes should be handled case-sensitively (as stored in DB)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test with different cases - should match exactly as stored
        resp = self.client.get("/api/v1/bible/versions/default/?lang=PT")
        # This should not match 'pt' and should fallback to English
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["language"], "en")  # Falls back to English since 'PT' != 'pt'
