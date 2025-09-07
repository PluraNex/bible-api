"""
Custom authentication classes for Bible API.
"""
from rest_framework import authentication, exceptions

from bible.models import APIKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom API Key authentication.

    Clients should authenticate by passing the API key in the "Authorization"
    header, preceded by the string "Api-Key ".  For example:

        Authorization: Api-Key 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = "Api-Key"

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = authentication.get_authorization_header(request).split()

        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth_header) == 1:
            msg = "Invalid token header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = "Invalid token header. Token string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth_header[1].decode()
        except UnicodeError as e:
            msg = "Invalid token header. Token string should not contain invalid characters."
            raise exceptions.AuthenticationFailed(msg) from e

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        """
        Authenticate the token.
        """
        try:
            api_key = APIKey.objects.select_related("user").get(key=key, is_active=True)
        except APIKey.DoesNotExist as e:
            raise exceptions.AuthenticationFailed("Invalid API key.") from e

        if not api_key.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        # Update last used timestamp
        api_key.update_last_used()

        return (api_key.user, api_key)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return self.keyword
