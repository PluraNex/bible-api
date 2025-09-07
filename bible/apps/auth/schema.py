"""
OpenAPI (drf-spectacular) integration for Api-Key auth.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "bible.apps.auth.authentication.ApiKeyAuthentication"
    name = "ApiKeyAuthentication"
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use header: Authorization: Api-Key <KEY>",
        }

