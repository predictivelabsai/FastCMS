# FastHTML-CMS Implementation Plan

Rewriting the core of Wagtail CMS in FastHTML with SQLite (via fastlite).

## Architecture Overview

```
FastHTML (Starlette + HTMX + FastTags)
    └── Uvicorn ASGI server
    └── HTMX for SPA-like admin interactions
    └── FastTags for server-side HTML rendering

Fastlite (SQLite via APSW)
    └── MiniDataAPI for CRUD
    └── FTS5 for full-text search
    └── JSON1 for StreamField block storage
    └── WAL mode for concurrent reads

No Django, no PostgreSQL, no React, no Node.js, no webpack.
```

---

## Phase 1: Core Foundation

### 1.1 Database Schema (`app/db.py`)

Define all core tables using fastlite dataclasses:

```
User        — id, email, name, password_hash, role, is_active, created_at
Session     — id, user_id, token, expires_at
Site        — id, hostname, port, site_name, root_page_id, is_default
Locale      — id, language_code, is_default
```

### 1.2 Authentication (`app/auth.py`)

- Password hashing with bcrypt
- Session-based auth using FastHTML sessions + Beforeware
- Login/logout views
- Role enum: admin, editor, moderator
- Beforeware that injects `auth` into request scope
- Skip patterns for public routes and static files

### 1.3 App Bootstrap (`main.py`)

- FastHTML app with `fast_app()`
- Static file serving
- Session middleware
- Auth Beforeware
- APIRouter for admin and API sub-apps
- Environment config from `.env`

---

## Phase 2: Page System

### 2.1 Page Tree (`app/pages.py`)

SQLite tables:
```
Page        — id, title, slug, content_type, depth, path (materialized path),
              parent_id, live, has_unpublished_changes, url_path,
              seo_title, search_description, owner_id,
              first_published_at, last_published_at, created_at, updated_at,
              locale_id, locked, locked_by_id, locked_at
```

Key functions:
- `get_children(page_id)` — direct children ordered by path
- `get_descendants(page_id)` — all descendants via path prefix query
- `get_ancestors(page_id)` — ancestors from path segments
- `move_page(page_id, new_parent_id, position)` — recompute paths
- `create_child_page(parent_id, data)` — assign path, depth
- `get_url(page_id)` — construct URL from url_path
- Materialized path format: `0001/0002/0003` (4-digit segments)

### 2.2 Page Content Types

```
PageContent — id, page_id, revision_id, field_name, field_type, value
```

Or simpler: store page body as JSON blob per page type:
```
PageBody    — id, page_id, body_json (JSON column with all field values)
```

Built-in page types:
- **HomePage** — hero text, featured items
- **ContentPage** — title, body (StreamField), sidebar
- **BlogIndexPage** — intro, filter settings
- **BlogPage** — title, date, author, body, tags, featured_image
- **FormPage** — title, intro, form_fields JSON, thank_you_text

### 2.3 Revisions (`app/pages.py`)

```
Revision    — id, page_id, content_json, created_at, created_by_id,
              is_published, published_at, comment
```

- Every save creates a new revision
- Publishing marks a revision as `is_published`
- Restore copies old revision content to a new revision
- Diff: JSON diff between two revisions' content_json

### 2.4 Page Routing

- Public page serving: walk the URL path segments, resolve via `url_path`
- `Page.serve(request)` equivalent: route handler that loads page + template
- 404 handling for missing pages
- Redirect support for moved pages

---

## Phase 3: Admin Interface

### 3.1 Admin Layout (`admin/components.py`)

HTMX-powered admin shell:
- **Sidebar**: collapsible navigation (Dashboard, Pages, Images, Documents, Snippets, Forms, Users, Settings)
- **Header**: user menu, search bar, notifications
- **Main area**: content area swapped via HTMX
- **Action menu**: contextual actions (Save Draft, Publish, Delete, etc.)

All admin routes under `/admin/` prefix using APIRouter.

### 3.2 Dashboard (`admin/dashboard.py`)

Route: `GET /admin/`

- Welcome message with user name
- Site summary cards (pages count, images count, documents count, users count)
- Recent pages (last 10 edited)
- Draft pages awaiting review
- Quick actions (New Page, Upload Image, etc.)

### 3.3 Page Explorer (`admin/page_explorer.py`)

Routes:
- `GET /admin/pages/` — root page listing
- `GET /admin/pages/{id}/` — children of page `{id}`

Features:
- Tree-style indented listing
- Status indicators (live, draft, scheduled)
- Quick actions per row (Edit, View Live, Add Child, Move, Delete)
- Breadcrumb navigation
- Sort by title, updated date, status
- Search within explorer via HTMX

### 3.4 Page Editor (`admin/page_editor.py`)

Routes:
- `GET /admin/pages/{id}/edit/` — edit form
- `POST /admin/pages/{id}/edit/` — save
- `GET /admin/pages/add/?parent={id}&type={type}` — create form
- `POST /admin/pages/add/` — create

Features:
- **Content tab**: title, slug (auto-generated), body fields
- **Promote tab**: SEO title, search description, slug override
- **Settings tab**: publication date, owner, locale
- **Action menu**: Save Draft, Publish, Unpublish, Delete, View Revisions
- Auto-slug generation from title via HTMX (`hx-trigger="keyup changed delay:500ms"`)
- Unsaved changes warning
- Live preview panel (iframe or side panel)
- Revision history with restore

### 3.5 Content Panels

Reusable panel components (FastHTML FT functions):

- `FieldPanel(name, label, field_type)` — text, textarea, number, date, email, url, checkbox, select
- `RichTextPanel(name, label)` — WYSIWYG editor (Trix or similar)
- `ImageChooserPanel(name, label)` — modal image picker
- `DocumentChooserPanel(name, label)` — modal document picker
- `PageChooserPanel(name, label)` — modal page tree picker
- `StreamFieldPanel(name, label, block_types)` — composable block editor
- `InlinePanel(name, label, model)` — nested related items
- `MultiFieldPanel(name, label, children)` — grouped fields

---

## Phase 4: Content Blocks (`app/blocks.py`)

StreamField-equivalent stored as JSON in SQLite.

### Block Types

```python
class Block:
    type: str       # "text", "image", "embed", etc.
    value: dict     # block-specific data
    id: str         # unique block instance ID

# Stored as JSON array:
[
    {"type": "heading", "value": {"text": "Welcome", "level": 2}, "id": "abc123"},
    {"type": "paragraph", "value": {"text": "<p>Hello world</p>"}, "id": "def456"},
    {"type": "image", "value": {"image_id": 42, "caption": "A photo"}, "id": "ghi789"},
]
```

### Built-in Blocks

- **HeadingBlock** — text + level (h2-h4)
- **ParagraphBlock** — rich text content
- **ImageBlock** — image chooser + caption + alt text
- **EmbedBlock** — URL → oEmbed rendering
- **TableBlock** — rows × columns data grid
- **CodeBlock** — language + code with syntax highlighting
- **QuoteBlock** — quote text + attribution
- **ListBlock** — ordered/unordered list items
- **DocumentBlock** — document chooser + description
- **RawHTMLBlock** — raw HTML (admin only)
- **StructBlock** — named group of sub-blocks (composite)
- **StreamBlock** — mixed list of block types (recursive)

### Block Editor UI

- HTMX-powered add/remove/reorder
- Each block type has an edit form component
- Drag handle for reordering (Sortable.js)
- Add block button with type chooser dropdown
- Delete block with confirmation
- Collapse/expand individual blocks

---

## Phase 5: Media Management

### 5.1 Images (`app/media.py`)

```
Image       — id, title, file_path, file_hash, file_size, width, height,
              alt_text, focal_point_x, focal_point_y, collection_id,
              uploaded_by_id, created_at, tags
```

Features:
- Upload with automatic thumbnail generation (Pillow)
- Renditions: on-demand resize/crop cached to disk
  - `image.get_rendition("width-400")` → resized file
  - `image.get_rendition("fill-300x200")` → cropped to exact size
  - `image.get_rendition("max-800x600")` → fit within bounds
- Focal point for smart cropping
- Collection-based organization
- Tag-based filtering
- Usage tracking (which pages reference this image)
- Formats: JPEG, PNG, WebP, GIF, SVG passthrough

```
Rendition   — id, image_id, filter_spec, file_path, width, height
```

### 5.2 Documents (`app/media.py`)

```
Document    — id, title, file_path, file_hash, file_size, file_ext,
              collection_id, uploaded_by_id, created_at, tags
```

Features:
- Upload and serve with proper Content-Type
- Collection-based organization
- Download tracking
- File type validation

### 5.3 Collections

```
Collection  — id, name, parent_id, path, depth
```

- Hierarchical organization (same materialized path as pages)
- Permission assignment per collection per user role
- Used for both images and documents

### 5.4 Media Admin (`admin/media_library.py`)

Routes:
- `GET /admin/images/` — image listing (grid + list view toggle)
- `GET /admin/images/{id}/` — image detail/edit
- `POST /admin/images/add/` — upload
- `GET /admin/documents/` — document listing
- `GET /admin/documents/{id}/` — document detail/edit
- `POST /admin/documents/add/` — upload

Features:
- Grid view with thumbnails
- List view with metadata
- Upload with drag-and-drop (via HTMX file upload)
- Inline title/alt text editing
- Collection filter sidebar
- Tag filter
- Bulk tagging
- Image chooser modal (for use in page editor)

---

## Phase 6: Search (`app/search.py`)

### SQLite FTS5 Setup

```sql
CREATE VIRTUAL TABLE search_index USING fts5(
    title, body, content_type, object_id,
    tokenize='porter unicode61'
);
```

### Indexing

- Auto-index on page publish (insert/update FTS entry)
- Auto-index images and documents on save
- Bulk reindex management command
- Strip HTML tags before indexing rich text

### Search Features

- Full-text search with relevance ranking (`rank`)
- Prefix matching for autocomplete
- Filter by content type (pages, images, documents)
- Highlight matched terms in results
- Admin search bar (global search across all content)
- Public site search page

---

## Phase 7: Snippets (`app/snippets.py`)

### Snippet Registry

```python
snippet_registry = {}

def register_snippet(cls):
    """Decorator to register a model class as a snippet."""
    snippet_registry[cls.__name__] = cls
    return cls
```

### Built-in Snippet Types

Define via fastlite dataclasses:
- **NavigationMenu** — name, items (JSON array of {label, url, page_id})
- **SocialMediaLinks** — platform, url, icon
- **FooterContent** — column, content (rich text)
- **Testimonial** — name, role, quote, photo_id
- **FAQ** — question, answer, category, sort_order

### Snippet Admin (`admin/snippet_editor.py`)

Routes:
- `GET /admin/snippets/` — list registered snippet types
- `GET /admin/snippets/{type}/` — list instances
- `GET /admin/snippets/{type}/{id}/edit/` — edit form
- `POST /admin/snippets/{type}/{id}/edit/` — save

Auto-generated CRUD forms based on dataclass field types.

---

## Phase 8: Dynamic Forms (`app/forms.py`)

### Form Page Model

```
FormPage    — id, page_id (FK to Page), intro, thank_you_text,
              from_email, to_email, subject
FormField   — id, form_page_id, label, field_type, required, choices,
              default_value, help_text, sort_order
FormSubmission — id, form_page_id, data_json, submitted_at, submitted_by_ip
```

Field types: text, textarea, email, number, url, checkbox, radio, dropdown, date, file

### Features

- Admin UI to add/remove/reorder form fields
- Public form rendering with validation
- Submission storage in SQLite
- Submission list view in admin
- CSV export of submissions
- Optional email notification on submission

---

## Phase 9: JSON API (`app/api.py`)

RESTful API under `/api/v1/`.

### Endpoints

```
GET  /api/v1/pages/                — list pages (filterable, paginated)
GET  /api/v1/pages/{id}/           — single page with all fields
GET  /api/v1/pages/?child_of={id}  — children of a page
GET  /api/v1/pages/?type=BlogPage  — filter by type
GET  /api/v1/pages/?search=query   — full-text search

GET  /api/v1/images/               — list images
GET  /api/v1/images/{id}/          — single image with rendition URLs

GET  /api/v1/documents/            — list documents
GET  /api/v1/documents/{id}/       — single document
```

### Features

- JSON responses with proper Content-Type
- Pagination: `?limit=20&offset=0`
- Field selection: `?fields=title,body,date`
- Nested expansion: `?expand=featured_image`
- CORS headers for headless usage
- Optional API key authentication

---

## Phase 10: Workflow & Settings

### 10.1 Publish Workflow (`app/workflows.py`)

Simple publish workflow (no multi-step approval in v1):
- **Draft** → Save without publishing
- **Publish** → Make page live
- **Unpublish** → Remove from live site
- **Schedule** → Set future publish date (background check via periodic task)
- **Lock/Unlock** — Prevent concurrent editing

### 10.2 Site Settings (`app/settings.py`)

```
SiteSetting — id, site_id, key, value_json
```

Built-in settings:
- Site name, tagline, logo image
- Contact email, phone, address
- Social media URLs
- Analytics tracking code
- Custom CSS/JS injection
- SEO defaults (default meta description, OG image)

Admin UI: key-value settings editor at `/admin/settings/`

---

## Phase 11: User Management (`admin/user_manager.py`)

Routes:
- `GET /admin/users/` — user listing
- `GET /admin/users/{id}/edit/` — edit user
- `POST /admin/users/add/` — create user
- `GET /admin/users/{id}/delete/` — delete confirmation

Features:
- User CRUD with role assignment
- Password change (self + admin)
- Active/inactive toggle
- Filter by role
- Last login tracking
- Profile preferences (theme, notifications)

---

## Phase 12: Public Site Rendering

### URL Resolution

```python
@rt("/{path:path}")
def serve_page(path: str):
    page = pages("url_path=?", (f"/{path}/",))
    if not page: raise HTTPException(404)
    # Load page body, render with appropriate template
    return render_page(page)
```

### Template System

Use FastHTML FT components as "templates":

```python
def render_page(page):
    body = load_body(page)
    return (
        Title(page.seo_title or page.title),
        Meta(name="description", content=page.search_description),
        SiteHeader(),
        Main(render_blocks(body['blocks'])),
        SiteFooter(),
    )
```

Each block type has a `render_block(block)` function returning FT elements.

---

## Implementation Order

| Priority | Module | Effort | Dependencies |
|----------|--------|--------|-------------|
| 1 | Database schema + migrations | 1 day | None |
| 2 | Auth (login, session, roles) | 1 day | Database |
| 3 | Admin shell (sidebar, layout) | 1 day | Auth |
| 4 | Page tree (CRUD, materialized path) | 2 days | Database |
| 5 | Page explorer (admin listing) | 1 day | Page tree, Admin shell |
| 6 | Page editor (basic fields) | 2 days | Page tree, Admin shell |
| 7 | Revisions | 1 day | Page editor |
| 8 | Rich text editor integration | 1 day | Page editor |
| 9 | Image upload + management | 2 days | Database, Auth |
| 10 | Document upload + management | 1 day | Images (shared patterns) |
| 11 | Collections | 1 day | Images, Documents |
| 12 | Content blocks (StreamField) | 3 days | Rich text, Images |
| 13 | Block editor UI | 2 days | Content blocks |
| 14 | Full-text search (FTS5) | 1 day | Pages, Images, Docs |
| 15 | Snippets | 1 day | Admin shell |
| 16 | Dynamic forms | 2 days | Pages, Admin shell |
| 17 | JSON API | 1 day | Pages, Images, Docs |
| 18 | Public page rendering | 2 days | Pages, Blocks |
| 19 | Publish workflow + scheduling | 1 day | Pages, Revisions |
| 20 | Site settings | 1 day | Admin shell |
| 21 | User management admin | 1 day | Auth |
| 22 | Multi-site support | 1 day | Pages, Settings |

**Estimated total: ~27 days for one developer**

---

## What We're NOT Building (v1 scope cuts)

- **Multi-step approval workflows** — v1 has simple draft/publish only
- **Internationalization / translation UI** — locale field exists but no translation workflow
- **Elasticsearch/OpenSearch backends** — SQLite FTS5 only
- **Complex permission policies** — v1 has role-based, not object-level permissions
- **ModelAdmin / custom admin views** — snippets cover most use cases
- **Contrib modules** (redirects, sitemaps, search promotions) — future additions
- **Frontend cache invalidation** — not needed with SQLite
- **Commenting system on pages** — future addition
- **Audit logging** — future addition (basic revision history covers core need)
- **oEmbed provider resolution** — v1 stores embed HTML directly

---

## Tech Stack Summary

| Layer | Wagtail | FastHTML-CMS |
|-------|---------|---------|
| Framework | Django | FastHTML (Starlette) |
| Database | PostgreSQL | SQLite (fastlite) |
| ORM | Django ORM | fastlite MiniDataAPI |
| Search | Elasticsearch | SQLite FTS5 |
| Admin frontend | React (Draftail) | HTMX + FastTags |
| Rich text | Draft.js (Draftail) | Trix / Quill (vanilla JS) |
| CSS | Custom SCSS | Custom CSS (or MonsterUI) |
| Task queue | Celery | Background tasks (Starlette) |
| Caching | Redis/Memcached | In-process dict + SQLite |
| File storage | Django Storage | Local filesystem |
| API | Django REST Framework | Custom JSON handlers |
| Auth | Django auth | bcrypt + session cookies |
