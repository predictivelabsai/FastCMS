# FastHTML-CMS

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A modern, lightweight content management system built with [FastHTML](https://fastht.ml), storing data in PostgreSQL (or SQLite for zero-config local use). Inspired by [Wagtail](https://wagtail.org), reimagined for simplicity and speed.

**Built by [Predictive Labs Ltd](https://predictivelabs.ai)** | [PyPI](https://pypi.org/project/fasthtml-cms/)

![FastHTML-CMS Admin Tour](static/screenshots/admin-tour.gif)

## Features

- **Page Tree** — Hierarchical page management with drag-and-drop reordering
- **Rich Text Editing** — WYSIWYG editor with image and link embedding
- **StreamField-style Blocks** — Composable content blocks (text, image, embed, table, code)
- **Media Library** — Image and document management with collections and tagging
- **User Management** — Role-based access control (Admin, Editor, Moderator)
- **Search** — SQLite FTS5 full-text search; case-insensitive search on PostgreSQL
- **Revision History** — Full version control with diff and restore
- **Draft/Publish Workflow** — Draft, review, schedule, and publish content
- **Snippets** — Reusable content fragments manageable from the admin
- **Dynamic Forms** — Build forms in the admin, collect submissions, export CSV
- **JSON API** — Headless CMS capability with RESTful endpoints
- **Multi-Site Support** — Serve multiple sites from a single instance
- **Live Preview** — See changes before publishing
- **PostgreSQL or SQLite** — set `DATABASE_URL` for PostgreSQL; leave it unset for an embedded SQLite file
- **Sign-in** — email/password, Google sign-in; VIISP, Microsoft Entra ID and LDAP / Active Directory adapters in development (see below)
- **HTMX-Powered Admin** — Fast, SPA-like admin experience with server-side rendering

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Install from PyPI
pip install fasthtml-cms

# Or clone the repository
git clone https://github.com/predictivelabs/FastHTML-CMS.git
cd FastHTML-CMS

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# Initialize the database and create an admin user
python setup.py

# Start the server
python main.py
```

The app will be running at **http://localhost:5001**.

- **Public site**: http://localhost:5001/
- **Admin panel**: http://localhost:5001/admin/
- **API**: http://localhost:5001/api/v1/pages/

Default admin credentials (set during `setup.py`):
- Email: `admin@example.com`
- Password: `admin` (change immediately in production)

### Configuration

Environment variables (set in `.env`):

```env
# Server
HOST=0.0.0.0
PORT=5001

# Database: PostgreSQL when set (DB_URL also accepted) ...
DATABASE_URL=postgresql://fastcms:fastcms@localhost:5432/fastcms
# ... otherwise SQLite files
DATABASE_PATH=data/fasthtml-cms.db

# Security
SECRET_KEY=change-me-to-a-random-string
SESSION_COOKIE=fasthtml_cms_session

# Media
MEDIA_PATH=media/
MAX_UPLOAD_SIZE_MB=10

# Site
SITE_NAME=FastHTML-CMS
DEFAULT_LOCALE=en
```

## Project Structure

```
FastHTML-CMS/
├── main.py                 # Application entry point
├── setup.py                # Database init and admin user creation
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── data/
│   └── fasthtml-cms.db     # SQLite database (created on first run)
├── media/                  # Uploaded images and documents
├── static/                 # CSS, JS, and static assets
│   ├── css/
│   ├── js/
│   └── img/
├── app/
│   ├── __init__.py
│   ├── db.py               # Database models and schema
│   ├── auth.py             # Authentication and authorization
│   ├── pages.py            # Page tree and content management
│   ├── blocks.py           # StreamField block system
│   ├── media.py            # Image and document management
│   ├── search.py           # Full-text search (FTS5)
│   ├── snippets.py         # Reusable content snippets
│   ├── forms.py            # Dynamic form builder
│   ├── api.py              # JSON API endpoints
│   ├── settings.py         # Site settings management
│   ├── workflows.py        # Draft/publish/review workflow
│   └── components.py       # Shared FastHTML UI components
├── admin/
│   ├── __init__.py
│   ├── routes.py           # Admin route definitions
│   ├── dashboard.py        # Admin dashboard
│   ├── page_editor.py      # Page create/edit views
│   ├── page_explorer.py    # Page tree browser
│   ├── media_library.py    # Image/document manager
│   ├── user_manager.py     # User administration
│   ├── snippet_editor.py   # Snippet management
│   └── components.py       # Admin UI components (sidebar, panels, choosers)
└── templates/              # Email templates and other text templates
```

See [`.env.example`](.env.example) for the full list.

## Database: PostgreSQL or SQLite

FastCMS picks its backend at start-up, following the same convention as the other
Fast* apps (FastCRE): one connection URL in the environment.

| `DATABASE_URL` | Backend | Notes |
|---|---|---|
| `postgresql://user:pass@host:5432/db` | PostgreSQL (psycopg 3) | Recommended for production. `postgres://` and `DB_URL` are accepted. |
| unset / empty | SQLite (`DATABASE_PATH`, `FASTSME_AUTH_DB`) | Zero-config fallback for local use; behaviour unchanged. |

Tables are created on first start (and missing columns added), so there is no
separate migration tool. `python setup.py` is idempotent: it seeds the root/home
pages and default settings and, when `FASTCMS_ADMIN_EMAIL` /
`FASTCMS_ADMIN_PASSWORD` are set, the first admin without prompting.

On PostgreSQL, search uses a plain `search_index` table with `ILIKE` matching
instead of SQLite FTS5.

### Docker

```bash
cp .env.example .env          # set SECRET_KEY, FASTCMS_ADMIN_* etc.
docker compose up --build     # postgres:16 + FastCMS on http://localhost:5001
```

The container entrypoint runs `setup.py` on every start (idempotent); set
`FASTCMS_SKIP_MIGRATE=1` to skip it.

There is no automatic SQLite → PostgreSQL data copy yet; start a fresh instance or
export/import content.

## Sign-in integrations

| Provider | Status | Enable with |
|---|---|---|
| Email + password | Available | always on |
| Google | Available | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| VIISP (Lithuanian e-government login: Smart-ID, Mobile-ID, banks, eID) | In development (stub) | `AUTH_VIISP_ENABLED=1` + `VIISP_*` |
| Microsoft Entra ID (OIDC / SSO) | In development (stub) | `AUTH_ENTRA_ENABLED=1` + `ENTRA_*` |
| LDAP / Active Directory | In development (stub) | `AUTH_LDAP_ENABLED=1` + `LDAP_*` |

The adapters live in `app/auth_providers/` and share one interface,
`AuthProvider` (`authenticate`, `get_login_url`, `handle_callback`,
`map_user_roles`). They are disabled by default and not yet wired into the login
routes. Their network flows raise `NotImplementedError`; each module lists its
TODOs. `AUTH_PROVIDERS_MOCK=1` makes Entra ID and LDAP return mock identities for
local UI work and tests only. `AUTH_<NAME>_ADMIN_GROUPS` maps directory groups to
the `admin` role. None of them is certified by, or affiliated with, the identity
provider.

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-fasthtml` | Web framework (Starlette + HTMX + FastTags) |
| `fastlite` | SQLite ORM with MiniDataAPI (SQLite fallback) |
| `psycopg[binary]` | PostgreSQL driver |
| `python-multipart` | File upload handling |
| `pillow` | Image processing and thumbnails |
| `python-dotenv` | Environment variable loading |
| `bcrypt` | Password hashing |
| `itsdangerous` | Signed tokens for previews and password resets |

## Development

```bash
# Run with live reload (development mode)
python main.py --reload

# Run tests (SQLite always; PostgreSQL when TEST_DATABASE_URL is set)
pip install pytest httpx
python -m pytest tests/
TEST_DATABASE_URL=postgresql://fastcms:fastcms@localhost:5432/fastcms python -m pytest tests/

# Reset database
rm data/fasthtml-cms.db && python setup.py
```

## Deployment

FastHTML-CMS runs as a single Python process. Point `DATABASE_URL` at PostgreSQL for production, or leave it unset to use an embedded SQLite file with no external services. See **Docker** above for a compose stack.

```bash
# Production
pip install fasthtml-cms
python setup.py
python main.py
```

For production, set `SECRET_KEY` to a strong random value and configure a reverse proxy (nginx/caddy) in front of uvicorn.

## Demo

Try the live demo at **[fastcms.predictivelabs.ai](https://fastcms.predictivelabs.ai)**

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
