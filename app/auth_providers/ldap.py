"""LDAP / Active Directory adapter: STUB.

Planned implementation with ``ldap3`` (not yet a dependency):

    server = ldap3.Server(LDAP_URL, use_ssl=LDAP_URL.startswith("ldaps://"))
    svc = ldap3.Connection(server, LDAP_BIND_DN, LDAP_BIND_PASSWORD, auto_bind=True)
    svc.search(LDAP_BASE_DN, LDAP_USER_FILTER.format(username=escape(username)),
               attributes=["mail", "displayName", "memberOf"])
    ldap3.Connection(server, user_dn, password, auto_bind=True)   # verify password

TODO: implement the above, escape filter input (ldap3.utils.conv.escape_filter_chars),
require LDAPS or StartTLS, map memberOf to groups, add timeouts.
"""
from __future__ import annotations

import os
from typing import Mapping

from .base import AuthIdentity, AuthProvider


class LDAPProvider(AuthProvider):
    name = "ldap"
    label = "Sign in with your directory account"
    enable_flag = "AUTH_LDAP_ENABLED"
    required_env = ("LDAP_URL", "LDAP_BASE_DN")

    @property
    def user_filter(self) -> str:
        return os.getenv("LDAP_USER_FILTER", "(sAMAccountName={username})")

    def get_login_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError("LDAP uses the username/password form; there is no redirect URL")

    def handle_callback(self, params: Mapping[str, str], redirect_uri: str = "") -> AuthIdentity:
        raise NotImplementedError("LDAP has no callback; call authenticate()")

    def authenticate(self, username: str, password: str) -> AuthIdentity:
        if self.mock_mode():
            if not username or not password:
                raise ValueError("username and password are required")
            return AuthIdentity(provider=self.name, subject=f"mock-{username}",
                                email=f"{username}@example.com", name=username,
                                groups=["FastCMS-Editors"])
        self.ensure_configured()
        raise NotImplementedError("LDAP bind/search via ldap3 is not implemented yet (see module TODO)")
