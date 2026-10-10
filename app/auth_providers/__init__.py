"""Pluggable enterprise sign-in adapters (stubs).

Google sign-in lives in ``app/google_auth.py`` and is unchanged. The adapters
here share one interface (:class:`AuthProvider`) and are **disabled by default**;
each is switched on with its own env flag:

    AUTH_VIISP_ENABLED=1     Lithuanian e-government login (VIISP auth service)
    AUTH_ENTRA_ENABLED=1     Microsoft Entra ID (OIDC / SSO)
    AUTH_LDAP_ENABLED=1      LDAP / Active Directory

They are scaffolding: the network flows are not implemented yet and raise
``NotImplementedError`` (LDAP and Entra ID can return mock identities when
``AUTH_PROVIDERS_MOCK=1``, for local UI work and tests only).
"""
from __future__ import annotations

from .base import AuthIdentity, AuthProvider, ProviderNotConfigured, env_flag
from .entra_id import EntraIDProvider
from .ldap import LDAPProvider
from .viisp import VIISPProvider

PROVIDERS: dict[str, type[AuthProvider]] = {
    VIISPProvider.name: VIISPProvider,
    EntraIDProvider.name: EntraIDProvider,
    LDAPProvider.name: LDAPProvider,
}


def enabled_providers() -> dict[str, AuthProvider]:
    """Instantiate only the providers whose AUTH_<NAME>_ENABLED flag is on."""
    return {name: cls() for name, cls in PROVIDERS.items() if cls.is_enabled()}


def get_provider(name: str) -> AuthProvider:
    cls = PROVIDERS.get(name)
    if cls is None:
        raise KeyError(f"unknown auth provider {name!r}")
    if not cls.is_enabled():
        raise ProviderNotConfigured(f"{name} is disabled; set {cls.enable_flag}=1")
    return cls()


__all__ = [
    "AuthIdentity", "AuthProvider", "ProviderNotConfigured", "PROVIDERS",
    "EntraIDProvider", "LDAPProvider", "VIISPProvider",
    "enabled_providers", "get_provider", "env_flag",
]
