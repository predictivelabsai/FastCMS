"""Initialize database, create root page tree, and admin user."""
import sys
from app.db import (
    db, users, sites, collections, pages, setup_fts, now
)
from app.auth import hash_password
from app.snippets import get_snippet_types  # triggers registration
from app.settings import set_setting, DEFAULT_SETTINGS

def setup():
    print("FastHTML-CMS Setup")
    print("=" * 40)

    setup_fts()
    print("✓ FTS5 search index created")

    if not collections():
        collections.insert(name='Root', path='0001', depth=1, parent_id=0)
        print("✓ Root collection created")

    if not sites():
        sites.insert(hostname='localhost', port=5001, site_name='FastHTML-CMS',
                     root_page_id=1, is_default=True)
        print("✓ Default site created")

    if not pages():
        root = pages.insert(
            title='Root', slug='root', content_type='RootPage',
            path='0001', depth=1, numchild=1, url_path='/',
            live=True, created_at=now(), updated_at=now()
        )
        pages.insert(
            title='Home', slug='home', content_type='HomePage',
            path='00010001', depth=2, numchild=0, url_path='/',
            live=True, has_unpublished_changes=False,
            body_json='[{"type":"heading","value":{"text":"Welcome to FastHTML-CMS","level":2},"id":"welcome"},{"type":"paragraph","value":{"text":"<p>This is your new website. Edit this page from the <a href=\\"/admin/\\">admin panel</a>.</p>"},"id":"intro"}]',
            first_published_at=now(), last_published_at=now(),
            created_at=now(), updated_at=now()
        )
        pages.update(id=root.id, numchild=1)
        print("✓ Root page and Home page created")

    for key, default in DEFAULT_SETTINGS.items():
        set_setting(key, default)
    print("✓ Default settings initialized")

    if not users():
        email = input("Admin email [admin@example.com]: ").strip() or "admin@example.com"
        password = input("Admin password [admin]: ").strip() or "admin"
        name = input("Admin name [Admin]: ").strip() or "Admin"
        users.insert(
            email=email, name=name, password_hash=hash_password(password),
            role='admin', is_active=True, created_at=now()
        )
        print(f"✓ Admin user created ({email})")
    else:
        print("✓ Users already exist, skipping admin creation")

    print()
    print("Setup complete! Run: python main.py")
    print("Then visit: http://localhost:5001/admin/")

if __name__ == '__main__':
    setup()
