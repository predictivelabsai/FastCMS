"""Microsoft Entra ID (Azure AD) OIDC / SSO adapter: STUB.

Planned implementation: authorization-code flow with PKCE via ``msal``
(ConfidentialClientApplication) or ``authlib``. Neither is a hard dependency yet;
install ``msal`` when implementing.

TODO:
  * build the authorize URL with msal ``get_authorization_request_url`` (scopes
    openid profile email, plus User.Read if groups are read from Graph);
  * in handle_callback, exchange the code (``acquire_token_by_authorization_code``),
    validate the id_token (issuer = tenant, audience = client id, nonce);
  * read ``groups`` / ``roles`` claims for map_user_roles;
  * restrict tenants with ENTRA_ALLOWED_TENANTS for multi-tenant apps.
"""
from __future__ import annotations

import os
from typing import Mapping
from urllib.parse import urlencode

from .base import AuthIdentity, AuthProvider


class EntraIDProvider(AuthProvider):
    name = "entra"
    label = "Sign in with Microsoft"
    enable_flag = "AUTH_ENTRA_ENABLED"
    required_env = ("ENTRA_TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET")

    @property
    def authority(self) -> str:
        base = os.getenv("ENTRA_AUTHORITY_HOST", "https://login.microsoftonline.com")
        return f"{base.rstrip('/')}/{os.getenv('ENTRA_TENANT_ID', 'common')}"

    def get_login_url(self, redirect_uri: str, state: str) -> str:
        self.ensure_configured()
        # Shape of the final URL; PKCE + nonce will be added with msal.
        query = urlencode({
            "client_id": os.getenv("ENTRA_CLIENT_ID", ""),
            "response_type": "code",
            "redirect_uri": redirect_uri or os.getenv("ENTRA_REDIRECT_URI", ""),
            "response_mode": "query",
            "scope": "openid profile email",
            "state": state,
        })
        return f"{self.authority}/oauth2/v2.0/authorize?{query}"

    def handle_callback(self, params: Mapping[str, str], redirect_uri: str = "") -> AuthIdentity:
        if self.mock_mode():
            return AuthIdentity(provider=self.name, subject="mock-entra-oid",
                                email="mock.user@example.com", name="Mock Entra User",
                                groups=["FastCMS-Editors"])
        self.ensure_configured()
        raise NotImplementedError("Entra ID token exchange is not implemented yet (see module TODO)")

    def authenticate(self, username: str, password: str) -> AuthIdentity:
        raise NotImplementedError("Entra ID uses the OIDC redirect flow; ROPC is intentionally not supported")
