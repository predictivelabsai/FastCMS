"""Database backend selection for FastCMS.

Mirrors the FastCRE pattern: a single connection URL in the environment selects
PostgreSQL (psycopg 3 + SQLAlchemy URL style). When neither ``DATABASE_URL`` nor
``DB_URL`` is set, FastCMS falls back to the original local SQLite files.

    DATABASE_URL=postgresql://user:pass@host:5432/fastcms

Everything that talks to the database goes through :func:`connect` (DB-API style,
``?`` placeholders accepted on both backends) or the fastlite-compatible
``PGDatabase`` used by ``app.db``.
"""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator


def database_url() -> str:
    """Return the configured PostgreSQL URL, or '' for the SQLite fallback."""
    url = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql+psycopg://"):
        url = "postgresql://" + url[len("postgresql+psycopg://"):]
    return url if url.startswith("postgresql://") else ""


def is_postgres() -> bool:
    return bool(database_url())


_QMARK = re.compile(r"\?")


def to_pg(sql: str) -> str:
    """Translate SQLite-flavoured SQL (``?`` params) to psycopg (``%s``)."""
    sql = sql.replace("%", "%%")
    return _QMARK.sub("%s", sql)


def ddl_to_pg(sql: str) -> str:
    """Translate the small amount of SQLite DDL FastCMS uses to PostgreSQL."""
    sql = re.sub(r"\bid\s+INTEGER\s+PRIMARY\s+KEY\b", "id BIGSERIAL PRIMARY KEY", sql, flags=re.I)
    sql = re.sub(r"\bINTEGER\b", "BIGINT", sql, flags=re.I)
    return sql


class _Row(dict):
    """dict row that also supports positional access like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def _row_factory(cursor):
    names = [c.name for c in cursor.description or []]

    def make(values):
        return _Row(zip(names, values))

    return make


class PGCursor:
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = None
        self._prefetched: list | None = None

    def fetchone(self):
        if self._prefetched is not None:
            return self._prefetched.pop(0) if self._prefetched else None
        return self._cur.fetchone() if self._cur.description else None

    def fetchall(self):
        if self._prefetched is not None:
            rows, self._prefetched = self._prefetched, []
            return rows
        return self._cur.fetchall() if self._cur.description else []

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def rowcount(self):
        return self._cur.rowcount


class PGConnection:
    """Tiny sqlite3-like facade over a psycopg connection."""

    def __init__(self, url: str):
        import psycopg

        self._conn = psycopg.connect(url, row_factory=_row_factory)

    def execute(self, sql: str, params: Any = ()):
        stripped = sql.strip()
        if stripped.upper().startswith("PRAGMA"):
            return PGCursor(self._conn.cursor())
        cur = self._conn.cursor()
        wants_id = stripped.upper().startswith("INSERT") and "RETURNING" not in stripped.upper()
        if wants_id:
            sql = stripped.rstrip(";") + " RETURNING *"
        cur.execute(to_pg(sql), tuple(params or ()))
        wrapped = PGCursor(cur)
        if wants_id:
            row = cur.fetchone()
            wrapped.lastrowid = row.get("id") if row else None
            wrapped._prefetched = []
        return wrapped

    def executescript(self, script: str):
        for statement in [s.strip() for s in ddl_to_pg(script).split(";")]:
            if statement:
                self._conn.execute(statement)
        return None

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()
        return False


def connect(sqlite_path: str | os.PathLike | None = None, timeout: float = 15):
    """Open a DB-API connection: PostgreSQL if configured, else SQLite file."""
    url = database_url()
    if url:
        return PGConnection(url)
    conn = sqlite3.connect(str(sqlite_path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection(sqlite_path: str | os.PathLike | None = None) -> Iterator[Any]:
    conn = connect(sqlite_path)
    try:
        yield conn
    finally:
        conn.close()


def table_columns(conn, table: str) -> list[dict[str, Any]]:
    """Return sqlite PRAGMA table_info-shaped column dicts for either backend."""
    if isinstance(conn, PGConnection):
        rows = conn.execute(
            """SELECT c.column_name AS name, c.data_type AS type,
                      (c.is_nullable = 'NO') AS notnull, c.column_default AS dflt_value,
                      EXISTS (SELECT 1 FROM information_schema.table_constraints tc
                              JOIN information_schema.key_column_usage k
                                ON tc.constraint_name = k.constraint_name AND tc.table_schema = k.table_schema
                              WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = c.table_name
                                AND tc.table_schema = c.table_schema AND k.column_name = c.column_name) AS pk
               FROM information_schema.columns c
               WHERE c.table_schema = current_schema() AND c.table_name = ?
               ORDER BY c.ordinal_position""",
            (table,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["type"] = (d["type"] or "").upper().replace("CHARACTER VARYING", "TEXT")
            d["notnull"] = int(bool(d["notnull"]))
            d["pk"] = int(bool(d["pk"]))
            if d["pk"] and str(d["dflt_value"] or "").startswith("nextval("):
                d["dflt_value"] = None
            out.append(d)
        return out
    return [dict(r) for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


# ── fastlite-compatible layer for PostgreSQL ───────────────────────────

class NotFoundError(Exception):
    pass


_PY2PG = {int: "BIGINT", bool: "INTEGER", float: "DOUBLE PRECISION", str: "TEXT"}


class PGTable:
    def __init__(self, db: "PGDatabase", cls: type, name: str):
        self.db, self.cls, self.name = db, cls, name
        self.fields = dict(getattr(cls, "__annotations__", {}))
        self.defaults = {k: getattr(cls, k) for k in self.fields if hasattr(cls, k)}

    # rows ↔ objects
    def _obj(self, row: dict):
        obj = self.cls.__new__(self.cls)
        for key, typ in self.fields.items():
            val = row.get(key, self.defaults.get(key))
            if typ is bool and val is not None:
                val = bool(val)
            setattr(obj, key, val)
        return obj

    def _clean(self, values: dict) -> dict:
        out = {}
        for key, val in values.items():
            if key not in self.fields:
                continue
            if isinstance(val, bool):
                val = int(val)
            out[key] = val
        return out

    @staticmethod
    def _values(obj=None, kwargs=None) -> dict:
        values = {}
        if obj is not None:
            values.update(obj if isinstance(obj, dict) else dict(vars(obj)))
        values.update(kwargs or {})
        return values

    def __getitem__(self, pk):
        rows = self.db.execute(f'SELECT * FROM "{self.name}" WHERE id=?', [pk]).fetchall()
        if not rows:
            raise NotFoundError(f"{self.name}[{pk}] not found")
        return self._obj(rows[0])

    def __call__(self, where: str | None = None, where_args=None, order_by: str | None = None,
                 limit: int | None = None, offset: int | None = None):
        sql = f'SELECT * FROM "{self.name}"'
        args = list(where_args or [])
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        if offset is not None:
            sql += f" OFFSET {int(offset)}"
        return [self._obj(r) for r in self.db.execute(sql, args).fetchall()]

    def insert(self, obj=None, **kwargs):
        values = self._clean(self._values(obj, kwargs))
        if values.get("id") in (None, 0):
            values.pop("id", None)
        for key, default in self.defaults.items():
            values.setdefault(key, int(default) if isinstance(default, bool) else default)
        cols = list(values)
        if cols:
            sql = (f'INSERT INTO "{self.name}" ({",".join(chr(34)+c+chr(34) for c in cols)}) '
                   f'VALUES ({",".join("?" for _ in cols)}) RETURNING *')
        else:
            sql = f'INSERT INTO "{self.name}" DEFAULT VALUES RETURNING *'
        row = self.db.execute(sql, [values[c] for c in cols]).fetchone()
        return self._obj(row)

    def update(self, obj=None, **kwargs):
        values = self._clean(self._values(obj, kwargs))
        pk = values.pop("id", None)
        if pk is None:
            raise ValueError("update() needs an id")
        if values:
            sets = ",".join(f'"{c}"=?' for c in values)
            self.db.execute(f'UPDATE "{self.name}" SET {sets} WHERE id=?', [*values.values(), pk])
        return self[pk]

    def delete(self, pk):
        self.db.execute(f'DELETE FROM "{self.name}" WHERE id=?', [pk])
        return self


class PGDatabase:
    """Just enough of fastlite's Database API for FastCMS, on PostgreSQL."""

    is_postgres = True

    def __init__(self, url: str):
        import psycopg

        self._conn = psycopg.connect(url, autocommit=True, row_factory=_row_factory)

    def execute(self, sql: str, params: Any = ()):
        cur = self._conn.cursor()
        cur.execute(to_pg(sql), tuple(params or ()))
        return PGCursor(cur)

    def create(self, cls: type, transform: bool = True, name: str | None = None):
        table = name or re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        fields = dict(getattr(cls, "__annotations__", {}))
        cols = []
        for key, typ in fields.items():
            if key == "id":
                cols.append('"id" BIGSERIAL PRIMARY KEY')
                continue
            col = f'"{key}" {_PY2PG.get(typ, "TEXT")}'
            if hasattr(cls, key):
                default = getattr(cls, key)
                if isinstance(default, bool):
                    default = int(default)
                if isinstance(default, str):
                    default = "'" + default.replace("'", "''") + "'"
                col += f" DEFAULT {default}"
            cols.append(col)
        self._conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(cols)})')
        if transform:
            for col in cols[1:] if fields and "id" in fields else cols:
                self._conn.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {col}')
        return PGTable(self, cls, table)
