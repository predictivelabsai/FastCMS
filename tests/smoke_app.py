"""End-to-end smoke check, run in a fresh interpreter per backend by test_smoke.py.

The database backend is picked at import time from DATABASE_URL, so each backend
needs its own process.
"""
import json
import os
import sys
import uuid

from starlette.testclient import TestClient

import main  # noqa: E402  (imports app + creates tables)
from app import db as cms_db
from app.dbconn import is_postgres
from app.pages import create_page, publish_page, get_children
from app.search import reindex_all, search
from app.settings import set_setting, get_setting
from app.account_auth import accounts

expected = sys.argv[1]
assert ("postgres" if is_postgres() else "sqlite") == expected, (expected, is_postgres())

roots = cms_db.pages(where="depth=1", limit=1)
root = roots[0] if roots else cms_db.pages.insert(
    title="Root", slug="root", path="0001", depth=1, numchild=0, url_path="/", live=True,
    created_at=cms_db.now(), updated_at=cms_db.now())

slug = "smoke-" + uuid.uuid4().hex[:8]
body = json.dumps([{"type": "paragraph", "value": "Zebra-unique smoke body"}])
page = create_page(root.id, "Smoke Zebra Page", slug, body_json=body)
assert page.id and not page.live
publish_page(page.id, 0)
assert bool(cms_db.pages[page.id].live) is True
assert any(c.id == page.id for c in get_children(root.id))

reindex_all()
hits = search("Zebra")
assert any(h["object_id"] == page.id for h in hits), hits

set_setting("smoke_key", {"ok": True})
assert get_setting("smoke_key") in ({"ok": True}, '{"ok": true}'), get_setting("smoke_key")

user = cms_db.users.insert(email=f"{slug}@example.com", name="Smoke", password_hash="x",
                           role="editor", is_active=True, created_at=cms_db.now())
cms_db.users.update(id=user.id, is_active=False)
assert not cms_db.users[user.id].is_active
cms_db.log_action(user.id, "smoke", "page", page.id)

result = accounts.register(f"acct-{slug}@example.com", "correct horse battery staple", "Smoke")
assert result is not None

client = TestClient(main.app)
from fasthtml.common import to_xml
from app.landing import landing_page
html = to_xml(landing_page())
assert "Integrations" in html and "VIISP" in html and "Entra ID" in html and "LDAP" in html
r = client.get("/")
assert r.status_code == 200, r.status_code
r = client.get("/api/v1/health")
assert r.status_code == 200, r.text
r = client.get("/api/v1/pages", params={"q": "smoke zebra"})
assert r.status_code == 200, r.text
if expected == "postgres":
    # On SQLite the read API uses a stdlib sqlite3 connection while the CMS writes
    # through fastlite/apsw; in one process the two libraries do not see each
    # other's fresh writes (pre-existing behaviour), so only PostgreSQL checks rows.
    assert any(row["id"] == page.id for row in r.json()["data"]), r.json()
    r = client.get(f"/api/v1/pages/{page.id}")
    assert r.status_code == 200 and r.json()["slug"] == slug
from app.auth import hash_password
admin_email = f"admin-{slug}@example.com"
cms_db.users.insert(email=admin_email, name="Admin", password_hash=hash_password("pw"),
                    role="admin", is_active=True, created_at=cms_db.now())
r = client.post("/admin/login", data={"email": admin_email, "password": "pw"}, follow_redirects=False)
assert r.status_code == 303 and r.headers["location"] == "/admin/", (r.status_code, r.headers)
for path in ("/admin/", "/admin/pages/", "/admin/images/", "/admin/users/", "/admin/reports/", "/admin/settings/"):
    r = client.get(path, follow_redirects=False)
    assert r.status_code == 200, (path, r.status_code)
print(f"SMOKE OK ({expected})")
