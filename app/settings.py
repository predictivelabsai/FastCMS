import json
from app.db import site_settings

DEFAULT_SETTINGS = {
    'site_name': 'FastHTML-CMS',
    'site_tagline': '',
    'contact_email': '',
    'contact_phone': '',
    'contact_address': '',
    'social_twitter': '',
    'social_facebook': '',
    'social_linkedin': '',
    'social_github': '',
    'analytics_tracking_code': '',
    'custom_css': '',
    'custom_js': '',
    'default_meta_description': '',
    'og_image_id': '',
}

def get_setting(key, default=None):
    rows = site_settings(where="key=?", where_args=[key], limit=1)
    if rows:
        try: return json.loads(rows[0].value_json)
        except: return rows[0].value_json
    return default if default is not None else DEFAULT_SETTINGS.get(key, '')

def set_setting(key, value):
    existing = site_settings(where="key=?", where_args=[key], limit=1)
    val_json = json.dumps(value) if not isinstance(value, str) else json.dumps(value)
    if existing:
        site_settings.update(id=existing[0].id, value_json=val_json)
    else:
        site_settings.insert(site_id=1, key=key, value_json=val_json)

def get_all_settings():
    result = dict(DEFAULT_SETTINGS)
    for row in site_settings():
        try: result[row.key] = json.loads(row.value_json)
        except: result[row.key] = row.value_json
    return result
