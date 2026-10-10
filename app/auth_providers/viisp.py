"""VIISP (Lithuanian e-government gateway) sign-in adapter: STUB.

VIISP's authentication service lets citizens sign in with Smart-ID, Mobile-ID,
bank links or the national eID card. Integration is a signed SOAP/SAML-style
exchange with the VIISP auth service, which needs a registered service provider
(PID), an X.509 key pair registered with VIISP, and VIISP's public certificate.

Status: placeholders only, no network calls. Every flow raises NotImplementedError.

TODO:
  * build the signed ``authenticationRequest`` (XML-DSig, VIISP_PID, postback URL)
    and obtain a ticket from VIISP_AUTH_SERVICE_URL;
  * redirect the browser to VIISP_LOGIN_URL?ticket=…;
  * on postback, call ``authenticationDataRequest`` with the ticket and verify the
    response signature against VIISP_CERT_PATH;
  * map lt-personal-code / name / email attributes to AuthIdentity (store a salted
    hash of the personal code, not the code itself);
  * test against the VIISP test environment before production.
"""
from __future__ import annotations

import os
from typing import Mapping

from .base import AuthIdentity, AuthProvider


class VIISPProvider(AuthProvider):
    name = "viisp"
    label = "Sign in with VIISP (Smart-ID, Mobile-ID, bank, eID)"
    enable_flag = "AUTH_VIISP_ENABLED"
    required_env = (
        "VIISP_PID",                # service provider id issued by VIISP
        "VIISP_AUTH_SERVICE_URL",   # authentication service endpoint (test or prod)
        "VIISP_LOGIN_URL",          # browser redirect endpoint
        "VIISP_PRIVATE_KEY_PATH",   # our signing key (PEM), never committed
        "VIISP_CERT_PATH",          # VIISP public certificate (PEM)
    )

    @property
    def postback_url(self) -> str:
        return os.getenv("VIISP_POSTBACK_URL", "")

    def get_login_url(self, redirect_uri: str, state: str) -> str:
        self.ensure_configured()
        raise NotImplementedError("VIISP ticket request is not implemented yet (see module TODO)")

    def handle_callback(self, params: Mapping[str, str], redirect_uri: str = "") -> AuthIdentity:
        self.ensure_configured()
        raise NotImplementedError("VIISP authenticationDataRequest is not implemented yet")

    def authenticate(self, username: str, password: str) -> AuthIdentity:
        raise NotImplementedError("VIISP is redirect-based; use get_login_url/handle_callback")
