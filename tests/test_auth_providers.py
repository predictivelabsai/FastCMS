import pytest

from app.auth_providers import (PROVIDERS, AuthIdentity, AuthProvider, EntraIDProvider,
                                LDAPProvider, ProviderNotConfigured, VIISPProvider,
                                enabled_providers, get_provider)

FLAGS = ["AUTH_VIISP_ENABLED", "AUTH_ENTRA_ENABLED", "AUTH_LDAP_ENABLED", "AUTH_PROVIDERS_MOCK"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in FLAGS:
        monkeypatch.delenv(key, raising=False)


def test_registry_and_interface():
    assert set(PROVIDERS) == {"viisp", "entra", "ldap"}
    for cls in PROVIDERS.values():
        assert issubclass(cls, AuthProvider)
        for method in ("authenticate", "get_login_url", "handle_callback", "map_user_roles"):
            assert callable(getattr(cls, method))


def test_disabled_by_default():
    assert enabled_providers() == {}
    with pytest.raises(ProviderNotConfigured):
        get_provider("viisp")


def test_flags_enable(monkeypatch):
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "1")
    assert list(enabled_providers()) == ["ldap"]


def test_viisp_stub_raises(monkeypatch):
    monkeypatch.setenv("AUTH_VIISP_ENABLED", "1")
    for key in VIISPProvider.required_env:
        monkeypatch.setenv(key, "placeholder")
    p = get_provider("viisp")
    with pytest.raises(NotImplementedError):
        p.get_login_url("https://cms.example/auth/viisp/callback", "state")
    with pytest.raises(NotImplementedError):
        p.handle_callback({"ticket": "t"})
    with pytest.raises(NotImplementedError):
        p.authenticate("u", "p")


def test_viisp_missing_config(monkeypatch):
    monkeypatch.setenv("AUTH_VIISP_ENABLED", "1")
    with pytest.raises(ProviderNotConfigured):
        VIISPProvider().get_login_url("x", "s")


def test_entra_login_url_and_mock(monkeypatch):
    monkeypatch.setenv("AUTH_ENTRA_ENABLED", "1")
    monkeypatch.setenv("ENTRA_TENANT_ID", "tenant-123")
    monkeypatch.setenv("ENTRA_CLIENT_ID", "client-abc")
    monkeypatch.setenv("ENTRA_CLIENT_SECRET", "not-a-real-secret")
    url = EntraIDProvider().get_login_url("https://cms.example/cb", "st")
    assert url.startswith("https://login.microsoftonline.com/tenant-123/oauth2/v2.0/authorize?")
    assert "client_id=client-abc" in url and "state=st" in url
    with pytest.raises(NotImplementedError):
        EntraIDProvider().handle_callback({"code": "c"})
    monkeypatch.setenv("AUTH_PROVIDERS_MOCK", "1")
    ident = EntraIDProvider().handle_callback({"code": "c"})
    assert isinstance(ident, AuthIdentity) and ident.provider == "entra"


def test_ldap_mock_and_roles(monkeypatch):
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "1")
    monkeypatch.setenv("LDAP_URL", "ldaps://ldap.example")
    monkeypatch.setenv("LDAP_BASE_DN", "DC=example,DC=com")
    with pytest.raises(NotImplementedError):
        LDAPProvider().authenticate("jdoe", "pw")
    monkeypatch.setenv("AUTH_PROVIDERS_MOCK", "1")
    p = LDAPProvider()
    ident = p.authenticate("jdoe", "pw")
    assert ident.email == "jdoe@example.com"
    assert p.map_user_roles(ident) == "editor"
    monkeypatch.setenv("AUTH_LDAP_ADMIN_GROUPS", "FastCMS-Admins, fastcms-editors")
    assert p.map_user_roles(ident) == "admin"
