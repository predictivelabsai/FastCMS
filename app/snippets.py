from app.db import db

_registry = {}

def register_snippet(name, cls, fields, icon='📋'):
    table = db.create(cls, transform=True)
    _registry[name] = {'cls': cls, 'table': table, 'fields': fields, 'icon': icon}

def get_snippet_types():
    return _registry

def get_snippet_table(name):
    return _registry[name]['table']

def get_snippet_info(name):
    return _registry.get(name)

# ── Built-in snippets ─────────────────────────────────────────────────

class NavigationMenu:
    id: int; name: str; items_json: str = '[]'

class FooterContent:
    id: int; column: str; content: str = ''

class SocialLink:
    id: int; platform: str; url: str = ''; sort_order: int = 0

class Testimonial:
    id: int; name: str; role: str = ''; quote: str = ''; photo_id: int = 0; sort_order: int = 0

class FAQ:
    id: int; question: str; answer: str = ''; category: str = ''; sort_order: int = 0

register_snippet('NavigationMenu', NavigationMenu,
    [{'name': 'name', 'type': 'text', 'label': 'Name'},
     {'name': 'items_json', 'type': 'textarea', 'label': 'Items (JSON)'}],
    icon='🧭')

register_snippet('FooterContent', FooterContent,
    [{'name': 'column', 'type': 'text', 'label': 'Column'},
     {'name': 'content', 'type': 'textarea', 'label': 'Content'}],
    icon='🦶')

register_snippet('SocialLink', SocialLink,
    [{'name': 'platform', 'type': 'text', 'label': 'Platform'},
     {'name': 'url', 'type': 'url', 'label': 'URL'},
     {'name': 'sort_order', 'type': 'number', 'label': 'Sort Order'}],
    icon='🔗')

register_snippet('Testimonial', Testimonial,
    [{'name': 'name', 'type': 'text', 'label': 'Name'},
     {'name': 'role', 'type': 'text', 'label': 'Role'},
     {'name': 'quote', 'type': 'textarea', 'label': 'Quote'},
     {'name': 'sort_order', 'type': 'number', 'label': 'Sort Order'}],
    icon='💬')

register_snippet('FAQ', FAQ,
    [{'name': 'question', 'type': 'text', 'label': 'Question'},
     {'name': 'answer', 'type': 'textarea', 'label': 'Answer'},
     {'name': 'category', 'type': 'text', 'label': 'Category'},
     {'name': 'sort_order', 'type': 'number', 'label': 'Sort Order'}],
    icon='❓')
