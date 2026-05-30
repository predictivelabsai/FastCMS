from fastlite import database
from datetime import datetime, timezone
import os, json, hashlib

DB_PATH = os.getenv('DATABASE_PATH', 'data/fasthtml-cms.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = database(DB_PATH)

def now():
    return datetime.now(timezone.utc).isoformat()

# ── Table definitions ─────────────────────────────────────────────────

class User:
    id: int
    email: str
    name: str
    password_hash: str
    role: str = 'editor'
    is_active: bool = True
    last_login: str = ''
    created_at: str = ''

class Site:
    id: int
    hostname: str = 'localhost'
    port: int = 5001
    site_name: str = 'FastHTML-CMS'
    root_page_id: int = 0
    is_default: bool = True

class Collection:
    id: int
    name: str
    path: str = '0001'
    depth: int = 1
    parent_id: int = 0

class Page:
    id: int
    title: str
    slug: str
    content_type: str = 'ContentPage'
    path: str = '0001'
    depth: int = 1
    numchild: int = 0
    url_path: str = '/'
    live: bool = False
    has_unpublished_changes: bool = False
    owner_id: int = 0
    seo_title: str = ''
    search_description: str = ''
    show_in_menus: bool = False
    first_published_at: str = ''
    last_published_at: str = ''
    go_live_at: str = ''
    expire_at: str = ''
    expired: bool = False
    locked: bool = False
    locked_by_id: int = 0
    locked_at: str = ''
    body_json: str = '[]'
    extra_json: str = '{}'
    created_at: str = ''
    updated_at: str = ''

class Revision:
    id: int
    page_id: int
    content_json: str = '{}'
    created_at: str = ''
    created_by_id: int = 0
    is_published: bool = False
    published_at: str = ''
    comment: str = ''

class Image:
    id: int
    title: str
    file_path: str
    file_hash: str = ''
    file_size: int = 0
    width: int = 0
    height: int = 0
    alt_text: str = ''
    focal_point_x: float = 0.5
    focal_point_y: float = 0.5
    collection_id: int = 1
    uploaded_by_id: int = 0
    tags: str = ''
    created_at: str = ''

class Rendition:
    id: int
    image_id: int
    filter_spec: str
    file_path: str
    width: int = 0
    height: int = 0

class Document:
    id: int
    title: str
    file_path: str
    file_hash: str = ''
    file_size: int = 0
    file_ext: str = ''
    collection_id: int = 1
    uploaded_by_id: int = 0
    tags: str = ''
    created_at: str = ''

class SiteSetting:
    id: int
    site_id: int = 1
    key: str = ''
    value_json: str = ''

class FormField:
    id: int
    page_id: int
    label: str
    field_type: str = 'text'
    required: bool = False
    choices: str = ''
    default_value: str = ''
    help_text: str = ''
    sort_order: int = 0

class FormSubmission:
    id: int
    page_id: int
    data_json: str = '{}'
    submitted_at: str = ''
    submitted_by_ip: str = ''

class AuditLog:
    id: int
    user_id: int = 0
    action: str = ''
    content_type: str = ''
    object_id: int = 0
    object_repr: str = ''
    data_json: str = '{}'
    created_at: str = ''

# ── Create tables ─────────────────────────────────────────────────────

users = db.create(User, transform=True)
sites = db.create(Site, transform=True)
collections = db.create(Collection, transform=True)
pages = db.create(Page, transform=True)
revisions = db.create(Revision, transform=True)
images = db.create(Image, transform=True)
renditions = db.create(Rendition, transform=True)
documents = db.create(Document, transform=True)
site_settings = db.create(SiteSetting, transform=True)
form_fields = db.create(FormField, transform=True)
form_submissions = db.create(FormSubmission, transform=True)
audit_logs = db.create(AuditLog, transform=True)

# ── FTS5 ──────────────────────────────────────────────────────────────

def setup_fts():
    db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS search_index
                  USING fts5(title, body, content_type, object_id UNINDEXED,
                  tokenize='porter unicode61')""")

# ── Audit logging ─────────────────────────────────────────────────────

def log_action(user_id, action, content_type, object_id, object_repr='', data=None):
    audit_logs.insert(
        user_id=user_id, action=action, content_type=content_type,
        object_id=object_id, object_repr=object_repr,
        data_json=json.dumps(data or {}), created_at=now()
    )

def file_hash(content_bytes):
    return hashlib.sha1(content_bytes).hexdigest()
