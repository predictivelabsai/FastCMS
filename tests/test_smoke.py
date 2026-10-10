"""Smoke tests for both database backends.

SQLite always runs. PostgreSQL runs when TEST_DATABASE_URL points at a database
you are happy to write test rows into, e.g. the docker-compose service:

    TEST_DATABASE_URL=postgresql://fastcms:fastcms@localhost:5432/fastcms pytest
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(expected: str, env_extra: dict, tmp_path: Path):
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "DB_URL")}
    env.update(env_extra)
    env.setdefault("DATABASE_PATH", str(tmp_path / "cms.db"))
    env.setdefault("FASTSME_AUTH_DB", str(tmp_path / "accounts.sqlite"))
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run([sys.executable, str(ROOT / "tests" / "smoke_app.py"), expected],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert f"SMOKE OK ({expected})" in proc.stdout


def test_sqlite_fallback(tmp_path):
    _run("sqlite", {}, tmp_path)


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set")
def test_postgres(tmp_path):
    _run("postgres", {"DATABASE_URL": os.environ["TEST_DATABASE_URL"]}, tmp_path)


def test_database_url_parsing(monkeypatch):
    from app import dbconn
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h:5432/d")
    assert dbconn.database_url() == "postgresql://u:p@h:5432/d"
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/d")
    assert dbconn.database_url() == "postgresql://u:p@h/d"
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DB_URL", "postgresql://u@h/d")  # FastCRE-style name
    assert dbconn.is_postgres()
    monkeypatch.delenv("DB_URL")
    assert not dbconn.is_postgres()


def test_sql_translation():
    from app.dbconn import ddl_to_pg, to_pg
    assert to_pg("SELECT * FROM t WHERE a=? AND b LIKE '%x'") == "SELECT * FROM t WHERE a=%s AND b LIKE '%%x'"
    assert "BIGSERIAL PRIMARY KEY" in ddl_to_pg("CREATE TABLE a (id INTEGER PRIMARY KEY, n INTEGER)")
