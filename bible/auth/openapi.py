# bible/auth/openapi.py
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "bible.auth.authentication.ApiKeyAuthentication"
    name = "ApiKeyAuth"
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        """Define o esquema de segurança OpenAPI 3.0 para API Key."""
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "API Key authentication. Format: Api-Key your_api_key_here",
        }

    def get_security_requirement(self, auto_schema):
        """Define os requisitos de segurança para endpoints."""
        return {self.name: []}
