"""Common interface for FastCMS sign-in providers."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class ProviderNotConfigured(RuntimeError):
    """Raised when a provider is disabled or missing required settings."""


@dataclass
class AuthIdentity:
    """Normalised identity handed to FastCMS after a successful sign-in."""

    provider: str
    subject: str                 # stable provider-side id (sub, objectGUID, personal code hash…)
    email: str = ""
    name: str = ""
    groups: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class AuthProvider(ABC):
    """Base class: one instance per request is fine; config comes from env."""

    name: str = "base"
    label: str = "Sign in"
    enable_flag: str = ""
    #: env vars that must be non-empty for the provider to be usable
    required_env: tuple[str, ...] = ()

    @classmethod
    def is_enabled(cls) -> bool:
        return bool(cls.enable_flag) and env_flag(cls.enable_flag)

    def missing_config(self) -> list[str]:
        return [key for key in self.required_env if not os.getenv(key)]

    def ensure_configured(self) -> None:
        if not self.is_enabled():
            raise ProviderNotConfigured(f"{self.name} is disabled; set {self.enable_flag}=1")
        missing = self.missing_config()
        if missing:
            raise ProviderNotConfigured(f"{self.name} missing settings: {', '.join(missing)}")

    @staticmethod
    def mock_mode() -> bool:
        return env_flag("AUTH_PROVIDERS_MOCK")

    # ── flow ──────────────────────────────────────────────────────────
    @abstractmethod
    def get_login_url(self, redirect_uri: str, state: str) -> str:
        """URL to send the browser to (redirect-based providers)."""

    @abstractmethod
    def handle_callback(self, params: Mapping[str, str], redirect_uri: str = "") -> AuthIdentity:
        """Validate the provider's callback/response and return the identity."""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> AuthIdentity:
        """Direct credential check (form-based providers such as LDAP)."""

    def map_user_roles(self, identity: AuthIdentity) -> str:
        """Map provider groups to a FastCMS role ('admin' or 'editor').

        Uses AUTH_<NAME>_ADMIN_GROUPS (comma-separated). Default: editor.
        """
        admin_groups = {
            g.strip().lower()
            for g in os.getenv(f"AUTH_{self.name.upper()}_ADMIN_GROUPS", "").split(",")
            if g.strip()
        }
        if admin_groups and admin_groups & {g.lower() for g in identity.groups}:
            return "admin"
        return "editor"
