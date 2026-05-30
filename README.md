# FastHTML-CMS

A modern, lightweight content management system built with [FastHTML](https://fastht.ml) and SQLite. Inspired by [Wagtail](https://wagtail.org), reimagined for simplicity and speed.

**Built by [Predictive Labs Ltd](https://predictivelabs.ai)** | [PyPI](https://pypi.org/project/fasthtml-cms/)

![FastHTML-CMS Admin Tour](static/screenshots/admin-tour.gif)

## Features

- **Page Tree** — Hierarchical page management with drag-and-drop reordering
- **Rich Text Editing** — WYSIWYG editor with image and link embedding
- **StreamField-style Blocks** — Composable content blocks (text, image, embed, table, code)
- **Media Library** — Image and document management with collections and tagging
- **User Management** — Role-based access control (Admin, Editor, Moderator)
- **Full-Text Search** — SQLite FTS5 powered search across all content
- **Revision History** — Full version control with diff and restore
- **Draft/Publish Workflow** — Draft, review, schedule, and publish content
- **Snippets** — Reusable content fragments manageable from the admin
- **Dynamic Forms** — Build forms in the admin, collect submissions, export CSV
- **JSON API** — Headless CMS capability with RESTful endpoints
- **Multi-Site Support** — Serve multiple sites from a single instance
- **Live Preview** — See changes before publishing
- **SQLite Embedded Storage** — Zero-config database, no external dependencies
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

# Database
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

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-fasthtml` | Web framework (Starlette + HTMX + FastTags) |
| `fastlite` | SQLite ORM with MiniDataAPI |
| `python-multipart` | File upload handling |
| `pillow` | Image processing and thumbnails |
| `python-dotenv` | Environment variable loading |
| `bcrypt` | Password hashing |
| `itsdangerous` | Signed tokens for previews and password resets |

## Development

```bash
# Run with live reload (development mode)
python main.py --reload

# Run tests
python -m pytest tests/

# Reset database
rm data/fasthtml-cms.db && python setup.py
```

## Deployment

FastHTML-CMS runs as a single Python process with an embedded SQLite database. No external services required.

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

MIT License — see [LICENSE](LICENSE) for details.
