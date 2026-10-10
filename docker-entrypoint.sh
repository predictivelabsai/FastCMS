#!/usr/bin/env sh
# Container entrypoint for FastCMS (same pattern as FastCRE).
#
# On start we run `setup.py` (idempotent: creates tables, the search index, the
# root/home pages and default settings if missing) so fresh deploys come up
# without a manual step. An admin user is created only when
# FASTCMS_ADMIN_EMAIL and FASTCMS_ADMIN_PASSWORD are set.
#
# Set FASTCMS_SKIP_MIGRATE=1 to bypass (e.g. read-only replicas).

set -eu

if [ "${FASTCMS_SKIP_MIGRATE:-0}" != "1" ]; then
    echo "[entrypoint] running setup.py (idempotent)"
    python setup.py </dev/null || {
        echo "[entrypoint] setup failed, continuing to start so logs are visible" >&2
    }
fi

exec "$@"
